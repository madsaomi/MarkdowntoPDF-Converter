"""Поведенческие тесты gui/pomodoro.py и gui/welcome_tour.py.

Оба модуля — самодостаточные диалоги без внешних зависимостей, поэтому
проверяются целиком: настройки по умолчанию, логика таймера (старт, пауза,
сброс, переходы работа↔перерыв, финал), навигация по шагам тура и индикаторы.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QDialog

app = QApplication.instance() or QApplication([])

from src.gui.pomodoro import PomodoroDialog
from src.gui.welcome_tour import WelcomeTourDialog


# ─── Pomodoro: начальное состояние ───────────────────────────────────────────

def test_pomodoro_defaults():
    """Стартовые значения: 25/5/4, таймер не идёт, подпись 25:00."""
    d = PomodoroDialog()
    assert d.work_spin.value() == 25
    assert d.break_spin.value() == 5
    assert d.sessions_spin.value() == 4
    assert d.work_spin.minimum() == 1 and d.work_spin.maximum() == 120
    assert d.break_spin.maximum() == 30
    assert d.sessions_spin.maximum() == 20
    assert d.progress.value() == 0
    assert d.time_label.text() == "25:00"
    assert d._running is False
    assert d._seconds_left == 0
    print("[PASS] test_pomodoro_defaults")


def test_pomodoro_russian_button_label():
    """Русская локаль — «Старт»."""
    d = PomodoroDialog(lang="ru")
    assert d.btn_start.text() == "▶ Start"  # до перерисовки текст английский
    d._toggle()
    assert d.btn_start.text() == "⏸ Пауза"
    print("[PASS] test_pomodoro_russian_button_label")


# ─── Pomodoro: старт / пауза / сброс ────────────────────────────────────────

def test_pomodoro_start_begins_work_session():
    """Старт: первый рабочий интервал, поля настроек блокируются."""
    d = PomodoroDialog(lang="en")
    d._toggle()
    assert d._running is True
    assert d._seconds_left == 25 * 60
    assert d._total_seconds == 25 * 60
    assert d._is_work is True
    assert d._current_session == 1
    assert d.btn_start.text() == "⏸ Pause"
    assert d.work_spin.isEnabled() is False
    assert d.break_spin.isEnabled() is False
    assert d.sessions_spin.isEnabled() is False
    print("[PASS] test_pomodoro_start_begins_work_session")


def test_pomodoro_pause_keeps_remaining_time():
    """Пауза останавливает таймер и не сбрасывает оставшееся время."""
    d = PomodoroDialog(lang="en")
    d._toggle()
    d._seconds_left = 600
    d._toggle()
    assert d._running is False
    assert d._seconds_left == 600
    assert d.btn_start.text() == "▶ Start"

    # Повторный старт продолжает с того же места, а не с 25 минут
    d._toggle()
    assert d._running is True
    assert d._seconds_left == 600
    print("[PASS] test_pomodoro_pause_keeps_remaining_time")


def test_pomodoro_reset_restores_defaults():
    """Сброс возвращает подписи, прогресс и доступность полей."""
    d = PomodoroDialog(lang="ru")
    d._toggle()
    d._seconds_left = 42
    d.progress.setValue(70)
    d._reset()
    assert d._running is False
    assert d._seconds_left == 0
    assert d._is_work is True
    assert d._current_session == 0
    assert d.progress.value() == 0
    assert d.time_label.text() == "25:00"
    assert d.status_label.text() == "🍅 Готово"
    assert d.btn_start.text() == "▶ Старт"
    assert d.work_spin.isEnabled() is True
    assert d.break_spin.isEnabled() is True
    assert d.sessions_spin.isEnabled() is True
    print("[PASS] test_pomodoro_reset_restores_defaults")


def test_pomodoro_reset_english_labels():
    """Английская локаль в сбросе."""
    d = PomodoroDialog(lang="en")
    d._reset()
    assert d.status_label.text() == "🍅 Ready"
    assert d.btn_start.text() == "▶ Start"
    print("[PASS] test_pomodoro_reset_english_labels")


# ─── Pomodoro: тики и переходы фаз ──────────────────────────────────────────

def test_pomodoro_tick_formats_time_and_progress():
    """Тик уменьшает время, обновляет подпись и процент."""
    d = PomodoroDialog()
    d._total_seconds = 100
    d._seconds_left = 50
    d._tick()
    assert d._seconds_left == 49
    assert d.time_label.text() == "00:49"
    assert d.progress.value() == 51, d.progress.value()
    print("[PASS] test_pomodoro_tick_formats_time_and_progress")


def test_pomodoro_tick_with_long_interval():
    """Минуты и секунды форматируются двузначными числами."""
    d = PomodoroDialog()
    d._total_seconds = 25 * 60
    d._seconds_left = 20 * 60 + 5
    d._tick()
    assert d.time_label.text() == "20:04"
    print("[PASS] test_pomodoro_tick_with_long_interval")


def test_pomodoro_work_finishes_into_break():
    """Окончание работы переключает на перерыв и перезапускает таймер."""
    d = PomodoroDialog()
    d.break_spin.setValue(7)
    d._running = True
    d._is_work = True
    d._current_session = 1
    d._seconds_left = 0
    d._tick()
    assert d._is_work is False
    assert d._seconds_left == 7 * 60
    assert d._total_seconds == 7 * 60
    assert d.status_label.text() == "☕ Перерыв"
    assert d._running is True
    assert d._timer.isActive() is True
    print("[PASS] test_pomodoro_work_finishes_into_break")


def test_pomodoro_break_finishes_into_next_session():
    """Окончание перерыва увеличивает номер сессии и возвращает работу."""
    d = PomodoroDialog()
    d.work_spin.setValue(10)
    d.sessions_spin.setValue(4)
    d._running = True
    d._is_work = False
    d._current_session = 1
    d._seconds_left = 0
    d._tick()
    assert d._is_work is True
    assert d._current_session == 2
    assert d._seconds_left == 10 * 60
    assert d.status_label.text() == "🍅 Session 2/4"
    assert d._running is True
    print("[PASS] test_pomodoro_break_finishes_into_next_session")


def test_pomodoro_last_session_completes_cycle():
    """После последней сессии цикл завершается без нового интервала."""
    d = PomodoroDialog(lang="ru")
    d.sessions_spin.setValue(3)
    d._running = True
    d._is_work = True
    d._current_session = 3
    d._seconds_left = 0
    d._tick()
    assert d.status_label.text() == "🎉 Все сессии завершены!"
    assert d.btn_start.text() == "▶ Старт"
    assert d._running is False
    assert d._timer.isActive() is False
    assert d.work_spin.isEnabled() is True
    assert d.break_spin.isEnabled() is True
    assert d.sessions_spin.isEnabled() is True
    print("[PASS] test_pomodoro_last_session_completes_cycle")


def test_pomodoro_last_session_completes_cycle_english():
    """Английская подпись завершения цикла."""
    d = PomodoroDialog(lang="en")
    d.sessions_spin.setValue(1)
    d._is_work = True
    d._current_session = 1
    d._seconds_left = 0
    d._tick()
    assert d.status_label.text() == "🎉 All sessions done!"
    print("[PASS] test_pomodoro_last_session_completes_cycle_english")


# ─── Welcome tour: структура и навигация ────────────────────────────────────

def test_tour_steps_are_complete():
    """Все шаги имеют иконку, заголовок, описание и цвет."""
    assert len(WelcomeTourDialog.STEPS) == 6
    for step in WelcomeTourDialog.STEPS:
        assert set(step) == {"icon", "title", "desc", "color"}
        assert step["icon"] and step["title"] and step["desc"]
        assert step["color"].startswith("#")
    print("[PASS] test_tour_steps_are_complete")


def _tour(lang="ru"):
    """Создаёт и показывает тур.

    ``isVisible()`` дочернего виджета всегда ``False``, пока не показан сам
    диалог, поэтому все проверки видимости идут через показанное окно.
    """
    d = WelcomeTourDialog(lang=lang)
    d.show()
    app.processEvents()
    return d


def test_tour_initial_state():
    """Тур открывается на первом шаге; «Назад» скрыта."""
    d = _tour(lang="ru")
    assert d.windowTitle() == "Тур"
    assert d.stack.count() == 6
    assert d._current == 0
    assert d.stack.currentIndex() == 0
    assert d.btn_prev.isVisible() is False
    assert d.btn_skip.isVisible() is True
    assert d.btn_next.text() == "Далее →"
    assert len(d.dots) == 6
    print("[PASS] test_tour_initial_state")


def test_tour_english_titles():
    """Английские подписи кнопок."""
    d = _tour(lang="en")
    assert d.windowTitle() == "Welcome Tour"
    assert d.btn_prev.text() == "← Back"
    assert d.btn_next.text() == "Next →"
    assert d.btn_skip.text() == "Skip"
    print("[PASS] test_tour_english_titles")


def test_tour_next_advances_through_steps():
    """«Далее» листает шаги и показывает «Назад»."""
    d = _tour(lang="ru")
    d._next()
    assert d._current == 1
    assert d.stack.currentIndex() == 1
    assert d.btn_prev.isVisible() is True
    assert d.btn_next.text() == "Далее →"

    d._next()
    assert d._current == 2
    print("[PASS] test_tour_next_advances_through_steps")


def test_tour_last_step_shows_start_and_hides_skip():
    """На последнем шаге кнопка меняется на «Начать!», «Пропустить» скрыта."""
    d = _tour(lang="ru")
    for _ in range(5):
        d._next()
    assert d._current == 5
    assert d.btn_next.text() == "Начать!"
    assert d.btn_skip.isVisible() is False
    print("[PASS] test_tour_last_step_shows_start_and_hides_skip")


def test_tour_last_step_english_label():
    """Английская кнопка последнего шага — «Start!»."""
    d = _tour(lang="en")
    for _ in range(5):
        d._next()
    assert d.btn_next.text() == "Start!"
    print("[PASS] test_tour_last_step_english_label")


def test_tour_next_on_last_step_accepts_dialog():
    """На последнем шаге «Далее» закрывает тур с результатом Accepted."""
    d = _tour()
    d._current = len(d.STEPS) - 1
    d._next()
    assert d.result() == QDialog.DialogCode.Accepted
    print("[PASS] test_tour_next_on_last_step_accepts_dialog")


def test_tour_prev_steps_back_and_stops_at_first():
    """«Назад» листает назад и не уходит за первый шаг."""
    d = _tour()
    for _ in range(3):
        d._next()
    d._prev()
    assert d._current == 2
    assert d.stack.currentIndex() == 2
    for _ in range(5):
        d._prev()
    assert d._current == 0
    assert d.btn_prev.isVisible() is False
    print("[PASS] test_tour_prev_steps_back_and_stops_at_first")


def test_tour_dot_highlight_follows_current_step():
    """Активная точка окрашена тем же цветом, что и при создании."""
    d = _tour()
    initial = d.dots[0].styleSheet()
    d._next()
    assert "#8b5cf6" in d.dots[1].styleSheet(), d.dots[1].styleSheet()
    assert "#4a4a6a" in d.dots[0].styleSheet(), d.dots[0].styleSheet()
    # Возврат на первый шаг даёт ровно тот же цвет, что был изначально
    d._prev()
    assert d.dots[0].styleSheet() == initial, (d.dots[0].styleSheet(), initial)
    print("[PASS] test_tour_dot_highlight_follows_current_step")


def test_tour_skip_closes_dialog():
    """«Пропустить» закрывает диалог."""
    d = _tour()
    d.btn_skip.click()
    assert not d.isVisible()
    print("[PASS] test_tour_skip_closes_dialog")


def main():
    tests = [
        test_pomodoro_defaults,
        test_pomodoro_russian_button_label,
        test_pomodoro_start_begins_work_session,
        test_pomodoro_pause_keeps_remaining_time,
        test_pomodoro_reset_restores_defaults,
        test_pomodoro_reset_english_labels,
        test_pomodoro_tick_formats_time_and_progress,
        test_pomodoro_tick_with_long_interval,
        test_pomodoro_work_finishes_into_break,
        test_pomodoro_break_finishes_into_next_session,
        test_pomodoro_last_session_completes_cycle,
        test_pomodoro_last_session_completes_cycle_english,
        test_tour_steps_are_complete,
        test_tour_initial_state,
        test_tour_english_titles,
        test_tour_next_advances_through_steps,
        test_tour_last_step_shows_start_and_hides_skip,
        test_tour_last_step_english_label,
        test_tour_next_on_last_step_accepts_dialog,
        test_tour_prev_steps_back_and_stops_at_first,
        test_tour_dot_highlight_follows_current_step,
        test_tour_skip_closes_dialog,
    ]
    for t in tests:
        t()
    print("\nAll pomodoro/welcome-tour tests passed!")


if __name__ == "__main__":
    main()
