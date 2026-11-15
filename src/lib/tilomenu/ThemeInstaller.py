"""User theme installation and lookup for original TiloMenu theme archives.

Keep the original themedata.xml format. Never extract archive paths outside
the per-user theme directory or invoke a privileged shell.
"""
from pathlib import Path
import os
import shutil
import tarfile
import tempfile
import xml.etree.ElementTree as ET

KINDS = ("Menu", "Button", "Icon", "Sound")
USER_ROOT = Path.home() / ".local" / "share" / "tilomenu" / "Themes"


def theme_root():
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "tilomenu" / "Themes"


def theme_path(kind, name, system_root):
    if kind not in KINDS or not name or Path(name).name != name:
        raise ValueError("Invalid theme name or type")
    for root in (theme_root(), Path(system_root)):
        path = root / kind / name
        if path.is_dir() and (path / "themedata.xml").is_file():
            return str(path) + os.sep
    return str(Path(system_root) / kind / name) + os.sep


def installed_themes(kind, system_root):
    if kind not in KINDS:
        raise ValueError("Unsupported theme type")
    names = set()
    for root in (Path(system_root), theme_root()):
        folder = root / kind
        if folder.is_dir():
            names.update(p.name for p in folder.iterdir()
                         if p.is_dir() and not p.is_symlink() and (p / "themedata.xml").is_file())
    return sorted(names, key=str.casefold)


def _metadata(path):
    root = ET.parse(path).getroot()
    content = root if root.tag == "content" else root.find(".//content")
    kind = content.get("type") if content is not None else None
    if kind not in KINDS:
        raise ValueError("Theme metadata has no recognized content type")
    return kind


def install_archive(filename):
    """Install one original tar theme, returning (kind, name).

    Reject links and traversal. Extract only regular files and directories,
    with a size cap to avoid archive bombs.
    """
    with tarfile.open(filename, "r:*") as archive:
        members = archive.getmembers()
        if len(members) > 5000 or sum(m.size for m in members) > 128 * 1024 * 1024:
            raise ValueError("Theme archive is too large")
        files = []
        tops = set()
        for member in members:
            path = Path(member.name)
            parts = path.parts
            if (not parts or path.is_absolute() or
                    any(part in ("..", "") for part in parts) or
                    not (member.isfile() or member.isdir())):
                raise ValueError("Theme archive contains unsafe entries")
            if parts[0] == ".":
                continue
            tops.add(parts[0])
            files.append((member, parts))
        if len(tops) != 1:
            raise ValueError("Theme archive must contain a single theme folder")
        name = next(iter(tops))
        if name in (".", ".."):
            raise ValueError("Invalid theme folder")
        with tempfile.TemporaryDirectory(prefix="tilomenu-theme-") as work:
            root = Path(work)
            for member, parts in files:
                target = root.joinpath(*parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = archive.extractfile(member)
                    if source is None:
                        raise ValueError("Missing archive data")
                    with source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
            source_dir = root / name
            metadata = source_dir / "themedata.xml"
            if not metadata.is_file():
                raise ValueError("Theme package is missing themedata.xml")
            kind = _metadata(metadata)
            dest = theme_root() / kind / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                if not dest.is_dir() or dest.is_symlink():
                    raise ValueError("Theme destination is not a directory")
                shutil.rmtree(dest)
            shutil.copytree(source_dir, dest)
            return kind, name


def uninstall_user_theme(kind, name):
    if kind not in KINDS or not name or Path(name).name != name:
        raise ValueError("Invalid theme")
    path = theme_root() / kind / name
    if path.is_symlink():
        raise ValueError("Refusing to remove a symlink")
    if not path.is_dir():
        raise ValueError("Bundled themes cannot be removed here")
    shutil.rmtree(path)
