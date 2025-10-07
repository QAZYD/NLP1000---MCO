import re
from pathlib import Path
import pandas as pd

def clean_bible_text_to_excel():
    input_file = Path("RAW_FILES/bikolano_bible.txt")
    output_file_excel = Path("CONVERTED_FILES/bikolano_bible_cleaned.xlsx")
    output_file_sentences = Path("CONVERTED_FILES/bikolano_sentences.txt")  # renamed file

    current_verse = ""
    current_book = None
    current_chapter = None
    rows = []
    segmented_sentences = []  # store each full sentence

    with open(input_file, "r", encoding="utf-8") as infile:
        for line in infile:
            stripped = line.strip()
            if not stripped:
                continue

            # --- Delete lines that are just numbers or "Central Bikol" ---
            if stripped.isdigit() or stripped == "Central Bikol":
                continue

            # Remove parentheses (cross references, etc.)
            no_refs = re.sub(r"\([^)]*\)", "", stripped).strip()

            # Detect book+chapter lines (Mateo 1, Lukas 3, etc.)
            book_chapter_match = re.match(r"^(Mateo|Lukas|Markos)\s+(\d+)", no_refs)
            if book_chapter_match:
                # Save previous verse
                if current_verse:
                    verse_num = re.match(r"^(\d+)", current_verse)
                    if verse_num:
                        text = re.sub(r"^\d+\s*", "", current_verse).strip()
                        text = re.sub(r"[^A-Za-z\s]", "", text)
                        rows.append({
                            "Book": current_book,
                            "Chapter": current_chapter,
                            "Verse": verse_num.group(1),
                            "Text": text
                        })
                        segmented_sentences.append(text)
                current_verse = ""
                current_book, current_chapter = book_chapter_match.groups()
                continue

            # Skip non-verse headings
            if not re.match(r"^\d+", no_refs) and not current_verse:
                continue

            # Verse start
            if re.match(r"^\d+", no_refs):
                if current_verse:
                    verse_num = re.match(r"^(\d+)", current_verse)
                    if verse_num:
                        text = re.sub(r"^\d+\s*", "", current_verse).strip()
                        text = re.sub(r"[^A-Za-z\s]", "", text)
                        rows.append({
                            "Book": current_book,
                            "Chapter": current_chapter,
                            "Verse": verse_num.group(1),
                            "Text": text
                        })
                        segmented_sentences.append(text)

                # Handle verse range at start: n-m
                m = re.match(r"^(\d+)-(\d+)(.*)", no_refs)
                if m:
                    n1, n2, verse_text = m.groups()
                    verse_text = verse_text.strip()
                    verse_text = re.sub(r"[^A-Za-z\s]", "", verse_text)
                    rows.append({"Book": current_book, "Chapter": current_chapter, "Verse": n1, "Text": verse_text})
                    rows.append({"Book": current_book, "Chapter": current_chapter, "Verse": n2, "Text": verse_text})
                    segmented_sentences.append(verse_text)
                    current_verse = ""
                else:
                    current_verse = re.sub(r"^(\d+)", r"\1 ", no_refs, count=1)
            else:
                current_verse += " " + no_refs

    # Save last verse
    if current_verse:
        verse_num = re.match(r"^(\d+)", current_verse)
        if verse_num:
            text = re.sub(r"^\d+\s*", "", current_verse).strip()
            text = re.sub(r"[^A-Za-z\s]", "", text)
            rows.append({
                "Book": current_book,
                "Chapter": current_chapter,
                "Verse": verse_num.group(1),
                "Text": text
            })
            segmented_sentences.append(text)

    # Save segmented sentences (each full sentence per line)
    output_file_sentences.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file_sentences, "w", encoding="utf-8") as segfile:
        for s in segmented_sentences:
            segfile.write(s.strip() + "\n")

    # Save to Excel (Book, Chapter, Verse, Text separated)
    df = pd.DataFrame(rows, columns=["Book", "Chapter", "Verse", "Text"])
    df.to_excel(output_file_excel, index=False)

# Run cleaning
clean_bible_text_to_excel()
