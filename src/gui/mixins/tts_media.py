"""TTS: озвучка текста, настройки и экспорт аудио.

Выделено из ``src/gui/window_tools.py`` (TASK-012/PLAN-012), тела вербатим.
"""

import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QMessageBox, QComboBox, QSlider,
)
from PyQt6.QtCore import Qt


class TtsMediaMixin:
    def text_to_speech_speak(self):
        text = self.live_editor.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "TTS", "No text to speak")
            return

        from src.core.tts_engine import strip_markdown_for_tts, get_tts_engine
        clean = strip_markdown_for_tts(text)
        engine = get_tts_engine()

        def on_state(state):
            icons = {"playing": "playing", "paused": "paused", "stopped": "stopped"}
            self.append_log(f"TTS: {icons.get(state, state)}")

        engine.set_on_state_change(on_state)

        if engine.is_playing():
            engine.stop()
            self.toast("TTS stopped", "info")
            return

        engine.speak(clean, lang=self.current_lang)
        self.toast("Playing...", "success")

    def show_tts_settings(self):
        from src.core.tts_engine import get_tts_engine
        engine = get_tts_engine()
        voices = engine.get_voices()

        dlg = QDialog(self)
        dlg.setWindowTitle("TTS Settings")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)

        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice:"))
        voice_combo = QComboBox()
        for v in voices:
            gender_icon = {"male": "male", "female": "female", "neutral": "neutral"}.get(v.gender.value, "")
            premium = " *" if v.is_premium else ""
            voice_combo.addItem(f"{v.name} ({v.language}){premium} - {v.description}", v.id)
        voice_layout.addWidget(voice_combo)
        layout.addLayout(voice_layout)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        speed_slider = QSlider(Qt.Orientation.Horizontal)
        speed_slider.setRange(50, 200)
        speed_slider.setValue(int(engine.settings.speed * 100))
        speed_label = QLabel(f"{engine.settings.speed:.1f}x")
        speed_slider.valueChanged.connect(lambda v: speed_label.setText(f"{v/100:.1f}x"))
        speed_layout.addWidget(speed_slider)
        speed_layout.addWidget(speed_label)
        layout.addLayout(speed_layout)

        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("Pitch:"))
        pitch_slider = QSlider(Qt.Orientation.Horizontal)
        pitch_slider.setRange(50, 200)
        pitch_slider.setValue(int(engine.settings.pitch * 100))
        pitch_label = QLabel(f"{engine.settings.pitch:.1f}")
        pitch_slider.valueChanged.connect(lambda v: pitch_label.setText(f"{v/100:.1f}"))
        pitch_layout.addWidget(pitch_slider)
        pitch_layout.addWidget(pitch_label)
        layout.addLayout(pitch_layout)

        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Volume:"))
        vol_slider = QSlider(Qt.Orientation.Horizontal)
        vol_slider.setRange(0, 100)
        vol_slider.setValue(int(engine.settings.volume * 100))
        vol_label = QLabel(f"{int(engine.settings.volume * 100)}%")
        vol_slider.valueChanged.connect(lambda v: vol_label.setText(f"{v}%"))
        vol_layout.addWidget(vol_slider)
        vol_layout.addWidget(vol_label)
        layout.addLayout(vol_layout)

        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Export to File")
        btn_export.clicked.connect(lambda: self._export_tts_audio(engine))
        btn_layout.addWidget(btn_export)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        def apply_settings():
            engine.set_voice(voice_combo.currentData())
            engine.set_speed(speed_slider.value() / 100)
            engine.set_pitch(pitch_slider.value() / 100)
            engine.set_volume(vol_slider.value() / 100)

        btn_export.clicked.connect(apply_settings)
        dlg.exec()

    def _export_tts_audio(self, engine):
        from src.core.tts_engine import strip_markdown_for_tts
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Audio", "speech.mp3",
            "MP3 (*.mp3);;WAV (*.wav);;All (*)"
        )
        if path:
            text = self.live_editor.toPlainText()
            clean = strip_markdown_for_tts(text)
            if engine.export_to_file(clean, path, self.current_lang):
                self.toast(f"Audio saved: {os.path.basename(path)}", "success")
            else:
                self.toast("Export failed", "error")

