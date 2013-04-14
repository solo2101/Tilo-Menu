#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#  2004-2005 Nigel Tao
#
#(c) Whise 2008,2009 <helderfraga@gmail.com>
#
# Bookmarks
# Part of the Tilo

# Supports konkeror, epiphany, firefox 2 and 3, chromium, opera
# The support to firefox 3 (json code) , chromium and opera where introduced by whise
import gi
gi.require_version("Gtk", "2.0")
from gi.repository import Gtk

import os, stat, re, fileinput, base64, backend
from ConfigParser import RawConfigParser
try: 
	import pysqlite2.dbapi2 as sqlite
	SQLITE_ENABLED = True
except: 
	try:
		import sqlite3 as sqlite
		SQLITE_ENABLED = True
	except: 
		SQLITE_ENABLED = False
try:
	import cjson
	json_decoder = cjson.decode
	JSON_ENABLED = True
except ImportError:
	try:
		import json
		json_decoder = json.loads
		JSON_ENABLED = True
	except:	JSON_ENABLED = False

class Node:
	def __init__ (self, parent, data):
		self.data = data
		self.parent = parent
		self.children = []

	def append (self, data):
		return self.append_node (Node (self, data))

	def append_node (self, node):
		self.children.append (node)
		return node

	def up (self):
		return self.parent

	def down (self):
		if len (self.children) == 0:
			return None
		return self.children[0]

	def next (self):
		if self.parent is None:
			return None
		siblings = self.parent.children
		i = siblings.index (self)+1
		if i < len (siblings):
			return siblings[i]
		return None

	# callback signature: func (node, user_data). user_data is used for the nodes
	# in the first-depth. Subsequent depths use the return value of the callback.
	def traverse (self, callback, user_data):
		for n in self.children:
			d = callback (n, user_data)
			n.traverse (callback, d)

class Root (Node):
	def __init__ (self):
		Node.__init__ (self, None, None)

def old_tree_format_to_new (old_tree, old_favicons):
	new_tree = Root()
	for (name, href_or_folder) in old_tree:
		node = Node (new_tree, None)
		if name is None:
			bookmark = None
		else:
			favicon = None
			if href_or_folder.__class__ == [].__class__:
				folder = href_or_folder
				old_tree_format_to_new (folder, old_favicons, node)
				href = None
			else:
				href = href_or_folder
				if old_favicons != None and href in old_favicons:
					favicon = old_favicons [href]
			bookmark = Bookmark (href, name, None, favicon)
		node.data = bookmark
		new_tree.append_node (node)
	return new_tree

class Bookmark:
	def __init__ (self, url, title, description, favicon):
		self.url = url
		self.title = title
		self.description = description
		self.favicon = favicon

class BrowserSupport:
	def isBrowser (self, browser): pass
	def icon (self): return None
	def isFunctional (self): return True
	def requiredModule (self): return None
	def bookmarksFilename (self, browser): pass
	def editorCmd (self): return None
	def editorLabel (self): return None
	def editorIcon (self): return None
	def createTree (self, filename): pass
browsers_supported = []

##############################################
# Opera
##############################################

BOOKMARKS_FILE = "bookmarks.adr"

def get_opera_bookmarks():
	
	appleaf_content_id = "opera"

	_opera_home = os.path.expanduser("~/.opera/")
	_bookmarks_path = os.path.join(_opera_home, BOOKMARKS_FILE)
	bookmarks = []
	
	try:
		import codecs
		with codecs.open(_bookmarks_path, "r", "UTF-8") as bfile:
			name = None
			url = None
			for line in bfile:
				line = line.strip()
				if line.startswith(u'NAME='):
					name = line[5:]
				elif line.startswith(u'URL='):
					url = line[4:]
				elif line.startswith(u'#'):
					if name != None and url != None:
						bookmarks.append([name,url])

			return bookmarks
	except: return [None,None]	




