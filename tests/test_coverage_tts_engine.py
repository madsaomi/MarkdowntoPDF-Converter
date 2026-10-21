"""Поведенческие тесты core/tts_engine.py.

Движок озвучки — чистый Python без Qt, поэтому здесь всё проверяется
напрямую: каталог голосов, ограничения настроек, оценка длительности,
очистка Markdown, пауза/возобновление/остановка, выбор голоса pyttsx3,
экспорт в файл и обработка отсутствия/сбоя движка.
"""
import os
import sys
import threading
import time
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.core.tts_engine as te


# ─── фальшивый pyttsx3 ───────────────────────────────────────────────────────

class _FakeVoice:
    def __init__(self, vid):
        self.id = vid


class _FakePyttsx3Engine:
    def __init__(self, voices=None, fail_init=False):
        self._voices = voices if voices is not None else [
            _FakeVoice("ru_alexei"), _FakeVoice("en_james"),
        ]
        self.fail_init = fail_init
        self.props = {}
        self.said = []
        self.ran = 0
        self.saved = []

    def getProperty(self, name):
        if name == "voices":
            return self._voices
        return self.props.get(name)

    def setProperty(self, key, value):
        self.props[key] = value

    def say(self, text):
        self.said.append(text)

    def runAndWait(self):
        self.ran += 1

    def save_to_file(self, text, path):
        self.saved.append((text, path))


class _FakePyttsx3Module:
    """Подменяет модуль pyttsx3 в sys.modules."""

    def __init__(self, engine=None):
        self.engine = engine or _FakePyttsx3Engine()
        self.inits = 0

    def init(self):
        self.inits += 1
        if self.engine.fail_init:
            raise RuntimeError("no audio device")
        return self.engine


def _install_pyttsx3(engine=None):
    fake = _FakePyttsx3Module(engine)
    previous = sys.modules.get("pyttsx3", "missing")
    sys.modules["pyttsx3"] = fake
    return fake, previous


def _restore_pyttsx3(previous):
    if previous == "missing":
        sys.modules.pop("pyttsx3", None)
    else:
        sys.modules["pyttsx3"] = previous


class _NoPyttsx3:
    """Временно прячет pyttsx3, чтобы сработала ветка ImportError."""

    def __enter__(self):
        self._prev = sys.modules.get("pyttsx3", "missing")
        sys.modules["pyttsx3"] = None
        return self

    def __exit__(self, *exc):
        _restore_pyttsx3(self._prev)
        return False


# ─── каталог голосов и модели ────────────────────────────────────────────────

def test_voice_gender_enum_values():
    """Голосовые типы имеют стабильные строковые значения."""
    assert te.VoiceGender.MALE.value == "male"
    assert te.VoiceGender.FEMALE.value == "female"
    assert te.VoiceGender.NEUTRAL.value == "neutral"
    assert te.VoiceGender.CHILD.value == "child"
    assert te.VoiceGender.ELDERLY.value == "elderly"
    assert te.VoiceGender.ROBOT.value == "robot"
    assert te.VoiceGender.WHISPER.value == "whisper"
    assert te.VoiceGender.NARRATOR.value == "narrator"
    print("[PASS] test_voice_gender_enum_values")


def test_voice_profile_defaults():
    """У профиля голоса разумные значения по умолчанию."""
    v = te.VoiceProfile("id1", "Name", "ru", te.VoiceGender.MALE)
    assert v.speed == 1.0
    assert v.pitch == 1.0
    assert v.volume == 1.0
    assert v.description == ""
    assert v.is_premium is False
    assert v.accent == ""
    assert v.emotion == "neutral"
    print("[PASS] test_voice_profile_defaults")


def test_tts_settings_defaults():
    """Настройки воспроизведения по умолчанию."""
    s = te.TTSSettings()
    assert s.voice_id == "default"
    assert s.speed == 1.0
    assert s.pitch == 1.0
    assert s.volume == 1.0
    assert s.pause_between_paragraphs == 0.5
    assert s.pause_between_sentences == 0.2
    print("[PASS] test_tts_settings_defaults")


