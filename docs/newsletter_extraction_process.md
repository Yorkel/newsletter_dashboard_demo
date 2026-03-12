# NEWSLETTER EXTRACTION PROCESS
**ERP Weekly Education Newsletter**
---

## 1. PROJECT OVERVIEW
The goal of this process was to extract structured data from 100 archived ERP Weekly Education Newsletters, each stored as Word-generated HTML files.

Each newsletter issue contains around 12–20 news items, following this consistent structure:
- **Theme** – table with dark blue background
- **Subtheme** – table with grey or light blue background
- **Title** – usually bold text
- **Description** – follows the title
- **Link** – contained within the description

The aim was to create a structured dataset where each row corresponds to one news item, with the following columns:

`id`, `newsletter_number`, `issue_date`, `theme`, `subtheme`, `title`, `description`, `link`.


---

## 2. PROCESS SUMMARY

### Step 1: Organize Files
- Gathered all 100 newsletter HTML files into one folder:
  `data/newsletters_html/`
- Files cover issues 1–102 (newsletters 90 and 91 are missing; no source files available)
- Removed duplicate files:
  - `Newsletter 100 Erratum.html` (correction notice, no article content)
  - `Fw- TRIAL ESRC Education Research Programme Newsletter 96.html` (trial duplicate)

### Step 2: Parse HTML Structure
- Used **BeautifulSoup** to parse the Word-generated HTML files.
- Identified key visual and formatting cues:
  - Tables with **dark blue backgrounds** represent **Themes**
  - Tables with **grey or light blue backgrounds** represent **Subthemes**
  - Paragraphs with **bold or strong formatting** are **Titles**
  - Following paragraphs contain **Descriptions** and **Links**

### Step 3: Implement Extraction Logic
- Built a Python script (`src/extract/s00_extract_newsletters.py`) that:
  1. Iterates through all newsletters
  2. Extracts **themes, subthemes, titles, descriptions, and links**
  3. Cleans and canonicalises URLs (unwraps Outlook safelinks, strips tracking parameters)
  4. Deduplicates items across the main and fallback parsers
  5. Writes all items into a structured CSV file:
     `data/interim/extracted_newsletters.csv`


---

## 3. KEY ISSUES AND FIXES

### Issue 1: Inconsistent File Names
**Problem:** Original filenames had inconsistent prefixes (e.g., "ERP Newsletter", "ESRC Education Research Programme Newsletter", "FW-" prefixes).
**Fix:** Script extracts newsletter number from filename as a fallback when the number cannot be found in the HTML body text.

---

### Issue 2: Missing Data for Later Newsletters
**Problem:** Some newsletters reported "No rows parsed" due to slightly different colour shades for theme/subtheme tables.
**Fix:** Expanded the colour sets to cover all observed variants:
- **DARK_BLUE_BG:** `#002060`, `#1F3864`, `#203864`, `#00205B`, `#042854`, `#001F60`
- **GREY_BG:** `#DEEAF6`, `#E7E6E6`, `#D9D9D9`, `#A5DAE9`, `#D9E2F3`, `#DAE3F3`

---

### Issue 3: Newsletters Without Bold Titles
**Problem:** Some issues contained no bold or strong text — all item titles were plain paragraphs.
**Fix:** Added a fallback parser (`fallback_parse_by_link`) that:
- Detects items by the **presence of links** instead of bold formatting
- Groups paragraphs under the same **theme or subtheme**
- Uses the **first paragraph as the title** and the following as descriptions
- Creates an item when a **link** is encountered

---

### Issue 4: PDF-Export Newsletters (Plain Text Format)
**Problem:** Some newsletters (e.g. #90, #91, #103, #104) were exported from PDF with no tables — just plain divs/spans.
**Fix:** Added a third parser (`plaintext_parse`) that:
- Matches lines against a known list of theme headings
- Skips email header lines (Subject, Date, From, To, etc.)
- Identifies link tokens ("More", "Book now", etc.) to flush items

---

### Issue 5: Mixed Colour Formats (RGB vs HEX)
**Problem:** Some newsletters used CSS colour values in `rgb()` format instead of hexadecimal.
**Fix:** Added a conversion step to translate `rgb()` values to `#RRGGBB` format before matching.

---

### Issue 6: Tracking URLs and Outlook Safelinks
**Problem:** Many links were wrapped in Outlook safelinks or contained UTM tracking parameters, making URLs noisy and non-canonical.
**Fix:** Added URL helpers to unwrap safelinks and strip known tracking parameters before saving.

---

## 4. CURRENT STATE
- **100 HTML files** in `data/newsletters_html/`
- Issues **90 and 91 are missing** (no source files)
- Successfully extracted **1,886 news items** from 100 newsletters
- Output saved to: `data/interim/extracted_newsletters.csv`


---

## 5. RECOMMENDATIONS FOR FUTURE AUTOMATION

### 1. Standardize Newsletter Formatting
- Keep consistent theme/subtheme colours
- Always use bold text for titles
- Maintain a uniform date and issue number format

### 2. Include Metadata in Each Newsletter
- Add structured headers with issue number and date
- This will make parsing and indexing easier

### 3. Automate Ingestion
- Create a scheduled script (e.g., using **cron** or **GitHub Actions**) that:
  - Detects new HTML files
  - Runs the extraction automatically
  - Appends new rows to the master CSV

### 4. Add Automated Validation
- Detect missing themes, duplicate titles, or empty links
- Report inconsistencies for manual review

### 5. Extend Functionality
- Convert extracted data into a **searchable database** (e.g., SQLite or PostgreSQL)
- Use **NLP** to classify topics, detect entities, and analyse trends
- Build an **interactive dashboard** (e.g., with Streamlit) to visualise newsletter content over time


---

## 6. SUMMARY

| Stage                          | Description                                          | Outcome      |
|--------------------------------|------------------------------------------------------|--------------|
| File Organisation              | 100 newsletters in `data/newsletters_html/`          | ✅ Complete  |
| Duplicate Removal              | Removed erratum and trial duplicate files            | ✅ Complete  |
| HTML Parsing                   | Built BeautifulSoup parser                           | ✅ Complete  |
| Colour Variations              | Added extra HEX/RGB colours                          | ✅ Complete  |
| Non-Bold Titles                | Added fallback parser by link detection              | ✅ Complete  |
| PDF-Export Newsletters         | Added plaintext parser for div/span format           | ✅ Complete  |
| URL Cleaning                   | Unwrap safelinks, strip tracking params              | ✅ Complete  |
| Output                         | 1,886 rows in `data/interim/extracted_newsletters.csv` | ✅ Complete |
| Missing Issues (90, 91)        | No source files available                            | ⚠️ Gap       |
| Future Automation              | Standardisation and scheduling recommended           | 🔜 Next Step |

---

**Author:** Yorkel
**Last Updated:** March 2026
**Project:** ERP Newsletter Extraction and Automation
---
