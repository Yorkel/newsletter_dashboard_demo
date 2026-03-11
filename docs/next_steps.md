# Next Steps — AM2

Five things to do, in order.

---

## 1. ~~Talk to the curators~~ — Done

Key questions resolved from curator input (NC + Gemma Moss):

- **Section assignment happens before description writing** → confirmed: train on title only
- **~15–20 articles reviewed per week, ~12 included** → sets scale of the gathering tool
- **Version preference when deduplicating:** quality first, then source authority, then source diversity within the issue
- **Multiple angles on same topic can both be included** — deduplication is a suggestion, not automatic

Remaining open questions (lower priority — don't block modelling):
- What would "good enough" output look like — mostly-right with easy override, or near-perfect?
- Source–slant examples needed to refine deduplication logic

---

## 2. Extract issues 88–102 from HTML

**Why:** The processed CSV only covers issues 1–87 (up to May 2025). Issues 88–102 are in `data/raw/newsletters_html/` and need extracting. This adds ~180 more labelled examples and brings the training data up to date.

**What to do:**

```bash
python src/extract/extract00_newsletters.py
```

Check the existing script handles the newer filenames (`ESRC Education Research Programme Newsletter ##.html`). Append the new rows to `data/processed/newsletter_items_nov.csv` or save as a new version.

**Output:** Updated processed CSV covering issues 1–102.

---

## 3. Label normalisation + EDA notebook

**Why:** The processed CSV has 68 raw theme values — label noise before any modelling is done. This step produces the clean training data the classifier will be trained on.

**What to do:** Create `notebooks/00_label_normalisation_eda.ipynb`:

1. Apply the normalisation map from [docs/datasets.md](datasets.md) — collapse 68 themes → 6 clean labels
2. Drop internal programme rows and parsing noise
3. Inspect class distribution — are sections roughly balanced? (RPP is known to be the hardest to fill, so likely the smallest class)
4. Inspect title length distribution — are titles long enough to classify reliably?
5. Look at a random sample from each class — do the labels make sense?
6. Save clean dataset to `data/training/classifier_training.csv`

**Output:** `data/training/classifier_training.csv` — clean, labelled, ready for modelling.

---

## 4. Set up experiment tracking

**Why:** You're going to train 5 different models and compare them. Without experiment tracking, you'll lose results, forget hyperparameters, and waste time re-running things. Set this up before you write a single model.

**What to do:**

```bash
pip install mlflow
```

Create `notebooks/01_experiment_setup.ipynb` with a minimal working MLflow run that logs:
- Model name / type
- Hyperparameters
- Macro F1, per-class F1
- Confusion matrix as an artefact

Run it once with a dummy model to confirm it works. Decide where runs are stored (local `mlruns/` folder is fine for now).

**Output:** Working MLflow setup; `mlruns/` folder gitignored.

---

## 5. Build the baseline classifier

**Why:** You need a performance floor before any transformer work. The baseline also tells you whether this is a hard or easy problem — if TF-IDF + LogReg gets 0.85 F1, fine-tuning a transformer may not be worth the effort.

**What to do:** Create `notebooks/02_baseline_classifier.ipynb`:

1. Load `data/training/classifier_training.csv`
2. Stratified train/val/test split (70/15/15)
3. sklearn pipeline: `TfidfVectorizer` → `LogisticRegression`
4. Evaluate: macro F1, per-class precision/recall, confusion matrix
5. Inspect top features per class (LogReg coefficients → which words drive each section?)
6. Log everything to MLflow

**Output:** Baseline macro F1 score; understanding of which sections are hard to distinguish; logged MLflow run.

---

## After these five

Once baseline is done, the next block is transformer fine-tuning (Model 2 in the plan) — see [docs/project_plan.md](project_plan.md) for the full model comparison sequence.
