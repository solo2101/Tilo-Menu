# GnoMenu 2.9.1 source-first port audit

Reference: `gnomenu-2.9.1.tar.gz` from Launchpad, `gnomenu/src/lib/gnomenu/`.
Scope: Python 3 + GTK 3 on Fedora MATE. The original artwork and `themedata.xml` are the interface contract.

## Decision

**Port existing behavior, not a different menu with similar artwork.**
Keep the working Tilo-Menu GTK3 implementation as a regression baseline.
Port one original subsystem at a time, using the old classes as the behavioral specification.
Do **not** bulk-convert every Python 2 source file, replace the working menu wholesale, or edit third-party XML/artwork.

## Source inventory

| Original source | Original purpose | Current counterpart | Assessment |
| --- | --- | --- | --- |
| `Globals.py` (618 lines), `backend.py` (146) | Theme XML, configuration, applet and command settings | `themes/parser.py`, `themes/models.py`, `preferences.py`, `config/*` | Menu XML works; not all legacy attributes/options or separate Button/Icon/Sound themes are implemented. Modern JSON settings and duplicate config paths need consolidation. |
| `Menu_Main.py` (763) | Main window, geometry, hover timers, commands, keyboard/focus, sound | `menu.py` | Basic window and artwork are working; behavior is incomplete. |
| `Menu_Widgets.py` (3,118) | `MenuButton`, `MenuTab`, `ImageFrame`, search bars, four program-list types | `themes/renderer.py`, `search.py`, `app_list.py`, `avatar.py` | Recreated on GTK3; needs behavioral comparison for each widget and XML state. |
| `Menu_Widgets1.py` (2,710) | Older alternative widgets implementation | No direct counterpart | Do not port both. Refer to the newer `Menu_Widgets.py` used by `Menu_Main.py`. |
| `MenuParser.py` (186), `Menu_Items.py` (781) | Nested XDG menus, special pages, search, favorites, recent items, context menus | `applications.py`, `menu.py` | Major functional gap: current Gio.AppInfo list is flat, navigation and special commands are not the original model. |
| `Launcher.py` (86), `IconFactory.py` (137), `utils.py` (239) | Launching and icon resolution | `applications.py`, `icons.py`, MATE command allowlist | Modern replacements work for basic operations; original special actions need a mapping. |
| `GnoMenu-Settings.py` (959) | Themes, Preferences, Commands, About, installer, per-theme selection | `preferences.py`, `themes/importer.py` | Visual structure and secure Menu archive import work. Button, Icon, Sound and several preferences do not yet work. |
| `GnoMenu.py` (499), `Panel_Top.py` (154) | GNOME 2 applet button, panel sizing/placement, top/bottom support | None | Requires MATE-specific integration, not direct `gnomeapplet` imports. |
| `GnoMenu_rewrite.py` (588) | Alternative applet revision | No direct counterpart | Reference only; avoid porting two applets. |
| `bookmarks.py` (1,098), `zg.py`, session and auxiliary modules | Bookmarks, history, system integration | Mostly absent | Port only the supported behaviors using modern MATE/Gio integrations. |

The main original `lib/gnomenu` package contains roughly 13,500 Python source lines, including alternative or legacy implementations. Line count is not the amount we should copy.

## Highest-priority behavior differences

1. **XML actions**: Original `Menu_Main.Button_click` and `Tab_click` dispatch by XML `Command`, `SubMenu`, `CloseMenu`. Hover handling also uses `ExecOnHover` and 300ms timers. Current Tilo-Menu mostly maps visible labels to actions. Restore XML semantics with an allowlisted MATE action adapter, not arbitrary shell execution.
2. **Menu data/navigation**: Original `XDGMenu` has nested folders, Back, Places, System, Favorites, Recently Used, Recent Applications, bookmarks, searching, and context actions. Current `Gio.AppInfo.get_all()` approach is flat and only partially covers these.
3. **Widget geometry and states**: Original `MenuButton` and `MenuTab` define normal/selected/hover image rules, icon effects, label alignment and active state. Keep original behavior and XML positions. Use the existing GTK3/Cairo rendering rather than porting removed GTK2 GDK drawing APIs.
4. **Window lifecycle**: Original menu handles focus loss, placement against panel edges, keyboard navigation, pop-up visibility, hover delay and optional sound. Standalone GTK3 preview lacks several behaviors.
5. **Preferences**: Original has Menu/Button/Icon/Sound theme choices, program-list modes, icon sizing, hover effects, keyboard binding, commands, tooltips, and optional sound. Current settings covers only a subset; don't pretend unsupported controls work.
6. **Panel**: `gnomeapplet.Applet` and GConf are obsolete. Use the current MATE panel applet architecture, not the original GNOME 2 applet module.

