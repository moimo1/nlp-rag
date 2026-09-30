"""
clean_extracted.py
------------------
Reads OCR-extracted .txt files from ExtractedText/ and writes cleaned
versions to CleanedText/.

Cleaning pipeline (in order):
  1. Strip CamScanner watermark lines.
  2. Remove garbled / junk lines produced by OCR on logos/images.
  3. Detect and remove table-separator noise lines.
  4. Fix known OCR character-substitution misreads (rule-based).
  5. Normalize bullet characters (Unicode stand-ins and lone 'e') to *.
  6. Strip trailing scan-edge artifact characters.
  7. Strip leading underscore-indent artifacts (_*, _., _-).
  8. Collapse consecutive blank lines into a single blank line.
  9. Preserve  --- Page N ---  page markers throughout.
"""

import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT_DIR = os.path.join(os.path.dirname(__file__), "ExtractedText")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "CleanedText")

# ---------------------------------------------------------------------------
# 1. Watermark
# ---------------------------------------------------------------------------
WATERMARK_RE = re.compile(r"^\s*(?:ics\s+)?camscanner\s*$", re.IGNORECASE)

# ---------------------------------------------------------------------------
# 2. Garbled-line detection
# ---------------------------------------------------------------------------
def is_garbled(line):
    stripped = line.strip()
    if not stripped:
        return False
    alpha_count = sum(1 for ch in stripped if ch.isalpha())
    non_ws = [ch for ch in stripped if not ch.isspace()]
    if not non_ws:
        return True
    non_alnum_ratio = sum(1 for ch in non_ws if not ch.isalnum()) / len(non_ws)
    return alpha_count < 4 or non_alnum_ratio > 0.50

# ---------------------------------------------------------------------------
# 3. Table-separator noise detection
# ---------------------------------------------------------------------------
_CURRENCY_RE = re.compile(r"PhP|PHP|\d{1,3}(?:,\d{3})*\.\d{2}", re.IGNORECASE)
_COMMON_WORDS = {"of","in","and","the","to","for","a","an","by","or","at","as","on","be","with"}
_ALPHA_STRIP_RE = re.compile(r"[^a-zA-Z]")
_VOWEL_RE = re.compile(r"[aeiouAEIOU]")


def _has_vowel(word):
    return bool(_VOWEL_RE.search(word))


def is_table_noise(line):
    stripped = line.strip()
    if _CURRENCY_RE.search(stripped):
        return False
    alpha_words = [_ALPHA_STRIP_RE.sub("", w) for w in stripped.split()]
    alpha_words = [w for w in alpha_words if w]
    if not alpha_words:
        return False
    if any(len(w) > 20 for w in alpha_words):
        return True
    if len(alpha_words) < 3:
        return False
    avg_len = sum(len(w) for w in alpha_words) / len(alpha_words)
    vowel_ratio = sum(1 for w in alpha_words if _has_vowel(w)) / len(alpha_words)
    if avg_len <= 2.5:
        return True
    if avg_len <= 3.5 and vowel_ratio <= 0.75:
        return True
    if len(alpha_words) >= 6 and avg_len <= 4.5 and vowel_ratio < 1.0:
        common_ratio = sum(1 for w in alpha_words if w.lower() in _COMMON_WORDS) / len(alpha_words)
        if common_ratio < 0.35:
            return True
    return False

# ---------------------------------------------------------------------------
# 4. Known OCR misread corrections
# ---------------------------------------------------------------------------
_OCR_FIXES = {
    "Managernent": "Management",
    "managernent": "management",
    "Departrnent": "Department",
    "departrnent": "department",
    "Environrnent": "Environment",
    "environrnent": "environment",
    "Governrnent": "Government",
    "governrnent": "government",
    "Staternent": "Statement",
    "staternent": "statement",
    "Irnplementation": "Implementation",
    "irnplementation": "implementation",
    "Inforrnation": "Information",
    "inforrnation": "information",
    "Cornputer": "Computer",
    "cornputer": "computer",
    "Cornputing": "Computing",
    "cornputing": "computing",
    "Cornmerce": "Commerce",
    "cornmerce": "commerce",
    "Phillppines": "Philippines",
    "Philipines": "Philippines",
    "technolagy": "technology",
    "Technolagy": "Technology",
    "teennalogy": "technology",
    "Teennalogy": "Technology",
    "erivir": "",
    "HmmMents": "",
    "Schoo!": "School",
    "schoo!": "school",
    "Mathematies": "Mathematics",
    "mathematies": "mathematics",
    "Edueation": "Education",
    "edueation": "education",
    "Nuterhel": "Maternal",
    "sgents": "agents",
    "niemational": "international",
}

