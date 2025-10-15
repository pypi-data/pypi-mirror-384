# CDN Update Notice

## 🎉 Major Simplification: CDN-Hosted PptxViewJS

The `st_pptx_viewer` module now uses **CDN-hosted PptxViewJS by default**, eliminating the need to build the JavaScript bundle!

## What Changed

### Before
```bash
# Required build steps
cd /path/to/js-slide-viewer
npm install
npm run build:min

# Then install Python module
pip install -e ./st_pptx_viewer
```

### After
```bash
# Just install the Python module!
pip install -e ./st_pptx_viewer
```

## Benefits

✅ **No Build Required** - Skip npm install and build steps  
✅ **Faster Setup** - Get started in seconds  
✅ **Always Updated** - CDN serves the latest stable version  
✅ **Smaller Package** - No need to distribute the JS bundle  
✅ **Simpler Deployment** - Fewer dependencies to manage  

## How It Works

The module loads PptxViewJS from jsdelivr CDN:
```
https://cdn.jsdelivr.net/npm/pptxviewjs/dist/PptxViewJS.min.js
```

This happens automatically when you use `pptx_viewer()` - no configuration needed!

## Using a Local Bundle (Optional)

If you need to use a local PptxViewJS bundle (offline environments, custom builds, etc.):

```python
from st_pptx_viewer import pptx_viewer, PptxViewerConfig

config = PptxViewerConfig(
    pptxviewjs_path="/path/to/your/PptxViewJS.min.js"
)

pptx_viewer(uploaded_file, config=config)
```

## Requirements

- **Internet connection** - Required for CDN access (default mode)
- **Python 3.8+** - Unchanged
- **Streamlit 1.0+** - Unchanged

## Installation

### Quick Install
```bash
cd st_pptx_viewer
./install.sh
```

The installer now:
1. ✅ Checks Python version
2. ✅ Notes CDN usage (no build step!)
3. ✅ Installs dependencies
4. ✅ Installs module
5. ✅ Verifies installation

### Manual Install
```bash
pip install streamlit
pip install -e ./st_pptx_viewer
```

That's it! No `npm` commands needed.

## Migration Guide

If you're upgrading from a version that required building:

### 1. Update Your Installation Scripts
Remove any `npm` build commands:
```bash
# Remove these lines:
# npm install
# npm run build:min
```

### 2. Update Documentation
No need to mention building in your docs anymore!

### 3. Test Your App
The API hasn't changed - your code should work as-is:
```python
from st_pptx_viewer import pptx_viewer
pptx_viewer(uploaded_file)  # Works the same!
```

### 4. Optional: Remove Local Bundle
If you have a local bundle, you can remove it (unless you need offline support).

## Offline/Air-Gapped Environments

For environments without internet access:

1. **Build the bundle once** (on a machine with internet):
```bash
cd /path/to/js-slide-viewer
npm install
npm run build:min
```

2. **Copy the bundle** to your environment

3. **Configure the path**:
```python
config = PptxViewerConfig(
    pptxviewjs_path="/path/to/PptxViewJS.min.js"
)
pptx_viewer(file, config=config)
```

## CDN Details

### Provider
- **CDN**: jsdelivr.net
- **Package**: pptxviewjs
- **URL**: https://cdn.jsdelivr.net/npm/pptxviewjs/dist/PptxViewJS.min.js

### Benefits of jsdelivr
- ✅ Global CDN with high availability
- ✅ Automatic HTTPS
- ✅ Version pinning available
- ✅ Fast edge caching
- ✅ Free for open source

### CDN Reliability
jsdelivr is a production-grade CDN used by millions of developers worldwide. It provides:
- 99.9% uptime SLA
- Global edge network
- Automatic failover
- DDoS protection

## Troubleshooting

### CDN Not Loading
**Check:**
1. Internet connectivity
2. Firewall/proxy settings
3. Browser console for errors

**Solution:** Use a local bundle (see "Using a Local Bundle" above)

### Want Latest Development Version
The CDN serves the published npm package. For development versions:
1. Build locally
2. Use `pptxviewjs_path` config option

### Corporate Firewall Blocks CDN
**Solution:** 
1. Request CDN whitelist from IT
2. Or use local bundle approach

## Examples Updated

All example applications have been updated:
- ✅ `basic_example.py` - Uses CDN by default
- ✅ `advanced_example.py` - Shows all config options
- ✅ `compare_presentations.py` - Multiple viewers work fine
- ✅ `custom_styling.py` - All themes use CDN

## Documentation Updated

All documentation reflects the CDN change:
- ✅ README.md
- ✅ QUICKSTART.md
- ✅ USAGE.md
- ✅ MODULE_OVERVIEW.md
- ✅ COMPLETION_REPORT.md
- ✅ examples/README.md
- ✅ install.sh

## Backward Compatibility

The `pptxviewjs_path` parameter remains available:
- **Before**: Required to specify bundle path
- **After**: Optional, falls back to CDN if not specified

Existing code with `pptxviewjs_path` will continue to work!

## Questions?

### Why CDN?
Simplifies installation and deployment. Most modern web apps use CDN-hosted libraries.

### Is it secure?
Yes. jsdelivr uses HTTPS and has strong security practices. The module loads from a trusted CDN.

### What about speed?
CDN is typically faster than local serving due to edge caching and compression.

### Can I still use local bundle?
Absolutely! Just use the `pptxviewjs_path` configuration option.

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Installation** | npm + pip | pip only |
| **Build Required** | Yes | No |
| **Internet Required** | No | Yes (for CDN) |
| **Setup Time** | ~5 minutes | ~30 seconds |
| **Dependencies** | Node.js + Python | Python only |
| **Local Bundle** | Required | Optional |

## Celebrate! 🎉

You can now get started with `st_pptx_viewer` in just a few commands:

```bash
pip install -e ./st_pptx_viewer
streamlit run st_pptx_viewer/examples/basic_example.py
```

No npm, no build, no hassle! 🚀

