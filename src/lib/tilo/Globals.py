#!/usr/bin/env python3
# Global menu settings

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

from gi.repository import Gdk

def get_screen_size():
    """Return (width, height) using modern GDK API, with fallbacks."""
    try:
        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_primary_monitor()
            if monitor is None and display.get_n_monitors() > 0:
                monitor = display.get_monitor(0)
            if monitor:
                geo = monitor.get_geometry()
                # If you want to respect HiDPI scale, uncomment next two lines:
                try: scale = monitor.get_scale_factor()
                except Exception: scale = 1
                # return geo.width * scale, geo.height * scale
                return geo.width, geo.height
    except Exception:
        pass

    # Fallback to deprecated API if needed
    try:
        scr = Gdk.Screen.get_default()
        if scr:
            return scr.get_width(), scr.get_height()
    except Exception:
        pass

    # Last-ditch default
    return 1024, 768

import gc
import os
import sys
import xml.dom.minidom
import gettext

# local modules
import backend
import utils

# install prefix
try:
    with open("/etc/tilo/prefix", "r") as f:
        INSTALL_PREFIX = f.read().strip() or "/usr"
except Exception:
    INSTALL_PREFIX = "/usr"

# i18n
gettext.textdomain("tilo")
gettext.install("tilo", os.path.join(INSTALL_PREFIX, "share", "locale"))
gettext.bindtextdomain("tilo", os.path.join(INSTALL_PREFIX, "share", "locale"))

def _(s):
    return gettext.gettext(s)

# optional numpy
try:
    import numpy  # noqa: F401
    Has_Numpy = True
except Exception:
    Has_Numpy = False
    print("python numpy not installed, some effects and gtk native colors will be disabled")

# app info
name = "Tilo"
version = "0.3.1"
appdirname = "tilo"
print(f"{name} {version}")

############ paths ############
HomeDirectory = os.path.expanduser("~")
cfg_root = os.path.join(HomeDirectory, f".{appdirname}")
os.makedirs(cfg_root, exist_ok=True)

ConfigDirectory = cfg_root
AutoStartDirectory = os.path.join(HomeDirectory, ".config", "autostart")
ProgramDirectory = os.path.join(INSTALL_PREFIX, "lib", appdirname) + "/"
ThemeDirectory = os.path.join(INSTALL_PREFIX, "share", appdirname, "Themes") + "/"
GraphicsDirectory = os.path.join(INSTALL_PREFIX, "lib", appdirname, "graphics") + "/"

########### defaults ##########
ThemeCategories = ["Menu", "Icon", "Button"]
mateconf_app_key = f"/apps/{appdirname}"
TransitionS = 25        # ms
TransitionQ = 0.05      # 0..1
FirstUse = False

DefaultSettings = {
    "Tab_Efect": 1,
    "Bind_Key": "Super_L",
    "Sound_Theme": "None",
    "Show_Thumb": 0,
    "Disable_PS": 0,
    "Show_Tips": 0,
    "Prog_List": 3,
    "System_Icons": 0,
    "Distributor_Logo": 0,
    "Menu_Name": "Menu",
    "IconSize": 28,
    "ListSize": 10,
    "SuperL": 0,
    "Icon_Name": "Newstyles",
    "Button_Name": "GnoBlue",
    "Shownetandemail": 1,
    "GtkColors": 0,
    "TabHover": 0,
    "Search": "mate-search-tool",
    "Network_Config": "nm-connection-editor",
    "Control_Panel": "mate-control-center",
    "Package_Manager": "gksu synaptic",
    "Help": "yelp",
    "Power": "mate-session-save --shutdown-dialog",
    "Lock": "mate-screensaver-command --lock",
    "Suspend": f"python -u {ProgramDirectory}session-manager.py suspend",
    "Shutdown": f"python -u {ProgramDirectory}session-manager.py shutdown",
    "Hibernate": f"python -u {ProgramDirectory}session-manager.py hibernate",
    "Run": f"python -u {ProgramDirectory}Mate_run_dialog.py",
    "Logout": "mate-session-save --logout-dialog",
    "LogoutNow": "mate-session-save --logout",
    "Restart": f"python -u {ProgramDirectory}session-manager.py reboot",
    "User": "mate-about-me",
    "AdminRun": "gksu",
    "MenuEditor": "mozo",
}

