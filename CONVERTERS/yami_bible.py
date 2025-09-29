import re
from pathlib import Path
import pandas as pd

def clean_text_to_excel(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    verses_data = []

    i = 0
    total_lines = len(lines)
    while i < total_lines:
        # Detect the start of a book
        book_match = re.match(r'^\s*(Matay|Make|Locya)\s*\d+', lines[i])
        if book_match:
            current_book = book_match.group(1)
            chapter = 1
            last_verse = 0
            buffer = ""
            book_lines = []

            # Read lines until next book or end of file
            while i < total_lines:
                ln = lines[i].strip()
                next_book_match = re.match(r'^\s*(Matay|Make|Locya)\s*\d+', ln)
                if next_book_match and next_book_match.group(1) != current_book:
                    break  # stop at the next book

                # Skip lone book name lines
                if re.match(r'^\s*(Matay|Make|Locya)\s*$', ln):
                    i += 1
                    continue

                book_lines.append(ln)
                i += 1

            # --- Clean the book chunk ---

            # 1) Remove parenthetical references
            cleaned = []
            j = 0
            while j < len(book_lines):
                ln = book_lines[j]
                if re.search(r'\([^)]*:\d', ln):
                    if cleaned and not re.match(r'^\s*\d', cleaned[-1]):
                        cleaned.pop()
                    j += 1
                    continue
                cleaned.append(ln)
                j += 1
            book_lines = cleaned

            # 2) Remove Seysyo / copyright
            cleaned = []
            j = 0
            while j < len(book_lines):
                ln = book_lines[j]
                if 'Seysyo No Tao' in ln or '© Bible Society' in ln:
                    j += 1
                    continue
                if re.match(r'^\s*\d+\s*$', ln):
                    lookahead = " ".join(book_lines[j+1:j+4])
                    if 'Seysyo No Tao' in lookahead or '© Bible Society' in lookahead:
                        j += 1
                        continue
                cleaned.append(ln)
                j += 1
            book_lines = cleaned

            # 3) Join broken lines, split ranges, store chapter:verse, book, text
            def flush():
                nonlocal buffer, last_verse, chapter
                s = re.sub(r'\s+', ' ', buffer.strip())
                if not s:
                    return
                m = re.match(r'^(\d+)(?:-(\d+))?([^\s].*)?', s)
                if m:
                    verse_start = int(m.group(1))
                    verse_end = int(m.group(2)) if m.group(2) else verse_start
                    # numbering restart → new chapter
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
            i += 1  # skip until first book

    # --- Filter out leftover lines that are just book names ---
    verses_data = [
        row for row in verses_data
        if not re.match(rf'^{row["Book"]}\s*\d*$', row["Text"])
    ]

    # Write Excel
    df = pd.DataFrame(verses_data)
    df = df[["Book", "ChapterVerse", "Text"]]  # reorder columns
    df.to_excel(output_file, index=False)
    print(f"Saved cleaned Excel to: {output_file}")


# Example usage
base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "yami_bible.txt"
out_excel = base_dir / "CONVERTED_FILES" / "yami_bible_cleaned.xlsx"
clean_text_to_excel(input_file, out_excel)
