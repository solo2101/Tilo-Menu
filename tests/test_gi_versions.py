"""Ensure GI namespace versions are selected before repository imports.

This static check also covers direct imports that bypass the applet launcher.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMESPACES = {
    "Gtk": "3.0",
    "Gdk": "3.0",
    "GdkPixbuf": "2.0",
    "MatePanelApplet": "4.0",
}

failures = []
files = sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "tests").rglob("*.py"))
for path in files:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    versions = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if not (isinstance(node.func.value, ast.Name) and
                    node.func.value.id == "gi" and node.func.attr == "require_version"):
                continue
            if len(node.args) >= 2 and all(isinstance(x, ast.Constant) for x in node.args[:2]):
                versions.setdefault(str(node.args[0].value), []).append(
                    (str(node.args[1].value), node.lineno))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != "gi.repository":
            continue
        for name in node.names:
            namespace = name.name
            if namespace not in NAMESPACES:
                continue
            expected = NAMESPACES[namespace]
            if not any(version == expected and line < node.lineno
                       for version, line in versions.get(namespace, [])):
                failures.append(f"{path.relative_to(ROOT)}:{node.lineno}: "
                                f"missing gi.require_version({namespace!r}, {expected!r})")

if failures:
    raise SystemExit("\n".join(failures))
print(f"PASS: pinned GI imports in {len(files)} Python files")
