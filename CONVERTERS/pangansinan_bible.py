import re
from pathlib import Path
import pandas as pd

base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "chavacano_bible.txt"
cleaned_output = base_dir / "CONVERTED_FILES" / "pangansinan_bible_cleaned.txt"
final_output = base_dir / "CONVERTED_FILES" / "pangansinan_bible_final.txt"
excel_output = base_dir / "CONVERTED_FILES" / "pangansina_bible.xlsx"

def clean_text(in_file, out_file):
    cleaned_lines = []

    # Match lines that contain only "Mateo", "Marcos", or "Lucas" with optional numbers/commas
    book_pattern = re.compile(r"^\s*\d*\s*(Mateo|Marcos|Lucas)(?:[\s\d,]*)$")

    # Match the copyright/source line (with or without final period)
    copyright_pattern = re.compile(
        r"^The New Testament in Chavacano of the Philippines;.*Wycliffe Bible Translators, Inc\.?$"
    )

    # Regex to split verses: handles digits with optional letters, at start or mid-line
    verse_splitter = re.compile(r"(?=\b\d+[A-Za-z]*)")

    with open(in_file, "r", encoding="utf-8") as infile:
        for line in infile:
            stripped = line.strip()

            # Skip headers for Mateo, Marcos, or Lucas
            if book_pattern.match(stripped):
                continue
            # Skip copyright/source notes
            if copyright_pattern.match(stripped):
                continue

            if stripped:
                # Split the line into verses
                parts = verse_splitter.split(stripped)
                for part in parts:
                    if part.strip():
                        cleaned_lines.append(part.strip())

    with open(out_file, "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(cleaned_lines))


def prepare_final(in_file, out_file):
    """
    Merge lines for each verse so that each verse is on one line.
    Fix nC → n C.
    Convert lone chapter numbers to prefix verses as chapter:verse.
    Also creates an Excel file with book, chapter:verse, sentence.
    """
    verse_start = re.compile(r"^\s*(\d+[A-Z]?)\s*")  # detect verse numbers
    final_lines = []
    current_verse = None
    current_chapter = None

    with open(in_file, "r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()
            if not line:
                continue

            # Fix nC → n C anywhere in the line
            line = re.sub(r"(\d)([A-Z])", r"\1 \2", line)

            # Check if the line is a lone chapter number
            if line.isdigit():
                current_chapter = line
                continue

            # Check if the line starts with a verse number
            m = verse_start.match(line)
            if m:
                verse_number = m.group(1)
                # prepend chapter if known
                if current_chapter:
                    line = f"{current_chapter}:{verse_number} " + line[m.end():].lstrip()
                # save previous verse
                if current_verse:
                    final_lines.append(current_verse.strip())
                current_verse = line
            else:
                if current_verse:
                    current_verse += " " + line
                else:
                    current_verse = line

        # Save last verse
        if current_verse:
            final_lines.append(current_verse.strip())

    # Write cleaned final text
    with open(out_file, "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(final_lines))

    # --- Create Excel file ---
    data = []
    book_list = ["Mateo", "Marcos", "Lucas"]
    book_index = 0
    current_book = book_list[book_index]
    last_chapter = None  # track previous chapter to detect reset

    for line in final_lines:
        # Extract chapter:verse prefix
        m = re.match(r"^(\d+):(\d+)", line)
        if m:
            chapter, verse = m.groups()
            sentence = line[m.end():].strip()

            # Detect new book: chapter goes back to 1 after the first book
            if last_chapter is not None and chapter == "1" and last_chapter != "1":
                if book_index + 1 < len(book_list):
                    book_index += 1
                    current_book = book_list[book_index]

            last_chapter = chapter
            ref = f"{chapter}:{verse}"
            data.append([current_book, ref, sentence])
        else:
            # If no verse prefix, just add as is
            data.append([current_book, "", line])

    # Save to Excel
    excel_path = out_file.with_suffix(".xlsx")
    df = pd.DataFrame(data, columns=["book", "chapter:verse", "sentence"])
    df.to_excel(excel_path, index=False)

# Execute sequentially
clean_text(input_file, cleaned_output)
prepare_final(cleaned_output, final_output)
