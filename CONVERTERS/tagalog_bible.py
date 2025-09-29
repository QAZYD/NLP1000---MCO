import re
import pandas as pd
from pathlib import Path

def clean_text(text: str) -> str:
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b(\w+)( \1\b)+", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"[^a-zA-Z0-9À-ž\s.,;:!?-]", "", text)
    text = re.sub(r"[.,;:!?-]+$", "", text)
    return text

base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "tagalog_bible.txt"
original_output = base_dir / "CONVERTED_FILES" / "tagalog_bible_original.xlsx"
cleaned_output = base_dir / "CONVERTED_FILES" / "tagalog_bible_cleaned.xlsx"

with open(input_file, "r", encoding="utf-8") as f:
    lines = [ln.strip() for ln in f if ln.strip()]

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
        text = m.group(3)

        # Detect chapter reset → change book
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

# Original dataframe
df_original = pd.DataFrame(verses_data)

# Cleaned dataframe
df_cleaned = df_original.copy()
df_cleaned["Text"] = df_cleaned["Text"].apply(clean_text)

# Save
original_output.parent.mkdir(parents=True, exist_ok=True)
df_original.to_excel(original_output, index=False)
df_cleaned.to_excel(cleaned_output, index=False)

print(f"Done! Saved:\n- {original_output}\n- {cleaned_output}")
