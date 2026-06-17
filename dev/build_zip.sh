#!/usr/bin/env bash
# 用途：將 app/ 打包成可交付的 ZIP
# 使用方式：
#   ./dev/build_zip.sh              # 輸出 dist/portable_claude_env.zip
#   ./dev/build_zip.sh myname.zip   # 自訂輸出檔名

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$REPO_DIR/app"
DIST_DIR="$REPO_DIR/dist"

OUTPUT="${1:-portable_claude_env.zip}"
# 若沒有帶路徑，預設放到 dist/
if [[ "$OUTPUT" != */* ]]; then
  mkdir -p "$DIST_DIR"
  OUTPUT="$DIST_DIR/$OUTPUT"
fi

echo "[build] Packaging app/ → $OUTPUT"

(
  cd "$APP_DIR"
  python3 -c "
import zipfile, pathlib, sys
exclude = {'.venv', 'output', '__pycache__', 'python', 'node'}
out = sys.argv[1]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in pathlib.Path('.').rglob('*'):
        parts = set(f.parts)
        if f.is_file() and not parts & exclude and not f.name.endswith('.zip') and f.name != '.env':
            z.write(str(f))
print('[build] Done:', out)
" "$OUTPUT"
)

echo "[build] Size: $(du -sh "$OUTPUT" | cut -f1)"
