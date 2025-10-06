import re
from pathlib import Path
import pandas as pd

# Input/output paths - adjust if necessary
input_file = Path("../RAW_FILES/hiligaynon_bible.txt")
output_file_txt = Path("../CONVERTED_FILES/hiligaynon_cleaned.txt")
output_file_excel = Path("../CONVERTED_FILES/hiligaynon_bible_cleaned.xlsx")

def clean_hiligaynon_bible():

    # Normalization for book tokens we may encounter
    book_map = {
        "MATEO": "MATEO",
        "MARCOS": "MARCOS",
        "MAR": "MARCOS",
        "MARK": "MARCOS",
        "LUCAS": "LUCAS",
        "LUKAS": "LUCAS",
    }

    # Book Order
    book_sequence = ["MATEO", "MARCOS", "LUCAS"]
    book_index = 0

    # Regex patterns
    book_header_re = re.compile(r"^(MATEO|MARCOS|MAR|MARK|LUCAS|LUKAS)\b", re.IGNORECASE)
    # Note: we ignore the chapter number if present in a "MATEO Chapter X" header,
    # because your input may be inaccurate for those headers.
    chapter_re = re.compile(r"^Chapter\s+(\d+)\b", re.IGNORECASE)

    numeric_only_re = re.compile(r"^\s*(\d+)\s*$")       # line that contains only digits (and spaces)
    # page_indicator_with_space_re = re.compile(r"^\s+\d+\s*$") lines that start with space then number
    solitary_letter_re = re.compile(r"^[A-Za-z]$")       # single-letter lines (e.g. "a", "b")
    parenthetical_re = re.compile(r"\([^)]*\)")          # ( ... )
    tag_re = re.compile(r"<[^>]+>")                      # <tag>
    # keep Hiligaynon letters, digits and whitespace; remove other punctuation AFTER splitting verses
    remove_punct_re = re.compile(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ]")
    squeeze_space_re = re.compile(r"\s+")

    # read all lines so we can look ahead / behind for context
    with open(input_file, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # helper to find prev/next non-empty (stripped) line indices
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

    # accumulator and state
    current_book = None
    current_chapter = None
    chapter_buffer = []   # accumulate strings belonging to current chapter (we will join then split verses)
    rows = []
    cleaned_lines = []
    ambiguous = []        # collect ambiguous numeric-only decisions for manual review
    last_seen_verse = 0   # resets to 0 when chapter resets

    def flush_chapter_buffer():
        nonlocal chapter_buffer, current_book, current_chapter, rows, cleaned_lines, last_seen_verse
        if not chapter_buffer:
            return
        chap_text = " ".join(chapter_buffer).strip()
        chapter_buffer = []

        # remove tags and parentheticals before we try to locate verse numbers
        chap_text = parenthetical_re.sub("", chap_text)
        chap_text = tag_re.sub("", chap_text)

        # find verse numbers and slice text between them
        verse_num_re = re.compile(r"(\d{1,3})\s+")
        matches = list(verse_num_re.finditer(chap_text))
        if not matches:
            return

        for idx, m in enumerate(matches):
            verse_num = m.group(1)
            start = m.end()
            end = matches[idx + 1].start() if (idx + 1) < len(matches) else len(chap_text)
            verse_text = chap_text[start:end].strip()

            # cleanup text
            verse_text = remove_punct_re.sub("", verse_text)
            verse_text = squeeze_space_re.sub(" ", verse_text).strip()

            chap = current_chapter if current_chapter is not None else 1
            chap_verse = f"{chap}:{verse_num}"

            cleaned_lines.append(f"{current_book}|{chap_verse}|{verse_text}")
            rows.append({"Book": current_book, "ChapterVerse": chap_verse, "Text": verse_text})
            # update last_seen_verse
            try:
                last_seen_verse = max(last_seen_verse, int(verse_num))
            except Exception:
                pass

    # iterate through lines with index so we can use lookahead/behind
    for i, raw in enumerate(raw_lines):
        s_raw = raw.rstrip("\n")
        s = s_raw.strip()
        if s == "":
            continue

        # 1) Book header (MATEO / MARCOS / LUCAS) — do not trust chapter number here
        m_book = book_header_re.match(s)
        if m_book:
            # flush current chapter before switching book
            flush_chapter_buffer()
            bkkey = m_book.group(1).upper()
            current_book = book_map.get(bkkey, bkkey)
            # do not set current_chapter here (per your rule #2)
            # reset last_seen_verse so next Chapter will start at 1
            last_seen_verse = 0
            continue

        # 2) Correct chapter marker "Chapter N" (this is the authoritative chapter indicator)
        m_chap = chapter_re.match(s)
        if m_chap:
            flush_chapter_buffer()
            try:
                current_chapter = int(m_chap.group(1))
            except Exception:
                current_chapter = None
            last_seen_verse = 0

            # FIX: assign a book if we don't already have one
            if current_book is None and book_index < len(book_sequence):
                current_book = book_sequence[book_index]
                book_index += 1

            continue

        # 3) Skip solitary single-letter lines (page artifacts)
        if solitary_letter_re.match(s):
            continue

        # 4) Parenthetical-only lines (e.g., page footers like "(2)") — skip if the entire line becomes empty after removing parentheses
        if parenthetical_re.fullmatch(s):
            continue

        # 5) Numeric-only lines: need to decide page vs verse
        m_num = numeric_only_re.match(s)
        if m_num:
            n = int(m_num.group(1))

            # gather context
            pidx = prev_nonempty_idx(i)
            nidx = next_nonempty_idx(i)
            prev_line = raw_lines[pidx].strip() if pidx is not None else ""
            next_line = raw_lines[nidx].strip() if nidx is not None else ""

            # helper checks
            def is_header_line(text):
                return bool(book_header_re.match(text) or chapter_re.match(text))

            prev_is_header = is_header_line(prev_line) if prev_line else False
            next_is_header = is_header_line(next_line) if next_line else False

            # Heuristic decisions:
            is_verse = False

            # - If adjacent to a header -> treat as page number
            if prev_is_header or next_is_header:
                is_verse = False
                reason = "adjacent_to_header"
            else:
                # - If we have a current_chapter and this equals expected next verse -> verse
                if current_chapter is not None and (n == last_seen_verse + 1 or (last_seen_verse == 0 and n == 1)):
                    is_verse = True
                    reason = "matches_expected_next"
                else:
                    # - If no chapter known but next line is long verse-like text, treat as verse start (start-of-file edge)
                    next_len = len(next_line) if next_line else 0
                    next_looks_like_text = bool(next_line and not numeric_only_re.match(next_line) and not is_header_line(next_line) and next_len > 6)
                    # allow small jumps (e.g., last_seen_verse==0 but number==1)
                    small_jump_allowed = (current_chapter is not None and n <= last_seen_verse + 3)
                    if next_looks_like_text and (small_jump_allowed or last_seen_verse == 0 and n == 1):
                        is_verse = True
                        reason = "context_next_looks_like_text"
                    else:
                        is_verse = False
                        reason = "default_page"

            if is_verse:
                # insert the verse number token into chapter buffer so flush function will find it
                chapter_buffer.append(f"{n} ")
                # update last_seen_verse now (helps for subsequent numeric-only lines)
                last_seen_verse = n
            else:
                ambiguous.append({
                    "index": i,
                    "line": s,
                    "prev": prev_line,
                    "next": next_line,
                    "reason": reason
                })
            continue  # processed numeric-only line, go to next

        # 6) Non-numeric content line: clean minimal junk but keep text (we will strip punctuation later)
        # Remove stray inline parentheses fragments that might be cross-refs
        s = parenthetical_re.sub("", s)
        s = tag_re.sub("", s)
        # Append to chapter buffer
        chapter_buffer.append(s)

    # done scanning lines -> flush last chapter buffer
    flush_chapter_buffer()

    # Save Excel
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["Book", "ChapterVerse", "Text"])
    df.to_excel(output_file_excel, index=False)

    print(f"Saved Excel -> {output_file_excel}")


if __name__ == "__main__":
    clean_hiligaynon_bible()