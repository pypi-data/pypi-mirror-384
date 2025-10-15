# system imports
import signal
import sys
import os
import time
import random
from typing import Callable

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

from matplotlib.figure import Figure
from matplotlib.backends.qt_compat import QtWidgets, QtGui

# Fix plot font types to work in paper sumbissions (Don't use type 3 fonts)
import matplotlib

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

from .custom_widget import CustomWidget
from .figure_widget import FigureWidget
from .tabbed_figure_widget import TabbedFigureWidget
from .tab_group_container import TabGroupContainer

# if sys.modules.get('IPython') is not None:
try:
    from IPython.core.getipython import get_ipython

    _ipython = get_ipython()
except ImportError:
    _ipython = None

if _ipython is not None:
    from IPython.utils.capture import capture_output

    with capture_output() as captured:  # suppress output
        # register IPython event loop to Qt - prevents need to call app.exec()
        _ipython.run_line_magic("gui", "qt")

    # SIGINT handles ctrl+c. The following lines allow it to kill without errors.
    # Using sys.exit(0) in IPython stops script execution, but not the kernel.
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
else:
    # Use SIG_DFL (default) rather than letting Qt handle ctrl+c.
    # Qt throws a KeyboardInterrupt exception, but only when the mouse hovers
    # over the window or some other Qt action causes events to process.
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def is_interactive() -> bool:
    """
    Check if the current environment is interactive (e.g., IPython or Jupyter).

    Returns:
        out (bool): True if the environment is interactive, False otherwise.
    """
    return bool(_ipython)


icon_dir = os.path.join(os.path.dirname(__file__), "icons")
# icon_files = ['tabplot.svg'] + [f'abracatabra{i}.svg' for i in range(1, 4)]
icon_files = ["tabplot.svg", f"abracatabra{random.choice([1, 2, 3])}.svg"]
icon_paths = [os.path.join(icon_dir, icon) for icon in icon_files]


