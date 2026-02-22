"""
SentimentFi — AI-Powered Onchain Sentiment Oracle on Monad
==========================================================
Streamlit Frontend with Monad UI Kit Dark Purple Theme

Run:  streamlit run app.py
"""

import sys
import os

# Ensure the project root is always on sys.path so ai_engine can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime

# Bridge Streamlit Cloud secrets → os.environ so ai_engine can read them via os.getenv()
for _key in ("MONAD_RPC_URL", "PRIVATE_KEY", "CONTRACT_ADDRESS"):
    if _key not in os.environ:
        try:
            os.environ[_key] = st.secrets[_key]
        except (KeyError, FileNotFoundError):
            pass

from ai_engine.sentiment_engine import analyze_sentiment_detailed, MODEL_NAME
from ai_engine.data_fetcher import fetch_all, fetch_by_query
from ai_engine.blockchain import (
    push_onchain,
    read_sentiment,
    get_explorer_url,
    check_connection,
)

# ── Page Config ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SentimentFi — AI Sentiment Oracle",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Monad UI Kit Theme (Dark Purple) ──────────────────────────────────
# Colors extracted from: https://github.com/airfoil-frontend/monad-ui-kit
# purple-400: hsla(249, 92%, 76%, 1)  →  #9B8AFA
# purple-500: hsla(249, 92%, 70%, 1)  →  #836EF9
# purple-600: hsla(249, 100%, 66%, 1) →  #7C52FF  (main brand)
# purple-900: hsla(263, 100%, 16%, 1) →  #2A0052
# background: hsl(240, 10%, 4%)       →  #0A0A10
# card:       hsl(0, 0%, 3.9%)        →  #0A0A0A
# secondary:  hsl(240, 4%, 16%)       →  #272729
# muted-fg:   hsl(0, 0%, 63.9%)      →  #A3A3A3

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ────────────────────────────────────────── */
    .stApp {
        background-color: #0A0A10 !important;
        color: #FAFAFA !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Top header bar ────────────────────────────────── */
    header[data-testid="stHeader"] {
        background-color: #0A0A10 !important;
    }

    /* ── Sidebar ───────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #111114 !important;
    }

    /* ── Metric cards ──────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1A1A2E 0%, #16162A 100%);
        border: 1px solid #272729;
        border-radius: 0.6rem;
        padding: 1rem 1.25rem;
    }
    div[data-testid="stMetric"] label {
        color: #A3A3A3 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #FAFAFA !important;
        font-weight: 700 !important;
    }

    /* ── Buttons ───────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #7C52FF 0%, #836EF9 100%) !important;
        color: #FAFAFA !important;
        border: none !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #9B8AFA 0%, #7C52FF 100%) !important;
        box-shadow: 0 0 20px rgba(124, 82, 255, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ── Select boxes / dropdowns ──────────────────────── */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1A1A2E !important;
        border: 1px solid #272729 !important;
        border-radius: 0.5rem !important;
    }
    .stSelectbox div[data-baseweb="select"] * {
        color: #FAFAFA !important;
    }

    /* ── Text area ─────────────────────────────────────── */
    .stTextArea textarea {
        background-color: #1A1A2E !important;
        color: #FAFAFA !important;
        border: 1px solid #272729 !important;
        border-radius: 0.5rem !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Expander ──────────────────────────────────────── */
    .streamlit-expanderHeader {
        background-color: #1A1A2E !important;
        color: #FAFAFA !important;
        border-radius: 0.5rem !important;
    }

    /* ── Tabs ──────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid #272729 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #A3A3A3 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTabs [aria-selected="true"] {
        color: #9B8AFA !important;
        border-bottom: 2px solid #7C52FF !important;
    }

    /* ── Charts ────────────────────────────────────────── */
    .stPlotlyChart, .stVegaLiteChart {
        background-color: transparent !important;
    }

    /* ── Success / Error / Warning ─────────────────────── */
    .stSuccess {
        background-color: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        color: #22C55E !important;
    }
    .stError {
        background-color: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }

    /* ── Divider ───────────────────────────────────────── */
    hr {
        border-color: #272729 !important;
    }

    /* ── Custom card class ─────────────────────────────── */
    .monad-card {
        background: linear-gradient(135deg, #1A1A2E 0%, #16162A 100%);
        border: 1px solid #272729;
        border-radius: 0.6rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .monad-card-glow {
        background: linear-gradient(135deg, #1A1A2E 0%, #1E1640 100%);
        border: 1px solid rgba(124, 82, 255, 0.3);
        border-radius: 0.6rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 0 15px rgba(124, 82, 255, 0.1);
    }

    /* ── Hero header ───────────────────────────────────── */
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #9B8AFA 0%, #7C52FF 50%, #FAFAFA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    .hero-subtitle {
        color: #A3A3A3;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }

    /* ── Score display ─────────────────────────────────── */
    .score-positive { color: #22C55E; font-size: 2rem; font-weight: 700; }
    .score-negative { color: #EF4444; font-size: 2rem; font-weight: 700; }
    .score-neutral  { color: #A3A3A3; font-size: 2rem; font-weight: 700; }

    /* ── Badge ─────────────────────────────────────────── */
    .monad-badge {
        display: inline-block;
        background: rgba(124, 82, 255, 0.15);
        color: #9B8AFA;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* ── Link styling ──────────────────────────────────── */
    a {
        color: #9B8AFA !important;
        text-decoration: none !important;
    }
    a:hover {
        color: #7C52FF !important;
        text-decoration: underline !important;
    }

    /* ── Scrollbar ─────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0A0A10;
    }
    ::-webkit-scrollbar-thumb {
        background: #272729;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #7C52FF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session State Init ────────────────────────────────────────────────

if "sentiment_history" not in st.session_state:
    st.session_state.sentiment_history = []

if "last_score" not in st.session_state:
    st.session_state.last_score = None

if "last_tx_hash" not in st.session_state:
    st.session_state.last_tx_hash = None

if "last_detail" not in st.session_state:
    st.session_state.last_detail = None

if "live_data" not in st.session_state:
    st.session_state.live_data = {}

if "live_texts" not in st.session_state:
    st.session_state.live_texts = []

if "query_results" not in st.session_state:
    st.session_state.query_results = {}


# ── Helper Functions ──────────────────────────────────────────────────

def get_score_class(score: float) -> str:
    if score > 0.05:
        return "score-positive"
    elif score < -0.05:
        return "score-negative"
    return "score-neutral"


def get_score_emoji(score: float) -> str:
    if score > 0.3:
        return "🟢"
    elif score > 0.05:
        return "🟡"
    elif score > -0.05:
        return "⚪"
    elif score > -0.3:
        return "🟠"
    return "🔴"


# ── Header ────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">🟣 SentimentFi</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">'
    "AI-Powered Onchain Sentiment Oracle on Monad — "
    "Analyze crypto sentiment and push it onchain"
    "</div>",
    unsafe_allow_html=True,
)

# Connection status (non-blocking)
try:
    conn = check_connection()
    if conn["connected"]:
        st.markdown(
            f'<span class="monad-badge">⚡ Connected to Monad • Chain {conn["chain_id"]} • Block #{conn["latest_block"]}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="monad-badge" style="background:rgba(239,68,68,0.15);color:#EF4444;">⚠️ Monad RPC offline — UI still functional</span>',
            unsafe_allow_html=True,
        )
except Exception:
    st.markdown(
        '<span class="monad-badge" style="background:rgba(239,68,68,0.15);color:#EF4444;">⚠️ RPC check skipped</span>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Main Layout ───────────────────────────────────────────────────────

col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    # ── Token Selection ───────────────────────────────────────────────
    st.markdown("### 🎯 Select Token")
    token = st.selectbox(
        "Choose a token to analyze",
        options=["MONAD", "BTC", "ETH"],
        label_visibility="collapsed",
    )

    # ── Live Data Section ─────────────────────────────────────────────
    st.markdown("### 📡 Live Signal Data")

    col_fetch, col_status = st.columns([2, 1])
    with col_fetch:
        # Read any custom query the user may have typed (persisted via key)
        _custom_q = st.session_state.get("custom_query_input", "").strip()
        _btn_label = f"🔎 Search '{_custom_q}'" if _custom_q else "🔄 Fetch Live Data"
        if st.button(_btn_label, use_container_width=True, key="fetch_btn"):
            if _custom_q:
                with st.spinner(f"Searching Reddit + News for '{_custom_q}'..."):
                    data = fetch_by_query(_custom_q)
                    data["_searched"] = True
                    st.session_state.query_results = data
                    st.session_state.live_texts = data["combined_texts"]
                    st.session_state.live_data = data
            else:
                with st.spinner(f"Fetching live data for {token}..."):
                    data = fetch_all(token)
                    st.session_state.live_data = data
                    st.session_state.live_texts = data["combined_texts"]
    with col_status:
        if st.session_state.live_data:
            d = st.session_state.live_data
            r_status = "🟢" if d["reddit_ok"] else "🔴"
            c_status = "🟢" if d["cryptopanic_ok"] else "🔴"
            st.markdown(
                f'<div class="monad-card" style="padding:0.6rem;font-size:0.8rem;">'  
                f"{r_status} Reddit &nbsp;|&nbsp; {c_status} CryptoPanic<br>"
                f"<strong>{d['total']}</strong> signals loaded"
                f"</div>",
                unsafe_allow_html=True,
            )

    tab_reddit, tab_cp, tab_custom = st.tabs(["🔴 Reddit", "📰 News", "✏️ Custom Input"])

    with tab_reddit:
        reddit_posts = st.session_state.live_data.get("reddit", [])
        if not reddit_posts:
            st.markdown(
                '<div class="monad-card" style="text-align:center;color:#A3A3A3;">'
                "Click <strong>🔄 Fetch Live Data</strong> to load Reddit posts."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            for p in reddit_posts:
                upvotes = f"⬆ {p['upvotes']:,}" if p.get("upvotes") is not None else ""
                st.markdown(
                    f'<div class="monad-card" style="padding:0.75rem;margin-bottom:0.4rem;">'
                    f"<strong>{p['title']}</strong><br>"
                    f"<span style='color:#A3A3A3;font-size:0.75rem;'>r/{p['subreddit']} &nbsp;•&nbsp; {p['age']} &nbsp;•&nbsp; {upvotes}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    with tab_cp:
        cp_posts = st.session_state.live_data.get("cryptopanic", [])
        if not cp_posts:
            st.markdown(
                '<div class="monad-card" style="text-align:center;color:#A3A3A3;">'
                "Click <strong>🔄 Fetch Live Data</strong> to load CryptoPanic headlines."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            for p in cp_posts:
                st.markdown(
                    f'<div class="monad-card" style="padding:0.75rem;margin-bottom:0.4rem;">'
                    f"<strong>{p['title']}</strong><br>"
                    f"<span style='color:#A3A3A3;font-size:0.75rem;'>{p.get('source','News')} &nbsp;•&nbsp; {p['age']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    with tab_custom:
        st.markdown(
            "<p style='color:#A3A3A3;font-size:0.85rem;margin-bottom:0.5rem;'>"
            "Type a topic below — the <strong>Fetch button above updates automatically</strong> "
            "to search Reddit + News for your query, then click <strong>🔍 Analyze Sentiment</strong>."
            "</p>",
            unsafe_allow_html=True,
        )
        custom_query = st.text_input(
            "Search topic:",
            placeholder="e.g.  monad testnet   |   bitcoin ETF   |   ethereum upgrade",
            label_visibility="collapsed",
            key="custom_query_input",
        )
        # Show results from last query fetch
        qr = st.session_state.query_results
        if qr.get("total", 0) > 0:
            r_ok = "🟢" if qr["reddit_ok"] else "🔴"
            n_ok = "🟢" if qr["cryptopanic_ok"] else "🔴"
            st.caption(
                f"{r_ok} Reddit: {len(qr['reddit'])} posts  |  "
                f"{n_ok} News: {len(qr['cryptopanic'])} articles  |  "
                f"Total: {qr['total']} signals"
            )
            with st.expander("📝 Preview fetched signals", expanded=False):
                for p in qr["reddit"][:4]:
                    st.markdown(
                        f'<div class="monad-card" style="padding:0.6rem;margin-bottom:0.3rem;">'
                        f"<strong>{p['title'][:90]}</strong><br>"
                        f"<span style='color:#A3A3A3;font-size:0.75rem;'>r/{p['subreddit']} • {p['age']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                for p in qr["cryptopanic"][:4]:
                    st.markdown(
                        f'<div class="monad-card" style="padding:0.6rem;margin-bottom:0.3rem;">'
                        f"<strong>{p['title'][:90]}</strong><br>"
                        f"<span style='color:#A3A3A3;font-size:0.75rem;'>{p.get('source','News')} • {p['age']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        elif qr.get("_searched"):
            st.warning("No results found for that query. Try broader keywords.")

    # ── Analyze Button ────────────────────────────────────────────────
    st.markdown("### ⚡ Actions")

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("🔍 Analyze Sentiment", use_container_width=True, key="analyze_btn"):
            with st.spinner("Running AI sentiment analysis..."):
                # Priority: custom query → live fetched token data → error
                _q = st.session_state.get("custom_query_input", "").strip()
                if _q:
                    with st.spinner(f"Searching Reddit + News for '{_q}'..."):
                        qdata = fetch_by_query(_q)
                        qdata["_searched"] = True
                        st.session_state.query_results = qdata
                        st.session_state.live_texts = qdata["combined_texts"]
                        st.session_state.live_data = qdata
                    texts = qdata["combined_texts"]
                    if not texts:
                        st.warning("No results found for that query. Try broader keywords.")
                elif st.session_state.live_texts:
                    texts = st.session_state.live_texts
                else:
                    texts = []

                if not texts:
                    st.error("No data to analyze! Enter a search topic above, or click 🔄 Fetch Live Data first.")
                else:
                    detail = analyze_sentiment_detailed(texts)
                    score = detail["score"]
                    st.session_state.last_score = score
                    st.session_state.last_detail = detail

                    # Add to history
                    st.session_state.sentiment_history.append(
                        {
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "token": token,
                            "score": round(score, 4),
                            "confidence": detail["confidence"],
                            "bullish": detail["bullish_count"],
                            "bearish": detail["bearish_count"],
                        }
                    )

                    emoji = get_score_emoji(score)
                    label = "Bullish" if score > 0.05 else "Bearish" if score < -0.05 else "Neutral"
                    st.success(
                        f"{emoji} **{token}** \u2192 **{score:+.4f}** ({label}) "
                        f"| Confidence: **{detail['confidence']:.1%}** "
                        f"| \U0001f7e2 {detail['bullish_count']} Bullish / \U0001f534 {detail['bearish_count']} Bearish"
                    )

    with col_btn2:
        if st.button("⛓️ Push Onchain", use_container_width=True, key="push_btn"):
            if st.session_state.last_score is None:
                st.error("Analyze sentiment first!")
            else:
                with st.spinner("Pushing to Monad..."):
                    try:
                        tx_hash = push_onchain(token, st.session_state.last_score)
                        st.session_state.last_tx_hash = tx_hash
                        explorer_url = get_explorer_url(tx_hash)

                        st.success("✅ Transaction confirmed on Monad!")
                        st.markdown(
                            f'<div class="monad-card-glow">'
                            f"<strong>Tx Hash:</strong><br>"
                            f"<code>{tx_hash}</code><br><br>"
                            f'<a href="{explorer_url}" target="_blank">'
                            f"🔗 View on Monad Explorer →</a>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    except Exception as e:
                        st.error(f"Transaction failed: {e}")


with col_right:
    # ── Score Display ─────────────────────────────────────────────────
    st.markdown("### 📈 Sentiment Score")

    if st.session_state.last_score is not None:
        score = st.session_state.last_score
        detail = st.session_state.last_detail
        score_class = get_score_class(score)
        emoji = get_score_emoji(score)

        st.markdown(
            f'<div class="monad-card-glow">'
            f'<div class="{score_class}">{emoji} {score:+.4f}</div>'
            f'<div style="color:#A3A3A3;font-size:0.8rem;margin-top:0.4rem;">'
            f"Onchain integer value: {int(score * 100)} &nbsp;|&nbsp; "
            f"-1.0 = max bearish, +1.0 = max bullish"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        if detail:
            c1, c2, c3 = st.columns(3)
            c1.metric("Confidence", f"{detail['confidence']:.1%}")
            c2.metric("🟢 Bullish", detail["bullish_count"])
            c3.metric("🔴 Bearish", detail["bearish_count"])

            with st.expander("🔬 Per-signal breakdown", expanded=False):
                st.caption(f"Model: `{detail['model']}`")
                rows = []
                for item in detail["breakdown"]:
                    rows.append({
                        "": "🟢" if item["label"] == "POSITIVE" else "🔴",
                        "Text": item["text"],
                        "Confidence": f"{item['confidence']:.1%}",
                        "Score": f"{item['contribution']:+.4f}",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.markdown(
            '<div class="monad-card-glow">'
            '<div class="score-neutral">— No data yet —</div>'
            '<div style="color:#A3A3A3;font-size:0.8rem;margin-top:0.4rem;">'
            "Click 'Analyze Sentiment' to generate a score"
            "</div></div>",
            unsafe_allow_html=True,
        )

    # ── Onchain Read + Verification ───────────────────────────────────
    st.markdown("### 🔗 Onchain Verification")

    if st.button("📖 Read & Verify Onchain", use_container_width=True, key="read_btn"):
        try:
            onchain_score = read_sentiment(token)
            if st.session_state.last_score is not None:
                ai_score = st.session_state.last_score
                drift = abs(ai_score - onchain_score)
                c1, c2 = st.columns(2)
                c1.metric("AI Score", f"{ai_score:+.2f}")
                c2.metric("Onchain Score", f"{onchain_score:+.2f}", delta=f"drift {drift:.4f}", delta_color="off")
                if drift < 0.01:
                    st.success("✅ Onchain value matches AI output exactly")
                else:
                    st.warning(f"⚠️ Drift {drift:.4f} — may be from a previous push")
            else:
                st.metric(f"{token} Onchain", f"{onchain_score:+.2f}", delta=f"raw: {int(onchain_score*100)}")
        except Exception as e:
            st.error(f"Read failed: {e}")

    # ── Transaction Info ──────────────────────────────────────────────
    if st.session_state.last_tx_hash:
        st.markdown("### 🧾 Last Transaction")
        tx = st.session_state.last_tx_hash
        url = get_explorer_url(tx)
        st.markdown(
            f'<div class="monad-card">'
            f"<strong>Hash:</strong><br>"
            f"<code style='color: #9B8AFA; font-size: 0.8rem;'>{tx}</code><br><br>"
            f'<a href="{url}" target="_blank">🔗 Monad Explorer →</a>'
            f"</div>",
            unsafe_allow_html=True,
        )

# ── History & Chart ───────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 📊 Sentiment History")

if st.session_state.sentiment_history:
    df = pd.DataFrame(st.session_state.sentiment_history)

    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        st.line_chart(
            df.set_index("timestamp")["score"],
            color="#7C52FF",
        )

    with col_table:
        show_cols = [c for c in ["timestamp", "token", "score", "confidence", "bullish", "bearish"] if c in df.columns]
        st.dataframe(
            df[show_cols],
            use_container_width=True,
            hide_index=True,
        )
else:
    st.markdown(
        '<div class="monad-card" style="text-align: center;">'
        '<span style="color: #A3A3A3;">No sentiment data yet. '
        "Analyze some tokens to see the history chart.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #A3A3A3; font-size: 0.8rem;">'
    "🟣 <strong>SentimentFi</strong> — AI-Powered Onchain Sentiment Oracle on Monad<br>"
    "</div>",
    unsafe_allow_html=True,
)
