#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2009 <helderfraga@gmail.com>
#
# Cairo drawing helpers
# Part of the GnoMenu

import Globals
import cairo
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk as gtk, Gdk, GdkPixbuf, GLib


def draw_scaled_image(ctx,x,y, pix, w, h):
        """Draws a picture from specified path with a certain width and height"""
        ctx.save()
        ctx.translate(x, y)             
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(pix).scale_simple(w,h,GdkPixbuf.InterpType.BILINEAR)
        if Globals.flip != None:
                pixbuf = pixbuf.flip(Globals.flip)

        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        image = None
        ctx.paint()
        pixbuf = None
        image = None
        ctx.restore()

def draw_image(ctx,x,y, pix,flip=True):
        """Draws a picture from specified path with a certain width and height"""

        ctx.save()
        ctx.translate(x, y)             
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(pix)
        if Globals.flip != None and flip is True:
                pixbuf = pixbuf.flip(Globals.flip)
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        image = None
        ctx.paint()
        pixbuf = None
        image = None
        ctx.restore()

def draw_pixbuf(ctx,pixbuf):
        """Draws a picture from specified path with a certain width and height"""

        ctx.save()
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        image = None
        ctx.paint()
        image = None
        ctx.restore()

def draw_enhanced_image(ctx,x,y, pix):
        """Draws a picture from specified path with a certain width and height"""

        ctx.save()
        ctx.translate(x, y)     
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(pix)
        if Globals.flip != None:
                pixbuf = pixbuf.flip(Globals.flip)
        iw = pixbuf.get_width()
        ih = pixbuf.get_height()
        #We do this so the themes with fully transparent background are still clickable
        pixbuf.composite(pixbuf, 0, 0, iw, ih, 0, 0, 1, 1, GdkPixbuf.InterpType.NEAREST, 255)
        pixbuf.composite(pixbuf, 0, 0, iw, ih, 0, 0, 1, 1, GdkPixbuf.InterpType.NEAREST, 255)
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        image = None
        ctx.paint()
        pixbuf = None
        image = None
        ctx.restore()

def draw_image_gtk(ctx,x,y, pix,w,h,bgcolor,colorpb=None,flip=True):
        """Draws a picture from specified path with a certain width and height"""
                
        ctx.save()
        ctx.translate(x, y)     
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(pix)
        if Globals.Has_Numpy:
                if not colorpb:
                        
                        r = (bgcolor.red*255)/65535.0
                        g = (bgcolor.green*255)/65535.0
                        b = (bgcolor.blue*255)/65535.0
                        colorpb= pixbuf.copy()
                        # PyGObject no longer exposes get_pixels_array().
                        # Retain the original RGB recoloring loop and alpha.
                        pixels = bytearray(colorpb.get_pixels())
                        channels = colorpb.get_n_channels()
                        stride = colorpb.get_rowstride()
                        for row in range(colorpb.get_height()):
                                for col in range(colorpb.get_width()):
                                        i = row * stride + col * channels
                                        pixels[i] = int(r)
                                        pixels[i + 1] = int(g)
                                        pixels[i + 2] = int(b)
                        colorpb = GdkPixbuf.Pixbuf.new_from_bytes(
                                GLib.Bytes.new(bytes(pixels)),
                                colorpb.get_colorspace(),
                                colorpb.get_has_alpha(), 8,
                                colorpb.get_width(), colorpb.get_height(), stride)
        
                        pixbuf.composite(colorpb, 0, 0, w, h, 0,0, 1, 1, GdkPixbuf.InterpType.BILINEAR, 70)

                pixbuf = colorpb
        else:print('Error - Gtk colors required Numpy installed')
        if Globals.flip != None and flip is True:
                pixbuf = pixbuf.flip(Globals.flip)
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        image = None
        ctx.paint()
        pixbuf = None
        image = None
        ctx.restore()

def draw_background_pixbuf(ctx,pixbuf,flip=True):
        """Draws a picture from specified path with a certain width and height"""
                
        ctx.save()
        if Globals.flip != None and flip is True:
                pixbuf = pixbuf.flip(Globals.flip)
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        image = None
        ctx.paint()
        pixbuf = None
        image = None
        ctx.restore()

