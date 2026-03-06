#!/usr/bin/env python3
"""
Captcha OCR solver using ddddocr.
Reads image from stdin, outputs recognized text to stdout.
Install: pip install ddddocr
"""
import sys
import io

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import ddddocr

# Character confusion fixes (common OCR mistakes)
CHAR_FIX = {
    "o": "0", "O": "0",
    "l": "1", "I": "1",
    "z": "2", "Z": "2",
    "s": "5", "S": "5",
    "b": "6",
    "B": "8",
    "g": "9", "q": "9",
}

def solve():
    image_data = sys.stdin.buffer.read()
    if not image_data:
        sys.exit(1)

    ocr = ddddocr.DdddOcr(show_ad=False)
    result = ocr.classification(image_data)

    if not result:
        sys.exit(1)

    # Apply character fixes
    cleaned = "".join(CHAR_FIX.get(c, c) for c in result)

    # Only keep alphanumeric
    cleaned = "".join(c for c in cleaned if c.isalnum())

    print(cleaned)

if __name__ == "__main__":
    solve()
