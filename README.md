# Cursor Dark for Sublime Text

An unofficial Sublime Text color scheme converted from Cursor's bundled
`Cursor Dark` theme.

It includes base editor colors, Cursor-style syntax colors, and extra rules
for Sublime LSP semantic highlighting so C++ symbols such as namespaces, types,
methods, properties, and macros can look closer to Cursor.

## Install

Place `Cursor Dark.sublime-color-scheme` in your Sublime Text user package
folder:

```text
~/Library/Application Support/Sublime Text/Packages/User/
```

Then open `Preferences: Settings` and set:

```json
{
  "theme": "Adaptive.sublime-theme",
  "color_scheme": "Cursor Dark.sublime-color-scheme"
}
```

On macOS, you can open Sublime settings with `Cmd+,`.

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

Sublime and Cursor/VS Code use different theme systems, so this is a color
scheme port rather than a full UI theme clone. It changes editor and syntax
colors; the surrounding Sublime UI is still controlled by your selected
Sublime theme.

Cursor and the original bundled theme belong to their respective owners. This
repo is just an unofficial Sublime Text conversion.
