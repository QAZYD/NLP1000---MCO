import re
import pandas as pd
from pathlib import Path

def clean_text(text: str) -> str:
    """Clean text by removing tags, brackets, extra spaces, duplicates, and unwanted symbols."""
    text = re.sub(r"<.*?>", "", text)  # remove tags
    text = re.sub(r"\[.*?\]", "", text)  # remove brackets
    text = re.sub(r"\s+", " ", text).strip()  # normalize spaces
    text = re.sub(r"\b(\w+)( \1\b)+", r"\1", text, flags=re.IGNORECASE)  # remove duplicates
    text = re.sub(r"[^a-zA-Z0-9À-ž\s.,;:!?-]", "", text)  # remove weird symbols
    text = re.sub(r"[.,;:!?-]+$", "", text)  # remove trailing punctuation
    return text

def remove_punctuation(text: str) -> str:
    """Remove all punctuation, keeping only letters, numbers, and spaces."""
    return re.sub(r"[^\w\sÀ-ž]", "", text)

# File paths
base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "tagalog_bible.txt"
cleaned_output_excel = base_dir / "CONVERTED_FILES" / "tagalog_bible_cleaned.xlsx"
cleaned_output_txt = base_dir / "CONVERTED_FILES" / "tagalog_sentences.txt"

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
            "Chapter": chapter,
            "Verse": verse,
            "Text": text
        })

# Create DataFrame
df_cleaned = pd.DataFrame(verses_data)

# Save Excel
cleaned_output_excel.parent.mkdir(parents=True, exist_ok=True)
df_cleaned.to_excel(cleaned_output_excel, index=False)

# Create plain text sentences (no punctuation)
sentences = [remove_punctuation(t["Text"]) for t in verses_data if t["Text"].strip()]

# Write clean sentences to TXT file (one per line)
with open(cleaned_output_txt, "w", encoding="utf-8") as f:
    for sentence in sentences:
        f.write(sentence + "\n")

print(f"Done! Cleaned Excel saved at: {cleaned_output_excel}")
print(f"Sentences TXT saved at: {cleaned_output_txt}")
