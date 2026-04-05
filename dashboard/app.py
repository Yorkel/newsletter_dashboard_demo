"""
AM2 Newsletter Curator Dashboard
Streamlit app for reviewing classified articles and monitoring model performance.

Run: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# CONFIG
# -----------------------------
DATA_DIR = Path("data/modelling")
MODEL_DIR = Path("models")

CATEGORY_LABELS = {
    "teacher_rrd": "Teacher recruitment, retention & development",
    "edtech": "EdTech",
    "political_environment_key_organisations": "Political environment and key organisations",
    "four_nations": "Four Nations",
    "policy_practice_research": "Research – Practice – Policy",
    "what_matters_ed": "What matters in education?",
}

# Display order for the newsletter
CATEGORY_ORDER = [
    "teacher_rrd",
    "edtech",
    "political_environment_key_organisations",
    "four_nations",
    "policy_practice_research",
    "what_matters_ed",
]

CATEGORY_COLORS = {
    "edtech": "#5b9bd5",
    "four_nations": "#70ad47",
    "policy_practice_research": "#7b7fb5",
    "political_environment_key_organisations": "#4472c4",
    "teacher_rrd": "#ed7d31",
    "what_matters_ed": "#44b4a6",
}

SOURCE_LABELS = {
    "schoolsweek": "Schools Week",
    "gov": "GOV.UK",
    "fft": "FFT Education Datalab",
    "fed": "Further Education Development",
    "epi": "Education Policy Institute",
    "tes": "TES",
    "nfer": "National Foundation for Educational Research",
    "ofsted": "Ofsted",
    "sutton_trust": "Sutton Trust",
    "bbc": "BBC",
    "guardian": "The Guardian",
}

# ESRC brand colours
NAVY = "#0f1e3d"
TEAL = "#44b4a6"
LIGHT_BLUE = "#5b9bd5"
MID_BLUE = "#1d3461"


# -----------------------------
# DATA LOADING
# -----------------------------
@st.cache_data
def load_classified_articles():
    """Load classified articles from local CSV or Supabase."""
    csv_path = DATA_DIR / "classified_articles.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return pd.DataFrame()


@st.cache_data
def load_monitoring_log():
    """Load monitoring log."""
    log_path = DATA_DIR / "monitoring_log.csv"
    if log_path.exists():
        return pd.read_csv(log_path)
    return pd.DataFrame()


@st.cache_data
def load_val_results():
    """Load val predictions for baseline comparison."""
    val_path = DATA_DIR / "val_predictions.csv"
    if val_path.exists():
        return pd.read_csv(val_path)
    return pd.DataFrame()


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="ESRC ERP Newsletter",
    page_icon="📰",
    layout="wide",
)

# Custom CSS — ESRC brand colours
st.markdown(f"""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {NAVY};
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    [data-testid="stSidebar"] .stRadio label {{
        color: #c8d8ec !important;
    }}
    [data-testid="stSidebar"] .stRadio label:hover {{
        color: {TEAL} !important;
    }}

    /* Headers */
    h1 {{
        color: {NAVY} !important;
    }}
    h2, h3 {{
        color: {MID_BLUE} !important;
    }}

    /* Primary buttons */
    .stButton > button[kind="primary"] {{
        background-color: {TEAL};
        border-color: {TEAL};
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: #389e93;
        border-color: #389e93;
    }}

    /* Info boxes */
    .stAlert {{
        background-color: #e8f4f8;
        border-left-color: {TEAL};
    }}

    /* Progress bar */
    .stProgress > div > div > div {{
        background-color: {TEAL};
    }}

    /* Dividers */
    hr {{
        border-color: #dde3ed;
    }}

    /* Hide anchor link icons on headers */
    h1 a, h2 a, h3 a {{
        display: none !important;
    }}

    /* Card containers — light background */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: #f8f9fb !important;
        border-radius: 8px !important;
    }}

    /* Download button — light orange */
    [data-testid="stDownloadButton"] button {{
        background-color: #ffecd2 !important;
        color: #856404 !important;
        border: 1px solid #f0c36d !important;
    }}
    [data-testid="stDownloadButton"] button:hover {{
        background-color: #ffe0b2 !important;
    }}

    /* All buttons — same height */
    [data-testid="stButton"] button {{
        min-height: 50px !important;
        font-size: 13px !important;
    }}

    /* Colour buttons by text content */
    [data-testid="stButton"] button:has(p:contains("✓")) {{
        color: white !important;
        border: none !important;
    }}
    [data-testid="stButton"] button:has(p:contains("✕")) {{
        background-color: #95a5a6 !important;
        color: white !important;
        border: none !important;
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SIDEBAR
# -----------------------------
_logo_path = Path(__file__).parent / "Screenshot 2026-04-05 at 21.14.48.png"
if _logo_path.exists():
    st.sidebar.image(str(_logo_path), use_container_width=True)
st.sidebar.title("Newsletter Curator")

page = st.sidebar.radio(
    "Navigate",
    ["About", "Add Article", "Review Articles", "Organise", "Newsletter Draft", "Feedback"],
)

# Load data
df = load_classified_articles()

if df.empty:
    st.error("No classified articles found. Run `python src/pipeline.py --inference` first.")
    st.stop()

# Format dates as dd-mm-yyyy
if "article_date" in df.columns:
    df["article_date"] = pd.to_datetime(df["article_date"], errors="coerce").dt.strftime("%d-%m-%Y")

# -----------------------------
# SESSION STATE: track curator decisions
# -----------------------------
if "decisions" not in st.session_state:
    # Load from CSV if exists
    decisions_csv = DATA_DIR / "curator_decisions.json"
    if decisions_csv.exists():
        import json as _json
        with open(decisions_csv) as f:
            st.session_state.decisions = _json.load(f)
    else:
        st.session_state.decisions = {}
def _save_decisions():
    """Persist decisions to local JSON file."""
    import json as _json
    with open(DATA_DIR / "curator_decisions.json", "w") as f:
        _json.dump(st.session_state.decisions, f)

if "curator_articles" not in st.session_state:
    # Load from CSV if exists, otherwise empty
    curator_csv = DATA_DIR / "curator_added_articles.csv"
    if curator_csv.exists():
        st.session_state.curator_articles = pd.read_csv(curator_csv).to_dict("records")
    else:
        st.session_state.curator_articles = []


# -----------------------------
# PAGE: REVIEW ARTICLES
# -----------------------------
# Banner on every page
st.markdown(
    "<div style='background:#fff3cd;border:1px solid #ffc107;border-radius:5px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#856404;text-align:center;'>"
    "This is a prototype dashboard. The production version will be private to the programme curators.</div>",
    unsafe_allow_html=True,
)

if page == "About":
    st.title("ESRC Education Research Programme Newsletter")
    st.markdown("This dashboard supports the curation of the programme's weekly newsletter. It uses a classification model to automatically read each article and suggest the top two most likely newsletter categories, so curators can quickly review and confirm rather than sorting from scratch.")

    st.markdown(f"<div style='border-top:3px solid #1d3461;margin:20px 0;'></div>", unsafe_allow_html=True)

    # How it works
    st.subheader("How it works")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("**1. Collect**")
            st.markdown("Articles are pulled weekly from source feeds and classified by the model. Curators can also manually add articles the pipeline missed.")
        with st.container(border=True):
            st.markdown("**3. Organise**")
            st.markdown("Accepted articles are grouped by category. Select the top articles for the newsletter and move articles between categories if needed.")
    with col2:
        with st.container(border=True):
            st.markdown("**2. Review**")
            st.markdown("Each article receives two category suggestions with confidence scores. Accept the correct category or reject irrelevant items.")
        with st.container(border=True):
            st.markdown("**4. Publish**")
            st.markdown("Write descriptions for selected articles and download the newsletter draft as plain text.")

    st.markdown(f"<div style='border-top:3px solid #1d3461;margin:20px 0;'></div>", unsafe_allow_html=True)

    # Categories
    st.subheader("Newsletter categories")
    category_descriptions = {
        "teacher_rrd": "Teacher recruitment, retention, development, training, pay, workload, or the teaching profession.",
        "edtech": "Educational technology, AI in education, digital tools for learning, and technology policy in schools.",
        "political_environment_key_organisations": "News and announcements from key political and policy organisations (DfE, Ofsted, parliamentary committees, think tanks).",
        "four_nations": "Education in Scotland, Wales, or Northern Ireland, or devolved education policy.",
        "policy_practice_research": "Research reports, academic studies, evidence reviews, and practice-focused publications about education.",
        "what_matters_ed": "Broader education issues that matter to children and families: SEND, attendance, mental health, disadvantage, pupil welfare, poverty.",
    }

    cols = st.columns(3)
    for i, key in enumerate(CATEGORY_ORDER):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{CATEGORY_LABELS[key]}**")
                st.caption(category_descriptions[key])

    st.markdown(f"<div style='border-top:3px solid #1d3461;margin:20px 0;'></div>", unsafe_allow_html=True)

    # Dashboard pages
    st.subheader("Dashboard pages")
    pages_info = [
        ("Add Article", "Manually add articles the pipeline missed, with your own category suggestions."),
        ("Review Articles", "Review each article's two suggested categories. Accept the correct one or reject irrelevant items."),
        ("Organise", "Accepted articles grouped by category. Select the top articles and move between categories if needed."),
        ("Newsletter Draft", "Preview the final newsletter. Write descriptions and download as plain text."),
        ("Feedback", "Rate classification accuracy, flag problem categories, suggest missing sources."),
    ]
    for name, desc in pages_info:
        st.markdown(f"**{name}:** {desc}")

    st.markdown(f"<div style='border-top:3px solid #1d3461;margin:20px 0;'></div>", unsafe_allow_html=True)

    st.caption("The classification model reads article content and suggests the two most likely categories. It gets the correct category in its top two suggestions for roughly 9 out of 10 articles.")

elif page == "Review Articles":
    st.title("Review Articles")
    st.markdown("Review each article's classification. The model suggests two possible categories — **accept** the correct one or **reject** if neither fits. Rejected articles won't appear in the newsletter draft.")

    # Week selector + article count in one card
    weeks = sorted(df["week_number"].dropna().unique().astype(int).tolist(), reverse=True)
    with st.container(border=True):
        col_week, col_count = st.columns([1, 2])
        with col_week:
            selected_week = st.selectbox("Select week", weeks, index=0)

        filtered = df[df["week_number"] == selected_week].copy()

        # Add curator-submitted articles (they appear in all weeks)
        if st.session_state.curator_articles:
            curator_df = pd.DataFrame(st.session_state.curator_articles)
            curator_df["curator_added"] = True
            if "curator_added" not in filtered.columns:
                filtered["curator_added"] = False
            filtered = pd.concat([filtered, curator_df], ignore_index=True)

        n_curator = filtered["curator_added"].sum() if "curator_added" in filtered.columns else 0
        with col_count:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"**Week {selected_week}:** {len(filtered)} articles to review" + (f" ({n_curator} added by curator)" if n_curator else ""))

    # Download for manual review (centred)
    review_cols = ["title", "source", "article_date", "url", "top1", "top1_confidence", "top2", "top2_confidence"]
    available = [c for c in review_cols if c in filtered.columns]
    review_export = filtered[available].copy()
    if "top1_confidence" in review_export.columns:
        review_export["top1_confidence"] = (review_export["top1_confidence"] * 100).round(0).astype(int)
    if "top2_confidence" in review_export.columns:
        review_export["top2_confidence"] = (review_export["top2_confidence"] * 100).round(0).astype(int)

    from io import BytesIO
    buffer = BytesIO()
    review_export.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        f"Download week {selected_week} for manual review",
        buffer,
        file_name=f"week_{selected_week}_review.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown(f"<div style='border-top:3px solid #1d3461;margin:20px 0;'></div>", unsafe_allow_html=True)

    # Sort options
    sort_by = st.selectbox("Order by", ["Date (newest first)", "Date (oldest first)", "Source"])
    if sort_by == "Date (newest first)":
        filtered = filtered.sort_values("article_date", ascending=False, na_position="first")
    elif sort_by == "Date (oldest first)":
        filtered = filtered.sort_values("article_date", ascending=True, na_position="last")
    else:
        filtered = filtered.sort_values("source", na_position="last")

    # Progress
    n_reviewed = sum(1 for url in filtered["url"] if url in st.session_state.decisions)
    st.progress(n_reviewed / len(filtered) if len(filtered) > 0 else 0)
    st.caption(f"{n_reviewed} / {len(filtered)} reviewed")

    # Article cards
    for idx, row in filtered.iterrows():
        url = row.get("url", str(idx))
        conf1 = row["top1_confidence"]
        conf2 = row.get("top2_confidence", 0)
        cat1 = row["top1"]
        cat2 = row.get("top2", "")
        cat1_label = CATEGORY_LABELS.get(cat1, cat1)
        cat2_label = CATEGORY_LABELS.get(cat2, cat2)
        conf1_color = "#27ae60" if conf1 >= 0.6 else "#f39c12" if conf1 >= 0.4 else "#e74c3c"
        conf2_color = "#27ae60" if conf2 >= 0.6 else "#f39c12" if conf2 >= 0.4 else "#e74c3c"

        # Check if already reviewed
        decision = st.session_state.decisions.get(url)
        card_style = "opacity: 0.5;" if decision else ""

        with st.container(border=True):
            is_curator = row.get("curator_added", False)
            badge = " <span style='background:#f39c12;color:white;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;'>CURATOR ADDED</span>" if is_curator else ""
            st.markdown(f"**Article title:** {row.get('title', 'No title')}{badge}", unsafe_allow_html=True)
            source_name = SOURCE_LABELS.get(row.get('source', ''), row.get('source', ''))
            st.markdown(f"**Article source:** {source_name}  |  **Date:** {row.get('article_date', '')}")

            # Text preview
            if row.get("text_clean"):
                with st.expander("Preview text"):
                    st.write(str(row["text_clean"])[:500])

            if row.get("url"):
                st.markdown(f"[Open article ↗]({row['url']})")

            # Action buttons — show confidence only for model-classified articles
            is_curator = row.get("curator_added", False)
            btn1_text = f"✓ {cat1_label}" if is_curator else f"✓ {cat1_label} ({conf1:.0%})"
            btn2_text = f"✓ {cat2_label}" if is_curator else f"✓ {cat2_label} ({conf2:.0%})"

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button(btn1_text, key=f"acc1_{url}", use_container_width=True):
                    st.session_state.decisions[url] = {"action": "accept_top1", "label": cat1}
                    _save_decisions()
                    st.rerun()
            with col_b:
                if st.button(btn2_text, key=f"acc2_{url}", use_container_width=True):
                    st.session_state.decisions[url] = {"action": "accept_top2", "label": cat2}
                    _save_decisions()
                    st.rerun()
            with col_c:
                if st.button("✕ Reject", key=f"rej_{url}", use_container_width=True):
                    st.session_state.decisions[url] = {"action": "reject", "label": ""}
                    _save_decisions()
                    st.rerun()

            # Show decision if made
            if decision:
                if decision["action"] == "reject":
                    st.markdown(":red[Rejected]")
                else:
                    st.markdown(f":green[Accepted: {CATEGORY_LABELS.get(decision['label'], decision['label'])}]")

            pass  # container closes automatically

    # Export decisions
    if st.session_state.decisions:
        st.markdown(f"<div style='border-top:3px solid #1d3461;margin:20px 0;'></div>", unsafe_allow_html=True)
        decision_rows = []
        for url, dec in st.session_state.decisions.items():
            if dec["action"] == "reject":
                continue
            article = df[df["url"] == url].iloc[0] if url in df["url"].values else {}
            decision_rows.append({
                "url": url,
                "title": article.get("title", ""),
                "curator_label": dec["label"],
            })
        decisions_df = pd.DataFrame(decision_rows)

        from io import BytesIO
        buffer_dec = BytesIO()
        decisions_df.to_excel(buffer_dec, index=False, engine="openpyxl")
        buffer_dec.seek(0)

        _, dl_dec_col, _ = st.columns([1, 3, 1])
        with dl_dec_col:
            st.download_button(
                f"Download {len(decisions_df)} decisions",
                buffer_dec,
                file_name=f"curator_decisions_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )


# -----------------------------
# PAGE: ADD ARTICLE
# -----------------------------
elif page == "Add Article":
    st.title("Add Article")
    st.markdown("Articles from the programme's source feeds are automatically scraped, classified and loaded into the **Review Articles** page each week. Use this page to manually add any additional articles the pipeline may have missed — for example from sources not yet in the feed, or articles shared directly by colleagues. Added articles will appear on the Review page with a **CURATOR ADDED** badge.")

    with st.form("add_article_form", clear_on_submit=True):
        title = st.text_input("Article title *")
        source = st.text_input("Source (e.g. Schools Week, GOV.UK, TES)")
        date = st.date_input("Publication date")
        url = st.text_input("Link (URL)")
        description = st.text_area("Short description", max_chars=500)

        st.markdown("**Suggest two categories:**")
        cat_options = list(CATEGORY_LABELS.keys())
        cat_format = lambda x: CATEGORY_LABELS.get(x, x)
        col1, col2 = st.columns(2)
        with col1:
            cat1 = st.selectbox("Category 1", cat_options, format_func=cat_format, key="add_cat1")
        with col2:
            cat2 = st.selectbox("Category 2", cat_options, format_func=cat_format, key="add_cat2", index=1)

        submitted = st.form_submit_button("Add article", use_container_width=True)

        if submitted:
            if not title:
                st.error("Title is required.")
            else:
                article = {
                    "title": title,
                    "source": source,
                    "article_date": date.strftime("%d-%m-%Y"),
                    "url": url,
                    "text_clean": description,
                    "text_preview": description[:100] if description else "",
                    "top1": cat1,
                    "top1_confidence": 1.0,
                    "top2": cat2,
                    "top2_confidence": 0.0,
                    "confidence_gap": 1.0,
                    "week_number": None,
                    "curator_added": True,
                }
                st.session_state.curator_articles.append(article)
                st.success(f"Added: **{title}** → {CATEGORY_LABELS[cat1]} / {CATEGORY_LABELS[cat2]}")

    # Show previously added articles
    if st.session_state.curator_articles:
        st.subheader(f"Curator-added articles ({len(st.session_state.curator_articles)})")
        for i, art in enumerate(st.session_state.curator_articles):
            st.markdown(f"**{art['title']}** — {art['source']} · {art['article_date']} → {CATEGORY_LABELS.get(art['top1'], art['top1'])}")


# -----------------------------
# PAGE: ORGANISE
# -----------------------------
elif page == "Organise":
    st.title("Organise Newsletter")
    st.markdown("Accepted articles grouped by category. Select up to **3 per category** for the newsletter. Use **Move to** to reassign an article to a different category.")

    # Initialise newsletter selections
    if "newsletter_picks" not in st.session_state:
        st.session_state.newsletter_picks = set()
    if "category_overrides" not in st.session_state:
        st.session_state.category_overrides = {}  # {url: new_category}

    # Get accepted articles only
    accepted = []
    for url, dec in st.session_state.decisions.items():
        if dec["action"] == "reject":
            continue
        match = df[df["url"] == url]
        if len(match) > 0:
            row = match.iloc[0].to_dict()
        else:
            row = {"url": url, "title": "Unknown"}
        row["curator_label"] = dec["label"]
        # Apply category override if exists
        if url in st.session_state.category_overrides:
            row["curator_label"] = st.session_state.category_overrides[url]
        accepted.append(row)

    # Also add curator-added articles
    for art in st.session_state.curator_articles:
        art_copy = art.copy()
        art_copy["curator_label"] = art["top1"]
        art_copy["curator_added"] = True
        if art.get("url") in st.session_state.category_overrides:
            art_copy["curator_label"] = st.session_state.category_overrides[art["url"]]
        accepted.append(art_copy)

    if not accepted:
        st.warning("No accepted articles yet. Go to **Review Articles** and accept some articles first.")
    else:
        n_picked = len(st.session_state.newsletter_picks)
        st.info(f"**{len(accepted)} accepted articles** | **{n_picked} selected for newsletter**")

        # Group by category
        for cat_key in CATEGORY_ORDER:
            cat_label = CATEGORY_LABELS[cat_key]
            cat_articles = [a for a in accepted if a.get("curator_label") == cat_key]

            if not cat_articles:
                continue

            n_selected = sum(1 for a in cat_articles if a.get("url") in st.session_state.newsletter_picks)
            st.subheader(f"{cat_label} ({len(cat_articles)} articles, {n_selected} selected)")

            for art in cat_articles:
                art_url = art.get("url", "")
                is_picked = art_url in st.session_state.newsletter_picks
                is_curator = art.get("curator_added", False)
                badge = " <span style='background:#f39c12;color:white;padding:2px 6px;border-radius:3px;font-size:10px;'>CURATOR</span>" if is_curator else ""
                pick_badge = " <span style='background:#27ae60;color:white;padding:2px 6px;border-radius:3px;font-size:10px;'>SELECTED</span>" if is_picked else ""

                with st.container(border=True):
                    left, btn_col, move_col = st.columns([3, 1, 1])
                    with left:
                        st.markdown(f"**Article title:** {art.get('title', 'No title')}{badge}{pick_badge}", unsafe_allow_html=True)
                        source_name = SOURCE_LABELS.get(art.get('source', ''), art.get('source', ''))
                        st.markdown(f"**Article source:** {source_name}  |  **Date:** {art.get('article_date', '')}")
                    with btn_col:
                        if is_picked:
                            if st.button("Remove", key=f"unpick_{art_url}", use_container_width=True):
                                st.session_state.newsletter_picks.discard(art_url)
                                st.rerun()
                        else:
                            if n_selected >= 3:
                                st.button("Select (max 3)", key=f"pick_{art_url}", use_container_width=True, disabled=True)
                            else:
                                if st.button("Select", key=f"pick_{art_url}", use_container_width=True):
                                    st.session_state.newsletter_picks.add(art_url)
                                    st.rerun()
                    with move_col:
                        other_cats = [k for k in CATEGORY_LABELS if k != cat_key]
                        move_to = st.selectbox(
                            "Move to",
                            [""] + other_cats,
                            format_func=lambda x: "Move to..." if x == "" else CATEGORY_LABELS.get(x, x),
                            key=f"move_{art_url}",
                            label_visibility="collapsed",
                        )
                        if move_to:
                            st.session_state.category_overrides[art_url] = move_to
                            st.rerun()

        # Export newsletter selections
        st.markdown(f"<div style='border-top:3px solid #1d3461;margin:20px 0;'></div>", unsafe_allow_html=True)

        newsletter_articles = [a for a in accepted if a.get("url") in st.session_state.newsletter_picks]
        if newsletter_articles:
            st.markdown(f"**Newsletter selections: {len(newsletter_articles)} articles**")

            newsletter_df = pd.DataFrame(newsletter_articles)[["title", "curator_label", "url"]].copy()
            newsletter_df["curator_label"] = newsletter_df["curator_label"].map(lambda x: CATEGORY_LABELS.get(x, x))

            from io import BytesIO
            buffer_nl = BytesIO()
            newsletter_df.to_excel(buffer_nl, index=False, engine="openpyxl")
            buffer_nl.seek(0)

            st.download_button(
                "Download newsletter selections",
                buffer_nl,
                file_name=f"newsletter_selections_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )



# -----------------------------
# PAGE: NEWSLETTER DRAFT
# -----------------------------
elif page == "Newsletter Draft":
    st.title("Newsletter Draft")
    st.markdown("Preview and download the newsletter as plain text. Edit descriptions inline before downloading.")

    # Gather selected articles grouped by category
    accepted = []
    for url, dec in st.session_state.decisions.items():
        if dec["action"] == "reject":
            continue
        match = df[df["url"] == url]
        if len(match) > 0:
            row = match.iloc[0].to_dict()
        else:
            row = {"url": url, "title": "Unknown"}
        row["curator_label"] = dec["label"]
        if url in st.session_state.get("category_overrides", {}):
            row["curator_label"] = st.session_state.category_overrides[url]
        accepted.append(row)

    for art in st.session_state.curator_articles:
        art_copy = art.copy()
        art_copy["curator_label"] = art["top1"]
        if art.get("url") in st.session_state.get("category_overrides", {}):
            art_copy["curator_label"] = st.session_state.category_overrides[art["url"]]
        accepted.append(art_copy)

    picks = st.session_state.get("newsletter_picks", set())
    newsletter_articles = [a for a in accepted if a.get("url") in picks]

    if not newsletter_articles:
        st.warning("No articles selected for the newsletter. Go to **Organise** and select articles first.")
    else:
        today = datetime.now()
        newsletter_date = today.strftime("%d %B %Y")

        # Editable descriptions in session state
        if "draft_descriptions" not in st.session_state:
            st.session_state.draft_descriptions = {}

        # Header
        st.markdown(f"""
        <div style="background:#0f1e3d;color:white;padding:20px;border-radius:8px;text-align:center;margin-bottom:20px;">
            <div style="font-size:18px;font-weight:700;">ESRC Education Research Programme</div>
            <div style="font-size:14px;color:#8fa8c8;margin-top:4px;">ERP Newsletter</div>
            <div style="font-size:14px;color:#8fa8c8;">{newsletter_date}</div>
        </div>
        """, unsafe_allow_html=True)

        # Build plain text alongside the preview
        plain_text = f"ERP Newsletter\n{newsletter_date}\n\n"

        for cat_key in CATEGORY_ORDER:
            cat_articles = [a for a in newsletter_articles if a.get("curator_label") == cat_key]
            if not cat_articles:
                continue

            cat_label = CATEGORY_LABELS[cat_key]

            # Category header
            st.markdown(
                f"<div style='background:#1d3461;padding:10px 16px;border-radius:4px;margin:16px 0 8px 0;'>"
                f"<span style='color:#c8d8ec;font-size:15px;font-weight:600;'>{cat_label}</span></div>",
                unsafe_allow_html=True,
            )
            plain_text += f"\n{cat_label}\n\n"

            for art in cat_articles:
                art_url = art.get("url", "")
                title = art.get("title", "No title")
                source_name = SOURCE_LABELS.get(art.get("source", ""), art.get("source", ""))
                default_desc = str(art.get("text_clean", ""))[:300]

                # Editable description — empty by default for curator to write
                desc_key = f"desc_{art_url}"
                if desc_key not in st.session_state.draft_descriptions:
                    st.session_state.draft_descriptions[desc_key] = ""

                with st.container(border=True):
                    st.markdown(f"**{source_name} - {title}**")
                    edited_desc = st.text_area(
                        "Description",
                        value=st.session_state.draft_descriptions[desc_key],
                        key=desc_key,
                        height=80,
                        label_visibility="collapsed",
                    )
                    st.session_state.draft_descriptions[desc_key] = edited_desc
                    if art_url:
                        st.markdown(f"[Here]({art_url})")

                plain_text += f"{source_name} - {title}\n"
                plain_text += f"{st.session_state.draft_descriptions[desc_key]}\n"
                if art_url:
                    plain_text += f"Here: {art_url}\n"
                plain_text += "\n"

        # Footer
        plain_text += "\n---\n"
        plain_text += "You have indicated that you are happy to receive news and updates from the ESRC Education Research Programme. "
        plain_text += "To unsubscribe, please email nina.charalambous.15@ucl.ac.uk with the word UNSUBSCRIBE in the title of the email.\n"
        plain_text += "Do you find this newsletter useful? Are you happy with its frequency? Which section do you find most useful? "
        plain_text += "Any pressing topics we haven't covered? Any good sources of information you think we're missing? "
        plain_text += "How could we improve? We advocate for listening to different stakeholders and so we want your views too!\n"

        # Download
        st.markdown(f"<div style='border-top:3px solid #1d3461;margin:20px 0;'></div>", unsafe_allow_html=True)

        st.download_button(
            "Download newsletter draft (plain text)",
            plain_text,
            file_name=f"newsletter_draft_{today.strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True,
        )


# -----------------------------
# PAGE: FEEDBACK
# -----------------------------
elif page == "Feedback":
    st.title("Feedback")
    st.markdown("Help us improve the newsletter classification tool. Your feedback is used to refine the model and improve the curator experience.")

    with st.form("feedback_form", clear_on_submit=True):
        st.markdown("**How accurate were this week's classifications?**")
        accuracy_rating = st.select_slider(
            "Overall accuracy",
            options=["Very poor", "Poor", "OK", "Good", "Excellent"],
            value="OK",
        )

        st.markdown("**Were any categories consistently wrong?**")
        problem_cats = st.multiselect(
            "Select any categories that had frequent errors",
            options=CATEGORY_ORDER,
            format_func=lambda x: CATEGORY_LABELS.get(x, x),
        )

        st.markdown("**Are we missing any sources?**")
        missing_sources = st.text_area(
            "List any sources you think should be included in the pipeline",
            placeholder="e.g. NFER blog, Sutton Trust reports, a specific journal...",
            height=80,
        )

        st.markdown("**Any other suggestions?**")
        suggestions = st.text_area(
            "General feedback, feature requests, or comments",
            placeholder="e.g. categories need redefining, too many irrelevant articles, confidence scores not helpful...",
            height=100,
        )

        submitted = st.form_submit_button("Submit feedback", use_container_width=True)

        if submitted:
            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "accuracy_rating": accuracy_rating,
                "problem_categories": ", ".join(problem_cats) if problem_cats else "",
                "missing_sources": missing_sources,
                "suggestions": suggestions,
            }
            # Save to CSV
            feedback_path = DATA_DIR / "curator_feedback.csv"
            feedback_df = pd.DataFrame([feedback_entry])
            if feedback_path.exists():
                existing = pd.read_csv(feedback_path)
                feedback_df = pd.concat([existing, feedback_df], ignore_index=True)
            feedback_df.to_csv(feedback_path, index=False)
            st.success("Thank you — your feedback has been saved.")
