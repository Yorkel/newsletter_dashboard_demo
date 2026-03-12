"""
pipeline.py
Runs the full data pipeline in order:
  s00 — Extract newsletters from HTML files
  s01 — Clean and deduplicate
  s02 — Preprocess (themes, orgs, item types, text features)
  s03 — Split into train / val

Run from the project root:
  python src/pipeline.py

For a new weekly newsletter (extract → clean → preprocess → scrape snippets, no split):
  python src/pipeline.py --new-newsletter

The --new-newsletter path adds s02b_scrape, which fetches the first paragraph
from each article URL. This replaces the text feature at inference time so it
matches the training data (title + short text). Falls back to title only if
scraping fails.
"""

import argparse
import importlib
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `src.*` imports resolve
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

STEPS_FULL = [
    ("s00_extract",   "src.extract.s00_extract_newsletters"),
    ("s01_clean",     "src.preprocess.s01_clean"),
    ("s02_preprocess","src.preprocess.s02_preprocess"),
    ("s03_split",     "src.preprocess.s03_split"),
]

STEPS_NEW_NEWSLETTER = [
    ("s00_extract",    "src.extract.s00_extract_newsletters"),
    ("s01_clean",      "src.preprocess.s01_clean"),
    ("s02_preprocess", "src.preprocess.s02_preprocess"),
    ("s02b_scrape",    "src.preprocess.s02b_scrape"),
]


def run_step(name: str, module_path: str):
    print(f"\n{'='*50}")
    print(f"Running {name}...")
    print(f"{'='*50}")
    module = importlib.import_module(module_path)
    module.main()


def main():
    parser = argparse.ArgumentParser(description="ERP Newsletter data pipeline")
    parser.add_argument(
        "--new-newsletter",
        action="store_true",
        help="Run extract→clean→preprocess only (for new weekly newsletters). Skip the train/val split.",
    )
    args = parser.parse_args()

    steps = STEPS_NEW_NEWSLETTER if args.new_newsletter else STEPS_FULL

    for name, module_path in steps:
        run_step(name, module_path)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
