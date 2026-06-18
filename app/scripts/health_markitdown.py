from pathlib import Path
import os
from dotenv import load_dotenv
from markitdown import MarkItDown

ENV_FILE = Path.home() / ".portable_ai_environment" / "claude.env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
    ffmpeg_path = os.getenv("FFMPEG_PATH", "").strip().strip('"')
    if ffmpeg_path:
        os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

BASE = Path(__file__).resolve().parents[1]
TEST_DIR = BASE / "test_docs"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

samples = [
    TEST_DIR / "sample.docx",
    TEST_DIR / "sample.xlsx",
    TEST_DIR / "sample.pdf",
]

missing = [str(p) for p in samples if not p.exists()]
if missing:
    print("[markitdown] Sample files not found. Skipping conversion health check.")
    print("[markitdown] Missing:")
    for item in missing:
        print(" -", item)
    raise SystemExit(0)

md = MarkItDown()

for src in samples:
    print(f"[markitdown] Converting {src.name}...")
    result = md.convert(str(src))
    text = result.text_content or ""
    if not text.strip():
        raise SystemExit(f"[error] Empty conversion result: {src.name}")
    out = OUTPUT_DIR / f"{src.stem}.md"
    out.write_text(text, encoding="utf-8")

print("[markitdown] Health check passed.")

for f in OUTPUT_DIR.glob("*.md"):
    f.unlink()
