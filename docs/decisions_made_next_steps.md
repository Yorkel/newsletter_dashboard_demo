# Decisions Made & Next Steps — AM2

---

## Next Steps (do in order)

### 1. EDA — explore the full dataset

Use `data/preprocessed/newsletters_preprocessed.csv` (1,363 rows, full unsplit dataset).

Suggested notebook: `notebooks/01_eda.ipynb`

Things to look at:
- Class distribution of `new_theme` — how imbalanced is it?
- `item_type` breakdown — what proportion are articles vs reports vs academic papers?
- `org_broad_category` — which sectors dominate the newsletter?
- Top organisations by article count
- Title and description length distributions — are titles long enough to classify from?
- Articles per newsletter issue over time (`newsletter_number`) — any gaps or spikes?
- Unmapped organisations / domains (`organisation` is NaN) — are there important sources missing from the lookup?

This also doubles as analysis for Gemma's presentation — **[TO CLARIFY: confirm what the presentation needs before finalising]**

---

### 2. Analysis for Gemma's presentation — URGENT (event: 30 March 2026)

**Event:** BERA seminar — *"Teacher Recruitment and Retention and its links to attainment gaps in England"*
**Gemma's talk:** *"Teacher recruitment, retention and development: perspectives from policy and from research"*
**Audience:** Teacher educators, school leaders, teachers, educational researchers, policy makers

Notebook: `notebooks/02_gemma_presentation_analysis.ipynb`
Dataset: `data/preprocessed/newsletters_preprocessed.csv`

Filter to `new_theme == "teacher_rrd"` (203 items across issues 1–104).

Suggested analysis:
- How many teacher_rrd items have been featured across the programme's lifetime?
- Coverage over time — by newsletter issue / approximate date. Any spikes around policy announcements?
- Which organisations and source types dominate (government vs academic vs think tank vs media)?
- Top sources by count (which outlets cover this topic most?)
- Item type breakdown — reports, news articles, academic articles, government documents
- A curated list of the most notable titles (could be used as a reading list / slide reference)
- Comparison: how does teacher_rrd coverage compare in volume to other themes?

---

### 3. Set up experiment tracking
**Why:** You're going to train 5 different models and compare them. Without experiment tracking, you'll lose results, forget hyperparameters, and waste time re-running things. Set this up before you write a single model.

```bash
pip install mlflow
```

Create a minimal MLflow run that logs:
- Model name / type
- Hyperparameters
- Macro F1, per-class F1
- Confusion matrix as an artefact

Run it once with a dummy model to confirm it works. Store runs in local `mlruns/` folder (gitignored).

---

### 4. Build the baseline classifier (Model 1)

Create `notebooks/02_baseline_classifier.ipynb`:

1. Load `data/processed/train.csv` and `val.csv`
2. sklearn pipeline: `TfidfVectorizer` → `LogisticRegression`
3. Evaluate on val: macro F1, per-class precision/recall, confusion matrix
4. Inspect top features per class (LogReg coefficients)
5. Log everything to MLflow

**Output:** Baseline macro F1; understanding of which sections are hard to distinguish.

---

### 5. Fine-tuned Transformer (Model 2)

- Fine-tune DistilBERT / RoBERTa on the 6-section classification task
- Use HuggingFace `transformers` + `Trainer` API
- Techniques for small dataset: early stopping, learning rate warmup, weight decay
- Log to MLflow; compare to baseline

---

### 6. Sentence Transformer + Classifier Head (Model 3)

- Encode titles with `all-MiniLM-L6-v2` (frozen)
- Train lightweight LogReg or MLP head on embeddings
- Compare to Model 2: does full fine-tuning add much?

---

### After Models 1–3

- Model 4: Zero-shot Claude API classifier
- Model 5: Few-shot Claude API classifier (random vs RAG-style example selection)
- Compare all 5 on the same val set: macro F1, per-class F1, latency, cost
- Select best model for production use

---

## Completed Steps & Key Decisions

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