Settings = DefaultSettings.copy()
MaliciousStrings = ['rm ', 'sudo ', 'gksudo ', 'gksu ', 'su ', 'mkfs', '/dev', ':(){:|:', 'wget', 'chmod', 'os.system', 'fork']

def SecurityCheck(command):
    for st in MaliciousStrings:
        if command.find(st) != -1:
            utils.show_warning(_('Tilo detected a malicious script in this theme.\nThe script was blocked!\nYou should uninstall the selected theme and contact the website where you got it.\n\nThe script that tried to run was:') + ' ' + command.replace('&', ''))
            return ''
    return command

def SetDefaultSettings():
    for x in DefaultSettings:
        backend.save_setting(x, DefaultSettings[x])
    global FirstUse
    FirstUse = True

def ReloadSettings():
    def _set_defaults():
        for x in DefaultSettings:
            backend.save_setting(x, DefaultSettings[x])
        global FirstUse
        FirstUse = True

    def _get_settings():
        print("settings load")
        for x in DefaultSettings:
            Settings[x] = backend.load_setting(x)

    # globals populated here
    global orientation, panel_size, flip, MenuActions, MenuCommands, ImageDirectory, Actions, IconDirectory, MenuButtonDirectory, ThemeColor, ShowTop, FirstUse, Hibernate, StartMenuTemplate, ThemeColorCode, ThemeColorHtml, NegativeThemeColorCode, MenuWidth, MenuHeight, IconW, IconH, IconInX, IconInY, IconInW, IconInH, SearchX, SearchY, SearchW, SearchH, SearchIX, SearchIY, SearchInitialText, SearchTextColor, SearchBackground, SearchWidget, SearchWidgetPath, UserIconFrameOffsetX, UserIconFrameOffsetY, UserIconFrameOffsetH, UserIconFrameOffsetW, PG_buttonframe, PG_buttonframedimensions, MenuHasSearch, MenuHasIcon, MenuHasFade, OnlyShowFavs, OnlyShowRecentApps, CairoSearchTextColor, CairoSearchBackColor, CairoSearchBorderColor, CairoSearchRoundAngle, PG_iconsize, RI_numberofitems, MenuButtonCount, MenuButtonNames, MenuButtonMarkup, MenuButtonNameOffsetX, MenuButtonNameOffsetY, MenuButtonCommands, MenuButtonX, MenuButtonY, MenuButtonImage, MenuButtonImageBack, MenuButtonIcon, MenuButtonIconSel, MenuButtonIconX, MenuButtonIconY, MenuButtonIconSize, MenuButtonExecOnHover, MenuButtonSub, MenuButtonClose, MenuCairoIconButton, MenuLabelCount, MenuLabelNames, MenuLabelMarkup, MenuLabelX, MenuLabelY, MenuLabelCommands, MenuTabCount, MenuTabNames, MenuTabMarkup, MenuTabNameOffsetX, MenuTabNameOffsetY, MenuTabCommands, MenuTabX, MenuTabY, MenuTabImage, MenuTabIcon, MenuTabImageSel, MenuTabSub, MenuTabClose, MenuCairoIconTab, MenuCairoIcontabX, MenuCairoIcontabY, MenuCairoIcontabSize, MenuTabInvertTextColorSel, MenuImageCount, MenuImageNames, MenuImageX, MenuImageY, MenuImage, ButtonHasTop, ButtonLabelCount, ButtonBackground, ButtonTop, StartButton, StartButtonTop, ButtonLabelName, ButtonLabelMarkup, ButtonLabelX, ButtonLabelY, MenuButtonNameAlignment, MenuTabNameAlignment, MenuLabelNameAlignment, GtkColorCode

    menubar = Gtk.MenuBar()  # keep a Gtk object around to init GTK properly

    orientation = backend.load_setting("orientation")
    panel_size = backend.load_setting("size")
    flip = False if orientation == "top" else None

    _get_settings()
    for x in DefaultSettings:
        if Settings[x] is None:
            _set_defaults()
            _get_settings()
            break

    MenuActions = []
    MenuCommands = []
    def _add(action, cmd):
        MenuActions.append(action)
        MenuCommands.append(cmd)

    _add('Search', Settings['Search'])
    _add('Network Config', Settings['Network_Config'])
    _add('Control Panel', Settings['Control_Panel'])
    _add('Package Manager', Settings['Package_Manager'])
    _add('Help', Settings['Help'])
    _add('Power', Settings['Power'])
    _add('Shutdown', Settings['Shutdown'])
    _add('Lock', Settings['Lock'])
    _add('Suspend', Settings['Suspend'])
    _add('Hibernate', Settings['Hibernate'])
    _add('Run', Settings['Run'])
    _add('Logout', Settings['Logout'])
    _add('LogoutNow', Settings['LogoutNow'])
    _add('Restart', Settings['Restart'])

    ThemeColor = 'white'
    ImageDirectory = f"{INSTALL_PREFIX}/share/{appdirname}/Themes/Menu/{Settings['Menu_Name']}/"
    IconDirectory = f"{INSTALL_PREFIX}/share/{appdirname}/Themes/Icon/{Settings['Icon_Name']}/"
    MenuButtonDirectory = f"{INSTALL_PREFIX}/share/{appdirname}/Themes/Button/{Settings['Button_Name']}/"
    PG_iconsize = int(float(Settings['IconSize']))
    RI_numberofitems = int(float(Settings['ListSize']))

    # read Menu themedata.xml
    try:
        XMLSettings = xml.dom.minidom.parse(f"{ImageDirectory}themedata.xml")
    except Exception:
        print("Error loading Menu theme, reverting to default")
        _set_defaults()
        XMLSettings = xml.dom.minidom.parse(f"{ImageDirectory}themedata.xml")

    XContent = XMLSettings.childNodes[0].getElementsByTagName("theme")

    # choose color variant
    Found = 0
    for node in XContent:
        if node.attributes["color"].value in (ThemeColor, "All"):
            XBase = node
            ThemeColorHtml = node.attributes["colorvalue"].value
            ThemeColorCode = Gdk.RGBA()
            ThemeColorCode.parse(ThemeColorHtml)
            NegativeThemeColorCode = Gdk.RGBA()
            NegativeThemeColorCode.red = 1.0 - ThemeColorCode.red
            NegativeThemeColorCode.green = 1.0 - ThemeColorCode.green
            NegativeThemeColorCode.blue = 1.0 - ThemeColorCode.blue
            NegativeThemeColorCode.alpha = ThemeColorCode.alpha
            Found = 1
            break
    if Found == 0:
        print(f"Error: Failed to find theme color: {ThemeColor}")
        print("The available values are:")
        for node in XContent:
            print(node.attributes["color"].value)
        sys.exit(1)

    # background image size or explicit WindowDimensions
    SBase = XBase.getElementsByTagName("Background")
    StartMenuTemplate = SBase[0].attributes["Image"].value
    try:
        im = GdkPixbuf.Pixbuf.new_from_file(f"{ImageDirectory}{StartMenuTemplate}")
        MenuWidth = im.get_width()
        MenuHeight = im.get_height()
    except Exception:
        SBase = XBase.getElementsByTagName("WindowDimensions")
        MenuWidth = int(SBase[0].attributes["Width"].value)
        MenuHeight = int(SBase[0].attributes["Height"].value)

    # icon frame
    SBase = XBase.getElementsByTagName("IconSettings")
    try:
        UserIconFrameOffsetX = int(SBase[0].attributes["X"].value)
        UserIconFrameOffsetW = int(SBase[0].attributes["Width"].value)
        UserIconFrameOffsetH = int(SBase[0].attributes["Height"].value)

        ori = orientation or ""
        is_bottom = ori in ("bottom", "botton")
        if is_bottom:
            UserIconFrameOffsetY = int(SBase[0].attributes["Y"].value)
        elif ori == "top":
            UserIconFrameOffsetY = MenuHeight - int(SBase[0].attributes["Y"].value) - UserIconFrameOffsetH
        else:
            UserIconFrameOffsetY = int(SBase[0].attributes["Y"].value)

        IconW = int(SBase[0].attributes["Width"].value)
        IconH = int(SBase[0].attributes["Height"].value)
        IconInX = int(SBase[0].attributes["InsetX"].value)
        IconInY = int(SBase[0].attributes["InsetY"].value)
        IconInW = int(SBase[0].attributes["InsetWidth"].value)
        IconInH = int(SBase[0].attributes["InsetHeight"].value)
    except Exception:
        pass

    # search bar
    SBase = XBase.getElementsByTagName("SearchBarSettings")
    SearchWidget = SBase[0].attributes["Widget"].value
    if SearchWidget != "None":
        SearchX = int(SBase[0].attributes["X"].value)
        SearchW = int(SBase[0].attributes["Width"].value)
        SearchH = int(SBase[0].attributes["Height"].value)
        ori = orientation or ""
        is_bottom = ori in ("bottom", "botton")
        if is_bottom:
            SearchY = int(SBase[0].attributes["Y"].value)
        elif ori == "top":
            SearchY = MenuHeight - int(SBase[0].attributes["Y"].value) - SearchH
        else:
            SearchY = int(SBase[0].attributes["Y"].value)

        if SearchWidget == "Custom":
            SearchIX = int(SBase[0].attributes["InsetX"].value)
            SearchIY = int(SBase[0].attributes["InsetY"].value)
            SearchInitialText = SBase[0].attributes["InitialText"].value
            try:
                SearchTextColor = SBase[0].attributes["TextColor"].value
            except Exception:
                SearchTextColor = "#000000"
            SearchBackground = SBase[0].attributes["Background"].value
            SearchWidgetPath = SBase[0].attributes["WidgetName"].value

        if SearchWidget == "Cairo":
            try:
                CairoSearchTextColor = SBase[0].attributes["TextColor"].value
            except Exception:
                CairoSearchTextColor = "#000000"
            try:
                CairoSearchBackColor = SBase[0].attributes["BackColor"].value
            except Exception:
                CairoSearchBackColor = "#FFFFFF"
            try:
                CairoSearchBorderColor = SBase[0].attributes["BorderColor"].value
            except Exception:
                CairoSearchBorderColor = "#000000"
            try:
                CairoSearchRoundAngle = int(SBase[0].attributes["RoundAngle"].value)
            except Exception:
                CairoSearchRoundAngle = 0

    # program list
    SBase = XBase.getElementsByTagName("ProgramListSettings")
    PG_buttonframedimensions = (int(SBase[0].attributes["Width"].value), int(SBase[0].attributes["Height"].value))
    ori = orientation or ""
    is_bottom = ori in ("bottom", "botton")
    if is_bottom:
        PG_buttonframe = (int(SBase[0].attributes["X"].value), int(SBase[0].attributes["Y"].value))
    elif ori == "top":
        PG_buttonframe = (int(SBase[0].attributes["X"].value), MenuHeight - int(SBase[0].attributes["Y"].value) - int(PG_buttonframedimensions[1]))
    else:
        PG_buttonframe = (int(SBase[0].attributes["X"].value), int(SBase[0].attributes["Y"].value))
    try:
        OnlyShowFavs = int(SBase[0].attributes["OnlyShowFavs"].value)
    except Exception:
        OnlyShowFavs = 0
    try:
        OnlyShowRecentApps = int(SBase[0].attributes["OnlyShowRecentApps"].value)
    except Exception:
        OnlyShowRecentApps = 0

    # capabilities
    SBase = XBase.getElementsByTagName("Capabilities")
    MenuHasSearch = int(SBase[0].attributes["HasSearch"].value)
    MenuHasIcon = int(SBase[0].attributes["HasIcon"].value)
    MenuHasFade = int(SBase[0].attributes["HasFadeTransition"].value)

    # buttons
    MenuButtons = XBase.getElementsByTagName("Button")
    MenuButtonCount = len(MenuButtons)
    MenuButtonNames, MenuButtonMarkup = [], []
    MenuButtonNameOffsetX, MenuButtonNameOffsetY = [], []
    MenuButtonX, MenuButtonY = [], []
    MenuButtonImage, MenuButtonImageBack = [], []
    MenuButtonIcon, MenuButtonIconSel = [], []
    MenuButtonIconX, MenuButtonIconY, MenuButtonIconSize = [], [], []
    MenuButtonExecOnHover, MenuCairoIconButton = [], []
    MenuButtonSub, MenuButtonCommands, MenuButtonClose = [], [], []
    MenuButtonNameAlignment = []

    for node in MenuButtons:
        try:
            im = GdkPixbuf.Pixbuf.new_from_file(ImageDirectory + node.attributes["Image"].value)
        except Exception:
            print("Warning - Error loading theme, reverting to defaults")
            SetDefaultSettings()
            break

        h = im.get_height()
        MenuButtonNames.append(node.attributes["Name"].value)
        MenuButtonMarkup.append(node.attributes["Markup"].value)
        MenuButtonNameOffsetX.append(int(node.attributes["TextX"].value))
        try:
            MenuButtonNameAlignment.append(int(node.attributes["TextAlignment"].value))
        except Exception:
            MenuButtonNameAlignment.append(0)
        MenuButtonImage.append(node.attributes["Image"].value)
        try:
            MenuButtonImageBack.append(node.attributes["ImageBack"].value)
        except Exception:
            MenuButtonImageBack.append('')
        MenuButtonIcon.append(node.attributes["ButtonIcon"].value)
        MenuButtonIconSel.append(node.attributes["ButtonIconSel"].value)
        try:
            MenuButtonExecOnHover.append(int(node.attributes["ExecuteOnHover"].value))
        except Exception:
            MenuButtonExecOnHover.append(0)
        try:
            MenuCairoIconButton.append(node.attributes["Icon"].value)
        except Exception:
            MenuCairoIconButton.append("")
        try:
            MenuButtonIconX.append(int(node.attributes["ButtonIconX"].value))
        except Exception:
            MenuButtonIconX.append(0)
        try:
            MenuButtonIconY.append(int(node.attributes["ButtonIconY"].value))
        except Exception:
            MenuButtonIconY.append(0)
        try:
            MenuButtonIconSize.append(int(node.attributes["ButtonIconSize"].value))
        except Exception:
            MenuButtonIconSize.append(0)

        MenuButtonX.append(int(node.attributes["ButtonX"].value))
        ori = orientation or ""
        is_bottom = ori in ("bottom", "botton")
        if is_bottom:
            MenuButtonNameOffsetY.append(int(node.attributes["TextY"].value))
            MenuButtonY.append(int(node.attributes["ButtonY"].value))
        elif ori == "top":
            MenuButtonNameOffsetY.append(int(node.attributes["TextY"].value))
            MenuButtonY.append(MenuHeight - int(node.attributes["ButtonY"].value) - h)
        else:
            MenuButtonNameOffsetY.append(int(node.attributes["TextY"].value))
            MenuButtonY.append(int(node.attributes["ButtonY"].value))

        MenuButtonCommands.append(node.attributes["Command"].value)
        MenuButtonSub.append(int(node.attributes["SubMenu"].value))
        MenuButtonClose.append(int(node.attributes["CloseMenu"].value))

    # labels
    MenuLabels = XBase.getElementsByTagName("Label")
    MenuLabelCount = len(MenuLabels)
    MenuLabelNames, MenuLabelMarkup, MenuLabelCommands = [], [], []
    MenuLabelX, MenuLabelY = [], []
    MenuLabelNameAlignment = []
    for node in MenuLabels:
        MenuLabelNames.append(node.attributes["Name"].value)
        MenuLabelMarkup.append(node.attributes["Markup"].value)
        MenuLabelX.append(int(node.attributes["LabelX"].value))
        try:
            MenuLabelNameAlignment.append(int(node.attributes["TextAlignment"].value))
        except Exception:
            MenuLabelNameAlignment.append(0)
        ori = orientation or ""
        is_bottom = ori in ("bottom", "botton")
        if is_bottom:
            MenuLabelY.append(int(node.attributes["LabelY"].value))
        elif ori == "top":
            MenuLabelY.append(MenuHeight - int(node.attributes["LabelY"].value))
        else:
            MenuLabelY.append(int(node.attributes["LabelY"].value))
        if SecurityCheck(node.attributes["Command"].value) != '':
            MenuLabelCommands.append(node.attributes["Command"].value)
        else:
            MenuLabelCommands.append('')

    # tabs
    MenuTabs = XBase.getElementsByTagName("Tab")
    MenuTabCount = len(MenuTabs)
    MenuTabNames, MenuTabMarkup = [], []
    MenuTabNameOffsetX, MenuTabNameOffsetY = [], []
    MenuTabX, MenuTabY = [], []
    MenuTabImage, MenuTabIcon, MenuTabImageSel = [], [], []
    MenuCairoIconTab, MenuCairoIcontabX, MenuCairoIcontabY, MenuCairoIcontabSize = [], [], [], []
    MenuTabInvertTextColorSel = []
    MenuTabSub, MenuTabCommands, MenuTabClose = [], [], []
    MenuTabNameAlignment = []

    for node in MenuTabs:
        try:
            im = GdkPixbuf.Pixbuf.new_from_file(ImageDirectory + node.attributes["Image"].value)
            h = im.get_height()
        except Exception:
            im = GdkPixbuf.Pixbuf.new_from_file(ImageDirectory + node.attributes["ImageSel"].value)
            h = im.get_height()

        MenuTabNames.append(node.attributes["Name"].value)
        MenuTabMarkup.append(node.attributes["Markup"].value)
        MenuTabNameOffsetX.append(int(node.attributes["TextX"].value))
        try:
            MenuTabNameAlignment.append(int(node.attributes["TextAlignment"].value))
        except Exception:
            MenuTabNameAlignment.append(0)
        MenuTabImage.append(node.attributes["Image"].value)
        MenuTabImageSel.append(node.attributes["ImageSel"].value)
        MenuTabIcon.append(node.attributes["TabIcon"].value)
        try:
            MenuCairoIconTab.append(node.attributes["Icon"].value)
        except Exception:
            MenuCairoIconTab.append("")
        try:
            MenuCairoIcontabX.append(int(node.attributes["TabIconX"].value))
        except Exception:
            try:
                MenuCairoIcontabX.append(int(node.attributes["IconX"].value))
                print("WARNING - IconX is deprecated, use TabIconX instead")
            except Exception:
                MenuCairoIcontabX.append(0)
        try:
            MenuCairoIcontabY.append(int(node.attributes["TabIconY"].value))
        except Exception:
            try:
                MenuCairoIcontabY.append(int(node.attributes["IconY"].value))
                print("WARNING - IconY is deprecated, use TabIconY instead")
            except Exception:
                MenuCairoIcontabY.append(0)
        try:
            MenuCairoIcontabSize.append(int(node.attributes["TabIconSize"].value))
        except Exception:
            try:
                MenuCairoIcontabSize.append(int(node.attributes["IconSize"].value))
                print("WARNING - IconSize is deprecated, use TabIconSize instead")
            except Exception:
                MenuCairoIcontabSize.append(0)
        try:
            MenuTabInvertTextColorSel.append(int(node.attributes["InvertTextColorOnSel"].value))
        except Exception:
            MenuTabInvertTextColorSel.append(1)

        MenuTabX.append(int(node.attributes["TabX"].value))
        ori = orientation or ""
        is_bottom = ori in ("bottom", "botton")
        if is_bottom:
            MenuTabNameOffsetY.append(int(node.attributes["TextY"].value))
            MenuTabY.append(int(node.attributes["TabY"].value))
        elif ori == "top":
            MenuTabNameOffsetY.append(int(node.attributes["TextY"].value))
            MenuTabY.append(MenuHeight - int(node.attributes["TabY"].value) - h)
        else:
            MenuTabNameOffsetY.append(int(node.attributes["TextY"].value))
            MenuTabY.append(int(node.attributes["TabY"].value))

        MenuTabCommands.append(node.attributes["Command"].value)
        MenuTabSub.append(int(node.attributes["SubMenu"].value))
        MenuTabClose.append(int(node.attributes["CloseMenu"].value))

    # images
    MenuImages = XBase.getElementsByTagName("Image")
    MenuImageCount = len(MenuImages)
    MenuImageNames, MenuImageX, MenuImageY, MenuImage = [], [], [], []
    for node in MenuImages:
        im = GdkPixbuf.Pixbuf.new_from_file(ImageDirectory + node.attributes["Image"].value)
        h = im.get_height()
        MenuImageNames.append(node.attributes["Name"].value)
        MenuImage.append(node.attributes["Image"].value)
        MenuImageX.append(int(node.attributes["ImageX"].value))
        ori = orientation or ""
        is_bottom = ori in ("bottom", "botton")
        if is_bottom:
            MenuImageY.append(int(node.attributes["ImageY"].value))
        elif ori == "top":
            MenuImageY.append(MenuHeight - int(node.attributes["ImageY"].value) - h)
        else:
            MenuImageY.append(int(node.attributes["ImageY"].value))

    # button theme
    try:
        XMLSettings = xml.dom.minidom.parse(MenuButtonDirectory + "themedata.xml")
    except Exception:
        print("Error loading Menu button theme, reverting to default")
        SetDefaultSettings()
        XMLSettings = xml.dom.minidom.parse(MenuButtonDirectory + "themedata.xml")

    XBase = XMLSettings.getElementsByTagName("theme")
    ButtonHasTop = int(XBase[0].attributes["Top"].value)
    ShowTop = ButtonHasTop

    XMLSettings = xml.dom.minidom.parse(MenuButtonDirectory + "themedata.xml")
    XBase = XMLSettings.childNodes[0].childNodes[1]

    ButtonBackground = XMLSettings.getElementsByTagName("Background")
    if ButtonBackground:
        for node in ButtonBackground:
            StartButton = (
                MenuButtonDirectory + str(node.attributes["Image"].value),
                MenuButtonDirectory + str(node.attributes["ImageHover"].value),
                MenuButtonDirectory + str(node.attributes["ImagePressed"].value),
            )
    else:
        StartButton = (
            MenuButtonDirectory + "start-here.png",
            MenuButtonDirectory + "start-here-glow.png",
            MenuButtonDirectory + "start-here-depressed.png",
        )

    ButtonTop = XMLSettings.getElementsByTagName("Top")
    if ButtonTop:
        for node in ButtonTop:
            StartButtonTop = (
                MenuButtonDirectory + str(node.attributes["Image"].value),
                MenuButtonDirectory + str(node.attributes["ImageHover"].value),
                MenuButtonDirectory + str(node.attributes["ImagePressed"].value),
            )
    else:
        StartButtonTop = (
            MenuButtonDirectory + "start-here-top.png",
            MenuButtonDirectory + "start-here-top-glow.png",
            MenuButtonDirectory + "start-here-top-depressed.png",
        )

    ButtonLabels = XMLSettings.getElementsByTagName("Label")
    ButtonLabelCount = len(ButtonLabels)
    ButtonLabelName = ""
    ButtonLabelMarkup = ""
    ButtonLabelX = 0
    ButtonLabelY = 0
    if ButtonLabels:
        for node in ButtonLabels:
            ButtonLabelName = node.attributes["Name"].value
            ButtonLabelMarkup = node.attributes["MarkupNormal"].value
            ButtonLabelX = int(node.attributes["LabelX"].value)
            ButtonLabelY = int(node.attributes["LabelY"].value)

