#!/usr/bin/env python3
"""
Simple test script to verify formatting features work without Lexical errors
"""

import streamlit as st
from __init__ import streamlit_lexical_extended

st.title("Formatting Features Test")

# Test content with all supported formatting
test_content = """# Heading 1
## Heading 2  
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6

**Bold text** and *italic text* and ~~strikethrough text~~

> This is a quote block

- Bullet list item 1
- Bullet list item 2
- Bullet list item 3

1. Numbered list item 1
2. Numbered list item 2
3. Numbered list item 3

| Table | Header | Example |
| ----- | ------ | ------- |
| Cell 1 | Cell 2 | Cell 3 |
| **Bold** | *Italic* | ~~Strike~~ |

Normal paragraph text with various formatting.
"""

if "content" not in st.session_state:
    st.session_state.content = test_content

st.write("**Test all formatting features:**")
st.write("- Headings H1-H6")
st.write("- Bold, italic, strikethrough")
st.write("- Quotes")
st.write("- Bullet and numbered lists")
st.write("- Tables")
st.write("- Keyboard shortcuts: Ctrl+Shift+X for strikethrough")

result = streamlit_lexical_extended(
    value=st.session_state.content,
    placeholder="Test formatting features here...",
    key="formatting_test",
    height=400,
)

if result:
    st.session_state.content = result
    
st.subheader("Output:")
st.code(result, language="markdown")

st.subheader("Rendered:")
st.markdown(result)