_OCR_SUBS = [
    (re.compile(r"\b" + re.escape(bad) + r"\b"), good)
    for bad, good in _OCR_FIXES.items()
    if good
]
_OCR_DROPS = [
    re.compile(r"\b" + re.escape(bad) + r"\b")
    for bad, good in _OCR_FIXES.items()
    if not good
]


def apply_ocr_fixes(line):
    for pattern, replacement in _OCR_SUBS:
        line = pattern.sub(replacement, line)
    for pattern in _OCR_DROPS:
        line = pattern.sub("", line)
    return re.sub(r" {2,}", " ", line).strip()

# ---------------------------------------------------------------------------
# 5. Bullet normalization
#    Only actual Unicode bullet stand-ins and lone 'e' before a capital letter
#    are replaced. All other line starters are left untouched.
# ---------------------------------------------------------------------------
_BULLET_CHARS = set("\u00ab\u00bb\u00b7\u2022\u00a7\u00a2\u00b0\u00b4\u2019\u00a4")


def normalize_bullets(line):
    stripped = line.strip()
    if not stripped:
        return stripped
    first = stripped[0]
    rest = stripped[1:].lstrip()
    # Unicode bullet stand-in
    if first in _BULLET_CHARS and rest:
        return "* " + rest
    # Lone lowercase 'e' used as bullet before an uppercase letter
    if (len(stripped) >= 3
            and stripped[0] == "e"
            and stripped[1] == " "
            and stripped[2].isupper()):
        return "* " + stripped[2:]
    return stripped

# ---------------------------------------------------------------------------
# 6. Trailing scan-edge artifact stripping
# ---------------------------------------------------------------------------
_TRAIL_SYM_RE = re.compile(r"\s+[^\w\d()]{1}$")
_TRAIL_ALPHA_RE = re.compile(r"\s+[a-zA-Z]{1}$")


def strip_trailing_artifact(line):
    line = _TRAIL_SYM_RE.sub("", line).rstrip()
    line = _TRAIL_ALPHA_RE.sub("", line).rstrip()
    return line

# ---------------------------------------------------------------------------
# 7. Leading underscore-indent artifact stripping
#    Removes patterns like _*, _., _-, _ (indentation OCR artifacts).
# ---------------------------------------------------------------------------
_LEAD_INDENT_RE = re.compile(r"^[_]+[*.\-#]?\s*")


def strip_leading_indent_artifact(line):
    return _LEAD_INDENT_RE.sub("", line).strip()

# ---------------------------------------------------------------------------
# 8. Core cleaning function
# ---------------------------------------------------------------------------
PAGE_MARKER_RE = re.compile(r"^--- Page \d+ ---$")


def clean_text(raw):
    lines = raw.splitlines()
    cleaned = []
    blank_run = 0

    for line in lines:
        stripped = line.strip()

        # Always keep page markers
        if PAGE_MARKER_RE.match(stripped):
            blank_run = 0
            cleaned.append(stripped)
            continue

        # Drop watermark lines
        if WATERMARK_RE.match(stripped):
            continue

        # Blank line handling — at most one consecutive blank
        if not stripped:
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
            continue
        else:
            blank_run = 0

        # Drop garbled lines
        if is_garbled(stripped):
            continue

        # Drop table-separator noise
        if is_table_noise(stripped):
            continue

        # Apply OCR fixes
        fixed = apply_ocr_fixes(stripped)
        if not fixed:
            continue

        # Strip leading underscore-indent artifacts (before bullet normalization)
        fixed = strip_leading_indent_artifact(fixed)
        if not fixed:
            continue

        # Normalize bullet characters
        fixed = normalize_bullets(fixed)
        if not fixed:
            continue

        # Strip trailing scan-edge artifacts
        fixed = strip_trailing_artifact(fixed)
        if not fixed:
            continue

        cleaned.append(fixed)

    result = "\n".join(cleaned).strip()
    return result + "\n"

# ---------------------------------------------------------------------------
# 9. Entry point
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    txt_files = sorted(Path(INPUT_DIR).glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {INPUT_DIR}")
        return

    for txt_path in txt_files:
        raw = txt_path.read_text(encoding="utf-8")
        cleaned = clean_text(raw)

        out_path = Path(OUTPUT_DIR) / txt_path.name
        out_path.write_text(cleaned, encoding="utf-8")

        original_lines = len(raw.splitlines())
        cleaned_lines = len(cleaned.splitlines())
        removed = original_lines - cleaned_lines
        print(f"[OK] {txt_path.name}  |  {original_lines} -> {cleaned_lines} lines  ({removed} removed)")

    print(f"\nCleaned files written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