# strings for translation
String_list = ['Start', 'Menu', 'Control Panel', 'Favorites', 'Applications', 'My Computer', 'Computer', 'Recently Used', 'Recent', 'Recent Documents', 'Recent Items', 'Recent Applications', 'Web Bookmarks', 'Web Sites', 'Show History', 'History', 'Leave', 'Shutdown', 'Lock Screen', 'Lock', 'Lock Computer', 'Home Folder', 'Personal Folder', 'Home', 'Network', 'Connect', 'Connect To', 'Connect To Server', 'Connect to Server', 'Package Manager', 'Help', 'Power', 'Search', 'About Me', 'Log Out', 'Shutdown Computer', 'Shut Down...', 'Shut Down', 'Run', 'Run Application', 'Execute Application', 'All Applications', 'All Programs', 'Help And Support', 'Logout', 'System', 'Control Center', 'Install Software', 'Status', 'Programs', 'User', 'Distro', 'Hdd', 'Most Used', 'Used', 'Music', 'Videos', 'Pictures', 'Documents', 'Games', 'Suspend', 'Hibernate', 'Search for Files', 'Help Center']
String_list_translated = [_('Start'), _('Menu'), _('Control Panel'), _('Favorites'), _('Applications'), _('My Computer'), _('Computer'), _('Recently Used'), _('Recent'), _('Recent Documents'), _('Recent Items'), _('Recent Applications'), _('Web Bookmarks'), _('Web Sites'), _('Show History'), _('History'), _('Leave'), _('Shutdown'), _('Lock Screen'), _('Lock'), _('Lock Computer'), _('Home Folder'), _('Personal Folder'), _('Home'), _('Network'), _('Connect'), _('Connect To'), _('Connect To Server'), _('Connect to Server'), _('Package Manager'), _('Help'), _('Power'), _('Search'), _('About Me'), _('Log Out'), _('Shutdown Computer'), _('Shut Down...'), _('Shut Down'), _('Run'), _('Run Application'), _('Execute Application'), _('All Applications'), _('All Programs'), _('Help And Support'), _('Logout'), _('System'), _('Control Center'), _('Install Software'), _('Status'), _('Programs'), _('User'), _('Distro'), _('Hdd'), _('Most Used'), _('Used'), _('Music'), _('Videos'), _('Pictures'), _('Documents'), _('Games'), _('Suspend'), _('Hibernate'), _('Search for Files'), _('Help Center')]

