"""Smoke-test every bundled original XML theme with the archived GTK3 engine."""
from pathlib import Path
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
from ArchiveThemeParser import load_menu_theme
from ArchiveThemeRenderer import render_theme_buttons, render_theme_details
from ArchiveThemeSearch import ThemeSearch

themes = Path(__file__).resolve().parents[1] / 'src/share/tilomenu/Themes/Menu'
count = 0
for folder in sorted(themes.iterdir()):
    if not (folder / 'themedata.xml').is_file():
        continue
    theme = load_menu_theme(folder)
    frame = Gtk.Fixed()
    frame.set_size_request(theme.width, theme.height)
    buttons = render_theme_buttons(frame, theme)
    tabs, boxes = render_theme_details(frame, theme)
    assert len(buttons) == len(theme.buttons), folder
    assert len(boxes) == len(theme.tabs), folder
    if theme.capabilities.attributes.get('HasSearch') == '1':
        changed = []
        search = ThemeSearch(theme, lambda entry: changed.append(entry.get_text()))
        search.set_text('test')
        assert search.get_text() == 'test', folder
        assert changed == ['test'], folder
        assert search.entry.get_style_context().has_class('tilo-search-input')

    assert 0 < theme.width <= 1600 and 0 < theme.height <= 1600, folder
    count += 1
assert count >= 10, f'Only {count} themes rendered'
print(f'PASS: archived GTK3 chrome constructed all {count} bundled menu themes')
