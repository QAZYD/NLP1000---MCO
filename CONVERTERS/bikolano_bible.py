import re
from pathlib import Path
import pandas as pd

def clean_bikolano_text_to_excel(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    verses_data = []
    i = 0
    total_lines = len(lines)

    # Regex that matches all variations
    book_pattern = r'^\s*(Mateo|Marcos|Markos|Lucas|Lukas)\s*\d+'

    while i < total_lines:
        book_match = re.match(book_pattern, lines[i])
        if book_match:
            raw_book = book_match.group(1)
            # Normalize spelling
            if raw_book.startswith("Mat"):
                current_book = "Mateo"
            elif raw_book.startswith("Mar"):
                current_book = "Marcos"
            elif raw_book.startswith("Mark"):
                current_book = "Marcos"
            elif raw_book.startswith("Lu"):
                current_book = "Lucas"
            else:
                current_book = raw_book

            chapter = 1
            last_verse = 0
            buffer = ""
            book_lines = []

            # Read lines until next book or end of file
            while i < total_lines:
                ln = lines[i].strip()
                next_book_match = re.match(book_pattern, ln)
                if next_book_match:
                    break

                # Skip lone book name lines
                if re.match(r'^\s*(Mateo|Marcos|Markos|Lucas|Lukas)\s*$', ln):
                    i += 1
                    continue

                book_lines.append(ln)
                i += 1

            # --- Clean the book chunk ---

            # 1) Remove parenthetical references like (Mt. 27:1-2)
            cleaned = []
            for ln in book_lines:
                if re.search(r'\([^)]*:\d', ln):
                    continue
                cleaned.append(ln)
            book_lines = cleaned

            # 2) Remove copyright/footer
            cleaned = []
            for ln in book_lines:
                if 'Marahay na Bareta Biblia' in ln or '©' in ln or 'Philippine Bible Society' in ln:
                    continue
                cleaned.append(ln)
            book_lines = cleaned

            # 3) Join broken lines, split ranges, store
            def flush():
                nonlocal buffer, last_verse, chapter
                s = re.sub(r'\s+', ' ', buffer.strip())
                if not s:
                    return
                m = re.match(r'^(\d+)(?:-(\d+))?([^\s].*)?', s)
                if m:
                    verse_start = int(m.group(1))
                    verse_end = int(m.group(2)) if m.group(2) else verse_start
                    if verse_start == 1 and last_verse > 1:
                        chapter += 1
                    last_verse = verse_start
                    text = m.group(3).strip() if m.group(3) else ""
                    for v in range(verse_start, verse_end + 1):
                        verses_data.append({
                            "Book": current_book,
                            "ChapterVerse": f"{chapter}:{v}",
                            "Text": text
                        })
                else:
                    verses_data.append({
                        "Book": current_book,
                        "ChapterVerse": None,
                        "Text": s
                    })
                buffer = ""

            last_verse = 0
            for idx, ln in enumerate(book_lines):
                s = ln.strip()
                next_ln = book_lines[idx+1] if idx+1 < len(book_lines) else ""
                starts_with_verse = bool(re.match(r'^\d+(?:-\d+)?', s))
                if starts_with_verse and buffer:
                    flush()
                buffer = (buffer + " " + s).strip() if buffer else s
                next_starts_with_number = bool(re.match(r'^\d', next_ln.strip()))
                if next_starts_with_number:
                    flush()
            if buffer:
                flush()

        else:
            i += 1

    # Filter out leftover lines that are just book names
    verses_data = [
        row for row in verses_data
        if not re.match(rf'^{row["Book"]}\s*\d*$', row["Text"] or "")
    ]

    # Write Excel
    df = pd.DataFrame(verses_data)
    df = df[["Book", "ChapterVerse", "Text"]]
    df.to_excel(output_file, index=False)
    print(f"Saved cleaned Bikolano Excel to: {output_file}")


# Example usage
base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "bikolano_bible.txt"
out_excel = base_dir / "CONVERTED_FILES" / "bikolano_bible_cleaned.xlsx"
clean_bikolano_text_to_excel(input_file, out_excel)
