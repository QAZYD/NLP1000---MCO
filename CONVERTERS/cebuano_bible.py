import pandas as pd
from pathlib import Path

# File paths
base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "cebuano_bible.txt"
output_file = base_dir / "CONVERTED_FILES" / "cebuano_bible_cleaned.xlsx"

# Map book IDs to names
book_map = {
    "40N": "Matthew",
    "41N": "Mark",
    "42N": "Luke"
}

verses_data = []

# Read and parse
with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) < 4:
            continue  # skip malformed lines
        book_id, chapter, verse, text = parts[0], parts[1], parts[2], parts[3]
        book_name = book_map.get(book_id, "Unknown")
        chapter_verse = f"{chapter}:{verse}"
        verses_data.append({
            "Book": book_name,
            "ChapterVerse": chapter_verse,
            "Text": text
        })

# Save to Excel
df = pd.DataFrame(verses_data)
output_file.parent.mkdir(parents=True, exist_ok=True)
df.to_excel(output_file, index=False)

print(f"Saved cleaned Excel to: {output_file}")
