# Faceless Content - Setup Guide

## ⚠️ Software You Need to Install

### 1. Python 3.10+

**Option A: Microsoft Store (Easiest)**
```powershell
# Open Microsoft Store and search for "Python 3.12" or run:
winget install Python.Python.3.12
```

**Option B: Direct Download**
1. Go to https://www.python.org/downloads/
2. Download Python 3.12 or later
3. **IMPORTANT:** Check "Add Python to PATH" during installation

After installing, restart your terminal and verify:
```powershell
python --version
```

### 2. FFmpeg (Video Processing)

**Option A: Using winget**
```powershell
winget install FFmpeg
```

**Option B: Using Chocolatey**
```powershell
choco install ffmpeg
```

**Option C: Manual Installation**
1. Go to https://ffmpeg.org/download.html
2. Click "Windows" → "Windows builds from gyan.dev"
3. Download "ffmpeg-release-essentials.zip"
4. Extract to `C:\ffmpeg`
5. Add `C:\ffmpeg\bin` to your system PATH:
   - Search "Environment Variables" in Start menu
   - Edit "Path" under System variables
   - Add `C:\ffmpeg\bin`
   - Restart terminal

Verify:
```powershell
ffmpeg -version
```

### 3. Python Dependencies

After Python is installed:
```powershell
pip install requests
```

### 4. Video Editor (For Thumbnails & Final Touches)

**DaVinci Resolve (Free, Professional)**
- Download from: https://www.blackmagicdesign.com/products/davinciresolve
- Full editing suite, color grading, effects

**CapCut (Free, Simple)**  
- Download from: https://www.capcut.com/
- Great for TikTok/short-form editing
- Easy to use

### 5. Image Editor (For Thumbnails)

**GIMP (Free)**
- Download: https://www.gimp.org/downloads/

**Photopea (Free, Browser-based)**
- Go to: https://www.photopea.com/
- Photoshop alternative, no install needed

---

## 📁 What's Already Set Up

I've created the complete folder structure:
```
C:\Users\kat_l\clawd\faceless-content\
├── scary-stories/
│   └── scripts/stairs-in-the-woods_script.json ✅
├── finance/
│   └── scripts/7-money-mistakes_script.json ✅
├── luxury/
│   └── scripts/hermes-birkin-bags_script.json ✅
├── pipeline/
│   ├── config.py (needs your API keys)
│   ├── story_scraper.py
│   ├── image_generator.py
│   ├── tts_generator.py
│   ├── video_assembler.py
│   └── pipeline.py
├── BUSINESS_PLANS.md
├── CONTENT_IDEAS.md
└── PIPELINE_README.md
```

---

## 🔑 API Keys Needed

Edit `faceless-content/pipeline/config.py` with your credentials:

### Azure OpenAI (Images)
```python
AZURE_OPENAI_IMAGE_ENDPOINT = "https://YOUR-RESOURCE.openai.azure.com/"
AZURE_OPENAI_IMAGE_KEY = "your-key-here"
AZURE_OPENAI_IMAGE_DEPLOYMENT = "dall-e-3"  # or your deployment name
```

**Where to find these:**
1. Go to Azure Portal → Your OpenAI resource
2. Keys and Endpoint section has your endpoint and keys
3. Model deployments shows your deployment name

### Azure TTS (Voice)
```python
AZURE_TTS_KEY = "your-speech-key-here"
AZURE_TTS_REGION = "eastus"  # your region
```

**Where to find these:**
1. Azure Portal → Create a "Speech" resource (if you don't have one)
2. Keys and Endpoint section

---

## 🚀 Running the Pipeline

Once everything is installed and configured:

```powershell
cd C:\Users\kat_l\clawd\faceless-content\pipeline

# Test with existing script (no API calls for fetching)
python pipeline.py --niche scary-stories --skip-fetch

# Or process a specific script
python pipeline.py --niche finance --script "..\finance\scripts\7-money-mistakes_script.json"

# Full pipeline: fetch new stories and produce
python pipeline.py --niche scary-stories --count 3
```

---

## ✅ Checklist

- [ ] Install Python 3.12
- [ ] Install FFmpeg
- [ ] Run `pip install requests`
- [ ] Get Azure OpenAI endpoint + key
- [ ] Get Azure Speech (TTS) key
- [ ] Update `pipeline/config.py` with your keys
- [ ] Install DaVinci Resolve or CapCut
- [ ] (Optional) Install GIMP for thumbnails

---

## 📞 When You Have Your API Keys

Just paste them here and I'll update the config file for you, then we can test the pipeline together!