class OperaBookmarksParser (BrowserSupport):
	def __init__ (self):
		self.root = None
		#for x in get_bookmarks(fpath):
		#	print x['title'],x['uri'],x['type'],'text/x-moz-place'
		#print "Parsed # bookmarks:", list(get_bookmarks(fpath))
		self._opera_home = os.path.expanduser("~/.opera/")
		self._bookmarks_path = os.path.join(self._opera_home, BOOKMARKS_FILE)

	def isBrowser (self, browser):
		return browser.find ("opera") != -1 and os.path.exists (self._bookmarks_path)

	def icon (self):
		return "opera"

	def isFunctional (self):
		return True
	def requiredModule (self):
		return 'codecs'

	def bookmarksFilename (self, browser):
		dir = self._bookmarks_path
		if dir != None:
			return dir
		return None

	def editorCmd (self):
		return ""

	def editorLabel (self):
		return "Organize Bookmarks..."


	def createTree (self, filename):
		root = Root()
		node_id = {}
		for x in get_opera_bookmarks():
			
			root.append (Bookmark (x[1],x[0], None, None))
		return root


browsers_supported.append (OperaBookmarksParser())

##############################################
# Chromium
############################################## 


def get_chromium_home_file(needed_file):
	chromium_dir = os.path.expanduser("~/.config/chromium/Default/")
	if not os.path.exists(chromium_dir):
		return None

	return os.path.join(chromium_dir, needed_file)

def get_chromium_bookmarks(bookmarks_file):
	# construct and configure the parser
	if not bookmarks_file:
		return []

	with open(bookmarks_file) as f:
		content = f.read().decode("UTF-8")
		root = json_decoder(content)

	# make a dictionary of unique bookmarks
	bmap = {}

	def bmap_add(bmark, bmap):
		if bmark["id"] not in bmap:
			bmap[bmark["id"]] = bmark

	CONTAINER = "folder"
	UNWANTED_SCHEME = ("data", "place", "javascript")

	def is_container(ch):
		return ch["type"] == CONTAINER
	def is_bookmark(ch):
		return ch.get("url")
	def is_good(ch):
		return not ch["url"].split(":", 1)[0] in UNWANTED_SCHEME

	folders = []

	# add some folders
	folders.extend(root['roots']['bookmark_bar']['children'])
	folders.extend(root['roots']['other']['children'])

	for item in folders:
		if is_bookmark(item) and is_good(item):
			bmap_add(item, bmap)
		if is_container(item):
			folders.extend(item["children"])

	return bmap.values()



class ChromiumBookmarksParser (BrowserSupport):
	def __init__ (self):
		self.root = None
		#for x in get_bookmarks(fpath):
		#	print x['title'],x['uri'],x['type'],'text/x-moz-place'
		#print "Parsed # bookmarks:", list(get_bookmarks(fpath))


	def isBrowser (self, browser):
		return browser.find ("chromium-browser") != -1 and os.path.exists (get_chromium_home_file("Bookmarks"))

	def icon (self):
		return "chromium-browser"

	def isFunctional (self):
		return True
	def requiredModule (self):
		return "json"

	def bookmarksFilename (self, browser):
		dir = get_chromium_home_file("Bookmarks")
		if dir != None:
			return dir
		return None

	def editorCmd (self):
		return ""

	def editorLabel (self):
		return "Organize Bookmarks..."


	def createTree (self, filename):
		root = Root()
		node_id = {}
		
		for x in get_chromium_bookmarks(get_chromium_home_file("Bookmarks")):
			
			root.append (Bookmark (x['url'],x['name'], None, None))
		return root


browsers_supported.append (ChromiumBookmarksParser())

##############################################
# Firefox
##############################################

def get_firefox_home_file(needed_file):
    for firefox_dir in (os.path.expanduser(p) for p in
			("~/.mozilla/firefox-3/","~/.mozilla/firefox-3.9/","~/.mozilla/firefox-3.8/","~/.mozilla/firefox-3.7/","~/.mozilla/firefox-3.6/", "~/.mozilla/firefox-3.5/", "~/.mozilla/firefox/")):
        if os.path.exists(firefox_dir):
            break
    else:
        # no break
        return None
    # here we leak firefox_dir
    config = RawConfigParser({"Default" : 0})
    config.read(os.path.join(firefox_dir, "profiles.ini"))
    path = None

    for section in config.sections():
        if config.has_option(section, "Default") and config.get(section, "Default") == "1":
            path = config.get (section, "Path")
            break
        elif path is None and config.has_option(section, "Path"):
            path = config.get (section, "Path")
        
    if path is None:
        return ""

    if path.startswith("/"):
        return os.path.join(path, needed_file)

    return os.path.join(firefox_dir, path, needed_file)



