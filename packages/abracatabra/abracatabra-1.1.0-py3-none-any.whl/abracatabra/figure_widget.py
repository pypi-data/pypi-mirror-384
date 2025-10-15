from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from typing import Callable


class FigureWidget(QtWidgets.QWidget):
    """
    A Qt widget that contains a matplotlib figure canvas with an optional toolbar.
    Inherits from `QWidget`.

    Methods:
        `update_figure`: Updates the figure canvas if anything has changed.
        `show_toolbar`: Show or hide the navigation toolbar.
    """

    def __init__(self, blit: bool = False, include_toolbar: bool = True, parent=None):
        """
        Initializes the FigureWidget. This creates a matplotlib figure canvas
        and optionally includes a navigation toolbar.

        Args:
            blit (bool): If True, enables blitting for faster rendering.
            include_toolbar (bool): If True, includes a navigation toolbar
                with the canvas.
            parent: The parent widget for this widget.
        """
        super().__init__(parent)
        self.blit = blit
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = FigureCanvas()
        self.figure = self.canvas.figure
        # self.figure.set_layout_engine('tight') # slows down rendering ~2x
        # self.figure.tight_layout() # does not seem to do anything here
        layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setMaximumHeight(25)
        layout.addWidget(self.toolbar)
        self.toolbar.setVisible(include_toolbar)

        self.setLayout(layout)

        self._update_callback: Callable[[int], None] = lambda i: None

    def update_figure(self, callback_idx: int = 0) -> None:
        """
        Updates the figure canvas if anything has changed. If blitting is
        enabled, it will only redraw the parts of the figure that have changed.
        If not, it will redraw the entire canvas. NOTE that blitting requires
        the user to manage the background and artist updates manually, i.e., the
        user must call `canvas.copy_from_bbox()` and `canvas.restore_region()`
        at the appropriate times AND ensure that the artists are drawn before
        calling this method.

        Args:
            callback_idx (int): An index passed to the registered animation
                callback function. This index is intended to specify which frame
                of the animation to draw, if an animation callback has been
                registered.
        """
        self._update_callback(callback_idx)
        if not self.figure.stale:
            return
        if self.blit:
            self.canvas.blit()
        else:
            self.canvas.draw_idle()
        self.canvas.flush_events()

    def show_toolbar(self, show: bool = True) -> None:
        """
        Show or hide the navigation toolbar.

        Args:
            show (bool): If True, shows the toolbar. If False, hides it.
        """
        self.toolbar.setVisible(show)

    def register_animation_callback(self, callback: Callable[[int], None]) -> None:
        """
        Registers a callback function for how to update the figure during an
        animation. Note that if the figure has multiple axes or artists, the
        user is responsible for managing the updates to all of those objects in
        the callback function (callback is per figure not per axis/artist).

        Args:
            callback (Callable[[int], None]): A function specifying how to update
                the widget. The function should take a single integer argument,
                which is the index of the current frame in the animation to draw.
                Registering callbacks allows abracatabra to better manage the
                timing of updates.
        """
        self._update_callback = callback
