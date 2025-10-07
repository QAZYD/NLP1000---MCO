import re
import pandas as pd
from pathlib import Path

input_file = Path("../RAW_FILES/spanish_bible.txt")
output_folder = Path("../CONVERTED_FILES")
output_folder.mkdir(parents=True, exist_ok=True)

excel_path = output_folder / "spanish_bible_cleaned.xlsx"
txt_path = output_folder / "spanish_by_sentence.txt"

def clean_spanish_bible():
    verse_rows = []
    all_sentences = []

    line_re = re.compile(r"^(\d+):(\d+)\s+(.*)$")
    sentence_split = re.compile(r'(?<=[.!?])\s+')

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            m = line_re.match(line)
            if not m:
                continue

            chapter, verse, text = m.groups()
            text = re.sub(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ.!?]", "", text)
            text = re.sub(r"\s+", " ", text).strip()

            # Save verse info
            verse_rows.append({"ChapterVerse": f"{chapter}:{verse}", "Text": text})

            # Split into sentences
            for sentence in sentence_split.split(text):
                sentence = sentence.strip()
                if sentence:
                    all_sentences.append(sentence)

    # Save Excel by verse
    pd.DataFrame(verse_rows).to_excel(excel_path, index=False)
    print(f"Saved Excel -> {excel_path}")

    # Save sentences (1 per line)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sentences))
    print(f"Saved Sentences TXT -> {txt_path}")

if __name__ == "__main__":
    clean_spanish_bible()