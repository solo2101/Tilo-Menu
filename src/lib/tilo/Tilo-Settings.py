#!/usr/bin/env python3
# Tilo-Settings (GTK3)

import os, sys, tarfile, shutil, tempfile, xml.dom.minidom, subprocess
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf, GObject, GLib, Pango

import Globals
import backend
# IconFactory.Icontype is used for legacy theme fixups
try:
    import IconFactory
    ICON_TYPES = getattr(IconFactory, "Icontype", ["png", "xpm", "svg"])
except Exception:
    ICON_TYPES = ["png", "xpm", "svg"]

# i18n
try:
    with open("/etc/tilo/prefix", "r") as f:
        INSTALL_PREFIX = f.read().strip() or "/usr"
except Exception:
    INSTALL_PREFIX = "/usr"

import gettext
gettext.textdomain('tilo')
gettext.install('tilo', os.path.join(INSTALL_PREFIX, 'share', 'locale'))
gettext.bindtextdomain('tilo', os.path.join(INSTALL_PREFIX, 'share', 'locale'))
_ = gettext.gettext


# --------------------------
# helpers (dialogs, files)
# --------------------------
def ask_yes_no(parent, message, title="Tilo"):
    d = Gtk.MessageDialog(parent=parent, flags=0,
                          type=Gtk.MessageType.QUESTION,
                          buttons=Gtk.ButtonsType.YES_NO,
                          message_format=message)
    d.set_title(title)
    resp = d.run()
    d.destroy()
    return resp == Gtk.ResponseType.YES

def info(parent, message, title="Tilo"):
    d = Gtk.MessageDialog(parent=parent, flags=0,
                          type=Gtk.MessageType.INFO,
                          buttons=Gtk.ButtonsType.OK,
                          message_format=message)
    d.set_title(title)
    d.run()
    d.destroy()

def warn(parent, message, title="Tilo"):
    d = Gtk.MessageDialog(parent=parent, flags=0,
                          type=Gtk.MessageType.WARNING,
                          buttons=Gtk.ButtonsType.OK,
                          message_format=message)
    d.set_title(title)
    d.run()
    d.destroy()

def safe_extract(tar: tarfile.TarFile, path: str):
    # avoid path traversal
    for m in tar.getmembers():
        p = os.path.realpath(os.path.join(path, m.name))
        if not p.startswith(os.path.realpath(path) + os.sep):
            raise RuntimeError("Blocked unsafe path in archive")
    tar.extractall(path)


