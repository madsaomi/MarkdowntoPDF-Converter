from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class PomodoroDialog(QDialog):
    """Pomodoro timer dialog with work/break cycles."""

    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("🍅 Pomodoro Timer")
        self.setFixedSize(320, 280)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Settings
        settings_layout = QFormLayout()
        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 120)
        self.work_spin.setValue(25)
        self.work_spin.setSuffix(" min")
        settings_layout.addRow("Work:" if lang == "en" else "Работа:", self.work_spin)

        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 30)
        self.break_spin.setValue(5)
        self.break_spin.setSuffix(" min")
        settings_layout.addRow("Break:" if lang == "en" else "Перерыв:", self.break_spin)

        self.sessions_spin = QSpinBox()
        self.sessions_spin.setRange(1, 20)
        self.sessions_spin.setValue(4)
        settings_layout.addRow("Sessions:" if lang == "en" else "Сессии:", self.sessions_spin)
        layout.addLayout(settings_layout)

        # Status
        self.status_label = QLabel("🍅 Ready to start")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(self.status_label)

        # Progress
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet("""
            QProgressBar { border: 1px solid rgba(255,255,255,0.1); border-radius: 5px; background: rgba(51, 65, 85, 0.4); height: 20px; color: #e2e8f0; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #22d3ee); border-radius: 5px; }
        """)
        layout.addWidget(self.progress)

        # Timer label
        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Consolas", 32, QFont.Weight.Bold))
        layout.addWidget(self.time_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); color: white; font-weight: bold; padding: 8px 16px; border: none; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #047857,stop:1 #059669); }")
        self.btn_start.clicked.connect(self._toggle)
        btn_layout.addWidget(self.btn_start)

        self.btn_reset = QPushButton("⟳ Reset")
        self.btn_reset.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #475569,stop:1 #64748b); color: white; font-weight: bold; padding: 8px 16px; border: none; border-radius: 6px; } QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #334155,stop:1 #475569); }")
        self.btn_reset.clicked.connect(self._reset)
        btn_layout.addWidget(self.btn_reset)
        layout.addLayout(btn_layout)

        # Timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self._running = False
        self._is_work = True
        self._seconds_left = 0
        self._current_session = 0
        self._total_seconds = 0

    def _toggle(self):
        if self._running:
            self._timer.stop()
            self._running = False
            self.btn_start.setText("▶ Start" if self.lang == "en" else "▶ Старт")
        else:
            if self._seconds_left == 0:
                self._is_work = True
                self._current_session = 1
                self._total_seconds = self.work_spin.value() * 60
                self._seconds_left = self._total_seconds
            self._timer.start()
            self._running = True
            self.btn_start.setText("⏸ Pause" if self.lang == "en" else "⏸ Пауза")
            self.work_spin.setEnabled(False)
            self.break_spin.setEnabled(False)
            self.sessions_spin.setEnabled(False)

    def _reset(self):
        self._timer.stop()
        self._running = False
        self._seconds_left = 0
        self._is_work = True
        self._current_session = 0
        self.progress.setValue(0)
        self.time_label.setText("25:00")
        self.status_label.setText("🍅 Ready" if self.lang == "en" else "🍅 Готово")
        self.btn_start.setText("▶ Start" if self.lang == "en" else "▶ Старт")
        self.work_spin.setEnabled(True)
        self.break_spin.setEnabled(True)
        self.sessions_spin.setEnabled(True)

    def _tick(self):
        if self._seconds_left <= 0:
            self._timer.stop()
            self._running = False
            self._switch_phase()
            return

        self._seconds_left -= 1
        mins = self._seconds_left // 60
        secs = self._seconds_left % 60
        self.time_label.setText(f"{mins:02d}:{secs:02d}")

        elapsed = self._total_seconds - self._seconds_left
        pct = int((elapsed / max(1, self._total_seconds)) * 100)
        self.progress.setValue(pct)

    def _switch_phase(self):
        if self._is_work:
            # Work finished → break
            if self._current_session >= self.sessions_spin.value():
                self.status_label.setText("🎉 All sessions done!" if self.lang == "en" else "🎉 Все сессии завершены!")
                self.btn_start.setText("▶ Start" if self.lang == "en" else "▶ Старт")
                self.work_spin.setEnabled(True)
                self.break_spin.setEnabled(True)
                self.sessions_spin.setEnabled(True)
                return

            self._is_work = False
            self._total_seconds = self.break_spin.value() * 60
            self._seconds_left = self._total_seconds
            self.status_label.setText("☕ Break" if self.lang == "en" else "☕ Перерыв")
            self.progress.setStyleSheet("QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10b981); border-radius: 5px; }")
        else:
            # Break finished → work
            self._is_work = True
            self._current_session += 1
            self._total_seconds = self.work_spin.value() * 60
            self._seconds_left = self._total_seconds
            self.status_label.setText(f"🍅 Session {self._current_session}/{self.sessions_spin.value()}")
            self.progress.setStyleSheet("QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #60a5fa); border-radius: 5px; }")

        self._running = True
        self._timer.start()
