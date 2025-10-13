GnoMenu Documentation.

Copyright (C) 2010 GnoMenu Team, Helder Fraga, Shaun C. Marolf, Chris Hughes

Written by: Shaun C. Marolf, Helder Fraga

https://launchpad.net/gnomenu

------
Index:
------

1.0 Description
2.0 Installing GnoMenu
	2.1 Dependencies
	2.2 Install
		2.2.1 Install directories
		2.2.2 Avant-Window-Navigator applet install
		2.2.3 Cairo-Dock applet install
		2.2.4 Xfce applet install
		2.2.5 64 bit install
		2.2.6 Plasma Applet install
		2.2.7 Docky helper (applet) install
	2.3 Uninstall
	2.4 Installing new themes
	2.5 Configuring GnoMenu
3.0 Known GnoMenu Issues
4.0 Creating GnoMenu Themes
	4.1 Button Themes
	4.2 Icon Themes
	4.3 Sound Themes
	4.4 Menu Themes



----------------
1.0 Description:
---------------- 

GnoMenu is a consolidated menu system for Gnome that brings eye candy to the user's desktop. It is a fully functional third Generation menu system that supports themes for composited or non composited desktops. It can emulate the look and feel of most menus found on today's modern desktops, such as KDE, Windows XP, Vista and Windows 7. It can also be used to create unique custom menu designs, due to its powerful XML theme engine.

Based on “Vista Start Menu” by Chris Hughes. It was picked up for further development by Helder Fraga. Chris Hughes is a member of the GnoMenu team.
Helder has since forked the project and renamed it to GnoMenu. The current stable release is 2.0

GnoMenu is released under the GNU/GPL Version 3 software license.
Under Helder's development GnoMenu has had many serious bugs, annoyances and issues fixed. GnoMenu is maturing rapidly and proving to be a powerful menu applet in its own right.

GnoMenu is written in Python, which will allow it to be cross platform compatible in the future if desired.

GnoMenu has achieved the  goal to allow new and unique menu designs while being compliant with Gnome Menu standards. Though most have, not all the features planned on for GnoMenu have been implemented yet they are in (at the very least) the planning and drafting phases.


-----------------------
2.0 Installing GnoMenu:
-----------------------

Its best to use the packages for your type of distribution (i.e. DEB or RPM, etc.) However, installing from source files is extremely easy as well.
**Before installing GnoMenu from source code make sure ALL dependencies are met**

You can find info on distribution packages here: https://answers.launchpad.net/gnomenu/+faq/769

-----------------
2.1 Dependencies:
-----------------

* Depends:

python
python-xdg
python-cairo
python-gtk2 - that includes pygtk and python-pango
python-gnomeapplet *** necessary only when running on gnome-panel *** - or in some distros "python gnome desktop"
python-xml - may be needed in older distributions (eg: ubuntu before karmic)

* Recomends:

gmenu - will use this instead of xdg if it is installed
python-numpy - for gtk theme colors and some tab effects
python-gconf - or in some distros "python gnome"
python-keybinder or python-xlib - for keybinding
gettext - for translations
zeitgeist

WARNING - In some distribution the packages names may not be the same.(this is the Ubuntu example)

------------
2.2 Install:
------------

extract the contents of the tar.gz
cd "path of where you extracted the tar.gz"

sudo make install

(depending on the distribution the "sudo" command my change)

Then go to your gnome-panel , right click, add to panel, and select GnoMenu


--------------------------
2.2.1 Install directories:
--------------------------

GnoMenu installs by default in /usr/, where the themes get installed in /usr/share and the python code goes in /usr/lib.
You can change this by using the variables PREFIX and DESTDIR, eg:

sudo make install PREFIX=/etc

this will install GnoMenu in /etc/

-------------------------------------------
2.2.2 Avant-Window-Navigator applet install
-------------------------------------------

Just install GnoMenu like discribed above, then go to your AWN preferences and add it in the applets section
If you wish to install the AWN applet in another directory plaese use the AWNPREFIX in the makefile


-------------------------------
2.2.3 Cairo-Dock applet install
-------------------------------

Just install GnoMenu like discribed above, then go to your Cairo-Dock preferences, activate the dbus plugin, restart the dock, and add it in the applets section.
If you wish to install the Cairo-Dock applet in another directory plaese use the CAIRODOCKPREFIX in the makefile


-------------------------
2.2.4 Xfce applet install
-------------------------

Just install GnoMenu like discribed above, right click on the xfce-panel, add to panel (make shure xfapplet is installed) and select the xfapplet,the select gnomenu.


--------------------
2.2.5 64 bit install
--------------------

