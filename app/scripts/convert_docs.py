"""
Convert documents to Markdown with:
- Image extraction to separate files
- Hash-based state tracking (skip unchanged files)
- Auto-chunking for files > 100K (by chapter, fallback to size)

Usage:
    python convert_docs.py <file_or_dir> [<file_or_dir> ...]
    python convert_docs.py --project /path/to/project <file>

Output:  <project-root>/md-doc/
State:   <ai-env>/ai-state/convert_state.json
"""

import argparse
import base64
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from markitdown import MarkItDown

CHUNK_SIZE = 100 * 1024  # 100 KB
SUPPORTED_EXT = {".docx", ".xlsx", ".pdf", ".pptx", ".html", ".htm", ".csv", ".txt", ".md"}
STATE_FILE = "convert_state.json"


class DocConverter:
    def __init__(self, project_root: Path, aienv_dir: Path):
        self.project_root = project_root.resolve()
        self.aienv_dir = aienv_dir.resolve()
        self.output_dir = self.project_root / "md-doc"
        self.state_dir = self.aienv_dir / "ai-state"
        self.state_path = self.state_dir / STATE_FILE
        self.state = self._load_state()
        self.md = MarkItDown()

    # ── State management ──────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"files": {}}

    def _save_state(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _hash_file(self, path: Path) -> str:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()

    # ── Entry point ───────────────────────────────────────────────────────────

    def convert(self, source: Path):
        source = source.resolve()
        if not source.exists():
            print(f"[error] Not found: {source}")
            return
        if source.suffix.lower() not in SUPPORTED_EXT:
            print(f"[skip]  Unsupported format: {source.name}")
            return

        key = str(source)
        current_hash = self._hash_file(source)

        if self.state["files"].get(key, {}).get("hash") == current_hash:
            print(f"[skip]  {source.name} (unchanged)")
            return

        print(f"[convert] {source.name} ...")
        try:
            result = self.md.convert(str(source))
        except Exception as e:
            print(f"[error] Conversion failed: {e}")
            return

        text = result.text_content or ""

        # Extract base64 images to separate files
        img_dir = self.output_dir / source.stem
        text = self._extract_images(text, img_dir, source.stem)

        # Chunk if needed
        if len(text.encode("utf-8")) > CHUNK_SIZE:
            outputs = self._write_chunks(text, source.stem)
        else:
            out = self.output_dir / f"{source.stem}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            outputs = [str(out.relative_to(self.project_root))]
            print(f"  -> {out.relative_to(self.project_root)}")

        self.state["files"][key] = {
            "hash": current_hash,
            "converted_at": datetime.now().isoformat(),
            "source": str(source),
            "outputs": outputs,
        }
        self._save_state()

    # ── Image extraction ──────────────────────────────────────────────────────

    def _extract_images(self, text: str, img_dir: Path, stem: str) -> str:
        """Replace base64 data URIs with saved image files."""
        counter = [0]
        pattern = r'!\[([^\]]*)\]\(data:(image/[^;]+);base64,([A-Za-z0-9+/=\s]+)\)'

        def replace(m):
            alt = m.group(1)
            mime = m.group(2)
            data = re.sub(r'\s', '', m.group(3))
            ext = mime.split("/")[1].split("+")[0].split(";")[0]
            counter[0] += 1
            img_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{stem}_{counter[0]:03d}.{ext}"
            img_path = img_dir / filename
            try:
                img_path.write_bytes(base64.b64decode(data))
                rel = img_path.relative_to(self.output_dir)
                return f"![{alt}]({rel})"
            except Exception:
                return m.group(0)

        result = re.sub(pattern, replace, text, flags=re.DOTALL)
        if counter[0]:
            print(f"  -> extracted {counter[0]} image(s) to {img_dir.relative_to(self.project_root)}/")
        return result

    # ── Chunking ──────────────────────────────────────────────────────────────

    def _write_chunks(self, text: str, stem: str) -> list[str]:
        chunks = self._chunk_by_chapter(text)
        if not chunks:
            print(f"  (no chapters found, chunking by size)")
            chunks = self._chunk_by_size(text)
        else:
            chunks = self._merge_or_split(chunks)
            print(f"  (split into {len(chunks)} chapter chunk(s))")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        outputs = []
        for i, chunk in enumerate(chunks, 1):
            out = self.output_dir / f"{stem}_part{i:02d}.md"
            out.write_text(chunk, encoding="utf-8")
            outputs.append(str(out.relative_to(self.project_root)))
            print(f"  -> {out.relative_to(self.project_root)}")
        return outputs

    def _chunk_by_chapter(self, text: str) -> list[str]:
        """Split at top-level headings (# or ##)."""
        parts = re.split(r'(?=\n#{1,2} |\A#{1,2} )', text)
        parts = [p for p in parts if p.strip()]
        return parts if len(parts) > 1 else []

    def _merge_or_split(self, chunks: list[str]) -> list[str]:
        """Merge small chunks; further split chunks that are still too large."""
        result = []
        current = ""
        for chunk in chunks:
            candidate = current + chunk
            if len(candidate.encode("utf-8")) > CHUNK_SIZE and current:
                result.append(current)
                current = chunk
            else:
                current = candidate
        if current:
            result.append(current)

        # Further split any chunk still over limit
        final = []
        for chunk in result:
            if len(chunk.encode("utf-8")) > CHUNK_SIZE:
                final.extend(self._chunk_by_size(chunk))
            else:
                final.append(chunk)
        return final

    def _chunk_by_size(self, text: str) -> list[str]:
        """Split into CHUNK_SIZE byte blocks, breaking at newlines."""
        encoded = text.encode("utf-8")
        chunks = []
        start = 0
        while start < len(encoded):
            end = start + CHUNK_SIZE
            if end >= len(encoded):
                chunks.append(encoded[start:].decode("utf-8", errors="replace"))
                break
            # Break at last newline within the chunk
            nl = encoded[start:end].rfind(b"\n")
            if nl > 0:
                end = start + nl + 1
            chunks.append(encoded[start:end].decode("utf-8", errors="replace"))
            start = end
        return chunks


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert documents to Markdown with image extraction and chunking"
    )
    parser.add_argument("files", nargs="+", help="Files or directories to convert")
    parser.add_argument("--project", help="Project root directory (default: parent of ai-env)")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    aienv_dir = script_dir.parent
    project_root = Path(args.project).resolve() if args.project else aienv_dir.parent

    print(f"[config] project : {project_root}")
    print(f"[config] output  : {project_root / 'md-doc'}")
    print(f"[config] state   : {aienv_dir / 'ai-state' / STATE_FILE}")
    print()

    converter = DocConverter(project_root, aienv_dir)

    for target in args.files:
        path = Path(target)
        if path.is_dir():
            files = [p for p in sorted(path.rglob("*"))
                     if p.is_file() and p.suffix.lower() in SUPPORTED_EXT]
            if not files:
                print(f"[warn] No supported files in {path}")
            for f in files:
                converter.convert(f)
        elif path.is_file():
            converter.convert(path)
        else:
            print(f"[error] Not found: {path}")


if __name__ == "__main__":
    main()
