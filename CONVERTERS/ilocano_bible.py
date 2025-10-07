import re
from pathlib import Path
import pandas as pd

def clean_bible_text_to_excel():
    # keep original paths
    input_file = Path("RAW_FILES/ilocano_bible.txt")
    output_file_excel = Path("CONVERTED_FILES/ilocano_bible_cleaned.xlsx")
    output_file_sentences = Path("CONVERTED_FILES/ilocano_sentences.txt")

    current_book = None
    current_chapter = None
    rows = []
    sentences = []
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
            for v in range(start, end + 1):
                verse_label = f"{v}"
                if v == 6 and (start_letter or end_letter):
                    if start_letter == 'a' or end_letter == 'a':
                        verse_label = "6a"
                    elif start_letter == 'b' or end_letter == 'b':
                        verse_label = "6b"

                rows.append({"Book": book, "Verse": f"{chapter}:{verse_label}", "Sentence": verse_text})
                split_sentences(verse_text)
            return

        # Handle single lettered verse like 6a/6b
        lettered_match = re.match(r"^(\d+[a-z])(.*)", block)
        if lettered_match:
            v, verse_text = lettered_match.groups()
            verse_text = verse_text.strip()
            rows.append({"Book": book, "Verse": f"{chapter}:{v}", "Sentence": verse_text})
            split_sentences(verse_text)
            return

        # Normal single verse with number
        number_match = re.match(r"^(\d+)\s*(.*)", block)
        if number_match:
            v, verse_text = number_match.groups()
            verse_text = verse_text.strip()
            rows.append({"Book": book, "Verse": f"{chapter}:{v}", "Sentence": verse_text})
            split_sentences(verse_text)

    def split_sentences(text):
        """Split verse text into sentences and add them to the list."""
        clean_text = re.sub(r"[^\w\s.!?]", "", text)
        for sentence in re.split(r'[.!?]', clean_text):
            s = sentence.strip()
            if s:
                sentences.append(s)

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

            # Detect book + chapter lines
            book_chapter_match = re.match(r"^(San Mateo|San Lucas|San Marcos)\s+(\d+)", no_refs)
            if book_chapter_match:
                if verse_block:
                    process_verse_block(verse_block, current_book, current_chapter)
                verse_block = ""
                current_book, current_chapter = book_chapter_match.groups()
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

    # --- Save Excel ---
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["Book", "Verse", "Sentence"])
    df.to_excel(output_file_excel, index=False)

    # --- Save sentences file ---
    with open(output_file_sentences, "w", encoding="utf-8") as sfile:
        for s in sentences:
            sfile.write(s + "\n")

    print(f"Excel file saved -> {output_file_excel}")
    print(f"Sentences file saved -> {output_file_sentences}")

if __name__ == "__main__":
    clean_bible_text_to_excel()