# --------------------------
# main window
# --------------------------
class TiloSettings(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL, title=_("Tilo Settings"))
        try:
            self.set_icon_from_file(Globals.Applogo)
        except Exception:
            pass
        self.set_border_width(6)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.folder = os.path.expanduser("~")

        self.notebook = Gtk.Notebook()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(self.notebook, True, True, 0)
        self.add(vbox)

        # tabs
        self.add_theme_tab()
        self.add_prefs_tab()
        self.add_commands_tab()
        self.add_about_tab()

        # footer buttons
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.pack_end(hb, False, False, 0)
        btn_cancel = Gtk.Button.new_with_label(_("Cancel"))
        btn_apply  = Gtk.Button.new_with_label(_("Apply"))
        btn_ok     = Gtk.Button.new_with_label(_("Ok"))
        btn_cancel.connect("clicked", lambda *_: Gtk.main_quit())
        btn_apply.connect("clicked", lambda *_: self.save_settings())
        btn_ok.connect("clicked", self._ok_clicked)
        hb.pack_start(btn_cancel, False, False, 0)
        hb.pack_end(btn_ok, False, False, 0)

        # welcome or about page short-cuts
        if len(sys.argv) == 2 and sys.argv[1] == "--about":
            self.notebook.set_current_page(3)

        self.show_all()

    # ------------- Theme tab -------------
    def add_theme_tab(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        page.set_border_width(6)

        # === Menu theme ===
        self.image_menu = Gtk.Image()
        self.label_menu = Gtk.Label()
        self.label_menu.set_line_wrap(True)
        self.label_menu.set_max_width_chars(40)
        self.combo_menu = Gtk.ComboBoxText()
        bt_menu_ins = Gtk.Button.new_with_label(_("Install"))
        bt_menu_un  = Gtk.Button.new_with_label(_("Uninstall"))
        bt_menu_ins.connect("clicked", self.install_theme_dialog)
        bt_menu_un.connect("clicked", self.uninstall_theme_dialog, "Menu", self.combo_menu)

        menu_frame = Gtk.Frame.new(f"<b>{_('Menu Selection')}</b>")
        menu_frame.get_label_widget().set_use_markup(True)
        vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vb.set_border_width(10)
        hb_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hb_top.pack_start(self.image_menu, True, True, 0)
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right_box.pack_start(self.label_menu, True, True, 0)
        hb_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hb_actions.pack_start(bt_menu_ins, False, False, 0)
        hb_actions.pack_start(bt_menu_un, False, False, 0)
        hb_actions.pack_start(self.combo_menu, True, True, 0)
        right_box.pack_start(hb_actions, False, False, 0)
        hb_top.pack_start(right_box, True, True, 0)
        vb.pack_start(hb_top, True, True, 0)
        menu_frame.add(vb)
        page.pack_start(menu_frame, True, True, 0)

        # === Button theme ===
        self.image_button = Gtk.Image()
        self.label_button = Gtk.Label()
        self.label_button.set_line_wrap(True)
        self.label_button.set_max_width_chars(30)
        self.combo_button = Gtk.ComboBoxText()
        bt_but_ins = Gtk.Button.new_with_label(_("Install"))
        bt_but_un  = Gtk.Button.new_with_label(_("Uninstall"))
        bt_but_ins.connect("clicked", self.install_theme_dialog)
        bt_but_un.connect("clicked", self.uninstall_theme_dialog, "Button", self.combo_button)

        but_frame = Gtk.Frame.new(f"<b>{_('Button Selection')}</b>")
        but_frame.get_label_widget().set_use_markup(True)
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hb.set_border_width(6)
        hb.pack_start(self.image_button, False, False, 0)
        hb.pack_start(self.label_button, True, True, 0)
        vb2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        hb2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hb2.pack_start(bt_but_ins, False, False, 0)
        hb2.pack_start(bt_but_un, False, False, 0)
        hb2.pack_start(self.combo_button, True, True, 0)
        vb2.pack_start(hb, True, True, 0)
        vb2.pack_start(hb2, False, False, 0)
        but_frame.add(vb2)

        # === Icon theme ===
        self.image_icon = Gtk.Image()
        self.label_icon = Gtk.Label()
        self.label_icon.set_line_wrap(True)
        self.label_icon.set_max_width_chars(30)
        self.combo_icon = Gtk.ComboBoxText()
        bt_ico_ins = Gtk.Button.new_with_label(_("Install"))
        bt_ico_un  = Gtk.Button.new_with_label(_("Uninstall"))
        bt_ico_ins.connect("clicked", self.install_theme_dialog)
        bt_ico_un.connect("clicked", self.uninstall_theme_dialog, "Icon", self.combo_icon)

        ico_frame = Gtk.Frame.new(f"<b>{_('Icon Selection')}</b>")
        ico_frame.get_label_widget().set_use_markup(True)
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hb.set_border_width(6)
        hb.pack_start(self.image_icon, False, False, 0)
        hb.pack_start(self.label_icon, True, True, 0)
        vb3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        hb3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hb3.pack_start(bt_ico_ins, False, False, 0)
        hb3.pack_start(bt_ico_un, False, False, 0)
        hb3.pack_start(self.combo_icon, True, True, 0)
        vb3.pack_start(hb, True, True, 0)
        vb3.pack_start(hb3, False, False, 0)
        ico_frame.add(vb3)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.pack_start(but_frame, True, True, 0)
        row.pack_start(ico_frame, True, True, 0)
        page.pack_start(row, True, True, 0)

        # === Sound theme ===
        self.combo_sound = Gtk.ComboBoxText()
        self.label_sound = Gtk.Label()
        self.label_sound.set_line_wrap(True)
        self.label_sound.set_max_width_chars(50)
        bt_snd_ins = Gtk.Button.new_with_label(_("Install"))
        bt_snd_un  = Gtk.Button.new_with_label(_("Uninstall"))
        bt_snd_ins.connect("clicked", self.install_theme_dialog)
        bt_snd_un.connect("clicked", self.uninstall_theme_dialog, "Sound", self.combo_sound)

        snd_frame = Gtk.Frame.new(f"<b>{_('Sound theme')}</b>")
        snd_frame.get_label_widget().set_use_markup(True)
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hb.set_border_width(6)
        hb.pack_start(bt_snd_ins, False, False, 0)
        hb.pack_start(bt_snd_un, False, False, 0)
        hb.pack_start(self.label_sound, True, True, 0)
        hb.pack_end(self.combo_sound, False, False, 0)
        snd_frame.add(hb)
        page.pack_start(snd_frame, False, False, 0)

        # populate & connect
        self.reload_themes("Menu")
        self.reload_themes("Button")
        self.reload_themes("Icon")
        self.reload_themes("Sound")

        self.combo_menu.connect("changed", self._redraw_theme, "Menu")
        self.combo_button.connect("changed", self._redraw_theme, "Button")
        self.combo_icon.connect("changed", self._redraw_theme, "Icon")
        self.combo_sound.connect("changed", self._redraw_theme, "Sound")

        self.notebook.append_page(page, Gtk.Label(label=_("Themes")))

    def _pixbuf_or_default(self, path, w, h):
        try:
            return GdkPixbuf.Pixbuf.new_from_file_at_size(path, w, h)
        except Exception:
            try:
                return GdkPixbuf.Pixbuf.new_from_file(os.path.join(Globals.GraphicsDirectory, "theme.png"))
            except Exception:
                return None

    def _redraw_theme(self, combo, kind):
        active = combo.get_active_text()
        if not active:
            return
        if kind == "Menu":
            pb = self._pixbuf_or_default(f"{Globals.ThemeDirectory}Menu/{active}/themepreview.png", 200, 230)
            if pb: self.image_menu.set_from_pixbuf(pb)
            l = self._credits_text("Menu", active)
            self.label_menu.set_text(l)
        elif kind == "Button":
            pb = self._pixbuf_or_default(f"{Globals.ThemeDirectory}Button/{active}/themepreview.png", 64, 64)
            if pb: self.image_button.set_from_pixbuf(pb)
            l = self._credits_text("Button", active)
            self.label_button.set_text(l)
        elif kind == "Icon":
            pb = self._pixbuf_or_default(f"{Globals.ThemeDirectory}Icon/{active}/themepreview.png", 64, 64)
            if pb: self.image_icon.set_from_pixbuf(pb)
            l = self._credits_text("Icon", active)
            self.label_icon.set_text(l)
        elif kind == "Sound":
            if active == "None":
                self.label_sound.set_text("")
            else:
                self.label_sound.set_text(self._credits_text("Sound", active))

    def _credits_text(self, kind, name):
        xmlp = os.path.join(Globals.ThemeDirectory, kind, name, "themedata.xml")
        try:
            doc = xml.dom.minidom.parse(xmlp)
            node = doc.getElementsByTagName("ContentData")[0]
            nm = node.getAttribute("Name")
            au = node.getAttribute("Author")
            cp = node.getAttribute("Copyright")
            return f"{nm} by: {au}\n\n{cp}"
        except Exception:
            return ""

    def reload_themes(self, kind):
        base = os.path.join(INSTALL_PREFIX, "share", "tilo", "Themes", kind)
        items = []
        if os.path.isdir(base):
            items = sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))], key=str.upper)

        if kind == "Menu":
            self.combo_menu.get_model().clear()
            for i, d in enumerate(items):
                self.combo_menu.append_text(d)
                if d == Globals.Settings.get("Menu_Name", ""):
                    self.combo_menu.set_active(i)
            if self.combo_menu.get_active() < 0 and items:
                self.combo_menu.set_active(0)
            self._redraw_theme(self.combo_menu, "Menu")

        elif kind == "Button":
            self.combo_button.get_model().clear()
            for i, d in enumerate(items):
                self.combo_button.append_text(d)
                if d == Globals.Settings.get("Button_Name", ""):
                    self.combo_button.set_active(i)
            if self.combo_button.get_active() < 0 and items:
                self.combo_button.set_active(0)
            self._redraw_theme(self.combo_button, "Button")

        elif kind == "Icon":
            self.combo_icon.get_model().clear()
            for i, d in enumerate(items):
                self.combo_icon.append_text(d)
                if d == Globals.Settings.get("Icon_Name", ""):
                    self.combo_icon.set_active(i)
            if self.combo_icon.get_active() < 0 and items:
                self.combo_icon.set_active(0)
            self._redraw_theme(self.combo_icon, "Icon")

        elif kind == "Sound":
            self.combo_sound.get_model().clear()
            self.combo_sound.append_text("None")
            active = 0
            for idx, d in enumerate(items, start=1):
                self.combo_sound.append_text(d)
                if d == Globals.Settings.get("Sound_Theme", "None"):
                    active = idx
            self.combo_sound.set_active(active)
            self._redraw_theme(self.combo_sound, "Sound")

    # ------------- Preferences tab -------------
    def add_prefs_tab(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        page.set_border_width(10)

        # bind key
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.chk_bind = Gtk.CheckButton(label=_("Bind keyboad key") + " ex: <Alt>F11, <Control>F1")
        self.ent_bind = Gtk.Entry()
        self.ent_bind.set_text(Globals.Settings.get('Bind_Key', ''))
        self.chk_bind.set_active(int(Globals.Settings.get('SuperL', 0)))
        hb.pack_start(self.chk_bind, True, True, 0)
        hb.pack_end(self.ent_bind, True, True, 0)
        page.pack_start(hb, False, False, 0)

        # toggles
        def mk_check(key, label):
            c = Gtk.CheckButton(label=label)
            c.set_active(int(Globals.Settings.get(key, 0)))
            return key, c

        checks = [
            mk_check('Shownetandemail', _('Show Internet and Email Buttons')),
            mk_check('GtkColors',       _('Use Gtk Theme Colors in Program List')),
            mk_check('TabHover',        _('Tab Selection on Mouse Hover')),
            mk_check('System_Icons',    _('Use system icons instead of theme icons')),
            mk_check('Distributor_Logo',_('Use distributor logo instead of button theme')),
            mk_check('Show_Thumb',      _('Show thumbnails in recent items when available')),
            mk_check('Show_Tips',       _('Show tooltips in program list')),
            mk_check('Disable_PS',      _('Disable Places and System in program list')),
        ]
        self.check_map = dict(checks)
        for __k, c in checks:
            page.pack_start(c, False, False, 0)

        # sizes & list type
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.spin_icon = Gtk.SpinButton()
        self.spin_icon.set_range(16, 256); self.spin_icon.set_increments(1, 16)
        self.spin_icon.set_value(float(Globals.Settings.get('IconSize', 32)))
        hb.pack_start(self.spin_icon, False, False, 0)
        hb.pack_start(Gtk.Label(label=_('Icon Size in Program List')), False, False, 10)
        page.pack_start(hb, False, False, 0)

        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.spin_recent = Gtk.SpinButton()
        self.spin_recent.set_range(1, 50); self.spin_recent.set_increments(1, 5)
        self.spin_recent.set_value(float(Globals.Settings.get('ListSize', 10)))
        hb.pack_start(self.spin_recent, False, False, 0)
        hb.pack_start(Gtk.Label(label=_('Number of Items in Recent Items List')), False, False, 10)
        page.pack_start(hb, False, False, 0)

        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.combo_plist = Gtk.ComboBoxText()
        for t in (_('Listview'), _('Buttons (expanded)'), _('Buttons (fixed)'), _('Iconview (fastest)')):
            self.combo_plist.append_text(t)
        # (Drop “Cairo” type in GTK3 build)
        self.combo_plist.set_active(int(Globals.Settings.get('Prog_List', 0)))
        hb.pack_start(self.combo_plist, False, False, 0)
        hb.pack_start(Gtk.Label(label=_('Program list type')), False, False, 10)
        page.pack_start(hb, False, False, 0)

        # tab hover effect (kept for compatibility; no visual logic here)
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.combo_tabfx = Gtk.ComboBoxText()
        for t in (_('None'), _('Grow'), _('Black and White'), _('Blur'), _('Glow'), _('Saturate')):
            self.combo_tabfx.append_text(t)
        self.combo_tabfx.set_active(int(Globals.Settings.get('Tab_Efect', 0)))
        hb.pack_start(self.combo_tabfx, False, False, 0)
        hb.pack_start(Gtk.Label(label=_('Tab hover effect')), False, False, 10)
        page.pack_start(hb, False, False, 0)

        self.notebook.append_page(page, Gtk.Label(label=_("Preferences")))

    # ------------- Commands tab -------------
    def add_commands_tab(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        page.set_border_width(6)

        def row(key, label):
            hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            hb.pack_start(Gtk.Label(label=label), False, False, 0)
            e = Gtk.Entry(); e.set_text(Globals.Settings.get(key, ""))
            hb.pack_start(e, True, True, 0)
            page.pack_start(hb, False, False, 0)
            return key, e

        fields = [
            row('Search',          _('Search')),
            row('Network_Config',  _('Network Config')),
            row('Control_Panel',   _('Control Panel')),
            row('Package_Manager', _('Package Manager')),
            row('Help',            _('Help')),
            row('Power',           _('Shutdown Dialog')),
            row('Lock',            _('Lock Screen')),
            row('LogoutNow',       _('Logout')),
            row('Logout',          _('Logout Dialog')),
            row('Restart',         _('Restart')),
            row('Suspend',         _('Suspend')),
            row('Hibernate',       _('Hibernate')),
            row('Run',             _('Run')),
            row('Shutdown',        _('Shutdown')),
            row('User',            _('User about')),
            row('AdminRun',        _('Open as Administrator')),
            row('MenuEditor',      _('Menu Editor')),
        ]
        self.cmd_map = dict(fields)
        self.notebook.append_page(page, Gtk.Label(label=_("Commands")))

    # ------------- About tab -------------
    def add_about_tab(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        page.set_border_width(6)

        img = Gtk.Image()
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_size(Globals.Applogo, 80, 80)
            img.set_from_pixbuf(pb)
        except Exception:
            pass

        title = Gtk.Label(label=f"Tilo-Menu {Globals.version}")
        title.modify_font(Pango.FontDescription('Sans Bold 14'))
        credits = Gtk.Label(
            label=_("Tilo-Menu is based on GnoMenu, a consolidated menu for the GNOME/MATE desktop.\nBy Helder Fraga aka Whise <helderfraga@gmail.com>\nPlease Donate")
        )
        credits.set_justify(Gtk.Justification.CENTER)

        def open_url(_w, url):
            subprocess.Popen(["sh", "-c", f"xdg-open {url} >/dev/null 2>&1 &"])

        def link(label, url):
            b = Gtk.Button.new_with_label(label); b.connect("clicked", open_url, url); b.set_border_width(5); return b

        page.pack_start(img, False, False, 0)
        page.pack_start(title, False, False, 10)
        page.pack_start(credits, False, False, 10)
        page.pack_start(link(_("Donate"), "http://Gnome-look.org/content/donate.php?content=93057"), False, False, 0)
        page.pack_start(link(_("Download More Themes"), "http://Gnome-look.org/index.php?xcontentmode=189"), False, False, 0)
        page.pack_start(link(_("GnoMenu Themes Specifications"), "http://launchpad.net/GnoMenu/trunk/2.3/+download/GnoMenuThemeSpec.pdf"), False, False, 0)
        page.pack_start(link(_("Report Bug"), "https://bugs.launchpad.net/GnoMenu"), False, False, 0)
        page.pack_start(link(_("Help Translate"), "https://translations.launchpad.net/GnoMenu/trunk"), False, False, 0)
        page.pack_start(link(_("Visit Homepage"), "https://launchpad.net/gnomenu"), False, False, 0)

        self.notebook.append_page(page, Gtk.Label(label=_("About")))

    # ------------- Install/Uninstall -------------
    def uninstall_theme_dialog(self, _w, kind, combo: Gtk.ComboBoxText):
        name = combo.get_active_text()
        if not name:
            return
        if ask_yes_no(self, f"{_('Uninstall')} {kind} {_('theme')} {name}?"):
            install_dir = os.path.join(Globals.ThemeDirectory, kind, name)
            cmd = f'{Globals.Settings.get("AdminRun","")} sh -c "rm -rf \'{install_dir}\'"'
            subprocess.call(cmd, shell=True)
            # update list
            model = combo.get_model()
            idx = combo.get_active()
            model.remove(model.get_iter(idx))
            if model.iter_n_children(None) > 0:
                combo.set_active(0)

    def install_theme_dialog(self, *_a):
        dlg = Gtk.FileChooserDialog(
            title=_("Install a new theme"),
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
        )
        flt = Gtk.FileFilter()
        for pat in ("*.tar.bz2", "*.tar.gz", "*.tar", "*.tgz", "*.tbz2"):
            flt.add_pattern(pat)
        dlg.add_filter(flt)
        dlg.set_current_folder(self.folder)
        resp = dlg.run()
        filename = dlg.get_filename()
        self.folder = dlg.get_current_folder() or self.folder
        dlg.destroy()
        if resp == Gtk.ResponseType.OK and filename:
            self._install_theme(filename)

    def _install_theme(self, filename):
        tmpdir = tempfile.mkdtemp(prefix="tilo_")
        try:
            with tarfile.open(filename, "r:*") as tf:
                safe_extract(tf, tmpdir)
        except Exception as e:
            shutil.rmtree(tmpdir, ignore_errors=True)
            warn(self, _("Error - Theme package is corrupt!") + f"\n\n{e}")
            return

        # Find the theme root (folder containing themedata.xml)
        theme_root = None
        for root, dirs, files in os.walk(tmpdir):
            if "themedata.xml" in files:
                theme_root = root
                break
        if not theme_root:
            shutil.rmtree(tmpdir, ignore_errors=True)
            warn(self, _("Error - theme not installed\nMaybe the Theme was packaged incorrectly\nTry to install the Theme manually"))
            return

        # Parse type
        try:
            doc = xml.dom.minidom.parse(os.path.join(theme_root, "themedata.xml"))
            # new spec: <content type="Menu|Button|Icon|Sound">
            node = (doc.getElementsByTagName("content") or doc.getElementsByTagName("ContentData"))[0]
            typ = node.getAttribute("type") or "Menu"
        except Exception:
            shutil.rmtree(tmpdir, ignore_errors=True)
            warn(self, _("Error - theme not installed\nMaybe the Theme was packaged incorrectly\nTry to install the Theme manually"))
            return

        name = os.path.basename(theme_root.rstrip(os.sep))
        install_dir = os.path.join(INSTALL_PREFIX, "share", "tilo", "Themes", typ)
        dest = os.path.join(install_dir, name)

        # Already installed?
        if os.path.isdir(dest):
            if not ask_yes_no(self, _("Theme exists. Continue?")):
                shutil.rmtree(tmpdir, ignore_errors=True)
                return
            cmd = f'{Globals.Settings.get("AdminRun","")} sh -c "rm -rf \'{dest}\'"'
            subprocess.call(cmd, shell=True)

        # Copy (use AdminRun to elevate if needed)
        cmd = f'{Globals.Settings.get("AdminRun","")} sh -c "mkdir -p \'{install_dir}\' && cp -a \'{theme_root}\' \'{dest}\'"'
        rc = subprocess.call(cmd, shell=True)
        if rc != 0 or not os.path.isdir(dest):
            shutil.rmtree(tmpdir, ignore_errors=True)
            warn(self, _("Error - theme not installed\nMaybe the Theme was packaged incorrectly\nTry to install the Theme manually"))
            return

        # Legacy icon renames (keep old behavior)
        if typ in ("Icon", "Menu"):
            updated = False
            mapping = getattr(Globals, "MenuCairoSystemIcon", {})
            if typ == "Icon":
                for k, v in mapping.items():
                    for ext in ICON_TYPES:
                        src = os.path.join(dest, f"{k}.{ext}")
                        dst = os.path.join(dest, f"{v}.{ext}")
                        if os.path.exists(src):
                            cmd = f'{Globals.Settings.get("AdminRun","")} sh -c "mv \'{src}\' \'{dst}\'"'
                            subprocess.call(cmd, shell=True)
                            updated = True
            else:  # Menu
                td = os.path.join(dest, "themedata.xml")
                try:
                    with open(td, "r", encoding="utf-8", errors="ignore") as fh:
                        data = fh.read()
                    for k, v in mapping.items():
                        data = data.replace(f'"{k}.', f'"{v}.')
                        for ext in ICON_TYPES:
                            src = os.path.join(dest, f"{k}.{ext}")
                            dst = os.path.join(dest, f"{v}.{ext}")
                            if os.path.exists(src):
                                cmd = f'{Globals.Settings.get("AdminRun","")} sh -c "mv \'{src}\' \'{dst}\'"'
                                subprocess.call(cmd, shell=True)
                                updated = True
                    with open(os.path.join(tmpdir, "themedata.xml"), "w", encoding="utf-8") as fh:
                        fh.write(data)
                    cmd = f'{Globals.Settings.get("AdminRun","")} sh -c "cp \'{os.path.join(tmpdir, "themedata.xml")}\' \'{td}\'"'
                    subprocess.call(cmd, shell=True)
                except Exception:
                    pass
            if updated:
                info(self, _("This theme was created for a previous version of GnoMenu.\nThe theme was automatically updated in order to work properly."))

        shutil.rmtree(tmpdir, ignore_errors=True)
        # refresh combos
        self.reload_themes(typ)
        info(self, _("Theme installed"))

    # ------------- Save / Apply -------------
    def save_settings(self):
        backend.save_setting("Bind_Key", self.ent_bind.get_text())
        backend.save_setting("SuperL", int(self.chk_bind.get_active()))

        # toggles
        for key, widget in self.check_map.items():
            backend.save_setting(key, int(widget.get_active()))

        # sizes
        backend.save_setting("IconSize", int(self.spin_icon.get_value()))
        backend.save_setting("ListSize", int(self.spin_recent.get_value()))

        # combos
        backend.save_setting("Prog_List", int(self.combo_plist.get_active()))
        backend.save_setting("Tab_Efect", int(self.combo_tabfx.get_active()))
        backend.save_setting("Menu_Name", self.combo_menu.get_active_text() or "")
        backend.save_setting("Button_Name", self.combo_button.get_active_text() or "")
        backend.save_setting("Icon_Name", self.combo_icon.get_active_text() or "")
        backend.save_setting("Sound_Theme", self.combo_sound.get_active_text() or "None")

        # commands
        for key, entry in self.cmd_map.items():
            backend.save_setting(key, entry.get_text())

    def _ok_clicked(self, *_a):
        self.save_settings()
        # offer to restart Tilo menu if running
        try:
            out = subprocess.check_output("ps axo '%p,%a' | grep 'Tilo.py' | grep -v grep | cut -d',' -f1", shell=True)
            pid = out.decode().strip()
            if pid and ask_yes_no(self, _('Menu needs to restart, restart now?')):
                subprocess.call(f"kill -9 {pid}", shell=True)
        except Exception:
            pass
        Gtk.main_quit()


def main():
    win = TiloSettings()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
