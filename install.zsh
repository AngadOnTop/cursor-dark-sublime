#!/bin/zsh
set -euo pipefail

repo_dir=${0:A:h}
packages_dir="$HOME/Library/Application Support/Sublime Text/Packages"
user_dir="$packages_dir/User"
mizu_dir="$packages_dir/zzzz Mizu Icons"
afi_override_dir="$packages_dir/A File Icon/icons/multi"
afi_cache_dir="$packages_dir/zzz A File Icon/patches/general/multi"

mkdir -p "$user_dir" "$afi_override_dir"

cp "$repo_dir/Cursor Dark.sublime-color-scheme" "$user_dir/"
cp "$repo_dir/Cursor Dark.sublime-theme" "$user_dir/"
cp "$repo_dir/MSVC Light.sublime-color-scheme" "$user_dir/"
cp "$repo_dir/MSVC Light.sublime-theme" "$user_dir/"
cp "$repo_dir/A File Icon.sublime-settings" "$user_dir/"

rsync -a --delete "$repo_dir/zzzz Mizu Icons/" "$mizu_dir/"
rsync -a --delete "$repo_dir/zzzz Mizu Icons/icons/multi/" "$afi_override_dir/"

if [[ -d "$afi_cache_dir" ]]; then
  rsync -a "$repo_dir/zzzz Mizu Icons/icons/multi/" "$afi_cache_dir/"
fi

echo "Installed Cursor Dark, MSVC Light, and original-color Mizu icons."
echo "Restart Sublime Text if the sidebar icons do not refresh immediately."
