#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2008,2009 <helderfraga@gmail.com>
#
# Tilo widgets
# Part of the Tilo
import gi
gi.require_version("Gtk", "2.0")

from gi.repository import Gtk
import cairo
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Pango
from Menu_Items import XDMateMenu
import os
import commands
import Globals
import IconFactory
import cairo_drawing
#import gc
#import time


try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'

import gettext

gettext.textdomain('tilo')
gettext.install('tilo', INSTALL_PREFIX +  '/share/locale')
gettext.bindtextdomain('tilo', INSTALL_PREFIX +  '/share/locale')

def _(s):
	return gettext.gettext(s)


class MenuButton:
	def __init__(self,i,base,backimage):
		# base > EventBox > Fixed > All the rest
		self.i = i
		self.backimagearea = None
		self.Button = Gtk.EventBox()
		self.Frame = Gtk.Fixed()
		if not self.Button.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True
		self.Button.connect("composited-changed", self.composite_changed)
		self.Frame.connect("expose_event", self.expose)
		self.Button.add(self.Frame)
		if Globals.MenuButtonIcon[i]:
			self.Icon = Gtk.Image()
			self.SetIcon(Globals.ImageDirectory + Globals.MenuButtonIcon[i])
		self.Image = Gtk.Image()
	   	self.Setimage(Globals.ImageDirectory + Globals.MenuButtonImage[i])
		self.w = self.Pic.get_width()
		self.h = self.Pic.get_height()
		if self.backimagearea is None:
			if Globals.flip == False:
				self.backimagearea = backimage.subpixbuf(Globals.MenuButtonX[i],Globals.MenuHeight - Globals.MenuButtonY[i] - self.h,self.w,self.h)
				self.backimagearea = self.backimagearea.flip(Globals.flip)
			else:
				self.backimagearea = backimage.subpixbuf(Globals.MenuButtonX[i],Globals.MenuButtonY[i] ,self.w,self.h)
		# Set the background which is always present
		self.BackgroundImage = Gtk.Image()
		if Globals.MenuButtonImageBack[i] != '':
			self.BackgroundImage.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file(Globals.ImageDirectory + Globals.MenuButtonImageBack[i]))
		else:
			self.BackgroundImage.set_from_pixbuf(None)
		self.Image.set_size_request(self.w,self.h)
		self.Frame.set_size_request(self.w,self.h)		
		self.SetBackground()

		self.Frame.put(self.BackgroundImage,0,0)
		self.Frame.put(self.Image,0,0)
		if Globals.MenuButtonIcon[i]:
			self.Frame.put(self.Icon,Globals.MenuButtonIconX[i],Globals.MenuButtonIconY[i])
		self.Label = Gtk.Label()
		self.txt = Globals.MenuButtonMarkup[i]
		try:
			self.txt = self.txt.replace(Globals.MenuButtonNames[i],_(Globals.MenuButtonNames[i]))

		except:pass
		self.Label.set_markup(self.txt)
		if Globals.MenuButtonNameAlignment[i] == 0:
			self.Label.set_alignment(0, 0)
		elif Globals.MenuButtonNameAlignment[i] == 1:
			self.Label.set_alignment(0.5, 0)
		else:
			self.Label.set_alignment(1, 0)
		self.Label.set_size_request(int(self.w-Globals.MenuButtonNameOffsetX[i]*2)-2,-1)
		self.Label.set_ellipsize(Pango.EllipsizeMode.END)
		self.Frame.put(self.Label,Globals.MenuButtonNameOffsetX[i],Globals.MenuButtonNameOffsetY[i])
		if self.Label.get_text() == '' or Globals.Settings['Show_Tips']:
			self.Frame.set_tooltip_text(_(Globals.MenuButtonNames[i]))
		base.put(self.Button,Globals.MenuButtonX[i],Globals.MenuButtonY[i])
		#gc.collect()

	def composite_changed(self,widget):
		
	 	if not self.Button.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True

	def expose (self, widget, event):
		self.ctx = widget.window.cairo_create()
		# set a clip region for the expose event
		if self.supports_alpha == False:
			self.ctx.set_source_rgb(1, 1, 1)
		else:
			self.ctx.set_source_rgba(1, 1, 1,0)
		self.ctx.set_operator (cairo.OPERATOR_SOURCE)
		self.ctx.paint()
		cairo_drawing.draw_pixbuf(self.ctx,self.backimagearea)


	  
	def SetIcon(self,filename):
		# If the menu has an icon on top, then add that
		try:
			if Globals.MenuButtonIconSize[self.i] != 0:
				self.ww = Globals.MenuButtonIconSize[self.i]
				self.hh = self.ww
				self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(filename,self.ww,self.hh)
			else:
				self.Pic = GdkPixbuf.Pixbuf.new_from_file(filename)
				self.ww = self.Pic.get_width()
				self.hh = self.Pic.get_height()
			if Globals.Settings['System_Icons']:
				if Globals.MenuButtonIconSel[self.i] == '':
					ico = IconFactory.GetSystemIcon(Globals.MenuButtonIcon[self.i])
					if not ico:
						ico = filename
					self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.ww,self.hh)
			self.Icon.set_from_pixbuf(self.Pic)
		except:print 'error on button seticon'  + filename
				

	def Setimage(self,imagefile):
		# The image is background when it's not displaying the overlay
		self.Pic = GdkPixbuf.Pixbuf.new_from_file(imagefile)
		self.Image.set_from_pixbuf(self.Pic)

	def SetBackground(self):
		self.Image.set_from_pixbuf(None)


class MenuImage:
	def __init__(self,i,base,backimage):
		self.backimagearea = None
		self.Frame = Gtk.Fixed()
		if not self.Frame.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True
		self.Frame.connect("composited-changed", self.composite_changed)
		self.Image = Gtk.Image()
		self.Pic = GdkPixbuf.Pixbuf.new_from_file(Globals.ImageDirectory + Globals.MenuImage[i])
		self.w = self.Pic.get_width()
		self.h = self.Pic.get_height()
		if Globals.Settings['System_Icons']:
			ico = IconFactory.GetSystemIcon(Globals.MenuImage[i])
			if not ico:
				ico = Globals.ImageDirectory + Globals.MenuImage[i]
			self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.w,self.h)

		if self.backimagearea is None:
			if Globals.flip == False:
				self.backimagearea = backimage.subpixbuf(Globals.MenuImageX[i],Globals.MenuHeight - Globals.MenuImageY[i] - self.h,self.w,self.h)
				self.backimagearea = self.backimagearea.flip(Globals.flip)
			else:
				self.backimagearea = backimage.subpixbuf(Globals.MenuImageX[i],Globals.MenuImageY[i] ,self.w,self.h)
		self.Pic.composite(self.backimagearea, 0, 0, self.w, self.h, 0, 0, 1, 1, GdkPixbuf.InterpType.BILINEAR, 255)
		# Set the background which is always present
		self.Image.set_from_pixbuf(self.backimagearea)
		self.Image.set_size_request(self.w,self.h)
		self.Frame.set_size_request(self.w,self.h)
		self.Frame.put(self.Image,0,0)
		base.put(self.Frame,Globals.MenuImageX[i],Globals.MenuImageY[i])
		#gc.collect()

	def composite_changed(self,widget):
		
	 	if not self.Frame.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True


	def expose (self, widget, event):
		
		self.ctx = widget.window.cairo_create()
		# set a clip region for the expose event
		if self.supports_alpha == False:
			self.ctx.set_source_rgb(1, 1, 1)
		else:
			self.ctx.set_source_rgba(1, 1, 1,0)
		self.ctx.set_operator (cairo.OPERATOR_SOURCE)
		self.ctx.paint()

class MenuTab:
	def __init__(self,i,base,backimage):
		self.i = i
		self.backimagearea = None
		self.Tab = Gtk.EventBox()
		self.Frame = Gtk.Fixed()
		if not self.Tab.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True
		self.Tab.connect("composited-changed", self.composite_changed)
		self.Tab.connect("enter_notify_event", self.enter,i)
		self.Tab.connect("leave_notify_event", self.leave,i)
		self.Frame.connect("expose_event", self.expose)
		sel = GdkPixbuf.Pixbuf.get_file_info(Globals.ImageDirectory +Globals.MenuTabImageSel[self.i])
		self.w = sel[1]
		self.h = sel[2]
		sel = None
		self.Tab.add(self.Frame)
		if Globals.MenuTabIcon[i] != '':
			self.Icon = Gtk.Image()
			self.SetIcon(Globals.ImageDirectory + Globals.MenuTabIcon[i])
		# Set the top image
		self.Image = Gtk.Image()
	   	self.Setimage(Globals.ImageDirectory + Globals.MenuTabImage[i])
		
		# Clip the background from the back image
		# Grab the background pixels from under the location of the menu Tab

		if self.backimagearea is None:
			if Globals.flip == False:
				self.backimagearea = backimage.subpixbuf(Globals.MenuTabX[i],Globals.MenuHeight - Globals.MenuTabY[i] - self.h,self.w,self.h)
				self.backimagearea = self.backimagearea.flip(Globals.flip)
			else:
				self.backimagearea = backimage.subpixbuf(Globals.MenuTabX[i],Globals.MenuTabY[i] ,self.w,self.h)
		# Set the background which is always present
		self.Image.set_size_request(self.w,self.h)
		self.Frame.set_size_request(self.w,self.h)
		self.SetBackground()
		self.Frame.put(self.Image,0,0)
		if Globals.MenuTabIcon[i]:
			self.Frame.put(self.Icon,Globals.MenuCairoIcontabX[i],Globals.MenuCairoIcontabY[i])
		self.Label = Gtk.Label()
		self.txt = Globals.MenuTabMarkup[i]
		try:
			self.txt = self.txt.replace(Globals.MenuTabNames[i],_(Globals.MenuTabNames[i]))
		except:pass
		self.prime_color = self.txt[(self.txt.find("span foreground='") +len("span foreground='")):]
		self.prime_color = self.prime_color[:self.prime_color.find("'")]
		if self.prime_color == '':self.prime_color = Globals.ThemeColorHtml
		self.theme_color = Gdk.color_parse(self.prime_color)
		self.theme_color_r = 65535 - int(self.theme_color.red)
		self.theme_color_g = 65535 - int(self.theme_color.green)
		self.theme_color_b = 65535 - int(self.theme_color.blue)
		self.color = Gdk.Color(self.theme_color_r,self.theme_color_g,self.theme_color_b,0)
		self.second_color = self.color_to_hex(self.color)
		self.Frame.set_tooltip_text(_(Globals.MenuTabNames[i]))
		#self.Label.set_markup(self.txt)
		if Globals.MenuTabNameAlignment[i] == 0:
			self.Label.set_alignment(0, 0)
		elif Globals.MenuTabNameAlignment[i] == 1:
			self.Label.set_alignment(0.5, 0)
		else:
			self.Label.set_alignment(1, 0)
		self.Label.set_size_request(int(self.w-Globals.MenuTabNameOffsetX[i]*2)-2,-1)
		self.Label.set_ellipsize(Pango.EllipsizeMode.END)
		self.Frame.put(self.Label,Globals.MenuTabNameOffsetX[i],Globals.MenuTabNameOffsetY[i])
		base.put(self.Tab,Globals.MenuTabX[i],Globals.MenuTabY[i])
		self.selected_tab = False
		#gc.collect()


	def enter (self, widget, event,i):

		if Globals.Settings['Tab_Efect'] != 0 and Globals.MenuTabIcon[i] != '':
			if Globals.Settings['System_Icons']:
				ico = ico = IconFactory.GetSystemIcon(Globals.MenuTabIcon[i])
				if not ico:
					ico = Globals.ImageDirectory + Globals.MenuTabIcon[i]

			else:
				ico = Globals.ImageDirectory + Globals.MenuTabIcon[i]

			if Globals.Settings['Tab_Efect'] == 1: #grow
				self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.ww+4,self.hh+4)


			elif Globals.Settings['Tab_Efect'] == 2:#bw
				self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.ww,self.hh)
				self.Pic.saturate_and_pixelate(self.Pic, 0.0, False)

			elif Globals.Settings['Tab_Efect'] == 3:#Blur

				colorpb = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.ww,self.hh)
				alpha = 255#int(int(70) * 2.55 + 0.2)
				tk = 2
				bg = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, self.ww,self.hh)
				bg.fill(0x00000000)
				glow = bg.copy()
				# Prepare the glow that should be put bind the icon
				tk1 = tk - int(tk/2)
				for x, y in ((-tk1,-tk1), (-tk1,tk1), (tk1,-tk1), (tk1,tk1)):
					colorpb.composite(glow, 0, 0, self.ww, self.hh, x, y, 1, 1, GdkPixbuf.InterpType.BILINEAR, 170)
				for x, y in ((-tk,-tk), (-tk,tk), (tk,-tk), (tk,tk)):
					colorpb.composite(glow, 0, 0, self.ww, self.hh, x, y, 1, 1, GdkPixbuf.InterpType.BILINEAR, 70)
				glow.composite(bg, 0, 0, self.ww, self.hh, 0, 0, 1, 1, GdkPixbuf.InterpType.BILINEAR, alpha)
				self.Pic = bg
				

			elif Globals.Settings['Tab_Efect'] == 4:#glow
				if Globals.Has_Numpy:
					r = 255
				        g = 255
					b = 0
					self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.ww,self.hh)
					colorpb= self.Pic.copy()
				        for row in colorpb.get_pixels_array():
					        for pix in row:
						        pix[0] = r
					                pix[1] = g
	                				pix[2] = b
	
					alpha = 255#int(int(70) * 2.55 + 0.2)
					tk = 2
				        bg = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, self.ww,self.hh)
				        bg.fill(0x00000000)
				        glow = bg.copy()
				        # Prepare the glow that should be put bind the icon
				        tk1 = tk - int(tk/2)
				        for x, y in ((-tk1,-tk1), (-tk1,tk1), (tk1,-tk1), (tk1,tk1)):
						colorpb.composite(glow, 0, 0, self.ww, self.hh, x, y, 1, 1, GdkPixbuf.InterpType.BILINEAR, 170)
					for x, y in ((-tk,-tk), (-tk,tk), (tk,-tk), (tk,tk)):
						colorpb.composite(glow, 0, 0, self.ww, self.hh, x, y, 1, 1, GdkPixbuf.InterpType.BILINEAR, 70)
					glow.composite(bg, 0, 0, self.ww, self.hh, 0, 0, 1, 1, GdkPixbuf.InterpType.BILINEAR, alpha)
					self.Pic.composite(bg, 0, 0, self.ww, self.hh, 0, 0, 1, 1, GdkPixbuf.InterpType.BILINEAR, 255)
				        self.Pic = bg
				else:print 'Error - This efect requires numpy installed'					

			elif Globals.Settings['Tab_Efect'] == 5:#saturate
				self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.ww,self.hh)
				self.Pic.saturate_and_pixelate(self.Pic, 6.0, False)
					

			self.Icon.set_from_pixbuf(self.Pic)

			if Globals.Settings['Tab_Efect'] == 1:
				self.Frame.move(self.Icon,Globals.MenuCairoIcontabX[i]-2,Globals.MenuCairoIcontabY[i]-2)
			else:
				self.Frame.move(self.Icon,Globals.MenuCairoIcontabX[i],Globals.MenuCairoIcontabY[i])

	def leave (self, widget, event,i):
		if Globals.Settings['Tab_Efect'] != 0 and Globals.MenuTabIcon[i] != '':		
			if Globals.Settings['System_Icons']:
				ico = IconFactory.GetSystemIcon(Globals.MenuTabIcon[i])
				if not ico : 
					ico = Globals.ImageDirectory + Globals.MenuTabIcon[i]
			else:
				ico = Globals.ImageDirectory + Globals.MenuTabIcon[i]

			self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.ww,self.hh)
			self.Frame.move(self.Icon,Globals.MenuCairoIcontabX[i],Globals.MenuCairoIcontabY[i])
			self.Icon.set_from_pixbuf(self.Pic)

	def composite_changed(self,widget):
		
	 	if not self.Tab.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True

	def expose (self, widget, event):
		self.ctx = widget.window.cairo_create()
		# set a clip region for the expose event
		if self.supports_alpha == False:
			self.ctx.set_source_rgb(1, 1, 1)
		else:
			self.ctx.set_source_rgba(1, 1, 1,0)
		self.ctx.set_operator (cairo.OPERATOR_SOURCE)
		self.ctx.paint()
		cairo_drawing.draw_pixbuf(self.ctx,self.backimagearea)


	  
	def SetIcon(self,filename):
		# If the menu has an icon on top, then add that

		if Globals.Settings['System_Icons']:
			ico = IconFactory.GetSystemIcon(Globals.MenuTabIcon[self.i])
			if not ico:
				ico = Globals.ImageDirectory + Globals.MenuTabIcon[self.i]
		else:
			ico = Globals.ImageDirectory + Globals.MenuTabIcon[self.i]
		self.Pic = GdkPixbuf.Pixbuf.get_file_info(Globals.ImageDirectory + Globals.MenuTabIcon[self.i])
		self.ww = Globals.MenuCairoIcontabSize[self.i]
		self.hh = self.ww
		if self.ww == 0:self.ww = self.Pic[1]
		if self.hh == 0:self.hh = self.Pic[2]

		self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(ico,self.ww,self.hh)
		self.Icon.set_from_pixbuf(self.Pic)
		#except:print 'Menu Tab error in - ' + filename
				

	def Setimage(self,imagefile):
		# The image is background when it's not displaying the overlay
		try:
			self.Pic = GdkPixbuf.Pixbuf.new_from_file(imagefile)
			if Globals.Settings['GtkColors'] == 1 and Globals.Has_Numpy:
				
				bgcolor = Globals.GtkColorCode
				r = (bgcolor.red*255)/65535.0
				g = (bgcolor.green*255)/65535.0
				b = (bgcolor.blue*255)/65535.0
				colorpb= self.Pic.copy()
				for row in colorpb.get_pixels_array():
				        for pix in row:
					        pix[0] = r
				                pix[1] = g
		                		pix[2] = b

				self.Pic.composite(colorpb, 0, 0, self.w, self.h, 0, 0, 1, 1, GdkPixbuf.InterpType.BILINEAR, 70)
				self.Pic = colorpb

			if Globals.flip == False:
				self.Pic.flip(Globals.flip)
				self.Image.set_from_pixbuf(self.Pic.flip(Globals.flip))
			else:
				self.Image.set_from_pixbuf(self.Pic)
		except:pass


	def SetBackground(self):
		self.Image.set_from_pixbuf(None)

	def SetSelectedTab(self,tab):
		if tab == False:
			if Globals.MenuTabInvertTextColorSel[self.i]:
				self.txt1 = self.txt.replace(self.prime_color,self.second_color)
				self.Label.set_markup(self.txt1)
			else:
				self.Label.set_markup(self.txt)	
			self.selected_tab = False
			self.SetBackground()
			self.Setimage(Globals.ImageDirectory + Globals.MenuTabImage[self.i])

		else:
			self.Label.set_markup(self.txt)	
			self.selected_tab = True
			self.Setimage(Globals.ImageDirectory + Globals.MenuTabImageSel[self.i])

	def GetSelectedTab(self):
		return self.selected_tab

	def color_to_hex(self, color):
	        hexstring = ""
	        for col in 'red','green','blue':
	            hexfrag = hex(getattr(color,col) / (16 * 16)).split("x")[1]
	            if len(hexfrag) < 2: hexfrag = "0" + hexfrag
	            hexstring += hexfrag
	        #print 'returning hexstring: ',hexstring
	        return ('#' + str(hexstring))

