#!/usr/bin/env python3
"""
Test script to verify table menu positioning works correctly within component bounds
"""

import streamlit as st
from __init__ import streamlit_lexical_extended

st.title("Table Menu Positioning Test")

# Test content with tables in different positions
test_content = """# Table Menu Positioning Test

Test the table context menu positioning by right-clicking on cells in different positions:

## Table at the beginning
| Left | Center | Right |
| ---- | ------ | ----- |
| Cell 1 | Cell 2 | Cell 3 |
| Cell 4 | Cell 5 | Cell 6 |

Some text between tables to create spacing.

## Table in the middle
| Column A | Column B | Column C | Column D | Column E |
| -------- | -------- | -------- | -------- | -------- |
| Data 1 | Data 2 | Data 3 | Data 4 | Data 5 |
| Data 6 | Data 7 | Data 8 | Data 9 | Data 10 |

More text to create spacing and push the next table down.

## Table near the bottom
| First | Second | Third | Fourth |
| ----- | ------ | ----- | ------ |
| A1 | B1 | C1 | D1 |
| A2 | B2 | C2 | D2 |
| A3 | B3 | C3 | D3 |

## Wide table to test horizontal positioning
| Col1 | Col2 | Col3 | Col4 | Col5 | Col6 | Col7 | Col8 |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Data | Data | Data | Data | Data | Data | Data | Data |
| More | More | More | More | More | More | More | More |

## Instructions:
1. Right-click on cells in the **leftmost** column - menu should appear to the right
2. Right-click on cells in the **rightmost** column - menu should appear to the left or be repositioned
3. Right-click on cells in the **top** rows - menu should appear below
4. Right-click on cells in the **bottom** rows - menu should appear above or be repositioned
5. Try clicking the chevron button (▼) that appears when you select a cell
6. Verify the menu never goes outside the editor boundaries
"""

if "table_content" not in st.session_state:
    st.session_state.table_content = test_content

st.write("**Test Instructions:**")
st.write("1. Right-click on table cells in different positions")
st.write("2. Click on cells to see the chevron button (▼)")
st.write("3. Verify the menu always stays within the editor boundaries")
st.write("4. Test with tables at different positions (top, bottom, left, right)")

result = streamlit_lexical_extended(
    value=st.session_state.table_content,
    placeholder="Test table menu positioning...",
    key="table_menu_test",
    height=500,  # Taller editor to test vertical positioning
)

if result:
    st.session_state.table_content = result

st.subheader("Expected Behavior:")
st.write("✅ Menu appears within editor boundaries")
st.write("✅ Menu repositions when near edges")
st.write("✅ Chevron button stays within editor")
st.write("✅ No menu overflow outside component")

st.subheader("Output:")
st.code(result, language="markdown")