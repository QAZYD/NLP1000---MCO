import pandas as pd
from pathlib import Path

# === CONFIG ===
base_dir = Path(__file__).resolve().parent.parent
lang1_file = base_dir / "CONVERTED_FILES" / "english_bible_cleaned.xlsx"
lang2_file = base_dir / "CONVERTED_FILES" / "spanish_bible_cleaned.xlsx"
output_file = base_dir / "CORPUS_FILES" / "ENG-SPA-CORPUS.xlsx"

lang1_label = "English"
lang2_label = "Spanish"

# === BOOK NORMALIZATION MAP ===
book_map = {
    # English abbreviations → Standard names
    "Mat": "Matthew", "Matt": "Matthew", "Matthew": "Matthew",
    "Mar": "Mark", "Mk": "Mark", "Mark": "Mark",
    "Luk": "Luke", "Lk": "Luke", "Luke": "Luke",
    # Spanish abbreviations → Standard names
    "Mateo": "Matthew",
    "Marcos": "Mark",
    "Lucas": "Luke"
}

# === READ FILES ===
df1 = pd.read_excel(lang1_file)
df2 = pd.read_excel(lang2_file)

# === VERIFY REQUIRED COLUMNS ===
required_cols = {"Book", "Chapter", "Verse", "Text"}
for df_name, df in [("Lang1", df1), ("Lang2", df2)]:
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"{df_name} file missing columns: {missing}")

# === NORMALIZE BOOK NAMES ===
df1["Book"] = df1["Book"].map(book_map).fillna(df1["Book"])
df2["Book"] = df2["Book"].map(book_map).fillna(df2["Book"])

# === ALIGN BY Book, Chapter, Verse ===
merged = pd.merge(
    df1,
    df2,
    on=["Book", "Chapter", "Verse"],
    how="inner",
    suffixes=(f"_{lang1_label}", f"_{lang2_label}")
)

# === RENAME FOR CLARITY ===
merged = merged.rename(columns={
    f"Text_{lang1_label}": lang1_label,
    f"Text_{lang2_label}": lang2_label
})

# === ENSURE OUTPUT DIRECTORY EXISTS ===
output_file.parent.mkdir(parents=True, exist_ok=True)

# === SAVE OUTPUT ===
merged.to_excel(output_file, index=False)

print("English-Spanish parallel corpus successfully created!")
print(f"Output file: {output_file}")
print(f"Normalized books: {sorted(set(book_map.values()))}")
print(f"Total aligned verses: {len(merged)}")