def get_firefox_bookmarks(bookmarks_file):
	# construct and configure the parser
	if not bookmarks_file:
		return []

	with open(bookmarks_file) as f:
		content = f.read().decode("UTF-8")
		# HACK: Firefox' JSON writer leaves a trailing comma
		# HACK: at the end of the array, which no parser accepts
		if content.endswith(u"}]},]}"):
			content = content[:-6] + u"}]}]}"
		if content.endswith(u"[]},]}"):
			content = content[:-6] + u"[]}]}"
		try:
			root = json_decoder(content)
		except:print 'json error while reading firefox bookmarks...'

	# make a dictionary of unique bookmarks
	bmap = {}

	def bmap_add(bmark, bmap):
		if bmark["id"] not in bmap:
			bmap[bmark["id"]] = bmark

	def bmap_add_tag(id_, tag, bmap):
		if not "tags" in bmap[id_]:
			bmap[id_]["tags"] = []
		else:
			print "Already in, gets tag:", tag
		bmap[id_]["tags"].append(tag)

	MOZ_CONTAINER = "text/x-moz-place-container"
	MOZ_PLACE = "text/x-moz-place"
	UNWANTED_SCHEME = ("data", "place", "javascript")

	def is_container(ch):
		return ch["type"] == MOZ_CONTAINER
	def is_bookmark(ch):
		return ch["type"] == MOZ_PLACE and ch.get("uri")
	def is_good(ch):
		return not ch["uri"].split(":", 1)[0] in UNWANTED_SCHEME

	# find toplevel subfolders and tag folders
	catalogs = []
	tagcatalogs = []
	for child in root["children"]:
		if child.get("root") == "tagsFolder":
			tagcatalogs.extend(child["children"])
		elif child.get("root"):
			catalogs.append(child)

	# visit all subfolders recursively
	visited = set()
	while catalogs:
		next = catalogs.pop()
		if next["id"] in visited:
			continue
		for child in next["children"]:
			if is_container(child):
				catalogs.append(child)
				tagcatalogs.append(child)
			elif is_bookmark(child) and is_good(child):
				bmap_add(child, bmap)
		visited.add(next["id"])

	# visit all tag folders
	for tag in tagcatalogs:
		for bmark in tag["children"]:
			if is_bookmark(bmark) and is_good(bmark):
				bmap_add(bmark, bmap)
				bmap_add_tag(bmark["id"], tag["title"], bmap)

	return bmap.values()

class Firefox3FormatBookmarksParser (BrowserSupport):
	def __init__ (self):
		self.root = None
		#for x in get_bookmarks(fpath):
		#	print x['title'],x['uri'],x['type'],'text/x-moz-place'
		#print "Parsed # bookmarks:", list(get_bookmarks(fpath))


	def isBrowser (self, browser):
		return browser.find ("firefox") != -1 and os.path.exists (get_firefox_home_file("bookmarkbackups"))

	def icon (self):
		return "firefox"

	def isFunctional (self):
		return True
	def requiredModule (self):
		return "json"

	def bookmarksFilename (self, browser):
		dir = get_firefox_home_file("bookmarkbackups")
		if dir != None:
			return dir
		return None

	def editorCmd (self):
		return "firefox -chrome chrome://browser/content/places/places.xul"

	def editorLabel (self):
		return "Organize Bookmarks..."


	def createTree (self, filename):
		root = Root()
		node_id = {}
		for x in get_firefox_bookmarks(fpath):
			if fpath and os.path.splitext(fpath)[-1].lower() == ".json":
				root.append (Bookmark (x['uri'],x['title'], None, None))
		return root