class Separator:
	def __init__(self,i,base):
		self.Image = Gtk.Image()
		self.Setimage(Globals.ImageDirectory + Globals.MenuButtonImage[i])
		base.put(self.Image,Globals.MenuButtonX[i],Globals.MenuButtonY[i])

	def Setimage(self,imagefile):
		self.Pic = GdkPixbuf.Pixbuf.new_from_file(imagefile)
		self.Image.set_from_pixbuf(self.Pic)

class MenuLabel:
	def __init__(self,i,base):
		self.Label = Gtk.Label()
		self.Label.connect_after('expose-event', self.expose,i)
		self.txt = Globals.MenuLabelMarkup[i]
		self.txt = self.txt.replace(Globals.MenuLabelNames[i],_(Globals.MenuLabelNames[i]))
		if Globals.MenuLabelCommands[i] != "":
			a = commands.getoutput(str(Globals.MenuLabelCommands[i]))
			self.txt = self.txt.replace('[TEXT]',a)
		self.Label.set_markup(self.txt)
		#self.Label.set_max_width_chars(int(self.w/9))
		#self.Label.set_ellipsize(3)
		if Globals.MenuLabelNameAlignment[i] == 0:
			s = 0
		elif Globals.MenuLabelNameAlignment[i] == 1:
			s = int(self.Label.size_request()[0] /2)
		else:
			s = self.Label.size_request()[0]
		if Globals.flip == False:
			base.put(self.Label,Globals.MenuLabelX[i]-s,Globals.MenuLabelY[i]-self.Label.size_request()[1])
		else:
			base.put(self.Label,Globals.MenuLabelX[i]-s,Globals.MenuLabelY[i])
		#gc.collect()

	def expose(self,widget,event,i):
		self.txt = Globals.MenuLabelMarkup[i]

		if Globals.MenuLabelCommands[i] != "":
			a = commands.getoutput(str(Globals.MenuLabelCommands[i]))
			self.txt1 = self.txt.replace('[TEXT]',a)
			if self.txt1 != self.txt and self.txt1 != self.Label.get_label():
				
				self.Label.set_markup(self.txt1)

class ImageFrame:
	def __init__(self,w,h,ix,iy,iw,ih,base,backimage):
		self.backimagearea = None
		self.w = w
		self.h = h
		#print w,h,iw,ih,ix,iy
		self.ix = ix
		self.iy = iy
		self.iw = iw
		self.ih = ih
		self.base = base
		self.timer = None
		self.icons = [None,None,None,None]
		self.iconopacity = [0,0,0,0]
		self.step = [0,0,0,0]
		self.intrans = False 
		self.Pic = None
		self.frame_window = Gtk.EventBox()
		if not self.frame_window.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True
		self.Frame = Gtk.Fixed()
		self.Image = Gtk.Image()
		self.frame_window.set_tooltip_text(_('About Me'))
		self.frame_window.connect("button-press-event", self.but_click)
		self.frame_window.connect("composited-changed", self.composite_changed)
		self.Frame.connect('expose-event', self.expose)
		self.frame_window.add(self.Frame)
		self.frame_window.set_size_request(w,h)
		# Grab the background pixels from under the location of the menu button

		#self.backimagearea = self.backimagearea.add_alpha(True, chr(0xff), chr(0xff), chr(0xff))
		if self.backimagearea is None:
	
			if Globals.flip == False:

				self.backimagearea = backimage.subpixbuf(Globals.UserIconFrameOffsetX,Globals.MenuHeight - Globals.UserIconFrameOffsetY - self.h,self.w,self.h)
				self.backimagearea = self.backimagearea.flip(Globals.flip)
	
			else:
				self.backimagearea = backimage.subpixbuf(Globals.UserIconFrameOffsetX,Globals.UserIconFrameOffsetY,self.w,self.h)
		# Set the background which is always present
		self.Image.set_size_request(self.w,self.h)
		self.Frame.set_size_request(self.w,self.h)		
		self.SetBackground()
		self.Frame.put(self.Image,0,0)
		self.base.put(self.frame_window,self.ix,self.iy)
		self.Pic = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, self.w,self.h)
		self.Pic.fill(0x00000000)
		#gc.collect()


	def expose (self, widget, event):
		self.ctx = widget.window.cairo_create()
		# set a clip region for the expose event
		if self.supports_alpha == False:
			self.ctx.set_source_rgb(1, 1, 1)
		else:
			self.ctx.set_source_rgba(1, 1, 1,0)
		self.ctx.set_operator (cairo.OPERATOR_SOURCE)
		self.ctx.paint()
		cairo_drawing.draw_pixbuf(self.ctx,self.backimagearea)

	def composite_changed(self,widget):
		print self.frame_window.is_composited()

	def screen_changed(self,widget):
		# Screen change event
		screen = widget.get_screen()
		colormap = screen.get_rgba_colormap()
		widget.set_colormap(colormap)

	def Setimage(self):
		# The image is background when it's not displaying the overlay
		self.Image.set_from_pixbuf(None)
		self.Pic = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, self.w,self.h)
		self.Pic.fill(0x00000000)
		bg = self.Pic.copy()
		for i in range(0,len(self.iconopacity)):
			if self.icons[i] != None and self.iconopacity[i] > 0:
				if i ==1:
					self.icons[i].composite(self.Pic, self.ix, self.iy, self.icons[i].get_width(), self.icons[i].get_height(), self.ix, self.iy, 1, 1, GdkPixbuf.InterpType.BILINEAR, int(self.iconopacity[i]* 255))
				else:
					self.icons[i].composite(self.Pic, 0, 0, self.icons[i].get_width(), self.icons[i].get_height(), 0, 0, 1, 1, GdkPixbuf.InterpType.BILINEAR, int(self.iconopacity[i]* 255))
		
		self.Image.set_from_pixbuf(self.Pic)

	def SetBackground(self):
		self.Image.set_from_pixbuf(None)


	def but_click(self, widget, event):
		os.system(Globals.Settings['User'] + ' &')


	def move(self,x,y):
		# Relocate the window
		self.base.move(self.frame_window,x,y)

	def transition(self,step, speed, rate, termination_event):
		if self.timer:
			GObject.source_remove(self.timer)
			self.intrans = False
			self.Pic = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, self.w,self.h)
			self.Pic.fill(0x00000000)
		
		if step != self.step:
			if self.timer:
				GObject.source_remove(self.timer)
				self.intrans = False
		self.step = step
		if self.intrans == False:
			self.intrans = True
			# Add timer
			self.Pic = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, self.w,self.h)
			self.Pic.fill(0x00000000)
			self.timer = GObject.timeout_add(speed,self.updatefade, termination_event, rate)

	def updatefade(self, termination_event, rate):

		if self.step==[0,0,0,0]:
			self.intrans = False
			if termination_event:
				termination_event()
			return False
		for i in range(0,len(self.iconopacity)):
			self.iconopacity[i] = self.iconopacity[i] + round((rate*self.step[i]),2)
			if self.iconopacity[i] < 0: self.iconopacity[i] = 0
			if self.iconopacity[i] > 1: self.iconopacity[i] = 1
			if (self.iconopacity[i]<=0 or self.iconopacity[i]>=1) and self.step[i]!=0:
				self.step[i]=0
				
				self.iconopacity[i]=int(self.iconopacity[i])
			self.iconopacity[i]=round(self.iconopacity[i],2)
		
		self.Setimage()
		if self.step==[0,0,0,0]:
			self.Pic = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, self.w,self.h)
			self.Pic.fill(0x00000000)
			self.intrans = False
			if termination_event:
				termination_event()
			return False
		return True


	def updateimage(self,index,imagefile):

			# All .face files will load through this routine, even though they may be 'png' format 

		if index==1:

			self.temp = GdkPixbuf.Pixbuf.new_from_file(imagefile).scale_simple(self.iw,self.ih,GdkPixbuf.InterpType.BILINEAR)

		elif index==0:	

			self.temp = GdkPixbuf.Pixbuf.new_from_file(imagefile)
			self.w = self.temp.get_width()
			self.h = self.temp.get_height()
		else:
			try:
				self.temp = GdkPixbuf.Pixbuf.new_from_file_at_size(imagefile, self.w, self.h)
			except:
				print 'Warning: icon %s not found in tilo icons, trying system icons instead!' % imagefile
				image = IconFactory.GetSystemIcon(imagefile.split('/').pop())
				if not image:
					print 'Warning: icon %s was not found in system icons either!' % imagefile
					image = IconFactory.GetSystemIcon('gtk-missing-image')
				
				self.temp = GdkPixbuf.Pixbuf.new_from_file_at_size(image, self.w, self.h)
		if index==0:
			#FRAME
			self.icons[0] = self.temp
		if index==1:
			#.FACE
			self.icons[1] = self.temp
		if index==2:
			#1ST ICON
			self.icons[2] = self.temp
		if index==3:
			#2ND ICON
			self.icons[3] = self.temp