In order to install gnomenu on 64 bit systems you have to manually edit some files

To convert gnomenu to 64 bit operation. I use the following, which works
for me and does not give any error message:-

    1. Open gnomenu->Makefile then, change all '/lib' text with
       '/lib64'
    2. Repeat for 'setup.py'
    3. Finally open gnomenu->src and rename folder 'lib' to lib64

Thanks to Collin Mills


---------------------------
2.2.6 Plasma Applet install
---------------------------

Just install GnoMenu normally, with sudo make install


---------------------------
2.2.6 Docky helper / Applet install
---------------------------

1. Just install GnoMenu normally, with sudo make install
2. Activate the GnoMenu helper in Docky menu
3. Restart Docky


--------------
2.3 Uninstall:
--------------

sudo make uninstall


--------------------------
2.4 Installing new themes:
--------------------------


To install themes only use the GnoMenu configuration window (right click 'Preferences')

WARNING :
Do not copy them directly to the Themes directory
If you install themes that are not installable your menu will crash...


------------------------
2.5 Configuring GnoMenu:
------------------------


With the release of GnoMenu 2.0 there is a expanded preferences interface that greatly enhances the user options and implements the most requested features. Though not all requested features have been implemented the number of expanded options is increased significantly. This new design also makes interface compatible with Netbooks and small screen displays while still being friendly with large screen systems, both standard and widescreen.

GnoMenu uses four different theme file types to allow the user to create the style they wish to achieve.

1. Menu – This is the main theme for GnoMenu. The Menu Theme determines not only how GnoMenu looks, but how it functions as well.
 
2. Panel Button – The Panel Button has no impact on how GnoMenu functions. It simply allows the user to select how the button that opens the GnoMenu interface looks. Currently the only other two known Gnome Menu systems that allow this, without directly manipulating specific files, are Advanced Gnome Menu and Gnome Vista Menu.

3. Icons – Again this theme has no impact on GnoMenu's functions, it simply selects the default icon theme used by GnoMenu. The Menu Panels always use the system Icon theme. GnoMenu2 adds the ability to allow the Menu Theme to utilize System Icons instead of the built in or selected GnoMenu Icon theme. Not all GnoMenu Menu Themes use this function and regardless of what Icon theme you select the look of that particular theme will not change.

4. Sounds - GnoMenu has the ability to use sounds.

GnoMenu has many new user settable options:

Settings:

1. Bind keyboard Super L – Tells GnoMenu whether to use the Super L (Windows Hot) Key or not.

2. Show Internet and Email Buttons – Tells GnoMenu to show the Internet and Email Icons at the top of the Program List.

3. Use GTK Theme Colors in Program List – This feature was enabled due to issues with with dark themes in previous versions of GnoMenu. When checked GnoMenu will comply to the current system color settings.

4. Use system icons instead of theme icons - The theme must support this option for it to work. This is done to allow themers to keep a consistent theme look if desired. Though most themes in the GnoMenu2 series should support this not all will.

5. Tab Selection on Mouse Hover – Only affects tab styled menus and is simply is what it says. Place the pointer over a tab and it will be automatically selected.

6. Show thumbnails in recent items when available - New feature developed for GnoMenu2. Allows the menu to display thumbnails of recent files. This especially helpful with graphics.

7. Show tooltips in Progam List - Tooltips are new for the GnoMenu2 series and by default it will show tooltips for Tabs and Buttons but if you wish to also have tooltips show in the menu then turn on this option.

8. Icon Size in Program List – This is to allow GnoMenu to comply with accessibility standards so people can make GnoMenu easier to work with.

9. Number of Items in Recent Items List – Tells GnoMenu how many recently used items should be shown in the history list.

10. Program list type: There are four selectable options;

Listview - The current GnoMenu default

Buttons Expanded - The original list style

Buttons Fixed - The original style but with the button height fix to keep a consistent button size

Cairo - (experimental) This option is not fully functional at this time though its a good way to see what is slated for the future of GnoMenu development.

11. Tab hover effect - There are six options for when the mouse hovers over a tab:

None - Use no tab effects

Grow - Makes the tab icon slightly larger (default)

Black and White - Desaturates the color from the icon

Blur - Cause the icon to become blurry

Glow - Draws a yellow glow effect around the icon (Not recommended for dark themes)

Saturate - Intensifies the principal color of the icon

Built in Commands:

GnoMenu now allows the user to select what programs (as well as the modifiers) to use for its built in command set. The selected default programs are the most commonly used by Gnome end users, or are selected to coincide with certain themes included with GnoMenu.

