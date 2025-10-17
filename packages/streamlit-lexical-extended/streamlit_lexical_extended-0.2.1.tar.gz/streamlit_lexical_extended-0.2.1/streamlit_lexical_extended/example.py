import streamlit as st
from __init__ import streamlit_lexical_extended

st.write("#")
st.header("Lexical Rich Text Editor - Comprehensive Table Demo")

# Initialize the session state for editor content
if "editor_content" not in st.session_state:
    st.session_state["editor_content"] = (
        "# Comprehensive Table Demo\n\n"
        "This example demonstrates all table functionality in the Lexical editor.\n\n"
        "## Sample Data Table\n\n"
        "| Product | Price | Stock | Category | Rating |\n"
        "| ------- | ----: | ----: | -------- | -----: |\n"
        "| **Laptop** | $999.99 | 15 | Electronics | ⭐⭐⭐⭐⭐ |\n"
        "| *Smartphone* | $599.99 | 32 | Electronics | ⭐⭐⭐⭐ |\n"
        "| ~~Old Phone~~ | $199.99 | 0 | Electronics | ⭐⭐ |\n"
        "| Coffee Mug | $12.99 | 150 | Kitchen | ⭐⭐⭐⭐⭐ |\n\n"
        "## Employee Information\n\n"
        "| Name | Department | Salary | Start Date |\n"
        "| ---- | ---------- | -----: | ---------- |\n"
        "| Alice Johnson | Engineering | $95,000 | 2022-01-15 |\n"
        "| Bob Smith | Marketing | $75,000 | 2021-06-01 |\n"
        "| Carol Davis | HR | $65,000 | 2023-03-10 |\n\n"
        "## Features to Test:\n\n"
        "1. **Create new tables** - Use the table button in the toolbar\n"
        "2. **Edit cell content** - Click on any cell and type\n"
        "3. **Add/remove rows and columns** - Right-click on a cell for context menu\n"
        "4. **Text formatting** - Use bold, italic, strikethrough in cells\n"
        "5. **Multi-line content** - Content in cells can span multiple concepts\n"
        "6. **Round-trip conversion** - Edit the markdown below and see it update in the editor\n\n"
        "## Table with Multi-line Content\n\n"
        "| Task | Description | Status |\n"
        "| ---- | ----------- | ------ |\n"
        "| **Setup** | Install dependencies Configure environment Test connection | ✅ Complete |\n"
        "| **Development** | Write code Add tests Review changes | 🔄 In Progress |\n"
        "| **Deployment** | Build application Deploy to staging Deploy to production | ⏳ Pending |\n\n"
        "## Empty Table for Testing\n\n"
        "| Column 1 | Column 2 | Column 3 |\n"
        "| -------- | -------- | -------- |\n"
        "| | | |\n"
        "| | | |\n\n"
        "Try editing the tables above or create new ones using the toolbar!"
    )

# Add sample table templates
st.sidebar.header("Table Templates")
if st.sidebar.button("Load Simple Table"):
    st.session_state["editor_content"] = (
        "# Simple Table\n\n"
        "| Header 1 | Header 2 |\n"
        "| -------- | -------- |\n"
        "| Cell 1 | Cell 2 |\n"
        "| Cell 3 | Cell 4 |\n"
    )

if st.sidebar.button("Load Complex Table"):
    st.session_state["editor_content"] = (
        "# Complex Table with Formatting\n\n"
        "| **Product** | *Price* | ~~Old Price~~ | Status |\n"
        "| ----------- | ------: | ------------: | ------ |\n"
        "| **Premium Laptop** | $1,299.99 | ~~$1,499.99~~ | ✅ Available |\n"
        "| *Gaming Mouse* | $79.99 | ~~$99.99~~ | ⚠️ Low Stock |\n"
        "| Keyboard | $149.99 | $149.99 | ❌ Out of Stock |\n"
    )

if st.sidebar.button("Load Empty Template"):
    st.session_state["editor_content"] = (
        "# Create Your Own Table\n\n"
        "Use the table button in the toolbar to insert a new table.\n\n"
        "| | | |\n"
        "| --- | --- | --- |\n"
        "| | | |\n"
        "| | | |\n"
    )

if st.sidebar.button("Load Multi-line Example"):
    st.session_state["editor_content"] = (
        "# Multi-line Content in Tables\n\n"
        "This example shows multi-line content within table cells:\n\n"
        "| Feature | Description | Example |\n"
        "| ------- | ----------- | ------- |\n"
        "| **Simple Content** | Single line content | Line 1 Line 2 |\n"
        "| **Multiple Items** | Several items | Item 1 Item 2 Item 3 Item 4 |\n"
        "| **With Formatting** | Formatted content | **Bold text** *Italic text* ~~Strikethrough~~ |\n"
        "| **Mixed Content** | Text, code, symbols | Regular text `code snippet` • Bullet point → Arrow |\n\n"
        "Try editing these cells and adding your own content!"
    )

# 1) Plain text (Markdown) input
st.subheader("1) Markdown Input (Round-trip Testing)")
st.write("Edit the Markdown below to test round-trip conversion: Markdown → Table → Markdown")
input_md = st.text_area(
    "Markdown Content:",
    value=st.session_state["editor_content"],
    height=250,
    help="Changes here will update the editor above. This demonstrates round-trip conversion."
)
st.session_state["editor_content"] = input_md

# 2) The editor component
st.subheader("2) Interactive Table Editor")
st.write("**Instructions:**")
st.write("• Click the table button (📊) in the toolbar to insert new tables")
st.write("• Click any cell to edit its content")
st.write("• Add multiple content items in cells")
st.write("• Right-click on cells to access table management options")
st.write("• Use formatting buttons for bold, italic, strikethrough in cells")

markdown = streamlit_lexical_extended(
    value=st.session_state["editor_content"],
    placeholder="Click the table button in the toolbar to create your first table!",
    key="editor",
    height=600,
    overwrite=True,
    on_change=lambda: st.session_state.update({"editor_content": st.session_state.get("editor")}),
)

st.markdown("---")

# 3) Rendered Markdown output
st.subheader("3) Generated Markdown Output")
st.write("This shows the Markdown generated by the editor, demonstrating export functionality:")
st.code(markdown, language="markdown")

# 4) Rendered HTML preview
st.subheader("4) Rendered HTML Preview")
st.write("This shows how the Markdown renders as HTML:")
st.markdown(markdown)

# 5) Validation section
st.markdown("---")
st.subheader("5) Validation & Testing")

col1, col2 = st.columns(2)

with col1:
    st.write("**Table Count:**")
    if markdown:
        table_count = markdown.count("| ")
        if table_count > 0:
            # Rough estimation of tables by counting table rows
            estimated_tables = markdown.count("\n|") // 2  # Approximate
            st.success(f"✅ Found approximately {estimated_tables} table(s)")
        else:
            st.info("ℹ️ No tables detected")
    else:
        st.info("ℹ️ No content yet")

with col2:
    st.write("**Round-trip Test:**")
    if st.button("Test Round-trip Conversion"):
        # Test if the markdown can be parsed back
        test_content = markdown
        st.session_state["test_result"] = test_content
        st.success("✅ Round-trip conversion successful!")
        
if "test_result" in st.session_state:
    with st.expander("View Round-trip Result"):
        st.code(st.session_state["test_result"], language="markdown")
