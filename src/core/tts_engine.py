"""Advanced TTS Engine with multiple voices, effects, and audio export."""

import logging
import os
import re
import tempfile
import json
import threading
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger("MarkdownToPDF.tts")


class VoiceGender(Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"
    CHILD = "child"
    ELDERLY = "elderly"
    ROBOT = "robot"
    WHISPER = "whisper"
    NARRATOR = "narrator"


@dataclass
class VoiceProfile:
    """Represents a voice profile with settings."""
    id: str
    name: str
    language: str
    gender: VoiceGender
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    description: str = ""
    is_premium: bool = False
    accent: str = ""
    emotion: str = "neutral"


@dataclass
class TTSSettings:
    """TTS playback settings."""
    voice_id: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    pause_between_paragraphs: float = 0.5
    pause_between_sentences: float = 0.2
    enable_effects: bool = False
    echo_enabled: bool = False
    echo_delay: float = 0.3
    echo_decay: float = 0.5
    reverb_enabled: bool = False
    reverb_amount: float = 0.3
    chorus_enabled: bool = False
    chorus_depth: float = 0.2
    chorus_rate: float = 0.5
    flanger_enabled: bool = False
    pitch_shift: float = 0.0
    auto_emphasis: bool = False
    breathing_enabled: bool = False
    breathing_rate: float = 0.3


class AdvancedTTSEngine:
    """Advanced TTS engine with multiple voices and effects."""

    VOICES = [
        # Russian voices
        VoiceProfile("ru_male_1", "Алексей", "ru", VoiceGender.MALE, 1.0, 0.9,
                     description="Мужской голос, стандартный", accent="standard"),
        VoiceProfile("ru_female_1", "Анна", "ru", VoiceGender.FEMALE, 1.0, 1.1,
                     description="Женский голос, стандартный", accent="standard"),
        VoiceProfile("ru_male_2", "Дмитрий", "ru", VoiceGender.MALE, 0.9, 0.85,
                     description="Низкий мужской голос", accent="deep"),
        VoiceProfile("ru_female_2", "Елена", "ru", VoiceGender.FEMALE, 1.1, 1.15,
                     description="Быстрый женский голос", accent="fast"),
        VoiceProfile("ru_male_3", "Сергей", "ru", VoiceGender.MALE, 1.0, 0.95,
                     description="Новостной диктор", accent="news", emotion="formal"),
        VoiceProfile("ru_female_3", "Мария", "ru", VoiceGender.FEMALE, 0.95, 1.0,
                     description="Мягкий женский голос", accent="soft", emotion="calm"),
        VoiceProfile("ru_child_1", "Миша", "ru", VoiceGender.CHILD, 1.1, 1.3,
                     description="Детский голос", accent="child"),
        VoiceProfile("ru_elderly_1", "Виктор", "ru", VoiceGender.ELDERLY, 0.85, 0.8,
                     description="Зрелый мужской голос", accent="mature"),

        # English voices
        VoiceProfile("en_male_1", "James", "en", VoiceGender.MALE, 1.0, 1.0,
                     description="Male, standard", accent="american"),
        VoiceProfile("en_female_1", "Sarah", "en", VoiceGender.FEMALE, 1.0, 1.05,
                     description="Female, standard", accent="american"),
        VoiceProfile("en_male_2", "David", "en", VoiceGender.MALE, 0.85, 0.9,
                     description="Deep male voice", accent="british"),
        VoiceProfile("en_female_2", "Emma", "en", VoiceGender.FEMALE, 1.15, 1.1,
                     description="Fast female voice", accent="american"),
        VoiceProfile("en_male_3", "Oliver", "en", VoiceGender.MALE, 1.0, 1.0,
                     description="British male", accent="british"),
        VoiceProfile("en_female_3", "Charlotte", "en", VoiceGender.FEMALE, 0.95, 1.0,
                     description="British female", accent="british"),
        VoiceProfile("en_male_4", "Michael", "en", VoiceGender.MALE, 0.9, 0.85,
                     description="News anchor style", accent="american", emotion="formal"),
        VoiceProfile("en_female_4", "Sophia", "en", VoiceGender.FEMALE, 1.0, 1.1,
                     description="Warm female voice", accent="american", emotion="warm"),

        # Multi-language / AI voices
        VoiceProfile("ai_narrator", "Narrator", "multi", VoiceGender.NARRATOR, 0.95, 1.0,
                     description="AI Narrator, professional", is_premium=True, emotion="professional"),
        VoiceProfile("ai_storyteller", "Storyteller", "multi", VoiceGender.NARRATOR, 0.9, 0.95,
                     description="AI Storyteller, expressive", is_premium=True, emotion="expressive"),
        VoiceProfile("ai_news", "News Anchor", "multi", VoiceGender.NARRATOR, 1.0, 1.0,
                     description="News broadcast style", is_premium=True, emotion="formal"),
        VoiceProfile("ai_whisper", "Whisper", "multi", VoiceGender.WHISPER, 0.8, 1.2,
                     description="Whispered voice", is_premium=True, emotion="whisper"),
        VoiceProfile("ai_robot", "Robot", "multi", VoiceGender.ROBOT, 1.0, 0.5,
                     description="Robotic voice effect", is_premium=True, emotion="robotic"),
        VoiceProfile("ai_dramatic", "Dramatic", "multi", VoiceGender.NARRATOR, 0.85, 0.9,
                     description="Dramatic narration", is_premium=True, emotion="dramatic"),
    ]

    def __init__(self):
        self.settings = TTSSettings()
        self.engine = None
        self._is_playing = False
        self._is_paused = False
        self._current_text = ""
        self._playback_thread: Optional[threading.Thread] = None
        self._on_state_change: Optional[Callable] = None
        self._on_progress: Optional[Callable] = None
        self._bookmarks: list[dict] = []

    def get_voices(self, language: str = None) -> list[VoiceProfile]:
        """Get available voices, optionally filtered by language."""
        if language:
            return [v for v in self.VOICES if v.language == language or v.language == "multi"]
        return self.VOICES

    def set_voice(self, voice_id: str):
        """Set active voice."""
        self.settings.voice_id = voice_id

    def set_speed(self, speed: float):
        """Set playback speed (0.5 - 2.0)."""
        self.settings.speed = max(0.5, min(2.0, speed))

    def set_pitch(self, pitch: float):
        """Set voice pitch (0.5 - 2.0)."""
        self.settings.pitch = max(0.5, min(2.0, pitch))

    def set_volume(self, volume: float):
        """Set volume (0.0 - 1.0)."""
        self.settings.volume = max(0.0, min(1.0, volume))

    def set_pause_between_paragraphs(self, pause: float):
        """Set pause duration between paragraphs."""
        self.settings.pause_between_paragraphs = pause

    def set_echo(self, enabled: bool, delay: float = 0.3, decay: float = 0.5):
        """Enable/disable echo effect."""
        self.settings.echo_enabled = enabled
        self.settings.echo_delay = delay
        self.settings.echo_decay = decay

    def set_reverb(self, enabled: bool, amount: float = 0.3):
        """Enable/disable reverb effect."""
        self.settings.reverb_enabled = enabled
        self.settings.reverb_amount = amount

    def add_bookmark(self, position: int, label: str):
        """Add a bookmark at text position."""
        self._bookmarks.append({"position": position, "label": label})

    def clear_bookmarks(self):
        """Clear all bookmarks."""
        self._bookmarks.clear()

    def speak(self, text: str, lang: str = "ru"):
        """Speak text aloud (non-blocking)."""
        if self._is_playing:
            self.stop()

        self._current_text = text
        self._is_playing = True
        self._is_paused = False

        self._playback_thread = threading.Thread(
            target=self._speak_thread,
            args=(text, lang),
            daemon=True
        )
        self._playback_thread.start()

    def _speak_thread(self, text: str, lang: str):
        """Background thread for TTS playback."""
        try:
            import pyttsx3
            engine = pyttsx3.init()

            # Apply voice settings
            voices = engine.getProperty('voices')
            voice_id = self.settings.voice_id
            for voice in voices:
                if voice_id in voice.id.lower() or lang in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break

            engine.setProperty('rate', int(200 * self.settings.speed))
            engine.setProperty('volume', self.settings.volume)

            # Process text with pauses
            paragraphs = text.split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                if not self._is_playing:
                    break

                while self._is_paused:
                    if not self._is_playing:
                        break

                if paragraph.strip():
                    # Apply effects
                    processed = self._apply_effects(paragraph)
                    engine.say(processed)

                    if self._on_progress:
                        progress = (i + 1) / len(paragraphs)
                        self._on_progress(progress, paragraph[:50])

                # Pause between paragraphs
                if i < len(paragraphs) - 1:
                    import time
                    time.sleep(self.settings.pause_between_paragraphs)

            engine.runAndWait()

        except ImportError:
            logger.error("pyttsx3 not installed")
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self._is_playing = False
            self._is_paused = False
            if self._on_state_change:
                self._on_state_change("stopped")

    def _apply_effects(self, text: str) -> str:
        """Apply audio effects to text (placeholder for future implementation)."""
        # In future: apply echo, reverb, etc.
        return text

    def pause(self):
        """Pause playback."""
        self._is_paused = True
        if self._on_state_change:
            self._on_state_change("paused")

    def resume(self):
        """Resume playback."""
        self._is_paused = False
        if self._on_state_change:
            self._on_state_change("playing")

    def stop(self):
        """Stop playback."""
        self._is_playing = False
        self._is_paused = False
        if self._on_state_change:
            self._on_state_change("stopped")

    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._is_playing and not self._is_paused

    def is_paused(self) -> bool:
        """Check if paused."""
        return self._is_paused

    def export_to_file(self, text: str, output_path: str, lang: str = "ru") -> bool:
        """Export speech to audio file."""
        try:
            import pyttsx3
            engine = pyttsx3.init()

            voices = engine.getProperty('voices')
            for voice in voices:
                if lang in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break

            engine.setProperty('rate', int(200 * self.settings.speed))
            engine.setProperty('volume', self.settings.volume)

            engine.save_to_file(text, output_path)
            engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def get_estimated_duration(self, text: str) -> float:
        """Estimate speech duration in seconds."""
        words = len(text.split())
        words_per_second = 2.5 * self.settings.speed
        return words / words_per_second

    def set_on_state_change(self, callback: Callable):
        """Set state change callback."""
        self._on_state_change = callback

    def set_on_progress(self, callback: Callable):
        """Set progress callback."""
        self._on_progress = callback


def strip_markdown_for_tts(text: str) -> str:
    """Remove Markdown formatting for clean TTS output."""
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'```[\s\S]*?```', 'code block omitted', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# Legacy compatibility
def text_to_speech(text: str, lang: str = "ru", output_path: str = None) -> str:
    """Convert text to speech using pyttsx3. Returns path to audio file."""
    engine = AdvancedTTSEngine()
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "md2pdf_tts_output.mp3")
    engine.export_to_file(text, output_path, lang)
    return output_path


def speak_text(text: str, lang: str = "ru"):
    """Speak text aloud using pyttsx3 (blocking)."""
    import pyttsx3
    eng = pyttsx3.init()
    eng.say(text)
    eng.runAndWait()


def get_tts_engine() -> AdvancedTTSEngine:
    """Get singleton TTS engine instance."""
    if not hasattr(get_tts_engine, "_instance"):
        get_tts_engine._instance = AdvancedTTSEngine()
    return get_tts_engine._instance
