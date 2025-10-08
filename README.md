## **Setting Up the Project**

### **1. Install Python**

Make sure you have **Python 3.8 or higher** installed on your system.
You can check by running:

```bash
python --version
```

### **2. Install Required Libraries**

Install the necessary dependencies using `pip`:

```bash
pip install openpyxl pandas regex
```

These libraries are used for:

* **openpyxl** → writing Excel files
* **pandas** → handling structured data
* **regex** → pattern matching and text parsing

---

## **Running the Program**

Run the main script to process your Bible text file:

```bash
python lang_bible.py
```

**Parameters:**

* `RAW_FILES/ifugao_bible.txt` — raw text input file
* `CONVERTED_FILES/ifugao_bible_cleaned.xlsx` — Excel output file
* `CONVERTED_FILES/ifugao_sentences.txt` — text output segmented by sentence

---

## **Output**

After running the script, two output files are generated in the **`CONVERTED_FILES`** folder:

1. **Excel File (`.xlsx`)** — a structured version of the text
   Example:

   | Book    | Chapter:Verse | Text                                        |
   | ------- | ------------- | ------------------------------------------- |
   | Matthew | 1:1           | Chin himpangapo an narpugwan Hesu Kristo... |
   | Matthew | 1:2           | Nunholag hi Abraham ta hi Isaak...          |

2. **Text File (`.txt`)** — sentences segmented and listed line by line for further analysis
   Example:

   ```
   Chin himpangapo an narpugwan Hesu Kristo.
   Hay hato chi napfulog an himpangapo an narpugwan Hesu Kristo an holag Ari David.
   Nunholag hi Abraham ta hi Isaak.
   ```

