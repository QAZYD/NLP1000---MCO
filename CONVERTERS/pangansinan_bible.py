import re
from pathlib import Path
import pandas as pd
import os

# === Paths ===
base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "pangansinan_bible.txt"
excel_output = base_dir / "CONVERTED_FILES" / "pangansinan_bible_cleaned.xlsx"
sentences_output = base_dir / "CONVERTED_FILES" / "pangansinan_sentences.txt"


def clean_and_prepare(in_file):
    cleaned_lines = []
    book_pattern = re.compile(r"^\s*\d*\s*(Mateo|Marcos|Lucas)(?:[\s\d,]*)$")
    copyright_pattern = re.compile(
        r"^The New Testament in Chavacano of the Philippines;.*Wycliffe Bible Translators, Inc\.?$"
    )
    verse_splitter = re.compile(r"(?=\b\d+[A-Za-z]*)")

    # --- Cleaning phase ---
    with open(in_file, "r", encoding="utf-8") as infile:
        for line in infile:
            stripped = line.strip()
            if not stripped:
                continue
            if book_pattern.match(stripped) or copyright_pattern.match(stripped):
                continue

            parts = verse_splitter.split(stripped)
            for part in parts:
                if part.strip():
                    cleaned_lines.append(part.strip())

    # --- Verse assembly phase ---
    verse_start = re.compile(r"^\s*(\d+[A-Z]?)\s*")
    final_lines = []
    current_verse = None
    current_chapter = None

    for line in cleaned_lines:
        line = re.sub(r"(\d)([A-Z])", r"\1 \2", line)  # Fix nC → n C
        if line.isdigit():
            current_chapter = line
            continue

        m = verse_start.match(line)
        if m:
            verse_number = m.group(1)
            if current_chapter:
                line = f"{current_chapter}:{verse_number} " + line[m.end():].lstrip()
            if current_verse:
                final_lines.append(current_verse.strip())
            current_verse = line
        else:
            if current_verse:
                current_verse += " " + line
            else:
                current_verse = line
    if current_verse:
        final_lines.append(current_verse.strip())

    return final_lines


def generate_excel_and_sentences(final_lines, excel_path, sentences_path):
    data = []
    book_list = ["Mateo", "Marcos", "Lucas"]
    book_index = 0
    current_book = book_list[book_index]
    last_chapter = None

    all_sentences = []

    for line in final_lines:
        m = re.match(r"^(\d+):(\d+)", line)
        if m:
            chapter, verse = m.groups()
            sentence = line[m.end():].strip()

            if last_chapter is not None and chapter == "1" and last_chapter != "1":
                if book_index + 1 < len(book_list):
                    book_index += 1
                    current_book = book_list[book_index]

            last_chapter = chapter
            data.append([current_book, chapter, verse, sentence])

            # Split into smaller sentence-like fragments
            parts = re.split(r"(?<=[.!?])\s+", sentence)
            for p in parts:
                if p.strip():
                    all_sentences.append(p.strip())
        else:
            data.append([current_book, "", "", line])
            all_sentences.append(line.strip())

    # Save Excel file with separate columns
    df = pd.DataFrame(data, columns=["book", "chapter", "verse", "sentence"])
    df.to_excel(excel_path, index=False)

    # Save segmented sentences
    with open(sentences_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sentences))


def main():
    final_lines = clean_and_prepare(input_file)
    generate_excel_and_sentences(final_lines, excel_output, sentences_output)

    # Delete all other .txt files in CONVERTED_FILES except the sentences file
    for f in (base_dir / "CONVERTED_FILES").glob("*.txt"):
        if f != sentences_output:
            try:
                os.remove(f)
            except Exception:
                pass


if __name__ == "__main__":
    main()