def test_voices_catalog_is_consistent():
    """Каталог голосов: уникальные id, известные языки, премиум только multi."""
    ids = [v.id for v in te.AdvancedTTSEngine.VOICES]
    assert len(ids) == len(set(ids)), "id голосов должны быть уникальны"
    assert {v.language for v in te.AdvancedTTSEngine.VOICES} <= {"ru", "en", "multi"}
    for v in te.AdvancedTTSEngine.VOICES:
        if v.is_premium:
            assert v.language == "multi", v.id
    print("[PASS] test_voices_catalog_is_consistent")


def test_get_voices_all():
    """Без фильтра возвращается весь каталог."""
    engine = te.AdvancedTTSEngine()
    assert len(engine.get_voices()) == len(te.AdvancedTTSEngine.VOICES)
    print("[PASS] test_get_voices_all")


def test_get_voices_filtered_by_language():
    """Фильтр по языку добавляет мультиязычные голоса."""
    engine = te.AdvancedTTSEngine()
    ru = engine.get_voices("ru")
    assert ru, "должны быть русские голоса"
    assert all(v.language in ("ru", "multi") for v in ru)
    assert any(v.language == "multi" for v in ru), "multi-голоса доступны везде"

    multi = engine.get_voices("multi")
    assert multi and all(v.language == "multi" for v in multi)

    # Неизвестный язык не имеет собственных голосов, но multi доступны всегда
    unknown = engine.get_voices("de")
    assert unknown and all(v.language == "multi" for v in unknown), unknown
    print("[PASS] test_get_voices_filtered_by_language")


def test_set_voice():
    """Голос сохраняется в настройках."""
    engine = te.AdvancedTTSEngine()
    engine.set_voice("ru_female_1")
    assert engine.settings.voice_id == "ru_female_1"
    print("[PASS] test_set_voice")


# ─── ограничения настроек ────────────────────────────────────────────────────

def test_set_speed_clamps():
    """Скорость ограничена диапазоном 0.5..2.0."""
    engine = te.AdvancedTTSEngine()
    engine.set_speed(0.1)
    assert engine.settings.speed == 0.5
    engine.set_speed(5.0)
    assert engine.settings.speed == 2.0
    engine.set_speed(1.3)
    assert engine.settings.speed == 1.3
    print("[PASS] test_set_speed_clamps")


def test_set_pitch_clamps():
    """Высота голоса ограничена диапазоном 0.5..2.0."""
    engine = te.AdvancedTTSEngine()
    engine.set_pitch(0.0)
    assert engine.settings.pitch == 0.5
    engine.set_pitch(9.0)
    assert engine.settings.pitch == 2.0
    engine.set_pitch(0.8)
    assert engine.settings.pitch == 0.8
    print("[PASS] test_set_pitch_clamps")


def test_set_volume_clamps():
    """Громкость ограничена диапазоном 0.0..1.0."""
    engine = te.AdvancedTTSEngine()
    engine.set_volume(-1.0)
    assert engine.settings.volume == 0.0
    engine.set_volume(3.0)
    assert engine.settings.volume == 1.0
    engine.set_volume(0.4)
    assert engine.settings.volume == 0.4
    print("[PASS] test_set_volume_clamps")


def test_set_pause_between_paragraphs():
    """Пауза между абзацами сохраняется без ограничений."""
    engine = te.AdvancedTTSEngine()
    engine.set_pause_between_paragraphs(1.25)
    assert engine.settings.pause_between_paragraphs == 1.25
    print("[PASS] test_set_pause_between_paragraphs")


# ─── длительность и очистка текста ───────────────────────────────────────────

def test_estimated_duration_scales_with_speed():
    """25 слов при скорости 1.0 — 10 секунд, при 2.0 — 5 секунд."""
    engine = te.AdvancedTTSEngine()
    text = " ".join(["word"] * 25)
    assert engine.get_estimated_duration(text) == 10.0
    engine.set_speed(2.0)
    assert engine.get_estimated_duration(text) == 5.0
    print("[PASS] test_estimated_duration_scales_with_speed")


def test_estimated_duration_empty_text():
    """Пустой текст — нулевая длительность."""
    engine = te.AdvancedTTSEngine()
    assert engine.get_estimated_duration("") == 0.0
    print("[PASS] test_estimated_duration_empty_text")