class ImageFrame_cairo_surface:#flickers
	def __init__(self,w,h,ix,iy,iw,ih,base,backimage):
		self.backimagearea = None
		# Create the window itself
		self.w = w
		self.h = h
		self.ix = ix
		self.iy = iy
		self.iw = iw
		self.ih = ih
		self.frame_window = Gtk.EventBox()
		self.frame_window.set_tooltip_text(_('About Me'))
		base.put(self.frame_window,self.ix,self.iy)
		
		self.frame_window.set_size_request(w,h)
		#Connect redraw-events
		self.frame_window.connect("button-press-event", self.but_click)
		self.frame_window.connect("composited-changed", self.composite_changed)
		self.frame_window.connect_after('expose-event', self.expose)
		self.frame_window.connect('screen-changed', self.screen_changed)
		self.frame_window.connect('destroy', self.destroy)
		self.icons = [None,None,None,None]
		self.timer = None
		self.screen_changed(self.frame_window)
		if self.backimagearea is None:
	
			if Globals.flip == False:

				self.backimagearea = backimage.subpixbuf(Globals.UserIconFrameOffsetX,Globals.MenuHeight - Globals.UserIconFrameOffsetY - self.h,self.w,self.h)
				self.backimagearea = self.backimagearea.flip(Globals.flip)
	
			else:
				self.backimagearea = backimage.subpixbuf(Globals.UserIconFrameOffsetX,Globals.UserIconFrameOffsetY,self.w,self.h)
		self.resizematch(self.w,self.h)		
		self.iconopacity = [0,0,0,0]
		self.step = [0,0,0,0]
		self.intrans = False 
		self.backbuffer = None
		#gc.collect()


		
	def but_click(self, widget, event):
		os.system('%s &' % Globals.Settings['User'])

	def transition(self,step, speed, rate, termination_event):
		self.step = step
		if self.timer is None:
			self.timer = GObject.timeout_add(speed,self.updatefade, termination_event, rate)
	
	def composite_changed(self,widget):
		print self.frame_window.is_composited()

	def updatefade(self, termination_event, rate):

		for i in range(0,len(self.iconopacity)):
			if self.step[i]!=0:
				self.iconopacity[i] = self.iconopacity[i] + (rate*self.step[i])
				if self.iconopacity[i] < rate: self.iconopacity[i] = 0
				if self.iconopacity[i] > 1-rate: self.iconopacity[i] = 1
				if (self.iconopacity[i]<=0 or self.iconopacity[i]>=1):
					self.step[i]=0
	

		self.Redraw()
		if self.step==[0,0,0,0]:
			self.timer = None
			return False
		return True
		
	def screen_changed(self,widget):
		# Screen change event
		screen = widget.get_screen()
		colormap = screen.get_rgba_colormap()
		widget.set_colormap(colormap)
	
	def expose(self,widget,event):
		self.Redraw()
	
	def Redraw(self):
		if self.frame_window.window :
			self.cr = self.frame_window.window.cairo_create()

			if self.frame_window.is_composited() is True:	
				self.cr.save()
				self.cr.set_source_rgba(1, 1, 1, 0)
				self.cr.set_operator (cairo.OPERATOR_SOURCE)
				self.cr.set_source_pixbuf(self.backimagearea, 0, 0)
				self.cr.paint()
				self.cr.restore()
				self.cr.set_operator(cairo.OPERATOR_OVER) #DEST_ATOP
				#self.iconopacity.sort()
				for i in range(0,len(self.iconopacity)):
					if self.icons[i] != None and self.iconopacity[i] > 0:
						if i == 1:
							self.cr.set_source_surface(self.icons[i], self.ix, self.iy)				
						else:
							self.cr.set_source_surface(self.icons[i], 0, 0)
						self.cr.paint_with_alpha(round(self.iconopacity[i],2))

			else:
				self.cr.set_source_rgb(1, 1, 1)
				self.cr.set_operator (cairo.OPERATOR_SOURCE)
				self.cr.paint()
				self.cr.set_operator(cairo.OPERATOR_OVER) #DEST_ATOP
				self.cr.set_source_pixbuf(self.backimagearea, 0, 0)
				self.cr.paint()
				
				for i in range(0,len(self.iconopacity)):
					if self.icons[i] != None and self.iconopacity[i] > 0:
						if i == 1:
							self.cr.set_source_surface(self.icons[i], self.ix, self.iy)				
						else:
							self.cr.set_source_surface(self.icons[i], 0, 0)
						self.cr.paint_with_alpha(round(self.iconopacity[i],2))

	def move(self,x,y):
		# Relocate the window
		self.frame_window.set_uposition(x,y)


	def resize(self,w,h):
		self.frame_window.set_size_request(w,h)

	def resizematch(self,w,h):
		self.frame_window.set_size_request(w,h)
	
	def destroy(self,event):
		# Remove the window
		self.frame_window.destroy()
		Gtk.main_quit()

	def update(self):
		# Update the screen profile on request
		self.screen_changed(self.frame_window)
		
	def updateimage(self,index,imagefile):


		if index==0:

			self.temppixbuf = GdkPixbuf.Pixbuf.new_from_file(imagefile)
			self.w = self.temppixbuf.get_width()
			self.h = self.temppixbuf.get_height()

		elif index==1:

			self.temppixbuf = GdkPixbuf.Pixbuf.new_from_file(imagefile).scale_simple(self.iw,self.iw,GdkPixbuf.InterpType.BILINEAR)

		else:
			self.temppixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(imagefile, self.w, self.h)

		self.temp = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
		self.cr2 = cairo.Context(self.temp)
		self.ct = Gdk.CairoContext(self.cr2)
		self.ct.set_source_pixbuf(self.temppixbuf,0,0)
		self.ct.paint()

		if index==0:
			#FRAME
			self.icons[0] = self.temp
		elif index==1:
			#.FACE
			self.icons[1] = self.temp
		elif index==2:
			#1ST ICON
			self.icons[2] = self.temp
		elif index==3:
			#2ND ICON
			self.icons[3] = self.temp


class ImageFrame_new:
	def __init__(self,w,h,ix,iy,iw,ih,base,backimage):
		self.backimagearea = None
		# Create the window itself
		self.w = w
		self.h = h
		self.ix = ix
		self.iy = iy
		self.iw = iw
		self.ih = ih
		self.frame_window = Gtk.EventBox()
		self.frame_window.set_tooltip_text(_('About Me'))
		base.put(self.frame_window,self.ix,self.iy)
		
		self.frame_window.set_size_request(w,h)
		#Connect redraw-events
		self.frame_window.connect("button-press-event", self.but_click)
		self.frame_window.connect("composited-changed", self.composite_changed)
		self.frame_window.connect_after('expose-event', self.expose)
		self.frame_window.connect('screen-changed', self.screen_changed)
		self.frame_window.connect('destroy', self.destroy)
		self.icon1=cairo.ImageSurface
		self.icon2=cairo.ImageSurface
		self.icon3=cairo.ImageSurface
		self.icon4=cairo.ImageSurface
		self.timer = None
		self.screen_changed(self.frame_window)
		if self.backimagearea is None:
	
			if Globals.flip == False:

				self.backimagearea = backimage.subpixbuf(Globals.UserIconFrameOffsetX,Globals.MenuHeight - Globals.UserIconFrameOffsetY - self.h,self.w,self.h)
				self.backimagearea = self.backimagearea.flip(Globals.flip)
	
			else:
				self.backimagearea = backimage.subpixbuf(Globals.UserIconFrameOffsetX,Globals.UserIconFrameOffsetY,self.w,self.h)
		self.resizematch(self.w,self.h)		
		self.iconopacity = [0,0,0,0]
		self.step = [0,0,0,0]
		self.intrans = False 
		#gc.collect()

		
	def but_click(self, widget, event):
		os.system('%s &' % Globals.Settings['User'])

	def transition(self,step, speed, rate, termination_event):
		if self.timer:
			GObject.source_remove(self.timer)
			self.intrans = False
		
		if step != self.step:
			if self.timer:
				GObject.source_remove(self.timer)
				self.intrans = False
		self.step = step
		if self.intrans == False:
			self.intrans = True
			# Add timer
			self.timer = GObject.timeout_add(speed,self.updatefade, termination_event, rate)

	def composite_changed(self,widget):
		print self.frame_window.is_composited()

	def updatefade(self, termination_event, rate):

		for i in range(0,len(self.iconopacity)):

			self.iconopacity[i] = self.iconopacity[i] + (rate*self.step[i])
			if self.iconopacity[i] < 0: self.iconopacity[i] = 0
			if self.iconopacity[i] > 1: self.iconopacity[i] = 1
			if (self.iconopacity[i]<=0 or self.iconopacity[i]>=1):
				self.step[i]=0


		self.Redraw()
		if self.step==[0,0,0,0]:
			self.intrans = False
			if termination_event:
				termination_event()
			return False
		return True
	


		
	def screen_changed(self,widget):
		# Screen change event
		screen = widget.get_screen()
		colormap = screen.get_rgba_colormap()
		widget.set_colormap(colormap)
	
	def expose(self,widget,event):
		self.Redraw()
	
	def Redraw(self):
		if self.frame_window.window :
			self.cr = self.frame_window.window.cairo_create()
			if self.frame_window.is_composited() is True:	
				self.cr.set_source_rgba(1, 1, 1, 0)
				self.cr.set_operator (cairo.OPERATOR_SOURCE)
				pixbuf = self.backimagearea

				self.cr.set_source_pixbuf(pixbuf, 0, 0)
				self.cr.paint()
				#self.cr.set_operator(cairo.OPERATOR_OVER) #DEST_ATOP
				
				if self.iconopacity[0] != 0:
					self.icon1.paint_with_alpha(self.iconopacity[0])
				if self.iconopacity[1] != 0:
					self.icon2.paint_with_alpha(self.iconopacity[1])
				if self.iconopacity[2] != 0:
					self.icon3.paint_with_alpha(self.iconopacity[2])
				if self.iconopacity[3] != 0:
					self.icon4.paint_with_alpha(self.iconopacity[3])
			else:
				self.cr.set_source_rgb(1, 1, 1)
				self.cr.set_operator (cairo.OPERATOR_SOURCE)
				self.cr.paint()
				self.cr.set_operator(cairo.OPERATOR_OVER) #DEST_ATOP
				pixbuf = self.backimagearea
				self.cr.set_source_pixbuf(pixbuf, 0, 0)
				self.cr.paint()
				
				if isinstance(self.icon1,cairo.Surface):
					self.ctx.paint_with_alpha(self.iconopacity[0])
				if isinstance(self.icon2,cairo.Surface):
					self.ctx.paint_with_alpha(self.iconopacity[1])
				if isinstance(self.icon3,cairo.Surface):
					self.ctx.paint_with_alpha(self.iconopacity[2])
				if isinstance(self.icon4,cairo.Surface):
					self.ctx.paint_with_alpha(self.iconopacity[3])				
			
	def move(self,x,y):
		# Relocate the window
		self.frame_window.set_uposition(x,y)


	def resize(self,w,h):
		self.frame_window.set_size_request(w,h)

	def resizematch(self,w,h):
		self.frame_window.set_size_request(w,h)
	
	def destroy(self,event):
		# Remove the window
		self.frame_window.destroy()
		Gtk.main_quit()

	def update(self):
		# Update the screen profile on request
		self.screen_changed(self.frame_window)
		
	def updateimage(self,index,imagefile):

			# All .face files will load through this routine, even though they may be 'png' format 

			# Update the graphic being displayed (first image has size priority)

		if index==0:
			#FRAME

			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(imagefile,self.w,self.h)
			# Resize the image and create the cairo surface to be used
			self.icon1 = self.frame_window.window.cairo_create()
			self.temp = self.icon1.set_source_pixbuf(pixbuf, 0, 0)
		if index==1:
			#.FACE
			pixbuf = GdkPixbuf.Pixbuf.new_from_file(imagefile).scale_simple(self.iw,self.iw,GdkPixbuf.InterpType.BILINEAR)
			# Resize the image and create the cairo surface to be used
			self.icon2 = self.frame_window.window.cairo_create()
			self.temp = self.icon2.set_source_pixbuf(pixbuf, self.ix, self.iy)
			if Globals.MenuHasFade != 1:
				self.iconopacity = [1,1,-1,-1]
		if index==2:
			#1ST ICON
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(imagefile,self.w,self.h)
			# Resize the image and create the cairo surface to be used
			self.icon3 = self.frame_window.window.cairo_create()
			self.temp = self.icon3.set_source_pixbuf(pixbuf, 0, 0)
		if index==3:
			#2ND ICON
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(imagefile,self.w,self.h)
			# Resize the image and create the cairo surface to be used
			self.icon4 = self.frame_window.window.cairo_create()
			self.temp = self.icon4.set_source_pixbuf(pixbuf, 0, 0)
		#self.Redraw()

class GtkSearchBar(Gtk.Entry):
	def __init__(self):
		GObject.GObject.__init__(self)
		if Globals.Settings['GtkColors'] == 0:
			self.modify_base(Gtk.StateType.NORMAL, Globals.ThemeColorCode)

		self.connect("expose_event", self.expose)
		try:
			if self.text != _('Search'):
				self.font_desc = Pango.FontDescription('sans italic')
			else:
				self.font_desc = Pango.FontDescription('sans')
			self.modify_font(self.font_desc)
		except:pass
		if Globals.Settings['GtkColors'] == 0:
			self.modify_text(Gtk.StateType.NORMAL, Globals.NegativeThemeColorCode)
	   
	def expose (self, widget, event):
		try:
			if self.text != _('Search'):
				self.font_desc = Pango.FontDescription('sans italic')
			else:
				self.font_desc = Pango.FontDescription('sans')
			self.modify_font(self.font_desc)
		except:pass
				
class CairoSearchBar(Gtk.Entry):
 #   __gsignals__ = {
  #           'expose-event':   'override'}
	def __init__(self,BackColor="#FFFFFF",BorderColor="#000000",TextColor="#000000"):
		GObject.GObject.__init__(self)
		if Globals.Settings['GtkColors'] == 1:
			self.Backcolor = Globals.GtkColorCode
		else:
			self.Backcolor = Gdk.color_parse(BackColor)
		self.Backcolor_r = (self.Backcolor.red)/65535.0
		self.Backcolor_g = (self.Backcolor.green)/65535.0
		self.Backcolor_b = (self.Backcolor.blue)/65535.0
		self.Bordercolor = Gdk.color_parse(BorderColor)
		self.Bordercolor_r = (self.Bordercolor.red)/65535.0
		self.Bordercolor_g = (self.Bordercolor.green)/65535.0
		self.Bordercolor_b = (self.Bordercolor.blue)/65535.0
		#for state in [Gtk.StateType.ACTIVE, Gtk.StateType.NORMAL,Gtk.StateType.PRELIGHT, Gtk.StateType.SELECTED]: 
		self.modify_bg(Gtk.StateType.NORMAL, self.Backcolor)
		self.modify_base(Gtk.StateType.NORMAL, self.Backcolor)
		self.modify_text(Gtk.StateType.NORMAL, Gdk.color_parse(TextColor))
		self.connect("expose_event", self.expose)
		try:
			if self.text != _('Search'):
				self.font_desc = Pango.FontDescription('sans italic')
			else:
				self.font_desc = Pango.FontDescription('sans')
			self.modify_font(self.font_desc)
		except:pass
			   
	def expose (self, widget, event):
		self.cr = widget.window.cairo_create()
		self.cr.save()
		self.allocation = widget.allocation
		if self.is_composited() is True:	
			self.cr.set_source_rgba(1, 1, 1, 0)
		else:
			self.cr.set_source_rgb(1, 1, 1)
		self.cr.set_operator (cairo.OPERATOR_SOURCE)
		self.cr.paint()
		self.cr.restore()
		#self.cr.set_operator(cairo.OPERATOR_OVER) #DEST_ATOP
		r=5
		x0=0
		x1=x0+self.allocation.width
		y0=0
		y1=y0+self.allocation.height
		self.cr.rectangle(x0+1, y0+1, x1-1, y1-1)
		self.cr.set_source_rgb(self.Backcolor_r,self.Backcolor_g,self.Backcolor_b)
		self.cr.fill()
		self.cr.rectangle(x0, y0, x1, y1)
		self.cr.set_source_rgb(self.Bordercolor_r,self.Bordercolor_g,self.Bordercolor_b)
		self.cr.stroke()
		try:
			if self.text != _('Search'):
				self.font_desc = Pango.FontDescription('sans italic')
			else:
				self.font_desc = Pango.FontDescription('sans')
			self.modify_font(self.font_desc)
		except:pass

class CustomSearchBar_new:
	def __init__(self, base, BackImageFile=None, InitialText="",TextColor="#000000",SearchX=0,SearchY=0,SearchW=0,SearchH=0, X=4, Y=15,colorpb=None):
		self.backimagearea = None
		self.Button = Gtk.EventBox()
		self.Frame = Gtk.Fixed()
		if not self.Button.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True
		self.Button.connect("composited-changed", self.composite_changed)
		self.Frame.connect("expose_event", self.expose)
		self.Button.add(self.Frame)

