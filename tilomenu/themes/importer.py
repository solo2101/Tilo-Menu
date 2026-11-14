"""Import original GnoMenu Menu theme archives without changing their contents.

Accepts TAR/TAR.* and ZIP packages, including nested Themes/Menu folders.
Only <content type="Menu"> packages are installed in the Menu theme store.
Never execute theme code or extract unsafe links, absolute paths or traversals.
"""
import os
import re
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

from .parser import load_menu_theme


MAX_FILES = 5000
MAX_BYTES = 125 * 1024 * 1024
MAX_SINGLE_FILE = 25 * 1024 * 1024


class ThemeImportError(ValueError):
    """The selected archive is invalid or has no supported GnoMenu Menu theme."""


def _member_path(name):
    if not name or "\\" in name or name.startswith("/"):
        raise ThemeImportError("Unsafe archive path")
    if ".." in name.split("/") or "\x00" in name:
        raise ThemeImportError("Archive contains a parent-directory path")
    parts = PurePosixPath(name).parts
    if not parts or ":" in parts[0]:
        raise ThemeImportError("Unsafe archive path")
    return Path(*parts)


def _unpack(archive, staging):
    count = 0
    total = 0
    seen = set()

    def put(name, size, stream):
        nonlocal count, total
        relative = _member_path(name)
        count += 1
        total += size
        if (count > MAX_FILES or size > MAX_SINGLE_FILE
                or total > MAX_BYTES or size < 0):
            raise ThemeImportError("Theme archive exceeds file limits")
        if relative in seen:
            raise ThemeImportError("Duplicate archive filename: " + str(relative))
        seen.add(relative)
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as output:
            remaining = size
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise ThemeImportError("Truncated archive member")
                output.write(chunk)
                remaining -= len(chunk)

    if tarfile.is_tarfile(archive):
        with tarfile.open(archive, "r:*") as package:
            for member in package:
                _member_path(member.name)
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ThemeImportError("Archive contains a link or special file")
                source = package.extractfile(member)
                if source is None:
                    raise ThemeImportError("Cannot read a theme archive member")
                with source:
                    put(member.name, member.size, source)
    elif zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as package:
            for info in package.infolist():
                _member_path(info.filename)
                if info.is_dir():
                    continue
                # Reject UNIX symlinks, not only TAR links.
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ThemeImportError("Archive contains a symbolic link")
                with package.open(info) as source:
                    put(info.filename, info.file_size, source)
    else:
        raise ThemeImportError("Expected a .tar, compressed .tar, or .zip archive")


def _name(text):
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._-")
    if not value:
        raise ThemeImportError("Theme has no usable name")
    return value[:90]


def _menu_directories(staging):
    candidates = []
    for xml in staging.rglob("themedata.xml"):
        if not xml.is_file():
            continue
        try:
            root = ET.parse(xml).getroot()
        except ET.ParseError as error:
            raise ThemeImportError(f"Broken theme XML: {error}") from error
        if root.tag != "content" or root.get("type") != "Menu":
            continue
        directory = xml.parent
        try:
            theme = load_menu_theme(directory)
        except (OSError, ValueError, KeyError, ET.ParseError) as error:
            raise ThemeImportError(f"Unsupported Menu theme: {error}") from error
        # An XML theme without its original background will not render.
        if not (directory / theme.background).is_file():
            raise ThemeImportError(f"Missing original artwork: {theme.background}")
        candidates.append((directory, theme))
    # An archive can contain Icon and Button themes as well. Ignore those,
    # rather than putting them into Menu and corrupting the theme selector.
    return candidates


def import_theme_archive(archive, destination):
    """Extract validated Menu themes into destination, keeping artwork intact.

    Does not select a theme or overwrite installed themes. Returns new names.
    """
    archive = Path(archive).expanduser()
    destination = Path(destination).expanduser()
    if not archive.is_file():
        raise ThemeImportError(f"Theme archive not found: {archive}")
    destination.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        with tempfile.TemporaryDirectory(prefix=".tilo-import-", dir=destination) as temp:
            staged = Path(temp) / "contents"
            staged.mkdir()
            try:
                _unpack(archive, staged)
            except (tarfile.TarError, zipfile.BadZipFile, EOFError, OSError) as error:
                raise ThemeImportError(f"Unable to read archive: {error}") from error
            candidates = _menu_directories(staged)
            if not candidates:
                raise ThemeImportError("No GnoMenu Menu/themedata.xml found in archive")
            # Validate all candidates before copying any into the real store.
            plans = []
            reserved = set()
            for directory, theme in candidates:
                default = theme.metadata.get("Name", archive.stem) if directory == staged else directory.name
                base_name = _name(default)
                choice = base_name
                version = 2
                while (destination / choice).exists() or choice in reserved:
                    choice = f"{base_name}-{version}"
                    version += 1
                reserved.add(choice)
                plans.append((directory, choice))
            for directory, choice in plans:
                target = destination / choice
                shutil.copytree(directory, target)
                created.append(target)
                # Confirm the complete extracted theme still parses in place.
                load_menu_theme(target)
        return [path.name for path in created]
    except Exception:
        # A failed import must not leave partially installed theme directories.
        for path in created:
            shutil.rmtree(path, ignore_errors=True)
        raise