def test_strip_markdown_removes_images_and_links():
    """Картинки удаляются, у ссылок остаётся только текст."""
    out = te.strip_markdown_for_tts("Смотри ![схема](img/a.png) и [документ](http://x.y).")
    assert "img/a.png" not in out, out
    assert "схема" not in out, out
    assert "документ" in out, out
    assert "http://x.y" not in out, out
    print("[PASS] test_strip_markdown_removes_images_and_links")


def test_strip_markdown_removes_html_and_code():
    """HTML-теги, блоки кода и инлайн-код очищаются."""
    out = te.strip_markdown_for_tts(
        "<b>жирный</b>\n\n```python\nprint(1)\n```\n\nВызов `func()` тут."
    )
    assert "<b>" not in out and "</b>" not in out, out
    assert "print(1)" not in out, out
    assert "code block omitted" in out, out
    assert "`" not in out, out
    assert "func()" in out, out
    print("[PASS] test_strip_markdown_removes_html_and_code")


def test_strip_markdown_removes_heading_and_emphasis():
    """Заголовки, жирный/курсив, цитаты и разделители убираются."""
    out = te.strip_markdown_for_tts(
        "# Заголовок\n\n**жирный** и *курсив* и ***оба***\n\n> цитата\n\n---\n"
    )
    assert "#" not in out, out
    assert "*" not in out, out
    assert "_" not in out, out
    assert "жирный" in out and "курсив" in out, out
    assert "цитата" in out, out
    assert "---" not in out, out
    print("[PASS] test_strip_markdown_removes_heading_and_emphasis")


def test_strip_markdown_collapses_blank_lines():
    """Три и более переводов строки сжимаются до двух."""
    out = te.strip_markdown_for_tts("a\n\n\n\n\nb")
    assert "\n\n\n" not in out, repr(out)
    assert out == "a\n\nb", repr(out)
    print("[PASS] test_strip_markdown_collapses_blank_lines")


def test_strip_markdown_strips_surrounding_whitespace():
    """Результат не содержит обрамляющих пробелов."""
    assert te.strip_markdown_for_tts("\n\n  текст  \n\n") == "текст"
    print("[PASS] test_strip_markdown_strips_surrounding_whitespace")


# ─── состояние воспроизведения ───────────────────────────────────────────────

def test_speak_starts_daemon_thread():
    """speak() запускает фоновый демон-поток с исходным текстом и языком."""
    engine = te.AdvancedTTSEngine()
    seen = []

    def _fake(text, lang):
        seen.append((text, lang))
        engine._is_playing = False

    engine._speak_thread = _fake
    engine.speak("привет", "ru")
    engine._playback_thread.join(timeout=5)
    assert seen == [("привет", "ru")], seen
    assert not engine._playback_thread.is_alive()
    print("[PASS] test_speak_starts_daemon_thread")


def test_speak_stops_previous_playback():
    """Повторный speak() сначала останавливает предыдущее воспроизведение."""
    engine = te.AdvancedTTSEngine()
    stops = []
    engine.stop = lambda: stops.append(1)
    engine._is_playing = True
    engine._speak_thread = lambda text, lang: None
    engine.speak("текст", "ru")
    engine._playback_thread.join(timeout=5)
    assert stops == [1], stops
    print("[PASS] test_speak_stops_previous_playback")


def test_pause_resume_stop_state_and_callbacks():
    """Пауза/возобновление/остановка меняют состояние и зовут колбэк."""
    engine = te.AdvancedTTSEngine()
    states = []
    engine.set_on_state_change(lambda s: states.append(s))

    engine.pause()
    assert engine.is_paused()
    assert not engine._resume_event.is_set()

    engine.resume()
    assert not engine.is_paused()
    assert engine._resume_event.is_set()

    engine._is_playing = True
    engine.stop()
    assert not engine.is_playing()
    assert not engine.is_paused()
    assert engine._resume_event.is_set()

    assert states == ["paused", "playing", "stopped"], states
    print("[PASS] test_pause_resume_stop_state_and_callbacks")


