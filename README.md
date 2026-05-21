# 🌟 AI Virtual Outfit Try-On System

A complete virtual outfit try-on application: **live webcam**, **photo try-on**, PNG outfit catalog, and **screenshots saved to the `screenshots/` folder** via a layered Flask + JavaScript architecture.
---

## Quick Start

```bash
# Windows
run.bat

# Or manually
pip install -r backend/requirements.txt
python scripts/generate_sample_outfits.py
python backend/main.py
```

Open **http://localhost:5000**

---
## Presentation Demo Script

1. Start app → show architecture in README/DESIGN.  
2. **Live mode:** start camera, switch outfits, adjust scale, save screenshot.  
3. Open `screenshots/` folder to prove file was saved.  
4. **Photo mode:** upload photo, detect pose, try jacket, save again.  
5. Upload a custom PNG outfit.  
