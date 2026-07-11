#!/bin/zsh
set -euo pipefail

repo_dir=${0:A:h}
packages_dir="$HOME/Library/Application Support/Sublime Text/Packages"
user_dir="$packages_dir/User"
user_icons_dir="$user_dir/icons"
mizu_dir="$packages_dir/zzzz Mizu Icons"
afi_override_dir="$packages_dir/A File Icon/icons/multi"
afi_cache_dir="$packages_dir/zzz A File Icon/patches/general/multi"

write_icon_pref() {
  local label="$1"
  local scope="$2"
  local icon="$3"
  local pref_file="$user_dir/Icon - Mizu ${label}.tmPreferences"

  cat > "$pref_file" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://apple.com">
<plist version="1.0">
<dict>
    <key>scope</key>
    <string>${scope}</string>
    <key>settings</key>
    <dict>
        <key>icon</key>
        <string>${icon}</string>
    </dict>
</dict>
</plist>
EOF
}

mkdir -p "$user_dir" "$user_icons_dir" "$afi_override_dir"

cp "$repo_dir/Cursor Dark.sublime-color-scheme" "$user_dir/"
cp "$repo_dir/Cursor Dark.sublime-theme" "$user_dir/"
cp "$repo_dir/MSVC Light.sublime-color-scheme" "$user_dir/"
cp "$repo_dir/MSVC Light.sublime-theme" "$user_dir/"
cp "$repo_dir/A File Icon.sublime-settings" "$user_dir/"

rsync -a --delete "$repo_dir/zzzz Mizu Icons/" "$mizu_dir/"
rsync -a --delete "$repo_dir/zzzz Mizu Icons/icons/multi/" "$afi_override_dir/"
rsync -a "$repo_dir/zzzz Mizu Icons/icons/multi/" "$user_icons_dir/"

for icon_png in "$user_icons_dir"/file_type_*.png(N); do
  [[ "$icon_png" == *@2x.png ]] && continue
  [[ -f "${icon_png:r}@2x.png" ]] || cp "$icon_png" "${icon_png:r}@2x.png"
done

write_icon_pref "C" "source.c" "file_type_c"
write_icon_pref "C++" "source.c++" "file_type_c++"
write_icon_pref "C++ Header" "source.c++.header" "file_type_cppheader"
write_icon_pref "C#" "source.cs" "file_type_csharp"
write_icon_pref "CMake" "source.cmake" "file_type_cmake"
write_icon_pref "CSS" "source.css" "file_type_css"
write_icon_pref "Go" "source.go" "file_type_go"
write_icon_pref "HTML" "text.html" "file_type_html"
write_icon_pref "Java" "source.java" "file_type_java"
write_icon_pref "JavaScript" "source.js" "file_type_js"
write_icon_pref "JSX" "source.jsx" "file_type_jsx"
write_icon_pref "JSON" "source.json" "file_type_json"
write_icon_pref "Markdown" "text.html.markdown" "file_type_markdown"
write_icon_pref "Python" "source.python, text.plain.python" "file_type_python"
write_icon_pref "Rust" "source.rust" "file_type_rust"
write_icon_pref "Shell" "source.shell" "file_type_shell"
write_icon_pref "TypeScript" "source.js.typescript, source.ts" "file_type_typescript"
write_icon_pref "TSX" "source.tsx" "file_type_tsx"
write_icon_pref "YAML" "source.yaml" "file_type_yaml"

if [[ -d "$afi_cache_dir" ]]; then
  rsync -a "$repo_dir/zzzz Mizu Icons/icons/multi/" "$afi_cache_dir/"
fi

echo "Installed Cursor Dark, MSVC Light, and original-color Mizu icons."
echo "Restart Sublime Text if the sidebar icons do not refresh immediately."