## Modernization boundary

Preserve:
- XML and artwork bytes; metadata, names, flags, variants, geometry.
- User-visible workflow, enabled features, selection and hover behavior.
- Separate Menu, Button, Icon and Sound concepts.
- Credit and GPL notices from original source.

Replace:
- Python 2 syntax and removed modules (`commands`, static `gtk`, `pygtk`, `gobject`, `gio`).
- GTK2 expose events/colormap/pixmap masking with GTK3 `draw`, Cairo, RGBA visual.
- GConf / `.gnomenu` settings with explicit modern storage and optional one-time migration.
- GNOME 2 panel API with an independently tested MATE applet.
- Obsolete GNOME shell commands with safe MATE equivalents.
- Unsafe original installer extraction; retain the current safe archive importer.

**Do not rely on `gi.pygtkcompat`.** Recent PyGObject releases removed it. Port calls to native `gi.repository` APIs.
See https://pygobject.gnome.org/devguide/introspection_porting.html and https://docs.gtk.org/gtk3/migrating-2to3.html .

## Implementation order and gates

| Stage | Output | Acceptance gate |
| --- | --- | --- |
| 0. Preserve baseline | This audit, tests, GPL compliance check, XML behavior fixture list | All 15 original themes + DarkCandy still open unchanged |
| 1. Core/menu model | Port `MenuParser`, `Menu_Items` behavior into a modern XDG/Gio adapter and XML action dispatcher | Favorites, nested categories, Back, special tabs/buttons, search, recent pages, close-on-click, keyboard actions |
| 2. Widget fidelity | Port `MenuButton`, `MenuTab`, `MenuLabel`, `ImageFrame`, search logic from `Menu_Widgets.py` using GTK3/Cairo | Normal/selected/hover states, image geometry and per-theme flags match original behavior |
| 3. Settings parity | Original settings operations, Button/Icon theme support, sound behavior where available, settings migration | Each visible control works or is explicitly unavailable; safe install/uninstall, no third-party XML changes |
| 4. MATE panel | Native MATE panel button and menu placement, configurable icon/theme, panel orientation | Add/remove panel applet, open/close menu, monitor placement, stay hidden on focus loss |
| 5. Regression | Automated behavior tests and Fedora MATE screenshots for 15 bundled themes + DarkCandy | No regression in transparency, startup, scrolling, search, clicks or avatar |

Do not delete working modern code until its replacement passes functional and visual tests. Keep the refactor in small reviewable commits with original-source method references.

## Rough scope (engineering effort, not a delivery promise)

- Source-based standalone core and widget parity: **60–110 hours**.
- Missing menu features, settings and theme categories: **40–80 hours**.
- Native MATE panel applet plus integration: **40–80 hours**.
- End-to-end regression and packaging: **20–40 hours**.
- **Total full-scope estimate: roughly 160–310 hours (4–8 full-time workweeks).**

An incremental, original-source-based standalone menu without full panel/settings parity is a smaller initial milestone. Estimates depend on how much exact GTK2 visual behavior is required and the supported MATE panel API.

## Licensing

The original source headers declare **GNU GPL v3 or later**. The current Tilo-Menu repository has no top-level LICENSE file. Before copying original implementation code into this repository, add the appropriate GPL license text and retain per-file copyright/attribution notices. Preserve third-party theme authors' credits. This is a prerequisite for a direct source port.
