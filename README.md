# ESRC Education Research Programme — Newsletter Dashboard

A Streamlit dashboard that helps curators review ML-classified education articles and compile the programme's weekly newsletter.

## What it does

- **Review Articles** — Each article gets two category suggestions with confidence scores. Accept the correct one or reject.
- **Add Article** — Manually add articles the pipeline missed.
- **Organise** — Group accepted articles by category, select top picks, move between sections.
- **Newsletter Draft** — Write descriptions and download as plain text.
- **Sources** — View all monitored sources and their automation status.
- **Feedback** — Rate accuracy and suggest improvements.

## Newsletter categories

| Section | Label |
|---|---|
| Teacher recruitment, retention & development | `teacher_rrd` |
| EdTech | `edtech` |
| Political environment and key organisations | `political_environment_key_organisations` |
| Four Nations | `four_nations` |
| Research – Practice – Policy | `policy_practice_research` |
| What matters in education? | `what_matters_ed` |

## Run locally

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Data

The dashboard reads from `data/modelling/classified_articles.csv`, which is produced by the classification pipeline.

## License

MIT — see [LICENSE](LICENSE).
