import re
from pathlib import Path
import pandas as pd

# Define input/output file paths here
input_file = Path("../RAW_FILES/maranao.txt")
output_file_txt = Path("../CONVERTED_FILES/maranao_cleaned.txt")
output_file_excel = Path("../CONVERTED_FILES/maranao_bible_cleaned.xlsx")


def clean_maranao_bible():

    # State tracking
    current_book = None
    current_chapter = None
    current_verse_num = None
    current_verse_text = ""
    saw_new_chapter = False

    cleaned_lines = []
    rows = []

    # Regex patterns
    book_chapter_re = re.compile(r"^(MATIYO|MARKO|LOKAS)\s+(\d+)\b", re.IGNORECASE)
    verse_range_re = re.compile(r"^(\d+)-(\d+)\s*(.*)$")
    verse_start_re = re.compile(r"^(\d+)(?:[\.:])?\s*(.*)$")
    remove_paren_re = re.compile(r"\([^)]*\)")      # remove parentheses
    remove_tags_re = re.compile(r"<[^>]+>")         # remove XML/HTML tags
    remove_punct_re = re.compile(r'[.,:;!?\"“”]')   # remove punctuation

    with open(input_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            # --- Cleaning ---
            text = remove_paren_re.sub("", line)
            text = remove_tags_re.sub("", text)
            text = remove_punct_re.sub("", text)
            text = re.sub(r'\s+', ' ', text).strip()

            if not text:
                continue

            # --- 1) Book + chapter header ---
            m_book = book_chapter_re.match(text)
            if m_book:
                if current_verse_text:
                    cleaned_lines.append(f"{current_verse_num} {current_verse_text.strip()}")
                    rows.append({
                        "Book": current_book,
                        "ChapterVerse": f"{current_chapter}:{current_verse_num}",
                        "Text": current_verse_text.strip()
                    })
                    current_verse_text = ""
                    current_verse_num = None

                book_tok, chap_tok = m_book.groups()
                current_book = book_tok.capitalize()
                current_chapter = chap_tok
                saw_new_chapter = True
                cleaned_lines.append(f"{current_book} {current_chapter}")
                continue

            # --- 2) Handle implicit verse 1 ---
            if saw_new_chapter:
                if not re.match(r"^\d+", text):
                    current_verse_num = "1"
                    current_verse_text = text
                    saw_new_chapter = False
                    continue
                else:
                    saw_new_chapter = False

            # --- 3) Verse ranges ---
            m_range = verse_range_re.match(text)
            if m_range:
                n1, n2, verse_text = m_range.groups()
                verse_text = verse_text.strip()
                if current_verse_text:
                    cleaned_lines.append(f"{current_verse_num} {current_verse_text.strip()}")
                    rows.append({
                        "Book": current_book,
                        "ChapterVerse": f"{current_chapter}:{current_verse_num}",
                        "Text": current_verse_text.strip()
                    })
                    current_verse_text = ""
                    current_verse_num = None

                cleaned_lines.append(f"{n1} {verse_text}")
                cleaned_lines.append(f"{n2} {verse_text}")
                rows.append({"Book": current_book, "ChapterVerse": f"{current_chapter}:{n1}", "Text": verse_text})
                rows.append({"Book": current_book, "ChapterVerse": f"{current_chapter}:{n2}", "Text": verse_text})
                continue

            # --- 4) Normal verse start ---
            m_vs = verse_start_re.match(text)
            if m_vs:
                verse_num, after = m_vs.groups()
                after = after.strip()
                if current_verse_text:
                    cleaned_lines.append(f"{current_verse_num} {current_verse_text.strip()}")
                    rows.append({
                        "Book": current_book,
                        "ChapterVerse": f"{current_chapter}:{current_verse_num}",
                        "Text": current_verse_text.strip()
                    })
                current_verse_num = verse_num
                current_verse_text = after
                continue

            # --- 5) Continuation line ---
            if current_verse_text:
                current_verse_text += " " + text
            else:
                current_verse_num = "1"
                current_verse_text = text

    # --- Final verse ---
    if current_verse_text:
        cleaned_lines.append(f"{current_verse_num} {current_verse_text.strip()}")
        rows.append({
            "Book": current_book,
            "ChapterVerse": f"{current_chapter}:{current_verse_num}",
            "Text": current_verse_text.strip()
        })

    # --- Save Excel ---
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["Book", "ChapterVerse", "Text"])
    df.to_excel(output_file_excel, index=False)

    print(f"Excel file saved -> {output_file_excel}")


# Run cleaning
if __name__ == "__main__":
    clean_maranao_bible()
