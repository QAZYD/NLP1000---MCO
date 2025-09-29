import re
import pandas as pd
from pathlib import Path

def clean_text(text: str) -> str:
    text = re.sub(r"<.*?>", "", text)  # remove tags
    text = re.sub(r"\[.*?\]", "", text)  # remove brackets
    text = re.sub(r"\s+", " ", text).strip()  # normalize spaces
    text = re.sub(r"\b(\w+)( \1\b)+", r"\1", text, flags=re.IGNORECASE)  # remove duplicates
    text = re.sub(r"[^a-zA-Z0-9À-ž\s.,;:!?-]", "", text)  # remove weird symbols
    text = re.sub(r"[.,;:!?-]+$", "", text)  # remove trailing punctuation
    return text

# File paths
base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "tagalog_bible.txt"
cleaned_output = base_dir / "CONVERTED_FILES" / "tagalog_bible_cleaned.xlsx"

# Read input
with open(input_file, "r", encoding="utf-8") as f:
    lines = [ln.strip() for ln in f if ln.strip()]

# Track verses
verses_data = []
book_order = ["Matthew", "Mark", "Luke"]
current_book_index = 0
current_book = book_order[current_book_index]
last_chapter = 0

for ln in lines:
    m = re.match(r"(\d+):(\d+)\s+(.*)", ln)
    if m:
        chapter = int(m.group(1))
        verse = int(m.group(2))
        text = clean_text(m.group(3))

        # Detect chapter reset → switch book
        if chapter == 1 and last_chapter > 1:
            current_book_index += 1
            if current_book_index < len(book_order):
                current_book = book_order[current_book_index]
        last_chapter = chapter

        verses_data.append({
            "Book": current_book,
            "ChapterVerse": f"{chapter}:{verse}",
            "Text": text
        })

# Save only cleaned dataframe
df_cleaned = pd.DataFrame(verses_data)
cleaned_output.parent.mkdir(parents=True, exist_ok=True)
df_cleaned.to_excel(cleaned_output, index=False)

print(f"Done! Cleaned Excel saved at: {cleaned_output}")
