from matplotlib.backends.qt_compat import QtWidgets
from typing import Callable


class CustomWidget(QtWidgets.QWidget):
    def __init__(self, widget: QtWidgets.QWidget, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget, stretch=1)
        self.setLayout(layout)

        def callback(idx: int = 0) -> None:
            return

        self.update_widget = callback

    def register_animation_callback(self, callback: Callable[[int], None]) -> None:
        """
        Registers a callback function for how to update the custom widget during
        an animation.

        Args:
            callback (Callable[[int], None]): A function specifying how to update
                the widget. The function should take a single integer argument,
                which is the index of the current frame in the animation to draw.
                Registering callbacks allows abracatabra to better manage the
                timing of updates.
        """
        self.update_widget = callback
