import re
import pandas as pd
from pathlib import Path

# === BASE DIRECTORIES ===
base_dir = Path(__file__).resolve().parent.parent  # project root
input_file = base_dir / "RAW_FILES" / "spanish_bible.txt"
output_folder = base_dir / "CONVERTED_FILES"
output_folder.mkdir(parents=True, exist_ok=True)

excel_path = output_folder / "spanish_bible_cleaned.xlsx"
txt_path = output_folder / "spanish_by_sentence.txt"  # <-- fixed

def remove_punctuation(text: str) -> str:
    return re.sub(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ]", "", text)

def clean_spanish_bible():
    verse_rows = []
    all_sentences = []

    line_re = re.compile(r"^(\d+):(\d+)\s+(.*)$")

    # Book tracking
    book_order = ["Matthew", "Mark", "Luke"]
    current_book_index = 0
    current_book = book_order[current_book_index]
    last_chapter = 0

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            m = line_re.match(line)
            if not m:
                continue

            chapter, verse, text = m.groups()
            chapter = int(chapter)
            verse = int(verse)

            # Detect chapter reset → new book
            if chapter == 1 and last_chapter > 1:
                current_book_index += 1
                if current_book_index < len(book_order):
                    current_book = book_order[current_book_index]

            last_chapter = chapter

            # Remove punctuation and normalize spaces
            text = remove_punctuation(text)
            text = re.sub(r"\s+", " ", text).strip()

            # Only save if chapter and verse exist
            if chapter and verse:
                verse_rows.append({
                    "Book": current_book,
                    "Chapter": chapter,
                    "Verse": verse,
                    "Text": text
                })
                all_sentences.append(text)

    # Save Excel by verse
    df = pd.DataFrame(verse_rows)
    df.to_excel(excel_path, index=False)
    print(f"Saved Excel -> {excel_path}")

    # Save sentences TXT (1 per line)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sentences))
    print(f"Saved Sentences TXT -> {txt_path}")


if __name__ == "__main__":
    clean_spanish_bible()
