
import streamlit as st
from contextlib import contextmanager
import html as _html
import re
import math
import hashlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

 
# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="InsightForge AI | Conversational Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# =====================================================================
# DESIGN TOKENS
# =====================================================================
INK = "#0A0F1E"
SURFACE = "#111A2E"
SURFACE_2 = "#16213A"
LINE = "#223152"
TEXT = "#E8EEF9"
MUTED = "#8A9AB8"
TEAL = "#2DD4BF"
VIOLET = "#8B5CF6"
SKY = "#38BDF8"
AMBER = "#F59E0B"
ROSE = "#FB7185"
PALETTE = [TEAL, VIOLET, SKY, AMBER, ROSE, "#34D399", "#A78BFA", "#60A5FA"]
 
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
 
html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
.stApp {{
    background:
        radial-gradient(900px 400px at 85% -10%, rgba(139,92,246,0.18), transparent 60%),
        radial-gradient(800px 380px at 0% 0%, rgba(45,212,191,0.12), transparent 55%),
        {INK};
    color: {TEXT};
}}
#MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }}
 
/* ---------- Hero ---------- */
.hero {{
    display:flex; align-items:center; justify-content:space-between; gap:1rem;
    padding: 1.4rem 1.6rem; border-radius: 18px;
    background: linear-gradient(120deg, {SURFACE} 0%, {SURFACE_2} 100%);
    border: 1px solid {LINE}; margin-bottom: 1.4rem;
}}
.hero h1 {{
    font-family:'Space Grotesk',sans-serif; font-size: 2rem; font-weight:700;
    margin:0; letter-spacing:-0.5px; color:{TEXT};
}}
.hero p {{ margin:0.35rem 0 0 0; color:{MUTED}; font-size:0.98rem; }}
.pill-row {{ display:flex; gap:0.5rem; flex-wrap:wrap; }}
.pill {{
    padding: 0.3rem 0.75rem; border-radius: 999px; font-size: 0.78rem; font-weight:500;
    background: rgba(45,212,191,0.10); color:{TEAL}; border:1px solid rgba(45,212,191,0.35);
}}
.pill.v {{ background: rgba(139,92,246,0.12); color:#B8A2FF; border-color: rgba(139,92,246,0.4); }}
.pill.s {{ background: rgba(56,189,248,0.10); color:{SKY}; border-color: rgba(56,189,248,0.35); }}
 
/* ---------- KPI cards ---------- */
.kpi {{
    background: {SURFACE}; border:1px solid {LINE}; border-radius:16px;
    padding: 1rem 1.2rem; position:relative; overflow:hidden; height:100%;
}}
.kpi::before {{
    content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--accent);
}}
.kpi .label {{ color:{MUTED}; font-size:0.82rem; font-weight:500; }}
.kpi .value {{
    font-family:'Space Grotesk',sans-serif; font-size:1.85rem; font-weight:700;
    color:{TEXT}; margin-top:0.2rem; line-height:1.15; word-break:break-word;
}}
.kpi .hint {{ color:{MUTED}; font-size:0.78rem; margin-top:0.25rem; }}
 
/* ---------- Panels ---------- */
.panel-title {{
    font-family:'Space Grotesk',sans-serif; font-size:1.1rem; font-weight:600;
    color:{TEXT}; margin: 0.2rem 0 0.6rem 0;
}}
.insight {{
    background: linear-gradient(135deg, rgba(45,212,191,0.10), rgba(139,92,246,0.12));
    border:1px solid rgba(45,212,191,0.35); border-radius:16px; padding:1.1rem 1.3rem;
}}
.insight .tag {{ color:{TEAL}; font-weight:600; font-size:0.85rem; margin-bottom:0.3rem; }}
.insight .body {{ font-size:1.05rem; line-height:1.55; color:{TEXT}; }}
 
/* ---------- Empty state ---------- */
.step {{
    background:{SURFACE}; border:1px solid {LINE}; border-radius:16px; padding:1.2rem; height:100%;
}}
.step .num {{
    width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-family:'Space Grotesk',sans-serif; color:{INK}; background:var(--accent); margin-bottom:0.7rem;
}}
.step h4 {{ margin:0 0 0.3rem 0; color:{TEXT}; font-size:1.02rem; }}
.step p {{ margin:0; color:{MUTED}; font-size:0.9rem; line-height:1.5; }}
 
/* ---------- Streamlit widget overrides ---------- */
section[data-testid="stSidebar"] {{ background:#080C18; border-right:1px solid {LINE}; }}
section[data-testid="stSidebar"] h3 {{ color:{TEXT}; font-family:'Space Grotesk',sans-serif; }}
.stTextInput input {{
    background:{SURFACE} !important; color:{TEXT} !important; border:1px solid {LINE} !important;
    border-radius:12px !important; padding:0.85rem 1rem !important; font-size:1rem !important;
}}
.stTextInput input:focus {{ border-color:{TEAL} !important; box-shadow:0 0 0 3px rgba(45,212,191,0.2) !important; }}
.stButton > button {{
    border-radius:12px; border:1px solid {LINE}; background:{SURFACE}; color:{TEXT};
    font-weight:500; transition: all .15s ease;
}}
.stButton > button:hover {{ border-color:{TEAL}; color:{TEAL}; }}
.stButton > button[kind="primary"] {{
    background: linear-gradient(90deg, {TEAL}, {SKY}); color:{INK}; border:none; font-weight:700;
}}
.stButton > button[kind="primary"]:hover {{ color:{INK}; filter:brightness(1.08); }}
.stTabs [data-baseweb="tab-list"] {{ gap:0.4rem; border-bottom:1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ background:transparent; border-radius:10px 10px 0 0; color:{MUTED}; padding:0.5rem 1rem; }}
.stTabs [aria-selected="true"] {{ color:{TEAL} !important; }}
div[data-testid="stDataFrame"] {{ border:1px solid {LINE}; border-radius:12px; overflow:hidden; }}
.stExpander {{ background:{SURFACE}; border:1px solid {LINE} !important; border-radius:12px !important; }}
.stDownloadButton > button {{ border-radius:12px; background:{SURFACE} !important; border:1px solid {TEAL} !important; }}
.stDownloadButton > button p, .stDownloadButton > button span {{ color:{TEAL} !important; font-weight:600; }}
 
/* ---------- Dark file uploader ---------- */
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {{
    background:{SURFACE} !important; border:1px dashed {TEAL} !important; border-radius:14px !important;
}}
[data-testid="stFileUploader"] * {{ color:{TEXT} !important; }}
[data-testid="stFileUploader"] small {{ color:{MUTED} !important; }}
[data-testid="stFileUploader"] svg {{ fill:{MUTED} !important; }}
[data-testid="stFileUploader"] button {{
    background:{SURFACE_2} !important; border:1px solid {LINE} !important; border-radius:10px !important;
}}
[data-testid="stFileUploader"] button:hover {{ border-color:{TEAL} !important; }}
[data-testid="stFileUploaderFile"], [data-testid="stFileUploaderFile"] > div {{
    background:{SURFACE_2} !important; border-radius:10px !important;
}}
 
/* ---------- Visible text everywhere ---------- */
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div {{
    color:{TEXT} !important; font-family:'Space Grotesk',sans-serif; font-weight:700;
}}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color:#B4C2DC !important; }}
[data-testid="stAlert"] p, [data-testid="stAlert"] div {{ color:{TEXT} !important; }}
[data-testid="stCaptionContainer"], .stCaption {{ color:#B4C2DC !important; }}
label, .stSelectbox label p {{ color:#B4C2DC !important; }}
.stTabs [data-baseweb="tab"] p {{ color:#B4C2DC !important; font-weight:500; font-size:0.98rem; }}
.stTabs [data-baseweb="tab"]:hover p {{ color:{TEXT} !important; }}
.stTabs [aria-selected="true"] p {{ color:{TEAL} !important; font-weight:700; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color:{TEAL} !important; }}
.stButton > button p {{ color:inherit !important; }}
.stButton > button[kind="primary"] p {{ color:{INK} !important; font-weight:700; }}
 
/* ---------- Loader ---------- */
.loader-card {{
    display:flex; align-items:center; gap:1rem; padding:1rem 1.3rem; margin:0.6rem 0;
    background:{SURFACE}; border:1px solid {TEAL}; border-radius:14px;
    box-shadow:0 0 28px rgba(45,212,191,0.2);
}}
.loader-ring {{
    width:30px; height:30px; border-radius:50%; flex-shrink:0;
    border:4px solid rgba(45,212,191,0.2); border-top-color:{TEAL}; border-right-color:{VIOLET};
    animation:spin .8s linear infinite;
}}
.loader-text {{ color:{TEXT}; font-weight:600; font-size:1rem; }}
.loader-sub {{ color:{MUTED}; font-size:0.85rem; margin-top:0.1rem; }}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}
 
/* ---------- Themed data table ---------- */
.tbl-wrap {{
    max-height:460px; overflow:auto; background:{SURFACE};
    border:1px solid {LINE}; border-radius:14px;
}}
.tbl {{ width:100%; border-collapse:collapse; font-size:0.92rem; }}
.tbl th {{
    position:sticky; top:0; z-index:1; background:{SURFACE_2}; color:#B4C2DC;
    text-align:left; font-weight:600; padding:0.7rem 1rem; white-space:nowrap;
    border-bottom:1px solid {LINE};
}}
.tbl td {{
    padding:0.6rem 1rem; color:{TEXT}; white-space:nowrap;
    border-bottom:1px solid rgba(34,49,82,0.6);
}}
.tbl tr:nth-child(even) td {{ background:rgba(255,255,255,0.02); }}
.tbl tr:hover td {{ background:rgba(45,212,191,0.10); }}
.tbl td.num, .tbl th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.tbl td.num {{ color:{TEAL}; }}
.tbl-note {{ color:{MUTED}; font-size:0.82rem; margin-top:0.4rem; }}
.tbl-wrap::-webkit-scrollbar {{ height:10px; width:10px; }}
.tbl-wrap::-webkit-scrollbar-thumb {{ background:{LINE}; border-radius:8px; }}
 
/* ---------- Light surfaces get dark text ---------- */
[data-testid="stFileUploaderFile"] {{
    background:#E8EEF9 !important; border-radius:10px !important;
}}
[data-testid="stFileUploaderFile"] *,
[data-testid="stFileUploaderFile"] small {{ color:#0F172A !important; }}
[data-testid="stFileUploaderFile"] > div, [data-testid="stFileUploaderFile"] div[class] {{ background:transparent !important; }}
[data-testid="stFileUploaderFile"] button {{ background:transparent !important; border:none !important; }}
[data-testid="stFileUploaderFile"] button svg {{ fill:#0F172A !important; color:#0F172A !important; }}
 
.stExpander summary, [data-testid="stExpander"] summary {{
    background:#E8EEF9 !important; border-radius:12px !important;
}}
.stExpander summary *, [data-testid="stExpander"] summary * {{ color:#0F172A !important; font-weight:600; }}
.stExpander summary svg, [data-testid="stExpander"] summary svg {{ fill:#0F172A !important; color:#0F172A !important; }}
 
/* ---------- Loaded badge ---------- */
.loaded {{
    display:flex; align-items:center; justify-content:space-between; gap:0.6rem;
    background:rgba(34,197,94,0.10); border:1px solid rgba(34,197,94,0.45);
    border-radius:12px; padding:0.8rem 1rem; color:{TEXT}; font-weight:500; margin:0.6rem 0;
}}
.loaded .name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.loaded .tick {{
    flex-shrink:0; width:24px; height:24px; border-radius:50%; background:#22C55E; color:#fff;
    display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:800;
    box-shadow:0 0 12px rgba(34,197,94,0.55);
}}
 
/* ---------- Uploaded file chip: white background, black text ---------- */
[data-testid="stFileUploader"] [data-testid^="stFileChip"],
[data-testid="stFileUploader"] [data-testid^="stFileUploaderFile"] {{
    background:#FFFFFF !important; border-radius:10px !important;
}}
[data-testid="stFileUploader"] [data-testid^="stFileChip"] *,
[data-testid="stFileUploader"] [data-testid^="stFileUploaderFile"] * {{
    color:#0F172A !important; background:transparent !important;
}}
[data-testid="stFileUploader"] [data-testid^="stFileChip"] svg,
[data-testid="stFileUploader"] [data-testid^="stFileUploaderFile"] svg {{
    fill:#0F172A !important; color:#0F172A !important;
}}
[data-testid="stFileUploader"] [data-testid^="stFileChip"] button,
[data-testid="stFileUploader"] [data-testid^="stFileUploaderFile"] button {{
    border:none !important;
}}
 
/* ---------- Warning box ---------- */
.warnbox {{
    background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.5); border-radius:12px;
    padding:0.8rem 1rem; color:#FCD34D; font-size:0.93rem; margin-bottom:0.8rem;
}}
 
/* ---------- Chart explanation card ---------- */
.explain {{
    background:{SURFACE}; border:1px solid {LINE}; border-left:4px solid {VIOLET};
    border-radius:12px; padding:0.9rem 1.1rem; margin-top:0.4rem;
}}
.explain .etitle {{ color:#C4B5FD; font-weight:700; font-size:0.92rem; margin-bottom:0.4rem; }}
.explain ul {{ margin:0; padding-left:1.1rem; }}
.explain li {{ color:{TEXT}; font-size:0.94rem; line-height:1.55; margin-bottom:0.25rem; }}
.explain li b {{ color:{TEAL}; }}
</style>
""", unsafe_allow_html=True)
 
 
# =====================================================================
# UI HELPERS (presentation only, no business logic)
# =====================================================================
def explain_card(title, lines):
    if not lines:
        return
    items = "".join(f"<li>{l}</li>" for l in lines)
    st.markdown(f'<div class="explain"><div class="etitle">{title}</div><ul>{items}</ul></div>', unsafe_allow_html=True)
 
 
def describe_main(df, cat_col, metric):
    d = df[[cat_col, metric]].dropna(subset=[metric]).copy()
    if d.empty:
        return []
    lines = []
    m = pretty(metric)
    fv = lambda v: fmt_val(metric, v, df[metric])
    if is_time_like(d, cat_col):
        d[cat_col] = pd.to_datetime(d[cat_col])
        d = d.sort_values(cat_col)
        first, last = d.iloc[0], d.iloc[-1]
        peak, low = d.loc[d[metric].idxmax()], d.loc[d[metric].idxmin()]
        if first[metric] != 0:
            chg = (last[metric] - first[metric]) / abs(first[metric]) * 100
            word = "grew" if chg > 0 else "fell"
            lines.append(f"<b>Trend:</b> {m} {word} {abs(chg):.1f}% from {first[cat_col]:%b %Y} to {last[cat_col]:%b %Y}.")
        lines.append(f"<b>Peak:</b> highest at {fv(peak[metric])} on {peak[cat_col]:%b %Y}.")
        lines.append(f"<b>Low point:</b> lowest at {fv(low[metric])} on {low[cat_col]:%b %Y}.")
        return lines
 
    kind = metric_kind(metric)
    ds = d.sort_values(metric, ascending=False)
    lab = lambda r: _html.escape("Unknown" if pd.isna(r[cat_col]) else str(r[cat_col]))
    total = ds[metric].sum()
    top = ds.iloc[0]
    if kind == "sum" and total > 0:
        lines.append(f"<b>{lab(top)}</b> leads with {fv(top[metric])}, which is {top[metric] / total * 100:.1f}% of the total {m.lower()}.")
    else:
        lines.append(f"<b>{lab(top)}</b> has the highest {m.lower()} at {fv(top[metric])}.")
    if len(ds) >= 2:
        sec = ds.iloc[1]
        if kind == "sum" and sec[metric] > 0 and top[metric] > 0:
            lines.append(f"It is {top[metric] / sec[metric]:.1f}x the runner-up, <b>{lab(sec)}</b> ({fv(sec[metric])}).")
        else:
            lines.append(f"The runner-up is <b>{lab(sec)}</b> at {fv(sec[metric])}.")
    if kind == "sum" and len(ds) >= 4 and total > 0:
        t3 = ds[metric].head(3).sum() / total * 100
        mood = "heavily concentrated in a few categories" if t3 >= 70 else "fairly spread across categories"
        lines.append(f"The top 3 account for {t3:.1f}% of the total, so {m.lower()} is {mood}.")
    if len(ds) >= 3:
        lo = ds.iloc[-1]
        lines.append(f"The lowest is <b>{lab(lo)}</b> at {fv(lo[metric])}.")
    if kind == "avg" and len(ds) >= 2 and ds.iloc[-1][metric] > 0 and top[metric] > ds.iloc[-1][metric]:
        lines.append(f"The best group is {top[metric] / ds.iloc[-1][metric]:.1f}x the weakest.")
    if len(ds) > 15:
        lines.append(f"The chart shows the 15 largest of {len(ds):,} categories.")
    return lines
 
 
def describe_donut(df, cat_col, metric):
    d = df[[cat_col, metric]].dropna()
    d = d[d[metric] > 0].sort_values(metric, ascending=False)
    if len(d) < 2:
        return []
    total = d[metric].sum()
    top = d.iloc[0]
    share = top[metric] / total * 100
    lines = [f"<b>{_html.escape(str(top[cat_col]))}</b> holds the biggest slice at {share:.1f}%."]
    if share >= 50:
        lines.append("One category makes up more than half the total, so results depend heavily on it.")
    elif len(d) >= 3:
        t3 = d[metric].head(3).sum() / total * 100
        lines.append(f"The top 3 slices together cover {t3:.1f}%.")
    if len(d) > 8:
        lines.append("Only the 8 largest slices are drawn.")
    return lines
 
 
def describe_scatter(df, a, b):
    d = df[[a, b]].dropna()
    if len(d) < 3:
        return []
    r = d[a].corr(d[b])
    if pd.isna(r):
        return []
    strength = "strong" if abs(r) >= 0.7 else "moderate" if abs(r) >= 0.4 else "weak"
    direction = "positive" if r > 0 else "negative"
    meaning = f"when {pretty(a)} rises, {pretty(b)} tends to {'rise' if r > 0 else 'fall'}" if abs(r) >= 0.4 else "the two measures move mostly independently"
    return [f"<b>Relationship:</b> a {strength} {direction} link (correlation {r:.2f}); {meaning}."]
 
 
class ResultCheckError(Exception):
    """Raised when SQL runs but the result looks logically wrong."""
 
 
MEASURE_PAT = re.compile(r"(avg|average|mean|median|sum|total|count|cnt|rate|ratio|pct|percent|share|proportion|amount|revenue|sales|profit|price|fare|cost|score|max|min|number|qty|quantity|survival|passengers|records)", re.I)
RANK_PAT = re.compile(r"\b(highest|lowest|top|most|least|best|worst|maximum|minimum|largest|smallest|biggest|max|min)\b", re.I)
 
 
def split_columns(df):
    """Split result columns into dimensions (labels) and measures (numbers to chart)."""
    num = df.select_dtypes(include=["number"]).columns.tolist()
    measures = [c for c in num if MEASURE_PAT.search(str(c))]
    if not measures and num:
        last = num[-1]
        measures = [c for c in num if c == last or df[c].nunique() > 15 or not pd.api.types.is_integer_dtype(df[c])]
    dims = [c for c in df.columns if c not in measures]
    return dims, measures
 
 
def metric_kind(col):
    """'avg' for averages/rates (never summed), 'sum' for counts and totals."""
    if re.search(r"(avg|average|mean|median|rate|ratio|pct|percent|share|proportion|score|max|min)", str(col).lower()):
        return "avg"
    return "sum"
 
 
def fmt_val(col, v, series=None):
    """Format a number the way a human expects (percent for rates, commas for counts)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if not math.isfinite(x):
        return str(v)
    n = str(col).lower()
    if re.search(r"(pct|percent)", n):
        return f"{x:,.1f}%"
    if re.search(r"(rate|ratio|share|proportion)", n) and series is not None:
        sv = series.dropna()
        if len(sv) and sv.between(0, 1).all():
            return f"{x * 100:.1f}%"
        if len(sv) and sv.between(0, 100).all():
            return f"{x:.1f}%"
    if abs(x) < 1e15 and x == int(x):
        return f"{int(x):,}"
    return f"{x:,.2f}"
 
 
def row_label(row, dims):
    if row is None or not dims:
        return ""
    return " / ".join("Unknown" if pd.isna(row[d]) else str(row[d]) for d in dims)
 
 
def build_column_profile(frame):
    """Compact per-column facts (types, real values, ranges) so the LLM writes exact filters."""
    lines = []
    for c in frame.columns:
        s_ = frame[c]
        nn = s_.nunique(dropna=True)
        nulls = int(s_.isna().sum())
        if pd.api.types.is_numeric_dtype(s_):
            vals = sorted(s_.dropna().unique())
            if nn <= 2 and set(vals) <= {0, 1}:
                info = "binary flag 0/1 (AVG(col) is the rate of 1s)"
            elif nn <= 8:
                info = "numeric, values: " + ", ".join(f"{v:g}" for v in vals)
            else:
                info = f"numeric, {nn} distinct, range {s_.min():g} to {s_.max():g}"
        else:
            if nn <= 10:
                vals = s_.value_counts().head(10).index
                info = f"text, {nn} distinct, values: " + ", ".join(f"'{str(v)[:25]}'" for v in vals)
            else:
                ex = ", ".join(f"'{str(v)[:25]}'" for v in s_.dropna().unique()[:3])
                info = f"text, {nn} distinct, examples: {ex}"
        if nulls:
            info += f", {nulls} missing"
        quote = ' (use double quotes: "' + str(c) + '")' if re.search(r"[^0-9a-zA-Z_]", str(c)) else ""
        lines.append(f"- {c}{quote}: {info}")
    return "\n".join(lines)
 
 
def validate_result(df, question, n_src_rows):
    """Return a short reason if the result looks logically wrong, else None."""
    q = question.lower()
    if df.empty:
        return "the query returned no rows; check the filters and use the exact values from the column profile"
    dims, measures = split_columns(df)
    nums = df.select_dtypes(include=["number"]).columns.tolist()
    if len(df) >= 2:
        for i, a in enumerate(nums):
            for b in nums[i + 1:]:
                if (df[a] - df[b]).abs().max() < 1e-9:
                    return (f"columns {a} and {b} hold identical values, so the group condition was probably not applied per group; "
                            "use ONE query with CASE WHEN ... END AS group_label and GROUP BY group_label")
    if dims and 2 <= len(df) <= 10:
        for m in measures:
            if df[m].nunique(dropna=False) == 1:
                return (f"every group has the same {m} value, so the group condition was probably ignored; "
                        "use ONE query with CASE WHEN ... END AS group_label and GROUP BY group_label")
    if dims and RANK_PAT.search(q) and df[dims[0]].isna().any():
        return f"the result contains an empty (NULL) group in {dims[0]}; exclude it with WHERE {dims[0]} IS NOT NULL"
    if (measures and dims and len(df) > 30 and len(df) > 0.3 * n_src_rows
            and re.search(r"\b(count|how many|each|per|number of)\b", q)):
        return ("the grouping produced almost one group per row; group by a coarser category "
                "(for text, extract the needed part with SUBSTR and INSTR)")
    return None
 
 
def build_facts(df, max_rows=8):
    """Plain-text facts handed to the LLM, plus number tokens its answer must contain."""
    dims, measures = split_columns(df)
    n = len(df)
    tokens = []
 
    def row_text(r):
        label = row_label(r, dims)
        if measures:
            vals = ", ".join(f"{pretty(m)} = {fmt_val(m, r[m], df[m])}" for m in measures)
        else:
            vals = ", ".join(f"{c} = {r[c]}" for c in df.columns if c not in dims)
        return (label + ": " if label else "") + vals
 
    if n <= max_rows:
        shown = df
        lines = [row_text(r) for _, r in df.iterrows()]
        header = f"The result has {n} row(s). Every row:"
    else:
        m = measures[0] if measures else df.columns[-1]
        ordered = df.sort_values(m, ascending=False) if measures else df
        shown = pd.concat([ordered.head(3), ordered.tail(1)])
        lines = [row_text(r) for _, r in shown.iterrows()]
        header = f"The result has {n:,} rows. Top 3 and the lowest row:"
    if measures:
        for _, r in shown.iterrows():
            for m in measures[:2]:
                tokens.append(fmt_val(m, r[m], df[m]).rstrip("%"))
    return header + "\n" + "\n".join(lines), list(dict.fromkeys(tokens))
 
 
def summary_ok(text, tokens):
    t = (text or "").lower().strip()
    bad = ("i'm sorry", "i am sorry", "i can't", "i cannot", "as an ai", "unable to", "not applicable", "no data")
    if len(t) < 25 or any(b in t for b in bad):
        return False
    t2 = t.replace(",", "")
    return all(tok.replace(",", "").lower() in t2 for tok in tokens)
 
 
def fallback_summary(df):
    """Deterministic takeaway used when the LLM summary is wrong, incomplete or refuses."""
    dims, measures = split_columns(df)
    n = len(df)
    if not measures:
        return f"The query returned {n:,} rows across {len(df.columns)} columns."
    m = measures[0]
    if not dims or n == 1:
        r = df.iloc[0]
        return ", ".join(f"{pretty(c)} is {fmt_val(c, r[c], df[c])}" for c in measures) + "."
    ordered = df.sort_values(m, ascending=False)
    top, low = ordered.iloc[0], ordered.iloc[-1]
    hi = f"{row_label(top, dims)} ({fmt_val(m, top[m], df[m])})"
    lo = f"{row_label(low, dims)} ({fmt_val(m, low[m], df[m])})"
    if n <= 6:
        listing = "; ".join(f"{row_label(r, dims)} = {fmt_val(m, r[m], df[m])}" for _, r in df.iterrows())
        return f"{pretty(m)} by {', '.join(pretty(d) for d in dims)}: {listing}. Highest is {hi} and lowest is {lo}."
    return f"Across {n:,} groups, {hi} ranks highest on {pretty(m)}, while {lo} is lowest."
 
 
def build_grouped_chart(df, dims, metric):
    d = df.copy()
    for c in dims[:2]:
        d[c] = d[c].astype(object).where(d[c].notna(), "Unknown").astype(str)
    d["_lbl"] = d[metric].map(lambda v: fmt_val(metric, v, df[metric]))
    fig = px.bar(d, x=dims[0], y=metric, color=dims[1], barmode="group", text="_lbl",
                 color_discrete_sequence=PALETTE)
    fig.update_traces(texttemplate="%{text}", textposition="outside", cliponaxis=False,
                      marker_line_width=0, textfont=dict(color=TEXT))
    fig.update_xaxes(type="category", title=None)
    fig.update_yaxes(title=None)
    style_fig(fig)
    fig.update_layout(legend=dict(orientation="h", y=1.12, x=0, title=None, font=dict(color=MUTED)))
    return fig
 
 
def build_heatmap(df, dims, metric):
    d = df.copy()
    for c in dims[:2]:
        d[c] = d[c].astype(object).where(d[c].notna(), "Unknown").astype(str)
    pv = d.pivot_table(index=dims[1], columns=dims[0], values=metric, aggfunc="mean")
    text = [["" if pd.isna(v) else fmt_val(metric, v, df[metric]) for v in row] for row in pv.values]
    fig = go.Figure(go.Heatmap(
        z=pv.values, x=[str(c) for c in pv.columns], y=[str(i) for i in pv.index],
        text=text, texttemplate="%{text}", textfont=dict(color="#fff", size=14),
        colorscale=[[0, "#1E3A8A"], [0.5, VIOLET], [1, TEAL]], showscale=False, xgap=4, ygap=4,
        hovertemplate="%{y} / %{x}: %{text}<extra></extra>",
    ))
    style_fig(fig)
    fig.update_xaxes(type="category", title=dims[0].replace("_", " ").title())
    fig.update_yaxes(type="category", title=dims[1].replace("_", " ").title(), gridcolor="rgba(0,0,0,0)")
    return fig
 
 
def describe_grouped(df, dims, metric):
    d = df[dims[:2] + [metric]].dropna(subset=[metric])
    if d.empty:
        return []
    fv = lambda v: fmt_val(metric, v, df[metric])
    lab = lambda r: " / ".join(_html.escape("Unknown" if pd.isna(r[x]) else str(r[x])) for x in dims[:2])
    top, low = d.loc[d[metric].idxmax()], d.loc[d[metric].idxmin()]
    lines = [f"<b>Highest:</b> {lab(top)} at {fv(top[metric])}.", f"<b>Lowest:</b> {lab(low)} at {fv(low[metric])}."]
    if low[metric] > 0 and top[metric] > low[metric]:
        lines.append(f"The best combination is {top[metric] / low[metric]:.1f}x the weakest.")
    by = d.groupby(dims[1])[metric].mean().sort_values(ascending=False)
    if len(by) >= 2:
        lines.append(f"On average, <b>{_html.escape(str(by.index[0]))}</b> ({fv(by.iloc[0])}) is ahead of "
                     f"<b>{_html.escape(str(by.index[-1]))}</b> ({fv(by.iloc[-1])}) across {pretty(dims[0])} groups.")
    return lines
 
 
def render_table(df, max_rows=500, index=False):
    data = df.head(max_rows)
    if index:
        data = data.reset_index().rename(columns={"index": ""})
    plain_hint = ("year", "id", "code", "zip", "phone")
    head = ""
    for c in data.columns:
        cls = "num" if pd.api.types.is_numeric_dtype(data[c]) else ""
        head += f'<th class="{cls}">{_html.escape(str(c))}</th>'
    body = ""
    for _, row in data.iterrows():
        cells = ""
        for c in data.columns:
            v = row[c]
            is_num = pd.api.types.is_numeric_dtype(data[c])
            if pd.isna(v):
                txt = "—"
            elif is_num:
                plain = any(h in str(c).lower() for h in plain_hint)
                fv = float(v)
                if abs(fv) < 1e18 and fv == int(fv):
                    txt = str(int(v)) if plain else f"{int(v):,}"
                else:
                    txt = f"{float(v):,.2f}"
            else:
                txt = _html.escape(str(v))
            cells += f'<td class="{"num" if is_num else ""}">{txt}</td>'
        body += f"<tr>{cells}</tr>"
    html_out = f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    if len(df) > max_rows:
        html_out += f'<div class="tbl-note">Showing the first {max_rows:,} of {len(df):,} rows. Download the CSV for everything.</div>'
    st.markdown(html_out, unsafe_allow_html=True)
 
 
@contextmanager
def neon_loader(message, sub=""):
    box = st.empty()
    box.markdown(
        f'<div class="loader-card"><div class="loader-ring"></div>'
        f'<div><div class="loader-text">{message}</div><div class="loader-sub">{sub}</div></div></div>',
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        box.empty()
 
 
def fmt_num(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    a = abs(x)
    if a >= 1e9:
        return f"{x / 1e9:.2f}B"
    if a >= 1e6:
        return f"{x / 1e6:.2f}M"
    if a >= 1e4:
        return f"{x / 1e3:.1f}K"
    if x == int(x):
        return f"{int(x):,}"
    return f"{x:,.2f}"
 
 
def pretty(name):
    return str(name).replace("_", " ").title()
 
 
def kpi(label, value, hint="", accent=TEAL):
    return (
        f'<div class="kpi" style="--accent:{accent}">'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'<div class="hint">{hint}</div></div>'
    )
 
 
def style_fig(fig, height=380):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Inter, sans-serif", size=13),
        margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(bgcolor=SURFACE_2, bordercolor=TEAL, font=dict(color=TEXT)),
        coloraxis_showscale=False,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=False, linecolor=LINE, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor="rgba(138,154,184,0.12)", zeroline=False, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    return fig
 
 
def is_time_like(df, col):
    hint = any(k in str(col).lower() for k in ["date", "month", "year", "time", "day", "week", "quarter"])
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        return True
    if hint and df[col].dtype == object:
        try:
            pd.to_datetime(df[col])
            return True
        except Exception:
            return False
    return False
 
 
def build_main_chart(df, cat_col, metric):
    data = df.copy()
    if is_time_like(data, cat_col):
        data[cat_col] = pd.to_datetime(data[cat_col])
        data = data.sort_values(cat_col)
        fig = px.area(data, x=cat_col, y=metric, markers=True)
        fig.update_traces(
            line=dict(color=TEAL, width=3),
            fillcolor="rgba(45,212,191,0.18)",
            marker=dict(size=7, color=INK, line=dict(color=TEAL, width=2)),
        )
        return style_fig(fig)
 
    data = data.sort_values(metric, ascending=True).tail(15)
    data[cat_col] = data[cat_col].astype(object).where(data[cat_col].notna(), "Unknown")
    data["_lbl"] = data[metric].map(lambda v: fmt_val(metric, v, df[metric]))
    horizontal = len(data) > 5 or data[cat_col].astype(str).str.len().max() > 12
    if horizontal:
        fig = px.bar(
            data, x=metric, y=cat_col, orientation="h", color=metric,
            color_continuous_scale=[[0, "#1E3A8A"], [0.5, VIOLET], [1, TEAL]], text="_lbl",
        )
        fig.update_yaxes(type="category", title=None)
        fig.update_xaxes(title=None)
    else:
        data = data.sort_values(metric, ascending=False)
        fig = px.bar(
            data, x=cat_col, y=metric, color=metric,
            color_continuous_scale=[[0, "#1E3A8A"], [0.5, VIOLET], [1, TEAL]], text="_lbl",
        )
        fig.update_xaxes(type="category", title=None)
        fig.update_yaxes(title=None)
    fig.update_traces(
        texttemplate="%{text}", textposition="outside", cliponaxis=False,
        marker_line_width=0, textfont=dict(color=TEXT),
    )
    return style_fig(fig, height=max(340, 36 * len(data) + 80) if horizontal else 380)
 
 
def build_donut(df, cat_col, metric):
    data = df[[cat_col, metric]].copy()
    data = data[data[metric] > 0].sort_values(metric, ascending=False).head(8)
    fig = go.Figure(go.Pie(
        labels=data[cat_col].astype(str), values=data[metric], hole=0.68,
        marker=dict(colors=PALETTE, line=dict(color=INK, width=3)),
        textinfo="percent", textfont=dict(color="#fff", size=13), sort=False,
        hovertemplate="%{label}<br>%{value:,.2f} (%{percent})<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b style='font-size:22px'>{fmt_num(data[metric].sum())}</b><br><span style='color:{MUTED}'>Total</span>",
        showarrow=False, font=dict(color=TEXT),
    )
    style_fig(fig, height=380)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.08, font=dict(color=MUTED)))
    return fig
 
 
# =====================================================================
# HERO
# =====================================================================
st.markdown(
    '<div class="hero"><div>'
    '<h1>InsightForge AI</h1>'
    '<p>Turn any CSV into answers. Ask a question in plain English and get the SQL, a live dashboard and an executive insight in seconds.</p>'
    '</div>'
    '<div class="pill-row">'
    '<span class="pill">Local Ollama · qwen2.5-coder</span>'
    '<span class="pill v">Schema RAG · ChromaDB</span>'
    '<span class="pill s">Self-correcting SQL</span>'
    '</div></div>',
    unsafe_allow_html=True,
)
 
# =====================================================================
# SIDEBAR: UPLOAD + DATASET PROFILE
# =====================================================================
with st.sidebar:
    st.markdown("### Your dataset")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"], label_visibility="collapsed")
 
if "result" not in st.session_state:
    st.session_state.result = None
if "user_query" not in st.session_state:
    st.session_state.user_query = ""
if "auto_run" not in st.session_state:
    st.session_state.auto_run = False
 
 
def use_suggestion(text):
    st.session_state.user_query = text
    st.session_state.auto_run = True
 
 
if uploaded_file is not None:
    try:
        df_user = pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df_user = pd.read_csv(uploaded_file, encoding='latin1')
 
    # Reset stored result when a different file is uploaded
    file_key = f"{uploaded_file.name}-{uploaded_file.size}"
    if st.session_state.get("file_key") != file_key:
        st.session_state.file_key = file_key
        st.session_state.result = None
        st.session_state.user_query = ""
 
    num_cols_all = df_user.select_dtypes(include=["number"]).columns.tolist()
    cat_cols_all = [c for c in df_user.columns if c not in num_cols_all and df_user[c].nunique() <= 30]
    missing_pct = df_user.isna().sum().sum() / max(df_user.size, 1) * 100
 
    with st.sidebar:
        st.markdown(
            f'<div class="loaded"><span class="name">Loaded {_html.escape(uploaded_file.name)}</span><span class="tick">✓</span></div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        c1.metric("Rows", f"{len(df_user):,}")
        c2.metric("Columns", f"{len(df_user.columns)}")
        c3, c4 = st.columns(2)
        c3.metric("Numeric", f"{len(num_cols_all)}")
        c4.metric("Missing", f"{missing_pct:.1f}%")
 
        with st.expander("Column types"):
            render_table(pd.DataFrame({"column": df_user.columns, "type": df_user.dtypes.astype(str).values}))
        with st.expander("Preview first rows"):
            render_table(df_user.head(5))
 
    # Convert CSV to In-Memory SQLite Database
    engine = create_engine("sqlite:///:memory:")
    df_user.to_sql('dataset', con=engine, if_exists='replace', index=False)
    db = SQLDatabase(engine, sample_rows_in_table_info=2)
 
    # --- SCHEMA RAG INDEXING ---
    table_documents = []
    for table in db.get_usable_table_names():
        schema_info = db.get_table_info([table])
        doc = Document(
            page_content=f"Table Name: {table}\nSchema Details:\n{schema_info}\n\nColumn profile (use these exact values in filters):\n{build_column_profile(df_user)}",
            metadata={"table_name": table}
        )
        table_documents.append(doc)
 
    schema_key = "schema_" + hashlib.md5((file_key + str(list(df_user.columns))).encode()).hexdigest()[:12]
    vector_store = Chroma.from_documents(table_documents, embedding=None, collection_name=schema_key)
    retriever = vector_store.as_retriever(search_kwargs={"k": 1})
 
    # --- INITIALIZE OLLAMA MODEL & PROMPTS ---
    @st.cache_resource
    def load_llm():
        return ChatOllama(model="qwen2.5-coder:7b", temperature=0, num_ctx=2048, num_predict=512)
 
    llm = load_llm()
 
    sql_prompt = PromptTemplate.from_template("""
    You are an expert SQLite developer. Write ONE valid SQLite query that answers the user question.
    Output ONLY the executable SQL wrapped in markdown tags (```sql ... ```).
 
    Rules:
    1. Use only the table dataset and the columns in the schema. Wrap any column name that contains a dot, space or dash in double quotes.
    2. Use the column profile to write exact filters (real spelling of categories, 0/1 for flags).
    3. To compare groups (alone vs with family, survivors vs non-survivors, male vs female) write ONE query with CASE WHEN ... END AS group_label (or the column itself) and GROUP BY it, returning one row per group. Never repeat the same subquery per group and never put the group condition in WHERE.
       Example: SELECT CASE WHEN a = 0 AND b = 0 THEN 'Group 1' ELSE 'Group 2' END AS group_label, COUNT(*) AS total FROM dataset GROUP BY group_label;
    4. Rate or percentage of a 0/1 column: ROUND(AVG(col) * 100, 1) AS rate_pct. Averages: ROUND(AVG(col), 2).
    5. For highest, lowest, top or most questions: ORDER BY the metric and LIMIT, and exclude empty groups with WHERE group_col IS NOT NULL.
    6. To pull a word out of text use SUBSTR and INSTR (SQLite has no SPLIT or REGEXP). Example: the word between ', ' and '.' in a text column col is SUBSTR(col, INSTR(col, ', ') + 2, INSTR(col, '.') - INSTR(col, ', ') - 2).
    7. Give every output column a short snake_case alias. Do not return raw ID or name columns unless asked.
 
    Retrieved Schema:
    {schema}
 
    Question: {question}
    """)
    sql_chain = sql_prompt | llm | StrOutputParser()
 
    correction_prompt = PromptTemplate.from_template("""
    You are an expert SQLite debugging assistant.
    User Question: "{question}"
    Retrieved Schema: {schema}
    Failed SQL: {bad_sql}
    Problem: {error_message}
 
    Fix the query. Remember: ONE query, use CASE WHEN ... END AS group_label with GROUP BY to compare groups, double-quote column names that contain dots, exclude NULL groups for ranking questions, and give every column a snake_case alias.
    Return ONLY valid SQL in markdown tags (```sql ... ```).
    """)
    correction_chain = correction_prompt | llm | StrOutputParser()
 
    summary_prompt = PromptTemplate.from_template("""
    You are a business intelligence analyst. Explain the result below to a non-technical reader in 2 to 3 short sentences.
    Use ONLY the facts given and copy the numbers exactly. If the result has 8 rows or fewer, mention EVERY row and its value. Otherwise mention the top 3 and the lowest. Say which is highest and which is lowest.
    Never apologise, never say you cannot summarise, and never ask questions.
 
    Question: {question}
    Facts:
    {facts}
 
    Summary:
    """)
    summary_chain = summary_prompt | llm | StrOutputParser()
 
    # =================================================================
    # QUESTION BAR
    # =================================================================
    st.markdown('<div class="panel-title">What do you want to know?</div>', unsafe_allow_html=True)
    try:
        ask_col, btn_col = st.columns([5, 1.2], gap="small", vertical_alignment="center")
    except TypeError:  # older Streamlit versions
        ask_col, btn_col = st.columns([5, 1.2], gap="small")
    with ask_col:
        user_query = st.text_input(
            "Ask a question", key="user_query", label_visibility="collapsed",
            placeholder="e.g. What is the total revenue grouped by product category?",
        )
    with btn_col:
        run_clicked = st.button("Run analysis", type="primary", use_container_width=True)
 
    # Suggested questions generated from the dataset's own columns
    suggestions = []
    if num_cols_all and cat_cols_all:
        n, c = num_cols_all[0], cat_cols_all[0]
        suggestions = [
            f"What is the total {n} by {c}?",
            f"Show the top 5 {c} by {n}",
            f"What is the average {n} for each {c}?",
            f"How many records are there per {c}?",
        ]
    elif num_cols_all:
        n = num_cols_all[0]
        suggestions = [f"What is the total {n}?", f"What is the average {n}?", f"Show the 10 highest {n} values"]
    if suggestions:
        st.caption("Try one of these")
        chip_cols = st.columns(len(suggestions))
        for i, s in enumerate(suggestions):
            chip_cols[i].button(s, key=f"sugg_{i}", on_click=use_suggestion, args=(s,), use_container_width=True)
 
    run_requested = run_clicked or st.session_state.auto_run
    st.session_state.auto_run = False
 
    # =================================================================
    # CORE PIPELINE (logic unchanged)
    # =================================================================
    if run_requested:
        if not user_query.strip():
            st.warning("Type a question first, then press Run analysis.")
        else:
            with neon_loader("Analysing your data...", "Finding the right schema, writing SQL and verifying it runs"):
                # 1. Schema RAG Retrieval
                relevant_docs = retriever.invoke(user_query)
                retrieved_schema = "\n\n".join([doc.page_content for doc in relevant_docs])
 
                # 2. Initial SQL Generation
                raw_response = sql_chain.invoke({"schema": retrieved_schema, "question": user_query})
                current_sql = raw_response.replace("```sql", "").replace("```", "").strip()
 
                # 3. Execution & Self-Correction Loop (also checks that the result makes sense)
                max_retries = 3
                success = False
                final_df = None
                status_logs = []
                fallback_df, fallback_sql, warning = None, None, None
 
                for attempt in range(max_retries):
                    try:
                        trial_df = pd.read_sql_query(current_sql, engine)
                        issue = validate_result(trial_df, user_query, len(df_user))
                        if issue:
                            fallback_df, fallback_sql, warning = trial_df, current_sql, issue
                            if attempt < max_retries - 1:
                                raise ResultCheckError(issue)
                        else:
                            warning = None
                        final_df = trial_df
                        success = True
                        status_logs.append(f"Attempt {attempt + 1}: Query Executed Successfully ✅")
                        break
                    except Exception as e:
                        error_msg = str(e)
                        if isinstance(e, ResultCheckError):
                            status_logs.append(f"Attempt {attempt + 1}: Result looked wrong and was flagged ⚠️ ({error_msg})")
                            error_msg = "The query ran but the result looks wrong: " + error_msg
                        else:
                            status_logs.append(f"Attempt {attempt + 1} Failed: {error_msg} ❌")
                        if attempt < max_retries - 1:
                            status_logs.append("Triggering Ollama Self-Correction Engine... 🔄")
                            corrected_raw = correction_chain.invoke({
                                "question": user_query,
                                "schema": retrieved_schema,
                                "bad_sql": current_sql,
                                "error_message": error_msg
                            })
                            current_sql = corrected_raw.replace("```sql", "").replace("```", "").strip()
 
                if not success and fallback_df is not None:
                    final_df, current_sql, success = fallback_df, fallback_sql, True
                    status_logs.append("Used the closest result found ⚠️")
 
                # 4. Key takeaway: LLM writes it from verified facts; checked, with a safe fallback
                ai_summary = None
                if success:
                    facts_text, tokens = build_facts(final_df)
                    try:
                        raw_summary = summary_chain.invoke({"question": user_query, "facts": facts_text}).strip()
                    except Exception:
                        raw_summary = ""
                    ai_summary = raw_summary if summary_ok(raw_summary, tokens) else fallback_summary(final_df)
 
            st.session_state.result = {
                "question": user_query, "sql": current_sql, "df": final_df,
                "logs": status_logs, "success": success, "summary": ai_summary,
                "warning": warning if success else None,
            }
 
    # =================================================================
    # RESULTS DASHBOARD
    # =================================================================
    res = st.session_state.result
    if res is None:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("Your dashboard will appear here. Pick a suggested question or type your own.")
    elif not res["success"]:
        st.error("The query still failed after 3 automatic fixes. Try rephrasing the question using your column names.")
        with st.expander("See what was attempted"):
            for log in res["logs"]:
                st.write(log)
            st.code(res["sql"], language="sql")
    else:
        rdf = res["df"]
        dims, measures = split_columns(rdf)
        retries = sum(1 for l in res["logs"] if ("Failed" in l or "flagged" in l))
 
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="panel-title">Results for: “{_html.escape(res["question"])}”</div>', unsafe_allow_html=True)
 
        # ---- KPI row ----
        k = st.columns(4, gap="medium")
        k[0].markdown(kpi("Rows returned", f"{len(rdf):,}", "from your dataset", TEAL), unsafe_allow_html=True)
        if measures:
            m0 = measures[0]
            col0 = rdf[m0]
            has_vals = col0.notna().any()
            hi_lab = row_label(rdf.loc[col0.idxmax()], dims) if (has_vals and dims) else "Max value"
            lo_lab = row_label(rdf.loc[col0.idxmin()], dims) if (has_vals and dims) else "Min value"
            if len(rdf) == 1:
                k[1].markdown(kpi(pretty(m0), fmt_val(m0, col0.iloc[0], col0), "result of your query", VIOLET), unsafe_allow_html=True)
                if len(measures) > 1:
                    m1 = measures[1]
                    k[2].markdown(kpi(pretty(m1), fmt_val(m1, rdf[m1].iloc[0], rdf[m1]), "second measure", SKY), unsafe_allow_html=True)
                else:
                    k[2].markdown(kpi("Columns", f"{len(rdf.columns)}", "in the result", SKY), unsafe_allow_html=True)
            elif metric_kind(m0) == "sum":
                k[1].markdown(kpi(f"Total {pretty(m0)}", fmt_num(col0.sum()), "sum across returned rows", VIOLET), unsafe_allow_html=True)
                k[2].markdown(kpi("Highest", fmt_val(m0, col0.max(), col0), hi_lab, SKY), unsafe_allow_html=True)
            else:
                k[1].markdown(kpi("Lowest", fmt_val(m0, col0.min(), col0), lo_lab, VIOLET), unsafe_allow_html=True)
                k[2].markdown(kpi("Highest", fmt_val(m0, col0.max(), col0), hi_lab, SKY), unsafe_allow_html=True)
        else:
            k[1].markdown(kpi("Columns", f"{len(rdf.columns)}", "in the result", VIOLET), unsafe_allow_html=True)
            k[2].markdown(kpi("Numeric columns", "0", "no chart available", SKY), unsafe_allow_html=True)
        k[3].markdown(
            kpi("Auto-fixes used", f"{retries}", "SQL passed on first try" if retries == 0 else "SQL repaired automatically", AMBER),
            unsafe_allow_html=True,
        )
 
        st.markdown("<br>", unsafe_allow_html=True)
 
        # ---- Warning (only when the result could not be fully verified) ----
        if res.get("warning"):
            st.markdown(
                f'<div class="warnbox">⚠️ This result may not fully answer your question: {_html.escape(res["warning"])}. '
                'Try rephrasing, or check the generated SQL.</div>',
                unsafe_allow_html=True,
            )
 
        # ---- AI insight ----
        st.markdown(
            f'<div class="insight"><div class="tag">Key takeaway</div><div class="body">{_html.escape(res["summary"])}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
 
        # ---- Tabs ----
        tab_dash, tab_data, tab_sql = st.tabs(["Dashboard", "Data table", "SQL and logs"])
 
        with tab_dash:
            if measures and dims and len(rdf) >= 2:
                metric = measures[0]
                if len(measures) > 1:
                    metric = st.selectbox("Metric to chart", measures, format_func=pretty)
                cat_col = dims[0]
                left, right = st.columns([1.5, 1], gap="large")
                if len(dims) >= 2 and not is_time_like(rdf, dims[0]):
                    with left:
                        st.markdown(f'<div class="panel-title">{pretty(metric)} by {pretty(dims[0])} and {pretty(dims[1])}</div>', unsafe_allow_html=True)
                        st.plotly_chart(build_grouped_chart(rdf, dims, metric), use_container_width=True, config={"displayModeBar": False})
                        explain_card("What this chart tells you", describe_grouped(rdf, dims, metric))
                    with right:
                        st.markdown('<div class="panel-title">Heatmap view</div>', unsafe_allow_html=True)
                        st.plotly_chart(build_heatmap(rdf, dims, metric), use_container_width=True, config={"displayModeBar": False})
                        explain_card("How to read the heatmap", ["Each cell is one combination. Bright teal means a higher value and deep blue a lower one."])
                else:
                    with left:
                        st.markdown(f'<div class="panel-title">{pretty(metric)} by {pretty(cat_col)}</div>', unsafe_allow_html=True)
                        st.plotly_chart(build_main_chart(rdf, cat_col, metric), use_container_width=True, config={"displayModeBar": False})
                        explain_card("What this chart tells you", describe_main(rdf, cat_col, metric))
                    with right:
                        if metric_kind(metric) == "sum" and (rdf[metric] > 0).sum() >= 2 and not is_time_like(rdf, cat_col):
                            st.markdown('<div class="panel-title">Share of total</div>', unsafe_allow_html=True)
                            st.plotly_chart(build_donut(rdf, cat_col, metric), use_container_width=True, config={"displayModeBar": False})
                            explain_card("How to read the split", describe_donut(rdf, cat_col, metric))
                        else:
                            st.markdown('<div class="panel-title">Summary stats</div>', unsafe_allow_html=True)
                            render_table(rdf[measures].describe().T.round(2), index=True)
            elif len(measures) >= 2 and not dims:
                st.markdown(f'<div class="panel-title">{pretty(measures[0])} vs {pretty(measures[1])}</div>', unsafe_allow_html=True)
                fig = px.scatter(rdf, x=measures[0], y=measures[1], color_discrete_sequence=[TEAL])
                fig.update_traces(marker=dict(size=10, opacity=0.85, line=dict(color=INK, width=1)))
                st.plotly_chart(style_fig(fig), use_container_width=True, config={"displayModeBar": False})
                explain_card("What this chart tells you", describe_scatter(rdf, measures[0], measures[1]))
            else:
                st.info("This answer is a single value or has no numeric columns, so the KPI cards above and the data table tell the full story.")
 
        with tab_data:
            render_table(rdf)
            st.download_button(
                "Download results as CSV", rdf.to_csv(index=False).encode("utf-8"),
                file_name="query_results.csv", mime="text/csv",
            )
 
        with tab_sql:
            st.markdown('<div class="panel-title">Generated SQL</div>', unsafe_allow_html=True)
            st.code(res["sql"], language="sql")
            st.markdown('<div class="panel-title">Execution log</div>', unsafe_allow_html=True)
            for log in res["logs"]:
                st.write(log)
 
else:
    # =================================================================
    # EMPTY STATE: guided onboarding instead of a blank page
    # =================================================================
    s1, s2, s3 = st.columns(3, gap="medium")
    s1.markdown(
        '<div class="step" style="--accent:#2DD4BF"><div class="num">1</div>'
        '<h4>Upload a CSV</h4><p>Use the panel on the left. Your file is loaded into a private in-memory database and never leaves your machine.</p></div>',
        unsafe_allow_html=True,
    )
    s2.markdown(
        '<div class="step" style="--accent:#8B5CF6"><div class="num">2</div>'
        '<h4>Ask in plain English</h4><p>Type a business question or pick a suggested one. The engine finds the right schema and writes the SQL for you.</p></div>',
        unsafe_allow_html=True,
    )
    s3.markdown(
        '<div class="step" style="--accent:#38BDF8"><div class="num">3</div>'
        '<h4>Get a dashboard</h4><p>See key numbers, charts, the raw data and a written takeaway. Failed queries are repaired automatically.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("Start by uploading a CSV file in the sidebar.")
 
