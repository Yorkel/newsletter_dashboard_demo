# Decisions Made & Next Steps — AM2

---

## Next Steps (do in order)

### 1. Preprocessing notebook (`02_preprocessing.ipynb`)

- Minimal text cleaning (remove URLs, email addresses — keep casing and punctuation for transformers)
- Encode metadata features (`item_type`, `org_broad_category`)
- Stratified train/val split
- Save train/val CSVs

---

### 2. Baseline classifier (`03_baseline_tfidf.ipynb`)

- TF-IDF + logistic regression with `class_weight="balanced"`
- Evaluate: macro F1, per-class precision/recall, confusion matrix
- Inspect top features per class (LogReg coefficients)

---

### 3. Sentence Transformer + Classifier Head (`04_sentence_transformer.ipynb`)

- Encode text with `all-MiniLM-L6-v2` (frozen)
- Train lightweight LogReg or MLP head on embeddings
- Compare to baseline: does embedding approach add much?

---

### 4. Fine-tuned Transformer (`05_transformer.ipynb`)

- Fine-tune DistilBERT/BERT on the 6-category classification task
- Techniques for small dataset: early stopping, low learning rate, 3-5 epochs, weight decay
- Compare to baseline

---

### 5. Claude API classifiers (`06_claude_api.ipynb`)

- Zero-shot Claude API classifier
- Few-shot Claude API classifier (random vs RAG-style example selection)
- DSPy optimisation pass — systematically optimise prompts against eval metrics rather than hand-tuning
- Inspect structured evaluation logged

---

### 6. Model comparison (`07_model_comparison.ipynb`)

- Compare all 5 models on the same val set: macro F1, per-class F1, confusion matrices, latency, cost
- Select best model for production use

---

### 7. Build inference pipeline

- Connect winning model to existing pipeline (`src/pipeline.py`)
- Add classification step (`s04_classify`) to the `--new-newsletter` path
- Use scraped articles from the separate weekly scraping repo (6 organisations, Jan 2026–present) as inference input
- Add new organisations to the mapping table as needed

---

### 8. Real-world validation (layer 2)

Two layers of validation:
- **Layer 1 (done in step 6):** val set evaluation — standard ML metrics on held-out historical data
- **Layer 2:** run the full inference pipeline on live scraped articles, then compare predicted categories against what the curator actually selected for that week's newsletter

This tests the whole system end-to-end: did the classifier categorise articles correctly? Did it miss articles the curator included? Did it suggest articles the curator didn't pick?

---

### 9. Semantic deduplication

- Use sentence transformer embeddings to compute pairwise cosine similarity between candidate articles
- Group articles above a similarity threshold — present groups to curator to pick the best version
- Skills: vector similarity, clustering, threshold tuning

---

### 10. Newsletter draft generation (stretch goal)

- Use Claude API to generate a structured newsletter draft grouped by section
- Short description per article generated from title + scraped body text
- Curator edits the draft, adds their voice, writes internal sections manually
- Potential to chain classification → deduplication → draft generation as an agentic pipeline using LangGraph
- Skills: RAG, structured LLM output, prompt chaining, end-to-end pipeline design

---

## Completed Steps & Key Decisions

---

### EDA — Done (2026-04-02)

Notebook: `notebooks/01_eda.ipynb`

Key decisions:
- Dropped `update_from_pi` and `update_from_programme` categories (curator content, not derived from articles)
- Dropped rows with fewer than 15 words (junk: sub-links, email signups, bylines)
- Dropped rows with unmapped organisations (platform/utility domains: eventbrite, zoom, bit.ly)
- Final clean dataset: 1,109 rows, 6 categories, saved to `data/processed/eda_cleaned.csv`
- Features for modelling: `text` (main signal via TF-IDF), `item_type`, `org_broad_category` (metadata features with signal)
- Categories have distinct vocabularies — TF-IDF will be effective
- Class balance is mild (13.0%–21.6%) — stratified splits and `class_weight="balanced"` sufficient
- 1,109 samples sufficient for TF-IDF + logistic regression; borderline for fine-tuning DistilBERT; too small for larger transformers
- Pipeline must keep input consistent: use title + short description at both training and inference time
- If a new source is added to scraping list, must also be added to the organisation mapping table

