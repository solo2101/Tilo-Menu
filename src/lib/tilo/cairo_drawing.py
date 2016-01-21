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

import pygtk
pygtk.require('2.0')
import Globals
import cairo
import gtk


def draw_scaled_image(ctx,x,y, pix, w, h):
	"""Draws a picture from specified path with a certain width and height"""
	ctx.save()
	ctx.translate(x, y)		
	pixbuf = gtk.gdk.pixbuf_new_from_file(pix).scale_simple(w,h,gtk.gdk.INTERP_BILINEAR)
	if Globals.flip != None:
		pixbuf = pixbuf.flip(Globals.flip)

	image = ctx.set_source_pixbuf(pixbuf, 0, 0)
	ctx.paint()
	pixbuf = None
	image = None
	ctx.restore()

def draw_image(ctx,x,y, pix,flip=True):
	"""Draws a picture from specified path with a certain width and height"""

	ctx.save()
	ctx.translate(x, y)		
	pixbuf = gtk.gdk.pixbuf_new_from_file(pix)
	if Globals.flip != None and flip is True:
		pixbuf = pixbuf.flip(Globals.flip)
	image = ctx.set_source_pixbuf(pixbuf, 0, 0)
	ctx.paint()
	pixbuf = None
	image = None
	ctx.restore()

def draw_pixbuf(ctx,pixbuf):
	"""Draws a picture from specified path with a certain width and height"""

	ctx.save()
	image = ctx.set_source_pixbuf(pixbuf, 0, 0)
	ctx.paint()
	image = None
	ctx.restore()

def draw_enhanced_image(ctx,x,y, pix):
	"""Draws a picture from specified path with a certain width and height"""

	ctx.save()
	ctx.translate(x, y)	
	pixbuf = gtk.gdk.pixbuf_new_from_file(pix)
	if Globals.flip != None:
		pixbuf = pixbuf.flip(Globals.flip)
	iw = pixbuf.get_width()
	ih = pixbuf.get_height()
	#We do this so the themes with fully transparent background are still clickable
	pixbuf.composite(pixbuf, 0, 0, iw, ih, 0, 0, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
	pixbuf.composite(pixbuf, 0, 0, iw, ih, 0, 0, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
	image = ctx.set_source_pixbuf(pixbuf, 0, 0)
	ctx.paint()
	pixbuf = None
	image = None
	ctx.restore()

def draw_image_gtk(ctx,x,y, pix,w,h,bgcolor,colorpb=None,flip=True):
	"""Draws a picture from specified path with a certain width and height"""
		
	ctx.save()
	ctx.translate(x, y)	
	pixbuf = gtk.gdk.pixbuf_new_from_file(pix)
	if Globals.Has_Numpy:
		if not colorpb:
			
			r = (bgcolor.red*255)/65535.0
			g = (bgcolor.green*255)/65535.0
			b = (bgcolor.blue*255)/65535.0
			colorpb= pixbuf.copy()
			for row in colorpb.get_pixels_array():
			        for pix in row:
				        pix[0] = r
			                pix[1] = g
	                		pix[2] = b
	
			pixbuf.composite(colorpb, 0, 0, w, h, 0,0, 1, 1, gtk.gdk.INTERP_BILINEAR, 70)

		pixbuf = colorpb
	else:print 'Error - Gtk colors required Numpy installed'
	if Globals.flip != None and flip is True:
		pixbuf = pixbuf.flip(Globals.flip)
	image = ctx.set_source_pixbuf(pixbuf, 0, 0)
	ctx.paint()
	pixbuf = None
	image = None
	ctx.restore()

def draw_background_pixbuf(ctx,pixbuf,flip=True):
	"""Draws a picture from specified path with a certain width and height"""
		
	ctx.save()
	if Globals.flip != None and flip is True:
		pixbuf = pixbuf.flip(Globals.flip)
	image = ctx.set_source_pixbuf(pixbuf, 0, 0)
	ctx.paint()
	pixbuf = None
	image = None
	ctx.restore()

