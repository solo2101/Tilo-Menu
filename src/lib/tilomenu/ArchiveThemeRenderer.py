"""Render original GnoMenu XML chrome independently of the desktop GTK theme.

Each button's Image is its hover state, not a permanently visible fill.
ImageBack is the optional resting background. Original Pango markup is honored.
"""
import getpass
import html
import platform
import shutil
import subprocess
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Pango', '1.0')
from gi.repository import GdkPixbuf, Gtk, Pango
from ArchiveThemeIcons import load_named_icon
from ArchiveThemeContrast import legible_markup


@lru_cache(maxsize=256)
def _pixbuf(directory, filename, size=None):
    if not filename:
        return None
    root = directory.resolve()
    path = (root / filename).resolve()
    if path.is_relative_to(root) and path.is_file():
        try:
            if size:
                return GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path), size, size, True)
            return GdkPixbuf.Pixbuf.new_from_file(str(path))
        except Exception:
            return None
    return None


@lru_cache(maxsize=256)
def _icon(directory, filename, size=0):
    pix = _pixbuf(directory, filename, size if size > 0 else None)
    if pix is not None:
        return pix
    if filename:
        image = load_named_icon(Path(filename).stem, size if size > 0 else 16)
        if image:
            return image.get_pixbuf()
    return None


def _set_safe_markup(label, markup, fallback=""):
    """Ignore malformed legacy markup rather than issuing GTK warnings."""
    if not markup:
        label.set_text(fallback)
        return
    try:
        ET.fromstring("<root>" + markup + "</root>")
    except ET.ParseError:
        label.set_text(fallback)
        return
    label.set_markup(markup)


def _is_valid_markup(markup):
    if not markup:
        return False
    try:
        ET.fromstring("<root>" + markup + "</root>")
        return True
    except ET.ParseError:
        return False


def _valid_markup(markup, fallback=""):
    """Keep legacy typography if valid, otherwise show a readable label."""
    if markup:
        try:
            ET.fromstring("<root>" + markup + "</root>")
            return markup
        except ET.ParseError:
            pass
    return html.escape(fallback)


def _color_label(label, theme, markup, fallback, x, y, width,
                 *, selected=False, invert_unselected=False, overlay="",
                 overlay_x=0, overlay_y=0):
    valid = _valid_markup(markup, fallback)
    corrected = legible_markup(
        theme, valid, x, y, width,
        selected=selected, invert_unselected=invert_unselected,
        overlay=overlay, overlay_x=overlay_x, overlay_y=overlay_y,
    )
    _set_safe_markup(label, corrected, fallback)


def _markup(container, attrs, width, *, theme, x=0, y=0, fallback="",
            selected=False, invert_unselected=False, overlay="",
            markup_override=None, text_x=None):
    markup = attrs.get("Markup", "") if markup_override is None else markup_override
    if not markup and not fallback:
        return None
    # Some legacy icon-only tabs contain intentionally unusable markup.
    if markup and not _is_valid_markup(markup) and not fallback:
        return None
    label = Gtk.Label()
    xoff = int(attrs.get("TextX", "0")) if text_x is None else text_x
    yoff = int(attrs.get("TextY", "0"))
    # Match GnoMenu 2.9.1's symmetric horizontal text insets.
    available = max(1, width - xoff * 2 - 2)
    _color_label(
        label, theme, markup, fallback, x + xoff, y + yoff, available,
        selected=selected, invert_unselected=invert_unselected,
        overlay=overlay, overlay_x=x, overlay_y=y,
    )
    label.set_xalign(
        (0.0, 0.5, 1.0)[max(0, min(2, int(attrs.get("TextAlignment", "0"))))]
    )
    label.set_ellipsize(Pango.EllipsizeMode.END)
    label.set_size_request(available, -1)
    container.put(label, xoff, yoff)
    return label


def _event_box(child, width, height, name, callback):
    eventbox = Gtk.EventBox()
    eventbox.set_visible_window(False)
    from ArchivedThemeChrome import transparent_chrome
    transparent_chrome(eventbox)
    eventbox.set_above_child(True)
    eventbox.set_size_request(width, height)
    eventbox.add(child)
    if name and name != ":SEPARATOR:":
        eventbox.set_tooltip_text(name)
        if callback is not None:
            eventbox.connect(
                "button-release-event",
                lambda _widget, event: bool(callback(name)) if event.button == 1 else False
            )
    return eventbox


