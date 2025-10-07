import re
import pandas as pd
from pathlib import Path

# File paths
base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "cebuano_bible.txt"
output_excel = base_dir / "CONVERTED_FILES" / "cebuano_bible_cleaned.xlsx"
output_segmented = base_dir / "CONVERTED_FILES" / "cebuano_segmented.txt"

# Map book IDs to names
book_map = {
    "40N": "Matthew",
    "41N": "Mark",
    "42N": "Luke"
}

verses_data = []
segmented_sentences = []

# Read and parse the input file
with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) < 4:
            continue  # skip malformed lines

        book_id, chapter, verse, text = parts[0], parts[1], parts[2], parts[3]
        book_name = book_map.get(book_id, "Unknown")

        # --- Remove punctuation, keep only letters and spaces ---
        text_cleaned = re.sub(r"[^A-Za-z\s]", "", text)

        # Add to main list
        verses_data.append({
            "Book": book_name,
            "Chapter": chapter,
            "Verse": verse,
            "Text": text_cleaned.strip()
        })

        # --- Sentence segmentation ---
        # Split by sentence-ending punctuation (., ?, !) before cleaning
        for sentence in re.split(r"[.!?]+", text):
            sentence = sentence.strip()
            if sentence:
                # Clean punctuation from each sentence
                sentence_cleaned = re.sub(r"[^A-Za-z\s]", "", sentence)
                segmented_sentences.append(sentence_cleaned.strip())

# --- Save cleaned data to Excel ---
df = pd.DataFrame(verses_data, columns=["Book", "Chapter", "Verse", "Text"])
output_excel.parent.mkdir(parents=True, exist_ok=True)
df.to_excel(output_excel, index=False)

# --- Save segmented sentences to text file ---
with open(output_segmented, "w", encoding="utf-8") as seg_file:
    for s in segmented_sentences:
        seg_file.write(s + "\n")

print(f"Cleaned Excel saved to: {output_excel}")
print(f"Segmented sentences saved to: {output_segmented}")
