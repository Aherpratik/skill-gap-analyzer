import re
import csv
from collections import Counter
from pathlib import Path
from docx import Document

# ----------------------------
# YOUR EXACT PATHS
# ----------------------------
RESUME_DIR = Path("/Users/pratikaher01/Documents/filmyai/data/resumes_docx")
JD_DIR = Path("/Users/pratikaher01/Documents/filmyai/data/jds_docx")

# ----------------------------
# CONFIG
# ----------------------------
MIN_FREQ = 2          # keep phrases appearing at least 2 times
MAX_PHRASE_LEN = 4    # 1–4 word phrases
OUTPUT_CSV = Path("data/mined_skill_phrases.csv")

WORD_RE = re.compile(r"[A-Za-z][A-Za-z+\-/&0-9]*")


def read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_docx(path: Path) -> str:
    try:
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"Error reading DOCX {path}: {e}")
        return ""


def read_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".txt":
        return read_txt(path)
    if ext == ".docx":
        return read_docx(path)
    return ""


def extract_phrases(text: str):
    words = WORD_RE.findall(text.lower())
    phrases = []
    for n in range(1, MAX_PHRASE_LEN + 1):  # unigram → 4-grams
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i+n])
            if len(phrase) < 3:
                continue
            if phrase.isdigit():
                continue
            phrases.append(phrase)
    return phrases


def iter_texts_from_folder(folder: Path):
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".txt", ".docx"}:
            yield read_file(path)


def main():
    counter = Counter()

    print("Reading resumes from", RESUME_DIR)
    for text in iter_texts_from_folder(RESUME_DIR):
        if not text.strip():
            continue
        for phrase in extract_phrases(text):
            counter[phrase] += 1

    print("Reading JDs from", JD_DIR)
    for text in iter_texts_from_folder(JD_DIR):
        if not text.strip():
            continue
        for phrase in extract_phrases(text):
            counter[phrase] += 1

    print("Filtering frequent phrases...")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["phrase", "frequency"])
        for phrase, freq in counter.most_common():
            if freq >= MIN_FREQ:
                writer.writerow([phrase, freq])

    print(f"Done. Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    print("\nMining skills from resumes and JDs...\n")
    main()