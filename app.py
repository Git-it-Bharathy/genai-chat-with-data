import streamlit as st
import pandas as pd
import sqlite3
import sys
import os
import uuid

sys.path.append(os.path.dirname(__file__))
from utils.llm import generate_sql, explain_result

st.set_page_config(
    page_title="NISQL",
    page_icon="assets/favicon.png" if os.path.exists("assets/favicon.png") else None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Global styling: light, elegant, serif-accented ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,500;1,600&family=Inter:wght@400;500;600&display=swap');

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    .stApp {
        background-color: #FAFAF8;
        color: #1A1A1A;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #F3F2EE;
        border-right: 1px solid #E5E3DD;
    }
    section[data-testid="stSidebar"] * {
        color: #1A1A1A;
    }

    .main .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

    .pill-badge {
        display: inline-block;
        background-color: #EFEEE9;
        border: 1px solid #DDD9CF;
        border-radius: 999px;
        padding: 6px 16px;
        font-size: 0.85rem;
        color: #4A4A45;
        margin-bottom: 1.5rem;
    }
    .pill-badge::before {
        content: "● ";
        color: #2E7D32;
    }

    .hero-title {
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        font-size: 4rem;
        text-align: center;
        line-height: 1.1;
        margin-bottom: 0;
        color: #1A1A1A;
    }
    .hero-title-italic {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-weight: 500;
        font-size: 4rem;
        text-align: center;
        line-height: 1.1;
        color: #6B6B63;
        margin-bottom: 1.5rem;
    }
    .hero-desc {
        text-align: center;
        color: #6B6B63;
        font-size: 1.05rem;
        max-width: 620px;
        margin: 0 auto 2rem auto;
        line-height: 1.6;
    }

    .feature-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E3DD;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.25s ease;
        height: 100%;
    }
    .feature-card:hover {
        border-color: #1A1A1A;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        transform: translateY(-2px);
    }
    .feature-icon {
        font-size: 1.5rem;
        margin-bottom: 0.75rem;
    }
    .feature-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        color: #1A1A1A;
    }
    .feature-desc {
        color: #6B6B63;
        font-size: 0.92rem;
        line-height: 1.5;
    }

    .stButton button {
        border-radius: 8px;
        background-color: #FFFFFF;
        color: #1A1A1A;
        border: 1px solid #DDD9CF;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        border-color: #1A1A1A;
        background-color: #F3F2EE;
    }

    div[data-testid="stFileUploader"] {
        border: 1.5px dashed #DDD9CF;
        border-radius: 12px;
        padding: 1.5rem;
        background-color: #FFFFFF;
    }

    .stChatInput textarea {
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        border: 1px solid #DDD9CF !important;
    }
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E3DD;
        border-radius: 12px;
    }
    a { color: #1A1A1A !important; text-decoration: underline; }

    hr { border-color: #E5E3DD; }
    </style>
""", unsafe_allow_html=True)

# --- Session state setup ---
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "active_id" not in st.session_state:
    st.session_state.active_id = None
if "page" not in st.session_state:
    st.session_state.page = "intro"

def new_conversation():
    conv_id = str(uuid.uuid4())
    st.session_state.conversations[conv_id] = {
        "title": "New chat",
        "history": [],
        "df": None,
        "schema": None,
        "table_name": None,
        "db_path": None
    }
    st.session_state.active_id = conv_id

if not st.session_state.conversations:
    new_conversation()

def delete_conversation(conv_id):
    db_path = st.session_state.conversations[conv_id].get("db_path")
    if db_path and os.path.exists(db_path):
        os.remove(db_path)
    del st.session_state.conversations[conv_id]
    if st.session_state.active_id == conv_id:
        if st.session_state.conversations:
            st.session_state.active_id = list(st.session_state.conversations.keys())[-1]
        else:
            new_conversation()

# --- Sidebar ---
with st.sidebar:
    st.markdown("## ● NISQL")
    st.caption("Team Delta · Streamlit data analysis")
    st.divider()

    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("Introduction", use_container_width=True):
            st.session_state.page = "intro"
            st.rerun()
    with nav2:
        if st.button("Try NISQL", use_container_width=True):
            st.session_state.page = "app"
            st.rerun()

    st.divider()

    if st.button("+ New chat", use_container_width=True):
        new_conversation()
        st.session_state.page = "app"
        st.rerun()

    st.markdown("**History**")
    for conv_id, conv in reversed(list(st.session_state.conversations.items())):
        label = conv["title"] if conv["title"] != "New chat" else "New chat"
        is_active = conv_id == st.session_state.active_id
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(f"{'● ' if is_active else ''}{label}", key=f"hist_{conv_id}", use_container_width=True):
                st.session_state.active_id = conv_id
                st.session_state.page = "app"
                st.rerun()
        with col2:
            if st.button("✕", key=f"del_{conv_id}"):
                delete_conversation(conv_id)
                st.rerun()

    st.divider()
    st.caption("Built by Bharathy S — Team Delta")
    st.caption("[GitHub](https://github.com/Git-it-Bharathy)")

active = st.session_state.conversations[st.session_state.active_id]

# --- Helper functions ---
def build_schema(df: pd.DataFrame, table_name: str) -> str:
    lines = [f"Table: {table_name}", "Columns:"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        if "int" in dtype or "float" in dtype:
            dtype_label = "numeric"
        elif "datetime" in dtype:
            dtype_label = "datetime"
        else:
            dtype_label = "text"
        sample_vals = df[col].dropna().unique()[:5]
        sample_str = ", ".join(str(v) for v in sample_vals)
        lines.append(f"- {col} ({dtype_label}) — example values: {sample_str}")
    return "\n".join(lines)

def run_query(sql: str, db_path: str) -> pd.DataFrame:
    sql = sql.strip()
    if not sql.upper().startswith("SELECT"):
        raise ValueError(f"Only SELECT queries are allowed. Got: {sql[:50]}")
    conn = sqlite3.connect(db_path)
    result = pd.read_sql(sql, conn)
    conn.close()
    return result

def ask(schema, db_path, question, max_retries=2):
    error_context = None
    sql = None
    for _ in range(max_retries + 1):
        sql = generate_sql(schema, question, error_context)
        try:
            result = run_query(sql, db_path)
            return sql, result
        except Exception as e:
            error_context = str(e)
    raise RuntimeError(f"Failed after {max_retries+1} attempts. Last SQL:\n{sql}")

def try_render_chart(result: pd.DataFrame):
    if result.shape[0] < 2:
        return
    numeric_cols = result.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = result.select_dtypes(exclude="number").columns.tolist()
    if not numeric_cols or not non_numeric_cols:
        return
    chart_data = result.set_index(non_numeric_cols[0])[[numeric_cols[0]]]
    st.bar_chart(chart_data)

# --- Page: Introduction ---
if st.session_state.page == "intro":
    st.markdown('<div class="pill-badge">Team Delta · Streamlit data analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Ask your data</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title-italic">what matters next.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-desc">NISQL turns CSV and Excel files into conversational analysis, '
        'generating safe SQL, clear answers, and charts from plain-English questions.</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Try NISQL live →", use_container_width=True):
            st.session_state.page = "app"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📤</div>
                <div class="feature-title">Upload any dataset</div>
                <div class="feature-desc">Bring in CSV or Excel files and NISQL detects the columns, data types, and sample values automatically. No database setup or manual schema work required.</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <div class="feature-title">Ask in plain English</div>
                <div class="feature-desc">Ask questions like "Which region grew fastest?" or "Summarize this data." NISQL translates your words into safe, read-only SQLite queries behind the scenes.</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Answers with context</div>
                <div class="feature-desc">Every response turns query results into a concise explanation and an automatic chart when the shape of the data supports it. If a query fails, NISQL retries with the error context and corrects itself.</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align:center;">
            <p style="font-size:0.85rem; letter-spacing:1px; color:#6B6B63; text-transform:uppercase;">Ask your data in plain english</p>
            <div class="hero-title" style="font-size:2.2rem;">NISQL turns every dataset<br>into a conversation.</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-desc">Upload a CSV or Excel file and explore trends, totals, and patterns '
        'without writing SQL. Results can include an automatic chart when the data supports it.</div>',
        unsafe_allow_html=True
    )

# --- Page: App ---
elif st.session_state.page == "app":
    if active["df"] is None:
        st.markdown('<div class="hero-title" style="font-size:2.5rem;">Ready to explore?</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-desc">Upload a dataset and start asking questions in plain English</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"], label_visibility="collapsed")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                df.columns = df.columns.str.replace(" ", "_").str.replace("-", "_")

                table_name = "data"
                os.makedirs("data", exist_ok=True)
                db_path = f"data/{st.session_state.active_id}.db"
                conn = sqlite3.connect(db_path)
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                conn.close()

                active["df"] = df
                active["schema"] = build_schema(df, table_name)
                active["table_name"] = table_name
                active["db_path"] = db_path
                active["title"] = uploaded_file.name

                st.rerun()
            except Exception as e:
                st.error(f"Couldn't read this file: {e}")
        st.stop()

    st.markdown('<div class="hero-title" style="font-size:2.5rem;">Ready when you are</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-desc">{active["table_name"]} · {len(active["df"])} rows loaded</div>', unsafe_allow_html=True)

    with st.expander("Preview dataset & schema"):
        st.dataframe(active["df"].head())
        st.text(active["schema"])

    if not active["history"]:
        st.markdown("**Try asking:**")
        cols = st.columns(2)
        sample_questions = [
            "Give me a summary of this data",
            "What are the key trends here?",
            "Show me the top 5 rows by the largest numeric column",
            "Are there any missing values?"
        ]
        for i, sq in enumerate(sample_questions):
            if cols[i % 2].button(sq, use_container_width=True, key=f"sample_{i}"):
                st.session_state.pending_question = sq

    question = st.chat_input("Ask a question about your data...")

    if "pending_question" in st.session_state:
        question = st.session_state.pending_question
        del st.session_state.pending_question

    if question:
        if active["title"] == "New chat" or not active["history"]:
            active["title"] = question[:40] + ("..." if len(question) > 40 else "")

        with st.spinner("Thinking..."):
            try:
                sql, result = ask(active["schema"], active["db_path"], question)
                explanation = explain_result(question, sql, result)
                active["history"].append((question, sql, result, explanation))
            except Exception as e:
                active["history"].append((question, None, None, f"Error: {e}"))
        st.rerun()

    for q, sql, result, explanation in reversed(active["history"]):
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            st.write(explanation)
            if result is not None:
                try_render_chart(result)
            if sql:
                with st.expander("View SQL & raw data"):
                    st.code(sql, language="sql")
                    st.dataframe(result)