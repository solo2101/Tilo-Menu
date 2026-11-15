"""Cairo application-list painter ported from the archived GTK3 renderer.

Gtk.IconView still owns selection, scrolling, keyboard navigation, drag/drop,
and the original XDGMenu actions. Only its pixels are replaced.  This avoids
the host GTK theme's opaque selection/row backgrounds.
"""
import cairo
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gdk, Gtk, Pango, PangoCairo


def draw_list(view, cr, model, background='#ffffff'):
    """Paint the original model at GTK's own cell rectangles.

    Reuse the archived renderer's Cairo, Pango ellipsis, selection overlay and
    rounded row drawing. The existing IconView still computes hit regions.
    """
    if model is None:
        return False
    width = view.get_allocated_width()
    height = view.get_allocated_height()
    if width < 1 or height < 1:
        return False
    color = Gdk.RGBA()
    if not color.parse(background):
        color.parse('#ffffff')
    cr.save()
    cr.rectangle(0, 0, width, height)
    cr.clip()
    # The original program-list area is an opaque color even when the
    # surrounding PNG uses transparency. Clear GTK's previous draw pass.
    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.set_source_rgb(color.red, color.green, color.blue)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)
    ink_light = (0.2126 * color.red + 0.7152 * color.green + 0.0722 * color.blue) < 0.55
    cr.set_source_rgb(*(0.97, 0.97, 0.97) if ink_light else (0.09, 0.09, 0.09))
    for index, row in enumerate(model):
        path = model.get_path(row.iter)
        try:
            found, rect = view.get_cell_rect(path, None)
        except (TypeError, AttributeError):
            # Preserve the GTK drawing path on platforms without this API.
            cr.restore()
            return False
        if not found or rect.y + rect.height < 0 or rect.y > height:
            continue
        if view.path_is_selected(path):
            cr.set_source_rgba(0.25, 0.47, 0.72, 0.30)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        icon = row[0]
        text = row[1] or ''
        inset = 7
        if icon is not None:
            iy = rect.y + (rect.height - icon.get_height()) / 2
            Gdk.cairo_set_source_pixbuf(cr, icon, rect.x + inset, iy)
            cr.paint()
            inset += icon.get_width() + 7
        layout = PangoCairo.create_layout(cr)
        layout.set_text(str(text), -1)
        layout.set_font_description(Pango.FontDescription('Sans 9'))
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        layout.set_width(max(1, rect.width - inset - 7) * Pango.SCALE)
        cr.move_to(rect.x + inset, rect.y + max(0, (rect.height - 17) / 2))
        cr.set_source_rgb(*(0.97, 0.97, 0.97) if ink_light else (0.09, 0.09, 0.09))
        PangoCairo.show_layout(cr, layout)
    cr.restore()
    return True
