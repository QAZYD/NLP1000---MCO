import re
from pathlib import Path
import pandas as pd

# Input/output paths
input_file = Path("../RAW_FILES/spanish_bible.txt")
output_file_txt = Path("../CONVERTED_FILES/spanish_cleaned.txt")
output_file_excel = Path("../CONVERTED_FILES/spanish_bible_cleaned.xlsx")


def clean_spanish_bible():
    books_order = ["Mathew", "Mark", "Luke"]
    book_index = 0
    current_book = books_order[book_index]

    last_chapter = 0
    rows = []
    cleaned_lines = []

    # Patterns
    line_re = re.compile(r"^(\d+):(\d+)\s+(.*)$")
    remove_tags_re = re.compile(r"<[^>]+>")
    remove_punct_re = re.compile(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ]')
    remove_extra_spaces = re.compile(r'\s+')

    with open(input_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            m = line_re.match(line)
            if not m:
                continue  # skip malformed lines

            chapter, verse, text = m.groups()
            chapter, verse = int(chapter), int(verse)

            # --- Detect book change ---
            if chapter == 1 and verse == 1:
                if last_chapter != 0:
                    book_index += 1
                    if book_index < len(books_order):
                        current_book = books_order[book_index]
                    else:
                        current_book = f"UnknownBook{book_index+1}"

            last_chapter = chapter

            # --- Cleaning ---
            text = remove_tags_re.sub("", text)
            text = remove_punct_re.sub("", text)
            text = remove_extra_spaces.sub(" ", text).strip()

            # Save cleaned line
            cleaned_lines.append(f"{current_book}|{chapter}|{verse}|{text}")

            # Save row for Excel
            rows.append({
                "Book": current_book,
                "ChapterVerse": f"{chapter}:{verse}",
                "Text": text
            })

    # --- Save Excel ---
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["Book", "ChapterVerse", "Text"])
    df.to_excel(output_file_excel, index=False)
    
    print(f"Excel file saved -> {output_file_excel}")


if __name__ == "__main__":
    clean_spanish_bible()
