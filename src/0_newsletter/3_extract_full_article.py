import os
import time
import uuid
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ✅ Import canonical_url from your original scraper
from extract_newsletters import canonical_url


# -----------------------------
# CONFIG
# -----------------------------
NEWSLETTER_ITEMS_CSV = "/workspaces/ERP_Newsletter/data/0_raw/1_newsletter_short_text/newsletter_items.csv"
ARTICLES_CSV = "/workspaces/ERP_Newsletter/data/0_raw/2_newsletter_full_article/newsletter_articles.csv"
MERGED_OUTPUT_CSV = "/workspaces/ERP_Newsletter/data/0_raw/2_newsletter_full_article/newsletter_items_with_articles.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}


# -----------------------------
# HTTP + HTML HELPERS
# -----------------------------
def fetch_html(url: str, timeout: int = 10) -> str | None:
    """Fetch raw HTML for a URL, with basic error handling."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code != 200:
            print(f"❌ {resp.status_code} fetching {url}")
            return None
        resp.encoding = resp.apparent_encoding
        return resp.text
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None


def extract_main_text(html: str) -> str | None:
    """
    Very simple heuristic to get main article text:
    - Prefer <article> tag if present and long enough
    - Else pick the largest <main>/<div>/<section> by text length
    - Else fall back to body text
    """
    soup = BeautifulSoup(html, "html.parser")

    # Strip scripts/styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # 1) Prefer <article>
    article_tag = soup.find("article")
    if article_tag:
        text = article_tag.get_text(" ", strip=True)
        if len(text.split()) > 50:
            return " ".join(text.split())

    # 2) Largest candidate container
    candidates = soup.find_all(["main", "div", "section"])
    best_text = ""
    for c in candidates:
        t = c.get_text(" ", strip=True)
        if len(t) > len(best_text):
            best_text = t

    if len(best_text.split()) > 50:
        return " ".join(best_text.split())

    # 3) Fallback: whole body
    body = soup.body or soup
    text = body.get_text(" ", strip=True)
    text = " ".join(text.split())
    return text if text else None


def article_title_from_html(html: str) -> str | None:
    """Try to extract a reasonable article title."""
    soup = BeautifulSoup(html, "html.parser")
    # <title> tag
    if soup.title and soup.title.string:
        t = " ".join(soup.title.string.split())
        if t:
            return t
    # Or an <h1>
    h1 = soup.find("h1")
    if h1:
        t = " ".join(h1.get_text(" ", strip=True).split())
        if t:
            return t
    return None


# -----------------------------
# MAIN
# -----------------------------
def main():
    if not os.path.exists(NEWSLETTER_ITEMS_CSV):
        raise FileNotFoundError(f"Newsletter items CSV not found: {NEWSLETTER_ITEMS_CSV}")

    df = pd.read_csv(NEWSLETTER_ITEMS_CSV)

    if "link" not in df.columns:
        raise ValueError("Input CSV must contain a 'link' column")

    # Keep only rows with links
    df = df[df["link"].notna()].copy()
    df["link"] = df["link"].astype(str).str.strip()
    df = df[df["link"] != ""]

    # Canonicalise links using your shared canonical_url function
    df["link_canonical"] = df["link"].apply(canonical_url)
    df = df[df["link_canonical"] != ""]
    links = df["link_canonical"].dropna().unique()

    print(f"🔗 Unique links to fetch: {len(links)}")

    rows = []
    for i, url in enumerate(links, start=1):
        print(f"[{i}/{len(links)}] Fetching {url}")
        html = fetch_html(url)
        if not html:
            rows.append({
                "article_id": str(uuid.uuid4()),
                "link_canonical": url,
                "domain": urlparse(url).netloc if url else "",
                "article_title": None,
                "article_text": None,
                "status": "error",
            })
            continue

        a_title = article_title_from_html(html)
        a_text = extract_main_text(html)

        rows.append({
            "article_id": str(uuid.uuid4()),
            "link_canonical": url,
            "domain": urlparse(url).netloc if url else "",
            "article_title": a_title,
            "article_text": a_text,
            "status": "ok" if a_text else "empty",
        })

        # Be polite to servers
        time.sleep(1)

    # Save articles table
    articles_df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(ARTICLES_CSV), exist_ok=True)
    articles_df.to_csv(ARTICLES_CSV, index=False)
    print(f"✅ Wrote {len(articles_df)} article rows to {ARTICLES_CSV}")

    # Merge back onto newsletter items
    merged = df.merge(
        articles_df,
        on="link_canonical",
        how="left",
        validate="many_to_one",
    )

    merged.to_csv(MERGED_OUTPUT_CSV, index=False)
    print(f"✅ Wrote merged dataset to {MERGED_OUTPUT_CSV}")


if __name__ == "__main__":
    main()