class CustomSearchBar(Gtk.Widget):
	def __init__(self, BackImageFile=None, InitialText="",TextColor="#000000",SearchX=0,SearchY=0,SearchW=0,SearchH=0, X=4, Y=15,colorpb=None):
		GObject.GObject.__init__(self)
		self.connect("expose_event", self.expose)#enter-notify-event

		self.colorpb = colorpb
		# Text Settings
		self.text = ""
		self.initialtext = InitialText
		self.TextColor = TextColor
		self.cursor = 0
		self.selection = False
		self.cursorblink = False
		self.cursorvisible = False
		color = Gdk.color_parse(TextColor)
		self.color_r = (color.red)/65535.0
		self.color_g = (color.green)/65535.0
		self.color_b = (color.blue)/65535.0		
		self.originalw = 0
		self.originalh = 0
		# Graphical Settings
		self.sx = SearchX
		self.sy = SearchY
		self.sw = SearchW
		self.sh = SearchH
		self.x = X
		self.y = Y
		self.hasrectangle = False
		self.cornerradius = 12
		self.backimage = BackImageFile
		self.backimagepb = GdkPixbuf.Pixbuf.new_from_file(self.backimage)
		self.BackImageBuffer = None
		if Globals.flip == False:

			self.backimagearea = self.colorpb.subpixbuf(self.sx,Globals.MenuHeight - self.sy-self.sh,self.sw,self.sh)
			self.backimagearea = self.backimagearea.flip(Globals.flip)
	
		else:
			self.backimagearea = self.colorpb.subpixbuf(self.sx,self.sy,self.sw,self.sh)
		if not self.is_composited():
	 
			self.supports_alpha = False
		else:
			self.supports_alpha = True


	def enter(self, widget, event):
		self.window.set_cursor(Gdk.Cursor.new(Gdk.XTERM))

	def leave(self, widget, event):
		self.window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.ARROW))
		
	def do_realize(self):
		# Create events
		self.set_flags(self.flags() | Gtk.REALIZED | Gtk.CAN_FOCUS | Gtk.HAS_FOCUS)
		
		# Create window for widget to be displayed in
			
		self.window = Gdk.Window(
			self.get_parent_window(),
			width=self.allocation.width,
			height=self.allocation.height,
			window_type=Gdk.WINDOW_CHILD,
			wclass=Gdk.INPUT_OUTPUT,
			event_mask=self.get_events() | Gdk.EventMask.EXPOSURE_MASK | Gdk.EventMask.KEY_PRESS_MASK  | Gdk.EventMask.KEY_RELEASE_MASK | Gdk.EventMask.FOCUS_CHANGE_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK 
| Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)

		
				
				
		# Associate the Gdk.Window with ourselves, Gtk+ needs a reference
		# between the widget and the gdk window
		self.window.set_user_data(self)
		
		# Attach the style to the Gdk.Window, a style contains colors and
		# GC contextes used for drawing
		self.style.attach(self.window)
		

		# The default color of the background should be what
		# the style (theme engine) tells us.
		self.style.set_background(self.window, Gtk.StateType.NORMAL)

		if Globals.Settings['GtkColors'] == 1:
			bgcolor = Globals.GtkColorCode
			self.t_color_r = 65535.0 - (bgcolor.red*255)/65535.0
			self.t_color_g = 65535.0- (bgcolor.green*255)/65535.0
			self.t_color_b = 65535.0- (bgcolor.blue*255)/65535.0
		else:
			color = Gdk.color_parse(self.TextColor)
			self.t_color_r = (color.red)/65535.0
			self.t_color_g = (color.green)/65535.0
			self.t_color_b = (color.blue)/65535.0
		self.window.move_resize(*self.allocation)
		
		# self.style is a Gtk.Style object, self.style.fg_gc is
		# an array or graphic contexts used for drawing the forground
		# colours	
		self.gc = self.style.fg_gc[Gtk.StateType.NORMAL]
		self.connect("key_press_event", self.do_keypress)
		self.connect("enter_notify_event", self.enter)
		self.connect("leave_notify_event", self.leave)
		#if self.cursorvisible:
		GObject.timeout_add(700,self.blinkcursor)
		
	def do_keypress(self,widget,event):
		key = event.hardware_keycode
		if key==9:
			self.text=""
			self.window.invalidate_rect(None,False)						
		elif key==22 and self.cursor>0:
			self.text = self.text[0:len(self.text)-1]
			self.window.invalidate_rect(None,False)
		else:
			self.text=self.text+event.string
			self.cursor = self.cursor + 1
			self.window.invalidate_rect(None,False)
	
	def set_text(self,text):
		self.text = text
		self.window.invalidate_rect(None,False)
	
	def get_text(self):
		return self.text

	def expose(self, widget, event):
		# Redraw the window
		self.context = widget.window.cairo_create()
		# Set the region to be redrawn
		self.context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
		self.context.clip()
		self.context.set_operator (cairo.OPERATOR_SOURCE)
		self.context.set_source_pixbuf(self.backimagearea, 0, 0)
		self.context.paint()
		self.context.set_operator (cairo.OPERATOR_OVER)
		self.draw(self.context)
		return False
	
	def blinkcursor(self):
		self.cursorblink = not self.cursorblink
		self.window.invalidate_rect(None,False)
		#Fixme Invalidate only the leading cursor-edge region
		return True
	
	def draw(self,context):
		# Get widget dimensions
		rect = self.get_allocation()
		x = rect.x + rect.width / 2
		y = rect.y + rect.height / 2
		w = self.allocation.width
		h = self.allocation.height
		
		# If button has changed shape, redraw it's background
		if w!=self.originalw or h!=self.originalh:
			self.BuildBackground(w,h)
			self.originalw = w
			self.originalh = h

		# Draw background
		context.set_source_surface(self.buttonsurface,0,0)
		context.paint()
		
		# Draw text to the text box
		context.move_to(self.x,self.y)
		if self.text == "" or self.text == _('Search'):
			context.select_font_face("Sans",cairo.FONT_SLANT_ITALIC,cairo.FONT_WEIGHT_NORMAL)
			context.set_font_size(12)
			context.set_source_rgba(self.t_color_r,self.t_color_g,self.t_color_b,0.6)
			context.show_text (_('Search'))
			if self.cursorblink:
				context.set_source_rgba(self.t_color_r,self.t_color_g,self.t_color_b,0.6)
				context.show_text ('|')
		else:
			context.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
			context.set_font_size(12)
			context.set_source_rgba(self.t_color_r,self.t_color_g,self.t_color_b,1)
			context.show_text (self.text)
			if self.cursorblink:
				context.set_source_rgba(self.t_color_r,self.t_color_g,self.t_color_b,0.8)
				context.show_text ('|')

	def BuildBackground(self,w,h):
		self.buttonsurface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
		context = cairo.Context(self.buttonsurface)
		self.ct = Gdk.CairoContext(context)
		if Globals.Settings['GtkColors'] == 1:
			cairo_drawing.draw_image_gtk(self.ct,0,0,self.backimage,w,h,Globals.GtkColorCode,None,False)
		else:
			cairo_drawing.draw_image(self.ct,0,0,self.backimage,False)
		if self.BackImageBuffer:
			context.set_source_surface(self.BackImageBuffer, 0, 0)			
			context.paint()
		if self.hasrectangle:
			# Draw the box
			self.DrawRoundedRect(context,0,0,w,h,self.cornerradius)
			# Fill
			context.set_source_rgba(self.color_r,self.color_g,self.color_b,1)
			context.paint()
		

	def DrawRoundedRect(self,context,x0,y0,w,h,radius):
		x1=x0+w
		y1=y0+h
		context.move_to(x0, y0 + radius)
		context.curve_to(x0 , y0, x0 , y0, x0 + radius, y0)
		context.line_to(x1 - radius, y0)
		context.curve_to(x1, y0, x1, y0, x1, y0 + radius)
		context.line_to(x1 , y1 - radius)
		context.curve_to(x1, y1, x1, y1, x1 - radius, y1)
		context.line_to(x0 + radius, y1)
		context.curve_to(x0, y1, x0, y1, x0, y1- radius)		 
		context.close_path()

class TreeProgramList(GObject.GObject):

	__gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_LAST, None, ()),
        'menu': (GObject.SignalFlags.RUN_LAST, None, ()),
        'clicked': (GObject.SignalFlags.RUN_LAST, None, ()),
        'right-clicked': (GObject.SignalFlags.RUN_LAST, None, ())
        }
	def __init__(self):
		GObject.GObject.__init__ (self)
		#Create the Base Menu Template and an XDG menu object
		self.XDG = XDMateMenu()
		self.XDG.connect('changed', self.menu_callback)
		#if Globals.flip == False:
		#	self.backimagearea = backimage.subpixbuf(Globals.PG_buttonframe[0],Globals.MenuHeight - Globals.PG_buttonframe[1] - Globals.PG_buttonframedimensions[1],Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
		#	self.backimagearea = self.backimagearea.flip(Globals.flip)
		#else:
		#	self.backimagearea = backimage.subpixbuf(Globals.PG_buttonframe[0],Globals.PG_buttonframe[1] ,Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
#=================================================================  
#GRAPHICAL CODE FOR MENU
#=================================================================  
	def menu_callback(self,event):
		
		self.Restart('previous')

	def ProgramListPopulate(self,Frame,Destroyer):
		self.BanFocusSteal = False
		self.Destroyer=Destroyer
		self.Frame=Frame
		self.ConstructGTKObjectsMenu(self.Frame)
		self.PopulateButtons()
        
	def ConstructGTKObjectsMenu(self, Frame):
		# Create components Frame -> ScrollFrame -> EventBox -> VBox -> Buttons
		self.ScrollFrame = Gtk.ScrolledWindow()
		self.VBoxOut = Gtk.VBox(False)
		self.EBox = Gtk.EventBox()
		self.tree1 = Gtk.TreeView()
		self.Button = Gtk.Button()
   		self.render = Gtk.CellRendererPixbuf()
		self.cell1 = Gtk.CellRendererText()
		self.column1 = Gtk.TreeViewColumn("", self.render,pixbuf=0)
		self.column2 = Gtk.TreeViewColumn("", self.cell1,text=1)
		self.Separator = None
		self.gtkicontheme = Gtk.IconTheme.get_default()
		self.gtkicontheme.connect('changed', self.update_icons) 
		targets = [('text/uri-list', 0, 0)]
		#self.tree1.connect("expose_event", self.expose)
		#self.EBox.connect("expose_event", self.expose)	
		#self.VBoxOut.connect("expose_event", self.expose)
		#self.ScrollFrame.connect("expose_event", self.expose)	
		#if Globals.Settings['GtkColors'] == 0:
			
			#self.VBoxOut.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			#self.ScrollFrame.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)

		#self.ScrollFrame.connect_after("map-event", self.map_event)
		self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])	  
		self.ScrollFrame.set_shadow_type(Gtk.ShadowType.NONE)
		self.ScrollFrame.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)

		self.VBoxOut.pack_start(self.ScrollFrame, True,True, 0)
		self.ScrollFrame.add(self.tree1)
		self.EBox.add(self.VBoxOut)
		self.Frame.put(self.EBox,Globals.PG_buttonframe[0],Globals.PG_buttonframe[1])
		self.tree1.set_headers_visible (0)
		self.tree1.append_column(self.column1)
		self.tree1.append_column(self.column2)

		if Globals.Settings['Show_Tips']:
			
			self.column3 = Gtk.TreeViewColumn("", self.cell1,text=1)
			self.column3.set_visible(False)
			self.tree1.append_column(self.column3)
			self.tree1.set_tooltip_column(2)
			

		
		self.tree1.set_cursor_on_cell((0,0), focus_column=None,focus_cell=None, start_editing=False)
		if Globals.Settings['Show_Tips']:
			self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, GObject.TYPE_STRING, GObject.TYPE_STRING)
		else:
			self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, GObject.TYPE_STRING)
		self.tree1.connect("key-press-event", self.PGListButtonKey)
		self.tree1.connect("drag-data-get", self.drag_data_get)
		self.tree1.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,targets,Gdk.DragAction.COPY)
		self.tree1.drag_source_add_text_targets()
		self.tree1.connect("button-press-event", self.drag_begin)
		self.tree1.connect("button-release-event", self.treeclick)
		self.cell1.set_property('ellipsize', Pango.EllipsizeMode.END)
		self.tree1.set_model(self.model)
		if Globals.Settings['GtkColors'] == 0:
			self.EBox.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			#self.cell1.set_property('background', Globals.ThemeColorCode)
			self.cell1.set_property('cell-background', Globals.ThemeColorCode)
			self.render.set_property('cell-background', Globals.ThemeColorCode)
			#self.tree1.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			self.tree1.modify_base(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			self.cell1.set_property('foreground',Globals.NegativeThemeColorCode)

		self.tree1.set_hover_selection(True)
		
		#gc.collect()

	def drag_begin(self, widget, drag_context):
		selection = widget.get_selection()
		selection.set_mode('single')
		model, iter = selection.get_selected()
		if iter:
			self.index = int(model.get_path(iter)[0])
			self.tree1.drag_source_set_icon_pixbuf(model.get_value(iter,0))

	def drag_data_get (self, widget, drag_context, selection_data, info, timestamp):
		uri_list = None
		if self.XDG.allgio is not None:
			for z in self.XDG.allgio:
				if z.get_name() == self.XDG.L_Names[self.index]:
					uri_list = 'file:///usr/share/applications/%s' % z.get_id()
					break
		if uri_list is None:
			name = str(self.XDG.L_Execs[self.index]).replace('%F','').replace('%f','').replace('%u','').replace('%U','')
			if name.startswith ('file:/'):
				uri_list = name
			elif name.startswith ('/'):
				uri_list = 'file://%s' % name
			else:
				uri_list = 'file:///usr/bin/%s' % name
		
		selection_data.set(selection_data.target, 8,uri_list)

	def update_icons(self,client, connection_id=None, entry=None, args=None):
		print 'icons changed'
		self.XDG.Icon_change()
		self.Restart('previous')

	def Restart(self,data='all'):

		if self.XDG.Restart(data):
			self.PopulateButtons()
		#gc.collect()

	def expose(self, widget, event):
		#widget.window.set_composited(1)
		cr = widget.window.cairo_create()
		if widget.is_composited() is True:	
			cr.set_source_rgba(1, 1, 1, 0)
		else:
			cr.set_source_rgb(1, 1, 1)
		cr.set_operator (cairo.OPERATOR_SOURCE)
		cr.paint()
		#cairo_drawing.draw_pixbuf(cr,self.backimagearea)

	def treeclick(self,widget,event):
		"""activated when clicking in the tree"""
		selection = widget.get_selection()
		selection.set_mode('single')
		rows = selection.get_selected_rows()[1]
		if rows:
			self.index = int(rows[0][0])
			self.ActivateButton(event)

	def map_event(self, widget, event):
		print 'map'
		self.PopulateButtons()


	def RemoveButtons(self):
		self.tree1.set_model(None)
		if self.Separator:
			self.Separator.destroy()
		try:
			self.Button.destroy()
		except:pass
		try:
			self.Label.destroy()
		except:pass
		# doing the following is faster then self.model.clear()
		if Globals.Settings['Show_Tips']:
			self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, GObject.TYPE_STRING, GObject.TYPE_STRING)
		else:
			self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, GObject.TYPE_STRING)
		
		self.tree1.freeze_child_notify()

		

	def PopulateButtons(self):
		self.RemoveButtons()
		self.Buttonlist = []
		#a = time.clock()
		for i in range(0,len(self.XDG.L_Names)):
			typ = self.XDG.L_Types[i]
			if typ==8:
				self.dummy()#self.AddSeparator())
			elif typ==9:
				self.AddLabel(self.XDG.L_Names[i])
			elif typ==2:
				self.AddBackButton(self.XDG.L_Names[i],self.XDG.L_Icons[i],i)
			else:
				self.AddButton(self.XDG.L_Names[i],self.XDG.L_Icons[i],i)
		#print time.clock() 
		#self.SetInputFocus()
		#gc.collect()
		self.tree1.set_model(self.model)
		self.tree1.thaw_child_notify()
		self.ScrollFrame.get_vscrollbar().set_value(0)


	def AddBackButton(self,name,icon,i):
		if name == _('Back'):
			if not icon:
				icon = GdkPixbuf.Pixbuf.new_from_file_at_size(Globals.BrokenImage, Globals.PG_iconsize, Globals.PG_iconsize)

		
			self.Button = Gtk.Button(name)
			self.Img = Gtk.Image()
			self.Img.set_from_pixbuf(icon)
			self.Button.set_image(self.Img)
			self.Button.set_alignment(0,0)
			self.Button.set_tooltip_text(_('Return to last menu'))
			self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
			self.Button.set_size_request(self.PG_buttonwidth, Globals.PG_iconsize+8)
			self.Button.set_relief(Gtk.ReliefStyle.NONE)
			self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],self.ScrollFrame.get_size_request()[1] - 	self.Button.get_size_request()[1])
			self.AddSeparator2()
			self.VBoxOut.pack_start(self.Button, True,True, 0)
			self.Button.connect("button-release-event", self.PGListButtonClick,i)
			self.Button.connect("key-press-event", self.PGListButtonKey,i)
			self.Button.show()
			image,label =  self.Button.get_children()[0].get_children()[0].get_children()
			if Globals.Settings['GtkColors'] == 0:
				label.modify_fg(Gtk.StateType.NORMAL, Globals.NegativeThemeColorCode)
			label.set_property("ellipsize", Pango.EllipsizeMode.END) 
			label.set_max_width_chars(int(Globals.PG_buttonframedimensions[0]/11))
			self.Buttonlist.append(self.Button)
			icon = None
		else:
			self.AddButton(name,icon,i)

	def AddButton(self,name,icon,i):

		if not icon:
			icon = GdkPixbuf.Pixbuf.new_from_file_at_size(Globals.BrokenImage, Globals.PG_iconsize, Globals.PG_iconsize)

		self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
		if Globals.Settings['Show_Tips']:
			try:
				comment = self.XDG.ItemComments[name]
			except KeyError: 
				comment = name
			self.model.insert(i,[icon,name,comment])
		else:
			self.model.insert(i,[icon,name])
		icon = None
		

	def AddLabel(self,name):
		self.Label = Gtk.Label(label=name)
		self.Label.set_line_wrap(True)
		self.Label.set_property("ellipsize", Pango.EllipsizeMode.END) 
		self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
		if self.Separator:
			self.Separator.set_size_request(self.PG_buttonwidth, 1)
		self.VBoxOut.pack_start(self.Label, False,False, 0)
		if Globals.Settings['GtkColors'] == 0:
			self.Label.modify_fg(Gtk.StateType.NORMAL, Globals.NegativeThemeColorCode)
		self.Label.show()
		self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1]- self.Label.size_request()[1]-1)
	


	def AddSeparator2(self):
		self.Separator = Gtk.HSeparator()
		self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
		self.Separator.set_size_request(self.PG_buttonwidth, 1)
			
		self.VBoxOut.pack_start(self.Separator, False,False, 0)
		self.Separator.show()
		return self.Separator

	def dummy(self):
		pass

	def AddSeparator(self):
		self.Separator = Gtk.HSeparator()
		self.model.append([None,'',''])
		

	def PGListButtonClick(self, widget, event,i):
		"""activated when clicking a button"""
		self.index = i
		self.ActivateButton(event)
		if event.button == 3:
			self.emit('menu')
		
	def ActivateButton(self,event):
		if event.type == Gdk.KEY_PRESS:event_button = 1
		elif event.type == Gdk.EventType.BUTTON_PRESS:event_button = event.button
		elif event.type ==  Gdk.BUTTON_RELEASE:event_button = event.button

		self.type = self.XDG.L_Types[self.index]
		a = self.XDG.ButtonClick(self.index,event)
		if event_button == 1:
			if a==1:
				self.Destroyer()
			self.PopulateButtons()
			self.emit('clicked')
			#gc.collect()
		elif event_button == 3:
			self.emit('right-clicked')

	def PGListButtonKey(self, widget, event,i=None):
		key = event.hardware_keycode
		if widget == self.tree1:
			if key == 36 or key == 65 or key == 114:	#Enter or Space or right
				selection = widget.get_selection()
				selection.set_mode('single')
				rows = selection.get_selected_rows()[1]
				if rows:
					self.index = int(rows[0][0])
					self.ActivateButton(event)
	
			elif key == 113: #Left
				self.Restart('previous')
		else:
			if key == 36 or key == 65 or key == 114:	#Enter or Space or right
				self.index = i
				self.ActivateButton(event)
			
			
	def SetInputFocus(self):
		# Give keyboard input focus to last item on list or to sub menu program group start
		pass

	def SetFirstButton(self,event):
		pass#self.Buttonlist[0].grab_focus()

	def SetLastButton(self,event):
		pass#self.Buttonlist[len(self.XDG.L_Names)-1].grab_focus()

