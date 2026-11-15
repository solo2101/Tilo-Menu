"""Bridge archived GTK3 menu chrome to original GnoMenu event handlers.

Only display widgets are replaced. Main_Menu keeps all original Button_click,
Tab_click, search, program-list, shutdown, Favorites and other actions.
"""
from pathlib import Path

import Globals
from ArchiveThemeParser import load_menu_theme
from ArchiveThemeRenderer import render_theme_buttons, render_theme_details


class ButtonAdapter:
    def __init__(self, widget):
        self.Button = widget

    def Setimage(self, filename):
        # Archived renderer handles its own hover artwork.
        pass

    def SetBackground(self):
        pass

    def SetIcon(self, filename):
        # Archived renderer handles normal and selected overlay icons.
        pass


class TabAdapter:
    def __init__(self, widget, selected):
        self.Tab = widget
        self._set_selected = selected
        self._selected = False

    def SetSelectedTab(self, value):
        self._selected = bool(value)
        self._set_selected(self._selected)

    def GetSelectedTab(self):
        return self._selected


def render_original_chrome(main):
    """Return original-indexed Button/Tab adapters for the archive painter."""
    theme = load_menu_theme(Path(Globals.ImageDirectory))
    buttons = render_theme_buttons(main.menuframe, theme)
    selected, tab_boxes = render_theme_details(main.menuframe, theme)

    # A missing artwork file must not alter original command indexes.
    button_widgets = [
        ButtonAdapter(box) if box is not None else None for box in buttons
    ]
    tab_widgets = []
    for idx, box in enumerate(tab_boxes):
        if box is None:
            tab_widgets.append(None)
            continue
        name = theme.tabs[idx].attributes.get('Name', '')
        tab_widgets.append(TabAdapter(box, selected[name]))
    return button_widgets, tab_widgets