def get_firefox_profile_dir():
	try:
		firefox_dir = os.path.expanduser("~/.mozilla/firefox/")
		path_pattern = re.compile("^Path=(.*)")
		for line in fileinput.input(firefox_dir + "profiles.ini"):
			if line == "":
				break
			match_obj = path_pattern.search(line)
			if match_obj:
				if match_obj.group(1).startswith("/"):
					return match_obj.group(1) + "/"
				else:
					return firefox_dir + match_obj.group(1) + "/"
	finally:
		fileinput.close()
	return None


class oldFirefox3FormatBookmarksParser (BrowserSupport):
	###This method uses sqlite , only works when firefox is not opened### use this method as a backup
	def __init__ (self):
		self.root = None

	def isBrowser (self, browser):
		return browser.find ("firefox") != -1 and os.path.exists (self.bookmarksFilename (browser))

	def icon (self):
		return "firefox"

	def isFunctional (self):
		return SQLITE_ENABLED
	def requiredModule (self):
		return "python-sqlite2"

	def bookmarksFilename (self, browser):
		dir = get_firefox_profile_dir()
		if dir != None:
			return dir + "places.sqlite"
		return None

	def editorCmd (self):
		return "firefox -chrome chrome://browser/content/places/places.xul"

	def editorLabel (self):
		return "Organize Bookmarks..."

	def createTree (self, filename):
		root = Root()
		node_id = {}

		def create_children (connection, parent_node, parent_id):
			connection = sqlite.connect (filename, timeout = 0.5)
			cursor = connection.cursor()
			cursor.execute ("SELECT title, id, fk, parent FROM moz_bookmarks WHERE parent = '%d' ORDER BY position" % (parent_id))
			for entry in cursor:
				title = entry[0]
				id = entry[1]
				fk = entry[2]
				parent = entry[3]
				url = None
				favicon = None
				if fk != None:
					c = connection.cursor()
					c.execute ("SELECT url, favicon_id FROM moz_places WHERE id = '%d'" % (fk))
					url, favicon_id = c.fetchone()

					if favicon_id != None:
						c = connection.cursor()
						c.execute ("SELECT mime_type, data FROM moz_favicons WHERE id = '%d'" % (favicon_id))
						mime_type, data = c.fetchone()

						loader = GdkPixbuf.Pixbuf.loader_new_with_mime_type (mime_type)
						loader.write (data)
						loader.close()
						pixbuf = loader.get_pixbuf()
						pixbuf = pixbuf.scale_simple (32, 32, GdkPixbuf.InterpType.BILINEAR)
						favicon = pixbuf

				if title is None:
					title = "<>"
				node = Node (parent_node, Bookmark (url, title, None, favicon))
				parent_node.append_node (node)
				if fk is None:
					create_children (connection, node, id)

		try:
			connection = sqlite.connect (filename)
			create_children (connection, root, 2)
		except sqlite.OperationalError, error:
			if self.root is None:
				root.append (Bookmark ("", "Error: firefox running, bookmarks locked\nDetails: %s" % (str (error)), None, None))
			else:
				# pass along old instance
				root = self.root
		else:
			self.root = root
		return root

dirloc = get_firefox_home_file("bookmarkbackups")
fpath = None
if dirloc:
	files = os.listdir(dirloc)
	if files:
		latest_file = (files.sort() or files)[-1]
		fpath = os.path.join(dirloc, latest_file)
if fpath and os.path.splitext(fpath)[-1].lower() == ".json" and JSON_ENABLED is True:
	browsers_supported.append (Firefox3FormatBookmarksParser())
else:
	browsers_supported.append (oldFirefox3FormatBookmarksParser())



##############################################
# Firefox 2
##############################################

try: import HTMLParser
except: HTMLPARSER_ENABLED = False
else:   HTMLPARSER_ENABLED = True

