# Datasets

## Raw Data

### `data/raw/newsletters_html/`
104 HTML files containing the ESRC Education Research Programme (ERP) newsletters, exported from email. Covers issues 1–102 (issues 90 and 91 are missing). Files are named by issue number and follow two naming conventions:
- `ERP Newsletter <n>.html` / `FW- ERP Newsletter <n>.html` — earlier issues (roughly 1–19)
- `ESRC Education Research Programme Newsletter <n>.html` / `FW- ESRC Education Research Programme Newsletter <n>.html` — later issues (20 onwards)

The `FW-` prefix indicates the email was forwarded. Content includes curated links to education research news, policy updates, and events.

---

## Processed Data

### `data/processed/newsletter_items_nov.csv`
1,668 rows of structured newsletter items extracted from the raw HTML files. Each row represents a single item (article, event, or announcement) from a newsletter issue.

**Columns:**
| Column | Description |
|---|---|
| `id` | Unique identifier (UUID) for each item |
| `newsletter_number` | The issue number the item came from |
| `issue_date` | Publication date of the newsletter |
| `theme` | Top-level category (e.g. DfE, Calls for evidence) |
| `subtheme` | Sub-category within the theme (often empty) |
| `title` | Headline or title of the item |
| `description` | Summary or body text of the item |
| `link` | URL to the full article or resource (often empty) |