def test_is_playing_is_false_while_paused():
    """При паузе is_playing() возвращает False."""
    engine = te.AdvancedTTSEngine()
    engine._is_playing = True
    assert engine.is_playing() is True
    engine.pause()
    assert engine.is_playing() is False
    assert engine.is_paused() is True
    print("[PASS] test_is_playing_is_false_while_paused")


def test_callbacks_can_be_set_to_none():
    """Колбэки опциональны — их отсутствие не ломает методы."""
    engine = te.AdvancedTTSEngine()
    engine.pause()
    engine.resume()
    engine.stop()
    assert engine._on_state_change is None
    print("[PASS] test_callbacks_can_be_set_to_none")


# ─── фоновое воспроизведение ─────────────────────────────────────────────────

def test_speak_thread_says_paragraphs_and_reports_progress():
    """Абзацы уходят в движок, прогресс считается по их числу."""
    engine = te.AdvancedTTSEngine()
    engine.set_volume(0.7)
    engine.set_pause_between_paragraphs(0)
    fake_engine = _FakePyttsx3Engine()
    fake_module, previous = _install_pyttsx3(fake_engine)
    progress = []
    states = []
    engine.set_on_progress(lambda p, preview: progress.append((p, preview)))
    engine.set_on_state_change(lambda s: states.append(s))
    engine._is_playing = True
    try:
        engine._speak_thread("первый абзац\n\nвторой абзац", "ru")
    finally:
        _restore_pyttsx3(previous)

    assert fake_module.inits == 1
    assert fake_engine.said == ["первый абзац", "второй абзац"], fake_engine.said
    assert fake_engine.ran == 1
    assert fake_engine.props["rate"] == 200
    assert fake_engine.props["volume"] == 0.7
    assert fake_engine.props["voice"] == "ru_alexei"
    assert [p for p, _ in progress] == [0.5, 1.0], progress
    assert progress[0][1] == "первый абзац"
    assert states == ["stopped"], states
    assert engine._is_playing is False
    print("[PASS] test_speak_thread_says_paragraphs_and_reports_progress")


def test_speak_thread_matches_voice_by_id():
    """Голос выбирается по подстроке voice_id, а не только по языку."""
    engine = te.AdvancedTTSEngine()
    engine.set_voice("JAMES")
    engine.set_pause_between_paragraphs(0)
    fake_engine = _FakePyttsx3Engine()
    _, previous = _install_pyttsx3(fake_engine)
    engine._is_playing = True
    try:
        engine._speak_thread("hello", "en")
    finally:
        _restore_pyttsx3(previous)
    assert fake_engine.props["voice"] == "en_james", fake_engine.props
    print("[PASS] test_speak_thread_matches_voice_by_id")


def test_speak_thread_skips_blank_paragraphs():
    """Пустые абзацы не отправляются в движок."""
    engine = te.AdvancedTTSEngine()
    engine.set_pause_between_paragraphs(0)
    fake_engine = _FakePyttsx3Engine()
    _, previous = _install_pyttsx3(fake_engine)
    engine._is_playing = True
    try:
        engine._speak_thread("текст\n\n   \n\nещё", "ru")
    finally:
        _restore_pyttsx3(previous)
    assert fake_engine.said == ["текст", "ещё"], fake_engine.said
    print("[PASS] test_speak_thread_skips_blank_paragraphs")


def test_speak_thread_respects_stop_before_first_paragraph():
    """Если остановили до старта, движок не получает текст."""
    engine = te.AdvancedTTSEngine()
    fake_engine = _FakePyttsx3Engine()
    _, previous = _install_pyttsx3(fake_engine)
    engine._is_playing = False
    try:
        engine._speak_thread("текст", "ru")
    finally:
        _restore_pyttsx3(previous)
    assert fake_engine.said == [], fake_engine.said
    assert fake_engine.ran == 1, "runAndWait вызывается всегда"
    print("[PASS] test_speak_thread_respects_stop_before_first_paragraph")


