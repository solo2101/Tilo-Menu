"""Keep original XML typography and portrait dimensions across GTK3 themes."""
from pathlib import Path
import re
import sys
import tempfile

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
from ArchiveThemeParser import load_menu_theme
from ArchiveThemeContrast import legible_markup
from ArchiveThemeRenderer import render_theme_buttons
from Menu_Widgets import ImageFrame

themes_dir = Path(__file__).resolve().parents[1] / 'src/share/tilomenu/Themes/Menu'
color = re.compile(r"foreground\s*=\s*['\"](#[0-9a-fA-F]{6})['\"]")
checked = 0

for folder in sorted(themes_dir.iterdir()):
    if not (folder / 'themedata.xml').is_file():
        continue
    theme = load_menu_theme(folder)
    for element in (*theme.buttons, *theme.tabs, *theme.labels):
        attrs = element.attributes
        markup = attrs.get('Markup', '')
        match = color.search(markup)
        if not match:
            continue
        x = int(attrs.get('ButtonX', attrs.get('TabX', attrs.get('LabelX', 0))))
        y = int(attrs.get('ButtonY', attrs.get('TabY', attrs.get('LabelY', 0))))
        actual = legible_markup(theme, markup, x, y, 80)
        assert actual == markup, (folder.name, attrs.get('Name'), markup, actual)
        if element.tag == 'Tab' and attrs.get('InvertTextColorOnSel') == '1':
            base = match.group(1)
            reversed_color = '#' + ''.join(
                f'{255 - int(base[i:i + 2], 16):02x}' for i in (1, 3, 5)
            )
            inverted = legible_markup(
                theme, markup, x, y, 80, invert_unselected=True, selected=False
            )
            assert reversed_color in inverted.lower(), (folder.name, attrs.get('Name'))
            selected = legible_markup(
                theme, markup, x, y, 80, invert_unselected=True, selected=True
            )
            assert selected == markup, (folder.name, attrs.get('Name'))
        checked += 1

# End-to-end GTK3 check: XP footer text must remain white, as XML specifies.
xp = load_menu_theme(themes_dir / 'XP')
layout = Gtk.Fixed()
buttons = render_theme_buttons(layout, xp)
for name in ('Lock Screen', 'Shut Down...'):
    index = next(i for i, b in enumerate(xp.buttons)
                 if b.attributes['Name'] == name)
    child = buttons[index].get_child()
    label = next(item for item in child.get_children() if isinstance(item, Gtk.Label))
    assert '#ffffff' in label.get_label().lower(), (
        name, 'GTK3 changed the original white theme text', label.get_label()
    )

# A theme's IconSettings dimensions define the frame and background crop.
# Loading a larger image must not expand the frame into adjacent XML widgets.
with tempfile.TemporaryDirectory() as temporary:
    picture = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 72, 72)
    picture.fill(0xffffffff)
    path = str(Path(temporary) / 'frame.png')
    picture.savev(path, 'png', [], [])
    background = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 120, 120)
    background.fill(0x336699ff)
    frame = ImageFrame(56, 56, 2, 2, 48, 48, Gtk.Fixed(), background)
    frame.updateimage(0, path)
    assert (frame.w, frame.h) == (56, 56)
    assert (frame.icons[0].get_width(), frame.icons[0].get_height()) == (56, 56)
    assert (frame.backimagearea.get_width(), frame.backimagearea.get_height()) == (56, 56)

assert checked >= 60, checked
print(f'PASS: original foreground colors in {checked} theme elements, XP footer, portrait frame bounds')
