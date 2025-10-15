# st_pptx_viewer Documentation Index

Welcome to the st_pptx_viewer module documentation!

## 🎉 New: CDN-Hosted PptxViewJS!

**No build required!** The module now uses CDN by default. See [CDN_UPDATE.md](CDN_UPDATE.md) for details.

## 📖 Documentation Guide

Choose the right document for your needs:

### 🚀 Getting Started

1. **[QUICKSTART.md](QUICKSTART.md)** - Start here!
   - ⏱️ Time: 5 minutes
   - 📋 Prerequisites and setup
   - 🎯 Your first viewer app
   - ⚡ Quick tips and tricks

2. **[USAGE.md](USAGE.md)** - Practical usage guide
   - ⏱️ Time: 15 minutes
   - 📚 Common patterns and recipes
   - 🎨 Styling examples
   - 🔧 Troubleshooting

### 📚 Complete Reference

3. **[README.md](README.md)** - Full documentation
   - ⏱️ Time: 30 minutes
   - 📖 Complete API reference
   - ⚙️ All configuration options
   - 📊 Multiple examples
   - 🐛 Troubleshooting guide

### 🏗️ Architecture & Design

4. **[MODULE_OVERVIEW.md](MODULE_OVERVIEW.md)** - Deep dive
   - ⏱️ Time: 20 minutes
   - 🏛️ Architecture and design
   - 🔄 Data flow diagrams
   - 🧩 Extension points
   - 🔮 Future roadmap

5. **[PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md)** - Package overview
   - ⏱️ Time: 10 minutes
   - 📦 What was created
   - ✨ Key features
   - 📊 Comparison with alternatives
   - 🎯 Use cases

### 💡 Examples

6. **[examples/README.md](examples/README.md)** - Examples guide
   - ⏱️ Time: 10 minutes
   - 🎨 4 complete example apps
   - 💻 How to run them
   - 🔍 What each demonstrates

## 📁 File Structure

```
st_pptx_viewer/
├── 📘 Documentation
│   ├── INDEX.md              ← You are here
│   ├── QUICKSTART.md         ← Start here (5 min)
│   ├── USAGE.md              ← Usage patterns (15 min)
│   ├── README.md             ← Full reference (30 min)
│   ├── MODULE_OVERVIEW.md    ← Architecture (20 min)
│   └── PACKAGE_SUMMARY.md    ← Overview (10 min)
│
├── 🐍 Python Module
│   ├── __init__.py           ← Public API
│   └── viewer.py             ← Implementation
│
├── 📦 Installation
│   ├── setup.py              ← Package setup
│   ├── pyproject.toml        ← Modern config
│   ├── MANIFEST.in           ← Distribution files
│   └── install.sh            ← Installation script
│
└── 📂 Examples
    ├── README.md             ← Examples guide
    ├── basic_example.py      ← Minimal (5 min)
    ├── advanced_example.py   ← Full config (15 min)
    ├── compare_presentations.py  ← Side-by-side (10 min)
    └── custom_styling.py     ← Themes (15 min)
```

## 🎯 Quick Navigation

### I want to...

#### ...get started quickly
→ [QUICKSTART.md](QUICKSTART.md)

#### ...see code examples
→ [examples/README.md](examples/README.md)
→ [USAGE.md](USAGE.md) (Common Patterns section)

#### ...understand all features
→ [README.md](README.md)

#### ...customize the styling
→ [USAGE.md](USAGE.md) (Styling Guide section)
→ [examples/custom_styling.py](examples/custom_styling.py)

#### ...use multiple viewers
→ [USAGE.md](USAGE.md) (Pattern 3)
→ [examples/compare_presentations.py](examples/compare_presentations.py)

#### ...troubleshoot issues
→ [USAGE.md](USAGE.md) (Troubleshooting section)
→ [README.md](README.md) (Troubleshooting section)

#### ...understand the architecture
→ [MODULE_OVERVIEW.md](MODULE_OVERVIEW.md)

#### ...extend the module
→ [MODULE_OVERVIEW.md](MODULE_OVERVIEW.md) (Extension Points section)

#### ...see what was created
→ [PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md)

## 🚦 Learning Path

### Beginner Path (30 minutes)
1. [QUICKSTART.md](QUICKSTART.md) - Setup and first app (5 min)
2. [examples/basic_example.py](examples/basic_example.py) - Run it (5 min)
3. [USAGE.md](USAGE.md) - Common patterns (15 min)
4. [examples/advanced_example.py](examples/advanced_example.py) - Try it (5 min)

