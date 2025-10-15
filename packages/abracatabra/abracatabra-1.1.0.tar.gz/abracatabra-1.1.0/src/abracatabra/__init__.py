"""
abracatabra
===========
A package for creating tabbed plot windows with matplotlib in a Qt environment.

Windows can be created with one or more tab groups. Each tab group can contain
one or more tabs, where is tab is a matplotlib Figure. The library provides
functions to show all open windows, update them, and a fun `abracatabra`
function to display all windows with a magical touch.

This package provides:
- `TabbedPlotWindow`: The main class for creating and managing tabbed plot windows.
- `show_all_windows`: Displays all open tabbed plot windows.
- `update_all_windows`: Updates all open tabbed plot windows.
- `animate_all_windows`: Animates all open tabbed plot windows based on
    registered callbacks.
- `abracatabra`: A fun function to display all open tabbed plot windows.
- `is_interactive`: Checks if the current environment is interactive
    (e.g., IPython or Jupyter).
- `__version__`: The version of the abracatabra package.
"""

from .tabbed_plot_window import TabbedPlotWindow, is_interactive
from .__about__ import __version__


def show_all_windows(tight_layout: bool = False, block: bool | None = None) -> None:
    """
    Shows all created windows.

    Args:
        tight_layout (bool): If True, applies a tight layout to all figures.
        block (bool): If True, block and run the GUI until all windows are
            closed, either individually or by pressing <ctrl+c> in the terminal.
            If False, the function returns immediately after showing the windows
            and you are responsible for ensuring the GUI event loop is running
            (interactive environments do this for you).
            Defaults to False in interactive environments, otherwise True.
    See Also
    -----
    `abracatabra()`: shows all created windows with a touch of magic!
    `update_all_windows()`: updates all open tabbed plot windows.
    `is_interactive()`: checks if the current environment is interactive.
    """
    TabbedPlotWindow.show_all(tight_layout, block)


def update_all_windows(delay_seconds: float = 0.0, callback_idx: int = 0) -> float:
    """
    Updates all open tabbed plot windows. This is similar to pyplot.pause()
    and is generally used to update the figure in a loop, e.g., an animation.
    This function only updates active tabs in each window, so inactive tabs are
    skipped to save time.

    Args:
        delay_seconds (float): The minimum delay in seconds before returning. If
            windows are updated faster than this, this function will block until
            `delay_seconds` seconds have passed. If the windows take longer than
            `delay_seconds` seconds to update, the function execution time will
            be greater than `delay_seconds`.
    Returns:
        update_time (float): The amount of time (seconds) taken to update the
            windows.
    See Also
    -----
    `show_all_windows()`: shows all created windows.
    `animate_all_windows()`: animates all open tabbed plot windows based on
        registered callbacks.
    `abracatabra()`: shows all created windows with a touch of magic!
    """
    return TabbedPlotWindow.update_all(delay_seconds, callback_idx)


def animate_all_windows(
    frames: int,
    ts: float,
    step: int = 1,
    speed_scale: float = 1.0,
    print_timing: bool = False,
    hold: bool = True,
) -> None:
    """
    Animates all created windows by repeatedly calling `update_all_windows()` in
    a loop for the given number of frames. This is a convenience function for
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
            whether to call `show_all_windows()` at the end or not.
    See Also
    -----
    `update_all_windows()`: updates all open tabbed plot windows.
    """
    TabbedPlotWindow.animate_all(frames, ts, step, speed_scale, print_timing, hold)


def abracatabra(
    tight_layout: bool = False, block: bool | None = None, verbose: bool = True
) -> None:
    """
    A more fun equivalent to `show_all_windows()`. Shows all created windows.

    Args:
        tight_layout (bool): If True, applies a tight layout to all figures.
        block (bool): If True, block and run the GUI until all windows are
            closed, either individually or by pressing <ctrl+c> in the terminal.
            If False, the function returns immediately after showing the windows
            and you are responsible for ensuring the GUI event loop is running
            (interactive environments do this for you).
            Defaults to False in interactive environments, otherwise True.
        verbose (bool): If True, prints a message when showing windows.
    See Also
    -----
    `show_all_windows()` : shows all created windows.
    `update_all_windows()` : updates all open tabbed plot windows.
    `is_interactive()` : checks if the current environment is interactive.
    """
    if verbose:
        print("Abracatabra! 🪄✨")
    for window in TabbedPlotWindow._registry.values():
        window.qt.setWindowIcon(window._icon2)
    TabbedPlotWindow.show_all(tight_layout, block)


__all__ = [
    "TabbedPlotWindow",
    "show_all_windows",
    "update_all_windows",
    "animate_all_windows",
    "abracatabra",
    "is_interactive",
    "__version__",
]
