from matplotlib.figure import Figure
from matplotlib.backends.qt_compat import QtWidgets

from .figure_widget import FigureWidget
from .custom_widget import CustomWidget


class TabbedFigureWidget(QtWidgets.QTabWidget):
    """
    A Qt widget that can contains multiple tabs, each with a matplotlib Figure.
    This class inherits from QTabWidget in order to create a tabbed interface.

    Methods:
        `add_figure_tab`: Adds a new tab with a matplotlib Figure.
        `add_custom_tab`: Adds a new tab with a custom Qt widget.
        `get_tab`: Returns the widget associated with a given tab ID.
        `set_tab_position`: Sets the position of the tab bar.
        `set_tab_fontsize`: Sets the font size of the tab bar.
    """

    def __init__(self, autohide: bool, position: str = "top", fontsize: int = 8):
        """
        Initializes the TabbedFigureWidget.

        Args:
            autohide (bool): If True, the tab bar will auto-hide when there is
                only one tab.
            position (str): The position of the tab bar. Can be 'top', 'bottom',
                'left', or 'right' as well as 'north', 'south', 'east', or
                'west' (only first character is checked).
            fontsize (int): The font size of the tab labels.
        """
        super().__init__()
        tabbar = self.tabBar()
        assert isinstance(tabbar, QtWidgets.QTabBar)
        tabbar.setAutoHide(autohide)
        tabbar.setContentsMargins(0, 0, 0, 0)
        self.set_tab_position(position)
        self.set_tab_fontsize(fontsize)
        self._figure_widgets: dict[str, FigureWidget] = {}
        self._custom_widgets: dict[str, CustomWidget] = {}

    def __getitem__(self, tab_id: str | int) -> FigureWidget | CustomWidget:
        """
        Provides dictionary-like access to tabs by their ID for convenience.
        """
        return self.get_tab(tab_id)

    def add_figure_tab(
        self, tab_id: str | int, blit: bool = False, include_toolbar: bool = True
    ) -> Figure:
        """
        Adds a new tab to the widget with the given title/tab_id, which
        creates and returns a matplotlib Figure. Tabs are displayed in the
        order they are added.

        Args:
            tab_id (str|int): The title/ID of the tab. If the tab ID already
                exists, the existing Figure from that tab will be returned.
            blit (bool): If True, enables blitting for faster rendering on the
                Figure in this tab.
            include_toolbar (bool): If True, includes a navigation toolbar
                with the Figure in this tab.
        """
        new_tab = FigureWidget(blit, include_toolbar)
        id_ = str(tab_id)
        if id_ in self._figure_widgets:
            return self._figure_widgets[id_].figure
        self._figure_widgets[id_] = new_tab
        idx = self.currentIndex()
        super().addTab(new_tab, id_)
        self.setCurrentWidget(new_tab)  # activate tab to auto size figure
        self.setCurrentIndex(idx)  # switch back to original tab
        return new_tab.figure

    def add_custom_tab(
        self,
        widget: QtWidgets.QWidget,
        tab_id: str | int,
    ) -> None:
        """
        Adds a new tab to the widget with the given title/tab_id, which
        contains the provided custom Qt widget. Tabs are displayed in the
        order they are added.

        Args:
            widget (QWidget): The custom Qt widget to add as a tab.
            tab_id (str|int): The title/ID of the tab.
        """
        id_ = str(tab_id)
        if id_ in self._figure_widgets | self._custom_widgets:
            raise ValueError(f"Tab with id '{id_}' already exists.")
        new_tab = CustomWidget(widget)
        self._custom_widgets[id_] = new_tab
        super().addTab(new_tab, id_)
        return

    def get_tab(self, tab_id: str | int) -> FigureWidget | CustomWidget:
        """
        Returns the widget associated with the given tab ID.

        Args:
            tab_id (str|int): The title/ID of the tab.

        Returns:
            widget (FigureWidget | CustomWidget): The widget associated with the
                given tab ID.
        """
        id_ = str(tab_id)
        if id_ in self._figure_widgets:
            return self._figure_widgets[id_]
        elif id_ in self._custom_widgets:
            return self._custom_widgets[id_]
        else:
            raise ValueError(f"Tab with id '{id_}' does not exist.")

    def set_tab_position(self, position: str = "top") -> None:
        """
        Sets the position of the tab bar.

        Args:
            position (str): The position of the tab bar. Can be 'top', 'bottom',
                'left', or 'right' as well as 'north', 'south', 'east', or
                'west' (only first character is checked).
        """
        char = position[0].lower()
        if char in ["b", "s"]:
            self.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)
        elif char in ["l", "w"]:
            self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        elif char in ["r", "e"]:
            self.setTabPosition(QtWidgets.QTabWidget.TabPosition.East)
        else:
            self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

    def set_tab_fontsize(self, fontsize: int) -> None:
        """
        Sets the font size of the tab bar.

        Args:
            fontsize (int): The font size to set for the tab bar.
        """
        tabbar = self.tabBar()
        assert isinstance(tabbar, QtWidgets.QTabBar)
        font = tabbar.font()
        font.setPointSize(fontsize)
        tabbar.setFont(font)
