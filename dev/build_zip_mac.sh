#!/usr/bin/env bash
# 用途：將 app-mac/ 打包成可交付的 macOS ZIP
# 使用方式：
#   ./dev/build_zip_mac.sh              # 輸出 dist/portable_claude_env_mac.zip
#   ./dev/build_zip_mac.sh myname.zip   # 自訂輸出檔名

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$REPO_DIR/app-mac"
DIST_DIR="$REPO_DIR/dist"

OUTPUT="${1:-portable_claude_env_mac.zip}"
if [[ "$OUTPUT" != */* ]]; then
  mkdir -p "$DIST_DIR"
  OUTPUT="$DIST_DIR/$OUTPUT"
fi

echo "[build] Packaging app-mac/ → $OUTPUT"

(
  cd "$APP_DIR"
  python3 -c "
import zipfile, pathlib, sys, os
exclude = {'.venv', 'output', '__pycache__', 'tools'}
out = sys.argv[1]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in pathlib.Path('.').rglob('*'):
        parts = set(f.parts)
        if f.is_file() and not parts & exclude and not f.name.endswith('.zip') and f.name != 'claude.env':
            info = zipfile.ZipInfo(str(f))
            # Preserve executable bit for .sh files
            if str(f).endswith('.sh'):
                info.external_attr = 0o755 << 16
            data = f.read_bytes()
            z.writestr(info, data)
print('[build] Done:', out)
" "$OUTPUT"
)

echo "[build] Size: $(du -sh "$OUTPUT" | cut -f1)"
