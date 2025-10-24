# /workspaces/ERP_Newsletter/src/labelling.py
import os, json, time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# ------------------------- config -------------------------
INPUT_CSV  = "/workspaces/ERP_Newsletter/data_processed/sample_to_label.csv"
OUTPUT_CSV = "/workspaces/ERP_Newsletter/data_processed/sample_llm_prelabeled.csv"
MODEL_NAME = "gpt-4o-mini"     # good quality & low cost
TEMP       = 0
BATCH_SLEEP_SECS = 0.3         # gentle pacing to avoid rate limits
MAX_CHARS = 6000               # guard against very long inputs
# ----------------------------------------------------------

# --- setup ---
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("Missing OPENAI_API_KEY. Set it via env var or .env")

from openai import OpenAI
client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """You label sentiment TOWARD the main education subject in the text.
Labels: positive, neutral, critical.
Return ONLY strict JSON: {"label":"positive|neutral|critical","confidence":0-1,"rationale":"<=25 words"}.
Rules:
- Judge stance toward the education subject/actor.
- Mixed/unclear => neutral.
- Be conservative with positive/critical.
"""

def call_llm(text: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f'Text:\n"""{text}"""'}
    ]
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMP,
        response_format={"type": "json_object"},  # force valid JSON
    )
    raw = resp.choices[0].message.content

    try:
        data = json.loads(raw)
        label = str(data.get("label","")).lower().strip()
        if label not in {"positive","neutral","critical"}:
            label = "neutral"
        conf = float(data.get("confidence", 0.5))
        rationale = str(data.get("rationale","")).strip()[:200]
    except Exception:
        label, conf, rationale = "neutral", 0.5, "parse_error"

    return {"llm_label": label, "llm_confidence": conf, "llm_rationale": rationale}

def robust_read_csv(path: str) -> pd.DataFrame:
    """Try utf-8 then fall back to latin1 automatically."""
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin1")

def main():
    # load input (robust to encoding)
    df = robust_read_csv(INPUT_CSV)

    # normalise required columns
    cols = [c.lower() for c in df.columns]
    df.columns = cols
    # Accept either 'doc_id' or 'id'; create doc_id
    if "doc_id" not in df.columns:
        if "id" in df.columns:
            df = df.rename(columns={"id": "doc_id"})
        else:
            raise SystemExit("Input must have a 'doc_id' or 'id' column.")
    if "text" not in df.columns:
        raise SystemExit("Input must have a 'text' column.")

    # drop rows with empty text
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0].copy()

    # resume logic: if OUTPUT exists, skip already labeled doc_ids
    done = set()
    if os.path.exists(OUTPUT_CSV):
        prev = robust_read_csv(OUTPUT_CSV)
        if "doc_id" in prev.columns:
            done = set(prev["doc_id"].tolist())
        else:
            prev = pd.DataFrame()
    else:
        prev = pd.DataFrame()

    rows = []
    for _, r in tqdm(df.iterrows(), total=len(df), desc="Labelling"):
        doc_id = r["doc_id"]
        if doc_id in done:
            continue

        text = str(r["text"])[:MAX_CHARS]
        if not text:
            continue

        try:
            out = call_llm(text)
        except Exception as e:
            time.sleep(2.0)  # basic backoff
            try:
                out = call_llm(text)
            except Exception as e2:
                out = {
                    "llm_label": "neutral",
                    "llm_confidence": 0.0,
                    "llm_rationale": f"error: {e2}"
                }

        row = {
            "doc_id": doc_id,
            "text": text,
            **out
        }
        rows.append(row)
        time.sleep(BATCH_SLEEP_SECS)

        # periodic save every 25 rows to avoid losing work
        if len(rows) % 25 == 0:
            tmp = pd.DataFrame(rows)
            out_df = pd.concat([prev, tmp], ignore_index=True) if not prev.empty else tmp
            out_df.to_csv(OUTPUT_CSV, index=False)

    # final save
    new_df = pd.DataFrame(rows)
    out_df = pd.concat([prev, new_df], ignore_index=True) if not prev.empty else new_df
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved {len(out_df)} labelled rows to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
