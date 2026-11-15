"""Bridge archived GTK3 menu chrome to original GnoMenu event handlers.

Only display widgets are replaced. Main_Menu keeps all original Button_click,
Tab_click, search, program-list, shutdown, Favorites and other actions.
"""
from pathlib import Path
from dataclasses import replace

from ArchiveThemeModels import ThemeElement

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


def oriented_theme(theme):
    """Use the original Globals.py orientation coordinates for archived art.

    The original code already accounts for the source image heights. Never
    transform the icons or their text; reposition their widget containers.
    """
    if Globals.orientation != 'top':
        return theme

    def changed(elements, field, values):
        result = []
        for index, element in enumerate(elements):
            attrs = dict(element.attributes)
            if index < len(values):
                attrs[field] = str(values[index])
            result.append(ThemeElement(element.tag, attrs))
        return tuple(result)

    return replace(
        theme,
        buttons=changed(theme.buttons, 'ButtonY', Globals.MenuButtonY),
        tabs=changed(theme.tabs, 'TabY', Globals.MenuTabY),
        labels=changed(theme.labels, 'LabelY', Globals.MenuLabelY),
        images=changed(theme.images, 'ImageY', Globals.MenuImageY),
    )


def render_original_chrome(main):
    """Return original-indexed Button/Tab adapters for the archive painter."""
    theme = oriented_theme(load_menu_theme(Path(Globals.ImageDirectory)))
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
