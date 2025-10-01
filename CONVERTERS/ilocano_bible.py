import re
from pathlib import Path
import pandas as pd

def clean_bible_text_to_excel():
    input_file = Path("RAW_FILES/ilocano_bible.txt")
    output_file_txt = Path("CONVERTED_FILES/ilocano_cleaned.txt")
    output_file_excel = Path("CONVERTED_FILES/ilocano_bible_cleaned.xlsx")

    cleaned_lines = []
    current_book = None
    current_chapter = None
    rows = []

    verse_block = ""

    def process_verse_block(block, book, chapter):
        """Process a full verse block (may contain ranges or 6a/6b)."""
        if not block.strip():
            return

        block = block.strip()

        # Handle ranges like 2-6a, 6b-11, 12-16
        range_match = re.match(r"^(\d+)([ab]?)-(\d+)([ab]?)(.*)", block)
        if range_match:
            start, start_letter, end, end_letter, verse_text = range_match.groups()
            start, end = int(start), int(end)
            verse_text = verse_text.strip()

            # Special handling for verse 6
            if start <= 6 <= end:
                for v in range(start, end + 1):
                    if v == 6:
                        if start_letter == 'a' or end_letter == 'a':
                            cleaned_lines.append(f"6a {verse_text}")
                            rows.append({"Book": book, "Verse": f"{chapter}:6a", "Sentence": verse_text})
                        if start_letter == 'b' or end_letter == 'b':
                            cleaned_lines.append(f"6b {verse_text}")
                            rows.append({"Book": book, "Verse": f"{chapter}:6b", "Sentence": verse_text})
                    else:
                        cleaned_lines.append(f"{v} {verse_text}")
                        rows.append({"Book": book, "Verse": f"{chapter}:{v}", "Sentence": verse_text})
            else:
                for v in range(start, end + 1):
                    cleaned_lines.append(f"{v} {verse_text}")
                    rows.append({"Book": book, "Verse": f"{chapter}:{v}", "Sentence": verse_text})
            return

        # Handle single lettered verse like 6a/6b
        lettered_match = re.match(r"^(\d+[a-z])(.*)", block)
        if lettered_match:
            v, verse_text = lettered_match.groups()
            verse_text = verse_text.strip()
            cleaned_lines.append(f"{v} {verse_text}")
            rows.append({"Book": book, "Verse": f"{chapter}:{v}", "Sentence": verse_text})
            return

        # Normal single verse with number
        number_match = re.match(r"^(\d+)\s*(.*)", block)
        if number_match:
            v, verse_text = number_match.groups()
            verse_text = verse_text.strip()
            cleaned_lines.append(f"{v} {verse_text}")
            rows.append({"Book": book, "Verse": f"{chapter}:{v}", "Sentence": verse_text})

    with open(input_file, "r", encoding="utf-8") as infile:
        for line in infile:
            stripped = line.strip()
            if not stripped:
                continue

            # Skip lines that are only numbers
            if stripped.isdigit():
                continue

            # Remove parentheses
            no_refs = re.sub(r"\([^)]*\)", "", stripped).strip()

            # Detect book+chapter lines
            book_chapter_match = re.match(r"^(San Mateo|San Lucas|San Marcos)\s+(\d+)", no_refs)
            if book_chapter_match:
                if verse_block:
                    process_verse_block(verse_block, current_book, current_chapter)
                verse_block = ""
                current_book, current_chapter = book_chapter_match.groups()
                cleaned_lines.append(no_refs)
                continue

            # Start of a new verse
            if re.match(r"^\d", no_refs):
                if verse_block:
                    process_verse_block(verse_block, current_book, current_chapter)
                verse_block = no_refs
            else:
                # Continuation of previous verse
                verse_block += " " + no_refs

    # Process any remaining block
    if verse_block:
        process_verse_block(verse_block, current_book, current_chapter)

    # Save cleaned text
    output_file_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file_txt, "w", encoding="utf-8") as outfile:
        for line in cleaned_lines:
            outfile.write(line + "\n")

    # Save to Excel
    df = pd.DataFrame(rows, columns=["Book", "Verse", "Sentence"])
    df.to_excel(output_file_excel, index=False)

# Run cleaning
clean_bible_text_to_excel()
