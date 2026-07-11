#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path, PurePosixPath
import json
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile


PACKAGE_NAME = "Mizu File Icons"
ICON_PREFIX = "mizu_"
SCALES = ((16, ""), (32, "@2x"), (48, "@3x"))

# A File Icon and Mizu occasionally use different names for the same format.
# Values are Mizu file extensions, file names, or SVG definition stems.
ICON_ALIASES = {
    "adonisjs": "node",
    "ae": "aep",
    "ansible": "yaml",
    "asciidoc": "markdown",
    "authorized_keys": "key",
    "authorizedd_keys": "key",
    "azure": "yaml",
    "biome": "config",
    "blade": "php",
    "blender": "threed",
    "bower": "package",
    "c#": "cs",
    "cabal": "haskell",
    "cad": "threed",
    "cairo": "code",
    "cf": "html",
    "cname": "config",
    "codecov": "yaml",
    "composer": "package.json",
    "coreboot": "boot",
    "cottle": "code",
    "cppheader": "hpp",
    "cython": "python",
    "delphi": "code",
    "diff": "patch",
    "dlang": "d",
    "dotnet": "visualstudio",
    "ejs": "html",
    "email": "mail",
    "fabricengine": "code",
    "fastq": "text",
    "gleam": "code",
    "glyphs": "font",
    "gradle_wrapper": "gradle",
    "graphviz": "dot",
    "gruntfile": "js",
    "gulpfile": "gulp",
    "haxelib": "haxe",
    "http": "text",
    "jq": "json",
    "known_hosts": "key",
    "kotlin_gradle": "kotlin",
    "ksp": "code",
    "liquid": "html",
    "llvm": "config",
    "lsl": "code",
    "maven_wrapper": "maven",
    "maya": "code",
    "mcnp": "code",
    "meson": "config",
    "mint": "code",
    "mp3tag": "audio",
    "mustache": "handlebars",
    "nextjs": "next",
    "nodejs": "node",
    "note": "markdown",
    "nsis": "config",
    "objc": "m",
    "objc++": "cpp",
    "odin": "code",
    "opengl": "shader",
    "parquet": "database",
    "pawn": "code",
    "pcb": "threed",
    "pkl": "config",
    "playlist": "audio",
    "postcss": "css",
    "postscript": "text",
    "protobuf": "code",
    "public_key": "key",
    "puppet": "ruby",
    "purebasic": "visualbasic",
    "reach": "react",
    "registry": "config",
    "restructuredtext": "rst",
    "riot": "react",
    "scheme": "lisp",
    "ssh_config": "config",
    "sshd_config": "config",
    "stata": "stats",
    "stylus": "css",
    "systemverilog": "v",
    "taskfile": "yaml",
    "test_js": "jsTest",
    "test_jsx": "jsTest",
    "test_tsx": "tsTest",
    "test_typescript": "tsTest",
    "tern": "config",
    "textile": "text",
    "toit": "code",
    "twig": "html",
    "typescript": "ts",
    "typst": "text",
    "unreal": "unity",
    "verilog": "v",
    "vhdl": "v",
    "vyper": "python",
    "windicss": "windi",
    "windows": "windowsSandbox",
    "wit": "code",
    "yarn_wrapper": "yarn",
}


