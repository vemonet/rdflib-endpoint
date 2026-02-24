#!/usr/bin/env python3
"""Generate DOCS.md from the custom functions registered in the example app.

Run from the repo root:
    python example/gen_docs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so both `src/` and `example/` are importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from example.main import ds  # noqa: E402  (import after path manipulation)

README = ROOT / "example" / "README.md"

START_MARKER = "<!-- FUNCTIONS_START -->"
END_MARKER = "<!-- FUNCTIONS_END -->"


def main() -> None:
    content = ds.generate_docs()
    if not content:
        print("No custom functions found — README.md not updated.", file=sys.stderr)
        sys.exit(1)

    # Read existing README and replace the block between markers
    text = README.read_text(encoding="utf-8")
    if START_MARKER in text and END_MARKER in text:
        pre, rest = text.split(START_MARKER, 1)
        _, post = rest.split(END_MARKER, 1)
        new_text = pre + START_MARKER + "\n\n" + content + "\n" + END_MARKER + post
        README.write_text(new_text, encoding="utf-8")
        print(f"✨ Updated {README.relative_to(ROOT)}")
    else:
        # Fallback: append the generated docs at the end
        README.write_text(text + "\n\n" + content + "\n", encoding="utf-8")
        print(f"Appended generated docs to {README.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
