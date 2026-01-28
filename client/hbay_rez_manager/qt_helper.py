from qtpy import QtCore, QtWidgets, QtGui
from ayon_core import style

class ProgressSignalWrapper(QtCore.QObject):
    progress_changed = QtCore.Signal(int, str)
    finished = QtCore.Signal()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.controller.progress_callback = self.progress_changed.emit

    @QtCore.Slot()
    def run(self):
        self.controller.run()
        self.finished.emit()

class ProgressBarDialog(QtWidgets.QDialog):
    def __init__(self, worker: ProgressSignalWrapper, window_title: str = "Installing...", parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(window_title)
        self.setModal(True)  # Blocks the rest of the UI
        self._first_show = True
        self.worker = worker
        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel("Starting...")
        layout.addWidget(self.label)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Connect signals from worker
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.finished.connect(self.accept)  # close dialog when done

    @QtCore.Slot(int, str)
    def update_progress(self, progress, message):
        self.progress_bar.setValue(progress)
        self.label.setText(message)

    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            # Set stylesheet, resize and move window
            self.setStyleSheet(style.load_stylesheet())
            self.resize(500, 100)
            current_pos = self.pos()
            new_pos = QtCore.QPoint(current_pos.x(), current_pos.y() - 300)
            self.move(new_pos)