class MozillaFormatBookmarksParser (BrowserSupport):
	def isBrowser (self, browser):
		return browser.find ("firefox") != -1

	def icon (self):
		return "firefox"

	def isFunctional (self):
		return HTMLPARSER_ENABLED
	def requiredModule (self):
		return "python html parser"

	def bookmarksFilename (self, browser):
		dir = get_firefox_profile_dir()
		if dir != None:
			return dir + "bookmarks.html"
		return None

	def editorCmd (self):
		return "firefox -chrome chrome://browser/content/bookmarks/bookmarksManager.xul"

	def editorLabel (self):
		return "Organize Bookmarks..."

	# Based on GPL code taken from bookmarks-applet.py
	# as found in mate-python version 1.4.4 (author unknown).
	def createTree (self, filename):
		class Parser (HTMLParser.HTMLParser):
			# Based on GPL code taken from bookmarks-applet.py
			# as found in mate-python version 1.4.4 (author unknown).
			def __init__(self, bookmarks_file_name):
				HTMLParser.HTMLParser.__init__(self)
				self.root = Root()
				self.node = self.root
				self.chars = ""
				self.feed (file (bookmarks_file_name, 'r').read())

			def load_favicon (self, data):
				try:
					i = data.find (';')
					mime_type = data[5:i]
					i = i+8  # ";base64,"
					data32 = base64.b64decode (data[i:])
					loader = GdkPixbuf.Pixbuf.loader_new_with_mime_type (mime_type)
					loader.write (data32)
					loader.close()
					pixbuf = loader.get_pixbuf()
					pixbuf = pixbuf.scale_simple (32, 32, GdkPixbuf.InterpType.BILINEAR)
					return pixbuf
				except:
					return None

			def up (self):
				self.node = self.node.up()
			def down (self):
				bookmark = Bookmark (None, "", None, None)
				self.node = self.node.append (bookmark)
			def get (self):
				return self.node.data

			def handle_starttag (self, tag, attrs):
				tag = tag.lower()
				if tag == "h3":
					self.down()
				elif tag == "a":
					self.down()
					bookmark = self.get()
					for tag, value in attrs:
						tag = tag.lower()
						if tag == 'href':
							bookmark.url = value
						elif tag == 'icon':
							bookmark.favicon = self.load_favicon (value)
				elif tag == "hr":
					self.node.append (None)
				self.chars = ""

			def handle_data (self, chars):
				self.chars = self.chars + chars

			def handle_endtag (self, tag):
				tag = tag.lower()
				if tag == "a" or tag == "h3":
					bookmark = self.get()
					bookmark.title = self.chars
				if tag == "dl" or tag == "a":
					bookmark = self.get()
					self.up()
		return Parser (filename).root

browsers_supported.append (MozillaFormatBookmarksParser())

##############################################
# Epiphany
##############################################

try: import xml.sax
except: XML_SAX_ENABLED = False
else:   XML_SAX_ENABLED = True