def normalized(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def package_paths():
    data_dir = Path.home() / "Library/Application Support/Sublime Text"
    packages_dir = data_dir / "Packages"
    installed_dir = data_dir / "Installed Packages"
    return data_dir, packages_dir, installed_dir


def find_vsix(argument):
    if argument:
        candidates = [Path(argument).expanduser()]
    else:
        downloads = Path.home() / "Downloads"
        candidates = sorted(downloads.glob("*Mizu*.vsix")) + sorted(downloads.glob("*Mizu*.zip"))

    valid = []
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            with zipfile.ZipFile(candidate) as archive:
                names = set(archive.namelist())
                if "extension/icon-theme.json" in names and any(
                    name.startswith("extension/i/") and name.endswith(".svg") for name in names
                ):
                    valid.append(candidate)
        except zipfile.BadZipFile:
            pass
    if not valid:
        raise RuntimeError("No Mizu archive containing extension/icon-theme.json and SVG icons was found")
    return valid[-1]


def find_a_file_icon(installed_dir):
    archive = installed_dir / "A File Icon.sublime-package"
    if not archive.is_file():
        raise RuntimeError("A File Icon is not installed through Package Control")
    return archive


def active_settings(user_dir):
    path = user_dir / "Preferences.sublime-settings"
    text = path.read_text()
    scheme = re.search(r'"color_scheme"\s*:\s*"([^"]+)"', text)
    theme = re.search(r'"theme"\s*:\s*"([^"]+)"', text)
    if not scheme or not theme:
        raise RuntimeError(f"Could not read active theme and color scheme from {path}")
    return path, text, scheme.group(1), theme.group(1)


def definition_lookup(icon_theme):
    definitions = icon_theme["iconDefinitions"]
    by_stem = {}
    for definition_id, definition in definitions.items():
        stem = PurePosixPath(definition["iconPath"]).stem
        by_stem.setdefault(normalized(stem), (str(definition_id), definition["iconPath"]))
    return definitions, by_stem


def resolve_icon_path(icon_name, icon_theme, definitions, by_stem):
    suffix = icon_name.removeprefix("file_type_")
    candidate = ICON_ALIASES.get(suffix, suffix)
    for table_name in ("fileExtensions", "fileNames"):
        table = icon_theme.get(table_name, {})
        if candidate in table:
            return definitions[str(table[candidate])]["iconPath"], None
    match = by_stem.get(normalized(candidate))
    if match:
        return match[1], None
    return definitions[str(icon_theme["file"])]["iconPath"], suffix


def extract_mappings(a_file_icon, icon_theme):
    definitions, by_stem = definition_lookup(icon_theme)
    mappings = []
    fallbacks = []
    with zipfile.ZipFile(a_file_icon) as archive:
        for name in sorted(archive.namelist()):
            if not (name.startswith("preferences/") and name.endswith(".tmPreferences")):
                continue
            preference = plistlib.loads(archive.read(name))
            icon_name = preference.get("settings", {}).get("icon")
            if not icon_name:
                continue
            icon_path, fallback = resolve_icon_path(icon_name, icon_theme, definitions, by_stem)
            if fallback:
                fallbacks.append(fallback)
            preference["settings"]["icon"] = ICON_PREFIX + icon_name
            mappings.append((PurePosixPath(name).name, preference, icon_name, icon_path))
    return mappings, sorted(set(fallbacks))


def render_svgs(jobs):
    renderer = Path(__file__).with_name("render-mizu-svg.swift")
    arguments = ["swift", str(renderer)]
    for svg_path, size, output_path in jobs:
        arguments.extend((str(svg_path), str(size), str(output_path)))
    subprocess.run(arguments, check=True)


def write_preference(path, scope, icon):
    value = {"scope": scope, "settings": {"icon": icon}}
    path.write_bytes(plistlib.dumps(value, fmt=plistlib.FMT_XML, sort_keys=False))


def build_package(staging, vsix, a_file_icon, aliases_dir):
    package_dir = staging / PACKAGE_NAME
    icons_dir = package_dir / "icons"
    preferences_dir = package_dir / "preferences"
    package_aliases_dir = package_dir / "aliases"
    icons_dir.mkdir(parents=True)
    preferences_dir.mkdir()

    with zipfile.ZipFile(vsix) as archive:
        icon_theme = json.loads(archive.read("extension/icon-theme.json"))
        mappings, fallbacks = extract_mappings(a_file_icon, icon_theme)
        definitions = icon_theme["iconDefinitions"]

        required_paths = {icon_path for _, _, _, icon_path in mappings}
        special = {
            "file": definitions[str(icon_theme["file"])]["iconPath"],
            "folder": definitions[str(icon_theme["folder"])]["iconPath"],
            "folder_expanded": definitions[str(icon_theme["folderExpanded"])]["iconPath"],
            "mizu_file_type_source": definitions[str(icon_theme["file"])]["iconPath"],
            "mizu_file_type_markup": definitions[str(icon_theme["fileExtensions"]["html"])]["iconPath"],
            "mizu_file_type_text": definitions[str(icon_theme["fileExtensions"]["txt"])]["iconPath"],
            "mizu_file_type_environment": definitions[str(icon_theme["fileExtensions"]["env"])]["iconPath"],
        }
        required_paths.update(special.values())

        extracted = {}
        source_dir = staging / "svg"
        for icon_path in sorted(required_paths):
            member = f"extension/{icon_path}"
            archive.extract(member, source_dir)
            extracted[icon_path] = source_dir / member

        jobs = []
        for _, _, icon_name, icon_path in mappings:
            for size, suffix in SCALES:
                jobs.append((extracted[icon_path], size, icons_dir / f"{ICON_PREFIX}{icon_name}{suffix}.png"))
        for icon_name, icon_path in special.items():
            for size, suffix in SCALES:
                jobs.append((extracted[icon_path], size, icons_dir / f"{icon_name}{suffix}.png"))
        render_svgs(jobs)

    for filename, preference, _, _ in mappings:
        (preferences_dir / filename).write_bytes(
            plistlib.dumps(preference, fmt=plistlib.FMT_XML, sort_keys=False)
        )

    write_preference(preferences_dir / "Mizu Source.tmPreferences", "source", "mizu_file_type_source")
    write_preference(
        preferences_dir / "Mizu Markup.tmPreferences", "text.html, text.xml", "mizu_file_type_markup"
    )
    write_preference(preferences_dir / "Mizu Text.tmPreferences", "text", "mizu_file_type_text")
    write_preference(
        preferences_dir / "Mizu Environment.tmPreferences", "source.env", "mizu_file_type_environment"
    )

    if aliases_dir.is_dir():
        shutil.copytree(aliases_dir, package_aliases_dir)

    metadata = {
        "source": str(vsix),
        "package": PACKAGE_NAME,
        "file_icon_mappings": len(mappings) + 4,
        "filename_alias_syntaxes": len(list(package_aliases_dir.glob("*.sublime-syntax")))
        if package_aliases_dir.exists()
        else 0,
        "fallback_to_generic_file": fallbacks,
    }
    (package_dir / "Mizu File Icons.sublime-settings").write_text(json.dumps(metadata, indent=2) + "\n")
    (package_dir / ".supports-a-file-icon-customization").write_text("")
    return package_dir, metadata


def collect_changed_files(user_dir, package_dir):
    files = [
        user_dir / "Preferences.sublime-settings",
        user_dir / "Cursor Dark.sublime-theme",
        user_dir / "MSVC Light.sublime-theme",
    ]
    files.extend(sorted(user_dir.glob("Icon - Mizu *.tmPreferences")))
    if package_dir.exists():
        files.append(package_dir)
    return files


def create_backup(data_dir, changed):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = data_dir / "Backup" / PACKAGE_NAME / stamp
    backup.mkdir(parents=True)
    manifest = []
    for source in changed:
        if not source.exists():
            continue
        relative = source.relative_to(data_dir)
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        manifest.append(str(source))
    (backup / "BACKUP_MANIFEST.txt").write_text("\n".join(manifest) + "\n")
    return backup


def ignore_old_package(path, text):
    if '"zzzz Mizu Icons"' in text:
        return
    match = re.search(r'("ignored_packages"\s*:\s*\[)(.*?)(\])', text, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"Could not find ignored_packages in {path}")
    body = match.group(2)
    indent_match = re.search(r"\n([ \t]+)\S", body)
    indent = indent_match.group(1) if indent_match else "\t\t"
    body = body.rstrip() + f'\n{indent}"zzzz Mizu Icons",\n\t'
    updated = text[: match.start(2)] + body + text[match.end(2) :]
    path.write_text(updated)


def prefix_user_overrides(user_dir):
    for path in sorted(user_dir.glob("Icon - Mizu *.tmPreferences")):
        value = plistlib.loads(path.read_bytes())
        icon = value.get("settings", {}).get("icon", "")
        if icon and not icon.startswith(ICON_PREFIX):
            value["settings"]["icon"] = ICON_PREFIX + icon
            path.write_bytes(plistlib.dumps(value, fmt=plistlib.FMT_XML, sort_keys=False))


def patch_theme(path):
    value = json.loads(path.read_text())
    rules = value["rules"]
    textures = {
        "icon_file": "Mizu File Icons/icons/file.png",
        "icon_folder": "Mizu File Icons/icons/folder.png",
        "icon_folder_loading": "Mizu File Icons/icons/folder.png",
        "icon_folder_dup": "Mizu File Icons/icons/folder.png",
    }
    for class_name, texture in textures.items():
        candidates = [rule for rule in rules if rule.get("class") == class_name and "parents" not in rule]
        if candidates:
            rule = candidates[0]
        else:
            rule = {"class": class_name, "content_margin": [8, 8], "layer0.opacity": 1}
            rules.append(rule)
        rule["layer0.texture"] = texture
        rule["layer0.tint"] = None

    expanded = next(
        (
            rule
            for rule in rules
            if rule.get("class") == "icon_folder"
            and any("expanded" in parent.get("attributes", []) for parent in rule.get("parents", []))
        ),
        None,
    )
    if expanded is None:
        expanded = {
            "class": "icon_folder",
            "parents": [{"class": "tree_row", "attributes": ["expanded"]}],
        }
        rules.append(expanded)
    expanded["layer0.texture"] = "Mizu File Icons/icons/folder_expanded.png"
    expanded["layer0.tint"] = None
    path.write_text(json.dumps(value, indent=2) + "\n")


def png_dimensions(path):
    data = path.read_bytes()[:26]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise RuntimeError(f"Invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def validate_package(package_dir):
    settings = package_dir / "Mizu File Icons.sublime-settings"
    metadata = json.loads(settings.read_text())
    references = set()
    for preference in (package_dir / "preferences").glob("*.tmPreferences"):
        value = plistlib.loads(preference.read_bytes())
        icon = value.get("settings", {}).get("icon")
        if icon:
            references.add(icon)
    missing = []
    bad_sizes = []
    for icon in sorted(references | {"file", "folder", "folder_expanded"}):
        for size, suffix in SCALES:
            path = package_dir / "icons" / f"{icon}{suffix}.png"
            if not path.is_file():
                missing.append(str(path))
            elif png_dimensions(path) != (size, size):
                bad_sizes.append(f"{path}: {png_dimensions(path)}")
    if missing or bad_sizes:
        raise RuntimeError(f"Icon validation failed; missing={missing}, bad_sizes={bad_sizes}")
    return metadata, len(references)


def main():
    data_dir, packages_dir, installed_dir = package_paths()
    user_dir = packages_dir / "User"
    vsix = find_vsix(sys.argv[1] if len(sys.argv) > 1 else None)
    a_file_icon = find_a_file_icon(installed_dir)
    preferences_path, preferences_text, scheme, theme = active_settings(user_dir)
    aliases_dir = packages_dir / "zzz A File Icon" / "aliases"
    target_package = packages_dir / PACKAGE_NAME

    with tempfile.TemporaryDirectory(prefix="mizu-file-icons-") as temporary:
        staged_package, metadata = build_package(Path(temporary), vsix, a_file_icon, aliases_dir)
        validate_package(staged_package)

        changed = collect_changed_files(user_dir, target_package)
        print("Existing files to modify or replace:")
        for path in changed:
            print(f"  {path}")
        backup = create_backup(data_dir, changed)

        shutil.copytree(staged_package, target_package, dirs_exist_ok=True)
        ignore_old_package(preferences_path, preferences_text)
        prefix_user_overrides(user_dir)
        for theme_path in (user_dir / "Cursor Dark.sublime-theme", user_dir / "MSVC Light.sublime-theme"):
            patch_theme(theme_path)

    installed_metadata, reference_count = validate_package(target_package)
    print(f"Active color scheme: {scheme}")
    print(f"Active UI theme: {theme}")
    print("File icon provider: A File Icon mappings with Mizu File Icons assets")
    print(f"Mizu archive: {vsix}")
    print(f"Package path: {target_package}")
    print(f"Backup path: {backup}")
    print(f"Validated icon references: {reference_count}")
    print(f"Alias syntaxes: {installed_metadata['filename_alias_syntaxes']}")
    print(f"Dedicated Mizu mappings: {installed_metadata['file_icon_mappings'] - len(metadata['fallback_to_generic_file'])}")
    print(f"Generic fallbacks: {len(metadata['fallback_to_generic_file'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
