"""Data structures for GnoMenu 2.9.1 XML menu themes."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ThemeElement:
    """One original XML element, retaining all attributes and their spelling."""

    tag: str
    attributes: dict[str, str]

    def integer(self, key: str, default: int = 0) -> int:
        return int(self.attributes.get(key, default))


@dataclass(frozen=True)
class MenuTheme:
    directory: Path
    metadata: dict[str, str]
    color: str
    color_value: str
    background: str
    width: int
    height: int
    icon: ThemeElement | None
    search: ThemeElement
    program_list: ThemeElement
    capabilities: ThemeElement
    buttons: tuple[ThemeElement, ...] = field(default_factory=tuple)
    tabs: tuple[ThemeElement, ...] = field(default_factory=tuple)
    labels: tuple[ThemeElement, ...] = field(default_factory=tuple)
    images: tuple[ThemeElement, ...] = field(default_factory=tuple)
    flipped: bool = False