#=================================================================  
#EXTRA FUNCTION PASSTHROUGH TO XDG
#See XDG module for command opcodes
#=================================================================  

	def CallSpecialMenu(self,command,data=None):
		self.XDG.CallSpecialMenu(command,data)
		self.PopulateButtons()
		#gc.collect()

	def destroy(self):
		self.XDG.destroy() #Allows XDG to de-initialse correctly (VERY IMPORTANT)




class CellRendererImage(Gtk.CellRenderer):

	__gproperties__ = {
		"image": (GObject.TYPE_PYOBJECT, "Image",
		"Image", GObject.PARAM_READWRITE),
	}

	def __init__(self):
		self.__gobject_init__()
		self.image = None

	def do_set_property(self, pspec, value):
		setattr(self, pspec.name, value)

	def do_get_property(self, pspec):
		return getattr(self, pspec.name)

	def func(self, model, path, iter, (image, tree)):
		if model.get_value(iter, 0) == image:
			self.redraw = 1
			cell_area = tree.get_cell_area(path, tree.get_column(0))
			tree.queue_draw_area(cell_area.x, cell_area.y, cell_area.width, \

				cell_area.height)

	def animation_timeout(self, tree, image):
		if image.get_storage_type() == Gtk.ImageType.ANIMATION:
			self.redraw = 0
			image.get_data('iter').advance()
			model = tree.get_model()
			model.foreach(self.func, (image, tree))
			if self.redraw:
				GObject.timeout_add(image.get_data('iter').get_delay_time(), \
					self.animation_timeout, tree, image)
			else:
				image.set_data('iter', None)

	def on_render(self, window, widget, background_area,cell_area, \
		expose_area, flags):
		if not self.image:
			return
		pix_rect = ()
		pix_rect.x, pix_rect.y, pix_rect.width, pix_rect.height = \
			self.on_get_size(widget, cell_area)

		pix_rect.x += cell_area.x
		pix_rect.y += cell_area.y
		pix_rect.width  -= 2 * self.get_property("xpad")
		pix_rect.height -= 2 * self.get_property("ypad")

		draw_rect = cell_area.intersect(pix_rect)
		draw_rect = expose_area.intersect(draw_rect)

		if self.image.get_storage_type() == Gtk.ImageType.ANIMATION:

			if not self.image.get_data('iter'):
				animation = self.image.get_animation()
				self.image.set_data('iter', animation.get_iter())
				GObject.timeout_add(self.image.get_data('iter').get_delay_time(), \
					self.animation_timeout, widget, self.image)

			pix = self.image.get_data('iter').get_pixbuf()
		elif self.image.get_storage_type() == Gtk.ImageType.PIXBUF:
			pix = self.image.get_pixbuf()
		else:
			return
		window.draw_pixbuf(widget.style.black_gc, pix, \
			draw_rect.x-pix_rect.x, draw_rect.y-pix_rect.y, draw_rect.x, \
			draw_rect.y+2, draw_rect.width, draw_rect.height, \
			Gdk.RGB_DITHER_NONE, 0, 0)

	def on_get_size(self, widget, cell_area):
		if not self.image:
			return 0, 0, 0, 0
		if self.image.get_storage_type() == Gtk.ImageType.ANIMATION:
			animation = self.image.get_animation()
			pix = animation.get_iter().get_pixbuf()
		elif self.image.get_storage_type() == Gtk.ImageType.PIXBUF:
			pix = self.image.get_pixbuf()
		else:
			return 0, 0, 0, 0
		pixbuf_width  = pix.get_width()
		pixbuf_height = pix.get_height()
		calc_width  = self.get_property("xpad") * 2 + pixbuf_width
		calc_height = self.get_property("ypad") * 2 + pixbuf_height
		x_offset = 0
		y_offset = 0
		if cell_area and pixbuf_width > 0 and pixbuf_height > 0:
			x_offset = self.get_property("xalign") * (cell_area.width - \
				calc_width -  self.get_property("xpad"))
			y_offset = self.get_property("yalign") * (cell_area.height - \
				calc_height -  self.get_property("ypad"))
		return x_offset, y_offset, calc_width, calc_height


class IconProgramList(GObject.GObject):

	__gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_LAST, None, ()),
        'menu': (GObject.SignalFlags.RUN_LAST, None, ()),
        'clicked': (GObject.SignalFlags.RUN_LAST, None, ()),
        'right-clicked': (GObject.SignalFlags.RUN_LAST, None, ())
        }
	def __init__(self):
		GObject.GObject.__init__ (self)
		#Create the Base Menu Template and an XDG menu object
		self.XDG = XDMateMenu()
		self.XDG.connect('changed', self.menu_callback)
		#if Globals.flip == False:
		#	self.backimagearea = backimage.subpixbuf(Globals.PG_buttonframe[0],Globals.MenuHeight - Globals.PG_buttonframe[1] - Globals.PG_buttonframedimensions[1],Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
		#	self.backimagearea = self.backimagearea.flip(Globals.flip)
		#else:
		#	self.backimagearea = backimage.subpixbuf(Globals.PG_buttonframe[0],Globals.PG_buttonframe[1] ,Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