class EpiphanyFormatBookmarksParser (BrowserSupport):
	def isBrowser (self, browser):
		if browser.find ("epiphany") != -1:
			return True
		else: return False

	def icon (self):
		return "epiphany"

	def isFunctional (self):
		return XML_SAX_ENABLED
	def requiredModule (self):
		return "python-xml"

	def bookmarksFilename (self, browser):
		self.bookmarks_file = os.path.expanduser("~/.mate2/epiphany/bookmarks.rdf")
		return self.bookmarks_file

	def editorCmd (self):
		return "epiphany --bookmarks-editor"

	def editorLabel (self):
		return "Edit Bookmarks..."

	def editorIcon (self):
		return "/usr/share/epiphany/icons/hicolor/16x16/actions/bookmark-view.png"

	def createTree (self, filename):
		# Based on GPL code taken from bookmarks-applet.py
		# as found in mate-python version 1.4.4 (author unknown).
		class Parser (xml.sax.ContentHandler):
			def __init__(self, bookmarks_file_name):
				xml.sax.ContentHandler.__init__(self)
				self.subjects = {}
				self.bookmarks_with_no_subjects = []
				self.chars = ""
				self.title = None
				self.href = None
				self.root_menu = []
				self.root_menu_map = {}
	
				parser = xml.sax.make_parser()
				parser.setContentHandler(self)
				if bookmarks_file_name and os.path.exists(bookmarks_file_name):
					parser.parse(bookmarks_file_name)

			def startElement(self, name, attrs):
				self.chars = ""
				if name == "item":
					self.title = None
					self.href = None
					self.no_subject = True

			def endElement(self, name):
				if name == "title":
					self.title = self.chars
				elif name == "link":
					if self.href is None:
						self.href = self.chars
				elif name == "ephy:smartlink":
					self.href = self.chars
				elif name == "dc:subject":
					self.no_subject = False
					s = self.chars
					if not s in self.subjects:
						self.subjects[s] = []
					self.subjects[s].append((self.title, self.href))
				elif name == "item":
					if self.no_subject:
						self.bookmarks_with_no_subjects.append((self.title, self.href))

			def characters(self, chars):
				self.chars = self.chars + chars

			def endDocument(self):
				self.root_menu = []
				createEpiphanyMenuSystem(self.root_menu, True, self.subjects.items(), self.bookmarks_with_no_subjects)

		def createEpiphanyMenuSystem (menu, toplevel, topics, uncategorized):
			# Apply Epiphany hierarchical bookmark system: see
			# http://home.exetel.com.au/harvey/epiphany/
			# We must use the exact same algorithm to get the same output.
			# This produces the same output as Epiphany 1.9.1.
			# Types:
			# 	* a Bookmark is a (title, href) pair, rendered as a 
			#	  separator if title is None.
			#	* a BookmarkList is a list of Bookmarks and 
			#	  (title, BookmarkList) pairs
			#	* titles, hrefs and topics are strings
			# input: 
			#	* topics is a list of (topic, list of Bookmarks) pairs
			#	* uncategorized is a list of Bookmarks, maybe empty
			#	* toplevel is True if this is the top level menu, where
			#	  we do not allow subdividions
			# output:
			#	* menu is a BookmarkList
			remaining = reduce(lambda x, (topic, bookmarks): x.union(bookmarks), 
					topics, set(uncategorized))
			unused = [(len(bookmarks), topic, bookmarks) 
					for topic, bookmarks in topics]
			menu_divisions = [[]]
			menu_divisions_named = []
			while True:
				unused = filter(lambda (l, t, b): l != 0, unused)
				unused.sort()
				if len(unused) == 0:
					break
				l, topic, bookmarks = unused.pop()
				if toplevel or (len(bookmarks) > 6 and len(remaining) > 20):
					# create a submenu
					submenu = []
					menu_divisions[0].append((topic, submenu))
					subtopics = []
					subuncat = set(bookmarks)
					for topic2, bookmarks2 in topics:
						if topic2 is topic:
							continue
						bookmarks_int = set(bookmarks).intersection(bookmarks2)
						if not bookmarks_int:
							continue
						subuncat -= bookmarks_int
						subtopics.append((topic2, list(bookmarks_int)))
					createEpiphanyMenuSystem(submenu, False, subtopics,
							list(subuncat))
				else:
					menu_divisions_named.append((topic, bookmarks))
				remaining -= set(bookmarks)
				unused = [(len(remaining.intersection(bookmarks)), topic, 
						bookmarks) for l, topic, bookmarks in unused]
			if menu_divisions_named:
				menu_divisions_named.sort(key = lambda x: x[0].lower())
				menu_divisions.extend(zip(*menu_divisions_named)[1])
			menu_divisions.append(uncategorized)
			for division in menu_divisions:
				if division:
					if menu and menu[-1][0] and not toplevel:
						# append a separator
						menu.append(None)
					division.sort(key = lambda x: x[0].lower())
					menu.extend (division)

		class FaviconsParser(xml.sax.ContentHandler):
			class EpiphanyFaviconCacheFileParser(xml.sax.ContentHandler):
				def __init__(self, favicon_cache_file_name, 
						favicon_cache_path):
					xml.sax.ContentHandler.__init__(self)
					self.favicon_uri_path_map = {}
					parser = xml.sax.make_parser()
					parser.setContentHandler(self)
					self.path = favicon_cache_path
					if favicon_cache_file_name and os.path.exists(
							favicon_cache_file_name):
						parser.parse(favicon_cache_file_name)

				def startElement(self, name, attrs):
					self.chars = ""
					if name == "node":
						self.uri = None
						self.hash = None
					elif name == "property":
						self.propertyId = attrs["id"]

				def endElement(self, name):
					if name == "node":
						self.favicon_uri_path_map[self.uri] = os.path.join(self.path, self.hash)
					elif name == "property":
						if self.propertyId == "2":
							self.uri = self.chars
						elif self.propertyId == "3":
							self.hash = self.chars
	
				def characters(self, chars):
					self.chars += chars

			def __init__(self, internal_bookmarks_file_name, 
					favicon_cache_file_name, favicon_cache_path, 
					pixbuf_cache = [{}]):
				xml.sax.ContentHandler.__init__(self)
				self.path_favicons_cached = pixbuf_cache[0]
				self.path_favicons = {}
				self.favicons = {}
				self.favicon_cache_path = favicon_cache_path

				self.favicon_uri_path_map = self.EpiphanyFaviconCacheFileParser(favicon_cache_file_name, favicon_cache_path).favicon_uri_path_map
				parser = xml.sax.make_parser()
				parser.setContentHandler(self)
				if internal_bookmarks_file_name and os.path.exists(
						internal_bookmarks_file_name):
					parser.parse(internal_bookmarks_file_name)
				pixbuf_cache[0] = self.path_favicons

			def pixbufFromUri(self, uri):
				for icon_path in [os.path.join(self.favicon_cache_path, uri.replace("/", "_")), self.favicon_uri_path_map.get(self.favicon)]:
					pixbuf = None
					if self.path_favicons_cached.has_key(icon_path):
						pixbuf = self.path_favicons_cached[icon_path]
					elif icon_path and os.path.exists(icon_path):
						try:
							pixbuf = icon_path
						except GObject.GError:
							pass
					self.path_favicons[icon_path] = pixbuf
					if pixbuf:
						return pixbuf

			def startElement(self, name, attrs):
				self.chars = ""
				if name == "node":
					self.href = None
					self.favicon = None
				elif name == "property":
					self.propertyId = attrs["id"]

			def endElement(self, name):
				if name == "node":
					if not self.favicon:
						return
					pixbuf = self.pixbufFromUri(self.favicon)
					if pixbuf:
						self.favicons[self.href] = pixbuf
				elif name == "property":
					if self.propertyId == "3":
						self.href = self.chars
					elif self.propertyId == "7":
						self.favicon = self.chars

			def characters(self, chars):
				self.chars += chars


		old_tree = Parser (self.bookmarks_file).root_menu
		old_favicons = FaviconsParser (*self.favicon_paths()).favicons
		return old_tree_format_to_new (old_tree, old_favicons)

	def favicon_paths (self):
		return [os.path.expanduser(x) for x in (
			"~/.mate2/epiphany/ephy-bookmarks.xml",
			"~/.mate2/epiphany/ephy-favicon-cache.xml",
			"~/.mate2/epiphany/favicon_cache/")]

