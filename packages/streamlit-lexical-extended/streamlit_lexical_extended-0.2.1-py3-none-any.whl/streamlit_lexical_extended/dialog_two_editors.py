#!/usr/bin/env python3
import streamlit as st
from __init__ import streamlit_lexical_extended as editor

st.set_page_config(page_title="Lexical dialog demo", page_icon="📝", layout="wide")

st.title("Dialog with two editors")
st.write("Click the button to open the dialog with two independent editors.")

# Initialize state for both editors
if "doc1" not in st.session_state:
    st.session_state["doc1"] = "# Editor 1\n\nStart typing..."
if "doc2" not in st.session_state:
    st.session_state["doc2"] = "# Editor 2\n\nStart typing..."

@st.dialog("Two editors", width="large", dismissible=True)
def edit_two():
    st.caption("Each editor has its own state. Closing the dialog returns to the main page.")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Editor A")
        val1 = editor(
            value=st.session_state["doc1"],
            placeholder="Type in editor A",
            key="dialog_editor_a",
            height=420,
            overwrite=True,
        )
        if val1 is not None:
            st.session_state["doc1"] = val1

    with col2:
        st.subheader("Editor B")
        val2 = editor(
            value=st.session_state["doc2"],
            placeholder="Type in editor B",
            key="dialog_editor_b",
            height=420,
            overwrite=True,
        )
        if val2 is not None:
            st.session_state["doc2"] = val2

    st.divider()
    if st.button("Close"):
        # Cause a full rerun; since we won't call edit_two() on the next run,
        # the dialog will be closed.
        st.rerun()

# Open dialog button
st.button("Open dialog", on_click= edit_two)

st.markdown("### Current content")
col1, col2 = st.columns(2)
with col1:
    st.write("Editor A content:")
    st.code(st.session_state["doc1"], language="markdown")
with col2:
    st.write("Editor B content:")
    st.code(st.session_state["doc2"], language="markdown")