#=================================================================  
#GRAPHICAL CODE FOR MENU
#=================================================================  
	def menu_callback(self,event):
		
		self.Restart('previous')

	def ProgramListPopulate(self,Frame,Destroyer):
		self.BanFocusSteal = False
		self.Destroyer=Destroyer
		self.Frame=Frame
		self.ConstructGTKObjectsMenu(self.Frame)
		self.PopulateButtons()
        
	def ConstructGTKObjectsMenu(self, Frame):
		# Create components Frame -> ScrollFrame -> EventBox -> VBox -> Buttons
		self.ScrollFrame = Gtk.ScrolledWindow()
		self.VBoxOut = Gtk.VBox(False)
		self.EBox = Gtk.EventBox()
		self.tree1 = Gtk.IconView()
		self.Button = Gtk.Button()
		self.Separator = None
		self.gtkicontheme = Gtk.IconTheme.get_default()
		self.gtkicontheme.connect('changed', self.update_icons) 
		targets = [('text/uri-list', 0, 0)]
		#self.tree1.connect("expose_event", self.expose)
		#self.EBox.connect("expose_event", self.expose)	
		#self.VBoxOut.connect("expose_event", self.expose)
		#self.ScrollFrame.connect("expose_event", self.expose)	
		if Globals.Settings['GtkColors'] == 0:
			self.EBox.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			#self.VBoxOut.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			#self.ScrollFrame.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)

		
		self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])	  
		self.ScrollFrame.set_shadow_type(Gtk.ShadowType.NONE)
		self.ScrollFrame.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
		self.VBoxOut.pack_start(self.ScrollFrame, True,True, 0)
		self.VBoxOut.set_border_width(0)
		self.ScrollFrame.add(self.tree1)
		self.EBox.add(self.VBoxOut)
		self.Frame.put(self.EBox,Globals.PG_buttonframe[0],Globals.PG_buttonframe[1])
		self.tree1.set_text_column(1)
		self.tree1.set_pixbuf_column(0)
		
		self.tree1.set_size_request(Globals.PG_buttonframedimensions[0], -1)

		
		self.tree1.set_orientation( Gtk.Orientation.HORIZONTAL)
		if Globals.Settings['Show_Tips']:
			self.tree1.set_tooltip_column (1)
		#Globals.PG_buttonframedimensions[0],self.ScrollFrame.get_size_request()[1]

		self.tree1.set_selection_mode(Gtk.SelectionMode.SINGLE)
		self.tree1.set_item_width(Globals.PG_buttonframedimensions[0]-2)
		cell = self.tree1.get_cells()[0]
		cell.set_property('ellipsize', Pango.EllipsizeMode.END)
		cell.set_fixed_size(-1,Globals.PG_iconsize)#+((Globals.PG_iconsize *8)/28))
		cell.set_property('ypad', (Globals.PG_iconsize *8)/28)
		#self.tree1.get_cells()[0].set_property('yalign', 0.1)
		try:
			self.tree1.set_item_padding(0)
		except:pass
		self.tree1.get_cells()[0].set_property('xpad', 6)
		if Globals.Settings['GtkColors'] == 0:
			cell.set_property('cell-background', Globals.ThemeColorCode)
			self.tree1.get_cells()[1].set_property('cell-background', Globals.ThemeColorCode)
			#self.tree1.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			self.tree1.modify_base(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			cell.set_property('foreground',Globals.NegativeThemeColorCode)
		
		self.tree1.set_row_spacing(0)
		self.tree1.set_margin(0)
		self.tree1.set_spacing(0)

		#self.tree1.set_cursor_on_cell((0,0), focus_column=None,focus_cell=None, start_editing=False)
		self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, GObject.TYPE_STRING)
		self.tree1.set_events(Gdk.EventMask.ALL_EVENTS_MASK)
		self.tree1.connect("key-press-event", self.PGListButtonKey)
		self.tree1.connect("motion-notify-event", self.move)
		self.tree1.connect("leave-notify-event", self.leave)
		self.tree1.connect("drag-data-get", self.drag_data_get)
		self.tree1.connect("drag-begin", self.drag_begin)
		self.tree1.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,targets,Gdk.DragAction.COPY)
		self.tree1.drag_source_add_text_targets()
		self.tree1.connect("button-press-event", self.drag_begin)
		self.tree1.connect("button-release-event", self.treeclick)
		self.tree1.set_model(self.model)
		#if Globals.Settings['GtkColors'] == 0:
			
			#self.tree1.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			#self.tree1.modify_base(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
		self.ScrollFrame.get_vscrollbar().set_events(Gdk.EventMask.ALL_EVENTS_MASK)
		self.ScrollFrame.get_vscrollbar().connect_after("map-event", self.map_event,'map')
		self.ScrollFrame.get_vscrollbar().connect_after("unmap-event", self.map_event,'unmap')
		#gc.collect()

	def leave(self, widget, event):
		self.tree1.unselect_path(self.index)


	def map_event(self,widget,event,a):
		if a == 'map':
			self.tree1.set_item_width(Globals.PG_buttonframedimensions[0]-self.ScrollFrame.get_vscrollbar().size_request()[0]-4)
		else:
			self.tree1.set_item_width(Globals.PG_buttonframedimensions[0]-2)

	def move(self, widget, event):
		mouse = widget.get_pointer()
	
		x = mouse[0]
		y = int(mouse[1] + self.ScrollFrame.get_vscrollbar().get_value())
		path = self.tree1.get_path_at_pos(x, y)
		if path:
			self.index = path[0]
			self.tree1.select_path(path)
			#self.tree1.set_cursor(path)

	def drag_begin(self, widget, drag_context):
		selection = widget.get_selected_items()
		if selection != []:
			self.index = int(selection[0][0])
			self.tree1.drag_source_set_icon_pixbuf(self.XDG.L_Icons[self.index])

	def drag_data_get (self, widget, drag_context, selection_data, info, timestamp):
		uri_list = None
		if self.XDG.allgio is not None:
			for z in self.XDG.allgio:
				if z.get_name() == self.XDG.L_Names[self.index]:
					uri_list = 'file:///usr/share/applications/%s' % z.get_id()
					break
		if uri_list is None:
			name = str(self.XDG.L_Execs[self.index]).replace('%F','').replace('%f','').replace('%u','').replace('%U','')
			if name.startswith ('file:/'):
				uri_list = name
			elif name.startswith ('/'):
				uri_list = 'file://%s' % name
			else:
				uri_list = 'file:///usr/bin/%s' % name
		
		selection_data.set(selection_data.target, 8,uri_list)

	def update_icons(self,client, connection_id=None, entry=None, args=None):
		print 'icons changed'
		self.XDG.Icon_change()
		self.Restart('previous')

	def Restart(self,data='all'):

		if self.XDG.Restart(data):
			self.PopulateButtons()
		#gc.collect()

	def expose(self, widget, event):
		#widget.window.set_composited(1)
		cr = widget.window.cairo_create()
		if widget.is_composited() is True:	
			cr.set_source_rgba(1, 1, 1, 0)
		else:
			cr.set_source_rgb(1, 1, 1)
		cr.set_operator (cairo.OPERATOR_SOURCE)
		cr.paint()
		#cairo_drawing.draw_pixbuf(cr,self.backimagearea)

	def treeclick(self,widget,event):
		"""activated when clicking in the tree"""
		selection = widget.get_selected_items()
		if selection != []:
			self.index = int(selection[0][0])
			self.ActivateButton(event)

	#def map_event(self, widget, event):
	#	print 'map'
	#	self.PopulateButtons()


	def RemoveButtons(self):
		self.tree1.set_model(None)
		if self.Separator:
			self.Separator.destroy()
		try:
			self.Button.destroy()
		except:pass
		try:
			self.Label.destroy()
		except:pass
		# doing the following is faster then self.model.clear()
		self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, GObject.TYPE_STRING)
		self.tree1.freeze_child_notify()
		

	def PopulateButtons(self):
		self.RemoveButtons()
		self.Buttonlist = []
		#a = time.clock()

		for i in range(0,len(self.XDG.L_Names)):
			typ = self.XDG.L_Types[i]
			if typ==8:
				self.dummy()#self.AddSeparator())
			elif typ==9:
				self.AddLabel(self.XDG.L_Names[i])
			elif typ==2:
				self.AddBackButton(self.XDG.L_Names[i],self.XDG.L_Icons[i],i)
			else:
				self.AddButton(self.XDG.L_Names[i],self.XDG.L_Icons[i],i)
		#print time.clock()-a
		#if a * Globals.PG_iconsize > Globals.PG_buttonframedimensions[1]:
		#	self.tree1.set_item_width(Globals.PG_buttonframedimensions[0]-self.ScrollFrame.get_vscrollbar().size_request()[0]-4)
		#else:
		#	self.tree1.set_item_width(Globals.PG_buttonframedimensions[0]-2)
		#print time.clock() 
		#self.SetInputFocus()
		#gc.collect()
		#print Globals.PG_buttonframedimensions[0]-self.ScrollFrame.size_request()[0]
		self.tree1.set_model(self.model)
		self.tree1.thaw_child_notify()
		self.ScrollFrame.get_vscrollbar().set_value(0)

	def AddBackButton(self,name,icon,i):
		if name == _('Back'):
			if not icon:
				icon = GdkPixbuf.Pixbuf.new_from_file_at_size(Globals.BrokenImage, Globals.PG_iconsize, Globals.PG_iconsize)

		
			self.Button = Gtk.Button(name)
			self.Img = Gtk.Image()
			self.Img.set_from_pixbuf(icon)
			self.Button.set_image(self.Img)
			self.Button.set_alignment(0,0)
			self.Button.set_tooltip_text(_('Return to last menu'))
			self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
			self.Button.set_size_request(self.PG_buttonwidth, Globals.PG_iconsize+8)
			self.Button.set_relief(Gtk.ReliefStyle.NONE)
			self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],self.ScrollFrame.get_size_request()[1] - 	self.Button.get_size_request()[1])
			self.AddSeparator2()
			self.VBoxOut.pack_start(self.Button, True,True, 0)
			self.Button.connect("button-release-event", self.PGListButtonClick,i)
			self.Button.connect("key-press-event", self.PGListButtonKey,i)
			self.Button.show()
			image,label =  self.Button.get_children()[0].get_children()[0].get_children()
			if Globals.Settings['GtkColors'] == 0:
				label.modify_fg(Gtk.StateType.NORMAL, Globals.NegativeThemeColorCode)
			label.set_property("ellipsize", Pango.EllipsizeMode.END) 
			label.set_max_width_chars(int(Globals.PG_buttonframedimensions[0]/11))
			self.Buttonlist.append(self.Button)
			icon = None
		else:
			self.AddButton(name,icon,i)

	def AddButton(self,name,icon,i):

		if not icon:
			icon = GdkPixbuf.Pixbuf.new_from_file_at_size(Globals.BrokenImage, Globals.PG_iconsize, Globals.PG_iconsize)

		self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
		if Globals.Settings['Show_Tips']:
			pass
		self.model.insert(i,[icon,name])
		icon = None
		

	def AddLabel(self,name):
		self.Label = Gtk.Label(label=name)
		self.Label.set_line_wrap(True)
		self.Label.set_property("ellipsize", Pango.EllipsizeMode.END) 
		self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
		if self.Separator:
			self.Separator.set_size_request(self.PG_buttonwidth, 1)
		self.VBoxOut.pack_start(self.Label, False,False, 0)
		if Globals.Settings['GtkColors'] == 0:
			self.Label.modify_fg(Gtk.StateType.NORMAL, Globals.NegativeThemeColorCode)
		self.Label.show()
		self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1]- self.Label.size_request()[1]-1)
	


	def AddSeparator2(self):
		self.Separator = Gtk.HSeparator()
		self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
		self.Separator.set_size_request(self.PG_buttonwidth, 1)
			
		self.VBoxOut.pack_start(self.Separator, False,False, 0)
		self.Separator.show()
		return self.Separator

	def dummy(self):
		pass

	def AddSeparator(self):
		self.Separator = Gtk.HSeparator()
		self.model.append([None,'',''])
		

	def PGListButtonClick(self, widget, event,i):
		"""activated when clicking a button"""
		self.index = i
		self.ActivateButton(event)
		if event.button == 3:
			self.emit('menu')
		
	def ActivateButton(self,event):
		if event.type == Gdk.KEY_PRESS:event_button = 1
		elif event.type == Gdk.EventType.BUTTON_PRESS:event_button = event.button
		elif event.type ==  Gdk.BUTTON_RELEASE:event_button = event.button

		self.type = self.XDG.L_Types[self.index]
		a = self.XDG.ButtonClick(self.index,event)
		if event_button == 1:
			if a==1:
				self.Destroyer()
			self.PopulateButtons()
			self.emit('clicked')
			#gc.collect()
		elif event_button == 3:
			self.emit('right-clicked')

	def PGListButtonKey(self, widget, event,i=None):
		key = event.hardware_keycode
		
		if widget == self.tree1:
			
			if key == 36 or key == 65 or key == 114:	#Enter or Space or right
				selection = widget.get_selected_items()
				if selection != []:
					self.index = int(selection[0][0])
					self.ActivateButton(event)
			elif key == 113: #Left
				self.Restart('previous')
		else:
			if key == 36 or key == 65 or key == 114:	#Enter or Space or right
				self.index = i
				self.ActivateButton(event)
			
			
	def SetInputFocus(self):
		# Give keyboard input focus to last item on list or to sub menu program group start
		pass

	def SetFirstButton(self,event):
		pass#self.Buttonlist[0].grab_focus()

	def SetLastButton(self,event):
		pass#self.Buttonlist[len(self.XDG.L_Names)-1].grab_focus()

#=================================================================  
#EXTRA FUNCTION PASSTHROUGH TO XDG
#See XDG module for command opcodes
#=================================================================  

	def CallSpecialMenu(self,command,data=None):
		self.XDG.CallSpecialMenu(command,data)
		self.PopulateButtons()
		#gc.collect()

	def destroy(self):
		self.XDG.destroy() #Allows XDG to de-initialse correctly (VERY IMPORTANT)

class ProgramList(GObject.GObject):

	__gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_LAST, None, ()),
        'menu': (GObject.SignalFlags.RUN_LAST, None, ()),
        'clicked': (GObject.SignalFlags.RUN_LAST, None, ()),
        'right-clicked': (GObject.SignalFlags.RUN_LAST, None, ())
        }
	def __init__(self):
		GObject.GObject.__init__ (self)
		#Create the Base Menu Template and an XDG menu object
		self.XDG = XDMateMenu()
		self.XDG.connect('changed', self.menu_callback)
		self.Buttonlist = []
		#if Globals.flip == False:
		#	self.backimagearea = backimage.subpixbuf(Globals.PG_buttonframe[0],Globals.MenuHeight - Globals.PG_buttonframe[1] - Globals.PG_buttonframedimensions[1],Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
		#	self.backimagearea = self.backimagearea.flip(Globals.flip)
		#else:
		#	self.backimagearea = backimage.subpixbuf(Globals.PG_buttonframe[0],Globals.PG_buttonframe[1] ,Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