---

### Analysis for Gemma's BERA presentation — Done (30 March 2026)

Notebook: `notebooks/bera/bera_analysis_clean.ipynb`

---

### Talk to the curators — Done

Key decisions from curator input (NC + Gemma Moss):

- **Section assignment happens before description writing** → confirmed: train on title only. Using descriptions in training would create a training/inference mismatch.
- **~15–20 articles reviewed per week, ~12 included** → sets scale of the gathering tool
- **Version preference when deduplicating:** quality first, then source authority, then source diversity within the issue
- **Multiple angles on same topic can both be included** — deduplication is a suggestion, not automatic

Remaining open questions (lower priority — don't block modelling):
- What would "good enough" output look like — mostly-right with easy override, or near-perfect?
- Source–slant examples needed to refine deduplication logic

---

### Extracted all newsletters from HTML — Done

- `src/extract/s00_extract_newsletters.py` scrapes all HTML newsletter files
- Covers issues 1–104
- Output: `data/interim/extracted_newsletters.csv` (~1,668 rows)

---

### Created preprocessing pipeline — Done (2026-03-12)

Converted exploration notebook (`experiments/notebooks/0_clean_preprocess.ipynb`) into three production scripts:

| Script | What it does |
|--------|-------------|
| `src/preprocess/s01_clean.py` | Fix encoding/unicode, drop missing essentials, deduplicate (3 passes) |
| `src/preprocess/s02_preprocess.py` | Standardise themes, extract domains, map orgs, classify item types, build text feature |
| `src/preprocess/s03_split.py` | Stratified 85/15 train/val split |
| `src/pipeline.py` | Runs s00→s01→s02→s03 in order |

Run the whole pipeline:
```bash
python src/pipeline.py
```

Run just extract→clean→preprocess for a new incoming newsletter (no split):
```bash
python src/pipeline.py --new-newsletter
```

---

### Key decisions made 2026-03-12

**Two-script approach over one-script:** Chose two separate scripts (s01 + s02) over a single script with functions, because two files are easier to read, debug, and iterate on for a smaller codebase.

**No data leakage from preprocessing before split:** All preprocessing in s01/s02 is rule-based (hardcoded dictionaries, regex, URL parsing) — no statistics are fit from the data. It is safe to preprocess the full dataset before splitting.

**Train/val/test split strategy:**
- Historical data (all newsletters processed to date) → stratified 85/15 **train/val split only**
- **Test set = new weekly newsletters as they arrive** — saved to `data/test/` by running the pipeline with `--new-newsletter`
- This is better than holding out historical data for test: genuinely unseen future data is a more realistic evaluation
- One newsletter ≈ 15–30 items; test set accumulates meaningfully after a few weeks
- Labels come automatically from the newsletter HTML structure — no manual labelling needed for test

**Item type classification added to s02:** Each newsletter item is classified as one of: `video`, `tweet`, `linkedin_post`, `academic_article`, `government_document`, `report`, `news_article`, `blog_post`, `social_media_post`, `article`. Uses domain-level overrides first, then org category rules, then URL pattern matching as a fallback.

**Stratified split by `new_theme`:** Ensures all 8 theme classes are proportionally represented in both train and val — important because classes are imbalanced.

**Training text feature:** Train on `text` = title + curator description. Curator descriptions are largely drawn from the article's own words (confirmed with curators), so they are a close proxy for a scraped snippet. No reprocessing of historical data needed.

**Inference text feature for new newsletters:** `s02b_scrape.py` fetches the first paragraph from each article URL and builds `text` = title + scraped snippet. Falls back to title only if scraping fails (paywall, 404, timeout). This runs in the `--new-newsletter` pipeline path only. The mismatch between curator descriptions (training) and scraped snippets (inference) is acceptable because both are short summaries of the article in the article's own language.

**`data/preprocessed/newsletters_preprocessed.csv` is the full analysis dataset:** 1,363 rows, all columns, unsplit. Use this for EDA and Gemma's presentation. `data/processed/train.csv` and `val.csv` are for model training only.
