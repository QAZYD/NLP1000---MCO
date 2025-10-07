import re
from pathlib import Path
import pandas as pd

base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "chavacano_bible.txt"
excel_output = base_dir / "CONVERTED_FILES" / "chavacano_bible_cleaned.xlsx"
sentences_output = base_dir / "CONVERTED_FILES" / "chavacano_sentences.txt"

def clean_and_convert_bible(in_file, excel_out, sentences_out):
    # Prepare regex patterns
    book_pattern = re.compile(r"^\s*\d*\s*(Mateo|Marcos|Lucas)(?:[\s\d,]*)$")
    copyright_pattern = re.compile(
        r"^The New Testament in Chavacano of the Philippines;.*Wycliffe Bible Translators, Inc\.?$"
    )
    verse_splitter = re.compile(r"(?=\b\d+[A-Za-z]*)")  # to detect verse numbers

    cleaned_lines = []
    current_chapter = None

    # --- Phase 1: read and split into verses ---
    with open(in_file, "r", encoding="utf-8") as infile:
        for line in infile:
            stripped = line.strip()
            if not stripped:
                continue
            if book_pattern.match(stripped):
                continue
            if copyright_pattern.match(stripped):
                continue

            parts = verse_splitter.split(stripped)
            for part in parts:
                if part.strip():
                    cleaned_lines.append(part.strip())

    # --- Phase 2: assemble Book / Chapter / Verse ---
    data = []
    book_list = ["Mateo", "Marcos", "Lucas"]
    book_index = 0
    current_book = book_list[book_index]
    last_chapter = None
    verse_start = re.compile(r"^\s*(\d+[A-Z]?)\s*")

    final_lines = []
    current_verse = None

    for line in cleaned_lines:
        line = line.strip()
        if not line:
            continue

        # Fix nC → n C
        line = re.sub(r"(\d)([A-Z])", r"\1 \2", line)

        # Lone chapter number
        if line.isdigit():
            current_chapter = line
            continue

        # Starts with verse number
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

    # --- Phase 3: clean and structure data ---
    sentences = []
    for line in final_lines:
        m = re.match(r"^(\d+):(\d+)\s*(.*)", line)
        if m:
            chapter, verse, sentence = m.groups()

            # Detect new book by reset to chapter 1
            if last_chapter is not None and chapter == "1" and last_chapter != "1":
                if book_index + 1 < len(book_list):
                    book_index += 1
                    current_book = book_list[book_index]

            last_chapter = chapter

            # Remove punctuation
            sentence = re.sub(r"[^A-Za-z\s]", "", sentence).strip()
            data.append([current_book, chapter, verse, sentence])
            sentences.append(sentence)
        else:
            # No chapter:verse found
            sentence = re.sub(r"[^A-Za-z\s]", "", line).strip()
            data.append([current_book, "", "", sentence])
            sentences.append(sentence)

    # --- Phase 4: write results ---
    excel_out.parent.mkdir(parents=True, exist_ok=True)

    # Save to Excel (Book, Chapter, Verse, Sentence)
    df = pd.DataFrame(data, columns=["Book", "Chapter", "Verse", "Sentence"])
    df.to_excel(excel_out, index=False)

    # Save segmented sentences
    with open(sentences_out, "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(s + "\n")

    print(f"Excel saved to: {excel_out}")
    print(f"Sentences saved to: {sentences_out}")


# Run the cleaner
clean_and_convert_bible(input_file, excel_output, sentences_output)