def render_theme_buttons(layout: Gtk.Fixed, theme, on_activate=None) -> None:
    """Draw original normal and hover button frames at their XML coordinates."""
    widgets = []
    for element in theme.buttons:
        attrs = element.attributes
        hover = _pixbuf(theme.directory, attrs.get("Image", ""))
        back = _pixbuf(theme.directory, attrs.get("ImageBack", ""))
        if hover is None and back is None:
            widgets.append(None)
            continue
        reference = hover or back
        width, height = reference.get_width(), reference.get_height()
        container = Gtk.Fixed()
        container.set_app_paintable(True)
        container.set_size_request(width, height)
        from ArchivedThemeChrome import transparent_chrome
        transparent_chrome(container)
        if back is not None:
            container.put(Gtk.Image.new_from_pixbuf(back), 0, 0)
        foreground = Gtk.Image()
        container.put(foreground, 0, 0)
        if attrs.get("Name") == ":SEPARATOR:":
            foreground.set_from_pixbuf(hover)
        # Icon describes the menu action, not button artwork.
        default_icon_name = attrs.get("ButtonIcon", "")
        icon_size = int(attrs.get("ButtonIconSize", "0") or "0")
        default_icon = _icon(theme.directory, default_icon_name, icon_size)
        selected_icon = _icon(theme.directory, attrs.get("ButtonIconSel", ""), icon_size)
        # GnoMenu's original Menu_Widgets.MenuButton only paints ButtonIcon
        # and ButtonIconSel. The XML Icon field selects a user-picture image
        # via Main_Menu.UpdateUserImage on hover; it is NEVER drawn here.
        icon = Gtk.Image()
        if default_icon is not None:
            icon.set_from_pixbuf(default_icon)
        if default_icon is not None or selected_icon is not None:
            container.put(
                icon,
                int(attrs.get("ButtonIconX", "0")),
                int(attrs.get("ButtonIconY", "0")),
            )
        x, y = element.integer("ButtonX"), element.integer("ButtonY")
        # Follow the original XML TextX, TextY and TextAlignment verbatim.
        label = _markup(
            container, attrs, width, theme=theme, x=x, y=y,
            overlay=attrs.get("ImageBack", ""),
            fallback=attrs.get("Name", "") if attrs.get("Markup") else "",
        )
        name = attrs.get("Name", "")
        eventbox = _event_box(container, width, height, name, on_activate)
        widgets.append(eventbox)
        if name != ":SEPARATOR:":
            def change_state(hovered, foreground=foreground, icon=icon,
                             picture=hover, default=default_icon,
                             selected=selected_icon, text=label,
                             attr=attrs, bx=x, by=y, w=width):
                foreground.set_from_pixbuf(picture if hovered else None)
                icon.set_from_pixbuf((selected or default) if hovered else default)
                if text is not None:
                    _color_label(
                        text, theme, attr.get("Markup", ""), attr.get("Name", ""),
                        bx + int(attr.get("TextX", "0")),
                        by + int(attr.get("TextY", "0")),
                        max(1, w - int(attr.get("TextX", "0")) - 4),
                        selected=hovered,
                        overlay=attr.get("Image", "") if hovered
                                else attr.get("ImageBack", ""),
                        overlay_x=bx, overlay_y=by,
                    )

            # Expose the original Setimage/SetBackground behavior through
            # the GTK3 painter. Main_Menu.Button_enter/leave owns the timing
            # and hover callbacks, as in the original GnoMenu source.
            eventbox._tilomenu_change_state = change_state
            if on_activate is not None:
                # Standalone archive consumers still own their hover events.
                eventbox.connect(
                    "enter-notify-event",
                    lambda _widget, _event, state=change_state:
                        state(True) or False,
                )
                eventbox.connect(
                    "leave-notify-event",
                    lambda _widget, _event, state=change_state:
                        state(False) or False,
                )
        layout.put(eventbox, element.integer("ButtonX"), element.integer("ButtonY"))
    return widgets


