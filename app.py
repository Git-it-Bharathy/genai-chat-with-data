import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(__file__))
from utils.db import run_query, SCHEMA
from utils.llm import generate_sql, explain_result

st.set_page_config(page_title="Chat with Your Data", page_icon="📊")
st.title("📊 Chat with Your Data")
st.caption("Ask questions about your sales data in plain English")

if "history" not in st.session_state:
    st.session_state.history = []

def ask(question, max_retries=2):
    error_context = None
    sql = None
    for _ in range(max_retries + 1):
        sql = generate_sql(SCHEMA, question, error_context)
        try:
            result = run_query(sql)
            return sql, result
        except Exception as e:
            error_context = str(e)
    raise RuntimeError(f"Failed after {max_retries+1} attempts. Last SQL:\n{sql}")

def try_render_chart(result: pd.DataFrame):
    """Auto-detect if the result is chartable and render it."""
    if result.shape[0] < 2:
        return  # single value, no point charting

    numeric_cols = result.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = result.select_dtypes(exclude="number").columns.tolist()

    if not numeric_cols or not non_numeric_cols:
        return  # need at least one label column + one numeric column

    label_col = non_numeric_cols[0]
    value_col = numeric_cols[0]

    chart_data = result.set_index(label_col)[[value_col]]
    st.bar_chart(chart_data)

question = st.chat_input("Ask a question about your data...")

if question:
    with st.spinner("Thinking..."):
        try:
            sql, result = ask(question)
            explanation = explain_result(question, sql, result)
            st.session_state.history.append((question, sql, result, explanation))
        except Exception as e:
            st.session_state.history.append((question, None, None, f"Error: {e}"))

for q, sql, result, explanation in reversed(st.session_state.history):
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