import re
import pandas as pd
from pathlib import Path

def clean_text(text: str) -> str:
    # 1. Remove document tags like <...> or [...]
    text = re.sub(r"<.*?>", "", text)     # remove <tags>
    text = re.sub(r"\[.*?\]", "", text)   # remove [tags]

    # 2. Remove unnecessary spaces
    text = re.sub(r"\s+", " ", text).strip()

    # 3. Remove duplicated consecutive words (case-insensitive)
    text = re.sub(r"\b(\w+)( \1\b)+", r"\1", text, flags=re.IGNORECASE)

    # 4. Remove unrelated symbols (keep only letters, digits, punctuation, and spaces)
    text = re.sub(r"[^a-zA-Z0-9À-ž\s.,;:!?-]", "", text)

    # 5. Remove punctuation at the END of the string
    text = re.sub(r"[.,;:!?-]+$", "", text)

    return text


# Define folder structure
base_dir = Path(__file__).resolve().parent.parent
input_file = base_dir / "RAW_FILES" / "tagalog_bible.txt"
original_output = base_dir / "CONVERTED_FILES" / "tagalog_bible_original.xlsx"
cleaned_output = base_dir / "CONVERTED_FILES" / "tagalog_bible_cleaned.xlsx"

# Read input
with open(input_file, "r", encoding="utf-8") as f:
    text = f.read()

# Extract verses
matches = re.findall(r'(\d+:\d+)\s+(.*?)(?=\s+\d+:\d+|$)', text)

# DataFrame with original text
df_original = pd.DataFrame(matches, columns=["Verse", "Text"])

# DataFrame with cleaned text
df_cleaned = df_original.copy()
df_cleaned["Text"] = df_cleaned["Text"].apply(clean_text)

# Save both files
original_output.parent.mkdir(parents=True, exist_ok=True)
df_original.to_excel(original_output, index=False)
df_cleaned.to_excel(cleaned_output, index=False)

print(f"Done! Saved:\n- {original_output}\n- {cleaned_output}")