def render_theme_details(layout: Gtk.Fixed, theme, on_tab=None,
                         tab_hover=False) -> dict:
    """Draw XML static images, labels and tabs without desktop-theme styling."""
    for element in theme.images:
        picture = _pixbuf(theme.directory, element.attributes.get("Image", ""))
        if picture is not None:
            layout.put(
                Gtk.Image.new_from_pixbuf(picture),
                element.integer("ImageX"), element.integer("ImageY"),
            )

    for element in theme.labels:
        attrs = element.attributes
        markup = attrs.get("Markup", "")
        command = attrs.get("Command", "").strip().casefold()
        replacement = ""
        if command == "whoami":
            replacement = getpass.getuser()
        elif "lsb_release" in command:
            try:
                replacement = platform.freedesktop_os_release().get(
                    "PRETTY_NAME", platform.system()
                )
            except (OSError, AttributeError):
                replacement = platform.system()
        elif command.startswith("df "):
            try:
                disk = shutil.disk_usage("/")
                replacement = f"{round(100 * disk.used / disk.total)}%"
            except OSError:
                replacement = "N/A"
        elif command.startswith("/sbin/ip route") or command.startswith("ip route"):
            try:
                result = subprocess.run(
                    ["ip", "-4", "-o", "addr", "show", "scope", "global"],
                    capture_output=True, text=True, timeout=1, check=False,
                )
                replacement = next(
                    (word.split("/")[0] for word in result.stdout.split()
                     if word.count(".") == 3 and "/" in word),
                    "N/A"
                )
            except (OSError, subprocess.TimeoutExpired):
                replacement = "N/A"
        elif attrs.get("Name") == "Username":
            replacement = getpass.getuser()

        text = markup.replace("[TEXT]", html.escape(replacement))
        label = Gtk.Label()
        x, y = element.integer("LabelX"), element.integer("LabelY")
        alignment = max(0, min(2, int(attrs.get("TextAlignment", "0"))))
        _color_label(
            label, theme, text, attrs.get("Name", ""), x, y,
            min(220, max(70, theme.width // 2)),
        )

        # The original GnoMenu uses the markup's natural pixel width to
        # anchor center- and right-aligned labels. get_preferred_size() on an
        # unparented GTK3 Label can be 0/1px: that caused every caption to
        # collapse into a literal "..." ellipsis.
        pango_layout = label.get_layout()
        natural, _height = pango_layout.get_pixel_size()
        if natural < 2 and label.get_text():
            natural = max(20, len(label.get_text()) * 7)
        natural = max(1, natural)
        left = x - (natural if alignment == 2 else
                    natural // 2 if alignment == 1 else 0)
        left = max(0, left)

        # GnoMenu's original MenuLabel uses the natural Pango text width.
        # The previous GTK3 adapter clipped every left label at ProgramList X,
        # even on XML themes where labels intentionally span both regions.
        # Restrict only to the actual popup edge, not an invented column.
        allowed = max(1, min(natural, theme.width - left - 4))
        if allowed < natural:
            label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_size_request(allowed, -1)
        label.set_xalign((0.0, 0.5, 1.0)[alignment])
        layout.put(label, left, y)

    tabs = {}
    tab_boxes = []
    tab_names = [e.attributes.get("Name", "") for e in theme.tabs]
    active = "Applications" if "Applications" in tab_names else (
        tab_names[0] if tab_names else ""
    )
    for element in theme.tabs:
        attrs = element.attributes
        normal = _pixbuf(theme.directory, attrs.get("Image", ""))
        selected = _pixbuf(theme.directory, attrs.get("ImageSel", ""))
        # GnoMenu's original MenuTab.Setimage() flips tab artwork
        # vertically for a top-panel popup. The background is already
        # flipped by Main_Menu.shape(), and oriented_theme() mirrors the
        # tab's Y coordinate. Reproduce the third part of that behavior:
        # flip the tab bitmap, not its text or action icon. Never mutate
        # _pixbuf's cached original, which is reused for bottom panels.
        if theme.flipped:
            normal = normal.flip(False) if normal is not None else None
            selected = selected.flip(False) if selected is not None else None
        reference = selected or normal
        if reference is None:
            tab_boxes.append(None)
            continue
        width, height = reference.get_width(), reference.get_height()
        container = Gtk.Fixed()
        container.set_size_request(width, height)
        from ArchivedThemeChrome import transparent_chrome
        transparent_chrome(container)
        picture = Gtk.Image()
        container.put(picture, 0, 0)
        icon_size = int(attrs.get("TabIconSize", "0") or "0")
        # Only TabIcon is painted on tabs; Icon is used for menu content.
        icon_name = attrs.get("TabIcon", "")
        icon_pix = _icon(theme.directory, icon_name, icon_size)
        if icon_pix is not None:
            container.put(
                Gtk.Image.new_from_pixbuf(icon_pix),
                int(attrs.get("TabIconX", "0")), int(attrs.get("TabIconY", "0")),
            )
        name = attrs.get("Name", "")
        tx, ty = element.integer("TabX"), element.integer("TabY")
        inverted = attrs.get("InvertTextColorOnSel", "0") == "1"
        # Original GnoMenu positions tab labels at TextX / TextY.
        # Never move or enlarge the authored caption to fit an icon.
        label = _markup(
            container, attrs, width, theme=theme, x=tx, y=ty,
            fallback="", selected=name == active,
            invert_unselected=inverted,
            overlay=attrs.get("ImageSel", "") if name == active
                    else attrs.get("Image", ""),
        )

        def set_selected(value, picture=picture, normal=normal, selected=selected,
                         text=label, attr=attrs, bx=tx, by=ty, w=width,
                         tab_name=name, invert=inverted):
            picture.set_from_pixbuf((selected or normal) if value else normal)
            if text is not None:
                _color_label(
                    text, theme, attr.get("Markup", ""), "",
                    bx + int(attr.get("TextX", "0")),
                    by + int(attr.get("TextY", "0")),
                    max(1, w - 2 * int(attr.get("TextX", "0")) - 2),
                    selected=value, invert_unselected=invert,
                    overlay=attr.get("ImageSel", "") if value
                            else attr.get("Image", ""),
                    overlay_x=bx, overlay_y=by,
                )
        tabs[name] = set_selected
        set_selected(name == active)
        box = _event_box(container, width, height, name, on_tab)
        tab_boxes.append(box)
        # Hover is only for switching tab pages, never for launching Places,
        # Recent or system actions when the pointer merely passes over them.
        if tab_hover and on_tab is not None and name in ('Favorites', 'Applications'):
            box.connect(
                "enter-notify-event",
                lambda _widget, _event, action=name: bool(on_tab(action))
            )
        layout.put(box, element.integer("TabX"), element.integer("TabY"))
    return tabs, tab_boxes
