"""Parse original GnoMenu 2.9.1 Menu/themedata.xml files without GTK.

Coordinates are preserved as authored; the MATE UI handles orientation.
Theme commands and Python modules are never executed while parsing.
"""

from pathlib import Path
import xml.etree.ElementTree as ET

from ArchiveThemeModels import MenuTheme, ThemeElement


def _element(node: ET.Element) -> ThemeElement:
    return ThemeElement(node.tag, dict(node.attrib))


def _required(parent: ET.Element, name: str) -> ET.Element:
    node = parent.find(name)
    if node is None:
        raise ValueError(f"Missing required theme element: {name}")
    return node


def load_menu_theme(directory: str | Path, color: str = "white") -> MenuTheme:
    """Load one original XML theme and select its matching color variant."""
    directory = Path(directory)
    root = ET.parse(directory / "themedata.xml").getroot()
    if root.tag != "content" or root.get("type") != "Menu":
        raise ValueError("Expected a GnoMenu Menu theme")

    variants = root.findall("theme")
    selected = next(
        (node for node in variants if node.get("color") in (color, "All")),
        None,
    )
    if selected is None and variants:
        selected = variants[0]
    if selected is None:
        raise ValueError("Theme contains no color variants")

    background = _required(selected, "Background").attrib["Image"]
    dimensions = _required(selected, "WindowDimensions")
    metadata = root.find("ContentData")
    icon = selected.find("IconSettings")

    return MenuTheme(
        directory=directory,
        metadata=dict(metadata.attrib) if metadata is not None else {},
        color=selected.get("color", ""),
        color_value=selected.get("colorvalue", ""),
        background=background,
        width=int(dimensions.attrib["Width"]),
        height=int(dimensions.attrib["Height"]),
        icon=_element(icon) if icon is not None else None,
        search=_element(_required(selected, "SearchBarSettings")),
        program_list=_element(_required(selected, "ProgramListSettings")),
        capabilities=_element(_required(selected, "Capabilities")),
        buttons=tuple(map(_element, selected.findall("Button"))),
        tabs=tuple(map(_element, selected.findall("Tab"))),
        labels=tuple(map(_element, selected.findall("Label"))),
        images=tuple(map(_element, selected.findall("Image"))),
    )
