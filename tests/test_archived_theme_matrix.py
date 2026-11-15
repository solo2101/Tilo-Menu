"""Smoke-test every bundled original XML theme with the archived GTK3 engine."""
from pathlib import Path
import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf
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
    if folder.name in ('Gray', 'iTheme', 'XP'):
        original = GdkPixbuf.Pixbuf.new_from_file(str(folder / theme.background))
        color_samples = []
        for fraction_x, fraction_y in ((0.55, 0.4), (0.85, 0.4), (0.85, 0.7)):
            x = min(original.get_width()-1, int(original.get_width()*fraction_x))
            y = min(original.get_height()-1, int(original.get_height()*fraction_y))
            n = original.get_n_channels()
            offset = y * original.get_rowstride() + x * n
            color_samples.append(tuple(original.get_pixels()[offset:offset+n]))
        # These themes have an opaque interior in their original PNG.
        # If the desktop is visible through these pixels, GTK3 painting
        # is at fault, not an intentionally transparent theme asset.
        assert all(len(rgba) == 4 and rgba[3] == 255
                   for rgba in color_samples), (folder.name, color_samples)
    frame = Gtk.Fixed()
    frame.set_size_request(theme.width, theme.height)
    buttons = render_theme_buttons(frame, theme)
    tabs, boxes = render_theme_details(frame, theme)
    assert len(buttons) == len(theme.buttons), folder
    assert len(boxes) == len(theme.tabs), folder
    # Follow GnoMenu's original MenuButton: its ButtonIcon is painted,
    # while XML Icon is reserved for the user-picture hover action.
    for element, widget in zip(theme.buttons, buttons):
        if widget is None:
            continue
        children = widget.get_child().get_children()
        icons = [child for child in children if isinstance(child, Gtk.Image)]
        expected = 1  # foreground hover image (may be empty)
        if element.attributes.get('ImageBack'):
            expected += 1
        if element.attributes.get('ButtonIcon') or element.attributes.get('ButtonIconSel'):
            expected += 1
        assert len(icons) == expected, (folder.name, element.attributes.get('Name'),
                                        len(icons), expected)
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
