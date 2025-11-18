# src/film_gap/nlp/extract.py
from pathlib import Path
import csv, re
from typing import Dict, List, Tuple

def load_taxonomy(csv_path: Path) -> Dict[str, List[str]]:
    """
    Robust CSV loader:
    - Handles UTF-8 BOM
    - Normalizes newlines
    - Ignores the 'type' column if present
    - Uses alias list split by ';'
    """
    import io, csv

    # Read raw bytes and decode with BOM handling
    raw = csv_path.read_bytes()
    text = raw.decode("utf-8-sig", errors="replace")
    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    f = io.StringIO(text)
    reader = csv.reader(f)

    try:
        header = next(reader)
    except StopIteration:
        return {}

    header = [h.strip().lower() for h in header]
    # determine column indices
    try:
        i_canon = header.index("canonical")
    except ValueError:
        return {}  # header not found

    i_alias = header.index("aliases") if "aliases" in header else None

    taxo: Dict[str, List[str]] = {}
    for row in reader:
        if not row or all(not str(x).strip() for x in row):
            continue
        if i_canon >= len(row):
            continue
        canonical = row[i_canon].strip().upper()
        if not canonical:
            continue
        aliases: List[str] = [canonical]
        if i_alias is not None and i_alias < len(row):
            alias_field = row[i_alias].strip()
            if alias_field:
                aliases += [a.strip() for a in alias_field.split(";") if a.strip()]
        taxo[canonical] = aliases
    return taxo


def find_spans(text_lower: str, term_lower: str) -> List[Tuple[int,int]]:
    spans=[]
    for m in re.finditer(re.escape(term_lower), text_lower, flags=re.IGNORECASE):
        spans.append((m.start(), m.end()))
    return spans[:5]

def extract_skills(text: str, taxo: Dict[str, List[str]]) -> List[str]:
    """Return a sorted list of canonical skills found in the text."""
    text_lower = text.lower()
    found=set()
    for canon, variants in taxo.items():
        for v in variants:
            v = v.lower()
            if v and v in text_lower:
                found.add(canon)
                break
    return sorted(found)

def guess_years(text: str) -> int:
    m = re.search(r"(\d+)\s+(?:years|yrs)", text.lower())
    return int(m.group(1)) if m else 0

def predict_role(text: str) -> str:
    t = text.lower()
    if "line producer" in t or "lp" in t:
        return "LINE_PRODUCING"
    if "director of photography" in t or "dop" in t or "cinematograph" in t:
        return "CINEMATOGRAPHY"
    if "colorist" in t or "color grading" in t:
        return "COLOR_GRADING"
    if "premiere" in t:
        return "ADOBE_PREMIERE"
    return "UNKNOWN"
