#!/usr/bin/env python3
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

TARGETS = [
    ("C", "source.c", "c", "file_type_c"),
    ("C++", "source.c++", "cpp", "file_type_c++"),
    ("C++ Header", "source.c++.header", "hpp", "file_type_cppheader"),
    ("C#", "source.cs", "cs", "file_type_csharp"),
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


def render_svgs(jobs):
    renderer = Path(__file__).with_name("render-mizu-svg.swift")
    arguments = ["swift", str(renderer)]
    for svg_path, size, output_path in jobs:
        arguments.extend((str(svg_path), str(size), str(output_path)))
    subprocess.run(arguments, check=True)


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
            generated = []
            jobs = []

            for label, scope, extension, icon in TARGETS:
                definition_id = str(extensions[extension])
                icon_path = definitions[definition_id]["iconPath"]
                archive.extract(f"extension/{icon_path}", tmp_dir)
                svg_path = tmp_dir / "extension" / icon_path

                rendered = tmp_dir / f"{icon}.png"
                rendered_2x = tmp_dir / f"{icon}@2x.png"
                jobs.extend(((svg_path, 16, rendered), (svg_path, 32, rendered_2x)))
                generated.append((label, scope, icon, rendered, rendered_2x))

            render_svgs(jobs)

            for label, scope, icon, rendered, rendered_2x in generated:
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