def test_speak_thread_waits_while_paused():
    """Пауза приостанавливает поток до возобновления/остановки."""
    engine = te.AdvancedTTSEngine()
    engine.set_pause_between_paragraphs(0)
    fake_engine = _FakePyttsx3Engine()
    _, previous = _install_pyttsx3(fake_engine)
    engine._is_playing = True
    engine.pause()  # выставит _is_paused и сбросит событие

    worker = threading.Thread(
        target=engine._speak_thread, args=("абзац", "ru"), daemon=True
    )
    worker.start()
    try:
        # Пока пауза не снята, поток обязан ждать и ничего не читать
        time.sleep(0.2)
        assert worker.is_alive(), "поток должен ждать снятия паузы"
        assert fake_engine.said == [], fake_engine.said

        engine.stop()
        worker.join(timeout=5)
        assert not worker.is_alive(), "после stop() поток должен завершиться"
        assert fake_engine.said == [], "после остановки текст не читается"
    finally:
        _restore_pyttsx3(previous)
    print("[PASS] test_speak_thread_waits_while_paused")


def test_speak_thread_reports_missing_pyttsx3():
    """Без pyttsx3 движок не падает и сообщает об остановке."""
    engine = te.AdvancedTTSEngine()
    states = []
    engine.set_on_state_change(lambda s: states.append(s))
    engine._is_playing = True
    with _NoPyttsx3():
        engine._speak_thread("текст", "ru")
    assert states == ["stopped"], states
    assert engine._is_playing is False
    print("[PASS] test_speak_thread_reports_missing_pyttsx3")


def test_speak_thread_swallows_engine_failure():
    """Сбой инициализации движка перехватывается, состояние сбрасывается."""
    engine = te.AdvancedTTSEngine()
    states = []
    engine.set_on_state_change(lambda s: states.append(s))
    fake_engine = _FakePyttsx3Engine(fail_init=True)
    _, previous = _install_pyttsx3(fake_engine)
    engine._is_playing = True
    try:
        engine._speak_thread("текст", "ru")
    finally:
        _restore_pyttsx3(previous)
    assert states == ["stopped"], states
    assert engine._is_playing is False
    print("[PASS] test_speak_thread_swallows_engine_failure")


# ─── экспорт в файл ──────────────────────────────────────────────────────────

def test_export_to_file_success():
    """Экспорт вызывает save_to_file и возвращает True."""
    engine = te.AdvancedTTSEngine()
    engine.set_speed(1.5)
    fake_engine = _FakePyttsx3Engine()
    _, previous = _install_pyttsx3(fake_engine)
    try:
        ok = engine.export_to_file("привет", "out.mp3", "ru")
    finally:
        _restore_pyttsx3(previous)
    assert ok is True
    assert fake_engine.saved == [("привет", "out.mp3")], fake_engine.saved
    assert fake_engine.props["rate"] == 300
    assert fake_engine.props["voice"] == "ru_alexei"
    print("[PASS] test_export_to_file_success")


def test_export_to_file_failure_returns_false():
    """Сбой движка при экспорте возвращает False, а не исключение."""
    engine = te.AdvancedTTSEngine()
    fake_engine = _FakePyttsx3Engine(fail_init=True)
    _, previous = _install_pyttsx3(fake_engine)
    try:
        ok = engine.export_to_file("привет", "out.mp3", "ru")
    finally:
        _restore_pyttsx3(previous)
    assert ok is False
    print("[PASS] test_export_to_file_failure_returns_false")


def test_export_to_file_without_pyttsx3_returns_false():
    """Отсутствие pyttsx3 — тоже False, без исключения."""
    engine = te.AdvancedTTSEngine()
    with _NoPyttsx3():
        ok = engine.export_to_file("привет", "out.mp3", "ru")
    assert ok is False
    print("[PASS] test_export_to_file_without_pyttsx3_returns_false")


def test_export_to_file_no_matching_voice():
    """Если голос под язык не найден, экспорт всё равно идёт."""
    engine = te.AdvancedTTSEngine()
    fake_engine = _FakePyttsx3Engine(voices=[_FakeVoice("de_klaus")])
    _, previous = _install_pyttsx3(fake_engine)
    try:
        ok = engine.export_to_file("hi", "out.mp3", "xx")
    finally:
        _restore_pyttsx3(previous)
    assert ok is True
    assert "voice" not in fake_engine.props
    print("[PASS] test_export_to_file_no_matching_voice")