The built in Command Set simply determines what programs are used when certain Icons and Buttons are selected by the user. Users should take great caution when making changes. Improperly formated commands can, and will, make that particular function unusable until corrected.

The following commands should never be changed:

Restart
Suspend
Hibernate
Shutdown

GnoMenu has incorporated its own set of programs to handle these functions due to changes in Gnome. Changing these commands will cause undesired results in tab based menu designs.

The About Tab is Information and links for GnoMenu.


-------------------------
3.0 Known GnoMenu Issues:
-------------------------

GnoMenu like any other application has Bugs.
You can report Bugs here: https://launchpad.net/gnomenu

----------------------------
4.0 Creating GnoMenu Themes:
----------------------------

------------------
4.1 Button Themes:
------------------

Panel Buttons are fairly simple. The Button Theme consists of three working PNG files and one preview PNG file. One PNG is for the for the normal state. The second is for when the mouse is hovering over the button and the last one is for when the button is pressed. The preview PNG is used to show how the button looks in the Theme Preferences Selection.
The XML file format for Button Themes is as follows:

<?xml version="1.0" ?>
<content type="Button">
<ContentData Name="VAX" Author="Shaun Marolf" Copyright="Vaxxipooh"/>
<theme Top="0" id="HasTop">
	<Background Image="start-here.png" ImagePressed="start-here-depressed.png" ImageHover="start-here-glow.png"/>
</theme>
</content>

Button themes tend to use varying sizes (*Need to change this to a uniform size) but all are in png format.

Required Buttons are;

start_here (normal)
start_here_depressed (pressed)
start_here_glow (hover)
themepreview (For the preferences dialog to show how the button set looks)

If the button theme has a top piece then the following graphics are also required;

start_here_top
start_here_top_depressed
start_here_top_glow


----------------
4.2 Icon Themes:
----------------


Icon Themes are pretty simple. They are nothing more than selected Icons for display in the Menu Theme. The icons PNG files.

The XML file format is as follows:

<?xml version="1.0" ?>
<content type="Icon">
<theme>
<ContentData Name="Icon Theme name" Author="Icon Theme Creator" Copyright="License or Copyright Holder"/>
</theme>
</content>

Icons should be in png format.
Icon names used are;

applications-accessories.png
applications-games.png
applications-internet.png
applications-other.png
computer.png
document-open-recent.png
emblem-favorite.png
emblem-package.png
evolution.png
folder-documents.png
folder-home.png
folder-images.png
folder-music.png
folder-videos.png
gnome-control-center.png
gnome-help.png
gnome-network-properties.png
gtk-missing-image.png
gtk-network.png
search.png
system-shutdown.png
themedata.xml
themepreview.png
web-browser.png

The theme installer automaticly updates old theme names to new ones,but since new themes uses more icons then before some of the themes need to be manually updated.

If the Icons are not in the Icon theme GnoMenu will use the current user selected icons.



-----------------
4.3 Sound Themes:
-----------------


<?xml version="1.0" ?>
<content type="Sound">
<theme>
<ContentData Name="Default" Author="Canonical" Copyright="GPL"/>
</theme>
</content>

The above is the XML code for sound themes. Required sound files for sound themes are:

button-pressed.ogg
hide-menu.ogg
show-menu.ogg
tab-pressed.ogg



----------------
4.4 Menu Themes:
----------------


Creation of a Menu Theme requires a basic understanding of XML code and formatting.

<?xml version="1.0" ?>
<content type="Menu">
<ContentData Name="GnoMenu default" Author="Helder Fraga" Version="1.0" Copyright="GPL"/>

The above is the header information file. Never change the xml version

Content type informs GnoMenu this is a menu theme.

ContentData gives base information about the theme:

	Name="name of the theme"
	Author="name of the theme creator"
	Version ="version number of the theme"
	Copyright="copyright license the theme is being released under"

# If only one theme type available then specify color='All'
<theme color="All" color_lang="All" colorvalue="#ffffff">
	<Background Image="startmenu.png"/>
	

The above tells GnoMenu what the name of the main image file is for the menu frame.

	<IconSettings X="16" Y="13" Width="66" Height="58" InsetX="6" InsetY="6" InsetWidth="44" InsetHeight="44"/>

The above tells GnoMenu where to place the user image frame, what size it is and the inset size of the frame to properly scale the user image to fit. This must be included in the XML code or it will not work. If your theme is not going to have a user image frame then use the following code:

<IconSettings X="0" Y="0" Width="0" Height="0" InsetX="0" InsetY="0" InsetWidth="0" InsetHeight="0"/>