browsers_supported.append (EpiphanyFormatBookmarksParser())


##############################################
# Konqueror / Galeon / Midori
##############################################

class XbelFormatBookmarksParser (BrowserSupport):
	def isBrowser (self, browser):
		if browser.find ("konqueror") != -1:
			self.bookmarks_file = os.path.expanduser("~/.kde/share/apps/konqueror/bookmarks.xml")
			return True
		elif browser.find("midori")  != -1:
			self.bookmarks_file =  os.path.expanduser("~/.config/midori/bookmarks.xbel")
			return True
		elif browser.find("galeon")  != -1:
			self.bookmarks_file =  os.path.expanduser("~/.galeon/bookmarks.xbel")
			return True
		else:return False

	def icon (self):
		return "konqueror"

	def isFunctional (self):
		return XML_SAX_ENABLED
	def requiredModule (self):
		return "python-xml"

	def bookmarksFilename (self, browser):
		return self.bookmarks_file

	def editorCmd (self):
		return "keditbookmarks"

	def editorLabel (self):
		return "Edit Bookmarks"

	def createTree (self, filename):
		class Parser (xml.sax.ContentHandler):
			def __init__(self, bookmarks_file_name):
				xml.sax.ContentHandler.__init__(self)
				self.root_menu = []
	
				self.currently_in_bookmark = False
				self.currently_in_folder = False
				self.currently_in_smarturl = False
				self.currently_in_title = False
	
				self.title = ""
				self.current_bookmark_name = None
				self.current_bookmark_href = None
				self.current_folder = self.root_menu
				self.folder_stack = [self.root_menu]
	
				parser = xml.sax.make_parser()
				parser.setContentHandler(self)
				if bookmarks_file_name and os.path.exists(bookmarks_file_name):
					parser.parse(bookmarks_file_name)

			def startElement(self, name, attrs):
				if name == "folder":
					self.currently_in_folder = True

				elif name == "bookmark":
					self.currently_in_bookmark = True
					if attrs.has_key("href"):
						self.current_bookmark_href = attrs["href"]
					else:
						self.current_bookmark_href = ""

				elif name == "smarturl":
					self.currently_in_smarturl = True
					self.current_bookmark_href = ""

				elif name == "title":
					self.currently_in_title = True
					self.title = ""

			def endElement(self, name):
				if name == "folder":
					self.folder_stack.pop()
					self.currently_in_folder = False

				if name == "separator":
					self.folder_stack[-1].append((None, None))

				elif name == "bookmark":
					self.folder_stack[-1].append((self.current_bookmark_name, self.current_bookmark_href))
					self.currently_in_bookmark = False
					self.current_bookmark_name = None
					self.current_bookmark_href = None

				elif name == "smarturl":
					self.currently_in_smarturl = False

				elif name == "title":
					if self.currently_in_bookmark:
						self.current_bookmark_name = self.title
					elif self.currently_in_folder:
						f = []
						self.folder_stack[-1].append((self.title, f))
						self.folder_stack.append(f)
					self.currently_in_title = False

			def characters(self, chars):
				if self.currently_in_title:
					self.title += chars
				elif self.currently_in_smarturl:
					self.current_bookmark_href += chars

		old_tree = Parser (self.bookmarks_file).root_menu
		return old_tree_format_to_new (old_tree, None)


