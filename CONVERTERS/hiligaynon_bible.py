import re
from pathlib import Path
import pandas as pd

# Base directory (folder containing this script)
base_dir = Path(__file__).resolve().parent

# Input/output paths
input_file = base_dir.parent / "RAW_FILES" / "hiligaynon_bible.txt"
output_file_excel = base_dir.parent / "CONVERTED_FILES" / "hiligaynon_bible_cleaned.xlsx"
output_file_sentences = base_dir.parent / "CONVERTED_FILES" / "hiligaynon_sentences.txt"

def clean_hiligaynon_bible():
    # Normalization for book tokens
    book_map = {
        "MATEO": "MATEO",
        "MARCOS": "MARCOS",
        "MAR": "MARCOS",
        "MARK": "MARCOS",
        "LUCAS": "LUCAS",
        "LUKAS": "LUCAS",
    }

    book_sequence = ["MATEO", "MARCOS", "LUCAS"]
    book_index = 0

    # Regex patterns
    book_header_re = re.compile(r"^(MATEO|MARCOS|MAR|MARK|LUCAS|LUKAS)\b", re.IGNORECASE)
    chapter_re = re.compile(r"^Chapter\s+(\d+)\b", re.IGNORECASE)
    numeric_only_re = re.compile(r"^\s*(\d+)\s*$")
    solitary_letter_re = re.compile(r"^[A-Za-z]$")
    parenthetical_re = re.compile(r"\([^)]*\)")
    tag_re = re.compile(r"<[^>]+>")
    remove_punct_re = re.compile(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ]")
    squeeze_space_re = re.compile(r"\s+")
    sentence_split_re = re.compile(r"(?<=[.!?])\s+")

    # Read lines
    with open(input_file, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    def prev_nonempty_idx(i):
        j = i - 1
        while j >= 0:
            if raw_lines[j].strip() != "":
                return j
            j -= 1
        return None

    def next_nonempty_idx(i):
        j = i + 1
        while j < len(raw_lines):
            if raw_lines[j].strip() != "":
                return j
            j += 1
        return None

    current_book = None
    current_chapter = None
    chapter_buffer = []
    rows = []
    sentences = []
    last_seen_verse = 0

    def flush_chapter_buffer():
        nonlocal chapter_buffer, current_book, current_chapter, rows, last_seen_verse, sentences
        if not chapter_buffer:
            return

        chap_text = " ".join(chapter_buffer).strip()
        chapter_buffer = []

        # Remove tags and parentheses
        chap_text = parenthetical_re.sub("", chap_text)
        chap_text = tag_re.sub("", chap_text)

        # Find verse numbers
        verse_num_re = re.compile(r"(\d{1,3})\s+")
        matches = list(verse_num_re.finditer(chap_text))
        if not matches:
            return

        for idx, m in enumerate(matches):
            verse_num = m.group(1)
            start = m.end()
            end = matches[idx + 1].start() if (idx + 1) < len(matches) else len(chap_text)
            verse_text = chap_text[start:end].strip()

            # Clean verse text
            verse_text = remove_punct_re.sub("", verse_text)
            verse_text = squeeze_space_re.sub(" ", verse_text).strip()

            # Segment sentences
            verse_sentences = sentence_split_re.split(verse_text)
            for s in verse_sentences:
                s = s.strip()
                if s:
                    sentences.append(s)

            # Save to Excel
            chapter_num = current_chapter if current_chapter is not None else 1
            rows.append({
                "Book": current_book,
                "Chapter": chapter_num,
                "Verse": verse_num,
                "Text": verse_text
            })

            try:
                last_seen_verse = max(last_seen_verse, int(verse_num))
            except Exception:
                pass

    for i, raw in enumerate(raw_lines):
        s_raw = raw.rstrip("\n")
        s = s_raw.strip()
        if s == "":
            continue

        # Book headers
        m_book = book_header_re.match(s)
        if m_book:
            flush_chapter_buffer()
            bkkey = m_book.group(1).upper()
            current_book = book_map.get(bkkey, bkkey)
            last_seen_verse = 0
            continue

        # Chapter lines
        m_chap = chapter_re.match(s)
        if m_chap:
            flush_chapter_buffer()
            try:
                current_chapter = int(m_chap.group(1))
            except Exception:
                current_chapter = None
            last_seen_verse = 0
            if current_book is None and book_index < len(book_sequence):
                current_book = book_sequence[book_index]
                book_index += 1
            continue

        # Skip single letters or parenthetical-only lines
        if solitary_letter_re.match(s) or parenthetical_re.fullmatch(s):
            continue

        # Numeric-only lines: decide if verse or page number
        m_num = numeric_only_re.match(s)
        if m_num:
            n = int(m_num.group(1))
            pidx = prev_nonempty_idx(i)
            nidx = next_nonempty_idx(i)
            prev_line = raw_lines[pidx].strip() if pidx is not None else ""
            next_line = raw_lines[nidx].strip() if nidx is not None else ""

            def is_header_line(text):
                return bool(book_header_re.match(text) or chapter_re.match(text))

            prev_is_header = is_header_line(prev_line)
            next_is_header = is_header_line(next_line)
            next_looks_like_text = bool(next_line and not numeric_only_re.match(next_line) and not is_header_line(next_line) and len(next_line) > 6)

            is_verse = False
            if prev_is_header or next_is_header:
                is_verse = False
            elif current_chapter is not None and (n == last_seen_verse + 1 or (last_seen_verse == 0 and n == 1)):
                is_verse = True
            elif next_looks_like_text:
                is_verse = True

            if is_verse:
                chapter_buffer.append(f"{n} ")
                last_seen_verse = n
            continue

        # Normal text line
        s = parenthetical_re.sub("", s)
        s = tag_re.sub("", s)
        chapter_buffer.append(s)

    flush_chapter_buffer()

    # Save Excel
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["Book", "Chapter", "Verse", "Text"])
    df.to_excel(output_file_excel, index=False)

    # Save sentences
    with open(output_file_sentences, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(sentences))

    print(f"Saved Excel -> {output_file_excel}")
    print(f"Saved Sentences -> {output_file_sentences}")

if __name__ == "__main__":
    clean_hiligaynon_bible()