### Intermediate Path (60 minutes)
1. Complete Beginner Path (30 min)
2. [README.md](README.md) - Full API reference (20 min)
3. [examples/compare_presentations.py](examples/compare_presentations.py) (5 min)
4. [examples/custom_styling.py](examples/custom_styling.py) (5 min)

### Advanced Path (90 minutes)
1. Complete Intermediate Path (60 min)
2. [MODULE_OVERVIEW.md](MODULE_OVERVIEW.md) - Architecture (20 min)
3. [PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md) - Design decisions (10 min)

## 📝 Cheat Sheets

### Installation
```bash
./st_pptx_viewer/install.sh
```

### Minimal Usage
```python
from st_pptx_viewer import pptx_viewer
pptx_viewer(uploaded_file)
```

### With Configuration
```python
from st_pptx_viewer import pptx_viewer, PptxViewerConfig
config = PptxViewerConfig(width=1200, enable_keyboard=True)
pptx_viewer(uploaded_file, config=config)
```

### Run Examples
```bash
streamlit run st_pptx_viewer/examples/basic_example.py
streamlit run st_pptx_viewer/examples/advanced_example.py
```

## 🔗 External Resources

- **Streamlit Docs**: https://docs.streamlit.io
- **PptxViewJS**: See main repository README
- **Python Packaging**: https://packaging.python.org

## 📊 Documentation Stats

| Document | Purpose | Time | Lines |
|----------|---------|------|-------|
| QUICKSTART.md | Getting started | 5 min | 150 |
| USAGE.md | Practical guide | 15 min | 400 |
| README.md | Complete reference | 30 min | 500 |
| MODULE_OVERVIEW.md | Architecture | 20 min | 600 |
| PACKAGE_SUMMARY.md | Overview | 10 min | 450 |
| examples/README.md | Examples guide | 10 min | 150 |
| INDEX.md | This file | 5 min | 200 |

**Total: 7 docs, ~2,450 lines of documentation**

## 🎓 Documentation by Role

### For End Users (App Builders)
1. QUICKSTART.md
2. USAGE.md
3. examples/README.md
4. README.md

### For Library Developers
1. MODULE_OVERVIEW.md
2. PACKAGE_SUMMARY.md
3. README.md
4. viewer.py (source code)

### For Package Maintainers
1. setup.py
2. pyproject.toml
3. MANIFEST.in
4. MODULE_OVERVIEW.md

## 🆘 Getting Help

### Problem Solving Flowchart
```
Having an issue?
    ├─→ Installation problem?
    │   └─→ See QUICKSTART.md "Common Issues"
    │
    ├─→ Usage question?
    │   └─→ See USAGE.md "Common Patterns"
    │
    ├─→ Configuration question?
    │   └─→ See README.md "Configuration Options"
    │
    ├─→ Styling question?
    │   └─→ See USAGE.md "Styling Guide"
    │       See examples/custom_styling.py
    │
    ├─→ Bug or error?
    │   └─→ See USAGE.md "Troubleshooting"
    │       See README.md "Troubleshooting"
    │
    └─→ Architecture question?
        └─→ See MODULE_OVERVIEW.md
```

### Still Need Help?
- Check browser console (F12) for errors
- Try the examples to isolate the issue
- Check GitHub Issues (if published)

## 🎯 Quick Tips

### 💡 Pro Tips
1. **Start simple**: Use default config first, customize later
2. **Use examples**: Copy and modify the example apps
3. **Browser console**: Check for JavaScript errors (F12)
4. **Type hints**: Your IDE will show available options
5. **Custom CSS**: Use `!important` to override defaults

### ⚠️ Common Mistakes
1. Forgetting to build the bundle: `npm run build:min`
2. Not installing module: `pip install -e ./st_pptx_viewer`
3. Missing `!important` in custom CSS
4. Using same key for multiple viewers
5. Uploading non-PPTX files

### ✅ Best Practices
1. Use `PptxViewerConfig` for type safety
2. Give unique keys to multiple viewers
3. Test with various PPTX files
4. Start with examples, then customize
5. Keep custom CSS minimal and focused

## 📅 Version History

### v1.0.0 (Current)
- Initial release
- Core viewer functionality
- 18+ configuration options
- 4 example applications
- Complete documentation

## 🎉 Summary

This module provides a complete solution for displaying PowerPoint presentations in Streamlit applications. Whether you're building a simple viewer or a complex presentation management system, the documentation and examples will guide you through the process.

**Happy coding! 🚀**

---

*Choose a document from the guide above and start exploring!*