class TabbedPlotWindow:
    """
    A class to create a tabbed plot window where the tabs are matplotlib
    figures. The window can also be divided into multiple tab groups, each
    containing multiple tabs.

    Attributes:
        `id`: Unique identifier for the window.
        `tab_groups`: A container for the tab groups in the window. Can be
            accessed like a 2D array, e.g. `window.tab_groups[0, 0]` for the
            tab group in the first row and first column.
    Methods:
        `add_figure_tab`: Method to add a new figure tab to the window.
        `add_custom_tab`: Method to add a new custom widget tab to the window.
        `register_animation_callback`: Method to register a callback function for
            how to update the figure or custom widget in a tab.
        `update`: Method to update the figure on the active tab.
        `set_size`: Method to set the size of the window in either pixels or a
            percentage of the screen.
        `apply_tight_layout`: Applies a tight layout to the figure in each tab.
        `enable_tab_autohide`: Enables auto-hiding of tabs in the window.
        `set_tab_position`: Sets the position of the tab bar in the window.
        `set_tab_fontsize`: Sets the font size of the tab labels in the window.
    Static Methods:
        `show_all`: Shows all created windows.
        `update_all`: Updates all created windows.
        `get_screen_size`: Returns the size of the screen in pixels.
    """

    _app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    _registry: dict[str, Self] = {}
    _latest_id = None
    _count = 0
    # _icons = [QtGui.QIcon(icon) for icon in icon_paths]
    _icon1 = QtGui.QIcon(icon_paths[0])
    _icon2 = QtGui.QIcon(icon_paths[1])

    def __new__(
        cls,
        window_id: str | int | None = None,
        nrows: int | list[int] = 1,
        ncols: int | list[int] = 1,
        size: tuple[int | float, int | float] = (0.6, 0.8),
        open_window: bool = True,
        autohide_tabs: bool = False,
        tab_position: str = "top",
        tab_fontsize: int = 8,
    ) -> Self:
        if window_id is None:
            # Generate a unique identifier if none is provided
            id_ = str(len(cls._registry) + 1)
            while id_ in cls._registry:
                id_ = str(int(id_) + 1)
        else:
            id_ = str(window_id)

        # Return instance if it exists
        if id_ in cls._registry:
            return cls._registry[id_]

        # Create a new instance if it does not exist
        instance = super().__new__(cls)
        cls._registry[id_] = instance
        cls._latest_id = id_
        cls._count += 1
        return instance

    def __init__(
        self,
        window_id: str | int | None = None,
        nrows: int | list[int] = 1,
        ncols: int | list[int] = 1,
        size: tuple[int | float, int | float] = (0.6, 0.8),
        open_window: bool = True,
        autohide_tabs: bool = False,
        tab_position: str = "top",
        tab_fontsize: int = 8,
    ):
        """
        Creates a new tabbed plot window with the given ID and size. If a window
        with the same ID already exists, it will return that instance instead of
        creating a new one. Only nrows or ncols can be a list, not both.

        Args:
            window_id (str|int|None): The ID of the window. If None, a unique ID
                will be created based on the number of existing windows.
            nrows (int|list[int]): The number of rows of tab groups. If a list,
                specifies the number of columns in each row, e.g. nrows=[1,2]
                would have 1 row in the first column and 2 rows in the second
                column.
            ncols (int|list[int]): The number of columns of tab groups. If a
                list, specifies the number of rows in each column,
                e.g. ncols=[1,2] would have 1 column in the first row and 2
                columns in the second row.
            size (tuple[int|float, int|float]): Size of the window (width, height).
                If an int, the value will be treated as pixels. If a float, it will be
                treated as a percentage of the screen size (based on your
                PRIMARY DISPLAY).
            open_window (bool): If True, the window will be displayed
                immediately after creation. Otherwise, it will be hidden until
                another method is called to show it.
            autohide_tabs (bool): If True, the tab bar will auto-hide when there
                is only one tab in a tab group.
            tab_position (str): The position of the tab bar. This can be 'top',
                'bottom', 'left', or 'right' as well as 'north', 'south',
                'east', or 'west' (logic only looks at first character).
            tab_fontsize (int): The font size of the tab labels.
        """
        if hasattr(self, "id"):
            return
        # super().__init__()
        self.qt = QtWidgets.QMainWindow()
        self.id = str(self._latest_id)
        self.qt.setWindowTitle(f"Plot Window: {self.id}")
        self.set_size(size)
        self.qt.setWindowIcon(TabbedPlotWindow._icon1)
        main_widget = QtWidgets.QWidget()
        self.qt.setCentralWidget(main_widget)

        row_major = True
        tab_groups = []
        if isinstance(nrows, int) and isinstance(ncols, int):
            ## create a grid layout with nrows x ncols
            main_layout = QtWidgets.QGridLayout(main_widget)
            if nrows < 1 or ncols < 1:
                raise ValueError(
                    f"Can not have {nrows} rows or {ncols} columns. Must be at least 1."
                )
            for r in range(nrows):
                row: list[TabbedFigureWidget] = []
                for c in range(ncols):
                    main_layout.setColumnStretch(c, 1)
                    widget = TabbedFigureWidget(
                        autohide_tabs, tab_position, tab_fontsize
                    )
                    row.append(widget)
                    main_layout.addWidget(widget, r, c)
                tab_groups.append(row)
        elif isinstance(ncols, list):
            ## create a vertical layout nested with horizontal layouts
            if isinstance(nrows, list):
                raise ValueError("Either nrows or ncols can be a list, not both.")
            main_layout = QtWidgets.QVBoxLayout(main_widget)
            for r in ncols:
                if r < 1:
                    raise ValueError(f"Can not have {r} columns. Must be at least 1.")
                widget_row = QtWidgets.QWidget()
                hlayout = QtWidgets.QHBoxLayout(widget_row)
                hlayout.setContentsMargins(0, 0, 0, 0)
                row = []
                for c in range(r):
                    widget = TabbedFigureWidget(
                        autohide_tabs, tab_position, tab_fontsize
                    )
                    row.append(widget)
                    hlayout.addWidget(widget)
                tab_groups.append(row)
                main_layout.addWidget(widget_row)
        elif isinstance(nrows, list):
            ## create a horizontal layout nested with vertical layouts
            if isinstance(ncols, list):
                raise ValueError("Either nrows or ncols can be a list, not both.")
            row_major = False
            main_layout = QtWidgets.QHBoxLayout(main_widget)
            for c in nrows:
                if c < 1:
                    raise ValueError(f"Can not have {c} columns. Must be at least 1.")
                widget_col = QtWidgets.QWidget()
                vlayout = QtWidgets.QVBoxLayout(widget_col)
                vlayout.setContentsMargins(0, 0, 0, 0)
                col = []
                for r in range(c):
                    widget = TabbedFigureWidget(
                        autohide_tabs, tab_position, tab_fontsize
                    )
                    col.append(widget)
                    vlayout.addWidget(widget)
                tab_groups.append(col)
                main_layout.addWidget(widget_col)
        else:
            raise ValueError("Invalid values for `nrows` and `ncols`")
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_groups = TabGroupContainer(tab_groups, row_major)

        # Register close event handler
        self.qt.closeEvent = self.close_event

        if open_window:
            self.qt.show()

    def add_figure_tab(
        self,
        tab_id: str,
        blit: bool = False,
        include_toolbar: bool = True,
        row: int = 0,
        col: int = 0,
    ) -> Figure:
        """
        Adds a new tab to the window with the given ID and returns the Figure
        created for that tab. If a tab with the same ID already exists, the
        existing Figure will be returned instead of creating a new one.

        Args:
            tab_id (str): The ID of the tab.
            blit (bool): Whether blitting will be used with the Figure in this
                tab. If True, you are responsible for managing the background
                and updating individual artists.
            include_toolbar (bool): Whether to display a matplotlib toolbar with
                the Figure in this tab.
            row (int): The row index of the tab group to add the tab to.
            col (int): The column index of the tab group to add the tab to.
        Returns:
            figure (Figure): The matplotlib figure in this tab.
        Notes
        -----
        Can alternatively call `add_figure_tab` directly on a tab group:
        ```python
        window = TabbedPlotWindow(ncols=2)
        fig_left = window.add_figure_tab("left", row=0, col=0)
        fig_right = window.tab_groups[0, 1].add_figure_tab("right")
        ```
        """
        fig_tab_widget = self.tab_groups[row, col]
        figure = fig_tab_widget.add_figure_tab(tab_id, blit, include_toolbar)
        return figure

    def add_custom_tab(
        self,
        widget: QtWidgets.QWidget,
        tab_id: str | int,
        row: int = 0,
        col: int = 0,
    ) -> None:
        """
        Adds a new tab, containing the provided widget, to the window with the
        given ID as the tab label. The ID must be unique within the tab group.

        Args:
            widget (QWidget): The custom Qt widget to add as a tab.
            tab_id (str): The ID of the tab.
            row (int): The row index of the tab group to add the tab to.
            col (int): The column index of the tab group to add the tab to.
        Notes
        -----
        Can alternatively call `add_custom_tab` directly on a tab group:
        ```python
        window = TabbedPlotWindow(ncols=2)
        tab_left = window.add_custom_tab("left", widget, row=0, col=0)
        tab_right = window.tab_groups[0, 1].add_custom_tab("right", widget)
        ```
        """
        tab_widget = self.tab_groups[row, col]
        tab_widget.add_custom_tab(widget, tab_id)
        return

    def register_animation_callback(
        self, callback: Callable[[int], None], tab_id: str, row: int = 0, col: int = 0
    ) -> None:
        """
        Registers a callback function for how to update the figure or the custom
        widget in the specified tab during an animation.

        Args:
            tab_id (str): The ID/title of the tab.
            callback (Callable[[int], None]): A function specifying how to update
                the widget. The function should take a single integer argument,
                which is the index of the current frame in the animation to draw.
                Registering callbacks allows abracatabra to better manage the
                timing of updates.
            row (int): The row index of the tab group containing the tab.
            col (int): The column index of the tab group containing the tab.
        """
        tab_widget = self.tab_groups[row, col][tab_id]
        tab_widget.register_animation_callback(callback)
        return

    def update(self, callback_idx: int = 0) -> None:
        """
        This will update the figure on the active (visible) tabs. Similar to
        pyplot.pause(), but for the current tab on this window. No additional
        time delay is added to the function, so it will return immediately after
        updating the figure.
        """
        if not self.qt.isVisible():
            self.qt.show()
        for tabs in self.tab_groups:
            active_tab_idx = tabs.currentIndex()
            active_widget = tabs.widget(active_tab_idx)
            if isinstance(active_widget, FigureWidget):
                active_widget.update_figure(callback_idx)
            elif isinstance(active_widget, CustomWidget):
                active_widget.update_widget(active_tab_idx)

    def close_event(self, event: QtGui.QCloseEvent) -> None:
        """
        Qt event function - DO NOT CALL DIRECTLY.

        This method is called when the window is closed. It will remove the
        window from the list of windows and check if there are any other windows
        open. If not, it will exit the application.
        """
        event.accept()
        # self.qt.closeEvent(event)
        del TabbedPlotWindow._registry[self.id]
        TabbedPlotWindow._count -= 1
        # if TabbedPlotWindow._count == 0:
        #     self._app.quit()

    def set_size(self, size: tuple[int | float, int | float]) -> None:
        """
        Sets the size of the window in either pixels or a percentage of the
        screen.

        Args:
            size (tuple[int|float, int|float]): Size of the window (width, height).
                If an int, the value will be treated as pixels. If a float,
                it will be treated as a percentage of the screen size.
        """
        width, height = size
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid size: {size}. Values must be positive.")
        screen_size = self.qt.screen().size()
        screen_width, screen_height = screen_size.width(), screen_size.height()
        if isinstance(width, float):
            if width > 1.0:
                raise ValueError(f"Width percentage {width} must be between 0 and 1.")
            width = int(screen_width * width)
        if isinstance(height, float):
            if height > 1.0:
                raise ValueError(f"Height percentage {height} must be between 0 and 1.")
            height = int(screen_height * height)
        width = min(width, screen_width)
        height = min(height, screen_height)
        self.qt.resize(width, height)

    def apply_tight_layout(self):
        """
        Applies a tight layout to the figure in each tab of the window, even if
        they are not the active Figure. Same as calling figure.tight_layout()
        directly on each Figure.
        """
        for tabs in self.tab_groups:
            current_index = tabs.currentIndex()
            for i in range(tabs.count()):
                tab = tabs.widget(i)
                if not isinstance(tab, FigureWidget):
                    continue
                tabs.setCurrentIndex(i)  # tab has to be active to apply tight layout
                tab.figure.tight_layout()
                tab.update_figure()
            tabs.setCurrentIndex(current_index)

    def enable_tab_autohide(self, enable: bool = True) -> None:
        """
        Enables auto-hiding of tabs in the window. This will hide the tab bar
        when there is only one tab in a tab group.

        Args:
            enable (bool): Whether to enable auto-hiding of tabs.
        """
        for tabs in self.tab_groups:
            tabs.setTabBarAutoHide(enable)

    def set_tab_position(self, position: str) -> None:
        """
        Sets the position of the tab bar in the window.

        Args:
            position (str): The position of the tab bar. This can be 'top',
                'bottom', 'left', or 'right' as well as 'north', 'south',
                'east', or 'west' (logic only looks at first character).
        """
        for tabs in self.tab_groups:
            tabs.set_tab_position(position)

    def set_tab_fontsize(self, fontsize: int) -> None:
        """
        Sets the font size of the tab labels in the window.

        Args:
            fontsize (int): The font size of the tab labels.
        """
        for tabs in self.tab_groups:
            tabs.set_tab_fontsize(fontsize)

    @staticmethod
    def show_all(tight_layout: bool = False, block: bool | None = None) -> None:
        """
        Shows all created windows.

        Args:
            tight_layout (bool): If True, applies a tight layout to all figures.
            block (bool): If True, block and run the GUI until all windows are
                closed, either individually or by pressing <ctrl+c> in the
                terminal. If False, the function returns immediately after
                showing the windows and you are responsible for ensuring the GUI
                event loop is running (interactive environments do this for you).
                Defaults to False in interactive environments, otherwise True.
        """
        for key in list(TabbedPlotWindow._registry.keys()):
            if not key in TabbedPlotWindow._registry:
                continue  # in case window was closed during iteration
            window = TabbedPlotWindow._registry[key]
            if not window.qt.isVisible():
                window.qt.show()
            if tight_layout:
                window.apply_tight_layout()
        if block is None:
            block = not is_interactive()
        if not block:
            return
        if TabbedPlotWindow._count > 0 and TabbedPlotWindow._app is not None:
            try:
                TabbedPlotWindow._app.exec()  # type: ignore
            except:
                TabbedPlotWindow._app.exec_()  # for compatibility with Qt5

    @staticmethod
    def update_all(delay_seconds: float, callback_idx: int = 0) -> float:
        """
        Updates all created windows. This is similar to pyplot.pause() and is
        generally used to update the figure in a loop, e.g., an animation. This
        function only updates active tabs in each window, so inactive tabs are
        skipped to save time.

        Args:
            delay_seconds (float): The minimum delay in seconds before returning.
                If windows are updated faster than this, this function will
                block until `delay_seconds` seconds have passed. If the windows
                take longer than `delay_seconds` seconds to update, the function
                execution time will be greater than `delay_seconds`.
        Returns:
            update_time (float): The amount of time (seconds) taken to update
                the windows.
        """
        start = time.perf_counter()
        for key in list(TabbedPlotWindow._registry.keys()):
            if not key in TabbedPlotWindow._registry:
                continue  # in case window was closed during iteration
            window = TabbedPlotWindow._registry[key]
            window.update(callback_idx)
        update_time = time.perf_counter() - start
        if TabbedPlotWindow._count > 0:
            remaining_delay = max(delay_seconds - update_time, 0.0)
            time.sleep(remaining_delay)
        return update_time

    @staticmethod
    def animate_all(
        frames: int,
        ts: float,
        step: int = 1,
        speed_scale: float = 1.0,
        print_timing: bool = False,
        hold: bool = True,
    ) -> None:
        """
        Animates all created windows by repeatedly calling `update_all()` in a
        loop for the given number of frames. This is a convenience function for
        simple animations. For this to work well, you should have already
        registered animation callbacks for each tab that will be animated.

        Args:
            frames (int): The number of frames to animate.
            ts (float): The time step between frames in seconds. The intention
                is that this time step matches real time, e.g., a simulation
                that saves data every `ts` seconds.
            step (int): The step size between frames. For example, if you want
                to animate every 2nd frame, set step=2. This is useful if your
                animation is running slower than real time and you want to draw
                batches of data between a single frame.
            speed_scale (float): A scaling factor for the speed of the animation.
                For example, if speed_scale=2.0, the animation will run twice as
                fast (i.e., half the time step between frames), meaning that a
                10 sec simulation should take 5 sec to animate.
            print_timing (bool): If True, prints timing information for each frame,
                inluding the running animation time and wall time. Also prints hints
                after the animation is done on how to improve performance if the
                animation is running slower than real time.
            hold (bool): Specify whether to keep the windows open (blocking code)
                at the last frame when the animation is complete. Essentially
                whether to call `show_all()` at the end or not.
        """
        if frames < 1 or step < 1:
            raise ValueError("Frames and step must be positive integers.")
        if ts <= 0 or speed_scale <= 0:
            raise ValueError("Time step and speed scale must be positive values.")
        if step / frames > 0.01:
            print("Warning: `step` is larger than 1% of `frames`.")

        start = time.perf_counter()
        for i in range(0, frames, step):
            delay = ts * step / speed_scale
            TabbedPlotWindow.update_all(delay, i)

            if not print_timing:
                continue

            elapsed = time.perf_counter() - start
            print(
                f"animation time: {i*ts:.2f}s",
                f"real time: {elapsed:.2f}s",
                sep=" | ",
                end="\r",
            )
        # Ensure the final frame is drawn
        TabbedPlotWindow.update_all(0.0, frames - 1)

        if print_timing:
            print()  # newline after final frame printout

        real_time = time.perf_counter() - start
        sim_time = frames * ts
        actual_speed_scale = sim_time / real_time
        buffer_percent = 10.0
        percent_error = (speed_scale - actual_speed_scale) / speed_scale * 100.0
        if percent_error > buffer_percent:
            print("Your computer is not keeping up with the requested speeds!")
            print(f"Tried to run at {speed_scale:.1f}x speed,", end=" ")
            print(f"but actual speed was {actual_speed_scale:.1f}x.")
            if speed_scale > 1.0:
                print("Try decreasing 'speed_scale' or increasing 'step'")
            else:
                print("Try increasing 'step'")

        if hold:
            TabbedPlotWindow.show_all()

    @staticmethod
    def get_screen_size() -> tuple[int, int]:
        """
        Returns the size of the screen in pixels. Tries to get the screen size
        of the screen at the current cursor position. If no screen is found,
        it will return the size of the primary screen.

        Returns:
            (width, height) (tuple[int,int]): The width and height of the screen
                in pixels.
        """
        screen = TabbedPlotWindow._app.screenAt(QtGui.QCursor.pos())
        if screen is None:
            # Fallback to primary screen if no screen is found at cursor position
            screen = TabbedPlotWindow._app.primaryScreen()
        size = screen.size()
        return size.width(), size.height()