#=================================================================  
#GRAPHICAL CODE FOR MENU
#=================================================================  
	def menu_callback(self,event):
		
		self.Restart('previous')

	def ProgramListPopulate(self,Frame,Destroyer):
		self.BanFocusSteal = False
		self.Destroyer=Destroyer
		self.Frame=Frame
		self.ConstructGTKObjectsMenu(self.Frame)
		self.PopulateButtons()
        
	def ConstructGTKObjectsMenu(self, Frame):
		# Create components Frame -> ScrollFrame -> EventBox -> VBox -> Buttons
		self.PrevSelButtons = []
		self.PrevSelButton = -1
		self.ScrollFrame = Gtk.ScrolledWindow()
		self.VBoxIn = Gtk.VBox(False)
		self.VBoxOut = Gtk.VBox(False)
		self.VBoxOut.pack_start(self.ScrollFrame, True,True, 0)
		self.ScrollFrame.connect_after("map-event", self.map_event)
		#self.ScrollFrame.connect("expose_event", self.expose)
		#self.VBoxOut.connect("expose_event", self.expose)
		#self.VBoxIn.connect("expose_event", self.expose)
		self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])      
		self.ScrollFrame.set_shadow_type(Gtk.ShadowType.NONE)
		self.ScrollFrame.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
		#Build structure
		self.ScrollFrame.add_with_viewport(self.VBoxIn)
		self.ScrollFrame.get_children()[0].set_shadow_type(Gtk.ShadowType.NONE)
		if Globals.Settings['GtkColors'] == 0:
		

			self.VBoxOut.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			self.VBoxIn.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			self.ScrollFrame.modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)
			self.ScrollFrame.get_children()[0].modify_bg(Gtk.StateType.NORMAL, Globals.ThemeColorCode)

		
		
		self.Frame.put(self.VBoxOut,Globals.PG_buttonframe[0],Globals.PG_buttonframe[1])
		#Show newly created widgets
		
		self.ScrollFrame.set_shadow_type(Gtk.ShadowType.NONE)
		self.gtkicontheme = Gtk.IconTheme.get_default()
		self.gtkicontheme.connect('changed', self.update_icons) 
		self.Separator = None
      		#Gtk.rc_parse_string ("""
	         #      style \"Tilo-Button\"
	          #     {
	           #      GtkButton::inner-border = {0,0,0,0}
	            #   }
	             #  widget \"*.TiloButton\" style \"Tilo-Button\"
	              # """)
	

	def update_icons(self,client, connection_id=None, entry=None, args=None):
		print 'icons changed'
		self.XDG.Icon_change()
		self.Restart('previous')

	def Restart(self,data='all'):
	
		if self.XDG.Restart(data):
			self.PopulateButtons()
		#gc.collect()

	def expose(self, widget, event):
		cr = widget.window.cairo_create()
		if widget.is_composited() is True:	
			cr.set_source_rgba(1, 1, 1, 0)
		else:
			cr.set_source_rgb(1, 1, 1)
		cr.set_operator (cairo.OPERATOR_SOURCE)
		cr.paint()
		#cairo_drawing.draw_pixbuf(cr,self.backimagearea)
		#pass


	def map_event(self, widget, event):
		print 'map'
		self.PopulateButtons()

	def PopulateButtons(self):
		self.RemoveButtons()
		self.Buttonlist = []
		for i in range(0,len(self.XDG.L_Names)):
			typ = self.XDG.L_Types[i]
			if typ==8:
				self.AddSeparator()
			elif typ==9:
				self.AddLabel(self.XDG.L_Names[i])
			else:
				self.AddButton(self.XDG.L_Names[i],self.XDG.L_Icons[i],i)
		
		self.SetInputFocus()
		#gc.collect()
		try:
			self.VBoxIn.get_children()[0].grab_focus()
		except:pass
		self.ScrollFrame.get_vscrollbar().set_value(0)
		
		
	def AddButton(self,name,icon,i):
		self.Button = Gtk.Button(name)

		if icon:
			self.Pic = icon
		else:
			self.Pic = GdkPixbuf.Pixbuf.new_from_file_at_size(Globals.BrokenImage, Globals.PG_iconsize, Globals.PG_iconsize)

		self.Img = Gtk.Image()
		self.Img.set_from_pixbuf(self.Pic)
		self.Button.set_alignment(0,0)
		
		self.Button.set_image(self.Img)
		self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
		self.Button.set_size_request(self.PG_buttonwidth, Globals.PG_iconsize+10)
		self.Button.set_relief(Gtk.ReliefStyle.NONE)

		if name ==_('Back'):
			self.Button.set_tooltip_text(_('Return to last menu'))
			self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],self.ScrollFrame.get_size_request()[1] - self.Button.get_size_request()[1])
			self.AddSeparator2()
			self.VBoxOut.pack_start(self.Button, True,True, 0)
			self.Buttonlist.append(self.Button)
		else:
			self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
			if Globals.Settings['Prog_List'] == 1:
				self.VBoxIn.pack_start(self.Button, True,True, 0)
			elif Globals.Settings['Prog_List'] == 2:
				self.VBoxIn.pack_start(self.Button, False,False, 0)
			if Globals.Settings['Show_Tips']:
				if name in self.XDG.ItemComments:
					self.Button.set_tooltip_text(self.XDG.ItemComments[name])
				else:
					self.Button.set_tooltip_text(name)
		self.Button.connect("drag-data-get", self.drag_data_get,i)
		targets = [('text/uri-list', 0, 0)]
		self.Button.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,targets,Gdk.DragAction.COPY)
		self.Button.drag_source_add_text_targets()
		#self.tree1.connect("drag-begin", self.drag_begin)
		self.Button.connect("button-press-event", self.drag_begin)
		self.Button.connect("button-release-event", self.PGListButtonClick,i)
		self.Button.connect("key-press-event", self.PGListButtonKey,i)
		self.Button.show()
		image,label =  self.Button.get_children()[0].get_children()[0].get_children()
		if Globals.Settings['GtkColors'] == 0:
			label.modify_fg(Gtk.StateType.NORMAL, Globals.NegativeThemeColorCode)
		label.set_property("ellipsize", Pango.EllipsizeMode.END) 
		label.set_alignment(0, label.get_alignment()[1])
		label.set_padding(5,0)
		label.set_size_request(Globals.PG_buttonframedimensions[0]-Globals.PG_iconsize*2,-1)
		#label.set_max_width_chars(int(Globals.PG_buttonframedimensions[0]/11))
		iconfile = None
		return self.Button


	def drag_begin(self, widget, drag_context):
		
		widget.drag_source_set_icon_pixbuf(widget.get_image().get_pixbuf())

	def drag_data_get (self, widget, drag_context, selection_data, info, timestamp,i):
		self.index = i
		uri_list = None
		
		if self.XDG.allgio is not None:
			for z in self.XDG.allgio:
				if z.get_name() == self.XDG.L_Names[self.index]:
					uri_list = 'file:///usr/share/applications/%s' % z.get_id()
					break
					
		
		if uri_list is None:
			name = str(self.XDG.L_Execs[self.index]).replace('%F','').replace('%f','').replace('%u','').replace('%U','')
			if name.startswith ('file:/'):
				uri_list = name
			elif name.startswith ('/'):
				uri_list = 'file://%s' % name
			else:
				uri_list = 'file:///usr/bin/%s' % name
		
		selection_data.set(selection_data.target, 8,uri_list)

	def AddLabel(self,name):
		self.Label = Gtk.Label(label=name)
		self.Label.set_line_wrap(True)
		self.Label.set_property("ellipsize", Pango.EllipsizeMode.END) 
		self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
		if self.Separator:
			self.Separator.set_size_request(self.PG_buttonwidth, 1)
		self.VBoxOut.pack_start(self.Label, True,True, 0)
		if Globals.Settings['GtkColors'] == 0:
			self.Label.modify_fg(Gtk.StateType.NORMAL, Globals.NegativeThemeColorCode)
		self.Label.show()
		self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1]- self.Label.size_request()[1]-1)
		self.Buttonlist.append(self.Label)

	def AddSeparator2(self):
		self.Separator = Gtk.HSeparator()
		self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
		self.Separator.set_size_request(self.PG_buttonwidth, 1)
		self.VBoxOut.pack_start(self.Separator, True,True, 0)
		self.Separator.show()
		return self.Separator

	def AddSeparator(self):
		self.Separator = Gtk.HSeparator()
		self.PG_buttonwidth = Globals.PG_buttonframedimensions[0] - 12
		self.Separator.set_size_request(self.PG_buttonwidth, 1)
		self.VBoxIn.pack_start(self.Separator, True,True, 0)
		self.Separator.show()
		self.Buttonlist.append(self.Separator)

	def PGListButtonClick(self, widget, event,i):
		mouse = widget.get_pointer()
		x = 0
		y = 0
		w = x + widget.get_allocation().width
		h = y + widget.get_allocation().height
		if mouse[0] > x and mouse[0] < w and mouse[1] > y and mouse[1] < h:
			
			self.index = i
			self.ActivateButton(event,self.index)
			if event.button == 3:
				self.emit('menu')
		
	def ActivateButton(self,event,i):
		if event.type == Gdk.KEY_PRESS:event_button = 1
		elif event.type == Gdk.EventType.BUTTON_PRESS:event_button = event.button
		elif event.type ==  Gdk.BUTTON_RELEASE:event_button = event.button
		self.index = i
		self.type = self.XDG.L_Types[self.index]
		a = self.XDG.ButtonClick(self.index,event)
		if event_button == 1:
			if a==1:
				self.Destroyer()
			self.PopulateButtons()
			self.emit('clicked')
			#gc.collect()
		elif event_button == 3:
			self.emit('right-clicked')



	def RemoveButtons(self):
		#TODO this is still slow, try to make is faster
		if self.Separator:
			self.Separator.destroy()
		self.VBoxIn.foreach(lambda widget:self.VBoxIn.remove(widget))
		for item in self.Buttonlist:
			item.destroy()

	def PGListButtonKey(self, widget, event,i):
		
		self.index = i
		key = event.hardware_keycode
		#98 up    104 dn
		if key == 98 or key == 111:	#Up (menu loop-around)
			if self.index == 0:
				# Set timeout to call last button (as key press has not gone through yet)
				GObject.timeout_add(100,self.SetFirstButton, self)
				
			inc = self.ScrollFrame.get_vscrollbar().get_adjustment().get_value() - self.ScrollFrame.get_vscrollbar().get_adjustment().get_step_increment()
			if inc < self.ScrollFrame.get_vscrollbar().get_adjustment().get_lower(): inc = self.ScrollFrame.get_vscrollbar().get_adjustment().get_lower()
			if self.index < len(self.VBoxIn.get_children())-1:
				self.ScrollFrame.get_vscrollbar().get_adjustment().set_value(inc)
		elif key == 104 or key == 116:	#Down
			if self.index == len(self.XDG.L_Names)-1:
				# Set timeout to call last button (as key press has not gone through yet)
				GObject.timeout_add(100,self.SetLastButton, self)
			inc = self.ScrollFrame.get_vscrollbar().get_adjustment().get_value() + self.ScrollFrame.get_vscrollbar().get_adjustment().get_step_increment() 
			if inc + self.ScrollFrame.get_vscrollbar().get_adjustment().get_page_size() > self.ScrollFrame.get_vscrollbar().get_adjustment().get_upper(): inc = self.ScrollFrame.get_vscrollbar().get_adjustment().get_upper() - self.ScrollFrame.get_vscrollbar().get_adjustment().get_page_size()


			if self.index > 0:
				self.ScrollFrame.get_vscrollbar().get_adjustment().set_value(inc)

		elif key == 102 or key == 144 or key == 114:	#Right
			self.type = self.XDG.L_Types[self.index]
			if self.type == 0:
				self.ActivateButton(event,self.index)
				self.PrevSelButtons.append(self.index)
		elif key == 100 or key == 113 or key == 22:	#Left
			if self.XDG.PrevMenu:
				self.XDG.CallSpecialMenu(0)
				if self.PrevSelButtons:
					self.PrevSelButton = self.PrevSelButtons.pop()
				self.PopulateButtons()
			#gc.collect()
		elif key == 36 or key == 65:	#Enter or Space
			self.ActivateButton(event,self.index)
		else:
			pass
			
	def SetInputFocus(self):
		# Give keyboard input focus to last item on list or to sub menu program group start
		if self.BanFocusSteal == False:
			try:
				if self.PrevSelButton == -1:
					if self.XDG.PrevMenu and len(self.XDG.L_Names) > 4 and self.XDG.searchresults==0:	
						self.VBoxIn.get_children()[3].grab_focus()
					else:
						self.VBoxIn.get_children()[len(self.VBoxIn.get_children())-1].grab_focus()

				else:
					self.VBoxIn.get_children()[self.PrevSelButton].grab_focus()
					self.PrevSelButton = -1
			except:pass

	def SetFirstButton(self,event):
		self.VBoxIn.get_children()[0].grab_focus()

	def SetLastButton(self,event):
		self.VBoxIn.get_children()[len(self.VBoxIn.get_children())-1].grab_focus()

#=================================================================  
#EXTRA FUNCTION PASSTHROUGH TO XDG
#See XDG module for command opcodes
#=================================================================  

	def CallSpecialMenu(self,command,data=None):
		self.XDG.CallSpecialMenu(command,data)
		self.PopulateButtons()
		#gc.collect()

	def destroy(self):
		self.XDG.destroy() #Allows XDG to de-initialse correctly (VERY IMPORTANT)



class MenuArea(Gtk.DrawingArea):
	__gsignals__ = {
                    'button-press-event' : 'override',
                    'button-release-event' : 'override',
                    'motion-notify-event' : 'override',
					'scroll-event' : 'override',
					'key-press-event' : 'override',
					'leave-notify-event' : 'override',
					'enter-notify-event' : 'override',
					
					"show-scrollbar" : (GObject.SignalFlags.RUN_FIRST, None, ()),
					"hide-scrollbar" : (GObject.SignalFlags.RUN_FIRST, None, ()),
					"update-scrollbar": (GObject.SignalFlags.RUN_FIRST, None, [GObject.TYPE_INT, GObject.TYPE_INT]),
					"scroll-scrollbar": (GObject.SignalFlags.RUN_FIRST, None, [GObject.TYPE_INT]),
					"reset-scrollbar": (GObject.SignalFlags.RUN_FIRST, None, ()),
                    }
	def __init__(self):
		GObject.GObject.__init__(self)
		#self.MenuEngine = MenuSource()
		#self.MenuEngine.connect("update-menu", self.update_menu)
		self.Buttons = []
		self.scroll = 0
		self.width = 0	# Cache last drawn width for context menu placement
		self.netheight = 0
		self.visibleheight = 0
		self.mouse_in_region = False
		self.selected_button = None
		#self.padding = 1
		self.pointer_x = 0
		self.pointer_y = 0
		self.add_events(Gdk.EventMask.BUTTON_MOTION_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK | Gdk.EventMask.BUTTON_PRESS_MASK |
				Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.KEY_PRESS_MASK)

	def scrollbar_changed(self,value):
		self.scroll = value
		self.force_redraw()
		
	#def ChangeMenu(self,menu):
		# Menu is changed externally (e.g. by search or by other menu button)
	#	self.MenuEngine.ChangeMenu(menu)
	#	self.CreateButtons(self.MenuEngine.Menu)
	#	self.emit("reset-scrollbar")
	#	self.force_redraw()
	
	def CreateButtons(self,menu):
		self.selected_button = None
		self.Buttons = []	# Clean unload of memory?
		if menu:
			for item in menu:
				self.Buttons.append(internalbutton(item))
			if self.Buttons:
				self.selected_button = self.Buttons[0]
	
	def Map_Coords_To_Button(self, x, y):
		if self.mouse_in_region == False:
			return None
		step_y = globals.menuitempadding - self.scroll
		for item in self.Buttons:
			if y >= step_y and y <= step_y + item.last_reported_height: 
				return item
			step_y = step_y + item.last_reported_height + globals.menuitempadding
	
	def Map_Button_To_Coords(self, button):
		step_y = globals.menuitempadding - self.scroll
		for item in self.Buttons:
			if item == button:
				return int(self.width / 2), int(step_y + item.last_reported_height)
			step_y = step_y + item.last_reported_height + globals.menuitempadding
		return 0,0
	
	def draw(self, cr, width, height):
		cr.set_source_rgb(*globals.menucolor)
		cr.rectangle(0, 0, width, height)
		cr.fill()
		
		self.width = width
		
		# Calculate the total height of the list
		self.visibleheight = height
		netheight = globals.menuitempadding
		for item in self.Buttons:
			netheight += item.get_height(cr) + globals.menuitempadding
		if netheight != self.netheight:
			self.netheight = netheight
			if self.netheight > height:
				self.emit("show-scrollbar")
				self.emit("update-scrollbar", netheight - height, height)
				
			else:
				self.emit("hide-scrollbar")
				
		
		y = globals.menuitempadding - self.scroll
		for item in self.Buttons:
			pattern = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width - globals.menuitempadding * 2), int(item.get_height(cr)))
			cr2 = cairo.Context(pattern)
			if item == self.selected_button:
				item.selected = True
			else:
				item.selected = False
			# Only draw if in region
			if y >= - item.get_height(cr) and y < height:
				item.draw(cr2,width - globals.menuitempadding * 2,item.get_height(cr))
				cr.set_source_surface(pattern,globals.menuitempadding,y)
				cr.paint()
			y = y + item.get_height(cr) + globals.menuitempadding
			
	def do_motion_notify_event(self, event):
		self.pointer_x = event.x
		self.pointer_y = event.y
		self.select_button()

	def select_button(self):
		if self.mouse_in_region:
			item = self.Map_Coords_To_Button(self.pointer_x,self.pointer_y)
			if item != self.selected_button:
				self.selected_button = item
				self.force_redraw()

	def Key_Navigate(self,event):
		if event.keyval == 65362: #up
			if self.selected_button:
				if self.Buttons != []:
					if self.selected_button != self.Buttons[0]:
						#prevheight = self.selected_button.get_height()
						self.selected_button = self.Buttons[self.Buttons.index(self.selected_button) - 1]
						# Only scroll if new button is about to become offscreen
						if self.Map_Button_To_Coords(self.selected_button)[1] <= self.selected_button.get_height():
							scrollheight = 0 - self.selected_button.get_height() - globals.menuitempadding
						else:
							scrollheight = 0
							
					elif self.selected_button == self.Buttons[0]:
						self.selected_button = self.Buttons[-1]
						scrollheight = self.Map_Button_To_Coords(self.selected_button)[1]
					self.emit("scroll-scrollbar", scrollheight)
			else:
				if len(self.Buttons) >= 1:
					self.selected_button = self.Buttons[0]
				self.emit("scroll-scrollbar", -25)
			self.force_redraw()
		elif event.keyval == 65364: #Down
			if self.selected_button:
				if self.Buttons != []:
					if self.selected_button != self.Buttons[-1]:
						self.selected_button = self.Buttons[self.Buttons.index(self.selected_button) + 1]
						# Only scroll if new button is about to become offscreen
						if self.Map_Button_To_Coords(self.selected_button)[1] >= self.visibleheight:
							scrollheight = self.selected_button.get_height() + globals.menuitempadding
							self.emit("scroll-scrollbar", scrollheight)
					elif self.selected_button == self.Buttons [-1]:
						self.selected_button = self.Buttons[0]
						self.emit("reset-scrollbar")
			else:
				if len(self.Buttons) >= 1:
					self.selected_button = self.Buttons[0]
				self.emit("scroll-scrollbar", 25)
			self.force_redraw()
		elif event.keyval == 65361: #Left
			self.MenuEngine.Navigate_Back()
		elif event.keyval == 65363 or event.keyval == 65421 or event.keyval == 65293: #Enter, Right
			if self.selected_button:
				self.MenuEngine.ButtonClicked(1, self.selected_button.xdgbutton)
		elif event.keyval == 65383:	#Menu key
			if self.selected_button:
				self.MenuEngine.ButtonClicked(3, self.selected_button.xdgbutton, event.get_time(), self.PopUpMenuAlignment)
	
	def PopUpMenuAlignment(self,menu):
