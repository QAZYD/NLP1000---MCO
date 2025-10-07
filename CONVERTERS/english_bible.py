import re
from pathlib import Path
import pandas as pd

# Base directory (the folder where this script is located)
base_dir = Path(__file__).resolve().parent

# Input/output paths
input_file = base_dir.parent / "RAW_FILES" / "english_bible.txt"
output_file_excel = base_dir.parent / "CONVERTED_FILES" / "english_bible_cleaned.xlsx"
output_file_sentences = base_dir.parent / "CONVERTED_FILES" / "english_sentences.txt"

def clean_english_bible():
    rows = []
    sentence_lines = []

    # Regex patterns
    remove_tags_re = re.compile(r"<[^>]+>")
    remove_punct_re = re.compile(r"[^\w\s]")
    remove_extra_spaces = re.compile(r"\s+")
    sentence_split_re = re.compile(r'(?<=[.!?])\s+')  # split on ., ?, ! followed by space

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

            # Split into sentences before punctuation removal
            raw_sentences = sentence_split_re.split(text)

            cleaned_sentences = []
            for s in raw_sentences:
                s = remove_punct_re.sub("", s)  # remove punctuation
                s = remove_extra_spaces.sub(" ", s).strip()
                if s:
                    cleaned_sentences.append(s)
                    sentence_lines.append(s)

            # Join cleaned sentences for Excel output
            text_cleaned = " ".join(cleaned_sentences)

            # Store data for Excel
            rows.append({
                "Book": book,
                "Chapter": chapter,
                "Verse": verse,
                "Text": text_cleaned
            })

    # --- Save Excel ---
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["Book", "Chapter", "Verse", "Text"])
    df.to_excel(output_file_excel, index=False)

    # --- Save Sentences File ---
    with open(output_file_sentences, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(sentence_lines))

    print(f"Excel file saved -> {output_file_excel}")
    print(f"Sentence file saved -> {output_file_sentences}")

if __name__ == "__main__":
    clean_english_bible()
