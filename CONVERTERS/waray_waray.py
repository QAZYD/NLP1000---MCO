import re
from pathlib import Path
import pandas as pd

def clean_bible_text_to_excel():
    input_file = Path("RAW_FILES/waray_waray_bible.txt")
    output_file_excel = Path("CONVERTED_FILES/waray_waray_bible_cleaned.xlsx")
    output_file_sentences = Path("CONVERTED_FILES/waray_waray_sentences.txt")

    current_book = None
    current_chapter = None
    rows = []
    sentences = []
    verse_block = ""

    def process_verse_block(block, book, chapter):
        if not block or not block.strip():
            return
        sblock = block.strip()

        # Handle ranges like 2-6a, 6b-11, 12-16
        range_match = re.match(r"^(\d+)([ab]?)-(\d+)([ab]?)(.*)", sblock)
        if range_match:
            start, start_letter, end, end_letter, verse_text = range_match.groups()
            start, end = int(start), int(end)
            verse_text = (verse_text or "").strip()
            for v in range(start, end + 1):
                rows.append({"Book": book, "Chapter": chapter, "Verse": v, "Sentence": verse_text})
                sentences.append(verse_text)
            return

        # Single-lettered verse like 6a / 6b
        lettered_match = re.match(r"^(\d+)([a-zA-Z])\s*(.*)", sblock)
        if lettered_match:
            num, letter, verse_text = lettered_match.groups()
            verse_text = (verse_text or "").strip()
            # ✅ Move the letter into the sentence
            full_sentence = f"{letter} {verse_text}".strip()
            rows.append({"Book": book, "Chapter": chapter, "Verse": num, "Sentence": full_sentence})
            sentences.append(full_sentence)
            return

        # Normal single verse
        number_match = re.match(r"^(\d+)\s*(.*)", sblock)
        if number_match:
            v, verse_text = number_match.groups()
            verse_text = (verse_text or "").strip()
            rows.append({"Book": book, "Chapter": chapter, "Verse": v, "Sentence": verse_text})
            sentences.append(verse_text)
            return

        # Fallback
        rows.append({"Book": book, "Chapter": chapter, "Verse": "", "Sentence": sblock})
        sentences.append(sblock)

    # === Read & parse ===
    with open(input_file, "r", encoding="utf-8") as infile:
        for raw in infile:
            stripped = raw.strip()
            if not stripped:
                continue

            if stripped.isdigit():
                continue

            # Remove parenthetical refs
            no_refs = re.sub(r"\([^)]*\)", "", stripped)
            no_punct = no_refs.strip()

            # Detect book+chapter lines
            book_chapter_match = re.match(r"^(Mateo|Lucas|Marcos)\s+(\d+)", no_punct)
            if book_chapter_match:
                if verse_block:
                    process_verse_block(verse_block, current_book, current_chapter)
                verse_block = ""
                current_book, current_chapter = book_chapter_match.groups()
                continue

            # Start of a new verse
            if re.match(r"^\d", no_punct):
                if verse_block:
                    process_verse_block(verse_block, current_book, current_chapter)
                verse_block = no_punct
            else:
                verse_block += " " + no_punct

    # Process leftover block
    if verse_block:
        process_verse_block(verse_block, current_book, current_chapter)

    # === Normalize before Excel ===
    normalized = []
    for r in rows:
        book = r.get("Book", "") or ""
        sentence = r.get("Sentence", "") or ""
        chap = r.get("Chapter", "")
        verse = r.get("Verse", "")

        if isinstance(verse, str) and ":" in verse:
            parts = verse.split(":", 1)
            if parts:
                if not chap:
                    chap = parts[0]
                verse = parts[1]

        normalized.append({
            "Book": str(book),
            "Chapter": str(chap),
            "Verse": str(verse),
            "Sentence": str(sentence)
        })

    # Ensure output folder exists
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)

    # Save Excel
    df = pd.DataFrame(normalized, columns=["Book", "Chapter", "Verse", "Sentence"])
    df.to_excel(output_file_excel, index=False)

    # Save sentences
    with open(output_file_sentences, "w", encoding="utf-8") as sf:
        for s in sentences:
            sf.write((s or "").strip() + "\n")

    print(f"Saved Excel -> {output_file_excel}")
    print(f"Saved sentences -> {output_file_sentences}")

# Run
clean_bible_text_to_excel()
