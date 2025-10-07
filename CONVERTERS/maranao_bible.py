import re
from pathlib import Path
import pandas as pd

def clean_maranao_bible():
    input_file = Path("RAW_FILES/maranao.txt")
    output_file_excel = Path("CONVERTED_FILES/maranao_bible_cleaned.xlsx")
    output_file_sentences = Path("CONVERTED_FILES/maranao_sentences.txt")

    current_book = None
    current_chapter = None
    current_verse_num = None
    current_verse_text = ""
    saw_new_chapter = False

    rows = []
    sentences = []

    book_chapter_re = re.compile(r"^(MATIYO|MARKO|LOKAS)\s+(\d+)\b", re.IGNORECASE)
    verse_range_re = re.compile(r"^(\d+)-(\d+)\s*(.*)$")
    verse_start_re = re.compile(r"^(\d+)(?:[\.:])?\s*(.*)$")
    remove_paren_re = re.compile(r"\([^)]*\)")
    remove_tags_re = re.compile(r"<[^>]+>")
    remove_punct_re = re.compile(r"[,:;!?\"“”]")

    def split_sentences(text):
        clean_text = re.sub(r"[^\w\s.!?]", "", text)
        for s in re.split(r"[.!?]", clean_text):
            s = s.strip()
            if s:
                sentences.append(s)

    with open(input_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            text = remove_paren_re.sub("", line)
            text = remove_tags_re.sub("", text)
            text = remove_punct_re.sub("", text)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue

            m_book = book_chapter_re.match(text)
            if m_book:
                if current_verse_text:
                    rows.append({
                        "Book": current_book,
                        "ChapterVerse": f"{current_chapter}:{current_verse_num}",
                        "Text": current_verse_text.strip()
                    })
                    split_sentences(current_verse_text)
                    current_verse_text = ""
                    current_verse_num = None

                book_tok, chap_tok = m_book.groups()
                current_book = book_tok.capitalize()
                current_chapter = chap_tok
                saw_new_chapter = True
                continue

            if saw_new_chapter:
                if not re.match(r"^\d+", text):
                    current_verse_num = "1"
                    current_verse_text = text
                    saw_new_chapter = False
                    continue
                else:
                    saw_new_chapter = False

            m_range = verse_range_re.match(text)
            if m_range:
                n1, n2, verse_text = m_range.groups()
                verse_text = verse_text.strip()
                if current_verse_text:
                    rows.append({
                        "Book": current_book,
                        "ChapterVerse": f"{current_chapter}:{current_verse_num}",
                        "Text": current_verse_text.strip()
                    })
                    split_sentences(current_verse_text)
                    current_verse_text = ""
                    current_verse_num = None

                for n in (n1, n2):
                    rows.append({
                        "Book": current_book,
                        "ChapterVerse": f"{current_chapter}:{n}",
                        "Text": verse_text
                    })
                    split_sentences(verse_text)
                continue

            m_vs = verse_start_re.match(text)
            if m_vs:
                verse_num, after = m_vs.groups()
                after = after.strip()
                if current_verse_text:
                    rows.append({
                        "Book": current_book,
                        "ChapterVerse": f"{current_chapter}:{current_verse_num}",
                        "Text": current_verse_text.strip()
                    })
                    split_sentences(current_verse_text)
                current_verse_num = verse_num
                current_verse_text = after
                continue

            if current_verse_text:
                current_verse_text += " " + text
            else:
                current_verse_num = "1"
                current_verse_text = text

    if current_verse_text:
        rows.append({
            "Book": current_book,
            "ChapterVerse": f"{current_chapter}:{current_verse_num}",
            "Text": current_verse_text.strip()
        })
        split_sentences(current_verse_text)

    # --- ✅ SPLIT ChapterVerse into two columns before saving ---
    output_file_excel.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["Book", "ChapterVerse", "Text"])

    # Split "3:5" → Chapter=3, Verse=5
    df[["Chapter", "Verse"]] = df["ChapterVerse"].str.split(":", n=1, expand=True)

    # Rearrange columns
    df = df[["Book", "Chapter", "Verse", "Text"]]
    df.to_excel(output_file_excel, index=False)

    # --- Save sentences ---
    with open(output_file_sentences, "w", encoding="utf-8") as sf:
        for s in sentences:
            sf.write(s + "\n")

    print(f"Excel file saved -> {output_file_excel}")
    print(f"Sentence file saved -> {output_file_sentences}")

if __name__ == "__main__":
    clean_maranao_bible()
