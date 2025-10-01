import re
from pathlib import Path
import pandas as pd

# Input/output paths
input_file = Path("../RAW_FILES/english_bible.txt")
output_file_txt = Path("../CONVERTED_FILES/english_cleaned.txt")
output_file_excel = Path("../CONVERTED_FILES/english_bible_cleaned.xlsx")


def clean_english_bible():

    rows = []
    cleaned_lines = []

    # Patterns for cleaning
    remove_tags_re = re.compile(r"<[^>]+>")
    remove_punct_re = re.compile(r'[^\w\s]')
    remove_extra_spaces = re.compile(r'\s+')

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Split the pipe-delimited fields
            parts = line.split("|")
            if len(parts) < 4:
                continue  # skip malformed lines

            book, chapter, verse, text = parts[:4]

            # --- Cleaning ---
            text = text.replace("~", "")
            text = remove_tags_re.sub("", text)
            text = remove_punct_re.sub("", text)
            text = remove_extra_spaces.sub(" ", text).strip()

            # Save to cleaned text file
            cleaned_lines.append(f"{book}|{chapter}|{verse}|{text}")

            # Save row for Excel
            rows.append({
                "Book": book,
                "ChapterVerse": f"{chapter}:{verse}",
                "Text": text
            })

    # --- Save Excel ---
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["Book", "ChapterVerse", "Text"])
    df.to_excel(output_file_excel, index=False)

    print(f"Excel file saved -> {output_file_excel}")


if __name__ == "__main__":
    clean_english_bible()
