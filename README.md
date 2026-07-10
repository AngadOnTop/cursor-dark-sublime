# Cursor Dark and MSVC Light for Sublime Text

Unofficial Sublime Text themes and color schemes:

- `Cursor Dark`, converted from Cursor's bundled dark theme.
  <img width="1440" height="900" alt="Screenshot 2026-07-10 at 5 33 09 pm" src="https://github.com/user-attachments/assets/ac056607-c5b7-4f81-9908-6640de9a40c9" />

- `MSVC Light`, inspired by the classic Visual Studio/MSVC light editor look.
  <img width="1440" height="900" alt="Screenshot 2026-07-10 at 5 33 28 pm" src="https://github.com/user-attachments/assets/781a9da6-fbb6-4425-88d0-5d61a963ea87" />


Each style has two files:

- `.sublime-theme` for Sublime's UI chrome, including sidebar, tabs, panels,
  popups, buttons, and status bar.
- `.sublime-color-scheme` for editor and syntax colors.

The color schemes include extra rules for Sublime LSP semantic highlighting so
C++ symbols such as namespaces, types, methods, properties, and macros can look
closer to Cursor.

## Install

Place the `.sublime-theme` and `.sublime-color-scheme` files in your Sublime
Text user package folder:

```text
~/Library/Application Support/Sublime Text/Packages/User/
```

Then open `Preferences: Settings` and choose one:

```json
{
  "theme": "Cursor Dark.sublime-theme",
  "color_scheme": "Cursor Dark.sublime-color-scheme"
}
```

```json
{
  "theme": "MSVC Light.sublime-theme",
  "color_scheme": "MSVC Light.sublime-color-scheme"
}
```

On macOS, you can open Sublime settings with `Cmd+,`.

You can also switch from the command palette:

```text
UI: Select Theme
UI: Select Color Scheme
```

For richer sidebar file-type icons, install `A File Icon` from Package Control.
Then place the `zzzz Mizu Icons` folder in:

```text
~/Library/Application Support/Sublime Text/Packages/
```

The Mizu package uses the same `file_type_*.png` names as `A File Icon`. For
Sublime's native custom-icon method, copy those PNGs into:

```text
~/Library/Application Support/Sublime Text/Packages/User/icons/
```

Then add `.tmPreferences` mappings in `Packages/User/` that point a scope to the
icon name. For example, C++ uses `source.c++` and `file_type_c++`.

For an A File Icon persistent override, also copy `zzzz Mizu Icons/icons/multi/`
into:

```text
~/Library/Application Support/Sublime Text/Packages/A File Icon/icons/multi/
```

Place `A File Icon.sublime-settings` in `Packages/User/` to keep icon tinting
disabled. You can run `./install.zsh` from this repo to copy the themes, color
schemes, Mizu icons, User icon mappings, and A File Icon overrides
automatically.

The included Mizu PNGs have their white VS Code export matte stripped so the
icons render transparently on both dark and light Sublime themes.

For Sublime's active-theme custom icon method, run:

```sh
python3 tools/install-mizu-theme-icons.py "/path/to/Mizu Icons 2.10.1.vsix"
```

That script reads `Preferences.sublime-settings`, creates an `icons/` folder for
the active theme, renders the original Mizu VSIX SVGs into `.png` and `@2x.png`
files, mirrors them into `Packages/User/icons/`, and writes the matching
`.tmPreferences` files.

## LSP Semantic Highlighting

For Cursor-like C++ highlighting, install:

```text
LSP
LSP-clangd
```

Then add this to `Packages/User/LSP.sublime-settings`:

```json
{
  "semantic_highlighting": true
}
```

This lets `clangd` color symbols that Sublime's normal syntax engine cannot
distinguish on its own.

## Notes

Sublime and Cursor/VS Code use different theme systems, so this is an
approximation rather than a pixel-perfect clone. The UI themes extend Sublime's
built-in `Adaptive.sublime-theme` and tint the major UI surfaces.

Cursor, Visual Studio, and the original bundled themes belong to their
respective owners. This repo is just an unofficial Sublime Text conversion and
companion light scheme.
