# Dashboard Deployment Guide

This folder contains everything needed to deploy the ERP Newsletter Curator Dashboard as a standalone Streamlit app.

## What's in this folder

```
deployment/
  app.py                              # The Streamlit dashboard
  requirements.txt                    # Python dependencies
  Screenshot 2026-04-05 at 21.14.48.png  # Logo image
  .streamlit/config.toml              # Streamlit theme config
  .gitignore                          # Ignores .env, __pycache__, etc.
  data/modelling/
    classified_articles.csv           # Classified articles (from pipeline)
  DEPLOYMENT.md                       # This file
```

## How to deploy

### Option 1: Streamlit Community Cloud (recommended)

1. Clone this repo (or fork it)
2. Delete everything except the contents of `deployment/` (move files to root)
3. Push to a public GitHub repo
4. Go to [Streamlit Cloud](https://share.streamlit.io/) and connect the repo
5. Set main file path to `app.py`
6. Deploy

### Option 2: Run locally

```bash
cd deployment
pip install -r requirements.txt
streamlit run app.py
```

## Updating the data

When you run the pipeline (`python src/pipeline.py --inference`) in the main repo, it produces a new `data/modelling/classified_articles.csv`. Copy that file into this folder to update the dashboard:

```bash
cp data/modelling/classified_articles.csv deployment/data/modelling/classified_articles.csv
```

Then commit and push to trigger a redeploy on Streamlit Cloud.

## Notes

- The dashboard reads from a local CSV file, not directly from Supabase
- No API keys or secrets are needed to run the dashboard
- The `.env` file is gitignored and not included
