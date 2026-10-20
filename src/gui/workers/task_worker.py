"""Простой воркер на QThread для блокирующих задач.

Выполняет функцию в фоновом потоке, возвращает результат через сигналы.
"""

from PyQt6.QtCore import QObject, QThread, pyqtSignal


class TaskWorker(QObject):
    """Воркер для выполнения блокирующей функции в QThread."""

    started = pyqtSignal()
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self._thread = None

    def start(self):
        """Запускает воркер в новом QThread."""
        self._thread = QThread(self.parent())
        self.moveToThread(self._thread)
        self._thread.started.connect(self.run)
        self.finished.connect(self._thread.quit)
        self.finished.connect(self.deleteLater)
        self.error.connect(self._thread.quit)
        self.error.connect(self.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self.started.emit()
        self._thread.start()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class TaskThread:
    """Упрощённый API: TaskThread(fn, ...).start(on_finish=..., on_error=...)"""

    def __init__(self, fn, *args, **kwargs):
        self.worker = TaskWorker(fn, *args, **kwargs)
        self._on_finish = None
        self._on_error = None

    def start(self, on_finish=None, on_error=None, parent=None):
        if on_finish:
            self._on_finish = on_finish
            self.worker.finished.connect(on_finish)
        if on_error:
            self._on_error = on_error
            self.worker.error.connect(on_error)
        if parent is not None and self.worker.parent() is None:
            try:
                self.worker.setParent(parent)
            except Exception:
                pass
        self.worker.start()
        return self
