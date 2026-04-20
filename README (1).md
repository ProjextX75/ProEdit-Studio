# ProEdit Studio

**AI-powered video editor built with Python & Tkinter**

ProEdit Studio is a free, open-source desktop video editor with AI features powered by OpenAI and Google Gemini. It runs on Windows, macOS, and Linux.

![ProEdit Studio](proedit_icon.png)

---

## ✨ Features

- 🎬 **Video & Image Editing** — Import, trim, crop, rotate, flip, speed control
- 🎨 **Color Grading** — Curves, levels, exposure, highlights, shadows, temperature, vibrance
- ✂ **AI Scene Detection** — Auto-split long videos into scenes
- 🤖 **AI Creative Studio** — Powered by OpenAI GPT-4o & Google Gemini Vision
- ✏ **Text & Titles** — Add text overlays with custom fonts and animations
- 😀 **Stickers & Elements** — Emoji stickers and shape overlays
- 🎵 **Audio** — Background music, audio mixing, volume control
- 📐 **Format Presets** — YouTube, TikTok/Reels, Instagram, Cinematic and more
- 🖼 **Picture-in-Picture** — Overlay a second video on your clip
- 💚 **Green Screen** — Chroma key removal
- 📤 **Export** — MP4, GIF, social media presets
- 🌙 **Dark / Light Theme** — Full theme toggle
- 💾 **Auto-save** — Project auto-saved every few minutes
- ⌨ **Keyboard Shortcuts** — Full shortcut support

---

## 🚀 Quick Start

### Option 1 — Windows EXE (easiest)
Download the latest `ProEditStudio.exe` from the [Releases](../../releases) page and run it. No Python required!

### Option 2 — Run from source

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python video_editor_v3.py
```

---

## 📋 Requirements (source only)

- Python 3.10+
- See `requirements.txt` for Python packages

---

## 🔑 AI Features Setup

To use AI features, add your API keys in **Settings** (⚙ icon):

- **OpenAI** — Get a key at [platform.openai.com](https://platform.openai.com)
- **Google Gemini** — Get a key at [aistudio.google.com](https://aistudio.google.com)

AI features are optional — the editor works fully without them.

---

## 🖥 Supported Platforms

| Platform | Status |
|----------|--------|
| Windows 10/11 | ✅ Full support |
| Linux (Ubuntu, Mint, etc.) | ✅ Full support |
| macOS | ⚠ Mostly works (some UI differences) |

---

## 🙋 Feature Requests

I am actively open to adding new features at users request! Drop a suggestion in the [Issues](../../issues) tab and I'll do my best to build it in a future update.

---

## ☕ Support the Project

If you find ProEdit Studio useful, consider leaving a tip — it helps me keep building and adding new features!

[![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/projextx75)

---

## 📄 License

MIT License — free to use, modify and distribute.

---

## 🙏 Credits

Built with:
- [MoviePy](https://github.com/Zulko/moviepy) — Video processing
- [Pillow](https://python-pillow.org/) — Image processing
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern UI components
- [OpenAI API](https://openai.com) — AI features
- [Google Gemini](https://deepmind.google/technologies/gemini/) — AI vision features
