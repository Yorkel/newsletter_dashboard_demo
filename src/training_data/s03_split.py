"""
s03_split.py
Splits preprocessed newsletter data into train and validation sets.
Uses stratified split by new_theme to ensure all classes are represented.

Test set is NOT created here — new weekly newsletters serve as the live test set.
Run s00 → s01 → s02 on each new newsletter and save to data/test/.

Input:  data/preprocessed/newsletters_preprocessed.csv
Output: data/processed/train.csv
        data/processed/val.csv
"""

import pandas as pd
from sklearn.model_selection import train_test_split

# -----------------------------
# CONFIG
# -----------------------------
INPUT_CSV  = "data/preprocessed/newsletters_preprocessed.csv"
TRAIN_CSV  = "data/processed/train.csv"
VAL_CSV    = "data/processed/val.csv"

VAL_SIZE   = 0.15   # 15% validation
RANDOM_SEED = 42

LABEL_COL  = "new_theme"

# Known target classes — rows with other values are excluded from modelling
VALID_THEMES = {
    "update_from_programme",
    "update_from_pi",
    "what_matters_ed",
    "teacher_rrd",
    "edtech",
    "four_nations",
    "policy_practice_research",
    "political_environment_key_organisations",
}


# -----------------------------
# MAIN
# -----------------------------

def main():
    print("Loading preprocessed data...")
    df = pd.read_csv(INPUT_CSV)
    print(f"  Loaded {len(df)} rows")

    # Keep only rows with a known theme label
    before = len(df)
    df = df[df[LABEL_COL].isin(VALID_THEMES)].copy()
    print(f"  Kept {len(df)} rows with known themes (excluded {before - len(df)} unmapped)")

    # Show class distribution before split
    print("\nClass distribution:")
    print(df[LABEL_COL].value_counts().to_string())

    # Stratified split
    train_df, val_df = train_test_split(
        df,
        test_size=VAL_SIZE,
        stratify=df[LABEL_COL],
        random_state=RANDOM_SEED,
    )

    train_df = train_df.reset_index(drop=True)
    val_df   = val_df.reset_index(drop=True)

    print(f"\nTrain: {len(train_df)} rows")
    print(f"Val:   {len(val_df)} rows")

    # Save
    import os
    os.makedirs("data/processed", exist_ok=True)
    train_df.to_csv(TRAIN_CSV, index=False)
    val_df.to_csv(VAL_CSV,   index=False)
    print(f"\nSaved train → {TRAIN_CSV}")
    print(f"Saved val   → {VAL_CSV}")
    print("\nNote: test set = new weekly newsletters. Run s00→s01→s02 on each and save to data/test/")


if __name__ == "__main__":
    main()