# ─── легаси-обёртки ──────────────────────────────────────────────────────────

def test_text_to_speech_uses_default_temp_path():
    """Без пути результат попадает во временный каталог."""
    engine = te.AdvancedTTSEngine()
    engine.export_to_file = lambda text, path, lang: True
    orig = te.AdvancedTTSEngine
    te.AdvancedTTSEngine = lambda: engine
    try:
        path = te.text_to_speech("текст", "ru")
    finally:
        te.AdvancedTTSEngine = orig
    import tempfile
    assert path.endswith("md2pdf_tts_output.mp3"), path
    assert os.path.dirname(os.path.abspath(path)) == os.path.abspath(tempfile.gettempdir()), path
    print("[PASS] test_text_to_speech_uses_default_temp_path")


def test_text_to_speech_respects_custom_path():
    """Указанный путь возвращается без изменений."""
    calls = []
    engine = te.AdvancedTTSEngine()
    engine.export_to_file = lambda text, path, lang: calls.append((text, path, lang)) or True
    orig = te.AdvancedTTSEngine
    te.AdvancedTTSEngine = lambda: engine
    try:
        path = te.text_to_speech("текст", "en", "custom.wav")
    finally:
        te.AdvancedTTSEngine = orig
    assert path == "custom.wav"
    assert calls == [("текст", "custom.wav", "en")], calls
    print("[PASS] test_text_to_speech_respects_custom_path")


def test_speak_text_is_blocking():
    """speak_text синхронно передаёт текст движку и ждёт завершения."""
    fake_engine = _FakePyttsx3Engine()
    _, previous = _install_pyttsx3(fake_engine)
    try:
        te.speak_text("привет", "ru")
    finally:
        _restore_pyttsx3(previous)
    assert fake_engine.said == ["привет"], fake_engine.said
    assert fake_engine.ran == 1
    print("[PASS] test_speak_text_is_blocking")


def test_get_tts_engine_is_singleton():
    """get_tts_engine возвращает один и тот же экземпляр."""
    if hasattr(te.get_tts_engine, "_instance"):
        del te.get_tts_engine._instance
    first = te.get_tts_engine()
    second = te.get_tts_engine()
    assert first is second
    assert isinstance(first, te.AdvancedTTSEngine)
    print("[PASS] test_get_tts_engine_is_singleton")


def main():
    tests = [
        test_voice_gender_enum_values,
        test_voice_profile_defaults,
        test_tts_settings_defaults,
        test_voices_catalog_is_consistent,
        test_get_voices_all,
        test_get_voices_filtered_by_language,
        test_set_voice,
        test_set_speed_clamps,
        test_set_pitch_clamps,
        test_set_volume_clamps,
        test_set_pause_between_paragraphs,
        test_estimated_duration_scales_with_speed,
        test_estimated_duration_empty_text,
        test_strip_markdown_removes_images_and_links,
        test_strip_markdown_removes_html_and_code,
        test_strip_markdown_removes_heading_and_emphasis,
        test_strip_markdown_collapses_blank_lines,
        test_strip_markdown_strips_surrounding_whitespace,
        test_speak_starts_daemon_thread,
        test_speak_stops_previous_playback,
        test_pause_resume_stop_state_and_callbacks,
        test_is_playing_is_false_while_paused,
        test_callbacks_can_be_set_to_none,
        test_speak_thread_says_paragraphs_and_reports_progress,
        test_speak_thread_matches_voice_by_id,
        test_speak_thread_skips_blank_paragraphs,
        test_speak_thread_respects_stop_before_first_paragraph,
        test_speak_thread_waits_while_paused,
        test_speak_thread_reports_missing_pyttsx3,
        test_speak_thread_swallows_engine_failure,
        test_export_to_file_success,
        test_export_to_file_failure_returns_false,
        test_export_to_file_without_pyttsx3_returns_false,
        test_export_to_file_no_matching_voice,
        test_text_to_speech_uses_default_temp_path,
        test_text_to_speech_respects_custom_path,
        test_speak_text_is_blocking,
        test_get_tts_engine_is_singleton,
    ]
    for t in tests:
        t()
    print("\nAll tts_engine tests passed!")


if __name__ == "__main__":
    main()