GnoMenu always uses the file "user-image-frame.png" for the user image frame.

	<SearchBarSettings  X="110" Y="40" Width="260" Height="20" Widget="gtk"/>

Tells GnoMenu the coordinates of the Search bar, size and if desired what search widget to use.

	<ProgramListSettings X="91" Y="80" Width="274" Height="371" OnlyShowRecentApps="0" OnlyShowFavs="0"/>

This is the center point of the menu. This is the main display. Dependent on the tab or button selected by the user it shows the program, file or options list the user can then select from. If OnlyShowRecentApps="1" it will show recentapps as a default instead of application, same goes for OnlyShowFavs="1".

	<Capabilities HasSearch="1" HasIcon="1" HasFadeTransition="1"/>\

Tells GnoMenu what features to utilize, simple on off functions, where 0=off and 1=on. Even though you must have the IconsSettings line in the code the setting 'HasIcon="0"' should be set if its not going to be used.

	<Label Name="Username"	Markup="&lt;span foreground='#dbdbdb' font_desc='Sui Generis 12' stretch='semicondensed'&gt;[TEXT]&lt;/span&gt;" LabelX="110" LabelY="18" Command="whoami"/>

Labels allow the themer to display extra information in the theme. The above label shows the user name.

<Label Name="System"	Markup="&lt;span foreground='#FFFFFF' font_desc='Sans Bold 10' stretch='normal'&gt;IP :  [TEXT]&lt;/span&gt;" LabelX="20" LabelY="130" Command="/sbin/ip route | grep 'src ' | cut -d c -f3 "/>

The above label shows what IP Address is assigned to the computer.

<Label Name="Username"	Markup="&lt;span foreground='#dbdbdb' font_desc='Sans Bold 30' stretch='semicondensed'&gt;[TEXT]&lt;/span&gt;" LabelX="105" LabelY="15" Command=" date +%H:%M"/>

The above label shows the system time. NOTE: This label will not update until the menu is opened again. It only shows the current time that the menu was called up from the launch (start) button. 

	<Label Name="System"	Markup="&lt;span foreground='#dbdbdb' font_desc='Sans Bold 20' stretch='semicondensed'&gt;[TEXT]&lt;/span&gt;" LabelX="20" LabelY="90" Command="lsb_release -d | sed -e 's/.*: //' | awk '{print $2,$3}'"/>

The above label will show the Distribution and Version of Linux being used.

	<Tab Name="Favorites"	Markup="&lt;span foreground='#000000' font_desc='Sans 6' stretch='semicondensed'&gt;Favorites&lt;/span&gt;"		TextX="15" TextY="60" Image="" ImageSel="m_tab.png" TabIcon="m_favorites.png" TabX="18" TabY="78" SubMenu="1" Command="7" CloseMenu="0" Icon="m_favorites.png" AddBackButton='0'/>

GnoMenu now has the ability to justify text on tabs, buttons and labels. By adding the following to the XML code line for them:

TextAlignment="X"

Where X =:

0 - Left justification
1 - Center justification
2 - Right justification

	Tabs were first introduced to GnoMenu during the 1.9.xx development phase and have expanded GnoMenu's options, abilities and design features greatly. The main things a themer needs to be aware of when utilizing tabs is how to make them function correctly. These are controlled by the SubMenu, Command, CloseMenu and AddBackButton options. All are a simple on off function with the exception of the command. The command action table is as follows:

Command Number		Function

1			Opens Applications Menu
2			Opens a list of recently used applications
3			Opens Auxiliary Functions
4			Opens a list of recently accessed files
7			Opens Favorites Menu
8			Opens Places Menu (GTK Favorites)
9			Opens the shut down, logout and lock options menu
10			Opens The default Web Browser's list of bookmarks


Buttons are like tabs in many respects but act differently. When using buttons the "Command=" line needs to list the actual command the themer wishes to use.

The first tab code listed in the XML code will be the default tab (The one GnoMenu highlights when the menu is first opened.) Themers need to be aware of this so that they can make sure that they select the correct tab they want for the default.

NOTE: Due to GTK limitations recently used applications is based on the file mime type and will list the default program that the system uses for the file type and not the actual program. This is a known issue that is being worked out. Recent Apps is a new GnoMenu2 function and is still under development.

<Button Name="Control Panel" Markup="" TextX="0" TextY="0" Image="m_button.png" ButtonIcon="m_controlpanel.png" ButtonIconSel="" ButtonX="321" ButtonY="275" SubMenu="0" Command="Control Panel" CloseMenu="1" Icon=""/>


Icon translation matrix: This is now deprecated in GnoMenu. See section 4.2 for further information.