#		lambda p : (lambda f : self.Map_Button_To_Coords(self.selected_button), True)
		coords = self.Map_Button_To_Coords(self.selected_button)
		return coords[0], coords[1], True
	
	def do_scroll_event(self,event):
		if event.direction == Gdk.ScrollDirection.UP:
			self.emit("scroll-scrollbar", -25)
		elif event.direction == Gdk.ScrollDirection.DOWN:
			self.emit("scroll-scrollbar", 25)
		elif event.direction == Gtk.gtk.SCROLL_LEFT:
			self.MenuEngine.Navigate_Back()
		elif event.direction == Gdk.ScrollDirection.RIGHT:
			if self.selected_button:
				self.MenuEngine.ButtonClicked(1, self.selected_button.xdgbutton)

	def do_enter_notify_event(self, event):
		self.pointer_x = event.x
		self.pointer_y = event.y
		self.mouse_in_region = True

	def do_button_press_event(self, event):
		self.pointer_x = event.x
		self.pointer_y = event.y
		self.select_button()
			
	def do_button_release_event(self, event):
		self.pointer_x = event.x
		self.pointer_y = event.y
		self.select_button()
		if self.selected_button:
			self.MenuEngine.ButtonClicked(event.button, self.selected_button.xdgbutton, event.get_time())
				

	def update_menu(self,event):
		self.emit("reset-scrollbar")
		self.CreateButtons(self.MenuEngine.Menu)
		self.force_redraw()
			
	def do_leave_notify_event(self, event):
		self.pointer_x = event.x
		self.pointer_y = event.y
		self.mouse_in_region = False
		self.selected_button = None
		
	def force_redraw(self):
		if self.window:
			rect = (0, 0, self.window.get_size())
			self.window.invalidate_rect(rect, True)

class internalbutton:
	def __init__(self, button):
		self.xdgbutton = button
		self.text = button.title
		self.icon = create_image_surface(button.icon)
		self.selected = False
		self.last_reported_height = 0

	def get_width(self):
		return 0
	
	def get_height(self, cr=None):
		if cr:
			text_w, text_h = cr.text_extents(self.text)[2:4]
			if text_h * (self.text.count("\n") + 1) + globals.v_text_padding > globals.buttonheight - 2:
				self.last_reported_height = text_h * (self.text.count("\n") + 1) + globals.v_text_padding
				return self.last_reported_height
		#self.last_reported_height = globals.buttonheight
		return self.last_reported_height
	
	def draw(self,cr, width, height):
		# Draw image underlay when selected
		if self.selected:
			draw_rounded_rect(cr,0,0,width,height,globals.buttoncornerradius)	
			pat = cairo.LinearGradient (0, 0, 0, height)
			for item in globals.selectedbuttongradient:
				pat.add_color_stop_rgba (*item)
			cr.set_source(pat)
			cr.fill_preserve()
			cr.set_source_rgba(*globals.buttonbordercolor)
			cr.set_line_width(globals.buttonborderwidth)
			cr.stroke()

		# Draw icon, preserve aspect ratio of icon, and pass on space settings to the text renderer
		if self.icon:
			if width > height:
				h = height - globals.buttoniconpadding
				w = (float(height) / float(self.icon.get_height())) * self.icon.get_width() - globals.buttoniconpadding
			elif height <= width:
				w = width - globals.buttoniconpadding
				h = (float(width) / float(self.icon.get_width())) * self.icon.get_height() - globals.buttoniconpadding
			x,y = 0, height / 2 - h / 2				
			draw_scaled_image(cr, self.icon, x, y, w, h)
			
		else:
			x = 0; y = 0; w = 0; h = 0

		if self.text:
			offset_y = 0
			text_size_reduction = 0
			for item in self.text.split("\n"):
				cr.select_font_face(globals.font, globals.fontitalic, globals.fontbold)
				renderstyle = cairo.FontOptions()
				renderstyle.set_antialias(cairo.ANTIALIAS_DEFAULT)
				cr.set_font_options(renderstyle)
				cr.set_font_size(globals.fontsize - text_size_reduction)
				if self.selected:
					cr.set_source_rgb(*globals.fontselectcolor)
				else:
					cr.set_source_rgb(*globals.fontcolor)
				text_w, text_h = cr.text_extents(item)[2:4]
				if self.xdgbutton.textrightjustify:
					tx = width - globals.buttonpadding - cr.text_extents(item)[4]
					if tx < x + w + globals.buttonpadding:
						while tx < x + w + globals.buttonpadding:
							text_size_reduction += 1
							cr.set_font_size(globals.fontsize - text_size_reduction)
							tx = width - globals.buttonpadding - cr.text_extents(item)[4]		
					cr.move_to(tx, height / 2 + 4 + offset_y - text_h * self.text.count("\n") / 2 + self.text.count("\n")) # border width
				else:
					cr.move_to(x + w + globals.buttonpadding, height / 2 + 4 + offset_y - text_h * self.text.count("\n") / 2 + self.text.count("\n")) # border width
				cr.show_text(item)
				cr.stroke()
				offset_y = offset_y + text_h
				text_size_reduction = 3




class CairoProgramList:
	__gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_LAST, None, ()),
        'menu': (GObject.SignalFlags.RUN_LAST, None, ())
        }
	def __init__(self):
		#Create the Base Menu Template and an XDG menu object		
		self.XDG = XDMateMenu()

#=================================================================  
#GRAPHICAL CODE FOR MENU
#=================================================================  

	def ProgramListPopulate(self,Frame,Destroyer):
		self.Destroyer=Destroyer
		self.Frame = Frame
		self.ConstructGTKObjectsMenu(Frame)
		
		#self.PopulateButtons()
        
	def ConstructGTKObjectsMenu(self, Frame):
		self.menu = CairoMenuObject()
		self.menu.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
                              Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                              Gdk.EventMask.BUTTON_PRESS_MASK)
		self.menu.connect("motion_notify_event", self.mousemove)
		self.menu.connect("button-press-event", self.buttonpress)
		self.menu.set_size_request(Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])      
		Frame.put(self.menu, Globals.PG_buttonframe[0],Globals.PG_buttonframe[1])
		Frame.show_all()
		self.menu.UpdateButtons(self.XDG.L_Names)
		self.menu.InitiateAnimation(1)
		GObject.timeout_add(10,self.UpdateAnimation)
		
	def UpdateAnimation(self):
		self.Frame.queue_draw_area(Globals.PG_buttonframe[0],Globals.PG_buttonframe[1],Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
		#Gdk.window_process_all_updates()
		if self.menu.inanimation==1:
			return True
		else:
			return False
		
	def mousemove(self,widget,event):
		a = self.menu.seltext
		self.menu.seltext=self.menu.Unmap(event.x,event.y)
		if a != self.menu.seltext:
			self.menu.UpdateButtons(self.XDG.L_Names)		
			self.Frame.queue_draw_area(Globals.PG_buttonframe[0],Globals.PG_buttonframe[1],Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1])
	
	def buttonpress(self,widget,event):
		a=self.XDG.L_Types[self.menu.seltext]
		self.XDG.ButtonClick(self.menu.seltext)
		self.menu.NameBuffer = self.XDG.L_Names
		if a==0:		#forward menu movement
			self.menu.InitiateAnimation(2)
			GObject.timeout_add(10,self.UpdateAnimation)

		elif a==2:	#back menu movement
			self.menu.InitiateAnimation(3)
			GObject.timeout_add(10,self.UpdateAnimation)

#=================================================================  
#EXTRA FUNCTION PASSTHROUGH TO XDG
#See XDG module for command opcodes
#=================================================================  

	def CallSpecialMenu(self,command,data=None):
#		for item in self.Buttonlist:
#			item.destroy()
		self.XDG.CallSpecialMenu(command,data)
#		self.PopulateButtons()

		self.menu.UpdateButtons(self.XDG.L_Names)
		self.menu.InitiateAnimation(1)
		GObject.timeout_add(10,self.UpdateAnimation)

	def SetInputFocus(self):
		# Give keyboard input focus to last item on list or to sub menu program group start
		pass

	def SetFirstButton(self,event):
		pass#self.Buttonlist[0].grab_focus()

	def SetLastButton(self,event):
		pass#self.Buttonlist[len(self.XDG.L_Names)-1].grab_focus()
		

class CairoMenuObject(Gtk.DrawingArea):
    
    def __init__(self):
		import math as math
		self.math = math
		GObject.GObject.__init__(self)
		self.connect("expose_event", self.expose)
		# Screen dimensions
		self.x,self.y=Globals.PG_buttonframe[0],Globals.PG_buttonframe[1]
		self.w,self.h=Globals.PG_buttonframedimensions[0],Globals.PG_buttonframedimensions[1]
		#Standard settings
		self.font_size=[] 
		#Animation status
		self.inanimation=0
		self.activitycount=0
		self.deffont_size=10
		self.seltext = 0
		#Motion registers
		self.leftshift=0
		self.inleftshift=0
		self.leftshifti=0
		
    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        # set a clip region for the expose event
        self.context.rectangle(event.area.x, event.area.y,event.area.width, event.area.height)
        self.context.clip()
        self.draw(self.context)
        return False
    
    	
    def draw(self, context):
		x,y,w,h=self.x,self.y,self.w,self.h
		# Update animation handlers
		# Left shift
		if self.inleftshift==1:
			self.leftshifti=self.leftshifti+0.2
			self.leftshift=self.leftshiftd * w - (self.leftshiftd * self.math.sin(self.leftshifti)*w)
			if self.leftshifti>=self.math.pi/2:
				self.inleftshift=0
				self.leftshift=0
				self.activitycount = self.activitycount - 1
				if self.activitycount==0:
					self.inanimation=0
					
			self.UpdateButtons(self.NameBuffer)
			
		#Draw flat gradient background
		pat = cairo.LinearGradient (x, y,  w, h)
		pat.add_color_stop_rgba (0, .5, .5, .5, 1)
		pat.add_color_stop_rgba (1, .3, .3, 1, 1)
		context.set_source(pat)
		context.paint()
		context.set_source_rgba(0,0,0,.1)
		context.move_to(0, 0)
		context.curve_to(0, 250, w, h-150, w,h)
		context.line_to(w,0)
		context.move_to(w,0)
		context.fill_preserve()
		#Paint the button text onto the draw surface
		if isinstance(self.textsurface,cairo.Surface):
			context.set_source_surface(self.textsurface,self.leftshift,0)
			context.paint()
		if self.leftshiftdlw==-1:
			context.set_source_surface(self.prevtextsurface,self.leftshift+w,0)
			context.paint()
		elif self.leftshiftdlw==1:
			context.set_source_surface(self.prevtextsurface,self.leftshift-w,0)
			context.paint()

    def UpdateButtons(self,L_Names):
    	#Draw the button page overlay
		self.NameBuffer = L_Names
		if len(self.font_size) != len(self.NameBuffer):
			self.font_size = []
			self.font_move = []
			self.font_movec = []
			for i in range(len(self.NameBuffer)):
				self.font_size.append(10)
				self.font_move.append(0)
				self.font_movec.append(0)
		
		x,y,w,h=self.x,self.y,self.w,self.h
		self.textsurface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
		context = cairo.Context(self.textsurface)
		self.DrawButton(w,30)
		#Draw text col1
		context.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
		for i in range(0,len(L_Names)):
			if L_Names[i] != '<separator>':
				context.set_source_surface(self.buttonsurface,0,y+i*32-40)
				context.paint()
			
	
				if i==self.seltext:
					context.set_font_size(self.font_size[i]+1)
					context.set_source_rgba(1,1,1,1)
					context.move_to(15-3,y+i*32-22)
					context.show_text (L_Names[i])
				else:
					context.set_font_size(self.font_size[i])
					context.set_source_rgba(0,0,0,1)
					context.move_to(15-3,y+i*32-22)
					context.show_text (L_Names[i])
			
    def Unmap(self,x,y):
    	#Reverse map a mouse location to a specific button
		i = int(((y+40)-self.y)/32)
		if i>len(self.NameBuffer)-1:
			i=len(self.NameBuffer)-1
		return i
		
    def DrawButton(self,w,h):
		x0=0
		y0=0
		radius=8
		x1=x0+w
		y1=y0+h
		self.buttonsurface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
		context = cairo.Context(self.buttonsurface)
		context.move_to(x0, y0 + radius)
		context.curve_to(x0 , y0, x0 , y0, x0 + radius, y0)
		context.line_to(x1 - radius, y0)
		context.curve_to(x1, y0, x1, y0, x1, y0 + radius)
		context.line_to(x1 , y1 - radius)
		context.curve_to(x1, y1, x1, y1, x1 - radius, y1)
		context.line_to(x0 + radius, y1)
		context.curve_to(x0, y1, x0, y1, x0, y1- radius)
		 
		context.close_path()
		pat = cairo.LinearGradient (x0, y0,  x0, y1)
		pat.add_color_stop_rgba (0, .1, .1, 1, 1)
		pat.add_color_stop_rgba (1, 1, 1, 1, 1)
		context.set_source(pat)
		context.fill_preserve()
		context.set_source_rgba(0, 0, 0, 1)
		context.set_line_width(1.0)
		context.stroke()

    def InitiateAnimation(self,opcode,data=None):
		if opcode==0:		#Abort all and reset environment registers
			self.inanimation=0
			self.activitycount=0
			self.leftshift=0
		elif opcode==1:		#Leftshift
			self.activitycount=self.activitycount+1		#Animation activity
			self.inanimation=1							#Active animation flag
			self.leftshift=-self.w						#Initial offset
			self.leftshiftd=-1							#Page shift direction
			self.leftshifti=0							#Increment counter
			self.leftshiftdlw=0							#Display previous page, to what side
			self.inleftshift=1							#Animation specific activity flag
		elif opcode==2:		#Rightshift w/ pttl
			self.activitycount=self.activitycount+1
			self.inanimation=1
			self.leftshift=self.w
			self.leftshiftd=1
			self.leftshiftdlw=1
			self.leftshifti=0
			self.prevtextsurface=self.textsurface		#Backup previous text surface for frameshifting
			self.inleftshift=1
		elif opcode==3:		#Leftshift w/ pttr
			self.activitycount=self.activitycount+1
			self.inanimation=1
			self.leftshiftd=-1
			self.leftshift=-self.w
			self.leftshifti=0
			self.leftshiftdlw=-1
			self.prevtextsurface=self.textsurface
			self.inleftshift=1



