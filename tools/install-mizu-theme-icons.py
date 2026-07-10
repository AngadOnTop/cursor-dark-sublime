#!/usr/bin/env python3
from collections import deque
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from PIL import Image


TARGETS = [
    ("C", "source.c", "c", "file_type_c"),
    ("C++", "source.c++", "cpp", "file_type_c++"),
    ("C++ Header", "source.c++.header", "hpp", "file_type_cppheader"),
    ("CMake", "source.cmake", "cmake", "file_type_cmake"),
    ("CSS", "source.css", "css", "file_type_css"),
    ("Go", "source.go", "go", "file_type_go"),
    ("HTML", "text.html", "html", "file_type_html"),
    ("Java", "source.java", "java", "file_type_java"),
    ("JavaScript", "source.js", "js", "file_type_js"),
    ("JSX", "source.jsx", "jsx", "file_type_jsx"),
    ("JSON", "source.json", "json", "file_type_json"),
    ("Markdown", "text.html.markdown", "md", "file_type_markdown"),
    ("Python", "source.python, text.plain.python", "py", "file_type_python"),
    ("Rust", "source.rust", "rs", "file_type_rust"),
    ("Shell", "source.shell", "sh", "file_type_shell"),
    ("TypeScript", "source.js.typescript, source.ts", "ts", "file_type_typescript"),
    ("TSX", "source.tsx", "tsx", "file_type_tsx"),
    ("YAML", "source.yaml", "yaml", "file_type_yaml"),
]


def active_theme(user_dir):
    settings = user_dir / "Preferences.sublime-settings"
    text = settings.read_text()
    match = re.search(r'"theme"\s*:\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError(f"No theme key found in {settings}")
    return match.group(1)


def theme_folder_name(theme):
    if theme == "Default.sublime-theme":
        return "Theme - Default"
    if theme == "Adaptive.sublime-theme":
        return "Theme - Adaptive"
    return theme.removesuffix(".sublime-theme")


def is_background(pixel):
    r, g, b, a = pixel
    return a != 0 and r >= 238 and g >= 238 and b >= 238 and max(r, g, b) - min(r, g, b) <= 30


def strip_edge_matte(path):
    image = Image.open(path).convert("RGBA")
    width, height = image.size
    pixels = image.load()
    seen = set()
    queue = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        seen.add((x, y))
        if not is_background(pixels[x, y]):
            continue

        r, g, b, _ = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)
        queue.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))

    image.save(path)


def render_svg(svg_path, size, output_path):
    with tempfile.TemporaryDirectory(prefix="mizu-render-") as tmp:
        tmp_dir = Path(tmp)
        subprocess.run(
            ["qlmanage", "-t", "-s", str(size), "-o", str(tmp_dir), str(svg_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        rendered = tmp_dir / f"{svg_path.name}.png"
        shutil.copyfile(rendered, output_path)
    strip_edge_matte(output_path)


def write_icon_pref(user_dir, label, scope, icon):
    pref_file = user_dir / f"Icon - Mizu {label}.tmPreferences"
    pref_file.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://apple.com">
<plist version="1.0">
<dict>
    <key>scope</key>
    <string>{scope}</string>
    <key>settings</key>
    <dict>
        <key>icon</key>
        <string>{icon}</string>
    </dict>
</dict>
</plist>
"""
    )


def main():
    if len(sys.argv) != 2:
        print("usage: install-mizu-theme-icons.py MIZU_VSIX", file=sys.stderr)
        return 2

    packages_dir = Path.home() / "Library/Application Support/Sublime Text/Packages"
    user_dir = packages_dir / "User"
    theme = active_theme(user_dir)
    theme_dir = packages_dir / theme_folder_name(theme)
    icon_dirs = [theme_dir / "icons", user_dir / "icons"]

    for icon_dir in icon_dirs:
        icon_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mizu-vsix-") as tmp:
        tmp_dir = Path(tmp)
        with zipfile.ZipFile(sys.argv[1]) as archive:
            icon_theme = json.loads(archive.read("extension/icon-theme.json"))
            definitions = icon_theme["iconDefinitions"]
            extensions = icon_theme["fileExtensions"]

            for label, scope, extension, icon in TARGETS:
                definition_id = str(extensions[extension])
                icon_path = definitions[definition_id]["iconPath"]
                archive.extract(f"extension/{icon_path}", tmp_dir)
                svg_path = tmp_dir / "extension" / icon_path

                rendered = tmp_dir / f"{icon}.png"
                rendered_2x = tmp_dir / f"{icon}@2x.png"
                render_svg(svg_path, 16, rendered)
                render_svg(svg_path, 32, rendered_2x)

                for icon_dir in icon_dirs:
                    shutil.copyfile(rendered, icon_dir / rendered.name)
                    shutil.copyfile(rendered_2x, icon_dir / rendered_2x.name)

                write_icon_pref(user_dir, label, scope, icon)

    print(f"Active theme: {theme}")
    print(f"Theme icon directory: {theme_dir / 'icons'}")
    print(f"User icon directory: {user_dir / 'icons'}")
    print(f"Generated {len(TARGETS)} icon mappings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
