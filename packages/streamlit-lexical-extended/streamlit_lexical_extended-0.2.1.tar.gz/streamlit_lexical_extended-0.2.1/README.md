# streamlit-lexical-extended

Streamlit component that allows you to use Meta's [Lexical](https://lexical.dev/) as a rich text plugin. With tables and everything!

It is a spin off of [streamlit_lexical](https://github.com/alexander-dickson/streamlit_lexical).

## ✨ Features

- 📝 **Rich text editing** with Meta's Lexical editor
- 📊 **Full table support** with interactive cell editing
- 🎨 **Markdown formatting** (bold, italic, headings, lists, quotes)
- ⚡ **Dynamic height** - fixed or auto-expanding modes
- 🔄 **Debounced updates** for performance
- 🎯 **TypeScript + React** frontend

## 🚀 Installation

```bash
pip install streamlit-lexical-extended
```

## 📖 Usage

```python
import streamlit as st
from streamlit_lexical_extended import streamlit_lexical_extended

# Basic usage
result = streamlit_lexical_extended(
    value="# Hello World\n\nStart typing...",
    key="editor1"
)

st.write("Output:", result)
```

### With Fixed Height
```python
result = streamlit_lexical_extended(
    value="Content here...",
    height=400,  # Fixed 400px height
    key="fixed_editor"
)
```

### With Auto-Expand
```python
result = streamlit_lexical_extended(
    value="Content here...",
    min_height=200,  # Minimum 200px, grows with content
    key="auto_editor"
)
```

### With Debouncing
```python
result = streamlit_lexical_extended(
    value="Content here...",
    debounce=500,  # Wait 500ms before updating
    key="debounced_editor"
)
```

## 🔧 Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` | `str` | `""` | Initial markdown content |
| `height` | `int \| None` | `None` | Fixed height in pixels. If `None`, auto-expands |
| `min_height` | `int` | `400` | Minimum height for auto-expand mode |
| `placeholder` | `str` | `"Start typing..."` | Placeholder text |
| `debounce` | `int` | `300` | Debounce delay in milliseconds |
| `key` | `str` | Required | Unique key for the component |
| `overwrite` | `bool` | `False` | Force overwrite editor content |

## 🛠️ Development

See [BUILD_AND_PUBLISH.md](BUILD_AND_PUBLISH.md) for complete build and publish instructions.

### Quick Setup
```bash
# Clone repository
git clone https://github.com/yourusername/streamlit-lexical-extended.git
cd streamlit-lexical-extended

# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd streamlit_lexical_extended/frontend
npm install
npm run build
cd ../..

# Run example
streamlit run streamlit_lexical_extended/example.py
```

## 📦 Building & Publishing

```bash
# Build frontend
cd streamlit_lexical_extended/frontend && npm run build && cd ../..

# Build Python package
python -m build

# Upload to PyPI
twine upload dist/*
```

Or use the automated release script:
```bash
./release.sh 0.2.1
```

## 📄 License

MIT License

## 🙏 Credits

Based on [streamlit_lexical](https://github.com/alexander-dickson/streamlit_lexical) by Alexander Dickson.

Uses Meta's [Lexical](https://lexical.dev/) editor framework.
