import streamlit as st
from __init__ import streamlit_lexical_extended


def on_change_editor():
    st.session_state["editor_content"] = st.session_state["editor"]
    with open("text.txt", "w") as f:
        f.write(st.session_state["editor_content"])

    # Add this line to prevent full re-run
    st.session_state["update_editor"] = False


st.write("#")
st.header("Lexical Rich Text Editor")

# Initialize the session state for editor content
if "editor_content" not in st.session_state:
    try:
        with open("text.txt", "r") as f:
            st.session_state["editor_content"] = f.read()
    except FileNotFoundError:
        st.session_state["editor_content"] = ""
    st.session_state["update_editor"] = True

# Create an instance of our component
streamlit_lexical_extended(
    value=st.session_state["editor_content"]
    if st.session_state.get("update_editor", True)
    else None,
    placeholder="Enter some rich text",
    key="editor",
    height=300,
    overwrite=False,
    on_change=on_change_editor,
)

st.markdown(st.session_state["editor_content"])
st.markdown("---")

# Display the current content in session state (for debugging)
st.write("Current content in session state:\n", st.session_state["editor_content"])
