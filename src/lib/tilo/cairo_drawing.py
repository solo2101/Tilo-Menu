#!/usr/bin/env python3
# Cairo drawing helpers for GTK 3 + PyGObject

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

import Globals

def _load_pixbuf(path, flip=None):
    pb = GdkPixbuf.Pixbuf.new_from_file(path)
    if flip is None:
        flip = Globals.flip
    if flip is not None:
        pb = pb.flip(flip)
    return pb

def draw_scaled_image(cr, x, y, path, w, h):
    pb = _load_pixbuf(path)
    if w and h:
        pb = pb.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
    Gdk.cairo_set_source_pixbuf(cr, pb, x, y)
    cr.paint()

def draw_image(cr, x, y, path, flip=True):
    pb = GdkPixbuf.Pixbuf.new_from_file(path)
    if Globals.flip is not None and flip:
        pb = pb.flip(Globals.flip)
    Gdk.cairo_set_source_pixbuf(cr, pb, x, y)
    cr.paint()

def draw_pixbuf(cr, pb):
    Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
    cr.paint()

def draw_enhanced_image(cr, x, y, path):
    pb = _load_pixbuf(path)
    iw, ih = pb.get_width(), pb.get_height()
    tmp = pb.copy()
    tmp.composite(pb, 0, 0, iw, ih, 0, 0, 1, 1, GdkPixbuf.InterpType.NEAREST, 255)
    Gdk.cairo_set_source_pixbuf(cr, pb, x, y)
    cr.paint()

def draw_image_gtk(cr, x, y, path, w, h, bgcolor, colorpb=None, flip=True):
    # Minimal port, preserves signature. Recolor step skipped unless colorpb passed.
    pb = GdkPixbuf.Pixbuf.new_from_file(path)
    if colorpb:
        pb = colorpb
    if Globals.flip is not None and flip:
        pb = pb.flip(Globals.flip)
    if w and h:
        pb = pb.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
    Gdk.cairo_set_source_pixbuf(cr, pb, x, y)
    cr.paint()

def draw_background_pixbuf(cr, pb, flip=True):
    if Globals.flip is not None and flip:
        pb = pb.flip(Globals.flip)
    Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
    cr.paint()