browsers_supported.append (XbelFormatBookmarksParser())

## Wrapper

browser_cmd = backend.get_default_internet_browser()

class BookmarksMenu:
	def __init__ (self):
		self.format = None
		self.file = None
		for i in browsers_supported:
			if i.isBrowser (browser_cmd):
				self.format = i
				self.file = i.bookmarksFilename (browser_cmd)
				break
		self.mtime = self.get_mtime()
		self.tree = None
		self.dirty = True

	def is_dirty (self):
		return self.mtime != self.get_mtime()

	def get_mtime (self):
		if self.file is None: return 0
		return os.stat (self.file)[stat.ST_MTIME]

	def broken (self):
		return self.format is None or not self.format.isFunctional()
	def error (self):
		if self.format is None:
			if browser_cmd is None or browser_cmd == "":
				return "No Web Browser set as favorite.\nUse mate-control-center."
			return "Web Browser not supported:\n%s" % (browser_cmd)
		#if not self.format.isFunctional():
		return "Python module not installed:\n%s" % (self.format.requiredModule())

	def icon (self):
		if not self.broken():
			return self.format.icon()
		return None

	def hasEditor (self):
		return self.format.editorCmd() != None
	def editorLabel (self):
		return self.format.editorLabel()
	def editorIcon (self):
		return self.format.editorIcon()
	def editorCmd (self):
		return self.format.editorCmd()

	def getTree (self):
		if not self.broken() and (self.tree is None or self.is_dirty()):
			self.tree = self.format.createTree (self.file)
			self.mtime = self.get_mtime()
			self.dirty = True
		return self.tree


	def getBookmarks (self):
	
		self.bookmarker = []
		self.getTree().traverse (self.sendBookmark, 0)
		return self.bookmarker

	def sendBookmark (self,node, level):
		bookmark = node.data
		if bookmark.url != None and not self.broken() and not str(bookmark.url).startswith('place:'):
			if bookmark.favicon != None:
				self.bookmarker.append([bookmark.title,bookmark.url,bookmark.description, bookmark.favicon])
			else:
				self.bookmarker.append([bookmark.title,bookmark.url,bookmark.description, 'applications-internet'])
		return level+1

bookmarks = BookmarksMenu()