# load settings
try:
    ReloadSettings()
except Exception:
    print("**WARNING** - Unable to load settings, using defaults")
    print("Traceback:\n", sys.exc_info())
    SetDefaultSettings()
    ReloadSettings()

# screen size
screen = Gdk.Screen.get_default()
screenwidth = screen.get_width() if screen else 1024
screenheight = screen.get_height() if screen else 768

# icon theme
DefaultIconTheme = Gtk.IconTheme.get_default()
GtkIconTheme = DefaultIconTheme

# system icon mappings
MenuCairoSystemIcon = {
    'm_webbookmarks': 'applications-internet',
    'm_recentapps': 'applications-other',
    'm_shutdown': 'system-shutdown',
    'm_applications': 'applications-accessories',
    'm_favorites': 'emblem-favorite',
    'firefox_icon': 'web-browser',
    'm_computer': 'computer',
    'm_connect': 'mate-network-properties',
    'm_controlpanel': 'mate-control-center',
    'm_documents': 'folder-documents',
    'm_games': 'applications-games',
    'm_help': 'mate-help',
    'm_home': 'folder-home',
    'm_music': 'folder-music',
    'm_network': 'gtk-network',
    'm_pictures': 'folder-images',
    'm_recentitems': 'document-open-recent',
    'm_search': 'search',
    'm_synaptic': 'emblem-package',
    'm_videos': 'folder-videos',
    'no-user-image': 'gtk-missing-image',
    'thunderbird_icon': 'evolution',
    'm_trash': 'user-trash',
    'm_terminal': 'terminal',
    'm_run': 'gtk-execute',
    'm_lockscreen': 'lock',
    'm_logoutuser': 'system-switch-user',
    'm_software': 'system-software-install',
    'm_networktools': 'preferences-system-network',
    'm_systemmonitor.png': 'utilities-system-monitor',
}

# user image and assets
UserImageFrame = ImageDirectory + "user-image-frame.png"
DefaultUserImage = IconDirectory + "gtk-missing-image.png"
UserImage = os.path.join(HomeDirectory, ".face")
if not os.path.isfile(UserImage):
    UserImage = DefaultUserImage

Applogo = GraphicsDirectory + "logo.svg"
BrokenImage = GraphicsDirectory + "brokenlink.png"

gc.collect()
