"""
ProEdit Studio v3.0 - AI-Powered Video Editor
Requirements: pip install moviepy pillow numpy imageio imageio-ffmpeg customtkinter tkinterdnd2
Run: python video_editor_v3.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    ctk = None
    CTK_AVAILABLE = False

def safe_cfg(widget, **kwargs):
    """Universal config that works for both tk and CTk widgets."""
    try:
        widget.configure(**kwargs)
    except Exception:
        pass

def safe_pp(widget):
    """Safe pack_propagate for both tk and CTk."""
    try:
        widget.pack_propagate(False)
    except Exception:
        pass
import os
import json
import math
import threading

try:
    from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import tkinterdnd2 as dnd
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

try:
    import moviepy as mpy
    from moviepy import (
        VideoFileClip, ImageClip, AudioFileClip,
        concatenate_videoclips, CompositeVideoClip,
        TextClip, ColorClip, concatenate_audioclips
    )
    MOVIEPY_AVAILABLE = True
except Exception:
    try:
        import importlib
        mpy = importlib.import_module("moviepy")
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.video.VideoClip import ImageClip, ColorClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
        from moviepy.video.VideoClip import TextClip
        from moviepy.audio.AudioClip import concatenate_audioclips
        MOVIEPY_AVAILABLE = True
    except Exception:
        MOVIEPY_AVAILABLE = False

import urllib.request, urllib.error, base64, io

# ── Global settings store ────────────────────────────────────────────
GEMINI_MODELS = {
    "gemini-2.5-flash  (Recommended — paid & free)":  "gemini-2.5-flash",
    "gemini-2.5-pro    (Most capable — paid billing)": "gemini-2.5-pro-preview-05-06",
    "gemini-2.0-flash  (Fast — paid & free)":         "gemini-2.0-flash",
    "gemini-2.0-flash-lite (Fastest — free & paid)":  "gemini-2.0-flash-lite",
}
GEMINI_MODEL_LABELS = list(GEMINI_MODELS.keys())

OPENAI_MODELS = {
    "gpt-4o-mini  (Vision, affordable)":   "gpt-4o-mini",
    "gpt-4o       (Vision, best quality)": "gpt-4o",
    "gpt-4-turbo  (Vision, high quality)": "gpt-4-turbo",
}
OPENAI_MODEL_LABELS = list(OPENAI_MODELS.keys())

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# ── Pollinations AI (image gen — no API key needed) ──────────────────
APP_NAME = "ProEdit Studio"
APP_VERSION = "3.0"

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&nologo=true&enhance=true"

_SETTINGS = {
    "active_provider":  "openai",   # "openai" | "gemini"
    "openai_api_key":   "",
    "openai_model":     "gpt-4o-mini  (Vision, affordable)",
    "gemini_api_key":   "",
    "gemini_model":     "gemini-2.5-flash  (Recommended — paid & free)",
    "replicate_api_key":"",
    "fal_api_key":"",
    "wavespeed_api_key":"",
    "max_retries":      3,
    "compress_images":  True,
    "compress_quality": 60,
    "theme":            "dark",     # "dark" | "light"
    "recent_projects":  [],         # list of recent .cvp paths
}

# ── Config file for persistence ───────────────────────────────────────
import json as _json, os as _os
_CONFIG_PATH = _os.path.join(_os.path.expanduser("~"), ".proedit_config.json")

def _load_config():
    try:
        with open(_CONFIG_PATH) as f:
            data = _json.load(f)
            _SETTINGS.update({k:v for k,v in data.items() if k in _SETTINGS})
    except Exception:
        pass

def _save_config():
    try:
        with open(_CONFIG_PATH,"w") as f:
            _json.dump(_SETTINGS, f, indent=2)
    except Exception:
        pass

_load_config()
def get_gemini_url():
    """Build Gemini URL. v1beta works for ALL Gemini API keys."""
    model_label = _SETTINGS.get("gemini_model",
                                 "gemini-2.5-flash  (Recommended — paid & free)")
    model_id    = GEMINI_MODELS.get(model_label, "gemini-2.5-flash")
    return (f"https://generativelanguage.googleapis.com"
            f"/v1beta/models/{model_id}:generateContent")


# ── Theme ─────────────────────────────────────────────────────────────
BG     = "#0A0C14"   # deep dark background
WHITE  = "#12141F"   # panel background
CARD   = "#1A1D2E"   # card/input background
ACCENT = "#7C5CFC"   # vivid purple accent
A2     = "#F43F5E"   # rose
GREEN  = "#22D3A5"   # teal green
TEXT   = "#EAEDF5"   # crisp white text
MUTED  = "#5A647A"   # muted text
BORDER = "#252840"   # subtle border
SEL    = "#28265A"   # selection glow
DARK   = "#06070E"   # near-black
WARN   = "#FBBF24"   # amber
TRACK  = "#0E1018"   # timeline track

import platform as _platform
_FF = "Segoe UI" if _platform.system()=="Windows" else ("SF Pro Display" if _platform.system()=="Darwin" else "Inter")
try:
    import tkinter as _tk_test; _tk_test.font.Font(family=_FF)
except: _FF = "Helvetica"
F = {
    "h1":   (_FF, 20, "bold"),
    "h2":   (_FF, 14, "bold"),
    "h3":   (_FF, 12, "bold"),
    "body": (_FF, 11),
    "sm":   (_FF, 10),
    "xs":   (_FF, 9), }

# Light theme palette (swapped in when user toggles)
_LIGHT = {
    "BG":"#F1F5F9","WHITE":"#FFFFFF","CARD":"#F8FAFC","ACCENT":"#6366F1",
    "A2":"#F43F5E","GREEN":"#10B981","TEXT":"#1E293B","MUTED":"#64748B",
    "BORDER":"#E2E8F0","SEL":"#EEF2FF","DARK":"#1E293B","WARN":"#F59E0B",
    "TRACK":"#E2E8F0",
}
_DARK = {
    "BG":"#0A0C14","WHITE":"#12141F","CARD":"#1A1D2E","ACCENT":"#7C5CFC",
    "A2":"#F43F5E","GREEN":"#22D3A5","TEXT":"#EAEDF5","MUTED":"#5A647A",
    "BORDER":"#252840","SEL":"#28265A","DARK":"#06070E","WARN":"#FBBF24",
    "TRACK":"#0E1018",
}

def _apply_theme(mode):
    """Update all color globals for dark/light mode."""
    global BG,WHITE,CARD,ACCENT,A2,GREEN,TEXT,MUTED,BORDER,SEL,DARK,WARN,TRACK
    p = _LIGHT if mode=="light" else _DARK
    BG=p["BG"]; WHITE=p["WHITE"]; CARD=p["CARD"]; ACCENT=p["ACCENT"]
    A2=p["A2"]; GREEN=p["GREEN"]; TEXT=p["TEXT"]; MUTED=p["MUTED"]
    BORDER=p["BORDER"]; SEL=p["SEL"]; DARK=p["DARK"]; WARN=p["WARN"]
    TRACK=p["TRACK"]
    _SETTINGS["theme"] = mode
    _save_config()

_apply_theme(_SETTINGS.get("theme","dark"))

ASPECT_RATIOS = {
    "16:9  YouTube":      (1280, 720),
    "9:16  TikTok/Reels": (720, 1280),
    "1:1   Instagram":    (720, 720),
    "4:5   Portrait":     (864, 1080),
    "4:3   Classic":      (960, 720),
    "21:9  Cinematic":    (1680, 720), }

FILTERS     = ["None","Vivid","Warm","Cool","Sepia","B&W","Fade","Chrome","Matte","Noir"]
TRANSITIONS = ["None","Fade","Slide Left","Slide Right","Zoom In","Dissolve"]
STICKERS    = ["⭐","🔥","💥","✨","🎬","🎵","🏆","💯","❤️","😂",
               "👏","💪","🎉","🌟","💫","🚀","👑","🎯","💎","😎",
               "🤩","🥳","😍","🔝","🌈","⚡","🎪","🏅","🦁","🐯"]

# ── Helpers ───────────────────────────────────────────────────────────
def mkbtn(parent, text, cmd=None, style="default", px=12, py=6, **kw):
    palettes = {
        "default": (CARD,   TEXT,   BORDER),
        "accent":  (ACCENT, WHITE,  "#5A52E0"),
        "danger":  (DARK,   A2,     "#3D1A2A"),
        "dark":    (DARK,   WHITE,  ACCENT),
        "ghost":   (BG,     MUTED,  BORDER),
        "green":   (GREEN,  WHITE,  "#0EA874"),
        "pill":    (SEL,    ACCENT, "#3D3F6A"),
    }
    bg, fg, hov = palettes.get(style, palettes["default"])
    if CTK_AVAILABLE:
        # Map style to CTkButton hover color
        b = ctk.CTkButton(
            parent, text=text, command=cmd or (lambda: None),
            fg_color=bg, text_color=fg, hover_color=hov,
            corner_radius=4,
            font=ctk.CTkFont(size=11),
            height=32 + py*2,
            **{k: v for k, v in kw.items() if k not in
               ("font","padx","pady","relief","bd","cursor",
                "activebackground","activeforeground")}
        )
    else:
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, activebackground=hov, activeforeground=fg,
                      relief="flat", bd=0, cursor="hand2",
                      font=kw.pop("font", F["sm"]),
                      padx=px, pady=py)
        b.bind("<Enter>", lambda e: safe_cfg(b,bg=hov))
        b.bind("<Leave>", lambda e: safe_cfg(b,bg=bg))
    return b

def lbl(parent, text="", font=None, fg=TEXT, bg=WHITE, **kw):
    if CTK_AVAILABLE and isinstance(parent, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
        return ctk.CTkLabel(parent, text=text,
                            font=ctk.CTkFont(size=11),
                            text_color=fg, fg_color="transparent", **{
                                k:v for k,v in kw.items()
                                if k not in ("relief","bd","padx","pady")})
    return tk.Label(parent, text=text, font=font or F["body"],
                    fg=fg, bg=bg, **kw)

def sep(parent, bg=BORDER):
    return tk.Frame(parent, bg=bg, height=1)

def entry(parent, var, bg=CARD, width=20):
    if CTK_AVAILABLE:
        return ctk.CTkEntry(parent, textvariable=var,
                            fg_color=CARD, text_color=TEXT,
                            border_color=BORDER, border_width=1,
                            corner_radius=6, width=width*8, height=32)
    return tk.Entry(parent, textvariable=var, bg=bg, fg=TEXT,
                    insertbackground=TEXT, relief="flat",
                    font=F["body"], width=width)

def sec_hdr(parent, title, bg=WHITE):
    f = tk.Frame(parent, bg=bg)
    f.pack(fill="x", padx=12, pady=(12, 3))
    tk.Frame(f, bg=ACCENT, width=3, height=11).pack(side="left", pady=1)
    tk.Label(f, text=f"  {title.upper()}", bg=bg, fg="#8B96B8",
             font=("Helvetica",8,"bold"),
             ).pack(side="left")

def ctkF(parent, bg=WHITE, **kw):
    """Smart frame: CTkFrame when available, tk.Frame fallback."""
    if CTK_AVAILABLE:
        return ctk.CTkFrame(parent, fg_color=bg, corner_radius=0, **{
            k:v for k,v in kw.items()
            if k not in ("highlightthickness","highlightbackground",
                         "highlightcolor","relief","bd")})
    return tk.Frame(parent, bg=bg, **kw)

def ctkL(parent, text="", fg=TEXT, bg=WHITE, font=None, **kw):
    """Smart label: CTkLabel when available, tk.Label fallback."""
    if CTK_AVAILABLE:
        sz = 11
        bold = False
        if font and isinstance(font, tuple):
            sz = font[1] if len(font)>1 else 11
            bold = len(font)>2 and font[2]=="bold"
        return ctk.CTkLabel(parent, text=text, text_color=fg,
                            fg_color="transparent",
                            font=ctk.CTkFont(size=sz, weight="bold" if bold else "normal"),
                            **{k:v for k,v in kw.items()
                               if k not in ("relief","bd","padx","pady",
                                            "highlightthickness","cursor")})
    return tk.Label(parent, text=text, fg=fg, bg=bg,
                    font=font or F["body"], **kw)

def scrollframe(parent, bg=WHITE):
    if CTK_AVAILABLE:
        # Return a CTkScrollableFrame — caller uses it directly as the body
        sf = ctk.CTkScrollableFrame(parent, fg_color=bg, corner_radius=0,
                                     scrollbar_button_color=BORDER,
                                     scrollbar_button_hover_color=MUTED)
        return sf, sf   # outer==inner for CTk
    outer  = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
    vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner  = tk.Frame(canvas, bg=bg)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    wid = canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=vsb.set)
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    def _mw(e): canvas.yview_scroll(int(-1*(e.delta/120)), "units")
    def _on_enter(e): canvas.bind_all("<MouseWheel>", _mw)
    def _on_leave(e): canvas.unbind_all("<MouseWheel>")
    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)
    return outer, inner

# ── PIL filter ────────────────────────────────────────────────────────
def pil_filter(img, name):
    if name == "B&W":    return img.convert("L").convert("RGB")
    if name == "Sepia":
        r,g,b = img.split()
        return Image.merge("RGB",(
            r.point(lambda i:min(255,int(i*.393+i*.769+i*.189))),
            g.point(lambda i:min(255,int(i*.349+i*.686+i*.168))),
            b.point(lambda i:min(255,int(i*.272+i*.534+i*.131)))))
    if name == "Warm":
        r,g,b = img.split()
        return Image.merge("RGB",(r.point(lambda i:min(255,i+25)),g,b.point(lambda i:max(0,i-25))))
    if name == "Cool":
        r,g,b = img.split()
        return Image.merge("RGB",(r.point(lambda i:max(0,i-25)),g,b.point(lambda i:min(255,i+25))))
    if name == "Vivid":  return ImageEnhance.Color(img).enhance(1.8)
    if name == "Fade":   return ImageEnhance.Contrast(ImageEnhance.Brightness(img).enhance(1.1)).enhance(0.7)
    if name == "Chrome": return ImageEnhance.Color(ImageEnhance.Contrast(img).enhance(1.4)).enhance(1.3)
    if name == "Matte":  return ImageEnhance.Contrast(ImageEnhance.Brightness(img).enhance(1.05)).enhance(0.85)
    if name == "Noir":   return ImageEnhance.Contrast(img.convert("L").convert("RGB")).enhance(1.5)
    return img

def adjust(img, clip):
    if clip.filter != "None": img = pil_filter(img, clip.filter)
    img = ImageEnhance.Brightness(img).enhance(clip.brightness)
    img = ImageEnhance.Contrast(img).enhance(clip.contrast)
    img = ImageEnhance.Color(img).enhance(clip.saturation)
    if clip.rotation: img = img.rotate(-clip.rotation, expand=True)
    if clip.flip_h:   img = ImageOps.mirror(img)
    if clip.flip_v:   img = ImageOps.flip(img)
    return img

# ══════════════════════════════════════════════════════════════════════
# DATA MODELS
# ══════════════════════════════════════════════════════════════════════
class Overlay:
    def __init__(self):
        self.kind    = "text"
        self.content = "Text"
        self.x       = 0.5
        self.y       = 0.5
        self.size    = 40
        self.color   = "#FFFFFF"
        self.bold    = True
        self.start   = 0.0
        self.end     = 3.0
    def to_dict(self): return self.__dict__.copy()
    @classmethod
    def from_dict(cls, d):
        o = cls(); o.__dict__.update(d); return o

class Clip:
    def __init__(self, path):
        self.path       = path
        self.filename   = os.path.basename(path)
        self.label      = ""  # user-defined display name (set via Rename)
        self.is_image   = path.lower().endswith(
            (".jpg",".jpeg",".png",".gif",".bmp",".webp",".tiff"))
        self.duration   = 3.0 if self.is_image else self._probe()
        self.start_cut  = 0.0
        self.end_cut    = self.duration
        self.speed      = 1.0
        self.filter     = "None"
        self.brightness = 1.0
        self.contrast   = 1.0
        self.saturation = 1.0
        self.rotation   = 0
        self.flip_h     = False
        self.flip_v     = False
        self.transition = "None"
        self.trans_dur  = 0.5
        self.overlays   = []
        self.pip_path   = None
        self.pip_pos    = "bottom-right"
        self.pip_scale  = 0.25
        self.green_screen = False
        self.gs_tol     = 80
        self.thumb      = None
        self.grade      = {}  # color grading settings

    def _probe(self):
        if not MOVIEPY_AVAILABLE: return 10.0
        try:
            c = VideoFileClip(self.path); d = c.duration; c.close(); return d
        except: return 10.0

    @property
    def trimmed(self):
        return max(0.1, self.end_cut - self.start_cut) / max(0.1, self.speed)

    def load_thumb(self, size=(128,72)):
        if not PIL_AVAILABLE: return
        try:
            if self.is_image:
                img = Image.open(self.path).convert("RGB")
            elif MOVIEPY_AVAILABLE:
                c = VideoFileClip(self.path)
                img = Image.fromarray(c.get_frame(min(0.5, c.duration*0.1)))
                c.close()
            else: return
            img.thumbnail(size, Image.LANCZOS)
            pad = Image.new("RGB", size, (243,243,240))
            pad.paste(img, ((size[0]-img.width)//2,(size[1]-img.height)//2))
            self.thumb = ImageTk.PhotoImage(pad)
        except: pass

    def to_dict(self):
        d = {k:v for k,v in self.__dict__.items() if k != "thumb"}
        d["overlays"] = [o.to_dict() for o in self.overlays]
        return d

    @classmethod
    def from_dict(cls, d):
        c = cls(d["path"])
        for k,v in d.items():
            if k == "overlays": c.overlays = [Overlay.from_dict(o) for o in v]
            elif k != "thumb": setattr(c, k, v)
        return c

class Project:
    def __init__(self):
        self.clips        = []
        self.music_path   = None
        self.music_vol    = 0.8
        self.aspect_ratio = "16:9  YouTube"
        self.fps          = 30

    @property
    def res(self): return ASPECT_RATIOS.get(self.aspect_ratio,(1280,720))

    def total_dur(self): return sum(c.trimmed for c in self.clips)

    def to_dict(self):
        return {"clips":[c.to_dict() for c in self.clips],
                "music_path":self.music_path,"music_vol":self.music_vol,
                "aspect_ratio":self.aspect_ratio,"fps":self.fps}

    def from_dict(self, d):
        self.clips        = [Clip.from_dict(c) for c in d.get("clips",[])]
        self.music_path   = d.get("music_path")
        self.music_vol    = d.get("music_vol",0.8)
        self.aspect_ratio = d.get("aspect_ratio","16:9  YouTube")
        self.fps          = d.get("fps",30)

# ══════════════════════════════════════════════════════════════════════
# OVERLAY EDITOR
# ══════════════════════════════════════════════════════════════════════
def open_overlay_editor(root, clip, idx, cb):
    ov = clip.overlays[idx]
    dlg = tk.Toplevel(root)
    dlg.title("Edit Overlay")
    dlg.configure(bg=WHITE)
    dlg.resizable(False, False)
    dlg.grab_set()

    # Canva-style modal header
    hdr = tk.Frame(dlg, bg=ACCENT, height=48); hdr.pack(fill="x"); safe_pp(hdr)
    tk.Label(hdr, text="✦  Edit Overlay", bg=ACCENT, fg=WHITE,
             font=("Helvetica",13,"bold")).pack(side="left", padx=16, pady=12)
    tk.Button(hdr, text="✕", bg=ACCENT, fg=WHITE, relief="flat", bd=0,
              cursor="hand2", font=("Helvetica",14),
              command=dlg.destroy,
              activebackground="#5A52E0", activeforeground=WHITE).pack(side="right", padx=12)

    def row(txt):
        f = tk.Frame(dlg, bg=WHITE); f.pack(fill="x", padx=16, pady=4)
        tk.Label(f, text=txt, bg=WHITE, fg=MUTED,
                 font=("Helvetica",9,"bold"), width=11, anchor="w").pack(side="left")
        return f

    tv = tk.StringVar(value=ov.content)
    entry(row("Content"), tv, width=26).pack(side="left")

    sv = tk.IntVar(value=ov.size)
    tk.Spinbox(row("Font Size"),from_=10,to=120,textvariable=sv,
               bg=CARD,fg=TEXT,relief="flat",width=6,font=F["sm"]).pack(side="left")

    xv = tk.DoubleVar(value=ov.x)
    tk.Scale(row("X (0–1)"),variable=xv,from_=0,to=1,resolution=0.01,
             orient="horizontal",length=180,bg=WHITE,troughcolor=BORDER,
             highlightthickness=0).pack(side="left")

    yv = tk.DoubleVar(value=ov.y)
    tk.Scale(row("Y (0–1)"),variable=yv,from_=0,to=1,resolution=0.01,
             orient="horizontal",length=180,bg=WHITE,troughcolor=BORDER,
             highlightthickness=0).pack(side="left")

    stv = tk.DoubleVar(value=ov.start)
    tk.Spinbox(row("Start (s)"),from_=0,to=max(1,clip.trimmed),increment=0.1,
               format="%.1f",textvariable=stv,bg=CARD,fg=TEXT,relief="flat",
               width=7,font=F["sm"]).pack(side="left")

    env = tk.DoubleVar(value=ov.end)
    tk.Spinbox(row("End (s)"),from_=0,to=max(1,clip.trimmed),increment=0.1,
               format="%.1f",textvariable=env,bg=CARD,fg=TEXT,relief="flat",
               width=7,font=F["sm"]).pack(side="left")

    color_v = tk.StringVar(value=ov.color)
    cr = row("Color")
    cprev = tk.Frame(cr,bg=ov.color,width=26,height=26,cursor="hand2",
                     highlightthickness=1,highlightbackground=BORDER)
    cprev.pack(side="left",padx=(0,6))
    def pick():
        r = colorchooser.askcolor(color=color_v.get(),title="Color",parent=dlg)
        if r[1]: color_v.set(r[1]); safe_cfg(cprev,bg=r[1])
    mkbtn(cr,"Pick",pick,py=3,px=8).pack(side="left")

    bv = tk.BooleanVar(value=ov.bold)
    br = row("Bold")
    tk.Checkbutton(br,variable=bv,bg=WHITE,activebackground=WHITE).pack(side="left")

    sep(dlg).pack(fill="x",padx=14,pady=8)
    bf = tk.Frame(dlg,bg=WHITE); bf.pack(pady=8)
    def save():
        ov.content=tv.get(); ov.size=sv.get()
        ov.x=round(xv.get(),2); ov.y=round(yv.get(),2)
        ov.start=round(stv.get(),2); ov.end=round(env.get(),2)
        ov.color=color_v.get(); ov.bold=bv.get()
        cb(); dlg.destroy()
    mkbtn(bf,"Save",save,style="accent").pack(side="left",padx=4)
    mkbtn(bf,"Cancel",dlg.destroy,style="ghost").pack(side="left",padx=4)

# ══════════════════════════════════════════════════════════════════════
# INSPECTOR
# ══════════════════════════════════════════════════════════════════════
class Inspector(tk.Frame):
    def __init__(self, parent, on_change):
        super().__init__(parent, bg=WHITE, width=300,
                         highlightthickness=0)
        safe_pp(self)
        self._on_change = on_change
        self._clip = None
        self._show_empty()

    def show(self, clip):
        self._clip = clip
        self._rebuild()

    def clear(self):
        self._clip = None
        self._show_empty()

    def _show_empty(self):
        for w in self.winfo_children(): w.destroy()
        f = tk.Frame(self, bg=WHITE); f.pack(expand=True, fill="both")
        tk.Frame(f, height=50, bg=WHITE).pack()
        # Icon circle using canvas (more reliable than Frame+place)
        cv = tk.Canvas(f, width=72, height=72, bg=WHITE,
                       highlightthickness=0)
        cv.pack()
        cv.create_oval(4, 4, 68, 68, fill=SEL, outline=ACCENT, width=2)
        cv.create_text(36, 36, text="✦", fill=ACCENT,
                       font=("Helvetica",24,"bold"))
        tk.Frame(f, height=14, bg=WHITE).pack()
        tk.Label(f, text="Inspector", bg=WHITE, fg=TEXT,
                 font=("Helvetica",14,"bold")).pack()
        tk.Label(f, text="Select a clip to start editing",
                 bg=WHITE, fg=MUTED, font=("Helvetica",10),
                 justify="center").pack(pady=6)
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=24, pady=12)
        for tip in [("📁", "Import media from the left panel"),
                    ("🎬", "Click a clip in the timeline"),
                    ("✦",  "Drag overlays in the preview")]:
            row = tk.Frame(f, bg=WHITE); row.pack(fill="x", padx=20, pady=3)
            tk.Label(row, text=tip[0], bg=WHITE, fg=ACCENT,
                     font=("Helvetica",11), width=3).pack(side="left")
            tk.Label(row, text=tip[1], bg=WHITE, fg=MUTED,
                     font=("Helvetica",9), anchor="w").pack(side="left")

    def _rebuild(self):
        for w in self.winfo_children(): w.destroy()
        c = self._clip

        # ── Header with dual gradient stripe ─────────────────────────
        h = tk.Frame(self, bg="#120E2A", height=40)
        h.pack(fill="x"); safe_pp(h)
        tk.Frame(h, bg="#7C3AED", width=2).pack(side="left", fill="y")
        tk.Frame(h, bg="#EC4899", width=2).pack(side="left", fill="y")
        inner_h = tk.Frame(h, bg="#120E2A")
        inner_h.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        tk.Label(inner_h, text=f"✏  {c.filename[:22]}",
                 bg="#120E2A", fg="#EDE9FE",
                 font=("Helvetica",11,"bold"), anchor="w").pack(fill="x")
        tk.Label(inner_h, text=f"{c.trimmed:.1f}s  ·  {c.filter}",
                 bg="#120E2A", fg="#6B7FBA",
                 font=("Helvetica",8), anchor="w").pack(fill="x")

        # ── Tab bar ───────────────────────────────────────────────────
        tab_bar = tk.Frame(self, bg=DARK, height=30)
        tab_bar.pack(fill="x"); safe_pp(tab_bar)
        self._insp_tab = tk.StringVar(value="adjust")
        self._insp_tab_btns = {}
        self._insp_tab_frames = {}

        self._insp_tab_indicators = {}

        def _switch_tab(name):
            self._insp_tab.set(name)
            for n, b in self._insp_tab_btns.items():
                on = (n == name)
                safe_cfg(b, bg=WHITE, fg=ACCENT if on else "#4A5275",
                         font=("Helvetica", 8, "bold" if on else "normal"))
                # Show/hide accent indicator line
                ind = self._insp_tab_indicators.get(n)
                if ind:
                    ind.pack(fill="x") if on else ind.pack_forget()
            for n, f in self._insp_tab_frames.items():
                if n == name: f.pack(fill="both", expand=True)
                else:
                    try: f.pack_forget()
                    except Exception: pass

        for tid, tlbl in [("adjust","🎨 Adjust"),("transform","⚡ Transform"),
                           ("overlays","✦ Overlays"),("clip","✂ Clip")]:
            container = tk.Frame(tab_bar, bg=WHITE)
            container.pack(side="left", fill="both", expand=True)
            b = tk.Button(container, text=tlbl, bg=WHITE, fg="#4A5275",
                          relief="flat", bd=0, cursor="hand2",
                          font=("Helvetica",8), padx=8, pady=7,
                          activebackground=WHITE, activeforeground=ACCENT,
                          command=lambda n=tid: _switch_tab(n))
            b.pack(fill="both", expand=True)
            # Bottom indicator bar
            ind = tk.Frame(container, bg=ACCENT, height=2)
            self._insp_tab_indicators[tid] = ind
            self._insp_tab_btns[tid] = b
        # Show adjust as active
        safe_cfg(self._insp_tab_btns["adjust"], fg=ACCENT,
                 font=("Helvetica",8,"bold"))
        self._insp_tab_indicators["adjust"].pack(fill="x")

        # ── Scrollable container for all tab bodies ───────────────────
        if CTK_AVAILABLE:
            scroll_host = ctk.CTkScrollableFrame(self, fg_color=WHITE,
                                                  corner_radius=0,
                                                  scrollbar_button_color=BORDER,
                                                  scrollbar_button_hover_color=MUTED)
            scroll_host.pack(fill="both", expand=True)
            body = scroll_host
        else:
            sf, body = scrollframe(self)
            sf.pack(fill="both", expand=True)

        # ── Helper: collapsible section ───────────────────────────────
        _open_sections = getattr(self, "_open_sections", {
            "Tone & Exposure":True,"Color Grading":True,"Detail":False,
            "Effects":False,"LUT Presets":False,"Filter Presets":True,
            "Trim":True,"Speed":True,"Transition":False,"Transform":True,
            "Picture-in-Picture":False,"Green Screen":False,"Overlays":True,
        })
        self._open_sections = _open_sections

        def collapsible(parent, title, open_by_default=True):
            """Returns body frame — header toggles visibility on click."""
            is_open = _open_sections.get(title, open_by_default)
            wrapper = tk.Frame(parent, bg=WHITE)
            wrapper.pack(fill="x")

            hf = tk.Frame(wrapper, bg="#111426", cursor="hand2")
            hf.pack(fill="x")
            safe_pp(hf)
            arrow_v = tk.StringVar(value="▾" if is_open else "▸")
            # Left accent bar
            tk.Frame(hf, bg=ACCENT, width=2).pack(side="left", fill="y")
            tk.Label(hf, text=f"  {title.upper()}",
                     bg="#111426", fg="#9BA8CC",
                     font=("Helvetica",7,"bold")).pack(side="left", pady=7, padx=2)
            arrow_lbl = tk.Label(hf, textvariable=arrow_v,
                                  bg="#111426", fg=ACCENT,
                                  font=("Helvetica",8), padx=8)
            arrow_lbl.pack(side="right", pady=4)

            body_f = tk.Frame(wrapper, bg=WHITE)
            if is_open: body_f.pack(fill="x")

            def _toggle(e=None, bf=body_f, av=arrow_v, t=title):
                currently = _open_sections.get(t, True)
                _open_sections[t] = not currently
                if currently:
                    bf.pack_forget()
                    av.set("▸")
                else:
                    bf.pack(fill="x")
                    av.set("▾")

            def _hover_in(e=None):
                safe_cfg(hf, bg="#161929")
                for w in hf.winfo_children():
                    try: safe_cfg(w, bg="#161929")
                    except: pass
            def _hover_out(e=None):
                safe_cfg(hf, bg="#111426")
                for w in hf.winfo_children():
                    try: safe_cfg(w, bg="#111426")
                    except: pass
            for w in [hf, arrow_lbl]:
                w.bind("<Button-1>", _toggle)
                w.bind("<Enter>", _hover_in)
                w.bind("<Leave>", _hover_out)
            for child in hf.winfo_children():
                child.bind("<Button-1>", _toggle)
                child.bind("<Enter>", _hover_in)
                child.bind("<Leave>", _hover_out)

            return body_f

        # ══════════════════════════════════════════════════════════════
        # TAB 1: ADJUST
        # ══════════════════════════════════════════════════════════════
        t_adjust = tk.Frame(body, bg=WHITE)
        t_adjust.pack(fill="both", expand=True)
        self._insp_tab_frames["adjust"] = t_adjust

        # ── Photoshop-style slider helper ─────────────────────────────
        self._adj_vars = {}

        def _ps_slider(parent, label, attr, lo, hi, fmt=".1f", unit=""):
            val = getattr(c, attr, 0.0)
            r = tk.Frame(parent, bg=WHITE); r.pack(fill="x", padx=12, pady=2)
            hd = tk.Frame(r, bg=WHITE); hd.pack(fill="x")
            tk.Label(hd, text=label, bg=WHITE, fg=TEXT,
                     font=("Helvetica",9), anchor="w", width=12).pack(side="left")
            v = tk.DoubleVar(value=val); self._adj_vars[attr] = v

            # Clickable value badge (Feature 4: type exact value)
            vl = tk.Label(hd, bg="#0D1020", fg=ACCENT,
                          font=("Helvetica",8,"bold"), padx=5, pady=2,
                          width=7, cursor="hand2",
                          highlightthickness=1, highlightbackground="#252847")
            vl.pack(side="right")

            def _upd(*a, _vl=vl, _v=v): safe_cfg(_vl, text=f"{_v.get():{fmt}}{unit}")
            v.trace_add("write", _upd); _upd()

            def _click_val(e, _vl=vl, _v=v, _lo=lo, _hi=hi, _attr=attr):
                """Click badge to type exact value."""
                popup = tk.Toplevel()
                popup.overrideredirect(True)
                popup.configure(bg=CARD)
                popup.geometry(f"90x28+{e.x_root-45}+{e.y_root-14}")
                popup.attributes("-topmost", True)
                ev = tk.StringVar(value=f"{_v.get():{fmt}}")
                entry = tk.Entry(popup, textvariable=ev, bg=CARD, fg=TEXT,
                                  insertbackground=TEXT, relief="flat",
                                  font=("Helvetica",9), justify="center", width=10)
                entry.pack(fill="both", expand=True, padx=2, pady=2)
                entry.select_range(0, "end"); entry.focus_set()
                def _commit(e=None):
                    try:
                        val = float(ev.get())
                        val = max(_lo, min(_hi, val))
                        _v.set(val)
                        self._set(_attr, val)
                    except ValueError: pass
                    popup.destroy()
                entry.bind("<Return>", _commit)
                entry.bind("<Escape>", lambda e: popup.destroy())
                entry.bind("<FocusOut>", _commit)

            vl.bind("<Button-1>", _click_val)

            # Default value for double-click reset
            _defaults = {"exposure":0,"highlights":0,"shadows":0,"whites":0,"blacks":0,
                         "brightness":1,"contrast":1,"saturation":1,"vibrance":0,"hue_shift":0,
                         "temperature":0,"tint":0,"sharpness":0,"clarity":0,"noise_reduce":0,
                         "vignette":0,"grain":0,"blur_radius":0,"opacity":1}
            default_val = _defaults.get(attr, 0.0)

            sl = tk.Scale(r, variable=v, from_=lo, to=hi, resolution=(hi-lo)/300,
                     orient="horizontal", bg=WHITE, troughcolor="#1A1D30",
                     highlightthickness=0, showvalue=False, sliderlength=16,
                     sliderrelief="flat", width=6,
                     activebackground=ACCENT, fg=ACCENT,
                     command=lambda val, a=attr: self._set(a, self._adj_vars[a].get()))
            sl.pack(fill="x", expand=True)
            # Scroll wheel adjustment
            sl.bind("<MouseWheel>", lambda e, _v=v, _lo=lo, _hi=hi, _a=attr: (
                _v.set(max(_lo, min(_hi, _v.get() + (_hi-_lo)/100 * (1 if e.delta>0 else -1)))),
                self._set(_a, _v.get())))
            # Double-click to reset to default
            def _reset_slider(e=None, _v=v, _dv=default_val, _a=attr):
                _v.set(_dv)
                self._set(_a, _dv)
            sl.bind("<Double-Button-1>", _reset_slider)
            vl.bind("<Double-Button-1>", _reset_slider)
            # Show reset indicator dot when value differs from default
            def _check_modified(*a, _vl=vl, _v=v, _dv=default_val):
                is_default = abs(_v.get() - _dv) < 0.01
                safe_cfg(_vl, fg=MUTED if is_default else ACCENT,
                         bg="#0D1020" if is_default else "#1A0A30")
            v.trace_add("write", _check_modified); _check_modified()

        # Tone & Exposure
        s = collapsible(t_adjust, "Tone & Exposure", True)
        _ps_slider(s, "Exposure",   "exposure",    -2.0,  2.0, fmt="+.2f")
        _ps_slider(s, "Brightness", "brightness",   0.2,  2.0)
        _ps_slider(s, "Highlights", "highlights", -100,  100, fmt="+.0f")
        _ps_slider(s, "Shadows",    "shadows",    -100,  100, fmt="+.0f")
        _ps_slider(s, "Whites",     "whites",     -100,  100, fmt="+.0f")
        _ps_slider(s, "Blacks",     "blacks",     -100,  100, fmt="+.0f")
        _ps_slider(s, "Contrast",   "contrast",    0.2,  2.0)

        # Color Grading
        s = collapsible(t_adjust, "Color Grading", True)
        _ps_slider(s, "Temperature","temperature", -100,  100, fmt="+.0f", unit="K")
        _ps_slider(s, "Tint",       "tint",        -100,  100, fmt="+.0f")
        _ps_slider(s, "Saturation", "saturation",   0.0,  2.0)
        _ps_slider(s, "Vibrance",   "vibrance",       0,  100, fmt=".0f")
        _ps_slider(s, "Hue Shift",  "hue_shift",  -180,  180, fmt="+.0f", unit="°")

        # Detail
        s = collapsible(t_adjust, "Detail", False)
        _ps_slider(s, "Sharpness",  "sharpness",    0,  100, fmt=".0f")
        _ps_slider(s, "Clarity",    "clarity",   -100,  100, fmt="+.0f")
        _ps_slider(s, "Noise Reduc.","noise_reduce", 0, 100, fmt=".0f")

        # Effects
        s = collapsible(t_adjust, "Effects", False)
        _ps_slider(s, "Vignette",   "vignette",     0,  100, fmt=".0f")
        _ps_slider(s, "Film Grain", "grain",        0,  100, fmt=".0f")
        _ps_slider(s, "Blur",       "blur_radius",  0,   10, fmt=".1f", unit="px")
        _ps_slider(s, "Opacity",    "opacity",      0.0, 1.0)

        # LUT Presets
        s = collapsible(t_adjust, "LUT Presets", False)
        LUT_COLORS = {"Cinematic":"#1a2040","Orange Teal":"#0d1f18","Vintage":"#2a1e0e",
                      "Moonlight":"#0d1428","Matrix":"#0a1a0a","Bleach":"#262626",
                      "Kodak":"#2a1608","Fuji":"#122214","None":"#1C1F35"}
        LUTS = ["None","Cinematic","Orange Teal","Vintage","Moonlight","Matrix","Bleach","Kodak","Fuji"]
        lut_grid = tk.Frame(s, bg=WHITE); lut_grid.pack(fill="x", padx=12, pady=4)
        for i, lut in enumerate(LUTS):
            sel = getattr(c,"lut","None") == lut
            chip_bg = ACCENT if sel else LUT_COLORS.get(lut, CARD)
            b = tk.Button(lut_grid, text=lut,
                          bg=chip_bg, fg=WHITE if sel else "#7A8BB0",
                          relief="flat", font=("Helvetica",7,"bold" if sel else "normal"),
                          padx=4, pady=6, cursor="hand2",
                          highlightthickness=1 if sel else 0,
                          highlightbackground=ACCENT,
                          activebackground=ACCENT, activeforeground=WHITE,
                          command=lambda l=lut: (self._set("lut",l,True)))
            b.grid(row=i//3, column=i%3, padx=1, pady=1, sticky="ew")
            lut_grid.columnconfigure(i%3, weight=1)
        # Filter Presets — horizontal scrollable strip
        s = collapsible(t_adjust, "Filter Presets", True)
        fstrip_outer = tk.Frame(s, bg=WHITE); fstrip_outer.pack(fill="x", padx=12, pady=4)
        fstrip_canvas = tk.Canvas(fstrip_outer, bg=WHITE, height=52,
                                   highlightthickness=0)
        fstrip_canvas.pack(fill="x")
        fstrip = tk.Frame(fstrip_canvas, bg=WHITE)
        fstrip_canvas.create_window((0,0), window=fstrip, anchor="nw")
        fstrip.bind("<Configure>", lambda e: fstrip_canvas.configure(
            scrollregion=fstrip_canvas.bbox("all")))
        # Mouse scroll
        fstrip_canvas.bind("<MouseWheel>", lambda e: fstrip_canvas.xview_scroll(
            -1 if e.delta>0 else 1, "units"))
        FILTER_ICONS = {"None":"○","Vivid":"◉","Warm":"☀","Cool":"❄","Sepia":"⬡",
                        "B&W":"◑","Fade":"◌","Chrome":"✦","Matte":"▪","Noir":"●"}
        for flt in FILTERS:
            sel = flt == c.filter
            chip_bg = ACCENT if sel else "#16192E"
            fc = tk.Frame(fstrip, bg=chip_bg, cursor="hand2",
                           highlightthickness=1,
                           highlightbackground=ACCENT if sel else "#252847")
            fc.pack(side="left", padx=2, pady=3)
            tk.Label(fc, text=FILTER_ICONS.get(flt,"○"),
                     bg=chip_bg, fg=WHITE if sel else MUTED,
                     font=("Helvetica",12), padx=4, pady=2, cursor="hand2").pack()
            tk.Label(fc, text=flt, bg=chip_bg,
                     fg=WHITE if sel else "#6B7FBA",
                     font=("Helvetica",7,"bold" if sel else "normal"),
                     padx=6, pady=2, cursor="hand2").pack()
            def _f_hover_in(e, f=fc, bg=chip_bg):
                if f["bg"] != ACCENT:
                    safe_cfg(f, bg="#252847")
                    for ch in f.winfo_children(): safe_cfg(ch, bg="#252847")
            def _f_hover_out(e, f=fc, bg=chip_bg):
                if f["bg"] != ACCENT:
                    safe_cfg(f, bg=bg)
                    for ch in f.winfo_children(): safe_cfg(ch, bg=bg)
            for w in [fc] + list(fc.winfo_children()):
                w.bind("<Button-1>", lambda e, v=flt: self._set("filter",v,True))
                w.bind("<Enter>", _f_hover_in)
                w.bind("<Leave>", _f_hover_out)
        # Reset All
        def _reset_all():
            defs = {"exposure":0,"highlights":0,"shadows":0,"whites":0,"blacks":0,
                    "brightness":1,"contrast":1,"saturation":1,"vibrance":0,"hue_shift":0,
                    "temperature":0,"tint":0,"sharpness":0,"clarity":0,"noise_reduce":0,
                    "vignette":0,"grain":0,"blur_radius":0,"opacity":1,"lut":"None","filter":"None"}
            for a,v in defs.items():
                if a in self._adj_vars: self._adj_vars[a].set(v)
                setattr(c, a, v)
            self._on_change(); self._rebuild()
        # Mini histogram display
        hist_frame = tk.Frame(t_adjust, bg="#0D0F1A")
        hist_frame.pack(fill="x", padx=12, pady=(4,2))
        self._hist_canvas = tk.Canvas(hist_frame, bg="#0D0F1A", height=40,
                                       highlightthickness=0)
        self._hist_canvas.pack(fill="x")
        def _draw_histogram():
            cv = self._hist_canvas
            cv.delete("all")
            try:
                w = cv.winfo_width() or 200
                h = 40
                cv.create_rectangle(0,0,w,h,fill="#0D0F1A",outline="")
                if c.is_image and PIL_AVAILABLE:
                    img = Image.open(c.path).convert("L").resize((200,100),Image.LANCZOS)
                    import numpy as np
                    arr = np.array(img).flatten()
                    bins = [0]*32
                    for px in arr:
                        bins[min(px//8, 31)] += 1
                    mx = max(bins) or 1
                    bw = w / 32
                    for i, cnt in enumerate(bins):
                        bh = int((cnt/mx) * (h-4))
                        x0 = int(i*bw); x1 = int((i+1)*bw)
                        brightness = i/31
                        r = int(100 + brightness*155)
                        g = int(80 + brightness*100)
                        b_c = int(180 + brightness*75)
                        color = f"#{r:02x}{g:02x}{b_c:02x}"
                        cv.create_rectangle(x0,h-bh,x1,h,fill=color,outline="")
            except Exception: pass
        self._hist_canvas.bind("<Map>", lambda e: _draw_histogram())
        _draw_histogram()

        mkbtn(t_adjust, "↺  Reset All Adjustments", _reset_all,
              style="ghost", py=5).pack(fill="x", padx=12, pady=6)

        # ══════════════════════════════════════════════════════════════
        # TAB 2: TRANSFORM
        # ══════════════════════════════════════════════════════════════
        t_transform = tk.Frame(body, bg=WHITE)
        self._insp_tab_frames["transform"] = t_transform

        # Speed
        s = collapsible(t_transform, "Speed", True)
        spf = tk.Frame(s, bg=WHITE); spf.pack(fill="x", padx=12, pady=4)
        for spd in [0.25, 0.5, 1.0, 1.5, 2.0, 4.0]:
            sel = abs(c.speed-spd) < 0.01
            tk.Button(spf, text=f"{spd}×",
                      bg=ACCENT if sel else "#22263A",
                      fg=WHITE if sel else MUTED,
                      relief="flat", font=("Helvetica",9), padx=6, pady=5,
                      cursor="hand2",
                      command=lambda v=spd: self._set("speed",v,True)
                      ).pack(side="left", padx=2)

        # Rotation & Flip
        s = collapsible(t_transform, "Transform", True)
        rf = tk.Frame(s, bg=WHITE); rf.pack(fill="x", padx=12, pady=4)
        tk.Label(rf, text="Rotate", bg=WHITE, fg=TEXT,
                 font=("Helvetica",9,"bold")).pack(side="left", padx=(0,8))
        for deg in [0, 90, 180, 270]:
            sel = c.rotation == deg
            tk.Button(rf, text=f"{deg}°",
                      bg=ACCENT if sel else "#22263A",
                      fg=WHITE if sel else MUTED,
                      relief="flat", font=("Helvetica",9), padx=7, pady=4,
                      cursor="hand2",
                      command=lambda d=deg: self._set("rotation",d,True)
                      ).pack(side="left", padx=2)
        flipf = tk.Frame(s, bg=WHITE); flipf.pack(fill="x", padx=12, pady=4)
        tk.Label(flipf, text="Flip", bg=WHITE, fg=TEXT,
                 font=("Helvetica",9,"bold")).pack(side="left", padx=(0,8))
        for txt, axis, active in [("↔  H","h",c.flip_h),("↕  V","v",c.flip_v)]:
            tk.Button(flipf, text=txt,
                      bg=ACCENT if active else "#22263A",
                      fg=WHITE if active else MUTED,
                      relief="flat", font=("Helvetica",9), padx=10, pady=4,
                      cursor="hand2",
                      command=lambda a=axis: self._flip(a)
                      ).pack(side="left", padx=3)

        # Transition
        s = collapsible(t_transform, "Transition", True)
        trf = tk.Frame(s, bg=WHITE); trf.pack(fill="x", padx=12, pady=4)
        for i, tr in enumerate(TRANSITIONS):
            sel = tr == c.transition
            tk.Button(trf, text=tr,
                      bg=ACCENT if sel else "#22263A",
                      fg=WHITE if sel else MUTED,
                      relief="flat", font=("Helvetica",9), padx=6, pady=5,
                      cursor="hand2",
                      command=lambda v=tr: self._set("transition",v,True)
                      ).grid(row=i//3, column=i%3, padx=2, pady=2, sticky="ew")
            trf.columnconfigure(i%3, weight=1)

        # PiP
        s = collapsible(t_transform, "Picture-in-Picture", False)
        if c.pip_path:
            tk.Label(s, text=f"📹 {os.path.basename(c.pip_path)[:22]}",
                     bg=WHITE, fg=GREEN, font=F["xs"]).pack(padx=12, anchor="w")
            pf = tk.Frame(s, bg=WHITE); pf.pack(fill="x", padx=12, pady=2)
            ppv = tk.StringVar(value=c.pip_pos)
            om = tk.OptionMenu(pf, ppv, "top-left","top-right",
                                "bottom-left","bottom-right","center",
                                command=lambda v: self._set("pip_pos",v))
            safe_cfg(om, bg=WHITE, fg=TEXT, relief="flat", font=F["xs"],
                      highlightthickness=0, activebackground=SEL)
            om.pack(side="left", padx=4)
            mkbtn(s, "✕ Remove PiP", self._remove_pip, style="danger", py=3
                  ).pack(padx=12, anchor="w", pady=2)
        mkbtn(s, "＋ Set PiP Video", self._set_pip, py=3
              ).pack(padx=12, anchor="w", pady=2)

        # Green Screen
        if not c.is_image:
            s = collapsible(t_transform, "Green Screen", False)
            gsf = tk.Frame(s, bg=WHITE); gsf.pack(fill="x", padx=12, pady=2)
            self._gsv = tk.BooleanVar(value=c.green_screen)
            tk.Checkbutton(gsf, text="Enable", variable=self._gsv,
                           bg=WHITE, activebackground=WHITE, font=F["sm"],
                           command=lambda: self._set("green_screen",self._gsv.get())
                           ).pack(side="left")
            gsf2 = tk.Frame(s, bg=WHITE); gsf2.pack(fill="x", padx=12)
            tk.Label(gsf2, text="Tolerance", bg=WHITE, fg=MUTED,
                     font=F["xs"]).pack(side="left")
            self._gstv = tk.IntVar(value=c.gs_tol)
            tk.Scale(gsf2, variable=self._gstv, from_=10, to=200,
                     orient="horizontal", length=120, bg=WHITE,
                     troughcolor=BORDER, highlightthickness=0, showvalue=True,
                     command=lambda v: self._set("gs_tol",self._gstv.get())
                     ).pack(side="left")

        if c.is_image:
            s = collapsible(t_transform, "Image Duration", True)
            idf = tk.Frame(s, bg=WHITE); idf.pack(fill="x", padx=12, pady=2)
            tk.Label(idf, text="Seconds", bg=WHITE, fg=MUTED,
                     font=F["xs"]).pack(side="left")
            self._idv = tk.DoubleVar(value=c.duration)
            tk.Spinbox(idf, from_=0.5, to=30, increment=0.5,
                       textvariable=self._idv,
                       bg=CARD, fg=TEXT, relief="flat",
                       width=7, font=F["sm"]).pack(side="left", padx=4)
            mkbtn(s, "Apply", self._apply_img_dur, style="accent",
                  py=3).pack(padx=12, anchor="w", pady=2)

        # ══════════════════════════════════════════════════════════════
        # TAB 3: OVERLAYS
        # ══════════════════════════════════════════════════════════════
        t_overlays = tk.Frame(body, bg=WHITE)
        self._insp_tab_frames["overlays"] = t_overlays

        s = collapsible(t_overlays, "Overlays", True)
        mkbtn(s, "＋  Add Text Overlay", self._add_text_ov,
              style="accent", py=6).pack(fill="x", padx=12, pady=4)
        self._ovf = tk.Frame(s, bg=WHITE); self._ovf.pack(fill="x", padx=12)
        self._refresh_ovs()

        # ══════════════════════════════════════════════════════════════
        # TAB 4: CLIP
        # ══════════════════════════════════════════════════════════════
        t_clip = tk.Frame(body, bg=WHITE)
        self._insp_tab_frames["clip"] = t_clip

        # Trim
        s = collapsible(t_clip, "Trim", True)
        tf = tk.Frame(s, bg=WHITE); tf.pack(fill="x", padx=12, pady=4)
        tk.Label(tf, text="Start", bg=WHITE, fg=MUTED,
                 font=F["xs"], width=7, anchor="w").grid(row=0,column=0,sticky="w")
        self._sv = tk.DoubleVar(value=c.start_cut)
        tk.Spinbox(tf, from_=0, to=c.duration, increment=0.1, format="%.1f",
                   textvariable=self._sv, bg=CARD, fg=TEXT, relief="flat",
                   width=8, font=F["sm"]).grid(row=0,column=1,padx=4,pady=2)
        tk.Label(tf, text="End", bg=WHITE, fg=MUTED,
                 font=F["xs"], width=7, anchor="w").grid(row=1,column=0,sticky="w")
        self._ev = tk.DoubleVar(value=c.end_cut)
        tk.Spinbox(tf, from_=0, to=c.duration, increment=0.1, format="%.1f",
                   textvariable=self._ev, bg=CARD, fg=TEXT, relief="flat",
                   width=8, font=F["sm"]).grid(row=1,column=1,padx=4,pady=2)
        btn_row = tk.Frame(s, bg=WHITE); btn_row.pack(fill="x", padx=12, pady=6)
        mkbtn(btn_row,"✔  Apply Trim",self._apply_trim,style="accent",py=6,px=14
              ).pack(side="left",padx=(0,6))
        mkbtn(btn_row,"✂ Split",self._split_clip,py=6,px=12).pack(side="left")

        # Clip info
        s = collapsible(t_clip, "Clip Info", True)
        for label, val in [("File", c.filename[:24]),
                            ("Duration", f"{c.duration:.1f}s"),
                            ("Trimmed", f"{c.trimmed:.1f}s"),
                            ("Speed", f"{c.speed}×"),
                            ("Type", "Image" if c.is_image else "Video")]:
            row = tk.Frame(s, bg=WHITE); row.pack(fill="x", padx=12, pady=1)
            tk.Label(row, text=label, bg=WHITE, fg=MUTED,
                     font=("Helvetica",8), width=9, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=WHITE, fg=TEXT,
                     font=("Helvetica",9,"bold"), anchor="w").pack(side="left")

        # Remove clip button
        def _do_remove():
            app = self.winfo_toplevel()
            if hasattr(app, "_on_del") and hasattr(app, "_sel") and app._sel is not None:
                app._on_del(app._sel)
            else:
                self._on_change()
        mkbtn(t_clip, "🗑  Remove This Clip", _do_remove,
              style="danger", py=7).pack(fill="x", padx=12, pady=8)

        # Show adjust tab by default
        _switch_tab("adjust")

    def _set(self, attr, val, rebuild=False):
        if self._clip:
            setattr(self._clip, attr, val)
            self._on_change()
            if rebuild: self._rebuild()

    def _apply_trim(self):
        c = self._clip
        if not c: return
        s = max(0.0, min(self._sv.get(), c.duration))
        e = max(s+0.1, min(self._ev.get(), c.duration))
        c.start_cut=round(s,2); c.end_cut=round(e,2)
        self._on_change()

    def _split_clip(self):
        """Split clip at its midpoint into two clips."""
        c = self._clip
        if not c: return
        import copy
        mid = round((c.start_cut + c.end_cut) / 2, 2)
        if mid <= c.start_cut or mid >= c.end_cut:
            messagebox.showwarning("Cannot Split","Clip too short to split."); return
        root = self.winfo_toplevel()
        proj = getattr(root, "_proj", None)
        if not proj: return
        try: idx = proj.clips.index(c)
        except ValueError: return
        c2 = copy.deepcopy(c)
        c2.start_cut = mid; c2.end_cut = c.end_cut
        c.end_cut = mid
        proj.clips.insert(idx+1, c2)
        c2.load_thumb()
        self._on_change()
        messagebox.showinfo("Split!",
            f"Clip split at {mid:.1f}s into two parts.")

    def _flip(self, axis):
        if not self._clip: return
        if axis=="h": self._clip.flip_h = not self._clip.flip_h
        else:         self._clip.flip_v = not self._clip.flip_v
        self._on_change(); self._rebuild()

    def _apply_img_dur(self):
        if self._clip and self._clip.is_image:
            d=max(0.5,self._idv.get())
            self._clip.duration=d; self._clip.start_cut=0; self._clip.end_cut=d
            self._on_change()

    def _set_pip(self):
        if not self._clip: return
        p = filedialog.askopenfilename(
            title="PiP Video",
            filetypes=[("Video","*.mp4 *.mov *.avi *.mkv *.webm")])
        if p: self._set("pip_path",p,True)

    def _remove_pip(self):
        self._set("pip_path",None,True)

    def _add_text_ov(self):
        if not self._clip:
            messagebox.showinfo("No Clip","Select a clip first."); return
        ov = Overlay(); ov.end = self._clip.trimmed
        self._clip.overlays.append(ov)
        self._on_change()
        open_overlay_editor(self.winfo_toplevel(), self._clip,
                            len(self._clip.overlays)-1, self._ov_cb)

    def _ov_cb(self):
        self._refresh_ovs(); self._on_change()

    def _refresh_ovs(self):
        if not hasattr(self,"_ovf"): return
        for w in self._ovf.winfo_children(): w.destroy()
        if not self._clip: return
        for i,ov in enumerate(self._clip.overlays):
            icon = ("🖼" if ov.kind=="image_sticker" else
                    "😀" if ov.kind=="sticker" else "📝")
            nm   = "AI Sticker" if ov.kind=="image_sticker" else ov.content[:18]
            row  = tk.Frame(self._ovf, bg=CARD,
                            highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=2)
            # Icon + label
            tk.Label(row, text=icon, bg=CARD, fg=TEXT,
                     font=("Helvetica",12), padx=6, pady=4).pack(side="left")
            tk.Label(row, text=nm, bg=CARD, fg=TEXT,
                     font=("Helvetica",9), anchor="w").pack(side="left", fill="x", expand=True)
            # Buttons
            tk.Button(row, text="✏", bg=CARD, fg=ACCENT, relief="flat",
                      font=("Helvetica",11), padx=5, pady=3, cursor="hand2",
                      activebackground=SEL,
                      command=lambda i=i: self._edit_ov(i)).pack(side="left")
            tk.Button(row, text="✕", bg=CARD, fg=A2, relief="flat",
                      font=("Helvetica",11), padx=5, pady=3, cursor="hand2",
                      activebackground="#3D1A2A",
                      command=lambda i=i: self._del_ov(i)).pack(side="left", padx=(0,4))

    def _edit_ov(self, idx):
        if self._clip:
            open_overlay_editor(self.winfo_toplevel(),self._clip,idx,self._ov_cb)

    def _del_ov(self, idx):
        if self._clip:
            self._clip.overlays.pop(idx); self._ov_cb()

# ══════════════════════════════════════════════════════════════════════
# PREVIEW
# ══════════════════════════════════════════════════════════════════════
class Preview(tk.Frame):
    """Preview canvas with drag-to-reposition overlay support."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._clip      = None
        self._photo     = None
        self._on_change = None   # set by App after creation
        # drag state
        self._drag_ov      = None   # overlay being dragged
        self._drag_ox      = 0      # drag offset x
        self._drag_oy      = 0      # drag offset y
        self._last_hovered = None   # last clicked overlay index (for Delete key)

        self._cv = tk.Canvas(self, bg=BG, highlightthickness=0, cursor="arrow")
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Configure>",        lambda e: self._render())
        self._cv.bind("<ButtonPress-1>",    self._on_press)
        self._cv.bind("<B1-Motion>",        self._on_drag)
        self._cv.bind("<ButtonRelease-1>",  self._on_release)
        self._cv.bind("<ButtonPress-3>",    self._on_right_click)   # right-click = delete
        self._cv.bind("<Double-Button-1>",  self._on_double_click)  # double-click = delete
        self._cv.bind("<Delete>",           self._on_delete_key)    # Delete key
        # Zoom with Ctrl+scroll
        self._zoom  = 1.0
        self._pan_x = 0
        self._pan_y = 0
        self._cv.bind("<Control-MouseWheel>", self._on_zoom_scroll)
        # Middle mouse pan
        self._cv.bind("<ButtonPress-2>",   self._pan_start)
        self._cv.bind("<B2-Motion>",       self._pan_move)
        self._cv.bind("<BackSpace>",        self._on_delete_key)    # Backspace key
        self._draw_placeholder()

    def _on_zoom_scroll(self, e):
        factor = 1.1 if e.delta > 0 else 0.9
        self._zoom = max(0.25, min(4.0, self._zoom * factor))
        try:
            root = self.winfo_toplevel()
            if hasattr(root, "_zoom_lbl"):
                safe_cfg(root._zoom_lbl, text=f"{int(self._zoom*100)}%")
        except Exception: pass
        self._render()

    def _pan_start(self, e):
        self._pan_sx = e.x - self._pan_x
        self._pan_sy = e.y - self._pan_y

    def _pan_move(self, e):
        self._pan_x = e.x - self._pan_sx
        self._pan_y = e.y - self._pan_sy
        self._render()

    def _draw_placeholder(self):
        self._cv.delete("all")
        w = self._cv.winfo_width() or 500
        h = self._cv.winfo_height() or 300
        # Background
        self._cv.create_rectangle(0, 0, w, h, fill=BG, outline="")
        # Dashed drop-zone card
        pad = 40
        self._cv.create_rectangle(pad, pad, w-pad, h-pad,
            fill="#13151F", outline=BORDER, width=1, dash=(8,5))
        # Large icon circle matching mockup
        cx, cy = w//2, h//2 - 28
        r = 38
        self._cv.create_oval(cx-r, cy-r, cx+r, cy+r,
            fill=SEL, outline=ACCENT, width=2)
        self._cv.create_text(cx, cy,
            text="✦", fill=ACCENT, font=("Helvetica",26,"bold"))
        # Text below circle
        self._cv.create_text(w//2, cy+r+22,
            text="Preview", fill=TEXT, font=("Helvetica",16,"bold"))
        self._cv.create_text(w//2, cy+r+46,
            text="Import media  ·  click a clip in the timeline",
            fill=MUTED, font=("Helvetica",10))

    def show(self, clip):
        self._clip = clip
        self._render()

    def _render(self):
        if not self._clip or not PIL_AVAILABLE:
            self._draw_placeholder(); return
        self._cv.delete("all")
        w = max(self._cv.winfo_width(), 100)
        h = max(self._cv.winfo_height(), 60)
        c = self._clip
        try:
            if c.is_image:
                img = Image.open(c.path).convert("RGB")
            elif MOVIEPY_AVAILABLE:
                vc  = VideoFileClip(c.path)
                img = Image.fromarray(vc.get_frame(min(0.5, vc.duration*0.1)))
                vc.close()
            else:
                self._draw_placeholder(); return

            img = adjust(img, c)
            img.thumbnail((w-8, h-8), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            ix = (w - img.width)  // 2
            iy = (h - img.height) // 2
            self._cv.create_rectangle(0, 0, w, h, fill=BG)
            self._cv.create_image(ix, iy, anchor="nw", image=self._photo)

            # Draw overlays with drag handles
            if not hasattr(self, "_ov_photos"):
                self._ov_photos = []
            self._ov_photos.clear()

            for idx, ov in enumerate(c.overlays):
                ox = int(ov.x * w)
                oy = int(ov.y * h)
                fs = max(8, int(ov.size * h / 500))
                wt = "bold" if ov.bold else "normal"

                if ov.kind == "image_sticker" and os.path.exists(ov.content):
                    # Draw actual image sticker
                    try:
                        stk = Image.open(ov.content).convert("RGBA")
                        size = max(40, min(ov.size, 200))
                        stk.thumbnail((size, size), Image.LANCZOS)
                        # Composite onto transparent background
                        stk_photo = ImageTk.PhotoImage(stk)
                        self._ov_photos.append(stk_photo)   # keep ref
                        self._cv.create_image(ox, oy,
                            anchor="center", image=stk_photo,
                            tags=f"ov_{idx}")
                        r = size // 2 + 4
                    except Exception:
                        # Fallback to emoji if image fails
                        self._cv.create_text(ox, oy, text="🖼",
                            font=("Helvetica", fs), anchor="center",
                            tags=f"ov_{idx}")
                        r = fs // 2 + 4
                else:
                    # Draw text / emoji overlay
                    self._cv.create_text(ox+1, oy+1, text=ov.content,
                        fill="#000000", font=("Helvetica",fs,wt),
                        anchor="center", tags=f"ov_{idx}")
                    self._cv.create_text(ox, oy, text=ov.content,
                        fill=ov.color, font=("Helvetica",fs,wt),
                        anchor="center", tags=f"ov_{idx}")
                    r = max(6, fs//2 + 4)

                # drag handle ring
                self._cv.create_oval(ox-r, oy-r, ox+r, oy+r,
                    outline=ACCENT, width=1, dash=(3,3),
                    tags=f"ov_{idx}")
        except Exception:
            self._draw_placeholder()

    def _find_overlay_at(self, x, y):
        """Return overlay index at canvas position (x,y), or None."""
        if not self._clip:
            return None
        w = max(self._cv.winfo_width(), 1)
        h = max(self._cv.winfo_height(), 1)
        for idx, ov in enumerate(self._clip.overlays):
            ox = int(ov.x * w)
            oy = int(ov.y * h)
            if ov.kind == "image_sticker":
                hit = max(40, min(ov.size, 200)) // 2 + 8
            else:
                fs  = max(8, int(ov.size * h / 500))
                hit = fs + 10
            if abs(x - ox) < hit and abs(y - oy) < hit:
                return idx
        return None

    def _on_press(self, e):
        idx = self._find_overlay_at(e.x, e.y)
        if idx is not None:
            self._drag_ov = idx
            self._last_hovered = idx
            w = max(self._cv.winfo_width(), 1)
            h = max(self._cv.winfo_height(), 1)
            ov = self._clip.overlays[idx]
            self._drag_ox = e.x - int(ov.x * w)
            self._drag_oy = e.y - int(ov.y * h)
            safe_cfg(self._cv,cursor="fleur")
            self._cv.focus_set()   # grab keyboard focus for Delete key
        else:
            self._drag_ov = None
            safe_cfg(self._cv,cursor="arrow")

    def _on_drag(self, e):
        if self._drag_ov is None or not self._clip:
            return
        w = max(self._cv.winfo_width(), 1)
        h = max(self._cv.winfo_height(), 1)
        ov = self._clip.overlays[self._drag_ov]
        ov.x = round(max(0.0, min(1.0, (e.x - self._drag_ox) / w)), 3)
        ov.y = round(max(0.0, min(1.0, (e.y - self._drag_oy) / h)), 3)
        self._render()

    def _on_release(self, e):
        if self._drag_ov is not None and self._on_change:
            self._on_change()
        self._drag_ov = None
        safe_cfg(self._cv,cursor="arrow")

    def _delete_overlay_at(self, x, y):
        """Delete overlay at canvas position. Returns True if deleted."""
        if not self._clip:
            return False
        idx = self._find_overlay_at(x, y)
        if idx is None:
            return False
        ov = self._clip.overlays[idx]
        import tkinter.messagebox as _mb
        name = ov.content[:20] or "overlay"
        if _mb.askyesno("Delete Overlay",
                "Delete this overlay?",
                parent=self._cv):
            self._clip.overlays.pop(idx)
            self._render()
            if self._on_change:
                self._on_change()
            return True
        return False

    def _on_right_click(self, e):
        """Right-click on an overlay to delete it."""
        if not self._clip:
            return
        idx = self._find_overlay_at(e.x, e.y)
        if idx is None:
            return
        # Show context menu
        menu = tk.Menu(self._cv, tearoff=0,
                       bg=CARD, fg=TEXT, font=F["sm"],
                       activebackground=ACCENT, activeforeground=TEXT,
                       relief="flat", bd=0)
        ov = self._clip.overlays[idx]
        menu.add_command(label="✏  Edit overlay",
                         command=lambda: self._edit_overlay(idx))
        menu.add_separator()
        menu.add_command(label="🗑  Delete overlay",
                         command=lambda: self._delete_overlay(idx),
                         foreground=A2)
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def _on_double_click(self, e):
        """Double-click to delete overlay instantly."""
        if not self._clip:
            return
        idx = self._find_overlay_at(e.x, e.y)
        if idx is not None:
            self._delete_overlay(idx)

    def _on_delete_key(self, e):
        """Delete key removes the last selected overlay."""
        if not self._clip or not self._clip.overlays:
            return
        # Delete the last hovered/dragged overlay
        if hasattr(self, "_last_hovered") and self._last_hovered is not None:
            idx = self._last_hovered
            if 0 <= idx < len(self._clip.overlays):
                self._delete_overlay(idx)

    def _delete_overlay(self, idx):
        """Remove overlay at idx and refresh."""
        if not self._clip or idx >= len(self._clip.overlays):
            return
        self._clip.overlays.pop(idx)
        self._drag_ov = None
        self._last_hovered = None
        self._render()
        if self._on_change:
            self._on_change()

    def _edit_overlay(self, idx):
        """Open the overlay editor dialog."""
        if not self._clip or idx >= len(self._clip.overlays):
            return
        from tkinter import Toplevel
        open_overlay_editor(self._cv.winfo_toplevel(),
                            self._clip, idx,
                            lambda: (self._render(),
                                     self._on_change() if self._on_change else None))

# ══════════════════════════════════════════════════════════════════════
# TIMELINE
# ══════════════════════════════════════════════════════════════════════
class Timeline(tk.Frame):
    TW = 128; TH = 76

    def __init__(self, parent, project, on_select, on_delete, on_move, on_change):
        super().__init__(parent, bg=DARK, height=self.TH+56)
        safe_pp(self)
        self._proj=project; self._on_sel=on_select
        self._on_del=on_delete; self._on_move=on_move
        self._on_change=on_change; self._sel=None
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=DARK, height=28)
        hdr.pack(fill="x"); safe_pp(hdr)
        tk.Frame(hdr, bg=ACCENT, width=2).pack(side="left", fill="y")
        tk.Label(hdr, text="  TIMELINE", bg=DARK, fg=MUTED,
                 font=(F["xs"][0],8,"bold")).pack(side="left", padx=(6,12), pady=6)
        self._snap_var = tk.BooleanVar(value=True)
        tk.Checkbutton(hdr, text="Snap", variable=self._snap_var,
                       bg=DARK, fg=MUTED, selectcolor=DARK,
                       activebackground=DARK, activeforeground=ACCENT,
                       font=("Helvetica",8), bd=0, cursor="hand2"
                       ).pack(side="left", padx=4)
        self._multi_del_btn = tk.Button(hdr, text="🗑 Delete Selected",
            bg=A2, fg=WHITE, relief="flat", bd=0, cursor="hand2",
            font=("Helvetica",8), padx=8, pady=4,
            command=self._delete_selected)

        def _tl_btn(txt, cmd=None):
            b = tk.Button(hdr, text=txt, command=cmd or (lambda:None),
                          bg=CARD, fg=MUTED,
                          relief="flat", bd=0, cursor="hand2",
                          font=("Helvetica",8), padx=10, pady=4,
                          activebackground=BORDER, activeforeground=TEXT)
            b.bind("<Enter>", lambda e: safe_cfg(b,fg=TEXT))
            b.bind("<Leave>", lambda e: safe_cfg(b,fg=MUTED))
            return b

        _tl_btn("+ Add Clip").pack(side="left", padx=2)
        self._info = tk.Label(hdr, text="", bg=DARK, fg=MUTED, font=F["xs"])
        self._info.pack(side="right", padx=10)

        track=tk.Frame(self,bg=DARK); track.pack(fill="both",expand=True,padx=6,pady=(0,6))
        self._cv=tk.Canvas(track,bg=DARK,height=self.TH+4,highlightthickness=0)
        hsb=ttk.Scrollbar(track,orient="horizontal",command=self._cv.xview)
        self._cv.configure(xscrollcommand=hsb.set)
        self._cv.pack(fill="both",expand=True)
        hsb.pack(fill="x")
        self._inner=tk.Frame(self._cv,bg=TRACK)
        self._cv.create_window((0,0),window=self._inner,anchor="nw")
        self._inner.bind("<Configure>",
                          lambda e:self._cv.configure(scrollregion=self._cv.bbox("all")))
        # Playhead overlay canvas
        self._ph_x = 0
        self._cv.bind("<Motion>",      self._on_ph_hover)
        self._cv.bind("<Button-1>",    self._on_ph_click)
        self._cv.bind("<B1-Motion>",   self._on_ph_drag)

    def refresh(self, sel=None):
        if sel is not None: self._sel=sel
        for w in self._inner.winfo_children(): w.destroy()
        clips=self._proj.clips
        if not clips:
            ef = tk.Frame(self._inner, bg=DARK); ef.pack(fill="x", padx=20, pady=14)
            tk.Label(ef, text="＋", bg=DARK, fg=ACCENT,
                     font=("Helvetica",20)).pack(side="left", padx=(0,10))
            tf = tk.Frame(ef, bg=DARK); tf.pack(side="left")
            tk.Label(tf, text="Import media to get started",
                     bg=DARK, fg=TEXT, font=("Helvetica",10,"bold")).pack(anchor="w")
            tk.Label(tf, text="📁 Media tab on the left  ·  or + Add Clip below",
                     bg=DARK, fg=MUTED, font=("Helvetica",8)).pack(anchor="w")
            safe_cfg(self._info, text=""); return
        multi = getattr(self, "_multi_sel", set())
        sel_count = len(multi | ({self._sel} if self._sel is not None else set()))
        safe_cfg(self._info, text=f"{len(clips)} clips · {self._proj.total_dur():.1f}s"
                             + (f"  ·  {sel_count} selected" if sel_count > 1 else ""))
        if sel_count > 1:
            try: self._multi_del_btn.pack(side="left", padx=4)
            except: pass
        else:
            try: self._multi_del_btn.pack_forget()
            except: pass
        for i,clip in enumerate(clips): self._make_tile(i,clip)
        # add button
        ab=tk.Frame(self._inner,bg=SEL,width=44,height=self.TH,cursor="hand2",
                    highlightthickness=1,highlightbackground=ACCENT)
        ab.pack(side="left",padx=4,pady=2); safe_pp(ab)
        tk.Label(ab,text="＋",bg=SEL,fg=ACCENT,font=("Helvetica",24),cursor="hand2").pack(expand=True)
        for w in [ab]+list(ab.winfo_children()): w.bind("<Button-1>",lambda e:self._add_more())

    def _make_tile(self,idx,clip):
        sel=idx==self._sel
        clip_color = getattr(clip, "_label_color", None)
        tile_bg = "#2D3A5A" if sel else (clip_color or CARD)
        in_multi_now = idx in getattr(self,"_multi_sel",set())
        border_col = ACCENT if sel else (WARN if in_multi_now else (clip_color or BORDER))
        tile=tk.Frame(self._inner,
                      bg=tile_bg,
                      cursor="hand2",
                      highlightthickness=1,
                      highlightbackground=border_col,
                      width=self.TW,height=self.TH)
        tile.pack(side="left",padx=3,pady=2); safe_pp(tile)
        if clip.thumb:
            tk.Label(tile,image=clip.thumb,bg=ACCENT if sel else CARD,cursor="hand2"
                     ).pack(fill="both",expand=True)
        else:
            tk.Label(tile,text="🖼" if clip.is_image else "🎬",
                     bg=ACCENT if sel else CARD,font=("Helvetica",20),cursor="hand2"
                     ).pack(expand=True)
        strip=tk.Frame(tile,bg=DARK,height=18)
        strip.pack(fill="x",side="bottom"); safe_pp(strip)
        name=clip.filename[:10]+("…" if len(clip.filename)>10 else "")
        tk.Label(strip,text=name,bg=DARK,
                 fg=WHITE if sel else MUTED,font=F["xs"]).pack(side="left",padx=2)
        tk.Label(strip,text=f"{clip.trimmed:.1f}s",bg=DARK,
                 fg=ACCENT if not sel else WHITE,font=F["xs"]).pack(side="right",padx=2)
        # Show ✦ badge if clip has non-default adjustments
        _defaults = {"exposure":0,"highlights":0,"shadows":0,"whites":0,"blacks":0,
                     "brightness":1,"contrast":1,"saturation":1,"vibrance":0,
                     "hue_shift":0,"temperature":0,"tint":0,"sharpness":0,
                     "clarity":0,"noise_reduce":0,"vignette":0,"grain":0,"lut":"None","filter":"None"}
        has_adj = any(abs(getattr(clip,k,v)-v) > 0.01 if isinstance(v,float)
                      else getattr(clip,k,v)!=v
                      for k,v in _defaults.items())
        if has_adj:
            tk.Label(strip,text="✦",bg="#1A0A30",fg=ACCENT,
                     font=("Helvetica",7),padx=2).pack(side="left")
        # Waveform bar for video/audio clips
        if not clip.is_image and NUMPY_AVAILABLE:
            wf = tk.Canvas(tile, bg="#0D1B2A", height=18,
                           highlightthickness=0, width=self.TW)
            wf.pack(fill="x", side="bottom")
            self._draw_waveform(wf, clip, self.TW, 18)
        if clip.speed!=1.0:
            tk.Label(strip,text=f"{clip.speed}×",bg=GREEN,fg=WHITE,font=F["xs"]).pack(side="right")
        if clip.overlays:
            tk.Label(strip,text=f"T{len(clip.overlays)}",bg=A2,fg=WHITE,font=F["xs"]).pack(side="right")
        if getattr(clip,"_note",""):
            tk.Label(strip,text="📝",bg=DARK,fg=WARN,font=("Helvetica",7)).pack(side="right",padx=1)
        # Trim position bar — purple bar showing used portion of clip
        try:
            full_dur = clip.duration
            if full_dur > 0.1 and (clip.start_cut > 0.05 or (full_dur - clip.end_cut) > 0.05):
                tb = tk.Canvas(tile, bg="#0A0C14", height=3,
                               highlightthickness=0, width=self.TW)
                tb.pack(fill="x", side="bottom")
                rs = clip.start_cut / full_dur
                re = clip.end_cut / full_dur
                tb.create_rectangle(0,0,self.TW,3,fill="#0A0C14",outline="")
                tb.create_rectangle(int(rs*self.TW),0,int(re*self.TW),3,
                                    fill=ACCENT,outline="")
        except Exception: pass
        # delete
        dk=tk.Label(tile,text="✕",bg=A2,fg=WHITE,font=F["xs"],cursor="hand2",padx=3,pady=1)
        dk.place(relx=1.0,x=-2,y=2,anchor="ne")
        dk.bind("<Button-1>",lambda e,i=idx:self._on_del(i))
        # move
        if idx>0:
            ml=tk.Label(tile,text="◀",bg=ACCENT,fg=WHITE,font=F["xs"],cursor="hand2",padx=2)
            ml.place(x=2,y=2); ml.bind("<Button-1>",lambda e,i=idx:self._do_move(i,i-1))
        if idx<len(self._proj.clips)-1:
            mr=tk.Label(tile,text="▶",bg=ACCENT,fg=WHITE,font=F["xs"],cursor="hand2",padx=2)
            mr.place(relx=1.0,x=-18,y=2,anchor="ne")
            mr.bind("<Button-1>",lambda e,i=idx:self._do_move(i,i+1))
        # click to select + right-click for color label menu
        def _show_tile_menu(e, i=idx, cl=clip):
            menu = tk.Menu(self, tearoff=0, bg=CARD, fg=TEXT,
                           activebackground=ACCENT, activeforeground=WHITE,
                           relief="flat", bd=0, font=F["xs"])
            menu.add_command(label="🗑  Remove Clip",
                             command=lambda: self._on_del(i))
            menu.add_command(label="✂  Duplicate Clip",
                             command=lambda _i=i: self._duplicate_clip(_i))
            menu.add_command(label="📝  Clip Note…",
                             command=lambda _cl=cl: self._edit_clip_note(_cl))
            menu.add_separator()
            for lbl,col in [("🔵 Blue","#1a2340"),("🟢 Green","#1a2d1a"),
                             ("🔴 Red","#2d1a1a"),("🟡 Yellow","#2d2810"),
                             ("🟣 Purple","#2d1a2d"),("⬜ None",None)]:
                def _set(c=col, _cl=cl):
                    _cl._label_color = c
                    self._on_change()
                menu.add_command(label=lbl, command=_set)
            try: menu.tk_popup(e.x_root, e.y_root)
            finally: menu.grab_release()

        # Tooltip on hover
        def _show_tip(e, _c=clip):
            tip_text = _c.filename
            if getattr(_c,"_note",""): tip_text += f"\n📝 {_c._note}"
            tip_text += f"\n⏱ {_c.trimmed:.1f}s"
            if _c.speed != 1.0: tip_text += f"  ·  {_c.speed}×"
            tip = tk.Toplevel(); tip.overrideredirect(True)
            tip.attributes("-topmost", True); tip.configure(bg="#1C1F35")
            tk.Label(tip, text=tip_text, bg="#1C1F35", fg=TEXT,
                     font=("Helvetica",8), padx=8, pady=5, justify="left",
                     highlightthickness=1, highlightbackground=BORDER).pack()
            tip.geometry(f"+{e.x_root+12}+{e.y_root+12}")
            tile._tip = tip
        def _hide_tip(e):
            if hasattr(tile,"_tip"):
                try: tile._tip.destroy()
                except: pass

        def _bind_sel(w, i=idx):
            w.bind("<Button-1>", lambda e,ii=i: self._select(ii, shift=bool(e.state & 0x1)))
            w.bind("<Button-3>", _show_tile_menu)
            w.bind("<Enter>", _show_tip)
            w.bind("<Leave>", _hide_tip)
        _bind_sel(tile)
        for child in tile.winfo_children():
            if child not in (dk,): _bind_sel(child)

    def _select(self, idx, shift=False):
        if shift:
            if not hasattr(self,"_multi_sel"): self._multi_sel = set()
            if idx in self._multi_sel: self._multi_sel.discard(idx)
            else: self._multi_sel.add(idx)
        else:
            self._multi_sel = set()
        self._sel=idx; self.refresh(); self._on_sel(idx)
    def _do_move(self, a, b): self._on_move(a,b)

    def _draw_waveform(self, canvas, clip, w, h):
        """Draw a simple waveform on the tile canvas using numpy."""
        try:
            import numpy as np
            if not MOVIEPY_AVAILABLE: return
            vc = VideoFileClip(clip.path)
            if not vc.audio:
                vc.close(); return
            # Sample audio at low rate for speed
            fps   = 10
            dur   = min(clip.end_cut - clip.start_cut, 30)
            audio = vc.audio.subclipped(clip.start_cut,
                                         clip.start_cut + dur)
            arr   = audio.to_soundarray(fps=fps)
            vc.close()
            if arr.ndim > 1:
                arr = arr.mean(axis=1)
            # Normalize
            mx = np.abs(arr).max() or 1
            arr = arr / mx
            # Downsample to canvas width
            n = max(1, len(arr))
            step = max(1, n // w)
            chunks = [arr[i:i+step] for i in range(0, len(arr)-step, step)][:w]
            mid = h // 2
            canvas.delete("all")
            canvas.create_rectangle(0,0,w,h,fill="#0D1B2A",outline="")
            for i, chunk in enumerate(chunks):
                amp = int(np.abs(chunk).mean() * mid)
                amp = max(1, min(amp, mid))
                canvas.create_line(i, mid-amp, i, mid+amp,
                                   fill=ACCENT, width=1)
        except Exception:
            pass   # silently skip if audio not available

    def _on_ph_hover(self, e):
        """Show a time tooltip as mouse hovers over timeline."""
        clips = self._proj.clips
        if not clips: return
        total_w = len(clips) * (self.TW + 6)
        total_dur = sum(c.trimmed for c in clips) or 1
        t = (self._cv.canvasx(e.x) / total_w) * total_dur
        t = max(0, min(t, total_dur))
        if hasattr(self, "_ph_line"):
            try: self._cv.delete(self._ph_line)
            except: pass
        x = self._cv.canvasx(e.x)
        self._ph_line = self._cv.create_line(
            x, 0, x, self.TH+10,
            fill=WARN, width=1, dash=(4,3))

    def _on_ph_click(self, e):
        """Jump preview to clicked time position."""
        clips = self._proj.clips
        if not clips: return
        total_w = len(clips) * (self.TW + 6)
        total_dur = sum(c.trimmed for c in clips) or 1
        x = self._cv.canvasx(e.x)
        t = (x / max(total_w, 1)) * total_dur
        t = max(0, min(t, total_dur))
        # Find which clip this time falls in
        elapsed = 0
        for i, clip in enumerate(clips):
            if elapsed + clip.trimmed >= t:
                local_t = clip.start_cut + (t - elapsed)
                self._on_sel(i)
                if hasattr(self, "_scrub_cb") and self._scrub_cb:
                    self._scrub_cb(clip, local_t)
                break
            elapsed += clip.trimmed

    def _on_ph_drag(self, e):
        """Scrub through timeline on drag."""
        self._on_ph_click(e)

    def _duplicate_clip(self, idx):
        """Duplicate a clip and insert it after."""
        import copy
        if 0 <= idx < len(self._proj.clips):
            clone = copy.deepcopy(self._proj.clips[idx])
            clone.load_thumb()
            self._proj.clips.insert(idx+1, clone)
            self._sel = idx+1
            self.refresh(); self._on_change()

    def _edit_clip_note(self, clip):
        """Popup to add/edit a text note on a clip."""
        popup = tk.Toplevel()
        popup.title("Clip Note"); popup.configure(bg=WHITE)
        popup.geometry("300x130"); popup.grab_set()
        tk.Label(popup, text="Clip Note:", bg=WHITE, fg=TEXT,
                 font=F["sm"]).pack(anchor="w", padx=14, pady=(12,2))
        nv = tk.StringVar(value=getattr(clip,"_note",""))
        ent = tk.Entry(popup, textvariable=nv, bg=CARD, fg=TEXT,
                       insertbackground=TEXT, relief="flat",
                       font=F["sm"], width=34)
        ent.pack(fill="x", padx=14, pady=4); ent.focus_set()
        def _save(e=None):
            clip._note = nv.get().strip(); popup.destroy(); self._on_change()
        ent.bind("<Return>", _save)
        bf = tk.Frame(popup, bg=WHITE); bf.pack(fill="x", padx=14, pady=4)
        mkbtn(bf,"Save",_save,style="accent",py=4,px=12).pack(side="left")
        mkbtn(bf,"Cancel",popup.destroy,style="ghost",py=4,px=10).pack(side="left",padx=6)

    def _delete_selected(self):
        paths=filedialog.askopenfilenames(
            title="Add Media",
            filetypes=[("All Media","*.mp4 *.mov *.avi *.mkv *.webm "
                        "*.jpg *.jpeg *.png *.gif *.bmp *.webp")])
        for p in paths:
            c=Clip(p); c.load_thumb(); self._proj.clips.append(c)
        self.refresh(); self._on_change()

# ══════════════════════════════════════════════════════════════════════
# SIDE PANELS
# ══════════════════════════════════════════════════════════════════════
class SidePanel(tk.Frame):
    """Base class for all left panels."""
    def __init__(self, parent, project, get_clip, on_change):
        super().__init__(parent, bg=WHITE)
        self._proj=project; self._get_clip=get_clip; self._on_change=on_change
        if CTK_AVAILABLE:
            sf = ctk.CTkScrollableFrame(self, fg_color=WHITE,
                                         corner_radius=0,
                                         scrollbar_button_color=BORDER,
                                         scrollbar_button_hover_color=MUTED)
            sf.pack(fill="both", expand=True)
            self._body = sf
        else:
            sf, self._body = scrollframe(self)
            sf.pack(fill="both", expand=True)
        self._build()

    def _build(self): pass

class MediaPanel(SidePanel):
    def _build(self):
        b=self._body

        # ── Header ────────────────────────────────────────────────────
        hf = tk.Frame(b,bg=WHITE); hf.pack(fill="x",padx=14,pady=(14,4))
        tk.Label(hf,text="Media Library",bg=WHITE,fg=TEXT,
                 font=("Helvetica",13,"bold")).pack(anchor="w")
        tk.Label(hf,text="Import or choose from templates",
                 bg=WHITE,fg=MUTED,font=("Helvetica",9)).pack(anchor="w")

        # ── Quick Templates ────────────────────────────────────────────
        sec_hdr(b,"Quick Templates",bg=WHITE)
        tg = tk.Frame(b,bg=WHITE); tg.pack(fill="x",padx=12,pady=4)
        templates = [
            ("🏆","Highligh","#1a2340"),
            ("🎬","Cinematic","#1a2a1a"),
            ("✨","Glam","#2d1a2d"),
            ("🔥","Hype","#2d2a1a"),
        ]
        for i,(icon,name,col) in enumerate(templates):
            f = tk.Frame(tg,bg=col,cursor="hand2",
                         highlightthickness=1,highlightbackground=BORDER)
            f.grid(row=0,column=i,padx=3,pady=3,sticky="nsew")
            tg.columnconfigure(i,weight=1)
            tk.Label(f,text=icon,bg=col,font=("Helvetica",22),
                     pady=12,cursor="hand2").pack()
            tk.Label(f,text=name[:7],bg=col,fg=TEXT,
                     font=("Helvetica",8),pady=2,cursor="hand2").pack()
            def _apply_template(name=name):
                # Open import dialog then we could apply a style
                self._import()
            for w in [f]+list(f.winfo_children()):
                w.bind("<Button-1>", lambda e, n=name: self._import())
                w.bind("<Enter>",lambda e,ff=f: safe_cfg(ff,highlightbackground=ACCENT))
                w.bind("<Leave>",lambda e,ff=f: safe_cfg(ff,highlightbackground=BORDER))

        # ── Brand Colors ───────────────────────────────────────────────
        sec_hdr(b,"Brand Colors",bg=WHITE)
        cf = tk.Frame(b,bg=WHITE); cf.pack(fill="x",padx=14,pady=4)
        colors = ["#6366F1","#F472B6","#10B981","#F59E0B","#EF4444","#FFFFFF","#64748B"]
        for i,col in enumerate(colors):
            tk.Frame(cf,bg=col,width=26,height=26,
                     cursor="hand2").grid(row=i//4,column=i%4,padx=3,pady=3)
            cf.columnconfigure(i%4,weight=0)

        # ── Import Button ──────────────────────────────────────────────
        sep(b).pack(fill="x",padx=12,pady=8)
        if CTK_AVAILABLE:
            ctk.CTkButton(b, text="＋  Import Media",
                          command=self._import,
                          fg_color=ACCENT, text_color=WHITE,
                          hover_color="#5A52E0", corner_radius=4,
                          font=ctk.CTkFont(size=11,weight="bold"),
                          height=38).pack(fill="x",padx=14,pady=4)
        else:
            mkbtn(b,"＋  Import Media",self._import,
                  style="accent",py=8).pack(fill="x",padx=14,pady=4)

        # ── AI Features ───────────────────────────────────────────────
        sec_hdr(b,"AI Features",bg=WHITE)

        def _go_ai(mode):
            """Switch to AI panel and open the correct mode tab."""
            app = self.winfo_toplevel()
            # Switch sidebar to AI panel
            if hasattr(app, "_switch"):
                app._switch("ai")
            # Switch to the correct AI mode tab
            ai_panel = getattr(app, "_panels", {}).get("ai")
            if ai_panel and hasattr(ai_panel, "_switch_mode"):
                ai_panel._switch_mode(mode)

        ai_feats = [
            ("✦  AI Auto-Caption",    "#2D2F52", ACCENT,  "analyse"),
            ("✂  Background Remover", "#1A2D1A", GREEN,   "analyse"),
            ("🎬  Sora Video Gen",     "#1A1A2D", "#818CF8","sora"),
            ("✨  DALL-E Stickers",    "#2D1A2D", A2,      "imagegen"),
        ]
        for txt,bg_col,fg_col,mode in ai_feats:
            cmd = lambda m=mode: _go_ai(m)
            if CTK_AVAILABLE:
                ctk.CTkButton(b, text=txt,
                              fg_color=bg_col, text_color=fg_col,
                              hover_color=ACCENT, corner_radius=6,
                              font=ctk.CTkFont(size=10),
                              height=34, anchor="w",
                              command=cmd
                              ).pack(fill="x",padx=14,pady=2)
            else:
                btn = tk.Button(b,text=txt,bg=bg_col,fg=fg_col,
                                relief="flat",font=("Helvetica",9),
                                padx=10,pady=7,cursor="hand2",anchor="w",
                                command=cmd)
                btn.bind("<Enter>",lambda e,b=btn,c=bg_col: safe_cfg(b,bg=ACCENT))
                btn.bind("<Leave>",lambda e,b=btn,c=bg_col: safe_cfg(b,bg=c))
                btn.pack(fill="x",padx=14,pady=2)
    def _import(self):
        paths=filedialog.askopenfilenames(
            title="Import Media",
            filetypes=[("All Media","*.mp4 *.mov *.avi *.mkv *.webm "
                        "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff"), ("Video","*.mp4 *.mov *.avi *.mkv *.webm"),
                       ("Image","*.jpg *.jpeg *.png *.gif *.bmp *.webp")])
        for p in paths:
            c=Clip(p); c.load_thumb(); self._proj.clips.append(c)
        self._on_change()

    def _import_seq(self):
        folder=filedialog.askdirectory(title="Image Sequence Folder")
        if folder:
            files=sorted([os.path.join(folder,f) for f in os.listdir(folder)
                          if f.lower().endswith((".jpg",".jpeg",".png"))])
            for p in files:
                c=Clip(p); c.load_thumb(); self._proj.clips.append(c)
            self._on_change()

class TextPanel(SidePanel):
    def _build(self):
        b=self._body
        hf=tk.Frame(b,bg=WHITE); hf.pack(fill="x",padx=14,pady=(14,4))
        tk.Label(hf,text="Text",bg=WHITE,fg=TEXT,
                 font=("Helvetica",15,"bold")).pack(anchor="w")
        tk.Label(hf,text="Add titles and overlays to your clip",
                 bg=WHITE,fg=MUTED,font=F["xs"]).pack(anchor="w")
        sep(b).pack(fill="x",padx=12,pady=8)
        mkbtn(b,"＋  Add Text Box",self._add,style="accent",py=10
              ).pack(fill="x",padx=12,pady=4)
        sec_hdr(b,"Quick Styles",bg=WHITE)
        for name,sz,bold,col in [("Big Title",52,True,TEXT),("Subtitle",36,False,TEXT),
                              ("Caption",24,False,MUTED),("Label",20,True,ACCENT)]:
            f=tk.Frame(b,bg=CARD,highlightthickness=1,highlightbackground=BORDER,
                       cursor="hand2")
            f.pack(fill="x",padx=12,pady=3)
            tk.Label(f,text=name,bg=CARD,fg=col,cursor="hand2",
                     font=("Helvetica",min(sz//2,16),"bold" if bold else "normal"),
                     pady=10,padx=12).pack()
            for w in [f]+list(f.winfo_children()):
                w.bind("<Button-1>",lambda e,s=sz,bl=bold:self._add_styled(s,bl))
                w.bind("<Enter>",lambda e,ff=f: safe_cfg(ff,highlightbackground=ACCENT))
                w.bind("<Leave>",lambda e,ff=f: safe_cfg(ff,highlightbackground=BORDER))

    def _add(self): self._add_styled(36,False)
    def _add_styled(self,size,bold):
        clip=self._get_clip()
        if not clip: messagebox.showinfo("No Clip","Select a clip first."); return
        ov=Overlay(); ov.size=size; ov.bold=bold; ov.end=clip.trimmed
        clip.overlays.append(ov)
        self._on_change()
        open_overlay_editor(self.winfo_toplevel(),clip,len(clip.overlays)-1,self._on_change)

class StickerPanel(SidePanel):
    def _build(self):
        b=self._body
        hf=tk.Frame(b,bg=WHITE); hf.pack(fill="x",padx=14,pady=(14,4))
        tk.Label(hf,text="Stickers",bg=WHITE,fg=TEXT,
                 font=("Helvetica",15,"bold")).pack(anchor="w")
        tk.Label(hf,text="AI-generated and emoji stickers",
                 bg=WHITE,fg=MUTED,font=F["xs"]).pack(anchor="w")

        # DALL-E AI Sticker Generator
        if CTK_AVAILABLE:
            ai_frame = ctk.CTkFrame(b, fg_color=CARD, corner_radius=10,
                                     border_width=2, border_color=ACCENT)
            ai_frame.pack(fill="x", padx=12, pady=8)
            hdr = ctk.CTkFrame(ai_frame, fg_color=ACCENT, corner_radius=4)
            hdr.pack(fill="x", padx=2, pady=2)
            ctk.CTkLabel(hdr, text="✨  AI Sticker Generator  (DALL-E)",
                         text_color=WHITE, fg_color="transparent",
                         font=ctk.CTkFont(size=11,weight="bold")).pack(
                         side="left", padx=10, pady=8)
        else:
            ai_frame = tk.Frame(b, bg=CARD, highlightthickness=1, highlightbackground=ACCENT)
            ai_frame.pack(fill="x", padx=12, pady=8)
            hdr = tk.Frame(ai_frame, bg=ACCENT); hdr.pack(fill="x")
            tk.Label(hdr, text="✨  AI Sticker Generator  (DALL-E)",
                     bg=ACCENT, fg=WHITE, font=F["sm"], pady=6, padx=10).pack(side="left")
        sec_hdr(ai_frame, "Describe your sticker", bg=CARD)
        self._dalle_prompt = tk.Text(ai_frame, height=3, bg=WHITE, fg=TEXT,
                                      insertbackground=TEXT, relief="flat",
                                      font=F["sm"], wrap="word",
                                      highlightthickness=1, highlightbackground=BORDER)
        self._dalle_prompt.pack(fill="x", padx=10, pady=4)
        self._dalle_prompt.insert("1.0",
            "A glowing golden trophy with sparkles, cartoon style, white background")
        style_f = tk.Frame(ai_frame, bg=CARD); style_f.pack(fill="x", padx=10, pady=2)
        tk.Label(style_f, text="Style:", bg=CARD, fg=MUTED, font=F["xs"]).pack(side="left")
        self._dalle_style_v = tk.StringVar(value="cartoon sticker")
        for style in ["cartoon","pixel art","watercolor","neon","flat icon"]:
            tk.Button(style_f, text=style, bg=WHITE, fg=TEXT,
                      relief="flat", font=F["xs"], padx=4, pady=2, cursor="hand2",
                      command=lambda s=style: self._dalle_style_v.set(s)
                      ).pack(side="left", padx=1)
        self._dalle_gen_btn = mkbtn(ai_frame, "✨  Generate AI Sticker",
                                     self._generate_dalle_sticker, style="accent", px=12, py=6)
        self._dalle_gen_btn.pack(fill="x", padx=10, pady=6)
        self._dalle_canvas = tk.Canvas(ai_frame, bg="#111827",
                                        highlightthickness=0, width=120, height=120)
        self._dalle_canvas.pack(pady=4)
        self._dalle_canvas.create_text(60, 60, text="AI sticker\npreview",
            fill=MUTED, font=F["xs"], justify="center")
        self._dalle_photo   = None
        self._dalle_pil_img = None
        mkbtn(ai_frame, "➕  Add to Clip", self._add_dalle_sticker,
              style="green", px=10, py=4).pack(fill="x", padx=10, pady=(0,8))

        # Emoji Stickers
        sep(b).pack(fill="x",padx=12,pady=8)
        lbl(b,"Emoji Stickers",fg=MUTED,font=F["xs"],bg=WHITE).pack(padx=12,anchor="w")
        grid=tk.Frame(b,bg=WHITE); grid.pack(fill="x",padx=12,pady=4)
        for i,s in enumerate(STICKERS):
            f=tk.Frame(grid,bg=CARD,cursor="hand2",
                       highlightthickness=1,highlightbackground=BORDER)
            f.grid(row=i//4,column=i%4,padx=3,pady=3,sticky="ew")
            grid.columnconfigure(i%4,weight=1)
            lw=tk.Label(f,text=s,bg=CARD,font=("Helvetica",20),pady=4,cursor="hand2")
            lw.pack()
            for w in [f,lw]: w.bind("<Button-1>",lambda e,st=s:self._add(st))

    def _generate_dalle_sticker(self):
        key = _SETTINGS.get("openai_api_key","").strip()
        if not key:
            messagebox.showwarning("OpenAI Key Required",
                "Enter your OpenAI key in Settings to use AI sticker generation.")
            return
        prompt = self._dalle_prompt.get("1.0","end").strip()
        if not prompt:
            messagebox.showwarning("No Prompt","Describe your sticker first.")
            return
        style = self._dalle_style_v.get()
        full_prompt = f"{prompt}, {style} style, white background, high quality, no text"
        safe_cfg(self._dalle_gen_btn,state="disabled", text="Generating…")

        def _go():
            try:
                payload = json.dumps({
                    "model": "dall-e-3",
                    "prompt": full_prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "response_format": "b64_json",
                }).encode()
                req = urllib.request.Request(
                    "https://api.openai.com/v1/images/generations",
                    data=payload,
                    headers={"Authorization": f"Bearer {key}",
                             "Content-Type": "application/json"},
                    method="POST")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                b64 = data["data"][0]["b64_json"]
                pil_img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
                self._dalle_pil_img = pil_img

                def _show(img=pil_img):
                    disp = img.copy(); disp.thumbnail((120,120), Image.LANCZOS)
                    bg = Image.new("RGBA",(120,120),(17,24,39,255))
                    ox=(120-disp.width)//2; oy=(120-disp.height)//2
                    bg.paste(disp,(ox,oy),disp)
                    photo = ImageTk.PhotoImage(bg)
                    self._dalle_photo = photo
                    self._dalle_canvas.delete("all")
                    self._dalle_canvas.create_image(60,60,anchor="center",image=self._dalle_photo)
                    safe_cfg(self._dalle_gen_btn,state="normal",text="✨  Generate AI Sticker")
                self.after(0, _show)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8",errors="replace")
                try: msg = json.loads(body).get("error",{}).get("message",body[:200])
                except: msg = body[:200]
                self.after(0, lambda m=msg,c=e.code: (
                    safe_cfg(self._dalle_gen_btn,state="normal",text="✨  Generate AI Sticker"),
                    messagebox.showerror("Failed",f"HTTP {c}: {m}")))
            except Exception as ex:
                self.after(0, lambda m=str(ex): (
                    safe_cfg(self._dalle_gen_btn,state="normal",text="✨  Generate AI Sticker"),
                    messagebox.showerror("Error",m)))

        threading.Thread(target=_go, daemon=True).start()

    def _add_dalle_sticker(self):
        if not self._dalle_pil_img:
            messagebox.showinfo("No Sticker","Generate an AI sticker first."); return
        clip = self._get_clip()
        if not clip:
            messagebox.showinfo("No Clip","Select a clip in the timeline first."); return
        import tempfile
        # Save sticker as PNG with transparency
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        self._dalle_pil_img.save(tmp.name, "PNG"); tmp.close()
        ov = Overlay()
        ov.kind    = "image_sticker"   # special kind for image overlays
        ov.content = tmp.name          # content = path to the PNG file
        ov.size    = 120               # display size in pixels
        ov.x       = 0.5
        ov.y       = 0.5
        ov.end     = clip.trimmed
        ov.color   = "#FFFFFF"
        ov.bold    = False
        clip.overlays.append(ov)
        self._on_change()
        Toast.show(self.winfo_toplevel() if hasattr(self,"winfo_toplevel") else self,
                   "AI sticker added! Drag in preview to reposition.", "success")

    def _add(self,sticker):
        clip=self._get_clip()
        if not clip: messagebox.showinfo("No Clip","Select a clip first."); return
        ov=Overlay(); ov.kind="sticker"; ov.content=sticker; ov.size=56; ov.end=clip.trimmed
        clip.overlays.append(ov)
        self._on_change()
        Toast.show(self.winfo_toplevel(), f"{sticker} added to clip!", "success")


class TitlesPanel(SidePanel):
    PRESETS=[("Fade In Title","#FFFFFF","#1A1A2E",52),
             ("Bold Slide","#FFD700","#1A1A2E",48),
             ("Neon Pop","#00FF88","#111111",44),
             ("Cinematic","#FFFFFF","#000000",40),
             ("Retro","#FF6B6B","#FFFFFF",46),
             ("Minimal","#1A1A2E","#F7F7F5",38)]

    def _build(self):
        b=self._body
        hf=tk.Frame(b,bg=WHITE); hf.pack(fill="x",padx=14,pady=(14,4))
        tk.Label(hf,text="Title Cards",bg=WHITE,fg=TEXT,
                 font=("Helvetica",15,"bold")).pack(anchor="w")
        tk.Label(hf,text="Tap a preset to add to your clip",
                 bg=WHITE,fg=MUTED,font=F["xs"]).pack(anchor="w")
        sep(b).pack(fill="x",padx=12,pady=6)
        for name,color,bg_col,size in self.PRESETS:
            if CTK_AVAILABLE:
                btn = ctk.CTkButton(b, text=f"  {name}   Aa {size}pt",
                                     command=lambda n=name,c=color,s=size:self._add(n,c,s),
                                     fg_color=bg_col, text_color=color,
                                     hover_color=ACCENT,
                                     corner_radius=4,
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     height=52, anchor="w")
                btn.pack(fill="x", padx=12, pady=3)
            else:
                f=tk.Frame(b,bg=WHITE,cursor="hand2",
                           highlightthickness=1,highlightbackground=BORDER)
                f.pack(fill="x",padx=12,pady=3)
                inner=tk.Frame(f,bg=bg_col,height=56,cursor="hand2")
                inner.pack(fill="x"); safe_pp(inner)
                lf=tk.Frame(inner,bg=bg_col); lf.place(relx=0,rely=0,relwidth=1,relheight=1)
                tk.Label(lf,text=name,bg=bg_col,fg=color,
                         font=("Helvetica",13,"bold"),cursor="hand2").pack(side="left",padx=12,pady=8)
                tk.Label(lf,text=f"Aa {size}pt",bg=bg_col,
                         fg=color,font=("Helvetica",9),cursor="hand2").pack(side="right",padx=10)
                for w in [f,inner,lf]+list(lf.winfo_children()):
                    w.bind("<Button-1>",lambda e,n=name,c=color,s=size:self._add(n,c,s))
                    w.bind("<Enter>",lambda e,ff=f:safe_cfg(ff,highlightbackground=ACCENT))
                    w.bind("<Leave>",lambda e,ff=f:safe_cfg(ff,highlightbackground=BORDER))

    def _add(self,name,color,size):
        clip=self._get_clip()
        if not clip: messagebox.showinfo("No Clip","Select a clip first."); return
        ov=Overlay(); ov.content="YOUR TITLE"; ov.size=size; ov.color=color
        ov.bold=True; ov.x=0.5; ov.y=0.5; ov.end=min(3.0,clip.trimmed)
        clip.overlays.append(ov)
        self._on_change()
        open_overlay_editor(self.winfo_toplevel(),clip,len(clip.overlays)-1,self._on_change)

class AudioPanel(SidePanel):
    def _build(self):
        b=self._body
        hf=tk.Frame(b,bg=WHITE); hf.pack(fill="x",padx=14,pady=(14,4))
        tk.Label(hf,text="Audio",bg=WHITE,fg=TEXT,
                 font=("Helvetica",15,"bold")).pack(anchor="w")
        tk.Label(hf,text="Add background music to your project",
                 bg=WHITE,fg=MUTED,font=F["xs"]).pack(anchor="w")
        sep(b).pack(fill="x",padx=12,pady=8)
        sec_hdr(b,"Background Music",bg=WHITE)
        mkbtn(b,"♪  Add Music Track",self._import,style="accent",py=10
              ).pack(fill="x",padx=12,pady=4)
        self._mlbl=lbl(b,"No music added",fg=MUTED,font=F["xs"],bg=WHITE)
        self._mlbl.pack(padx=12,anchor="w",pady=2)
        if self._proj.music_path:
            safe_cfg(self._mlbl,text=f"🎵 {os.path.basename(self._proj.music_path)[:26]}",fg=GREEN)
        vf=tk.Frame(b,bg=WHITE); vf.pack(fill="x",padx=12,pady=4)
        vh=tk.Frame(vf,bg=WHITE); vh.pack(fill="x")
        lbl(vh,"Volume",fg=TEXT,font=("Helvetica",9,"bold"),bg=WHITE).pack(side="left")
        self._vol_lbl=tk.Label(vh,bg=SEL,fg=ACCENT,font=("Helvetica",8,"bold"),padx=6,pady=1)
        self._vol_lbl.pack(side="right")
        self._vv=tk.DoubleVar(value=self._proj.music_vol)
        def _upd_vol(*a):
            safe_cfg(self._vol_lbl,text=f"{int(self._vv.get()*100)}%")
            setattr(self._proj,"music_vol",self._vv.get())
        tk.Scale(vf,variable=self._vv,from_=0,to=1,resolution=0.05,
                 orient="horizontal",bg=WHITE,troughcolor=BORDER,
                 highlightthickness=0,showvalue=False,
                 activebackground=ACCENT,
                 command=lambda v:_upd_vol()
                 ).pack(fill="x")
        _upd_vol()
        mkbtn(b,"✕  Remove Music",self._remove,style="danger",py=6
              ).pack(fill="x",padx=12,pady=6)

    def _import(self):
        p=filedialog.askopenfilename(title="Choose Music",
                                      filetypes=[("Audio","*.mp3 *.wav *.aac *.ogg *.flac *.m4a")])
        if p:
            self._proj.music_path=p
            safe_cfg(self._mlbl,text=f"🎵 {os.path.basename(p)[:26]}",fg=GREEN)
            self._on_change()

    def _remove(self):
        self._proj.music_path=None
        safe_cfg(self._mlbl,text="No music added",fg=MUTED)
        self._on_change()

class FormatPanel(SidePanel):
    def _build(self):
        b=self._body
        hf=tk.Frame(b,bg=WHITE); hf.pack(fill="x",padx=14,pady=(14,4))
        tk.Label(hf,text="Format",bg=WHITE,fg=TEXT,
                 font=("Helvetica",15,"bold")).pack(anchor="w")
        tk.Label(hf,text="Canvas size, aspect ratio & quality",
                 bg=WHITE,fg=MUTED,font=F["xs"]).pack(anchor="w")
        sep(b).pack(fill="x",padx=12,pady=8)
        sec_hdr(b,"Aspect Ratio",bg=WHITE)
        self._arv=tk.StringVar(value=self._proj.aspect_ratio)
        ar_grid=tk.Frame(b,bg=WHITE); ar_grid.pack(fill="x",padx=12,pady=4)
        for i,(ar,(w,h)) in enumerate(ASPECT_RATIOS.items()):
            sel=ar==self._proj.aspect_ratio
            btn=tk.Button(ar_grid,text=f"{ar}\n{w}×{h}",
                       bg=SEL if sel else CARD,
                       fg=ACCENT if sel else MUTED,
                       relief="flat",font=("Helvetica",8),
                       padx=4,pady=6,cursor="hand2",
                       highlightthickness=1,
                       highlightbackground=ACCENT if sel else BORDER,
                       command=lambda a=ar:(self._arv.set(a),self._update_ar()))
            btn.grid(row=i//3,column=i%3,padx=2,pady=2,sticky="ew")
            ar_grid.columnconfigure(i%3,weight=1)
        sep(b).pack(fill="x",padx=12,pady=8)
        sec_hdr(b,"FPS",bg=WHITE)
        fpf=tk.Frame(b,bg=WHITE); fpf.pack(fill="x",padx=12,pady=4)
        self._fpv=tk.IntVar(value=self._proj.fps)
        for fps in [24,30,60]:
            sel=fps==self._proj.fps
            tk.Button(fpf,text=f"{fps} fps",
                      bg=SEL if sel else CARD,
                      fg=ACCENT if sel else MUTED,
                      relief="flat",font=("Helvetica",9),
                      padx=10,pady=5,cursor="hand2",
                      highlightthickness=1,
                      highlightbackground=ACCENT if sel else BORDER,
                      command=lambda f=fps:(self._fpv.set(f),
                                           setattr(self._proj,"fps",f))
                      ).pack(side="left",padx=3)

    def _update_ar(self):
        self._proj.aspect_ratio=self._arv.get(); self._on_change()

# ══════════════════════════════════════════════════════════════════════
# COLOR GRADING PANEL
# ══════════════════════════════════════════════════════════════════════
class ColorGradingPanel(SidePanel):
    """Professional curves & levels color grading panel."""
    def _build(self):
        b = self._body

        # Header
        hf = tk.Frame(b, bg=WHITE); hf.pack(fill="x", padx=14, pady=(14,4))
        tk.Label(hf, text="Color Grading", bg=WHITE, fg=TEXT,
                 font=("Helvetica",13,"bold")).pack(anchor="w")
        tk.Label(hf, text="Curves, levels & adjustments",
                 bg=WHITE, fg=MUTED, font=("Helvetica",9)).pack(anchor="w")

        sep(b).pack(fill="x", padx=12, pady=8)

        # ── Curves display ────────────────────────────────────────────
        sec_hdr(b, "RGB Curve", bg=WHITE)
        curve_f = tk.Frame(b, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        curve_f.pack(fill="x", padx=14, pady=4)

        self._curve_canvas = tk.Canvas(curve_f, bg="#0A0C14", width=340, height=180,
                                        highlightthickness=0)
        self._curve_canvas.pack(padx=4, pady=4)

        # Curve channel selector
        ch_f = tk.Frame(b, bg=WHITE); ch_f.pack(fill="x", padx=14, pady=(4,2))
        self._curve_ch = tk.StringVar(value="RGB")
        ch_colors = [("RGB", TEXT), ("R", "#F43F5E"), ("G", "#22D3A5"), ("B", "#38BDF8")]
        for ch, col in ch_colors:
            def _sel_ch(c=ch): self._curve_ch.set(c); self._draw_curve()
            tk.Button(ch_f, text=ch, bg=SEL if ch=="RGB" else CARD, fg=col,
                      relief="flat", font=("Helvetica",9,"bold"), padx=10, pady=3,
                      cursor="hand2", command=_sel_ch).pack(side="left", padx=2)

        # Curve control points (stored per channel)
        self._curves = {
            "RGB": [(0,0),(64,64),(128,128),(192,192),(255,255)],
            "R":   [(0,0),(128,128),(255,255)],
            "G":   [(0,0),(128,128),(255,255)],
            "B":   [(0,0),(128,128),(255,255)],
        }
        self._drag_pt = None
        self._curve_canvas.bind("<Button-1>",      self._curve_click)
        self._curve_canvas.bind("<B1-Motion>",     self._curve_drag)
        self._curve_canvas.bind("<ButtonRelease-1>",self._curve_release)
        self._curve_canvas.bind("<Button-3>",      self._curve_remove)
        self._draw_curve()

        tk.Label(b, text="Left-click to add points · Right-click to remove",
                 bg=WHITE, fg=MUTED, font=("Helvetica",7)).pack(pady=(0,4))

        sep(b).pack(fill="x", padx=12, pady=8)

        # ── Levels ────────────────────────────────────────────────────
        sec_hdr(b, "Levels", bg=WHITE)

        def _level_row(label, var, from_, to, default, color=ACCENT):
            rf = tk.Frame(b, bg=WHITE); rf.pack(fill="x", padx=14, pady=2)
            tk.Label(rf, text=label, bg=WHITE, fg=MUTED,
                     font=("Helvetica",8), width=10, anchor="w").pack(side="left")
            sl = tk.Scale(rf, variable=var, from_=from_, to=to, orient="horizontal",
                          bg=WHITE, troughcolor=BORDER, highlightthickness=0,
                          activebackground=color, length=180,
                          command=lambda v: self._apply_grading())
            sl.pack(side="left")
            tk.Button(rf, text="↺", bg=WHITE, fg=MUTED, relief="flat",
                      font=("Helvetica",10), cursor="hand2",
                      command=lambda v=var, d=default: (v.set(d), self._apply_grading())
                      ).pack(side="left", padx=2)

        self._black_pt  = tk.IntVar(value=0)
        self._white_pt  = tk.IntVar(value=255)
        self._mid_pt    = tk.DoubleVar(value=1.0)
        self._exposure  = tk.DoubleVar(value=1.0)
        self._highlights= tk.DoubleVar(value=1.0)
        self._shadows   = tk.DoubleVar(value=1.0)
        self._temp      = tk.IntVar(value=0)
        self._tint      = tk.IntVar(value=0)
        self._vibrance  = tk.DoubleVar(value=1.0)

        _level_row("Black Point",  self._black_pt,  0,   100,  0,   "#2E3450")
        _level_row("White Point",  self._white_pt,  155, 255,  255, TEXT)
        _level_row("Midtones",     self._mid_pt,    0.2, 2.5,  1.0, MUTED)

        sep(b).pack(fill="x", padx=12, pady=8)
        sec_hdr(b, "Light & Color", bg=WHITE)

        _level_row("Exposure",     self._exposure,  0.1, 3.0,  1.0, WARN)
        _level_row("Highlights",   self._highlights,0.1, 2.0,  1.0, "#FBBF24")
        _level_row("Shadows",      self._shadows,   0.1, 2.0,  1.0, MUTED)
        _level_row("Temp (warm+)", self._temp,     -80,  80,   0,   "#F59E0B")
        _level_row("Tint (green+)",self._tint,     -80,  80,   0,   GREEN)
        _level_row("Vibrance",     self._vibrance,  0.0, 3.0,  1.0, ACCENT)

        sep(b).pack(fill="x", padx=12, pady=8)

        # ── LUT Presets ───────────────────────────────────────────────
        sec_hdr(b, "Look Presets", bg=WHITE)
        presets = [
            ("Cinematic",  {"_exposure":1.1,"_highlights":0.85,"_shadows":1.2,"_temp":-10,"_vibrance":1.3}),
            ("Warm Film",  {"_exposure":1.05,"_temp":30,"_tint":5,"_vibrance":1.2,"_shadows":1.1}),
            ("Cool Fade",  {"_exposure":0.95,"_temp":-25,"_highlights":0.9,"_vibrance":0.9}),
            ("Noir",       {"_temp":-50,"_vibrance":0.1,"_exposure":0.9,"_shadows":0.8}),
            ("Vivid Pop",  {"_vibrance":2.0,"_exposure":1.1,"_highlights":1.1,"_temp":10}),
            ("Matte",      {"_black_pt":20,"_white_pt":220,"_vibrance":0.85,"_exposure":1.05}),
        ]
        pg = tk.Frame(b, bg=WHITE); pg.pack(fill="x", padx=14, pady=4)
        for i, (name, vals) in enumerate(presets):
            def _apply_preset(v=vals):
                for attr, val in v.items():
                    if hasattr(self, attr): getattr(self, attr).set(val)
                self._apply_grading()
            btn = tk.Button(pg, text=name, bg=CARD, fg=MUTED,
                            relief="flat", font=("Helvetica",8), padx=6, pady=5,
                            cursor="hand2", highlightthickness=1,
                            highlightbackground=BORDER, command=_apply_preset)
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
            btn.bind("<Enter>", lambda e, b2=btn: safe_cfg(b2, bg=SEL, fg=ACCENT))
            btn.bind("<Leave>", lambda e, b2=btn: safe_cfg(b2, bg=CARD, fg=MUTED))
            pg.columnconfigure(i%2, weight=1)

        sep(b).pack(fill="x", padx=12, pady=8)

        # Reset button
        def _reset_all():
            self._black_pt.set(0); self._white_pt.set(255); self._mid_pt.set(1.0)
            self._exposure.set(1.0); self._highlights.set(1.0); self._shadows.set(1.0)
            self._temp.set(0); self._tint.set(0); self._vibrance.set(1.0)
            for ch in self._curves:
                n = len(self._curves[ch])
                self._curves[ch] = [(0,0),(128,128),(255,255)] if n<=3 else [(0,0),(64,64),(128,128),(192,192),(255,255)]
            self._draw_curve()
            self._apply_grading()
        mkbtn(b, "↺  Reset All Grading", _reset_all, style="ghost", py=6
              ).pack(fill="x", padx=14, pady=4)

    # ── Curve drawing ─────────────────────────────────────────────────
    def _draw_curve(self):
        cv = self._curve_canvas
        cv.delete("all")
        W, H = 340, 180
        # Grid
        for i in range(1, 4):
            x = int(i * W / 4); y = int(i * H / 4)
            cv.create_line(x, 0, x, H, fill="#1A1D2E", width=1)
            cv.create_line(0, y, W, y, fill="#1A1D2E", width=1)
        # Diagonal reference
        cv.create_line(0, H, W, 0, fill="#252840", width=1, dash=(4,4))

        ch = self._curve_ch.get()
        col_map = {"RGB": TEXT, "R": "#F43F5E", "G": "#22D3A5", "B": "#38BDF8"}
        col = col_map.get(ch, TEXT)
        pts = sorted(self._curves[ch], key=lambda p: p[0])

        # Draw curve as smooth line through points
        if len(pts) >= 2:
            coords = []
            for i in range(len(pts)-1):
                x0,y0 = pts[i]; x1,y1 = pts[i+1]
                for t in range(21):
                    tt = t/20
                    cx = x0 + (x1-x0)*tt
                    cy = y0 + (y1-y0)*tt
                    sx = int(cx / 255 * W)
                    sy = int((1 - cy/255) * H)
                    coords.extend([sx, sy])
            if len(coords) >= 4:
                cv.create_line(*coords, fill=col, width=2, smooth=True)

        # Control points
        for x, y in pts:
            sx = int(x/255 * W); sy = int((1-y/255) * H)
            cv.create_oval(sx-5, sy-5, sx+5, sy+5, fill=col, outline=WHITE, width=1)

    def _canvas_to_curve(self, cx, cy):
        W, H = 340, 180
        return int(cx/W*255), int((1-cy/H)*255)

    def _curve_click(self, e):
        ch = self._curve_ch.get()
        pts = self._curves[ch]
        cx, cy = self._canvas_to_curve(e.x, e.y)
        # Check if near existing point
        for i, (px, py) in enumerate(pts):
            sx = int(px/255*340); sy = int((1-py/255)*180)
            if abs(e.x-sx)<8 and abs(e.y-sy)<8:
                self._drag_pt = i; return
        # Add new point
        cx = max(0, min(255, cx)); cy = max(0, min(255, cy))
        pts.append((cx, cy))
        pts.sort(key=lambda p: p[0])
        self._drag_pt = pts.index((cx, cy))
        self._draw_curve(); self._apply_grading()

    def _curve_drag(self, e):
        if self._drag_pt is None: return
        ch = self._curve_ch.get()
        cx, cy = self._canvas_to_curve(e.x, e.y)
        cx = max(0, min(255, cx)); cy = max(0, min(255, cy))
        pts = self._curves[ch]
        if 0 <= self._drag_pt < len(pts):
            pts[self._drag_pt] = (cx, cy)
            pts.sort(key=lambda p: p[0])
        self._draw_curve(); self._apply_grading()

    def _curve_release(self, e):
        self._drag_pt = None

    def _curve_remove(self, e):
        ch = self._curve_ch.get()
        pts = self._curves[ch]
        for i, (px, py) in enumerate(pts):
            sx = int(px/255*340); sy = int((1-py/255)*180)
            if abs(e.x-sx)<8 and abs(e.y-sy)<8 and len(pts)>2:
                pts.pop(i); break
        self._draw_curve(); self._apply_grading()

    def _apply_grading(self):
        clip = self._get_clip()
        if not clip: return
        # Store grading settings on the clip
        clip.grade = {
            "black_pt":  self._black_pt.get(),
            "white_pt":  self._white_pt.get(),
            "mid_pt":    self._mid_pt.get(),
            "exposure":  self._exposure.get(),
            "highlights":self._highlights.get(),
            "shadows":   self._shadows.get(),
            "temp":      self._temp.get(),
            "tint":      self._tint.get(),
            "vibrance":  self._vibrance.get(),
            "curves":    {k: list(v) for k,v in self._curves.items()},
        }
        self._on_change()


# ══════════════════════════════════════════════════════════════════════
# SCENE DETECTION PANEL
# ══════════════════════════════════════════════════════════════════════
class SceneDetectPanel(SidePanel):
    """AI Scene Detection — auto-splits video clips by scene change."""
    def _build(self):
        b = self._body

        # Header
        hf = tk.Frame(b, bg=WHITE); hf.pack(fill="x", padx=14, pady=(14,4))
        tk.Label(hf, text="Scene Detection", bg=WHITE, fg=TEXT,
                 font=("Helvetica",13,"bold")).pack(anchor="w")
        tk.Label(hf, text="Auto-split videos by scene changes",
                 bg=WHITE, fg=MUTED, font=("Helvetica",9)).pack(anchor="w")

        sep(b).pack(fill="x", padx=12, pady=8)

        # Info card
        info = tk.Frame(b, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        info.pack(fill="x", padx=14, pady=4)
        tk.Label(info, text="🎬  How it works", bg=CARD, fg=ACCENT,
                 font=("Helvetica",9,"bold")).pack(anchor="w", padx=12, pady=(10,2))
        tk.Label(info, text="Analyses frame-by-frame differences to detect\n"
                           "cuts, fades and hard scene transitions. Each\n"
                           "detected scene becomes a separate clip.",
                 bg=CARD, fg=MUTED, font=("Helvetica",8),
                 justify="left").pack(anchor="w", padx=12, pady=(0,10))

        sep(b).pack(fill="x", padx=12, pady=8)
        sec_hdr(b, "Settings", bg=WHITE)

        # Sensitivity slider
        sf = tk.Frame(b, bg=WHITE); sf.pack(fill="x", padx=14, pady=6)
        tk.Label(sf, text="Sensitivity", bg=WHITE, fg=MUTED,
                 font=("Helvetica",8), width=10, anchor="w").pack(side="left")
        self._sens = tk.DoubleVar(value=30.0)
        tk.Scale(sf, variable=self._sens, from_=5, to=80, orient="horizontal",
                 bg=WHITE, troughcolor=BORDER, highlightthickness=0,
                 activebackground=ACCENT, length=180,
                 resolution=1).pack(side="left")

        tk.Label(b, text="Lower = more sensitive (more splits)\nHigher = fewer, bigger scenes",
                 bg=WHITE, fg=MUTED, font=("Helvetica",7), justify="left").pack(padx=14, anchor="w")

        sep(b).pack(fill="x", padx=12, pady=8)
        sec_hdr(b, "Min Scene Length", bg=WHITE)

        mf = tk.Frame(b, bg=WHITE); mf.pack(fill="x", padx=14, pady=6)
        tk.Label(mf, text="Min seconds", bg=WHITE, fg=MUTED,
                 font=("Helvetica",8), width=10, anchor="w").pack(side="left")
        self._min_dur = tk.DoubleVar(value=1.0)
        tk.Scale(mf, variable=self._min_dur, from_=0.5, to=10.0, resolution=0.5,
                 orient="horizontal", bg=WHITE, troughcolor=BORDER,
                 highlightthickness=0, activebackground=ACCENT,
                 length=180).pack(side="left")

        sep(b).pack(fill="x", padx=12, pady=8)

        # Status / results area
        self._status_f = tk.Frame(b, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        self._status_f.pack(fill="x", padx=14, pady=4)
        self._status_lbl = tk.Label(self._status_f, text="Select a video clip then run detection.",
                                     bg=CARD, fg=MUTED, font=("Helvetica",8),
                                     wraplength=330, justify="left")
        self._status_lbl.pack(padx=12, pady=10)

        # Progress bar (hidden until running)
        self._pb_frame = tk.Frame(b, bg=WHITE); self._pb_frame.pack(fill="x", padx=14)
        self._pb_var = tk.IntVar(value=0)
        self._pb = ttk.Progressbar(self._pb_frame, variable=self._pb_var,
                                    maximum=100, style="E.Horizontal.TProgressbar")

        sep(b).pack(fill="x", padx=12, pady=8)

        # Action buttons
        mkbtn(b, "🔍  Detect Scenes", self._run_detect, style="accent", py=8
              ).pack(fill="x", padx=14, pady=4)
        mkbtn(b, "✂  Split into Clips", self._apply_split, style="default", py=6
              ).pack(fill="x", padx=14, pady=2)
        mkbtn(b, "↺  Clear Results", self._clear, style="ghost", py=5
              ).pack(fill="x", padx=14, pady=2)

        self._scenes = []  # list of (start, end) tuples
        self._split_ready = False

    def _set_status(self, msg, col=None):
        safe_cfg(self._status_lbl, text=msg, fg=col or MUTED)

    def _run_detect(self):
        clip = self._get_clip()
        if not clip:
            self._set_status("⚠  No clip selected. Click a clip on the timeline first.", A2)
            return
        if clip.is_image:
            self._set_status("⚠  Scene detection only works on video files.", A2)
            return
        if not MOVIEPY_AVAILABLE or not NUMPY_AVAILABLE:
            self._set_status("⚠  Requires: pip install moviepy numpy", A2)
            return

        self._scenes = []
        self._split_ready = False
        self._set_status("⏳  Analysing video...", WARN)
        self._pb.pack(fill="x", pady=4)
        self._pb_var.set(0)

        threshold = self._sens.get()
        min_dur   = self._min_dur.get()

        def _detect():
            try:
                from moviepy import VideoFileClip as VFC
                vc = VFC(clip.path)
                fps = vc.fps or 24
                duration = vc.duration
                step = max(1, int(fps / 4))  # sample 4x per second
                total_frames = int(duration * fps)

                scenes = []
                prev_frame = None
                scene_start = clip.start_cut
                last_progress = 0

                for frame_idx in range(0, total_frames, step):
                    t = frame_idx / fps
                    if t > duration - 0.1: break
                    frame = vc.get_frame(t)
                    progress = int(frame_idx / total_frames * 100)
                    if progress != last_progress:
                        last_progress = progress
                        self._pb_var.set(progress)

                    if prev_frame is not None:
                        diff = float(np.mean(np.abs(frame.astype(float) - prev_frame.astype(float))))
                        if diff > threshold:
                            seg_dur = t - scene_start
                            if seg_dur >= min_dur:
                                scenes.append((scene_start, t))
                                scene_start = t
                    prev_frame = frame

                # Final scene
                final_end = clip.end_cut if clip.end_cut > 0 else duration
                if final_end - scene_start >= min_dur:
                    scenes.append((scene_start, final_end))

                vc.close()
                self._scenes = scenes
                self._split_ready = True
                self._pb_var.set(100)

                def _done():
                    self._pb.pack_forget()
                    if len(scenes) <= 1:
                        self._set_status(f"✓  No scene changes found above threshold.\n"
                                        f"Try lowering sensitivity.", GREEN)
                    else:
                        self._set_status(f"✓  Found {len(scenes)} scenes!\n\n" +
                                        "\n".join([f"  Scene {i+1}: {s:.1f}s → {e:.1f}s  ({e-s:.1f}s)"
                                                   for i, (s,e) in enumerate(scenes)]), GREEN)
                self._pb_frame.after(0, _done)

            except Exception as ex:
                def _err():
                    self._pb.pack_forget()
                    self._set_status(f"✗  Error: {ex}", A2)
                self._pb_frame.after(0, _err)

        threading.Thread(target=_detect, daemon=True).start()

    def _apply_split(self):
        if not self._split_ready or not self._scenes:
            self._set_status("⚠  Run detection first.", WARN)
            return
        clip = self._get_clip()
        if not clip:
            self._set_status("⚠  Original clip no longer selected.", A2)
            return

        import copy
        new_clips = []
        for start, end in self._scenes:
            nc = copy.deepcopy(clip)
            nc.start_cut = start
            nc.end_cut   = end
            nc.load_thumb()
            new_clips.append(nc)

        # Replace original clip with split clips
        idx = self._proj.clips.index(clip) if clip in self._proj.clips else -1
        if idx >= 0:
            self._proj.clips.pop(idx)
            for i, nc in enumerate(new_clips):
                self._proj.clips.insert(idx + i, nc)
        else:
            self._proj.clips.extend(new_clips)

        self._set_status(f"✓  Split into {len(new_clips)} clips on the timeline!", GREEN)
        self._scenes = []
        self._split_ready = False
        self._on_change()

    def _clear(self):
        self._scenes = []
        self._split_ready = False
        self._pb.pack_forget()
        self._set_status("Select a video clip then run detection.")


# ══════════════════════════════════════════════════════════════════════
# EXPORT ENGINE
# ══════════════════════════════════════════════════════════════════════
class Exporter:
    @staticmethod
    def run(proj, out, progress_cb=None, done_cb=None):
        def _go():
            try:
                if not MOVIEPY_AVAILABLE:
                    raise RuntimeError("MoviePy not installed.\nRun: pip install moviepy")
                w,h=proj.res; fps=proj.fps; segs=[]
                for idx,cd in enumerate(proj.clips):
                    if progress_cb:
                        progress_cb(int(idx/len(proj.clips)*75),
                                    f"Clip {idx+1}/{len(proj.clips)}…")
                    if cd.is_image:
                        base=ImageClip(cd.path).with_duration(cd.trimmed)
                    else:
                        base=VideoFileClip(cd.path).subclipped(cd.start_cut,cd.end_cut)
                    if cd.speed!=1.0 and not cd.is_image:
                        base=base.with_effects([mpy.video.fx.MultiplySpeed(cd.speed)])
                    base=base.resized((w,h))
                    fn,br,co,sa=cd.filter,cd.brightness,cd.contrast,cd.saturation
                    if fn!="None" or br!=1.0 or co!=1.0 or sa!=1.0:
                        base=base.image_transform(
                            lambda f,_fn=fn,_br=br,_co=co,_sa=sa:
                            Exporter._col(f,_fn,_br,_co,_sa))
                    if cd.rotation: base=base.with_effects([mpy.video.fx.Rotate(cd.rotation)])
                    if cd.flip_h:   base=base.with_effects([mpy.video.fx.MirrorX()])
                    if cd.flip_v:   base=base.with_effects([mpy.video.fx.MirrorY()])
                    if cd.green_screen and NUMPY_AVAILABLE:
                        tol=cd.gs_tol
                        def rmg(frame,_t=tol):
                            a=frame.astype(np.int32)
                            mask=(a[:,:,1]-a[:,:,0]>_t)&(a[:,:,1]-a[:,:,2]>_t)
                            frame[mask]=[0,0,0]; return frame
                        base=base.image_transform(rmg)
                    layers=[base]
                    if cd.pip_path and os.path.exists(cd.pip_path):
                        try:
                            pip=VideoFileClip(cd.pip_path)
                            pip=pip.subclipped(0,min(pip.duration,base.duration))
                            pw,ph=int(w*cd.pip_scale),int(h*cd.pip_scale)
                            pip=pip.resized((pw,ph))
                            pos={"top-left":(10,10),"top-right":(w-pw-10,10),
                                 "bottom-left":(10,h-ph-10),"bottom-right":(w-pw-10,h-ph-10),
                                 "center":((w-pw)//2,(h-ph)//2)}
                            pip = pip.with_position(pos.get(cd.pip_pos,(w-pw-10,h-ph-10)))
                            layers.append(pip)
                        except: pass
                    for ov in cd.overlays:
                        try:
                            tc=(TextClip(font="DejaVu-Sans-Bold",text=ov.content,
                                         font_size=ov.size,color=ov.color,
                                         stroke_color="black",stroke_width=1)
                                .with_position((ov.x,ov.y),relative=True)
                                .with_start(ov.start)
                                .with_end(min(ov.end,base.duration))
                                .with_duration(min(ov.end,base.duration)-ov.start))
                            layers.append(tc)
                        except: pass
                    if len(layers)>1:
                        base=CompositeVideoClip(layers,size=(w,h)).with_duration(cd.trimmed)
                    if cd.transition!="None" and idx>0:
                        base=base.with_effects([mpy.video.fx.FadeIn(cd.trans_dur)])
                    segs.append(base)
                if not segs: raise ValueError("No clips.")
                if progress_cb: progress_cb(80,"Joining clips…")
                final=concatenate_videoclips(segs,method="compose")
                if proj.music_path and os.path.exists(proj.music_path):
                    music=AudioFileClip(proj.music_path).with_volume_scaled(proj.music_vol)
                    if music.duration<final.duration:
                        loops=math.ceil(final.duration/music.duration)
                        music=concatenate_audioclips([music]*loops)
                    music=music.subclipped(0,final.duration)
                    if final.audio:
                        from moviepy.audio.AudioClip import CompositeAudioClip
                        final=final.with_audio(CompositeAudioClip([final.audio,music]))
                    else: final=final.with_audio(music)
                if progress_cb: progress_cb(88,"Encoding…")
                _preset = {"Fast":"ultrafast","Balanced":"medium",
                            "High":"slow","Max":"veryslow"}.get(q_var.get(),"medium")
                final.write_videofile(out, fps=fps, codec="libx264",
                                       audio_codec="aac", preset=_preset,
                                       audio_bitrate=ab_var.get(), logger=None)
                for s in segs:
                    try: s.close()
                    except: pass
                final.close()
                if progress_cb: progress_cb(100,"Done!")
                if done_cb: done_cb(True,out)
            except Exception as ex:
                if done_cb: done_cb(False,str(ex))
        threading.Thread(target=_go,daemon=True).start()

    @staticmethod
    def _col(frame,name,br,co,sa):
        if not PIL_AVAILABLE: return frame
        img=Image.fromarray(frame)
        if name!="None": img=pil_filter(img,name)
        img=ImageEnhance.Brightness(img).enhance(br)
        img=ImageEnhance.Contrast(img).enhance(co)
        img=ImageEnhance.Color(img).enhance(sa)
        return np.array(img)


# ══════════════════════════════════════════════════════════════════════
# CREATIVE ARCHITECT PANEL  (AI-powered design analysis via Gemini)
# ══════════════════════════════════════════════════════════════════════
GEMINI_VISION_URL  = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"
GEMINI_IMAGEN_URL  = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"


VIBE_PRESETS = ["Auto-Detect","Minimalist","Corporate","Vibrant","Retro","Dark & Moody","Soft Pastel","Bold & Urban"]
EDIT_ACTIONS = ["Remove Background","Upscale Resolution","Color Grade","Magic Expand","Object Isolation","Portrait Enhance"]

class CreativeArchitectPanel(SidePanel):
    """
    AI-powered design panel with 3 modes:
      1. Analyse & Auto-Apply  — Gemini Vision analyses image, applies suggestions to clip
      2. Prompt Generator      — Gemini writes a ready-to-use prompt for any AI tool
      3. Animation Plan        — Generates a shot-by-shot animation plan (Runway / Kling)
    """

    # ── constants ─────────────────────────────────────────────────────
    # GEMINI_URL is now dynamic — see get_gemini_url()
    VIBES       = ["Auto-Detect","Minimalist","Corporate","Vibrant",
                   "Retro","Dark & Moody","Soft Pastel","Bold & Urban","Cinematic","Neon"]
    EDIT_ACTS   = ["Remove Background","Upscale Resolution","Color Grade",
                   "Magic Expand","Object Isolation","Portrait Enhance"]
    ANIM_STYLES = ["Slow Motion","Zoom In","Ken Burns Pan","Dolly Push",
                   "Parallax Float","Cinematic Drift","Action Burst","Glitch FX"]

    def _build(self):
        b = self._body
        self._img_path   = None
        self._thumb_photo = None
        self._last_result = None
        self._action_vars = {}

        # ── Title ─────────────────────────────────────────────────────
        hf = ctkF(b, bg=WHITE); hf.pack(fill="x", padx=14, pady=(14,4))
        ctkL(hf, text="AI Studio", fg=TEXT,
             font=("Helvetica",15,"bold")).pack(anchor="w")
        provider_name = "OpenAI ChatGPT" if _SETTINGS.get("active_provider","gemini")=="openai" else "Google Gemini"
        lbl(b, f"Powered by {provider_name} · Switch provider in Settings",
            fg=MUTED, font=F["xs"], bg=WHITE, wraplength=320, justify="left"
            ).pack(padx=14, anchor="w")
        sep(b).pack(fill="x", padx=14, pady=8)

        # ── Image Upload — Canva-style drop zone ─────────────────────
        sec_hdr(b, "Source Image", bg=WHITE)
        up_zone = tk.Frame(b, bg=CARD, highlightthickness=2,
                           highlightbackground=BORDER, cursor="hand2")
        up_zone.pack(fill="x", padx=14, pady=4)

        # Canvas for thumbnail display
        self._thumb_cv = tk.Canvas(up_zone, bg=CARD, width=340, height=140,
                                    highlightthickness=0)
        self._thumb_cv.pack(fill="x", pady=4)
        # Default icon
        self._thumb_cv.create_oval(140,30,200,90, fill=SEL, outline=ACCENT, width=2,
                                    tags="icon_circle")
        self._thumb_cv.create_text(170,60, text="📷", font=("Helvetica",22),
                                    fill=ACCENT, tags="icon_text")
        self._thumb_cv.create_text(170,108, text="Click · Drag & Drop · Ctrl+V",
                                    fill=MUTED, font=("Helvetica",9),
                                    tags="hint_text")
        # Keep _thumb_lbl as hidden label (for compat with existing code)
        self._thumb_lbl = tk.Label(up_zone, bg=CARD, text="",
                                    fg=ACCENT, font=("Helvetica",10))
        self._img_name_lbl = tk.Label(up_zone, text="",
                                       fg=GREEN, font=("Helvetica",9,"bold"), bg=CARD)
        self._img_name_lbl.pack(pady=(0,6))

        for w in [up_zone, self._thumb_cv, self._img_name_lbl]:
            w.bind("<Button-1>", lambda e: self._upload_image())
            w.bind("<Enter>", lambda e: safe_cfg(up_zone,highlightbackground=ACCENT))
            w.bind("<Leave>", lambda e: safe_cfg(up_zone,highlightbackground=BORDER))

        sep(b).pack(fill="x", padx=14, pady=8)

        # ── Mode Tabs — 2 rows so all 5 fit ──────────────────────────
        sec_hdr(b, "Select AI Mode", bg=WHITE)
        self._mode_v = tk.StringVar(value="analyse")
        self._mode_frames = {}
        self._mode_btns   = {}

        # Tab container with dark background to make pills pop
        tab_bg = tk.Frame(b, bg=DARK, padx=6, pady=6)
        tab_bg.pack(fill="x", padx=12, pady=(4,8))

        tab_row1 = tk.Frame(tab_bg, bg=DARK)
        tab_row1.pack(fill="x", pady=(0,3))
        tab_row2 = tk.Frame(tab_bg, bg=DARK)
        tab_row2.pack(fill="x")

        self._tab_indicator_cv = tk.Canvas(b, bg=DARK, height=3,
                                            highlightthickness=0)
        self._tab_indicator_cv.pack(fill="x", padx=12, pady=(0,4))
        modes = [
            ("analyse",  "✦ Analyse",    tab_row1),
            ("prompt",   "🖼 Edit",       tab_row1),
            ("animate",  "📋 Plan",       tab_row1),
            ("imagegen", "🎨 Image Gen",  tab_row2),
            ("sora",     "🎬 Sora",       tab_row2),
            ("freetools","🌊 WaveSpeed", tab_row2),
        ]
        for name, label_txt, row in modes:
            is_first = (name == "analyse")
            btn_w = tk.Button(row, text=label_txt, relief="flat", cursor="hand2",
                              bg=ACCENT if is_first else CARD,
                              fg=WHITE if is_first else MUTED,
                              font=("Helvetica",9,"bold" if is_first else "normal"),
                              padx=4, pady=7,
                              activebackground=ACCENT, activeforeground=WHITE,
                              command=lambda n=name: self._switch_mode(n))
            btn_w.pack(side="left", expand=True, fill="x", padx=2)
            self._mode_btns[name] = btn_w

        # Single container — all mode frames live here, stacked via grid
        self._mode_container = tk.Frame(b, bg=WHITE)
        self._mode_container.pack(fill="x", padx=0)
        self._mode_container.columnconfigure(0, weight=1)

        # ── Mode: Analyse & Apply ─────────────────────────────────────
        mf_analyse = tk.Frame(self._mode_container, bg=WHITE)
        mf_analyse.grid(row=0, column=0, sticky="ew")
        self._mode_frames["analyse"] = mf_analyse

        sec_hdr(mf_analyse, "Design Request", bg=WHITE)
        self._analyse_req = tk.Text(mf_analyse, height=4, bg=CARD, fg=TEXT,
                                     insertbackground=TEXT, relief="flat",
                                     font=F["sm"], wrap="word",
                                     highlightthickness=1, highlightbackground=BORDER)
        self._analyse_req.pack(fill="x", padx=14, pady=4)
        self._analyse_req.insert("1.0", "Analyse this image. Suggest the best filter, colour grade, and text overlay layout for a professional social media post.")

        sec_hdr(mf_analyse, "Design Vibe", bg=WHITE)
        vf = tk.Frame(mf_analyse, bg=WHITE); vf.pack(fill="x", padx=14, pady=2)
        self._vibe_v = tk.StringVar(value="Auto-Detect")
        om = tk.OptionMenu(vf, self._vibe_v, *self.VIBES)
        safe_cfg(om,bg=CARD, fg=TEXT, relief="flat", font=F["sm"],
                  highlightthickness=0, activebackground=SEL, width=22)
        om.pack(side="left")

        sec_hdr(mf_analyse, "AI Edit Actions", bg=WHITE)
        af = tk.Frame(mf_analyse, bg=WHITE); af.pack(fill="x", padx=14, pady=2)
        for i, action in enumerate(self.EDIT_ACTS):
            v = tk.BooleanVar(value=i < 3)
            self._action_vars[action] = v
            tk.Checkbutton(af, text=action, variable=v, bg=WHITE,
                           activebackground=WHITE, font=F["sm"], fg=TEXT,
                           selectcolor=SEL, cursor="hand2"
                           ).grid(row=i//2, column=i%2, sticky="w", padx=4, pady=1)
            af.columnconfigure(i%2, weight=1)

        self._analyse_btn = mkbtn(mf_analyse, "✦  Analyse Image",
                                   self._run_analyse, style="dark", px=14, py=8)
        self._analyse_btn.pack(fill="x", padx=14, pady=(8,2))
        mkbtn(mf_analyse, "🔌  Test Connection (no image needed)",
              self._test_connection, style="ghost", px=10, py=5
              ).pack(fill="x", padx=14, pady=(0,4))

        # AI Background Remover
        sep(mf_analyse, bg=BORDER).pack(fill="x", padx=14, pady=4)
        sec_hdr(mf_analyse, "AI Background Remover", bg=WHITE)
        tk.Label(mf_analyse,
                 text="Upload an image above, then click to remove its background using PIL.",
                 bg=WHITE, fg=MUTED, font=F["xs"],
                 wraplength=340, justify="left").pack(padx=14, anchor="w", pady=(0,4))
        self._bg_rm_btn = mkbtn(mf_analyse, "✂  Remove Background",
                                 self._remove_background, style="accent", px=14, py=6)
        self._bg_rm_btn.pack(fill="x", padx=14, pady=2)
        self._bg_rm_canvas = tk.Canvas(mf_analyse, bg="#111827",
                                        highlightthickness=0, width=340, height=180)
        self._bg_rm_canvas.pack(padx=14, pady=4)
        self._bg_rm_canvas.create_text(170, 90,
            text="Background removed image appears here",
            fill=MUTED, font=F["xs"], width=280, justify="center")
        self._bg_rm_photo  = None
        self._bg_rm_result = None
        mkbtn(mf_analyse, "💾  Save Result", self._save_bg_removed,
              style="ghost", px=14, py=4).pack(fill="x", padx=14, pady=2)

        # AI Auto-Caption (Whisper)
        sep(mf_analyse, bg=BORDER).pack(fill="x", padx=14, pady=4)
        sec_hdr(mf_analyse, "AI Auto-Caption (Whisper)", bg=WHITE)
        tk.Label(mf_analyse,
                 text="Select a video clip in the timeline, then generate captions from its audio.",
                 bg=WHITE, fg=MUTED, font=F["xs"],
                 wraplength=340, justify="left").pack(padx=14, anchor="w", pady=(0,4))
        self._caption_btn = mkbtn(mf_analyse, "🎤  Generate Captions",
                                   self._run_autocaption, style="accent", px=14, py=6)
        self._caption_btn.pack(fill="x", padx=14, pady=(2,8))

        # ── Mode: AI Image Editor ─────────────────────────────────────
        mf_prompt = tk.Frame(self._mode_container, bg=WHITE)
        mf_prompt.grid(row=0, column=0, sticky="ew")
        self._mode_frames["prompt"] = mf_prompt

        # Green banner
        banner = tk.Frame(mf_prompt, bg="#065F46"); banner.pack(fill="x", padx=14, pady=(8,4))
        tk.Label(banner, text="🖼  AI Image Editor — Powered by OpenAI",
                 bg="#065F46", fg="white", font=F["sm"], pady=6, padx=10).pack(side="left")

        sec_hdr(mf_prompt, "What do you want to do to this image?", bg=WHITE)
        tk.Label(mf_prompt,
                 text="Examples: Make bg a sunset, Add dramatic lighting, Remove background, Comic book style",
                 bg=WHITE, fg=MUTED, font=F["xs"],
                 wraplength=340, justify="left").pack(padx=14, anchor="w", pady=(0,4))

        self._edit_req = tk.Text(mf_prompt, height=4, bg=CARD, fg=TEXT,
                                  insertbackground=TEXT, relief="flat",
                                  font=F["sm"], wrap="word",
                                  highlightthickness=1, highlightbackground=BORDER)
        self._edit_req.pack(fill="x", padx=14, pady=4)
        self._edit_req.insert("1.0", "Make the background a dramatic sunset sky with deep orange and purple colors")

        sec_hdr(mf_prompt, "Image Size", bg=WHITE)
        sz_row = tk.Frame(mf_prompt, bg=WHITE); sz_row.pack(fill="x", padx=14, pady=2)
        self._edit_size_v = tk.StringVar(value="1024x1024")
        for sz in ["1024x1024", "1024x1792", "1792x1024"]:
            tk.Radiobutton(sz_row, text=sz, variable=self._edit_size_v, value=sz,
                           bg=WHITE, fg=TEXT, font=F["xs"],
                           selectcolor=SEL, cursor="hand2",
                           activebackground=WHITE).pack(side="left", padx=6)

        self._prompt_btn = mkbtn(mf_prompt, "🖼  Generate Edited Image",
                                  self._run_prompt, style="green", px=14, py=8)
        self._prompt_btn.pack(fill="x", padx=14, pady=8)

        # Result preview inside the editor tab
        sec_hdr(mf_prompt, "Generated Image", bg=WHITE)
        self._edit_canvas = tk.Canvas(mf_prompt, bg="#111827",
                                       highlightthickness=0, width=340, height=220)
        self._edit_canvas.pack(padx=14, pady=4)
        self._edit_canvas.create_text(170, 110,
            text="Generated image will appear here",
            fill=MUTED, font=F["xs"], width=280, justify="center")
        self._edit_photo = None
        self._edit_pil_img = None

        self._edit_save_btn = mkbtn(mf_prompt, "💾  Save Generated Image",
                                     self._save_edit_image,
                                     style="accent", px=14, py=6)
        self._edit_save_btn.pack(fill="x", padx=14, pady=4)
        safe_cfg(self._edit_save_btn,state="disabled")
        self._edit_add_btn = mkbtn(mf_prompt, "➕  Add to Timeline",
                                     self._add_edit_image_to_timeline,
                                     style="ghost", px=14, py=6)
        self._edit_add_btn.pack(fill="x", padx=14, pady=(0,4))
        safe_cfg(self._edit_add_btn, state="disabled")

        # ── Mode: Animation Planner ───────────────────────────────────
        mf_anim = tk.Frame(self._mode_container, bg=WHITE)
        mf_anim.grid(row=0, column=0, sticky="ew")
        self._mode_frames["animate"] = mf_anim

        sec_hdr(mf_anim, "What should move?", bg=WHITE)
        self._anim_req = tk.Text(mf_anim, height=4, bg=CARD, fg=TEXT,
                                  insertbackground=TEXT, relief="flat",
                                  font=F["sm"], wrap="word",
                                  highlightthickness=1, highlightbackground=BORDER)
        self._anim_req.pack(fill="x", padx=14, pady=4)
        self._anim_req.insert("1.0", "Make the wrestler burst forward with slow-motion energy, dramatic lighting, and sparks flying.")

        sec_hdr(mf_anim, "Animation Style", bg=WHITE)
        as_f = tk.Frame(mf_anim, bg=WHITE); as_f.pack(fill="x", padx=14, pady=4)
        self._anim_style_v = tk.StringVar(value="Slow Motion")
        for i, style in enumerate(self.ANIM_STYLES):
            sel = style == "Slow Motion"
            btn_a = tk.Button(as_f, text=style,
                              bg=ACCENT if sel else CARD,
                              fg=WHITE if sel else TEXT,
                              relief="flat", font=F["xs"], padx=5, pady=3,
                              cursor="hand2",
                              command=lambda s=style: self._set_anim_style(s))
            btn_a.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
            as_f.columnconfigure(i%2, weight=1)

        sec_hdr(mf_anim, "Target Platform", bg=WHITE)
        plat_f = tk.Frame(mf_anim, bg=WHITE); plat_f.pack(fill="x", padx=14, pady=2)
        self._platform_v = tk.StringVar(value="Runway ML Gen-3")
        for plat in ["Runway ML Gen-3","Kling AI","Pika Labs","Luma Dream Machine","Sora"]:
            tk.Radiobutton(plat_f, text=plat, variable=self._platform_v, value=plat,
                           bg=WHITE, fg=TEXT, font=F["xs"], selectcolor=SEL,
                           activebackground=WHITE, cursor="hand2"
                           ).pack(anchor="w", padx=4)

        self._anim_btn = mkbtn(mf_anim, "🎬  Generate Animation Plan",
                                self._run_animate, style="dark", px=14, py=8)
        self._anim_btn.pack(fill="x", padx=14, pady=8)

        # ── Mode: AI Image Generator (Hugging Face) ──────────────────
        mf_imagegen = tk.Frame(self._mode_container, bg=WHITE)
        mf_imagegen.grid(row=0, column=0, sticky="ew")
        self._mode_frames["imagegen"] = mf_imagegen

        # HF banner
        hf_banner = tk.Frame(mf_imagegen, bg="#2D6A4F",
                             highlightthickness=0)
        hf_banner.pack(fill="x", padx=14, pady=(8,4))
        tk.Label(hf_banner,
                 text="🤗  Hugging Face — 100% Free Image Generation",
                 bg="#2D6A4F", fg="white", font=F["sm"],
                 pady=6, padx=10).pack(side="left")
        tk.Label(hf_banner,
                 text="No billing ever",
                 bg="#2D6A4F", fg="#95D5B2", font=F["xs"],
                 pady=6, padx=6).pack(side="right")

        # prompt input
        sec_hdr(mf_imagegen, "Image Prompt", bg=WHITE)
        self._hf_prompt = tk.Text(mf_imagegen, height=4, bg=CARD, fg=TEXT,
                                   insertbackground=TEXT, relief="flat",
                                   font=F["sm"], wrap="word",
                                   highlightthickness=1, highlightbackground=BORDER)
        self._hf_prompt.pack(fill="x", padx=14, pady=4)
        self._hf_prompt.insert("1.0",
            "A professional product photo of a sleek smartphone on a white marble surface, "
            "studio lighting, sharp focus, commercial photography style")

        # negative prompt
        sec_hdr(mf_imagegen, "Negative Prompt (what to avoid)", bg=WHITE)
        self._hf_neg = tk.Text(mf_imagegen, height=2, bg=CARD, fg=TEXT,
                                insertbackground=TEXT, relief="flat",
                                font=F["sm"], wrap="word",
                                highlightthickness=1, highlightbackground=BORDER)
        self._hf_neg.pack(fill="x", padx=14, pady=4)
        self._hf_neg.insert("1.0", "blurry, low quality, distorted, watermark, text")

        # style presets
        sec_hdr(mf_imagegen, "Style Preset", bg=WHITE)
        self._hf_style_v = tk.StringVar(value="None")
        HF_STYLES = ["None","Photorealistic","Cinematic","Digital Art","Oil Painting",
                     "Watercolor","Anime","Sketch","3D Render","Vintage","Neon","Fantasy"]
        sf_row = tk.Frame(mf_imagegen, bg=WHITE); sf_row.pack(fill="x", padx=14, pady=2)
        for i, style in enumerate(HF_STYLES):
            tk.Button(sf_row, text=style,
                      bg=ACCENT if style == "None" else CARD,
                      fg=WHITE if style == "None" else TEXT,
                      relief="flat", font=F["xs"], padx=4, pady=3, cursor="hand2",
                      command=lambda s=style: self._set_hf_style(s)
                      ).grid(row=i//4, column=i%4, padx=1, pady=1, sticky="ew")
            sf_row.columnconfigure(i%4, weight=1)
        self._hf_style_btns_frame = sf_row

        # image size
        sec_hdr(mf_imagegen, "Image Size", bg=WHITE)
        sz_row = tk.Frame(mf_imagegen, bg=WHITE); sz_row.pack(fill="x", padx=14, pady=2)
        self._hf_size_v = tk.StringVar(value="512x512")
        for sz in ["512x512","768x768","1024x1024","512x768","768x512"]:
            tk.Radiobutton(sz_row, text=sz, variable=self._hf_size_v, value=sz,
                           bg=WHITE, fg=TEXT, font=F["xs"],
                           selectcolor=SEL, cursor="hand2",
                           activebackground=WHITE).pack(side="left", padx=4)

        # num images
        ni_row = tk.Frame(mf_imagegen, bg=WHITE); ni_row.pack(fill="x", padx=14, pady=4)
        tk.Label(ni_row, text="Number of images:", bg=WHITE, fg=MUTED, font=F["sm"]).pack(side="left")
        self._hf_num_v = tk.IntVar(value=1)
        tk.Spinbox(ni_row, from_=1, to=4, textvariable=self._hf_num_v,
                   bg=CARD, fg=TEXT, relief="flat", width=4, font=F["sm"]).pack(side="left", padx=6)
        tk.Label(ni_row, text="(more = slower, uses more quota)",
                 bg=WHITE, fg=MUTED, font=F["xs"]).pack(side="left")

        # generate button
        self._hf_gen_btn = mkbtn(mf_imagegen, "🎨  Generate Image",
                                  self._run_hf_imagegen, style="green", px=14, py=8)
        self._hf_gen_btn.pack(fill="x", padx=14, pady=6)

        # generated image display
        self._hf_img_frame = tk.Frame(mf_imagegen, bg=CARD,
                                       highlightthickness=1, highlightbackground=BORDER)
        self._hf_img_frame.pack(fill="x", padx=14, pady=4)
        self._hf_img_lbl = tk.Label(self._hf_img_frame,
                                     text="Generated image will appear here",
                                     bg=CARD, fg=MUTED, font=F["sm"],
                                     pady=40)
        self._hf_img_lbl.pack()
        self._hf_photo_refs = []  # keep refs to avoid GC

        # save button
        self._hf_save_btn = mkbtn(mf_imagegen, "💾  Save Generated Image",
                                   self._save_hf_image,
                                   style="accent", px=14, py=6)
        self._hf_save_btn.pack(fill="x", padx=14, pady=4)
        safe_cfg(self._hf_save_btn,state="disabled")
        self._hf_add_btn = mkbtn(mf_imagegen, "➕  Add to Timeline",
                                   self._add_imagegen_to_timeline,
                                   style="ghost", px=14, py=5)
        self._hf_add_btn.pack(fill="x", padx=14, pady=(0,4))
        safe_cfg(self._hf_add_btn, state="disabled")
        self._hf_generated_imgs = []  # stores PIL images

        tk.Label(mf_imagegen,
                 text="💡 Get your free key at huggingface.co/settings/tokens → New Token → Read",
                 bg=WHITE, fg=MUTED, font=F["xs"],
                 wraplength=320, justify="left").pack(padx=14, anchor="w", pady=4)

        # ── Mode: Sora Video Generator ───────────────────────────────
        mf_sora = tk.Frame(self._mode_container, bg=WHITE)
        mf_sora.grid(row=0, column=0, sticky="ew")
        self._mode_frames["sora"] = mf_sora

        # Sora banner
        if CTK_AVAILABLE:
            sora_banner = ctk.CTkFrame(mf_sora, fg_color="#000000",
                                        corner_radius=4)
            sora_banner.pack(fill="x", padx=14, pady=(8,4))
            ctk.CTkLabel(sora_banner, text="🎬  Sora 2 — OpenAI Video Generation",
                         text_color="#FFFFFF", fg_color="transparent",
                         font=ctk.CTkFont(size=11,weight="bold")).pack(
                         side="left", padx=10, pady=8)
            ctk.CTkLabel(sora_banner, text="Uses your OpenAI key",
                         text_color="#888888", fg_color="transparent",
                         font=ctk.CTkFont(size=9)).pack(side="right",padx=8)
        else:
            sora_banner = tk.Frame(mf_sora, bg="#000000")
            sora_banner.pack(fill="x", padx=14, pady=(8,4))
            tk.Label(sora_banner, text="🎬  Sora 2 — OpenAI Video Generation",
                     bg="#000000", fg="#FFFFFF", font=F["sm"],
                     pady=7, padx=10).pack(side="left")
            tk.Label(sora_banner, text="Uses your OpenAI key",
                     bg="#000000", fg=MUTED, font=F["xs"],
                     pady=7, padx=6).pack(side="right")

        sec_hdr(mf_sora, "Video Prompt", bg=WHITE)
        tk.Label(mf_sora,
                 text="Describe your video: shot type, subject, action, setting, lighting.",
                 bg=WHITE, fg=MUTED, font=F["xs"],
                 wraplength=340, justify="left").pack(padx=14, anchor="w", pady=(0,2))
        self._sora_prompt = tk.Text(mf_sora, height=5, bg=CARD, fg=TEXT,
                                     insertbackground=TEXT, relief="flat",
                                     font=F["sm"], wrap="word",
                                     highlightthickness=1, highlightbackground=BORDER)
        self._sora_prompt.pack(fill="x", padx=14, pady=4)
        self._sora_prompt.insert("1.0",
            "Wide shot of a lone wolf standing on a snowy mountain peak at sunrise, "
            "dramatic golden light, cinematic slow motion, epic fantasy atmosphere")

        sec_hdr(mf_sora, "Model", bg=WHITE)
        sora_model_f = tk.Frame(mf_sora, bg=WHITE)
        sora_model_f.pack(fill="x", padx=14, pady=2)
        self._sora_model_v = tk.StringVar(value="sora-2")
        for model, desc in [("sora-2", "sora-2  (Fast, good quality)"),
                             ("sora-2-pro", "sora-2-pro  (Slower, best quality, 1080p)")]:
            tk.Radiobutton(sora_model_f, text=desc, variable=self._sora_model_v,
                           value=model, bg=WHITE, fg=TEXT, font=F["xs"],
                           selectcolor=SEL, cursor="hand2",
                           activebackground=WHITE).pack(anchor="w", padx=4, pady=1)

        sec_hdr(mf_sora, "Resolution", bg=WHITE)
        sora_res_f = tk.Frame(mf_sora, bg=WHITE)
        sora_res_f.pack(fill="x", padx=14, pady=2)
        self._sora_res_v = tk.StringVar(value="720p")
        for res in ["480p","720p","1080p"]:
            tk.Radiobutton(sora_res_f, text=res, variable=self._sora_res_v,
                           value=res, bg=WHITE, fg=TEXT, font=F["xs"],
                           selectcolor=SEL, cursor="hand2",
                           activebackground=WHITE).pack(side="left", padx=8)
        tk.Label(sora_res_f, text="(1080p = sora-2-pro only)",
                 bg=WHITE, fg=MUTED, font=F["xs"]).pack(side="left")

        sec_hdr(mf_sora, "Duration", bg=WHITE)
        sora_dur_f = tk.Frame(mf_sora, bg=WHITE)
        sora_dur_f.pack(fill="x", padx=14, pady=2)
        self._sora_dur_v = tk.StringVar(value="4")
        for dur in ["4","8","12"]:
            tk.Radiobutton(sora_dur_f, text=f"{dur}s", variable=self._sora_dur_v,
                           value=dur, bg=WHITE, fg=TEXT, font=F["xs"],
                           selectcolor=SEL, cursor="hand2",
                           activebackground=WHITE).pack(side="left", padx=6)

        self._sora_gen_btn = mkbtn(mf_sora, "🎬  Generate Video with Sora",
                                    self._run_sora, style="dark", px=14, py=8)
        self._sora_gen_btn.pack(fill="x", padx=14, pady=8)

        # Progress area
        self._sora_progress_lbl = tk.Label(mf_sora, text="",
            bg=WHITE, fg=MUTED, font=F["xs"], wraplength=340, justify="left")
        self._sora_progress_lbl.pack(padx=14, anchor="w")

        self._sora_progress_bar = ttk.Progressbar(mf_sora, mode="determinate",
                                                    maximum=100, value=0,
                                                    length=340,
                                                    style="E.Horizontal.TProgressbar")
        self._sora_progress_bar.pack(padx=14, pady=4)

        # Result display
        self._sora_result_lbl = tk.Label(mf_sora,
            text="Generated video will be saved to your chosen location.",
            bg=CARD, fg=MUTED, font=F["xs"],
            wraplength=340, justify="left", pady=8, padx=8)
        self._sora_result_lbl.pack(fill="x", padx=14, pady=4)

        self._sora_save_btn = mkbtn(mf_sora, "💾  Save Video to Disk",
                                     self._save_sora_video,
                                     style="accent", px=14, py=6)
        self._sora_save_btn.pack(fill="x", padx=14, pady=4)
        safe_cfg(self._sora_save_btn, state="disabled")
        self._sora_add_btn = mkbtn(mf_sora, "➕  Add Video to Timeline",
                                    self._add_sora_to_timeline,
                                    style="ghost", px=14, py=5)
        self._sora_add_btn.pack(fill="x", padx=14, pady=(0,4))
        safe_cfg(self._sora_add_btn, state="disabled")

        self._sora_reset_btn = mkbtn(mf_sora, "🔄  New Video — Reset Form",
                                      self._reset_sora,
                                      style="ghost", px=14, py=6)
        self._sora_reset_btn.pack(fill="x", padx=14, pady=(0,4))
        safe_cfg(self._sora_reset_btn, state="disabled")
        self._sora_video_bytes = None  # stores raw MP4 bytes

        tk.Label(mf_sora,
                 text="Sora costs approx $0.03-0.15/sec. A 10s 720p video is ~$0.30. "
                      "Generation takes 1-5 minutes. Requires OpenAI API key.",
                 bg="#FFF8E1", fg="#795548", font=F["xs"],
                 wraplength=340, justify="left", pady=6, padx=8).pack(
                     fill="x", padx=14, pady=4)



        # ══════════════════════════════════════════════════════════════
        # MODE: FREE VIDEO TOOLS (Clipboard + Browser launch)
        # ══════════════════════════════════════════════════════════════
        mf_free = tk.Frame(self._mode_container, bg=WHITE)
        mf_free.grid(row=0, column=0, sticky="ew")
        self._mode_frames["freetools"] = mf_free

        # Header
        fhdr = tk.Frame(mf_free, bg="#0A0A1E", height=52)
        fhdr.pack(fill="x", padx=14, pady=(8,4)); fhdr.pack_propagate(False)
        tk.Frame(fhdr, bg="#00C6FF", width=3).pack(side="left", fill="y")
        tk.Label(fhdr, text="  🌊  WaveSpeed.ai — AI Video Generation",
                 bg="#0A0A1E", fg="#EDE9FE",
                 font=("Helvetica",11,"bold")).pack(side="left", pady=14)
        tk.Label(fhdr, text="$1 free on signup",
                 bg="#0A0A1E", fg="#00C6FF",
                 font=("Helvetica",8)).pack(side="right", padx=10)

        # API Key
        sec_hdr(mf_free, "WaveSpeed API Key", bg=WHITE)
        ws_key_f = tk.Frame(mf_free, bg=WHITE)
        ws_key_f.pack(fill="x", padx=14, pady=4)
        self._ws_key_v = tk.StringVar(value=_SETTINGS.get("wavespeed_api_key",""))
        tk.Entry(ws_key_f, textvariable=self._ws_key_v, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=F["sm"],
                 show="*", width=28).pack(side="left", fill="x", expand=True)
        def _save_ws_key():
            _SETTINGS["wavespeed_api_key"] = self._ws_key_v.get().strip()
            _save_config()
            Toast.show(self.winfo_toplevel(), "WaveSpeed key saved!", "success")
        mkbtn(ws_key_f, "Save", _save_ws_key,
              style="accent", py=4, px=8).pack(side="left", padx=4)
        tk.Label(mf_free,
                 text="Sign up free at wavespeed.ai — $1 credit included, no tax ID needed",
                 bg=WHITE, fg=MUTED, font=F["xs"]).pack(padx=14, anchor="w")

        # Model selection
        sec_hdr(mf_free, "Video Model", bg=WHITE)
        self._ws_model_v = tk.StringVar(value="wan21_480")
        ws_models = [
            ("wan21_480", "⚡ Wan 2.1 480p",      "wavespeed-ai/wan-2.1/t2v-480p",            "Cheapest — trial friendly"),
            ("wan21_480f","🚀 Wan 2.1 480p Fast", "wavespeed-ai/wan-2.1/t2v-480p-ultra-fast", "Fastest option"),
            ("wan21_720", "🎬 Wan 2.1 720p",      "wavespeed-ai/wan-2.1/t2v-720p",            "Better quality"),
            ("wan22_720", "🏆 Wan 2.2 720p",      "wavespeed-ai/wan-2.2/t2v-720p",            "Latest model"),
        ]
        self._ws_model_ids = {r[0]: r[2] for r in ws_models}
        for mid, name, _, desc in ws_models:
            rf2 = tk.Frame(mf_free, bg=WHITE); rf2.pack(fill="x", padx=14, pady=2)
            tk.Radiobutton(rf2, text=name, variable=self._ws_model_v, value=mid,
                           bg=WHITE, fg=TEXT, activebackground=WHITE,
                           selectcolor=SEL, font=("Helvetica",10,"bold")).pack(side="left")
            tk.Label(rf2, text=desc, bg=WHITE, fg=MUTED,
                     font=("Helvetica",8)).pack(side="left", padx=6)

        # Prompt
        sec_hdr(mf_free, "Video Prompt", bg=WHITE)
        self._ws_prompt = tk.Text(mf_free, height=4, bg=CARD, fg=TEXT,
                                   insertbackground=TEXT, relief="flat",
                                   font=F["sm"], wrap="word", padx=8, pady=6)
        self._ws_prompt.pack(fill="x", padx=14, pady=4)
        self._ws_prompt.insert("1.0",
            "Cinematic slow motion shot of a wrestler performing a powerful move, "
            "dramatic stadium lighting, crowd roaring, epic atmosphere")

        # Duration
        sec_hdr(mf_free, "Duration", bg=WHITE)
        ws_dur_f = tk.Frame(mf_free, bg=WHITE); ws_dur_f.pack(fill="x", padx=14, pady=4)
        self._ws_dur_v = tk.StringVar(value="5")
        ws_dur_note = tk.Label(ws_dur_f, text="(Wan 2.2 supports 5s or 8s only)",
                               bg=WHITE, fg=MUTED, font=("Helvetica",7))
        for d in ["5","8"]:
            tk.Radiobutton(ws_dur_f, text=f"{d}s", variable=self._ws_dur_v,
                           value=d, bg=WHITE, fg=TEXT, activebackground=WHITE,
                           selectcolor=SEL, font=F["sm"]).pack(side="left", padx=6)
        ws_dur_note.pack(side="left", padx=4)

        # Progress
        self._ws_progress_lbl = tk.Label(mf_free, text="", bg=WHITE,
                                          fg=MUTED, font=F["xs"], wraplength=340)
        self._ws_progress_lbl.pack(padx=14, anchor="w", pady=2)
        self._ws_progress_bar = ttk.Progressbar(mf_free, mode="determinate",
                                                  maximum=100, value=0, length=340,
                                                  style="E.Horizontal.TProgressbar")
        self._ws_progress_bar.pack(padx=14, pady=4)
        self._ws_result_lbl = tk.Label(mf_free, text="", bg=WHITE,
                                        fg=GREEN, font=F["xs"], wraplength=340)
        self._ws_result_lbl.pack(padx=14, anchor="w", pady=2)

        # Buttons
        # Test button to find working model URL
        def _test_connection():
            key = _SETTINGS.get("wavespeed_api_key","").strip()
            if not key:
                Toast.show(self.winfo_toplevel(), "Save your API key first!", "warn"); return
            import threading as _t, urllib.request as _ur, json as _j
            safe_cfg(self._ws_progress_lbl, text="⏳ Testing model URLs…", fg=WARN)
            def _go():
                urls_to_test = [
                    "wavespeed-ai/wan-2.1/t2v-480p",
                    "wavespeed-ai/wan-2-1/t2v-480p",
                    "wan-2.1/t2v-480p",
                ]
                hdrs = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                payload = _j.dumps({"prompt":"test","size":"832*480","duration":5,"seed":-1}).encode()
                for uid in urls_to_test:
                    try:
                        url = f"https://api.wavespeed.ai/api/v3/{uid}"
                        req = _ur.Request(url, data=payload, headers=hdrs, method="POST")
                        with _ur.urlopen(req, timeout=10) as r:
                            resp = _j.loads(r.read().decode())
                        msg = f"✅ WORKS: {uid} → {resp}"
                        self.after(0, lambda m=msg: safe_cfg(self._ws_progress_lbl, text=m[:160], fg=GREEN))
                        return
                    except _ur.HTTPError as e:
                        body = e.read().decode()[:80]
                        msg = f"❌ {uid}: HTTP {e.code} {body}"
                        self.after(0, lambda m=msg: safe_cfg(self._ws_progress_lbl, text=m[:160], fg=A2))
                    except Exception as ex:
                        self.after(0, lambda m=str(ex)[:80]: safe_cfg(self._ws_progress_lbl, text=m, fg=A2))
            _t.Thread(target=_go, daemon=True).start()
        mkbtn(mf_free, "🔍 Test Connection", _test_connection,
              style="ghost", px=14, py=5).pack(fill="x", padx=14, pady=(0,4))

        self._ws_gen_btn = mkbtn(mf_free, "🌊  Generate Video",
                                  self._run_wavespeed, style="accent", px=14, py=8)
        self._ws_gen_btn.pack(fill="x", padx=14, pady=8)
        self._ws_save_btn = mkbtn(mf_free, "💾  Save Video to Disk",
                                   self._save_ws_video, style="accent", px=14, py=6)
        self._ws_save_btn.pack(fill="x", padx=14, pady=4)
        safe_cfg(self._ws_save_btn, state="disabled")
        self._ws_add_btn = mkbtn(mf_free, "➕  Add Video to Timeline",
                                  self._add_ws_video_to_timeline,
                                  style="ghost", px=14, py=5)
        self._ws_add_btn.pack(fill="x", padx=14, pady=(0,4))
        safe_cfg(self._ws_add_btn, state="disabled")
        self._ws_reset_btn = mkbtn(mf_free, "🔄  New Video — Reset Form",
                                    self._reset_wavespeed, style="ghost", px=14, py=6)
        self._ws_reset_btn.pack(fill="x", padx=14, pady=(0,4))
        safe_cfg(self._ws_reset_btn, state="disabled")
        self._ws_video_bytes = None

        tk.Label(mf_free,
                 text="💡 IMPORTANT: Go to wavespeed.ai/top-up and add your $1 "
                      "free credit to activate your API key and unlock video models. "
                      "Wan 2.2 Ultra Fast = $0.01/sec — a 5s video costs $0.05.",
                 bg="#E3F2FD", fg="#1565C0", font=F["xs"],
                 wraplength=340, justify="left", pady=6, padx=8
                 ).pack(fill="x", padx=14, pady=4)

        # ── Shared: Status + Results ──────────────────────────────────
        sep(b).pack(fill="x", padx=14, pady=6)
        # Quota tip banner
        tip_frame = tk.Frame(b, bg="#FFF8E1",
                             highlightthickness=1, highlightbackground="#FFD54F")
        tip_frame.pack(fill="x", padx=14, pady=4)
        tk.Label(tip_frame,
                 text="⚡ Quota tip: Use gemini-2.0-flash-lite (Settings) for the "
                      "highest free quota. For OpenAI use gpt-4o-mini. "
                      "Click Test Connection first to verify your key works.",
                 bg="#FFF8E1", fg="#795548", font=F["xs"],
                 wraplength=320, justify="left", pady=6, padx=8).pack(anchor="w")

        self._status_lbl = lbl(b, "Ready — upload an image and run analysis",
                                fg=MUTED, font=F["xs"], bg=WHITE, wraplength=320, justify="left")
        self._status_lbl.pack(padx=14, anchor="w", pady=2)

        # ── AI Edited Image Preview ───────────────────────────────────
        sec_hdr(b, "AI Edited Preview", bg=WHITE)
        self._ai_preview_frame = tk.Frame(b, bg="#111827",
                                           highlightthickness=1,
                                           highlightbackground=BORDER)
        self._ai_preview_frame.pack(fill="x", padx=14, pady=4)
        # Use Canvas — far more reliable than Label for image display
        self._ai_canvas = tk.Canvas(self._ai_preview_frame,
                                     bg="#111827", highlightthickness=0,
                                     width=340, height=220)
        self._ai_canvas.pack()
        self._ai_canvas.create_text(170, 110,
            text="Edited image will appear here after analysis",
            fill=MUTED, font=F["xs"], width=280, justify="center")
        self._ai_preview_photo = None  # keep ref — MUST stay on self

        # save edited image button
        self._save_edit_btn = mkbtn(b, "💾  Save Edited Image",
                                     self._save_edited_image,
                                     style="green", px=14, py=7)
        self._save_edit_btn.pack(fill="x", padx=14, pady=4)
        safe_cfg(self._save_edit_btn,state="disabled")
        self._edited_pil_img = None  # stores the PIL-edited image

        # ── Analysis Results ──────────────────────────────────────────
        sec_hdr(b, "Analysis Results", bg=WHITE)
        self._result_card = tk.Frame(b, bg=CARD, highlightthickness=1,
                                      highlightbackground=BORDER)
        self._result_card.pack(fill="x", padx=14, pady=4)
        self._result_lbl = lbl(self._result_card, "Run an analysis to see results here.",
                                fg=MUTED, font=F["xs"], bg=CARD,
                                wraplength=340, justify="left", pady=8, padx=8)
        self._result_lbl.pack(fill="x")

        # editing steps list
        self._steps_frame = tk.Frame(b, bg=WHITE)
        self._steps_frame.pack(fill="x", padx=14)

        # output text box
        lbl(b, "Full AI Response / JSON", font=F["h3"], fg=ACCENT, bg=WHITE
            ).pack(padx=14, anchor="w", pady=(10,2))
        self._out_text = tk.Text(b, height=10, bg="#1A1A2E", fg="#00FF88",
                                  insertbackground=WHITE, relief="flat",
                                  font=("Courier", 8), wrap="word",
                                  highlightthickness=1, highlightbackground=BORDER)
        self._out_text.pack(fill="x", padx=14, pady=2)
        self._out_text.insert("1.0", "Results will appear here after analysis…")
        safe_cfg(self._out_text,state="disabled")

        # action buttons
        btn_row = tk.Frame(b, bg=WHITE); btn_row.pack(fill="x", padx=14, pady=6)
        mkbtn(btn_row, "📋 Copy", self._copy_output,
              py=5, px=8).pack(side="left", padx=(0,3))
        mkbtn(btn_row, "🗑 Clear", self._clear_results,
              style="ghost", py=5, px=6).pack(side="left", padx=3)

        # show first mode
        self._switch_mode("analyse")

    # ── mode switching ────────────────────────────────────────────────
    def _switch_mode(self, name):
        self._mode_v.set(name)
        for n, f in self._mode_frames.items():
            if n == name:
                f.grid()          # show — restores to grid position
            else:
                f.grid_remove()   # hide — remembers grid options
        for n, b in self._mode_btns.items():
            on = (n == name)
            safe_cfg(b,
                bg=ACCENT if on else CARD,
                fg=WHITE if on else MUTED,
                font=("Helvetica",9,"bold" if on else "normal"))
        try:
            if hasattr(self, "_tab_indicator_cv"):
                cv = self._tab_indicator_cv
                btn = self._mode_btns.get(name)
                if btn:
                    btn.update_idletasks()
                    x = btn.winfo_x()
                    w = btn.winfo_width()
                    cv.delete("indicator")
                    cv.create_rectangle(x, 0, x+w, 3,
                                        fill=ACCENT, outline="",
                                        tags="indicator")
        except Exception: pass
        # Force scroll region update
        try:
            self._mode_container.update_idletasks()
            canvas = self._mode_container.master
            while canvas and not isinstance(canvas, tk.Canvas):
                canvas = canvas.master
            if canvas and isinstance(canvas, tk.Canvas):
                canvas.configure(scrollregion=canvas.bbox("all"))
        except Exception: pass
        # Animate sliding tab indicator
        try:
            if hasattr(self, "_tab_indicator_cv"):
                cv = self._tab_indicator_cv
                btn = self._mode_btns.get(name)
                if btn:
                    btn.update_idletasks()
                    x = btn.winfo_x()
                    w = btn.winfo_width()
                    cv.delete("indicator")
                    cv.create_rectangle(x, 0, x+w, 3,
                                        fill=ACCENT, outline="",
                                        tags="indicator")
        except Exception: pass

    def _set_anim_style(self, style):
        self._anim_style_v.set(style)
        # rebuild animation style buttons to reflect selection
        for w in self._mode_frames["animate"].winfo_children():
            if isinstance(w, tk.Frame):
                for btn_w in w.winfo_children():
                    if isinstance(btn_w, tk.Button):
                        sel = btn_w.cget("text") == style
                        safe_cfg(btn_w,bg=ACCENT if sel else CARD,
                                     fg=WHITE if sel else TEXT)

    # ── shared helpers ────────────────────────────────────────────────
    def _show_thumb(self, path):
        """Draw image thumbnail onto the upload zone canvas."""
        if not PIL_AVAILABLE: return
        try:
            cv = self._thumb_cv
            cv_w = cv.winfo_width() or 340
            cv.delete("all")
            img = Image.open(path).convert("RGB")
            img.thumbnail((cv_w-10, 130), Image.LANCZOS)
            self._thumb_photo = ImageTk.PhotoImage(img)
            cx = cv_w // 2
            cv.create_rectangle(0,0,cv_w,140, fill=CARD, outline="")
            cv.create_image(cx, 70, image=self._thumb_photo, anchor="center")
            # Success checkmark overlay
            cv.create_oval(cx+img.width//2-22, 4, cx+img.width//2+2, 28,
                           fill=GREEN, outline="")
            cv.create_text(cx+img.width//2-10, 16, text="✓",
                           fill=WHITE, font=("Helvetica",10,"bold"))
            safe_cfg(self._img_name_lbl,
                     text=f"✓ {os.path.basename(path)}", fg=GREEN)
        except Exception as ex:
            try:
                cv = self._thumb_cv
                cv.delete("all")
                cv.create_text(170, 70, text=f"⚠ {str(ex)[:60]}",
                               fill=WARN, font=("Helvetica",9), width=300)
            except Exception: pass

    def _upload_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp *.tiff"),
                       ("All Files", "*.*")])
        if not path: return
        self._img_path = path
        self._show_thumb(path)

    def _get_api_key(self):
        """Return the API key for the currently active provider."""
        p = _SETTINGS.get("active_provider","openai")
        if p == "openai": return _SETTINGS.get("openai_api_key","").strip()
        return _SETTINGS.get("gemini_api_key","").strip()

    def _active_provider(self):
        return _SETTINGS.get("active_provider","openai")

    def _encode_image(self):
        with open(self._img_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(self._img_path)[1].lower()
        mime = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",
                ".bmp":"image/bmp",".webp":"image/webp",".tiff":"image/tiff"
                }.get(ext, "image/jpeg")
        return data, mime

    def _call_api(self, api_key, prompt_text, img_data, mime_type, on_done, btn):
        """Unified API dispatcher with full debug logging."""
        import time as _time

        def _log(msg):
            print(f"[API DEBUG] {msg}")
            try:
                self.after(0, lambda m=msg: safe_cfg(self._status_lbl,text=m[:120], fg=WARN))
            except Exception:
                pass

        def _compress(b64, mime, quality):
            if not PIL_AVAILABLE:
                _log("PIL not available — skipping compression")
                return b64, mime
            try:
                raw = base64.b64decode(b64)
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                _log(f"Original image size: {img.width}x{img.height}")
                if img.width > 1024 or img.height > 1024:
                    img.thumbnail((1024, 1024), Image.LANCZOS)
                    _log(f"Resized to: {img.width}x{img.height}")
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=quality, optimize=True)
                comp     = base64.b64encode(buf.getvalue()).decode("utf-8")
                orig_kb  = len(b64) * 3 // 4 // 1024
                comp_kb  = len(comp) * 3 // 4 // 1024
                _log(f"Compressed: {orig_kb}KB -> {comp_kb}KB (quality={quality})")
                return comp, "image/jpeg"
            except Exception as ex:
                _log(f"Compression error (using original): {ex}")
                return b64, mime

        def _call_gemini(key, prompt, img, mime, attempt, max_tries):
            url   = get_gemini_url()
            model = _SETTINGS.get("gemini_model","gemini-1.5-flash-8b  (Free tier, higher quota)").split()[0]
            _log(f"Gemini call — model={model} attempt={attempt}/{max_tries}")
            _log(f"URL: {url[:80]}...")
            _log(f"Image mime: {mime}, b64 length: {len(img) if img else 0}")
            parts = [{"text": prompt}]
            if img:
                parts.append({"inline_data": {"mime_type": mime, "data": img}})
                _log("Including image in request")
            else:
                _log("Text-only request (no image)")
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": 0.5, "maxOutputTokens": 3000}
            }
            payload_bytes = json.dumps(payload).encode("utf-8")
            _log(f"Payload size: {len(payload_bytes)//1024}KB")
            req = urllib.request.Request(
                url, data=payload_bytes,
                headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
            _log("Sending request to Gemini...")
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw  = resp.read().decode("utf-8")
                code = resp.getcode()
            _log(f"Response HTTP {code}, body size: {len(raw)} chars")
            data = json.loads(raw)
            candidates = data.get("candidates", [])
            _log(f"Candidates in response: {len(candidates)}")
            if not candidates:
                # Check for prompt feedback / safety blocks
                feedback = data.get("promptFeedback", {})
                block    = feedback.get("blockReason", "unknown")
                _log(f"No candidates — blockReason: {block}")
                raise ValueError(
                    f"Gemini returned no candidates. Block reason: {block}\n"
                    "Try a different model in Settings (gemini-1.5-flash-8b recommended).")
            result = candidates[0]["content"]["parts"][0].get("text","")
            _log(f"Success — response length: {len(result)} chars")
            return result

        def _call_openai(key, prompt, img, mime, attempt, max_tries):
            model_label = _SETTINGS.get(
                "openai_model","gpt-4o-mini        (Vision, faster & cheaper)")
            model = OPENAI_MODELS.get(model_label, "gpt-4o-mini")
            _log(f"OpenAI call — model={model} attempt={attempt}/{max_tries}")
            _log(f"URL: {OPENAI_API_URL}")
            _log(f"Image mime: {mime}, b64 length: {len(img) if img else 0}")
            _log(f"Key starts with: {key[:8]}... length={len(key)}")
            if img:
                _log("Including image in OpenAI request (detail=low to save tokens)")
                msg_content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url",
                     "image_url": {"url": f"data:{mime};base64,{img}",
                                   "detail": "low"}}
                ]
            else:
                _log("Text-only OpenAI request (no image)")
                msg_content = [{"type": "text", "text": prompt}]
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": msg_content}],
                "max_tokens": 3000,
                "temperature": 0.5
            }
            payload_bytes = json.dumps(payload).encode("utf-8")
            _log(f"Payload size: {len(payload_bytes)//1024}KB")
            req = urllib.request.Request(
                OPENAI_API_URL, data=payload_bytes,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {key}"},
                method="POST")
            _log("Sending request to OpenAI...")
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw  = resp.read().decode("utf-8")
                code = resp.getcode()
            _log(f"Response HTTP {code}, body size: {len(raw)} chars")
            data = json.loads(raw)
            choices = data.get("choices", [])
            _log(f"Choices in response: {len(choices)}")
            if not choices:
                raise ValueError(
                    "OpenAI returned no choices.\n"
                    "Check your API key has GPT-4o access at platform.openai.com")
            result = choices[0]["message"]["content"]
            _log(f"Success — response length: {len(result)} chars")
            return result

        def _go():
            _log(f"=== API call started ===")
            _log(f"Provider: {self._active_provider()}")
            _log(f"API key length: {len(api_key)}")
            _log(f"Image data length: {len(img_data) if img_data else 0}")
            _log(f"Mime type: {mime_type}")

            if not api_key:
                self.after(0, lambda: on_done(False,
                    "No API key found.\n\n"
                    "Go to Settings (top bar) and enter your API key first."))
                self.after(0, lambda: safe_cfg(btn,state="normal"))
                return

            # img_data can be None for text-only calls
            final_img, final_mime = img_data, mime_type or "image/jpeg"
            if img_data and _SETTINGS.get("compress_images", True):
                final_img, final_mime = _compress(
                    img_data, final_mime,
                    int(_SETTINGS.get("compress_quality", 60)))

            provider  = self._active_provider()
            max_tries = int(_SETTINGS.get("max_retries", 3))

            for attempt in range(1, max_tries + 1):
                try:
                    if provider == "openai":
                        text = _call_openai(api_key, prompt_text,
                                            final_img, final_mime,
                                            attempt, max_tries)
                    else:
                        text = _call_gemini(api_key, prompt_text,
                                            final_img, final_mime,
                                            attempt, max_tries)

                    _log(f"=== API call succeeded on attempt {attempt} ===")
                    self.after(0, lambda t=text: on_done(True, t))
                    self.after(0, lambda: safe_cfg(btn,state="normal"))
                    return

                except urllib.error.HTTPError as e:
                    body = e.read().decode("utf-8", errors="replace")
                    _log(f"HTTPError {e.code}: {body[:400]}")
                    try:
                        err_json = json.loads(body)
                        if provider == "openai":
                            err_obj  = err_json.get("error", {})
                            msg      = err_obj.get("message", body[:300])
                            code_int = e.code
                        else:
                            err_obj  = err_json.get("error", {})
                            msg      = err_obj.get("message", body[:300])
                            code_int = err_obj.get("code", e.code)
                            if isinstance(code_int, str):
                                try:    code_int = int(code_int)
                                except: code_int = e.code
                    except Exception as parse_ex:
                        _log(f"Could not parse error body: {parse_ex}")
                        msg      = body[:300]
                        code_int = e.code

                    _log(f"Parsed error code={code_int} msg={msg[:100]}")

                    # 429 rate limit
                    if code_int == 429 and attempt < max_tries:
                        wait = 2 ** attempt
                        _log(f"Rate limited — waiting {wait}s before retry")
                        _time.sleep(wait)
                        continue

                    # helpful messages per error code
                    if code_int == 401:
                        msg = ("Invalid API key (401).\n\n"
                               "Your key was rejected. Please:\n"
                               "  1. Open Settings\n"
                               "  2. Re-paste your API key (make sure no spaces)\n"
                               f"  3. Key starts with: {api_key[:8]}... ({len(api_key)} chars)")
                    elif code_int == 403:
                        msg = ("Access denied (403).\n\n"
                               "Your key doesn't have access to this model.\n"
                               "Try gpt-4o-mini (OpenAI) or gemini-1.5-flash-8b (Gemini).")
                    elif code_int == 404:
                        msg = ("Model not found (404).\n\n"
                               "The selected model isn't available on your tier.\n"
                               "Open Settings and switch to a different model.")
                    elif code_int == 429:
                        msg = ("Quota exceeded (429).\n\n"
                               "You've hit your rate limit after all retries.\n"
                               "Wait 1 minute and try again, or upgrade your plan.")

                    self.after(0, lambda m=f"Error {code_int}: {msg}": on_done(False, m))
                    self.after(0, lambda: safe_cfg(btn,state="normal"))
                    return

                except urllib.error.URLError as e:
                    _log(f"URLError: {e.reason}")
                    self.after(0, lambda r=str(e.reason): on_done(False,
                        f"Network error: {r}\n\n"
                        "Check your internet connection and try again."))
                    self.after(0, lambda: safe_cfg(btn,state="normal"))
                    return

                except Exception as ex:
                    _log(f"Exception on attempt {attempt}: {type(ex).__name__}: {ex}")
                    if attempt < max_tries:
                        _time.sleep(1)
                        continue
                    self.after(0, lambda m=f"{type(ex).__name__}: {ex}": on_done(False, m))
                    self.after(0, lambda: safe_cfg(btn,state="normal"))
                    return

            # all retries exhausted
            tips = (
                "  • Switch to gpt-4o-mini in Settings\n"
                "  • Check billing: platform.openai.com/usage"
                if provider == "openai" else
                "  • Switch to gemini-1.5-flash-8b in Settings\n"
                "  • Wait 1 minute (free tier resets per minute)\n"
                "  • Check: ai.google.dev"
            )
            self.after(0, lambda mx=max_tries, t=tips: on_done(False,
                f"Failed after {mx} attempts.\n\n{t}"))
            self.after(0, lambda: safe_cfg(btn,state="normal"))

        safe_cfg(btn,state="disabled")
        threading.Thread(target=_go, daemon=True).start()


    def _pre_check(self):
        """Returns (api_key, img_data, mime) or None if validation fails."""
        key = self._get_api_key()
        if not key:
            provider = self._active_provider()
            if provider == "openai":
                messagebox.showwarning("API Key Required",
                    "Enter your OpenAI API key in Settings.\n\n"
                    "Get one at: platform.openai.com/api-keys")
            else:
                messagebox.showwarning("API Key Required",
                    "Enter your Gemini API key in Settings.\n\n"
                    "Free key at: aistudio.google.com/app/apikey")
            return None
        if not self._img_path or not os.path.exists(self._img_path):
            messagebox.showwarning("No Image", "Upload an image first.")
            return None
        try:
            data, mime = self._encode_image()
            return key, data, mime
        except Exception as ex:
            messagebox.showerror("Image Error", str(ex))
            return None

    def _set_status(self, msg, color=None):
        safe_cfg(self._status_lbl,text=msg, fg=color or MUTED)

    def _set_output(self, text):
        safe_cfg(self._out_text,state="normal")
        self._out_text.delete("1.0", "end")
        self._out_text.insert("1.0", text)
        safe_cfg(self._out_text,state="disabled")

    def _clear_results(self):
        safe_cfg(self._result_lbl,text="Run an analysis to see results here.", fg=MUTED)
        for w in self._steps_frame.winfo_children(): w.destroy()
        self._set_output("Results will appear here after analysis…")
        self._set_status("Cleared.", MUTED)
        self._last_result = None
        self._edited_pil_img = None
        self._ai_preview_photo = None
        self._ai_canvas.delete("all")
        self._ai_canvas.create_text(170, 110,
            text="Edited image will appear here after analysis",
            fill=MUTED, font=F["xs"], width=280, justify="center")
        safe_cfg(self._save_edit_btn,state="disabled")

    # ── MODE 1: Analyse & Apply ───────────────────────────────────────
    def _test_connection(self):
        """Send a minimal text-only request to verify key and connectivity."""
        key      = self._get_api_key()
        provider = self._active_provider()

        if not key:
            messagebox.showwarning("No API Key",
                "Enter your API key in Settings first.\n\n"
                "Click the ⚙ Settings button in the top bar.")
            return

        self._set_status("Testing connection...", WARN)

        def _go():
            import time as _time
            try:
                if provider == "openai":
                    # Text-only test — no image needed
                    payload = {
                        "model": OPENAI_MODELS.get(
                            _SETTINGS.get("openai_model","gpt-4o-mini        (Vision, faster & cheaper)"),
                            "gpt-4o-mini"),
                        "messages": [{"role":"user","content":"Say OK"}],
                        "max_tokens": 5
                    }
                    req = urllib.request.Request(
                        OPENAI_API_URL,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type":"application/json",
                                 "Authorization": f"Bearer {key}"},
                        method="POST")
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        data  = json.loads(resp.read().decode("utf-8"))
                    reply = data["choices"][0]["message"]["content"]
                    model = OPENAI_MODELS.get(
                        _SETTINGS.get("openai_model",""), "gpt-4o-mini")
                    self.after(0, lambda r=reply, m=model: (
                        self._set_status(
                            f"✅ OpenAI connected! Model: {m} — Reply: {r}", GREEN),
                        messagebox.showinfo("Connection OK",
                            f"OpenAI is working!\n\nModel: {m}\nResponse: {r}\n\n"
                            "You can now upload an image and run Analyse.")))
                else:
                    # Gemini text-only test
                    url = get_gemini_url()
                    payload = {
                        "contents": [{"parts":[{"text":"Say OK"}]}],
                        "generationConfig": {"maxOutputTokens": 5}
                    }
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type":"application/json",
                                 "x-goog-api-key": key},
                        method="POST")
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    reply = data["candidates"][0]["content"]["parts"][0].get("text","")
                    model = _SETTINGS.get("gemini_model","").split()[0]
                    self.after(0, lambda r=reply, m=model: (
                        self._set_status(
                            f"✅ Gemini connected! Model: {m} — Reply: {r}", GREEN),
                        messagebox.showinfo("Connection OK",
                            f"Gemini is working!\n\nModel: {m}\nResponse: {r}\n\n"
                            "You can now upload an image and run Analyse.")))

            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                try:
                    msg = json.loads(body).get("error",{}).get("message", body[:200])
                except Exception:
                    msg = body[:200]
                self.after(0, lambda c=e.code, m=msg: (
                    self._set_status(f"❌ HTTP {c}: {m[:80]}", A2),
                    messagebox.showerror("Connection Failed",
                        f"HTTP {c}: {m}\n\n"
                        "Common fixes:\n"
                        "  401 = bad API key (check Settings)\n"
                        "  403 = no model access (try a cheaper model)\n"
                        "  404 = wrong model name\n"
                        "  429 = quota exceeded (wait or upgrade)")))
            except urllib.error.URLError as e:
                self.after(0, lambda r=str(e.reason): (
                    self._set_status(f"❌ Network error: {r}", A2),
                    messagebox.showerror("No Connection",
                        f"Network error: {r}\n\nCheck your internet connection.")))
            except Exception as ex:
                self.after(0, lambda m=str(ex): (
                    self._set_status(f"❌ {m[:80]}", A2),
                    messagebox.showerror("Error", str(m))))

        threading.Thread(target=_go, daemon=True).start()

    def _run_analyse(self):
        checked = self._pre_check()
        if not checked: return
        key, img_data, mime = checked
        req_txt = self._analyse_req.get("1.0","end").strip() or "Analyse this image."
        vibe    = self._vibe_v.get()
        actions = [a for a,v in self._action_vars.items() if v.get()]

        prompt = (
            "You are a world-class graphic designer and AI orchestrator. "
            "Analyse this image and respond with ONLY a valid JSON object (no markdown, no backticks).\n\n"
            "JSON structure:\n"
            "{\n"
            '  \"subject_detection\": \"describe the main subject\",\n'
            '  \"color_palette\": [\"#hex1\",\"#hex2\",\"#hex3\"],\n'
            '  \"image_vibe\": \"mood/style\",\n'
            '  \"editing_steps\": [{\"step\":1,\"action\":\"name\",\"priority\":\"high\",\"description\":\"what to do\"}],\n'
            '  \"google_api_params\": {\"gemini_prompt\":\"...\",'
            '\"imagen_prompt\":\"...\",'
            '\"removal_mask\":\"...\",'
            '\"style_transfer\":\"...\",'
            '\"upscale_factor\":2,'
            '\"color_grade_lut\":\"...\"},\n'
            '  \"design_overlay\": {\"suggested_font\":\"...\",'
            '\"headline_text\":\"...\",'
            '\"subheadline_text\":\"...\",'
            '\"cta_button_text\":\"...\",'
            '\"color_scheme\":[\"#hex1\",\"#hex2\"],'
            '\"layout_template\":\"...\",'
            '\"text_placement\":\"top/bottom\"},\n'
            '  \"canva_template\": \"describe the ideal Canva template\"\n'
            "}\n\n"
            f"User request: {req_txt}\n"
            f"Preferred vibe: {vibe}\n"
            f"Requested actions: {', '.join(actions) if actions else 'auto-detect'}"
        )

        self._set_status("Sending to Gemini Vision...", WARN)
        safe_cfg(self._analyse_btn,text="Analysing...")

        def on_done(ok, text):
            safe_cfg(self._analyse_btn,text="Analyse Image", state="normal")
            if not ok:
                self._set_status(f"Error: {text[:80]}", A2)
                messagebox.showerror("Analysis Failed", text)
                return
            clean = text.strip()
            for fence in ["```json", "```"]:
                if fence in clean:
                    clean = clean.split(fence)[-1].split("```")[0].strip()
            try:
                result = json.loads(clean)
                self._last_result = result
                self._display_analyse_results(result)
                self._set_status("Analysis complete! Hit Apply to Clip to use suggestions.", GREEN)
            except json.JSONDecodeError:
                self._last_result = {"raw": text}
                self._set_output(text)
                self._set_status("Got response — see output box below.", GREEN)

        self._call_api(key, prompt, img_data, mime, on_done, self._analyse_btn)

    # ── MODE 2: AI Image Editor (OpenAI or Gemini)
    def _run_prompt(self):
        provider = _SETTINGS.get("active_provider","openai")
        key = self._get_api_key()
        if not key:
            messagebox.showwarning("API Key Required",
                "Enter your API key in Settings first.\n\n"
                "OpenAI: platform.openai.com/api-keys\n"
                "Gemini: aistudio.google.com/app/apikey")
            return
        instruction = self._edit_req.get("1.0","end").strip()
        if not instruction:
            messagebox.showwarning("No Instruction","Type what you want to do to the image.")
            return
        size = self._edit_size_v.get()
        safe_cfg(self._prompt_btn,state="disabled", text="Generating…")
        provider_label = "OpenAI" if provider == "openai" else "Gemini"
        self._set_status(f"Sending to {provider_label} image API…", WARN)

        def _go():
            try:
                # ── OpenAI path ───────────────────────────────────────
                if provider == "openai":
                    if self._img_path and os.path.exists(self._img_path):
                        with open(self._img_path, "rb") as f:
                            img_bytes = f.read()
                        ext = os.path.splitext(self._img_path)[1].lower()
                        mime_type = {".jpg":"image/jpeg",".jpeg":"image/jpeg",
                                     ".png":"image/png",".webp":"image/webp"}.get(ext,"image/png")
                        boundary = "----FormBoundaryVideoEditor"
                        body  = f"--{boundary}\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\n{instruction}\r\n".encode()
                        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\ngpt-image-1\r\n".encode()
                        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"size\"\r\n\r\n{size}\r\n".encode()
                        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"image[]\"; filename=\"image{ext}\"\r\nContent-Type: {mime_type}\r\n\r\n".encode()
                        body += img_bytes
                        body += f"\r\n--{boundary}--\r\n".encode()
                        req = urllib.request.Request(
                            "https://api.openai.com/v1/images/edits",
                            data=body,
                            headers={"Authorization": f"Bearer {key}",
                                     "Content-Type": f"multipart/form-data; boundary={boundary}"},
                            method="POST")
                    else:
                        payload = json.dumps({"model":"gpt-image-1","prompt":instruction,
                                              "size":size,"n":1}).encode()
                        req = urllib.request.Request(
                            "https://api.openai.com/v1/images/generations",
                            data=payload,
                            headers={"Authorization": f"Bearer {key}",
                                     "Content-Type": "application/json"},
                            method="POST")
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    b64 = data["data"][0].get("b64_json","")
                    url = data["data"][0].get("url","")
                    if b64:
                        raw = base64.b64decode(b64)
                    elif url:
                        with urllib.request.urlopen(url, timeout=60) as r: raw = r.read()
                    else:
                        raise ValueError("No image in OpenAI response")

                # ── Gemini path (imagen-3) ────────────────────────────
                else:
                    # Use Imagen 3 via Gemini API for image generation
                    img_url = (f"https://generativelanguage.googleapis.com"
                               f"/v1beta/models/imagen-3.0-generate-002:predict")
                    # Build prompt — include image description if we have one
                    full_prompt = instruction
                    if self._img_path and os.path.exists(self._img_path):
                        # Encode source image for reference
                        with open(self._img_path,"rb") as f:
                            src_b64 = base64.b64encode(f.read()).decode()
                        ext = os.path.splitext(self._img_path)[1].lower()
                        src_mime = {".jpg":"image/jpeg",".jpeg":"image/jpeg",
                                    ".png":"image/png"}.get(ext,"image/png")
                        payload = json.dumps({
                            "instances": [{"prompt": full_prompt}],
                            "parameters": {"sampleCount": 1,
                                           "aspectRatio": "1:1"}
                        }).encode()
                    else:
                        payload = json.dumps({
                            "instances": [{"prompt": full_prompt}],
                            "parameters": {"sampleCount": 1,
                                           "aspectRatio": "1:1"}
                        }).encode()
                    req = urllib.request.Request(
                        img_url, data=payload,
                        headers={"Content-Type":"application/json"},
                        method="POST")
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    b64 = data["predictions"][0].get("bytesBase64Encoded","")
                    if not b64:
                        raise ValueError("No image in Gemini response")
                    raw = base64.b64decode(b64)

                pil_img = Image.open(io.BytesIO(raw)).convert("RGB")

                def _show(img=pil_img):
                    self._edit_pil_img = img
                    thumb = img.copy(); thumb.thumbnail((340,260), Image.LANCZOS)
                    bg = Image.new("RGB",(340,260),(17,24,39))
                    bg.paste(thumb,((340-thumb.width)//2,(260-thumb.height)//2))
                    photo = ImageTk.PhotoImage(bg)
                    self._edit_photo = photo
                    self._edit_canvas.delete("all")
                    self._edit_canvas.create_image(170,130,anchor="center",image=self._edit_photo)
                    self._edit_canvas.update()
                    safe_cfg(self._edit_save_btn,state="normal")
                    safe_cfg(self._edit_add_btn,state="normal")
                    safe_cfg(self._prompt_btn,state="normal", text="🖼  Generate Edited Image")
                    self._set_status("✅ Image generated! Hit Save to download.", GREEN)
                self.after(50, _show)

            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                try:    msg = json.loads(body).get("error",{}).get("message", body[:300])
                except: msg = body[:300]
                self.after(0, lambda m=msg, c=e.code: (
                    safe_cfg(self._prompt_btn,state="normal", text="🖼  Generate Edited Image"),
                    self._set_status(f"❌ HTTP {c}: {m[:60]}", A2),
                    messagebox.showerror("Failed", f"HTTP {c}: {m}")))
            except Exception as ex:
                import traceback; traceback.print_exc()
                self.after(0, lambda m=str(ex): (
                    safe_cfg(self._prompt_btn,state="normal", text="🖼  Generate Edited Image"),
                    self._set_status(f"❌ {m[:80]}", A2),
                    messagebox.showerror("Error", m)))

        threading.Thread(target=_go, daemon=True).start()

    def _add_to_timeline(self, path):
        """Shared helper — add any file path to the main timeline."""
        app = self.winfo_toplevel()
        # Find the MediaPanel which holds _proj and _on_change
        media_panel = None
        for w in app.winfo_children():
            if hasattr(w, "_proj") and hasattr(w, "_on_change"):
                media_panel = w; break
        if media_panel is None:
            # Search deeper
            def _find(widget):
                if hasattr(widget,"_proj") and hasattr(widget,"_on_change"):
                    return widget
                for c in widget.winfo_children():
                    r = _find(c)
                    if r: return r
                return None
            media_panel = _find(app)
        if media_panel is None:
            Toast.show(app,"Could not find timeline — try importing manually.","warn")
            return
        c = Clip(path)
        c.load_thumb()
        media_panel._proj.clips.append(c)
        media_panel._on_change()

    def _add_imagegen_to_timeline(self):
        """Add Image Gen result to timeline."""
        imgs = getattr(self, "_hf_generated_imgs", [])
        if not imgs:
            Toast.show(self.winfo_toplevel(), "No generated image to add!", "warn"); return
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="proedit_ig_")
        tmp.close()
        imgs[0].save(tmp.name)
        self._add_to_timeline(tmp.name)
        Toast.show(self.winfo_toplevel(), "✅ Image Gen result added to timeline!", "success")

    def _add_sora_to_timeline(self):
        """Add Sora video to timeline."""
        if not self._sora_video_bytes:
            Toast.show(self.winfo_toplevel(), "No Sora video to add!", "warn"); return
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, prefix="proedit_sora_")
        tmp.write(self._sora_video_bytes)
        tmp.close()
        self._add_to_timeline(tmp.name)
        Toast.show(self.winfo_toplevel(), "✅ Sora video added to timeline!", "success")

    def _add_edit_image_to_timeline(self):
        """Add AI-generated edit image to timeline as a clip."""
        if not hasattr(self,"_edit_pil_img") or self._edit_pil_img is None:
            Toast.show(self.winfo_toplevel(),"No generated image to add!","warn"); return
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="proedit_ai_")
        tmp.close()
        self._edit_pil_img.save(tmp.name)
        self._add_to_timeline(tmp.name)
        Toast.show(self.winfo_toplevel(),"✅ AI image added to timeline!","success")

    def _add_ws_video_to_timeline(self):
        """Add WaveSpeed generated video to timeline as a clip."""
        if not self._ws_video_bytes:
            Toast.show(self.winfo_toplevel(),"No generated video to add!","warn"); return
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, prefix="proedit_ws_")
        tmp.write(self._ws_video_bytes)
        tmp.close()
        self._add_to_timeline(tmp.name)
        Toast.show(self.winfo_toplevel(),"✅ WaveSpeed video added to timeline!","success")

    def _save_edit_image(self):
        if not self._edit_pil_img:
            messagebox.showinfo("Nothing to Save","Generate an image first."); return
        p = filedialog.asksaveasfilename(
            defaultextension=".png", initialfile="ai_generated.png",
            filetypes=[("PNG","*.png"),("JPEG","*.jpg"),("All","*.*")])
        if p:
            self._edit_pil_img.save(p)
            self._set_status(f"✅ Saved: {os.path.basename(p)}", GREEN)


    # ── MODE 3: Animation Planner, img_data, mime, on_done, self._prompt_btn)

    # ── MODE 3: Animation Planner
    def _run_animate(self):
        # Animation planner works with OR without an image
        key = self._get_api_key()
        if not key:
            provider = self._active_provider()
            if provider == "openai":
                messagebox.showwarning("No API Key",
                    "Enter your OpenAI key in Settings.\n\nGet one at: platform.openai.com/api-keys")
            else:
                messagebox.showwarning("No API Key",
                    "Enter your Gemini key in Settings.\n\nGet one at: aistudio.google.com")
            return
        img_data, mime = None, None
        if self._img_path and os.path.exists(self._img_path):
            try:
                img_data, mime = self._encode_image()
            except Exception:
                pass
        checked = (key, img_data, mime)
        req_txt  = self._anim_req.get("1.0","end").strip() or "Animate this image."
        style    = self._anim_style_v.get()
        platform = self._platform_v.get()

        prompt = (
            f"You are a world-class motion designer and AI video director for {platform}.\n"
            "Analyse this image and create a detailed shot-by-shot animation plan.\n\n"
            "Include these sections with clear headers:\n\n"
            "SCENE ANALYSIS\n"
            "Describe subjects, depth layers, and key visual elements.\n\n"
            "CAMERA MOVEMENT\n"
            "Exact camera motion, speed, and duration.\n\n"
            "SUBJECT ANIMATION\n"
            "What each element does, timing, easing, and VFX.\n\n"
            "COPY-PASTE API PROMPT\n"
            f"A ready-to-use prompt for {platform} with all technical parameters.\n\n"
            "SETTINGS\n"
            f"Recommended {platform} settings: resolution, fps, duration, motion strength.\n\n"
            "POST PRODUCTION TIP\n"
            "One manual technique to enhance the result in After Effects or Premiere.\n\n"
            f"Animation style: {style}\n"
            f"User request: {req_txt}"
        )

        self._set_status("Building animation plan...", WARN)
        safe_cfg(self._anim_btn,text="Planning...")

        def on_done(ok, text):
            safe_cfg(self._anim_btn,text="Generate Animation Plan", state="normal")
            if not ok:
                self._set_status(f"Error: {text[:80]}", A2)
                messagebox.showerror("Failed", text)
                return
            safe_cfg(self._result_lbl,fg=TEXT,
                text=f"Animation plan ready for {platform} | Style: {style}")
            self._set_output(text)
            self._last_result = {"animation_plan": text, "platform": platform, "style": style}
            self._set_status(f"Animation plan ready! Copy the prompt for {platform}.", GREEN)

        self._call_api(key, prompt, img_data, mime, on_done, self._anim_btn)

    # ── Sora Video Generation ────────────────────────────────────────
    def _run_sora(self):
        import time as _time
        key = _SETTINGS.get("openai_api_key","").strip()
        if not key:
            messagebox.showwarning("OpenAI Key Required",
                "Sora requires your OpenAI API key.\n\n"
                "Go to Settings and enter your OpenAI key.")
            return

        prompt   = self._sora_prompt.get("1.0","end").strip()
        if not prompt:
            messagebox.showwarning("No Prompt","Enter a video prompt first.")
            return

        model    = self._sora_model_v.get()
        model    = self._sora_model_v.get()
        size_val = self._sora_res_v.get()  # e.g. "1280x720"
        duration = int(self._sora_dur_v.get())

        # Parse exact WxH from value — API requires exact strings
        try:
            width, height = (int(x) for x in size_val.split("x"))
        except Exception:
            width, height = 1280, 720
        # Auto-switch model to sora-2-pro for 1080p (required)
        if width >= 1792 or height >= 1024:
            model = "sora-2-pro"
        safe_cfg(self._sora_gen_btn,state="disabled", text="Submitting…")
        self._sora_progress_bar.start(10)
        safe_cfg(self._sora_progress_lbl,
            text=f"Submitting to Sora ({model}, {size_val}, {duration}s)…",
            fg=WARN)
        safe_cfg(self._sora_save_btn,state="disabled")
        self._sora_video_bytes = None

        def _go():
            try:
                # Step 1 — Create the video job using multipart/form-data
                # Correct endpoint: POST /v1/videos (not /v1/videos/generations)
                size_str = f"{width}x{height}"
                boundary = "----SoraFormBoundary"
                body  = f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{model}\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\n{prompt}\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"size\"\r\n\r\n{size_str}\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"seconds\"\r\n\r\n{duration}\r\n".encode()
                body += f"--{boundary}--\r\n".encode()

                req = urllib.request.Request(
                    "https://api.openai.com/v1/videos",
                    data=body,
                    headers={"Authorization": f"Bearer {key}",
                             "Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST")

                with urllib.request.urlopen(req, timeout=60) as resp:
                    job = json.loads(resp.read().decode("utf-8"))

                job_id = job.get("id","")
                if not job_id:
                    raise ValueError(f"No job ID returned: {job}")

                self.after(0, lambda jid=job_id: safe_cfg(self._sora_progress_lbl,
                    text=f"Job submitted! ID: {jid[:24]}  polling…",
                    fg=WARN))

                # Step 2 — Poll GET /v1/videos/{id} until completed
                start_time = _time.time()
                self.after(0, lambda: self._sora_progress_bar.config(mode="determinate", value=0))
                for attempt in range(120):   # up to 10 minutes
                    _time.sleep(5)
                    poll_req = urllib.request.Request(
                        f"https://api.openai.com/v1/videos/{job_id}",
                        headers={"Authorization": f"Bearer {key}"},
                        method="GET")
                    with urllib.request.urlopen(poll_req, timeout=30) as pr:
                        status_data = json.loads(pr.read().decode("utf-8"))

                    status = status_data.get("status","")
                    pct    = status_data.get("progress", 0) or 0
                    self.after(0, lambda s=status, p=pct, a=attempt:
                        safe_cfg(self._sora_progress_lbl,
                            text=f"Status: {s}  {int(p*100)}%  elapsed ~{(a+1)*5}s",
                            fg=WARN))

                    if status == "completed":
                        print(f"[SORA] Completed! Response keys: {list(status_data.keys())}")
                        print(f"[SORA] Full response: {str(status_data)[:500]}")
                        break
                    elif status == "failed":
                        err = status_data.get("error",{}).get("message","Unknown error")
                        raise ValueError(f"Sora generation failed: {err}")
                else:
                    raise TimeoutError("Sora generation timed out after 10 minutes.")

                # Step 3 — Download MP4
                # Check if response has a direct URL first
                video_url_direct = None
                generations = status_data.get("generations", [])
                if generations:
                    video_url_direct = generations[0].get("url","")

                if video_url_direct:
                    dl_req = urllib.request.Request(
                        video_url_direct,
                        headers={"Authorization": f"Bearer {key}"},
                        method="GET")
                else:
                    # Try standard download endpoint
                    dl_req = urllib.request.Request(
                        f"https://api.openai.com/v1/videos/{job_id}/content",
                        headers={"Authorization": f"Bearer {key}"},
                        method="GET")

                with urllib.request.urlopen(dl_req, timeout=120) as vr:
                    video_bytes = vr.read()
                
                if len(video_bytes) < 1000:
                    raise ValueError(f"Download too small ({len(video_bytes)} bytes) — may have failed")

                self._sora_video_bytes = video_bytes

                total_elapsed = int(_time.time() - start_time)
                total_mins, total_secs = divmod(total_elapsed, 60)
                total_str = f"{total_mins}m {total_secs:02d}s" if total_mins else f"{total_secs}s"

                def _done(ts=total_str):
                    self._sora_progress_bar.config(value=100)
                    safe_cfg(self._sora_gen_btn, state="normal",
                             text="🎬  Generate Video with Sora")
                    safe_cfg(self._sora_progress_lbl,
                        text=f"✅ Complete in {ts}!  {len(video_bytes)//1024}KB — hit Save.",
                        fg=GREEN)
                    safe_cfg(self._sora_result_lbl,
                        text=f"✅ Generated {duration}s {size_val} video with {model}  ({ts})",
                        fg=GREEN)
                    safe_cfg(self._sora_save_btn, state="normal")
                    safe_cfg(self._sora_add_btn, state="normal")
                    safe_cfg(self._sora_reset_btn, state="normal")
                    Toast.show(self, f"Sora video ready! Generated in {ts}", "success", 5000)
                self.after(0, _done)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                try:    msg = json.loads(body).get("error",{}).get("message", body[:300])
                except: msg = body[:300]
                self.after(0, lambda c=e.code, m=msg: self._sora_error(f"HTTP {c}: {m}"))
            except Exception as ex:
                import traceback; traceback.print_exc()
                self.after(0, lambda m=str(ex): self._sora_error(m))

        threading.Thread(target=_go, daemon=True).start()

    def _sora_error(self, msg):
        self._sora_progress_bar.stop()
        safe_cfg(self._sora_gen_btn,state="normal", text="🎬  Generate Video with Sora")
        safe_cfg(self._sora_progress_lbl,text=f"❌ {msg[:100]}", fg=A2)
        messagebox.showerror("Sora Error", msg)

    def _run_replicate(self):
        import time as _time
        key = _SETTINGS.get("replicate_api_key","").strip()
        if not key:
            Toast.show(self.winfo_toplevel(), "Add your Replicate API key first!", "error"); return
        prompt = self._rep_prompt.get("1.0","end").strip()
        if not prompt:
            Toast.show(self.winfo_toplevel(), "Enter a prompt first!", "warn"); return
        model_map = {
            "hunyuan": "tencent/hunyuan-video",
            "wan":     "wavespeedai/wan-2.1-1.3b-fp8",
            "mochi":   "genmoai/mochi-1",
            "ltx":     "lightricks/ltx-video",
        }
        model = model_map.get(self._rep_model_v.get(), "wavespeedai/wan-2.1-1.3b-fp8")
        duration = int(self._rep_dur_v.get())
        safe_cfg(self._rep_gen_btn, state="disabled", text="Generating…")
        safe_cfg(self._rep_save_btn, state="disabled")
        safe_cfg(self._rep_reset_btn, state="disabled")
        self._rep_progress_bar.config(value=0)
        safe_cfg(self._rep_progress_lbl, text="⏳ Submitting to Replicate…", fg=WARN)
        self._rep_video_bytes = None
        def _go():
            try:
                start = _time.time()
                payload = json.dumps({"input":{"prompt":prompt,"duration":duration}}).encode()
                req = urllib.request.Request(
                    f"https://api.replicate.com/v1/models/{model}/predictions",
                    data=payload,
                    headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                    method="POST")
                with urllib.request.urlopen(req, timeout=30) as r:
                    pred = json.loads(r.read().decode())
                pred_id = pred.get("id","")
                if not pred_id: raise ValueError(f"No prediction ID: {pred}")
                self.after(0, lambda: safe_cfg(self._rep_progress_lbl,
                    text="⏳ Submitted — polling…", fg=WARN))
                for attempt in range(180):
                    _time.sleep(5)
                    poll = urllib.request.Request(
                        f"https://api.replicate.com/v1/predictions/{pred_id}",
                        headers={"Authorization":f"Bearer {key}"},method="GET")
                    with urllib.request.urlopen(poll, timeout=30) as r:
                        data = json.loads(r.read().decode())
                    status = data.get("status","")
                    elapsed = int(_time.time()-start)
                    m2,s2 = divmod(elapsed,60)
                    t = f"{m2}m {s2:02d}s" if m2 else f"{s2}s"
                    pct = min(90,(attempt+1)*2)
                    self.after(0, lambda s=status,p=pct,ts=t: (
                        safe_cfg(self._rep_progress_lbl,
                                 text=f"⏳ {s.upper()}  ·  {ts} elapsed",fg=WARN),
                        self._rep_progress_bar.config(value=p)))
                    if status == "succeeded":
                        out = data.get("output")
                        if isinstance(out,list): out=out[0]
                        if not out: raise ValueError("No output URL")
                        with urllib.request.urlopen(
                                urllib.request.Request(out),timeout=120) as r:
                            self._rep_video_bytes = r.read()
                        elapsed2 = int(_time.time()-start)
                        m3,s3 = divmod(elapsed2,60)
                        ts = f"{m3}m {s3:02d}s" if m3 else f"{s3}s"
                        def _done(ts=ts):
                            self._rep_progress_bar.config(value=100)
                            safe_cfg(self._rep_gen_btn,state="normal",text="🔁  Generate Video")
                            safe_cfg(self._rep_progress_lbl,
                                text=f"✅ Done in {ts}!  {len(self._rep_video_bytes)//1024}KB",fg=GREEN)
                            safe_cfg(self._rep_result_lbl,
                                text=f"✅ {duration}s video  ({ts})",fg=GREEN)
                            safe_cfg(self._rep_save_btn,state="normal")
                            safe_cfg(self._rep_reset_btn,state="normal")
                            Toast.show(self,f"Replicate video ready! ({ts})","success",5000)
                        self.after(0,_done); return
                    elif status in ("failed","canceled"):
                        raise ValueError(data.get("error") or "Generation failed")
                raise TimeoutError("Replicate timed out after 15 minutes.")
            except Exception as ex:
                def _err(m=str(ex)):
                    safe_cfg(self._rep_gen_btn,state="normal",text="🔁  Generate Video")
                    safe_cfg(self._rep_progress_lbl,text=f"❌ {m[:120]}",fg=A2)
                    self._rep_progress_bar.config(value=0)
                    Toast.show(self,f"Error: {m[:80]}","error",6000)
                self.after(0,_err)
        threading.Thread(target=_go,daemon=True).start()

    def _save_rep_video(self):
        if not self._rep_video_bytes:
            Toast.show(self.winfo_toplevel(),"No video to save yet!","warn"); return
        path = filedialog.asksaveasfilename(defaultextension=".mp4",
            filetypes=[("MP4","*.mp4"),("All Files","*.*")],title="Save Replicate Video")
        if not path: return
        with open(path,"wb") as f: f.write(self._rep_video_bytes)
        Toast.show(self.winfo_toplevel(),f"Saved: {os.path.basename(path)}","success")

    def _reset_replicate(self):
        self._rep_video_bytes = None
        safe_cfg(self._rep_gen_btn,state="normal",text="🔁  Generate Video")
        safe_cfg(self._rep_save_btn,state="disabled")
        safe_cfg(self._rep_reset_btn,state="disabled")
        safe_cfg(self._rep_result_lbl,text="",fg=MUTED)
        safe_cfg(self._rep_progress_lbl,text="",fg=MUTED)
        try: self._rep_progress_bar.config(value=0)
        except Exception: pass
        try: self._rep_prompt.delete("1.0","end")
        except Exception: pass
        Toast.show(self.winfo_toplevel(),"Ready for a new Replicate video!","info")

    def _run_wavespeed(self):
        """Generate video using WaveSpeed.ai API."""
        import time as _time
        key = _SETTINGS.get("wavespeed_api_key","").strip()
        if not key:
            Toast.show(self.winfo_toplevel(), "Add your WaveSpeed API key first!", "error"); return
        prompt = self._ws_prompt.get("1.0","end").strip()
        if not prompt:
            Toast.show(self.winfo_toplevel(), "Enter a prompt first!", "warn"); return

        selected_key = self._ws_model_v.get()
        model_id = self._ws_model_ids.get(selected_key)
        if not model_id:
            Toast.show(self.winfo_toplevel(), "Please select a model.", "error"); return

        duration_raw = int(self._ws_dur_v.get())
        duration = 5 if duration_raw <= 5 else 8
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        size = "832*480" if "480p" in model_id else "1280*720"

        safe_cfg(self._ws_gen_btn, state="disabled", text="Generating…")
        safe_cfg(self._ws_save_btn, state="disabled")
        safe_cfg(self._ws_add_btn, state="disabled")
        safe_cfg(self._ws_reset_btn, state="disabled")
        self._ws_progress_bar.config(value=0)
        safe_cfg(self._ws_progress_lbl, text="⏳ Submitting…", fg=WARN)
        self._ws_video_bytes = None

        def _go():
            try:
                start = _time.time()
                payload = json.dumps({
                    "prompt": prompt,
                    "negative_prompt": "",
                    "size": size,
                    "num_inference_steps": 30,
                    "duration": duration,
                    "guidance_scale": 5,
                    "flow_shift": 5,
                    "seed": -1,
                    "enable_safety_checker": True,
                }).encode()

                # Step 1: Submit
                req = urllib.request.Request(
                    f"https://api.wavespeed.ai/api/v3/{model_id}",
                    data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as r:
                    sub = json.loads(r.read().decode())

                rdata = sub.get("data", sub)
                request_id = rdata.get("id","") or sub.get("id","")
                if not request_id:
                    raise ValueError(f"No request ID: {sub}")

                self.after(0, lambda rid=request_id: safe_cfg(self._ws_progress_lbl,
                    text=f"⏳ Submitted! ID={rid[:16]}…", fg=WARN))

                # Step 2: Poll with correct URL: GET /api/v3/predictions/{id}/result
                for attempt in range(180):
                    _time.sleep(5)
                    elapsed = int(_time.time()-start)
                    m2,s2 = divmod(elapsed,60)
                    t = f"{m2}m {s2:02d}s" if m2 else f"{s2}s"
                    pct = min(88, (attempt+1)*2)

                    poll = urllib.request.Request(
                        f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result",
                        headers=headers, method="GET")
                    with urllib.request.urlopen(poll, timeout=30) as r:
                        st = json.loads(r.read().decode())

                    pdata = st.get("data", st)
                    status = pdata.get("status", st.get("status",""))
                    self.after(0, lambda s=status,p=pct,ts=t: (
                        safe_cfg(self._ws_progress_lbl,
                            text=f"⏳ {s.upper()} · {ts}", fg=WARN),
                        self._ws_progress_bar.config(value=p)))

                    if status in ("completed","succeeded","success"):
                        outputs = pdata.get("outputs", st.get("outputs",[]))
                        video_url = outputs[0] if outputs else None
                        if not video_url:
                            raise ValueError(f"No output URL: {pdata}")

                        self.after(0, lambda: safe_cfg(self._ws_progress_lbl,
                            text="⏳ Downloading…", fg=WARN))
                        with urllib.request.urlopen(
                                urllib.request.Request(video_url), timeout=120) as r:
                            self._ws_video_bytes = r.read()

                        total = int(_time.time()-start)
                        m3,s3 = divmod(total,60)
                        ts = f"{m3}m {s3:02d}s" if m3 else f"{s3}s"
                        kb = len(self._ws_video_bytes)//1024

                        def _done(ts=ts,kb=kb):
                            self._ws_progress_bar.config(value=100)
                            safe_cfg(self._ws_gen_btn, state="normal", text="🌊  Generate Video")
                            safe_cfg(self._ws_progress_lbl,
                                text=f"✅ Done in {ts}! ({kb}KB)", fg=GREEN)
                            safe_cfg(self._ws_result_lbl,
                                text=f"✅ {model_id.split('/')[-1]} ({ts})", fg=GREEN)
                            safe_cfg(self._ws_save_btn, state="normal")
                            safe_cfg(self._ws_add_btn, state="normal")
                            safe_cfg(self._ws_reset_btn, state="normal")
                            Toast.show(self, f"Video ready! ({ts})", "success", 5000)
                        self.after(0, _done)
                        return

                    elif status in ("failed","error"):
                        raise ValueError(pdata.get("error", st.get("error","Generation failed")))

                raise TimeoutError("Timed out after 15 minutes.")

            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8","replace")
                try: msg = json.loads(body).get("message", body[:200])
                except: msg = body[:200]
                def _err(m=f"HTTP {e.code}: {msg}"):
                    safe_cfg(self._ws_gen_btn, state="normal", text="🌊  Generate Video")
                    safe_cfg(self._ws_progress_lbl, text=f"❌ {m[:160]}", fg=A2)
                    self._ws_progress_bar.config(value=0)
                    Toast.show(self, m[:100], "error", 8000)
                self.after(0, _err)
            except Exception as ex:
                def _err(m=str(ex)):
                    safe_cfg(self._ws_gen_btn, state="normal", text="🌊  Generate Video")
                    safe_cfg(self._ws_progress_lbl, text=f"❌ {m[:160]}", fg=A2)
                    self._ws_progress_bar.config(value=0)
                    Toast.show(self, m[:100], "error", 8000)
                self.after(0, _err)

        threading.Thread(target=_go, daemon=True).start()

    def _save_ws_video(self):
        if not self._ws_video_bytes:
            Toast.show(self.winfo_toplevel(), "No video to save yet!", "warn"); return
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 Video","*.mp4"),("All Files","*.*")],
            title="Save WaveSpeed Video")
        if not path: return
        with open(path,"wb") as f: f.write(self._ws_video_bytes)
        Toast.show(self.winfo_toplevel(), f"Saved: {os.path.basename(path)}", "success")

    def _reset_wavespeed(self):
        self._ws_video_bytes = None
        safe_cfg(self._ws_gen_btn, state="normal", text="🌊  Generate Video")
        safe_cfg(self._ws_save_btn, state="disabled")
        safe_cfg(self._ws_reset_btn, state="disabled")
        safe_cfg(self._ws_result_lbl, text="", fg=MUTED)
        safe_cfg(self._ws_progress_lbl, text="", fg=MUTED)
        try: self._ws_progress_bar.config(value=0)
        except Exception: pass
        try: self._ws_prompt.delete("1.0","end")
        except Exception: pass
        Toast.show(self.winfo_toplevel(), "Ready for a new WaveSpeed video!", "info")

    def _reset_sora(self):
        self._sora_video_bytes = None
        safe_cfg(self._sora_gen_btn, state="normal",
                 text="🎬  Generate Video with Sora")
        safe_cfg(self._sora_save_btn, state="disabled")
        safe_cfg(self._sora_reset_btn, state="disabled")
        safe_cfg(self._sora_result_lbl, text="", fg=MUTED)
        safe_cfg(self._sora_progress_lbl, text="", fg=MUTED)
        try: self._sora_progress_bar.config(value=0)
        except Exception: pass
        try: self._sora_prompt.delete("1.0", "end")
        except Exception: pass
        Toast.show(self.winfo_toplevel(), "Ready to generate a new Sora video!", "info")

    def _reset_analyse(self):
        safe_cfg(self._analyse_btn, state="normal", text="✦  Analyse Image")
        safe_cfg(self._status_lbl, text="Ready — upload an image and run analysis", fg=MUTED)
        self._img_data = None
        self._img_mime = None
        safe_cfg(self._img_name_lbl, text="", fg=MUTED)
        try:
            cv = self._thumb_cv
            cv.delete("all")
            cv.create_oval(140,30,200,90, fill=SEL, outline=ACCENT, width=2)
            cv.create_text(170,60, text="📷", font=("Helvetica",22), fill=ACCENT)
            cv.create_text(170,108, text="Click · Drag & Drop · Ctrl+V",
                           fill=MUTED, font=("Helvetica",9))
        except Exception: pass
        Toast.show(self.winfo_toplevel(), "Analyse panel cleared!", "info")

    def _reset_edit(self):
        try: self._edit_req.delete("1.0", "end")
        except Exception: pass
        try:
            self._edit_canvas.delete("all")
            self._edit_canvas.create_text(170, 110,
                text="Generated image will appear here",
                fill=MUTED, font=F["xs"], width=300)
        except Exception: pass
        safe_cfg(self._edit_save_btn, state="disabled")
        safe_cfg(self._prompt_btn, state="normal",
                 text="🖼  Generate Edited Image")
        self._edit_image_data = None
        Toast.show(self.winfo_toplevel(), "Ready for a new image edit!", "info")

    def _reset_anim(self):
        try:
            self._anim_req.delete("1.0", "end")
            self._anim_req.insert("1.0", "Make the wrestler burst forward with slow-motion energy.")
        except Exception: pass
        safe_cfg(self._anim_btn, state="normal",
                 text="🎬  Generate Animation Plan")
        Toast.show(self.winfo_toplevel(), "Animation planner reset!", "info")

    def _reset_imagegen(self):
        try: self._hf_prompt.delete("1.0", "end")
        except Exception: pass
        try: self._hf_neg.delete("1.0", "end")
        except Exception: pass
        safe_cfg(self._hf_save_btn, state="disabled")
        safe_cfg(self._hf_add_btn, state="disabled")
        try:
            self._hf_canvas.delete("all")
            self._hf_canvas.create_text(160, 100,
                text="Generated image will appear here",
                fill=MUTED, font=F["xs"])
        except Exception: pass
        self._hf_image_data = None
        Toast.show(self.winfo_toplevel(), "Ready to generate a new image!", "info")

    def _save_sora_video(self):
        if not self._sora_video_bytes:
            messagebox.showinfo("Nothing to Save","Generate a video first.")
            return
        p = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            initialfile="sora_video.mp4",
            filetypes=[("MP4 Video","*.mp4"),("All","*.*")],
            title="Save Sora Video")
        if p:
            with open(p,"wb") as f:
                f.write(self._sora_video_bytes)
            self._set_status(f"✅ Saved: {os.path.basename(p)}", GREEN)
            messagebox.showinfo("Saved!", f"Video saved to:\n{p}")

    # ── Hugging Face Image Generation ────────────────────────────────
    def _set_hf_style(self, style):
        self._hf_style_v.set(style)
        for btn_w in self._hf_style_btns_frame.winfo_children():
            if isinstance(btn_w, tk.Button):
                sel = btn_w.cget("text") == style
                safe_cfg(btn_w,bg=ACCENT if sel else CARD,
                             fg=WHITE if sel else TEXT)

    def _run_hf_imagegen(self):
        """Generate images using Pollinations.AI — no API key needed, truly free."""
        import urllib.parse

        prompt   = self._hf_prompt.get("1.0","end").strip()
        style    = self._hf_style_v.get()
        size_str = self._hf_size_v.get()
        num_imgs = self._hf_num_v.get()

        if not prompt:
            messagebox.showwarning("No Prompt", "Enter a prompt first."); return

        style_tags = {
            "Photorealistic": ", photorealistic, ultra detailed, 8k photography",
            "Cinematic":      ", cinematic lighting, movie still, anamorphic lens",
            "Digital Art":    ", digital art, concept art, artstation trending",
            "Oil Painting":   ", oil painting, impressionist, thick brushstrokes",
            "Watercolor":     ", watercolor painting, soft colors, paper texture",
            "Anime":          ", anime style, studio ghibli, cel shaded",
            "Sketch":         ", pencil sketch, hand drawn, detailed linework",
            "3D Render":      ", 3D render, octane render, blender, subsurface scattering",
            "Vintage":        ", vintage photo, film grain, faded colors, retro",
            "Neon":           ", neon lights, cyberpunk, glowing, dark background",
            "Fantasy":        ", fantasy art, magical, ethereal, epic lighting",
        }
        full_prompt = prompt + style_tags.get(style, "")

        try:
            w_str, h_str = size_str.split("x")
            img_w, img_h = int(w_str), int(h_str)
        except Exception:
            img_w, img_h = 512, 512

        safe_cfg(self._hf_gen_btn,state="disabled", text="Generating…")
        self._set_status("Generating via Pollinations.AI — no key needed…", WARN)

        def _go():
            generated = []
            for i in range(num_imgs):
                try:
                    self.after(0, lambda n=i+1, t=num_imgs:
                        self._set_status(f"Generating image {n}/{t} via Pollinations…", WARN))
                    # Add a seed variation per image so each is unique
                    import random
                    seed = random.randint(1, 999999)
                    encoded = urllib.parse.quote(full_prompt)
                    url = (f"https://image.pollinations.ai/prompt/{encoded}"
                           f"?width={img_w}&height={img_h}"
                           f"&nologo=true&enhance=true&seed={seed}")
                    req = urllib.request.Request(url,
                        headers={"User-Agent": "VideoEditor/3.0"})
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        raw = resp.read()
                    img = Image.open(io.BytesIO(raw)).convert("RGB")
                    generated.append(img)
                except Exception as ex:
                    self.after(0, lambda m=str(ex): (
                        self._set_status(f"❌ {m[:80]}", A2),
                        messagebox.showerror("Generation Failed",
                            f"Pollinations error: {m}\n\n"
                            "Check your internet connection and try again.")))
                    return

            self.after(0, lambda imgs=generated: self._display_hf_images(imgs))

        threading.Thread(target=_go, daemon=True).start()

    def _display_hf_images(self, imgs):
        """Show generated PIL images in the panel."""
        self._hf_generated_imgs = imgs
        safe_cfg(self._hf_gen_btn,state="normal", text="🎨  Generate Image")
        # clear old
        for w in self._hf_img_frame.winfo_children():
            w.destroy()
        self._hf_photo_refs.clear()

        for i, img in enumerate(imgs):
            # thumbnail for display
            disp = img.copy()
            disp.thumbnail((300, 300), Image.LANCZOS)
            photo = ImageTk.PhotoImage(disp)
            self._hf_photo_refs.append(photo)
            tk.Label(self._hf_img_frame, image=photo, bg=CARD).pack(pady=4)
            tk.Label(self._hf_img_frame,
                     text=f"Image {i+1}  —  {img.width}×{img.height}",
                     bg=CARD, fg=MUTED, font=F["xs"]).pack()

        safe_cfg(self._hf_save_btn,state="normal")
        safe_cfg(self._hf_add_btn,state="normal")
        self._set_status(f"✅ {len(imgs)} image(s) generated! Hit Save to download.", GREEN)

    def _save_hf_image(self):
        if not self._hf_generated_imgs:
            messagebox.showinfo("Nothing to Save", "Generate an image first."); return
        for i, img in enumerate(self._hf_generated_imgs):
            suffix = f"_{i+1}" if len(self._hf_generated_imgs) > 1 else ""
            p = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=f"ai_generated{suffix}.png",
                filetypes=[("PNG","*.png"),("JPEG","*.jpg"),("All","*.*")],
                title=f"Save Image {i+1}")
            if p:
                img.save(p)
                self._set_status(f"✅ Saved: {os.path.basename(p)}", GREEN)

    # ── AI Background Remover ────────────────────────────────────────
    def _remove_background(self):
        if not PIL_AVAILABLE:
            messagebox.showwarning("Missing","Pillow required."); return
        if not self._img_path or not os.path.exists(self._img_path):
            messagebox.showwarning("No Image","Upload an image first using the button above.")
            return
        safe_cfg(self._bg_rm_btn,state="disabled", text="Removing…")
        self._set_status("Removing background using PIL color segmentation…", WARN)

        def _go():
            try:
                img = Image.open(self._img_path).convert("RGBA")
                iw, ih = img.size
                # Simple background removal: make near-white/near-black pixels transparent
                data = img.load()
                # Sample corner pixels as "background" color
                corners = [(0,0),(iw-1,0),(0,ih-1),(iw-1,ih-1)]
                bg_samples = [data[x,y][:3] for x,y in corners]
                bg_r = sum(c[0] for c in bg_samples)//4
                bg_g = sum(c[1] for c in bg_samples)//4
                bg_b = sum(c[2] for c in bg_samples)//4
                threshold = 60
                for y in range(ih):
                    for x in range(iw):
                        r,g,b,a = data[x,y]
                        diff = abs(r-bg_r)+abs(g-bg_g)+abs(b-bg_b)
                        if diff < threshold:
                            data[x,y] = (r,g,b,0)
                # Also remove any near-white background
                for y in range(ih):
                    for x in range(iw):
                        r,g,b,a = data[x,y]
                        if a > 0 and r>220 and g>220 and b>220:
                            data[x,y] = (r,g,b,0)
                self._bg_rm_result = img

                def _show(i=img):
                    disp = i.copy(); disp.thumbnail((340,180),Image.LANCZOS)
                    # Show on checkered background
                    check = Image.new("RGB",(disp.width,disp.height))
                    for cy in range(0,disp.height,10):
                        for cx in range(0,disp.width,10):
                            col = (200,200,200) if (cx//10+cy//10)%2==0 else (255,255,255)
                            for py in range(min(10,disp.height-cy)):
                                for px in range(min(10,disp.width-cx)):
                                    check.putpixel((cx+px,cy+py),col)
                    check.paste(disp,(0,0),disp)
                    photo = ImageTk.PhotoImage(check)
                    self._bg_rm_photo = photo
                    self._bg_rm_canvas.delete("all")
                    safe_cfg(self._bg_rm_canvas,width=disp.width, height=disp.height)
                    self._bg_rm_canvas.create_image(
                        disp.width//2, disp.height//2,
                        anchor="center", image=self._bg_rm_photo)
                    safe_cfg(self._bg_rm_btn,state="normal", text="✂  Remove Background")
                    self._set_status("✅ Background removed! Hit Save to download.", GREEN)
                self.after(50, _show)
            except Exception as ex:
                self.after(0, lambda m=str(ex): (
                    safe_cfg(self._bg_rm_btn,state="normal", text="✂  Remove Background"),
                    self._set_status(f"Error: {m[:60]}", A2)))

        threading.Thread(target=_go, daemon=True).start()

    def _save_bg_removed(self):
        if not self._bg_rm_result:
            messagebox.showinfo("Nothing to Save","Remove background first."); return
        p = filedialog.asksaveasfilename(
            defaultextension=".png", initialfile="no_background.png",
            filetypes=[("PNG (supports transparency)","*.png"),("All","*.*")])
        if p:
            self._bg_rm_result.save(p)
            self._set_status(f"✅ Saved: {os.path.basename(p)}", GREEN)

    # ── AI Auto-Caption (Whisper) ─────────────────────────────────────
    def _run_autocaption(self):
        clip = self._get_clip()
        if not clip:
            messagebox.showwarning("No Clip","Select a video clip in the timeline first.")
            return
        if clip.is_image:
            messagebox.showwarning("Video Only","Auto-caption only works on video clips.")
            return
        key = _SETTINGS.get("openai_api_key","").strip()
        if not key:
            messagebox.showwarning("OpenAI Key Required",
                "Auto-caption uses OpenAI Whisper.\nEnter your OpenAI key in Settings.")
            return
        safe_cfg(self._caption_btn,state="disabled", text="Transcribing…")
        self._set_status("Sending audio to OpenAI Whisper…", WARN)

        def _go():
            try:
                # Extract audio from video using moviepy
                if not MOVIEPY_AVAILABLE:
                    raise RuntimeError("MoviePy required for audio extraction.")
                import tempfile
                vc = VideoFileClip(clip.path)
                audio = vc.audio
                if not audio:
                    raise RuntimeError("No audio track found in this clip.")
                # Save audio to temp MP3
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                    tmp_path = tf.name
                audio.write_audiofile(tmp_path, logger=None)
                vc.close()

                # Send to Whisper API
                with open(tmp_path,"rb") as af:
                    audio_bytes = af.read()
                os.unlink(tmp_path)

                boundary = "----WhisperBoundary"
                body  = f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nwhisper-1\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\nverbose_json\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"timestamp_granularities[]\"\r\n\r\nword\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audio.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode()
                body += audio_bytes
                body += f"\r\n--{boundary}--\r\n".encode()

                req = urllib.request.Request(
                    "https://api.openai.com/v1/audio/transcriptions",
                    data=body,
                    headers={"Authorization": f"Bearer {key}",
                             "Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST")
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                # Extract segments and create overlays
                segments = result.get("segments", [])
                if not segments:
                    # Fallback: use full text as single overlay
                    text = result.get("text","").strip()
                    if text:
                        segments = [{"start":0,"end":clip.trimmed,"text":text}]

                def _apply(segs=segments):
                    added = 0
                    for seg in segs:
                        ov = Overlay()
                        ov.content = seg.get("text","").strip()
                        ov.size    = 24
                        ov.bold    = False
                        ov.color   = "#FFFFFF"
                        ov.x       = 0.5
                        ov.y       = 0.90
                        ov.start   = round(float(seg.get("start",0)), 2)
                        ov.end     = round(float(seg.get("end", clip.trimmed)), 2)
                        if ov.content:
                            clip.overlays.append(ov)
                            added += 1
                    self._on_change()
                    safe_cfg(self._caption_btn,state="normal", text="🎤  Generate Captions")
                    self._set_status(f"✅ {added} caption segments added to clip!", GREEN)
                    messagebox.showinfo("Captions Added!",
                        f"{added} caption overlays added to {clip.filename}.\n\n"
                        "You can see and drag them in the Preview panel.")
                self.after(0, _apply)

            except urllib.error.HTTPError as e:
                body_txt = e.read().decode("utf-8", errors="replace")
                try: msg = json.loads(body_txt).get("error",{}).get("message", body_txt[:200])
                except: msg = body_txt[:200]
                self.after(0, lambda m=msg, c=e.code: (
                    safe_cfg(self._caption_btn,state="normal", text="🎤  Generate Captions"),
                    self._set_status(f"❌ HTTP {c}: {m[:60]}", A2),
                    messagebox.showerror("Caption Failed", f"HTTP {c}: {m}")))
            except Exception as ex:
                import traceback; traceback.print_exc()
                self.after(0, lambda m=str(ex): (
                    safe_cfg(self._caption_btn,state="normal", text="🎤  Generate Captions"),
                    self._set_status(f"❌ {m[:60]}", A2),
                    messagebox.showerror("Error", m)))

        threading.Thread(target=_go, daemon=True).start()

    # ── display analyse results ──────────────────────────────────────
    def _display_analyse_results(self, result):
        """Render the JSON analysis result into the results panel clearly."""
        # Update _result_lbl in place — never destroy it
        subject = result.get("subject_detection", "")
        vibe    = result.get("image_vibe", "")
        palette = result.get("color_palette", [])

        # Clear only the dynamic content frame inside result_card, not _result_lbl
        for w in self._result_card.winfo_children():
            if w is not self._result_lbl:
                w.destroy()
        safe_cfg(self._result_lbl,text="", fg=TEXT)

        if subject:
            tk.Label(self._result_card,
                     text=f"📸  {subject}",
                     bg=CARD, fg=TEXT, font=F["sm"],
                     wraplength=340, justify="left",
                     pady=4, padx=8).pack(anchor="w")
        if vibe:
            tk.Label(self._result_card,
                     text=f"🎨  Vibe: {vibe}",
                     bg=CARD, fg=ACCENT, font=F["sm"],
                     pady=2, padx=8).pack(anchor="w")
        if palette:
            pf = tk.Frame(self._result_card, bg=CARD)
            pf.pack(anchor="w", padx=8, pady=4)
            tk.Label(pf, text="Colors:", bg=CARD, fg=MUTED,
                     font=F["xs"]).pack(side="left")
            for hex_col in palette[:6]:
                try:
                    swatch = tk.Frame(pf, bg=hex_col, width=20, height=20,
                                      highlightthickness=1,
                                      highlightbackground=BORDER)
                    swatch.pack(side="left", padx=2)
                    safe_pp(swatch)
                except Exception:
                    pass

        # ── editing steps ─────────────────────────────────────────────
        for w in self._steps_frame.winfo_children(): w.destroy()

        steps = result.get("editing_steps", [])
        if steps:
            tk.Label(self._steps_frame,
                     text="RECOMMENDED EDITS",
                     bg=WHITE, fg=MUTED, font=F["xs"]).pack(anchor="w", pady=(6,2))
            priority_colors = {"high": A2, "medium": WARN, "low": GREEN}
            for step in steps[:6]:
                action   = step.get("action", "")
                desc     = step.get("description", "")
                priority = step.get("priority", "medium").lower()
                color    = priority_colors.get(priority, MUTED)

                row = tk.Frame(self._steps_frame, bg=CARD,
                               highlightthickness=1, highlightbackground=BORDER)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"  {action}",
                         bg=CARD, fg=TEXT, font=F["sm"],
                         anchor="w").pack(side="left", padx=4, pady=4)
                tk.Label(row, text=priority.upper(),
                         bg=color, fg=WHITE, font=F["xs"],
                         padx=6, pady=2).pack(side="right", padx=4, pady=4)
                if desc:
                    tk.Label(self._steps_frame,
                             text=f"   → {desc}",
                             bg=WHITE, fg=MUTED, font=F["xs"],
                             wraplength=330, justify="left",
                             anchor="w").pack(fill="x", padx=4)

        # ── design overlay suggestions ────────────────────────────────
        overlay = result.get("design_overlay", {})
        headline = overlay.get("headline_text", "")
        subhead  = overlay.get("subheadline_text", "")
        cta      = overlay.get("cta_button_text", "")
        font_sug = overlay.get("suggested_font", "")
        layout   = overlay.get("layout_template", "")

        if any([headline, subhead, cta, font_sug, layout]):
            tk.Label(self._steps_frame,
                     text="DESIGN OVERLAY SUGGESTIONS",
                     bg=WHITE, fg=MUTED, font=F["xs"]).pack(anchor="w", pady=(10,2))
            ov_card = tk.Frame(self._steps_frame, bg=SEL,
                               highlightthickness=1, highlightbackground=ACCENT)
            ov_card.pack(fill="x", pady=2)
            rows = []
            if headline:  rows.append(("Headline",  headline))
            if subhead:   rows.append(("Subhead",   subhead))
            if cta:       rows.append(("CTA",       cta))
            if font_sug:  rows.append(("Font",      font_sug))
            if layout:    rows.append(("Layout",    layout))
            for label, val in rows:
                r = tk.Frame(ov_card, bg=SEL); r.pack(fill="x", padx=8, pady=1)
                tk.Label(r, text=f"{label}:", bg=SEL, fg=MUTED,
                         font=F["xs"], width=8, anchor="w").pack(side="left")
                tk.Label(r, text=val, bg=SEL, fg=TEXT,
                         font=F["sm"], wraplength=260,
                         justify="left", anchor="w").pack(side="left")

        # ── canva template ────────────────────────────────────────────
        canva = result.get("canva_template", "")
        if canva:
            tk.Label(self._steps_frame,
                     text="CANVA TEMPLATE IDEA",
                     bg=WHITE, fg=MUTED, font=F["xs"]).pack(anchor="w", pady=(10,2))
            tk.Label(self._steps_frame,
                     text=canva,
                     bg=CARD, fg=TEXT, font=F["xs"],
                     wraplength=340, justify="left",
                     pady=6, padx=8).pack(fill="x", pady=2)

        # ── full JSON in output box ───────────────────────────────────
        self._set_output(json.dumps(result, indent=2))
        # Update the persistent result label — it is never destroyed
        try:
            safe_cfg(self._result_lbl,
                text=f"✅ Analysis complete — {len(steps)} edit suggestions found.",
                fg=GREEN)
        except Exception:
            pass

        # ── render PIL-edited preview image ───────────────────────────
        self._render_ai_preview(result)

    # ── AI image preview & save ──────────────────────────────────────
    def _render_ai_preview(self, result):
        """Apply AI edits to the uploaded image using PIL and show in panel."""
        if not PIL_AVAILABLE:
            self._set_status("PIL (Pillow) not installed.", A2)
            return
        if not self._img_path or not os.path.exists(self._img_path):
            self._set_status("No image uploaded — use Upload Image first.", A2)
            return

        # Run everything directly on main thread — safest for ImageTk
        def _do_render():
            try:
                img = Image.open(self._img_path).convert("RGB")

                # 1. Apply filter from vibe
                vibe = result.get("image_vibe","").lower()
                filter_map = {
                    "warm":"Warm","sunset":"Warm","golden":"Warm",
                    "cool":"Cool","cold":"Cool","blue":"Cool",
                    "retro":"Sepia","vintage":"Sepia","old":"Sepia",
                    "monochrome":"B&W","noir":"Noir",
                    "vivid":"Vivid","vibrant":"Vivid","colorful":"Vivid",
                    "dark":"Noir","moody":"Matte","fade":"Fade","matte":"Matte",
                    "chrome":"Chrome",
                }
                chosen_filter = "None"
                for kw, flt in filter_map.items():
                    if kw in vibe:
                        chosen_filter = flt
                        break
                img = pil_filter(img, chosen_filter)

                # 2. Apply adjustments from editing steps
                steps = result.get("editing_steps", [])
                brightness = 1.0
                contrast   = 1.0
                saturation = 1.0
                for step in steps:
                    action = step.get("action","").lower()
                    if any(k in action for k in ["upscale","sharpen","clarity","enhance"]):
                        contrast   = min(2.0, contrast + 0.15)
                        brightness = min(2.0, brightness + 0.05)
                    if any(k in action for k in ["color grade","colour grade","grade","lut"]):
                        saturation = min(2.0, saturation + 0.25)
                    if any(k in action for k in ["fade","soften","matte"]):
                        brightness = min(2.0, brightness + 0.08)
                        contrast   = max(0.2, contrast - 0.1)
                    if any(k in action for k in ["bright","exposure","light"]):
                        brightness = min(2.0, brightness + 0.1)

                img = ImageEnhance.Brightness(img).enhance(brightness)
                img = ImageEnhance.Contrast(img).enhance(contrast)
                img = ImageEnhance.Color(img).enhance(saturation)

                # 3. Draw text overlays
                overlay   = result.get("design_overlay", {})
                headline  = overlay.get("headline_text","")
                sub       = overlay.get("subheadline_text","")
                cta       = overlay.get("cta_button_text","")
                placement = overlay.get("text_placement","bottom")
                colors    = overlay.get("color_scheme",["#FFFFFF","#FFD700"])

                if any([headline, sub, cta]):
                    draw = ImageDraw.Draw(img)
                    iw, ih = img.size
                    top = "top" in placement.lower()

                    def hex_to_rgb(hx):
                        hx = hx.lstrip("#")
                        try:
                            return tuple(int(hx[i:i+2],16) for i in (0,2,4))
                        except Exception:
                            return (255,255,255)

                    c1 = hex_to_rgb(colors[0]) if colors else (255,255,255)
                    c2 = hex_to_rgb(colors[1]) if len(colors)>1 else (255,215,0)

                    def draw_text(text, y_frac, color):
                        y = int(ih * y_frac)
                        # shadow
                        draw.text((iw//2+2, y+2), text,
                                  fill=(0,0,0), anchor="mm")
                        draw.text((iw//2, y), text,
                                  fill=color, anchor="mm")

                    if headline:
                        draw_text(headline, 0.10 if top else 0.75, c1)
                    if sub:
                        draw_text(sub, 0.18 if top else 0.84, (220,220,220))
                    if cta:
                        draw_text(cta, 0.91, c2)

                # 4. Store full-res edited image for saving
                self._edited_pil_img = img.copy()

                # 5. Build display thumbnail as raw bytes (PIL only, no ImageTk yet)
                thumb = img.copy()
                max_w, max_h = 340, 260
                thumb.thumbnail((max_w, max_h), Image.LANCZOS)
                bg_img = Image.new("RGB", (max_w, max_h), (17, 24, 39))
                x_off = (max_w - thumb.width)  // 2
                y_off = (max_h - thumb.height) // 2
                bg_img.paste(thumb, (x_off, y_off))
                # Keep PIL image ref to convert on main thread
                display_img = bg_img

                # 6. Schedule display on main thread
                def _show(di=display_img, mw=max_w, mh=max_h,
                          cf=chosen_filter, br=brightness, co=contrast):
                    try:
                        print(f"[PREVIEW] Creating photo {mw}x{mh}, PIL size={di.size}")
                        photo = ImageTk.PhotoImage(di)
                        print(f"[PREVIEW] Photo created: {photo}")
                        self._ai_preview_photo = photo
                        print(f"[PREVIEW] Canvas: {self._ai_canvas}, winfo_id={self._ai_canvas.winfo_id()}")
                        self._ai_canvas.delete("all")
                        safe_cfg(self._ai_canvas,width=mw, height=mh)
                        img_id = self._ai_canvas.create_image(
                            mw // 2, mh // 2,
                            anchor="center",
                            image=self._ai_preview_photo)
                        print(f"[PREVIEW] Image placed, canvas item id={img_id}")
                        self._ai_canvas.update()
                        print(f"[PREVIEW] Canvas updated, items={self._ai_canvas.find_all()}")
                        safe_cfg(self._save_edit_btn,state="normal")
                        self._set_status(
                            f"✅ Done! Filter={cf} — scroll UP to see preview.",
                            GREEN)
                    except Exception as show_ex:
                        import traceback
                        print("[SHOW ERROR]", traceback.format_exc())
                        self._set_status(f"Display error: {show_ex}", A2)
                self.after(50, _show)

            except Exception as ex:
                import traceback
                print("[RENDER ERROR]", traceback.format_exc())
                self.after(0, lambda e=str(ex): self._set_status(
                    f"Render error: {e}", A2))

        # Use after(10) to run on main thread with slight delay so
        # the API response UI updates first
        self.after(10, _do_render)

    def _save_edited_image(self):
        """Save the PIL-edited image to disk."""
        if not self._edited_pil_img:
            messagebox.showinfo("Nothing to Save",
                "Run an analysis first to generate the edited image.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile="ai_edited_image.png",
            filetypes=[("PNG","*.png"),("JPEG","*.jpg"),("All","*.*")],
            title="Save AI Edited Image")
        if path:
            self._edited_pil_img.save(path)
            self._set_status(f"✅ Saved: {os.path.basename(path)}", GREEN)
            messagebox.showinfo("Saved!", "AI edited image saved to:\n" + path)

    # ── copy & apply ──────────────────────────────────────────────────
    def _copy_output(self):
        content = self._out_text.get("1.0","end").strip()
        if not content or content.startswith("Results will"):
            messagebox.showinfo("Nothing to Copy","Run an analysis first."); return
        self.clipboard_clear()
        self.clipboard_append(content)
        self._set_status("✅  Copied to clipboard!", GREEN)

    def _apply_to_clip(self):
        clip   = self._get_clip()
        result = self._last_result
        if not clip:
            messagebox.showinfo("No Clip",
                "Select a clip in the timeline first, then click Apply to Clip."); return
        if not result:
            messagebox.showinfo("No Results","Run an analysis first."); return

        applied = []

        # ── 1. Map vibe → filter ───────────────────────────────────────
        vibe = result.get("image_vibe","").lower()
        filter_map = {
            "warm":"Warm","sunset":"Warm","golden":"Warm",
            "cold":"Cool","cool":"Cool","blue":"Cool",
            "vintage":"Sepia","retro":"Sepia","old":"Sepia",
            "black":"B&W","monochrome":"B&W","noir":"Noir",
            "vivid":"Vivid","vibrant":"Vivid","colorful":"Vivid",
            "dark":"Noir","moody":"Matte","fade":"Fade","matte":"Matte",
            "chrome":"Chrome",
        }
        chosen_filter = "None"
        for kw, flt in filter_map.items():
            if kw in vibe:
                chosen_filter = flt
                break
        clip.filter = chosen_filter
        if chosen_filter != "None":
            applied.append(f"Filter → {chosen_filter}  (from vibe: {vibe})")

        # ── 2. Map editing_steps → PIL adjustments ────────────────────
        steps = result.get("editing_steps", [])
        for step in steps:
            action = step.get("action","").lower()
            # brightness / exposure boost
            if any(k in action for k in ["upscale","sharpen","clarity","enhance"]):
                clip.contrast   = min(2.0, clip.contrast + 0.15)
                clip.brightness = min(2.0, clip.brightness + 0.05)
                applied.append(f"Contrast +15%, Brightness +5%  (from: {step.get('action','')})")
            # color grade
            if any(k in action for k in ["color grade","colour grade","grade","lut"]):
                clip.saturation = min(2.0, clip.saturation + 0.2)
                applied.append(f"Saturation +20%  (from: {step.get('action','')})")
            # fade / soften
            if any(k in action for k in ["fade","soften","matte"]):
                clip.brightness = min(2.0, clip.brightness + 0.08)
                clip.contrast   = max(0.2, clip.contrast - 0.1)
                applied.append(f"Soft fade applied  (from: {step.get('action','')})")

        # ── 3. Apply text overlays from design_overlay ────────────────
        overlay   = result.get("design_overlay", {})
        headline  = overlay.get("headline_text","")
        sub       = overlay.get("subheadline_text","")
        cta       = overlay.get("cta_button_text","")
        placement = overlay.get("text_placement","bottom")
        colors    = overlay.get("color_scheme", ["#FFFFFF","#FFD700"])

        # clear old AI-generated overlays before re-applying
        clip.overlays = [o for o in clip.overlays if not getattr(o,"_ai_generated",False)]

        def make_ov(text, size, bold, color, y):
            o = Overlay()
            o.content = text; o.size = size; o.bold = bold
            o.color = color; o.x = 0.5; o.y = y
            o.end = clip.trimmed
            o._ai_generated = True
            return o

        top = "top" in placement.lower()
        if headline:
            clip.overlays.append(make_ov(headline, 46, True,
                colors[0] if colors else "#FFFFFF",
                0.12 if top else 0.76))
            applied.append("Headline: " + headline[:35])

        if sub:
            clip.overlays.append(make_ov(sub, 26, False, "#EEEEEE",
                0.20 if top else 0.86))
            applied.append("Subhead: " + sub[:35])

        if cta:
            clip.overlays.append(make_ov(cta, 24, True,
                colors[1] if len(colors)>1 else "#FFD700", 0.93))
            applied.append("CTA: " + cta[:35])

        # ── 4. Trigger preview update ──────────────────────────────────
        self._on_change()

        # ── 5. Show summary ────────────────────────────────────────────
        if applied:
            summary = "\n".join("• " + a for a in applied)
            messagebox.showinfo("✅ Applied to Clip!",
                f"Changes applied to: {clip.filename}\n\n"
                f"{summary}\n\n"
                "The preview has been updated. "
                "Use the Inspector panel to fine-tune any setting.")
        else:
            messagebox.showinfo("Nothing to Apply",
                "The analysis didn't find clear edit suggestions.\n"
                "Try running Analyse & Apply again with a more specific request.")


# ══════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════
# TOAST NOTIFICATION SYSTEM
# ══════════════════════════════════════════════════════════════════════
class Toast:
    """Slide-in toast notification that auto-dismisses."""
    _active = []

    @classmethod
    def show(cls, root, message, kind="info", duration=3000):
        """Show a toast. kind = 'info' | 'success' | 'error' | 'warn'"""
        colors = {
            "success": ("#10B981", "✅"),
            "error":   ("#EF4444", "❌"),
            "warn":    ("#F59E0B", "⚠"),
            "info":    ("#6366F1", "✦"),
        }
        accent, icon = colors.get(kind, colors["info"])

        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="#1E2235")

        # Position bottom-right
        root.update_idletasks()
        rw = root.winfo_width(); rh = root.winfo_height()
        rx = root.winfo_rootx(); ry = root.winfo_rooty()
        # Stack multiple toasts
        offset = len([t for t in cls._active if t.winfo_exists()]) * 58
        win.geometry(f"340x48+{rx+rw-354}+{ry+rh-64-offset}")

        # Border accent line
        tk.Frame(win, bg=accent, width=3).pack(side="left", fill="y")
        inner = tk.Frame(win, bg="#1E2235"); inner.pack(side="left", fill="both",
                                                         expand=True, padx=10, pady=10)
        tk.Label(inner, text=f"{icon}  {message}", bg="#1E2235", fg="#F1F5F9",
                 font=("Helvetica", 10), anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(inner, text="✕", bg="#1E2235", fg="#64748B",
                  relief="flat", bd=0, cursor="hand2", font=("Helvetica", 10),
                  command=lambda: cls._dismiss(win)).pack(side="right")

        cls._active.append(win)

        # Animate in (slide from right)
        def _slide_in(step=0):
            if not win.winfo_exists(): return
            if step < 10:
                x = rx + rw - 354 + int((10-step)*20)
                win.geometry(f"340x48+{x}+{ry+rh-64-offset}")
                win.after(20, lambda: _slide_in(step+1))
        _slide_in()

        # Auto dismiss
        win.after(duration, lambda: cls._dismiss(win))

    @classmethod
    def _dismiss(cls, win):
        try:
            if win.winfo_exists():
                win.destroy()
            if win in cls._active:
                cls._active.remove(win)
        except Exception:
            pass


class App(ctk.CTk if CTK_AVAILABLE else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ProEdit Studio — AI Video Editor")
        self.geometry("1600x900")
        self.minsize(1050,650)
        if CTK_AVAILABLE:
            ctk.set_appearance_mode("dark")
        else:
            self.configure(bg=BG)
        self._proj       = Project()
        self._sel        = None
        self._undo_stack = []
        self._redo_stack = []
        self._setup_styles()
        self._show_splash()
        self._build()
        self._bind_keys()
        self._check_deps()
        self._start_autosave()

    def _show_splash(self):
        """Animated splash screen on startup."""
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.configure(bg="#080A12")
        sw, sh = 420, 260
        # Centre on screen
        self.update_idletasks()
        sx = (self.winfo_screenwidth()-sw)//2
        sy = (self.winfo_screenheight()-sh)//2
        splash.geometry(f"{sw}x{sh}+{sx}+{sy}")
        splash.lift(); splash.attributes("-topmost", True)

        # Logo
        tk.Label(splash, text="✦", bg="#080A12", fg=ACCENT,
                 font=("Helvetica",52,"bold")).pack(pady=(40,6))
        tk.Label(splash, text="ProEdit Studio", bg="#080A12", fg=TEXT,
                 font=("Helvetica",22,"bold")).pack()
        tk.Label(splash, text="AI Video Editor", bg="#080A12", fg=MUTED,
                 font=("Helvetica",11)).pack(pady=2)

        # Progress bar
        pb_bg = tk.Frame(splash, bg="#1A1D27", height=3, width=300)
        pb_bg.pack(pady=24)
        pb_bg.pack_propagate(False)
        pb_fill = tk.Frame(pb_bg, bg=ACCENT, height=3, width=0)
        pb_fill.pack(side="left", fill="y")

        status_lbl = tk.Label(splash, text="Initializing…", bg="#080A12",
                               fg=MUTED, font=("Helvetica",9))
        status_lbl.pack()

        steps = [
            (25,  "Loading components…"),
            (50,  "Setting up AI features…"),
            (75,  "Preparing workspace…"),
            (100, f"Welcome to {APP_NAME} {APP_VERSION}!"),
        ]

        def _animate(i=0):
            if i >= len(steps):
                splash.after(300, splash.destroy)
                return
            pct, msg = steps[i]
            pb_fill.config(width=int(300 * pct/100))
            status_lbl.config(text=msg)
            splash.after(400, lambda: _animate(i+1))

        splash.after(100, _animate)
        splash.after(2500, splash.destroy)
        self.wait_window(splash)

    def _setup_styles(self):
        s=ttk.Style(self); s.theme_use("clam")
        s.configure("TScrollbar",background=BORDER,troughcolor=BG,
                     bordercolor=BG,arrowcolor=MUTED,relief="flat")
        s.configure("E.Horizontal.TProgressbar",
                     troughcolor=BORDER,background=ACCENT,bordercolor=BG)

    def _build(self):
        # ── Menu Bar (Premiere-style) ─────────────────────────────────
        menubar = tk.Frame(self, bg="#05060D", height=22)
        menubar.pack(fill="x"); safe_pp(menubar)
        tk.Frame(self, bg="#0D0E18", height=1).pack(fill="x")

        def _show_dropdown(btn, items):
            """Show a Premiere-style dropdown menu below the button."""
            m = tk.Menu(self, tearoff=0, bg="#0D0F1A", fg="#A0AABF",
                        activebackground=ACCENT, activeforeground=WHITE,
                        font=(_FF, 9), relief="flat", bd=0,
                        activeborderwidth=0)
            for item in items:
                if item == "---":
                    m.add_separator()
                else:
                    label, cmd = item
                    if cmd is None:
                        m.add_command(label=label, state="disabled",
                                      foreground="#3A4460")
                    else:
                        m.add_command(label=label, command=cmd)
            x = btn.winfo_rootx()
            y = btn.winfo_rooty() + btn.winfo_height()
            m.tk_popup(x, y)

        def _menubtn(parent, txt, items, fg="#6B7A99", hover=TEXT):
            b = tk.Button(parent, text=txt,
                          bg="#05060D", fg=fg, relief="flat", bd=0, cursor="hand2",
                          font=(_FF, 8), padx=8, pady=2,
                          activebackground="#12141F", activeforeground=TEXT)
            b.configure(command=lambda _b=b, _i=items: _show_dropdown(_b, _i))
            b.bind("<Enter>", lambda e, _b=b: safe_cfg(_b, fg=hover, bg="#12141F"))
            b.bind("<Leave>", lambda e, _b=b: safe_cfg(_b, fg=fg, bg="#05060D"))
            return b

        # ── File menu ────────────────────────────────────────────────
        def _save_as_wrap():
            if hasattr(self, "_save_as"): self._save_as()
            else: self._save()

        _menubtn(menubar, "File", [
            ("New Project",        self._new),
            ("Open Project…",      self._open),
            ("---", None),
            ("Save",               self._save),
            ("Save As…",           _save_as_wrap),
            ("---", None),
            ("Import Media…",      lambda: self._panels["media"]._import()),
            ("---", None),
            ("Recent Projects",    self._show_recent),
            ("---", None),
            ("Export Video…",      self._export),
            ("Export GIF…",        self._export_gif),
        ]).pack(side="left")

        # ── Edit menu ────────────────────────────────────────────────
        def _select_all():
            if self._proj.clips:
                self._on_sel(0)
                self._sv.set(f"Selected first clip — use timeline to select others")

        def _deselect():
            self._sel = None
            self._inspector.clear()
            self._sv.set("Deselected")

        def _delete_selected():
            if self._sel is not None:
                self._push_undo()
                self._on_del(self._sel)
                self._sv.set("Clip deleted")

        def _duplicate_selected():
            clip = self._get_clip()
            if not clip:
                self._sv.set("⚠  No clip selected to duplicate")
                return
            import copy
            nc = copy.deepcopy(clip)
            nc.load_thumb()
            idx = self._sel if self._sel is not None else len(self._proj.clips)-1
            self._push_undo()
            self._proj.clips.insert(idx+1, nc)
            self._on_change()
            self._sv.set("Clip duplicated")

        _menubtn(menubar, "Edit", [
            ("Undo",               self._undo),
            ("Redo",               self._redo),
            ("---", None),
            ("Duplicate Clip",     _duplicate_selected),
            ("Delete Selected",    _delete_selected),
            ("---", None),
            ("Select First Clip",  _select_all),
            ("Deselect",           _deselect),
            ("---", None),
            ("Preferences…",       self._show_settings),
        ]).pack(side="left")

        # ── Clip menu ────────────────────────────────────────────────
        def _split_at_mid():
            clip = self._get_clip()
            if not clip:
                self._sv.set("⚠  No clip selected"); return
            import copy
            mid = (clip.start_cut + clip.end_cut) / 2
            self._push_undo()
            nc = copy.deepcopy(clip)
            clip.end_cut = mid
            nc.start_cut = mid
            nc.load_thumb()
            idx = self._sel if self._sel is not None else 0
            self._proj.clips.insert(idx+1, nc)
            self._on_change()
            self._sv.set("Clip split at midpoint")

        def _set_speed(speed):
            clip = self._get_clip()
            if not clip:
                self._sv.set("⚠  No clip selected"); return
            self._push_undo()
            clip.speed = speed
            self._on_change()
            self._sv.set(f"Speed set to {speed}x")

        def _rename_clip():
            clip = self._get_clip()
            if not clip:
                self._sv.set("⚠  No clip selected"); return
            dlg = tk.Toplevel(self)
            dlg.title("Rename Clip")
            dlg.configure(bg=WHITE)
            dlg.resizable(False, False)
            dlg.grab_set()
            tk.Label(dlg, text="Clip Name:", bg=WHITE, fg=TEXT,
                     font=(_FF,10)).pack(padx=20, pady=(16,4))
            v = tk.StringVar(value=os.path.basename(clip.path))
            e = tk.Entry(dlg, textvariable=v, bg=CARD, fg=TEXT,
                         insertbackground=TEXT, relief="flat",
                         font=(_FF,10), width=30)
            e.pack(padx=20, pady=4)
            e.select_range(0, "end")
            def _ok():
                clip.label = v.get()
                self._on_change()
                dlg.destroy()
            bf = tk.Frame(dlg, bg=WHITE); bf.pack(pady=12)
            mkbtn(bf, "OK", _ok, style="accent").pack(side="left", padx=4)
            mkbtn(bf, "Cancel", dlg.destroy, style="ghost").pack(side="left", padx=4)

        def _remove_clip():
            if self._sel is not None:
                self._push_undo()
                self._on_del(self._sel)

        def _flip_h():
            clip = self._get_clip()
            if not clip: self._sv.set("⚠  No clip selected"); return
            self._push_undo()
            clip.flip_h = not clip.flip_h
            self._on_change()
            self._sv.set(f"Flip horizontal: {'on' if clip.flip_h else 'off'}")

        def _flip_v():
            clip = self._get_clip()
            if not clip: self._sv.set("⚠  No clip selected"); return
            self._push_undo()
            clip.flip_v = not clip.flip_v
            self._on_change()
            self._sv.set(f"Flip vertical: {'on' if clip.flip_v else 'off'}")

        def _rotate_clip(deg):
            clip = self._get_clip()
            if not clip: self._sv.set("⚠  No clip selected"); return
            self._push_undo()
            clip.rotation = (clip.rotation + deg) % 360
            self._on_change()
            self._sv.set(f"Rotation: {clip.rotation}°")

        _menubtn(menubar, "Clip", [
            ("Split at Midpoint",  _split_at_mid),
            ("Duplicate",          _duplicate_selected),
            ("Rename…",            _rename_clip),
            ("Remove from Timeline", _remove_clip),
            ("---", None),
            ("Speed: 0.25×",       lambda: _set_speed(0.25)),
            ("Speed: 0.5×",        lambda: _set_speed(0.5)),
            ("Speed: 1× (Normal)", lambda: _set_speed(1.0)),
            ("Speed: 1.5×",        lambda: _set_speed(1.5)),
            ("Speed: 2×",          lambda: _set_speed(2.0)),
            ("Speed: 4×",          lambda: _set_speed(4.0)),
            ("---", None),
            ("Flip Horizontal",    _flip_h),
            ("Flip Vertical",      _flip_v),
            ("Rotate 90° CW",      lambda: _rotate_clip(90)),
            ("Rotate 90° CCW",     lambda: _rotate_clip(-90)),
        ]).pack(side="left")

        # ── Sequence menu ────────────────────────────────────────────
        def _reverse_clips():
            if not self._proj.clips: return
            self._push_undo()
            self._proj.clips.reverse()
            self._on_change()
            self._sv.set("Clip order reversed")

        def _clear_timeline():
            if not self._proj.clips: return
            if messagebox.askyesno("Clear Timeline",
                                   "Remove all clips from the timeline?"):
                self._push_undo()
                self._proj.clips.clear()
                self._sel = None
                self._inspector.clear()
                self._on_change()
                self._sv.set("Timeline cleared")

        def _show_seq_settings():
            dlg = tk.Toplevel(self)
            dlg.title("Sequence Settings")
            dlg.configure(bg=WHITE)
            dlg.resizable(False, False)
            dlg.grab_set()
            hdr = tk.Frame(dlg, bg=ACCENT, height=44); hdr.pack(fill="x"); safe_pp(hdr)
            tk.Label(hdr, text="✦  Sequence Settings", bg=ACCENT, fg=WHITE,
                     font=(_FF,12,"bold")).pack(side="left", padx=16, pady=10)
            def row(label, widget_fn):
                f = tk.Frame(dlg, bg=WHITE); f.pack(fill="x", padx=20, pady=6)
                tk.Label(f, text=label, bg=WHITE, fg=MUTED,
                         font=(_FF,9), width=14, anchor="w").pack(side="left")
                widget_fn(f)
            # FPS
            fps_v = tk.IntVar(value=self._proj.fps)
            row("Frame Rate", lambda f: ttk.Combobox(
                f, textvariable=fps_v, values=[24,30,60],
                width=8, state="readonly").pack(side="left"))
            # Aspect ratio
            ar_v = tk.StringVar(value=self._proj.aspect_ratio)
            row("Aspect Ratio", lambda f: ttk.Combobox(
                f, textvariable=ar_v,
                values=list(ASPECT_RATIOS.keys()),
                width=20, state="readonly").pack(side="left"))
            sep(dlg).pack(fill="x", padx=16, pady=8)
            bf = tk.Frame(dlg, bg=WHITE); bf.pack(pady=10)
            def _apply():
                self._proj.fps = fps_v.get()
                self._proj.aspect_ratio = ar_v.get()
                self._on_change()
                dlg.destroy()
            mkbtn(bf, "Apply", _apply, style="accent").pack(side="left", padx=4)
            mkbtn(bf, "Cancel", dlg.destroy, style="ghost").pack(side="left", padx=4)

        def _move_clip_up():
            if self._sel is not None and self._sel > 0:
                self._push_undo()
                self._on_move(self._sel, self._sel-1)
                self._sv.set("Clip moved earlier")

        def _move_clip_down():
            if self._sel is not None and self._sel < len(self._proj.clips)-1:
                self._push_undo()
                self._on_move(self._sel, self._sel+1)
                self._sv.set("Clip moved later")

        _menubtn(menubar, "Sequence", [
            ("Sequence Settings…", _show_seq_settings),
            ("---", None),
            ("Move Clip Earlier",  _move_clip_up),
            ("Move Clip Later",    _move_clip_down),
            ("Reverse Clip Order", _reverse_clips),
            ("---", None),
            ("Clear Timeline",     _clear_timeline),
        ]).pack(side="left")

        # ── View menu ────────────────────────────────────────────────
        def _goto_panel(name):
            self._switch(name)

        _menubtn(menubar, "View", [
            ("Media Library",      lambda: _goto_panel("media")),
            ("Text",               lambda: _goto_panel("text")),
            ("Stickers",           lambda: _goto_panel("stickers")),
            ("Titles",             lambda: _goto_panel("titles")),
            ("Audio",              lambda: _goto_panel("audio")),
            ("Format",             lambda: _goto_panel("format")),
            ("Color Grading",      lambda: _goto_panel("grade")),
            ("Scene Detection",    lambda: _goto_panel("scenes")),
            ("AI Studio",          lambda: _goto_panel("ai")),
            ("---", None),
            ("Toggle Theme",       self._toggle_theme),
            ("Keyboard Shortcuts", self._show_shortcuts),
        ]).pack(side="left")

        # ── Window / Help ────────────────────────────────────────────
        _menubtn(menubar, "Window", [
            ("Settings…",          self._show_settings),
            ("Recent Projects…",   self._show_recent),
            ("Keyboard Shortcuts", self._show_shortcuts),
        ]).pack(side="left")

        _menubtn(menubar, "Help", [
            ("About ProEdit Studio", self._show_about),
            ("Keyboard Shortcuts",   self._show_shortcuts),
            ("---", None),
            ("Report a Bug",         lambda: __import__('webbrowser').open("https://github.com")),
        ]).pack(side="left")

        # ── Top bar ──────────────────────────────────────────────────
        top = tk.Frame(self, bg=DARK, height=46)
        top.pack(fill="x"); safe_pp(top)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Logo
        logo_f = tk.Frame(top, bg=DARK); logo_f.pack(side="left", padx=(14,12), pady=0)
        tk.Label(logo_f, text="✦", bg=DARK, fg=ACCENT,
                 font=(_FF, 13, "bold")).pack(side="left", padx=(0,5))
        tk.Label(logo_f, text="ProEdit Studio", bg=DARK, fg=TEXT,
                 font=(_FF, 10, "bold")).pack(side="left")
        tk.Label(logo_f, text=f"v{APP_VERSION}", bg=DARK, fg="#2E3450",
                 font=(_FF, 8)).pack(side="left", padx=(4,0))

        def _vsep(parent):
            tk.Frame(parent, bg=BORDER, width=1).pack(side="left", fill="y", pady=10, padx=6)

        def _topbtn(parent, txt, cmd, fg=MUTED, hover=TEXT, bg=DARK, font_size=9):
            b = tk.Button(parent, text=txt, command=cmd, bg=bg, fg=fg,
                          relief="flat", bd=0, cursor="hand2",
                          font=(_FF, font_size), padx=8, pady=6,
                          activebackground=WHITE, activeforeground=hover)
            b.bind("<Enter>", lambda e,_b=b: safe_cfg(_b, fg=hover, bg=WHITE))
            b.bind("<Leave>", lambda e,_b=b: safe_cfg(_b, fg=fg, bg=bg))
            return b

        _vsep(top)

        # File group
        for txt, cmd in [("New", self._new), ("Open", self._open), ("Save", self._save)]:
            _topbtn(top, txt, cmd).pack(side="left")
        _vsep(top)

        # History group
        self._undo_btn = tk.Button(top, text="↩", command=self._undo,
                                   bg=DARK, fg=MUTED, relief="flat", bd=0,
                                   cursor="hand2", font=(_FF, 11), padx=7, pady=5,
                                   activebackground=WHITE, activeforeground=WARN,
                                   state="disabled")
        self._undo_btn.pack(side="left")
        self._undo_btn.bind("<Enter>", lambda e: safe_cfg(self._undo_btn, fg=WARN, bg=WHITE) if str(self._undo_btn["state"])!="disabled" else None)
        self._undo_btn.bind("<Leave>", lambda e: safe_cfg(self._undo_btn, fg=MUTED, bg=DARK))

        self._redo_btn = tk.Button(top, text="↪", command=self._redo,
                                   bg=DARK, fg=MUTED, relief="flat", bd=0,
                                   cursor="hand2", font=(_FF, 11), padx=7, pady=5,
                                   activebackground=WHITE, activeforeground=WARN,
                                   state="disabled")
        self._redo_btn.pack(side="left")
        self._redo_btn.bind("<Enter>", lambda e: safe_cfg(self._redo_btn, fg=WARN, bg=WHITE) if str(self._redo_btn["state"])!="disabled" else None)
        self._redo_btn.bind("<Leave>", lambda e: safe_cfg(self._redo_btn, fg=MUTED, bg=DARK))

        _vsep(top)

        # Workspace tools
        for txt, cmd in [("⚙", self._show_settings), ("🕐", self._show_recent),
                         ("☀", self._toggle_theme), ("?", self._show_shortcuts)]:
            _topbtn(top, txt, cmd, font_size=10).pack(side="left", padx=1)

        # Right — export cluster
        right_f = tk.Frame(top, bg=DARK); right_f.pack(side="right", padx=(0, 12), pady=8)

        exp_b = tk.Button(right_f, text="▶  Export", command=self._export,
                          bg=ACCENT, fg="#FFFFFF", relief="flat", bd=0, cursor="hand2",
                          font=(_FF, 9, "bold"), padx=18, pady=6,
                          activebackground="#9B7FFE", activeforeground="#FFFFFF")
        exp_b.pack(side="right", padx=(4, 0))
        exp_b.bind("<Enter>", lambda e: safe_cfg(exp_b, bg="#9B7FFE"))
        exp_b.bind("<Leave>", lambda e: safe_cfg(exp_b, bg=ACCENT))

        for txt, cmd in [("Social", self._show_social_presets), ("GIF", self._export_gif)]:
            b2 = tk.Button(right_f, text=txt, command=cmd,
                           bg=CARD, fg=MUTED, relief="flat", bd=0, cursor="hand2",
                           font=(_FF, 8), padx=10, pady=6,
                           highlightthickness=1, highlightbackground=BORDER,
                           activebackground=WHITE, activeforeground=TEXT)
            b2.bind("<Enter>", lambda e,_b=b2: safe_cfg(_b, fg=TEXT, bg=WHITE))
            b2.bind("<Leave>", lambda e,_b=b2: safe_cfg(_b, fg=MUTED, bg=CARD))
            b2.pack(side="right", padx=2)

        self._sv = tk.StringVar(value=f"ProEdit Studio {APP_VERSION}  ·  Import media to begin  ·  Press ? for shortcuts")

        # body
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0) if CTK_AVAILABLE \
               else tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Sidebar (Premiere-style) ──────────────────────────────────
        self._strip = tk.Frame(body, bg="#07080F", width=80)
        self._strip.pack(side="left", fill="y"); safe_pp(self._strip)
        # Top accent line
        tk.Frame(self._strip, bg=ACCENT, height=2).pack(fill="x")
        tk.Frame(self._strip, height=8, bg="#07080F").pack()

        self._ibns = {}
        icons = [
            ("📁", "media",    ACCENT,   "Media"),
            ("✏",  "text",     "#F43F5E","Text"),
            ("😀", "stickers", "#FBBF24","Stickers"),
            ("🎬", "titles",   "#22D3A5","Titles"),
            ("🎵", "audio",    "#38BDF8","Audio"),
            ("📐", "format",   "#A78BFA","Format"),
            ("🎨", "grade",    "#F59E0B","Grade"),
            ("✂",  "scenes",   "#22D3A5","Scenes"),
            ("🤖", "ai",       "#F43F5E","AI"),
        ]
        for icon, name, accent_col, label in icons:
            outer = tk.Frame(self._strip, bg="#07080F")
            outer.pack(fill="x", pady=0)

            cv = tk.Canvas(outer, width=80, height=62, bg="#07080F",
                           highlightthickness=0, cursor="hand2")
            cv.pack()

            # Active indicator bar on left edge
            _bar = cv.create_rectangle(0, 8, 3, 54, fill="#07080F", outline="", tags="bar")
            # Hover bg
            _bg  = cv.create_rectangle(5, 4, 75, 58, fill="#07080F", outline="", tags="bg")
            # Icon circle
            _circ= cv.create_oval(24, 8, 56, 36, fill="#0F1018", outline="", tags="circ")
            _ic  = cv.create_text(40, 22, text=icon, font=(_FF, 14),
                                  fill="#3A4460", tags="ic")
            _lbl = cv.create_text(40, 47, text=label,
                                  font=(_FF, 7, "bold"), fill="#2E3450", tags="lbl")

            nl = tk.Label(outer, bg="#07080F")  # dummy for compat
            self._ibns[name] = (outer, cv, nl, accent_col, _bg, _circ, _ic, _lbl)

            def _on_enter(e, _cv=cv, _ac=accent_col):
                _cv.itemconfig("bg",   fill="#0F1018")
                _cv.itemconfig("circ", fill=_ac+"18")
                _cv.itemconfig("ic",   fill=TEXT)
                _cv.itemconfig("lbl",  fill="#8899BB")
            def _on_leave(e, n2=name, _cv=cv, _ac=accent_col):
                on = (n2 == getattr(self, "_active_panel", "media"))
                _cv.itemconfig("bar",  fill=_ac if on else "#07080F")
                _cv.itemconfig("bg",   fill=_ac+"12" if on else "#07080F")
                _cv.itemconfig("circ", fill=_ac+"25" if on else "#0F1018")
                _cv.itemconfig("ic",   fill=TEXT if on else "#3A4460")
                _cv.itemconfig("lbl",  fill=_ac if on else "#2E3450")
            def _on_click(e, n=name): self._switch(n)
            for w in [outer, cv]:
                w.bind("<Button-1>", _on_click)
                w.bind("<Enter>", _on_enter)
                w.bind("<Leave>", _on_leave)

        # panel area
        self._parea = tk.Frame(body, bg=WHITE, width=390,
                               highlightthickness=0)
        self._parea.pack(side="left",fill="y")
        safe_pp(self._parea)
        # Thin accent separator 
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")
        self._panels={}
        for name,cls in [("media",MediaPanel),("text",TextPanel),
                          ("stickers",StickerPanel),("titles",TitlesPanel),
                          ("audio",AudioPanel),("format",FormatPanel),
                          ("grade",ColorGradingPanel),("scenes",SceneDetectPanel),
                          ("ai",CreativeArchitectPanel)]:
            p=cls(self._parea,self._proj,self._get_clip,self._on_change)
            p.place(x=0,y=0,relwidth=1,relheight=1)
            self._panels[name]=p
        self._switch("media")

        # ── Centre ────────────────────────────────────────────────────
        centre = ctk.CTkFrame(body, fg_color=BG, corner_radius=0) if CTK_AVAILABLE                  else tk.Frame(body, bg=BG)
        centre.pack(side="left", fill="both", expand=True)

        # Canvas toolbar — Premiere-style compact tool strip
        ctbar = tk.Frame(centre, bg="#080A12", height=36)
        ctbar.pack(fill="x")
        safe_pp(ctbar)
        tk.Frame(ctbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        tk.Frame(ctbar, bg="#07080F", height=1).pack(side="top", fill="x")

        # Tool buttons with active state tracking
        self._active_tool = tk.StringVar(value="select")
        tool_btns = {}

        def _ctbtn(txt, tool_name=None):
            is_active = (tool_name == "select")
            b = tk.Button(ctbar, text=txt,
                          bg=SEL if is_active else "#080A12",
                          fg=ACCENT if is_active else MUTED,
                          relief="flat", bd=0, cursor="hand2",
                          font=(_FF, 11), padx=8, pady=3,
                          highlightthickness=1 if is_active else 0,
                          highlightbackground=ACCENT,
                          activebackground=SEL, activeforeground=ACCENT)
            def _click(tn=tool_name, btn=b):
                self._active_tool.set(tn or "")
                for n, tb in tool_btns.items():
                    on = (n == tn)
                    safe_cfg(tb,bg=SEL if on else WHITE,
                              fg=ACCENT if on else MUTED,
                              highlightthickness=1 if on else 0)
            b.bind("<Button-1>", lambda e: _click())
            b.bind("<Enter>", lambda e, btn=b, tn=tool_name:
                   safe_cfg(btn,bg=SEL) if self._active_tool.get()!=tn else None)
            b.bind("<Leave>", lambda e, btn=b, tn=tool_name:
                   safe_cfg(btn,bg=DARK) if self._active_tool.get()!=tn else None)
            if tool_name:
                tool_btns[tool_name] = b
            return b

        _ctbtn("✦", "select").pack(side="left", padx=2)
        _ctbtn("T",  "text").pack(side="left", padx=1)
        _ctbtn("⬜", "shape").pack(side="left", padx=1)
        tk.Frame(ctbar, bg=BORDER, width=1).pack(side="left", fill="y", pady=10, padx=6)
        _ctbtn("✂", "crop").pack(side="left", padx=1)
        _ctbtn("↔", "flip").pack(side="left", padx=1)
        _ctbtn("🔍", "zoom").pack(side="left", padx=1)
        tk.Frame(ctbar, bg=BORDER, width=1).pack(side="left", fill="y", pady=10, padx=6)
        self._res_lbl = tk.Label(ctbar, text="1920 × 1080", bg=DARK, fg=MUTED,
                                  font=("Helvetica",9))
        self._res_lbl.pack(side="left", padx=4)
        tk.Frame(ctbar, bg=BORDER, width=1).pack(side="left", fill="y", pady=8, padx=4)
        # Zoom controls
        def _zoom_in():
            if hasattr(self._preview, "_zoom"):
                self._preview._zoom = min(4.0, self._preview._zoom * 1.25)
                safe_cfg(self._zoom_lbl, text=f"{int(self._preview._zoom*100)}%")
                self._preview._render()
        def _zoom_out():
            if hasattr(self._preview, "_zoom"):
                self._preview._zoom = max(0.25, self._preview._zoom * 0.8)
                safe_cfg(self._zoom_lbl, text=f"{int(self._preview._zoom*100)}%")
                self._preview._render()
        def _zoom_reset():
            if hasattr(self._preview, "_zoom"):
                self._preview._zoom = 1.0
                self._preview._pan_x = 0
                self._preview._pan_y = 0
                safe_cfg(self._zoom_lbl, text="100%")
                self._preview._render()
        tk.Button(ctbar, text="−", bg=DARK, fg=MUTED, relief="flat",
                  font=("Helvetica",12), padx=4, cursor="hand2",
                  command=_zoom_out).pack(side="left")
        self._zoom_lbl = tk.Label(ctbar, text="100%", bg=DARK, fg=TEXT,
                                   font=("Helvetica",9), cursor="hand2",
                                   width=5)
        self._zoom_lbl.pack(side="left")
        self._zoom_lbl.bind("<Button-1>", lambda e: _zoom_reset())
        tk.Button(ctbar, text="+", bg=DARK, fg=MUTED, relief="flat",
                  font=("Helvetica",12), padx=4, cursor="hand2",
                  command=_zoom_in).pack(side="left")

        self._preview = Preview(centre)
        self._preview._on_change = self._on_change
        self._preview.pack(fill="both", expand=True)
        self._timeline=Timeline(centre,self._proj,
                                 on_select=self._on_sel,on_delete=self._on_del,
                                 on_move=self._on_move,on_change=self._on_change)
        self._timeline._scrub_cb = self._on_scrub
        self._timeline.pack(fill="x",side="bottom")
        # Drag-and-drop onto timeline/preview
        if DND_AVAILABLE:
            for w in [self._timeline, centre]:
                try:
                    w.drop_target_register(dnd.DND_FILES)
                    w.dnd_bind("<<Drop>>", self._on_file_drop)
                except Exception: pass

        # inspector — right panel
        self._inspector=Inspector(body,self._on_change)
        self._inspector.pack(side="right",fill="y")

        # ── Professional Status Bar ───────────────────────────────────
        statusbar = tk.Frame(self, bg="#03040A", height=20)
        statusbar.pack(fill="x", side="bottom")
        statusbar.pack_propagate(False)
        tk.Frame(self, bg=BORDER, height=1).pack(side="bottom", fill="x")
        # Left accent + status text
        tk.Frame(statusbar, bg=ACCENT, width=2).pack(side="left", fill="y")
        tk.Label(statusbar, textvariable=self._sv, bg="#03040A", fg="#3A4460",
                 font=(_FF, 7)).pack(side="left", padx=10)
        # Right info cluster
        self._sb_sel = tk.Label(statusbar, text="", bg="#03040A", fg=GREEN,
                                 font=(_FF, 7))
        self._sb_sel.pack(side="right", padx=8)
        tk.Frame(statusbar, bg=BORDER, width=1).pack(side="right", fill="y", pady=4)
        self._sb_res = tk.Label(statusbar, text="1920×1080  ·  30fps",
                                 bg="#03040A", fg="#2E3450", font=(_FF, 7))
        self._sb_res.pack(side="right", padx=8)
        tk.Frame(statusbar, bg=BORDER, width=1).pack(side="right", fill="y", pady=4)
        self._sb_dur = tk.Label(statusbar, text="", bg="#03040A", fg="#3A4460",
                                 font=(_FF, 7))
        self._sb_dur.pack(side="right", padx=8)
        tk.Frame(statusbar, bg=BORDER, width=1).pack(side="right", fill="y", pady=4)
        self._sb_clips = tk.Label(statusbar, text="", bg="#03040A", fg="#3A4460",
                                   font=(_FF, 7))
        self._sb_clips.pack(side="right", padx=8)

    def _refresh_sidebar_item(self, name, f, cv, nl):
        pass  # handled by _switch

    def _switch(self, name):
        self._active_panel = name
        for n, idata in self._ibns.items():
            _cv = idata[1]
            _ac = idata[3] if len(idata)>3 else ACCENT
            active = (n == name)
            try:
                _cv.itemconfig("bar",  fill=_ac if active else "#07080F")
                _cv.itemconfig("bg",   fill=_ac+"12" if active else "#07080F")
                _cv.itemconfig("circ", fill=_ac+"25" if active else "#0F1018")
                _cv.itemconfig("ic",   fill=TEXT if active else "#3A4460")
                _cv.itemconfig("lbl",  fill=_ac if active else "#2E3450")
            except Exception: pass
        self._panels[name].lift()

    def _get_clip(self):
        if self._sel is not None and 0<=self._sel<len(self._proj.clips):
            return self._proj.clips[self._sel]
        return None

    def _on_sel(self, idx):
        self._sel=idx
        clip=self._proj.clips[idx]
        self._inspector.show(clip)
        self._preview._clip = clip   # set directly to avoid double render
        self._preview.show(clip)
        self._timeline.refresh(idx)
        self._sv.set(f"Selected: {clip.filename}  —  drag overlays in preview to reposition")

    def _on_del(self, idx):
        self._proj.clips.pop(idx)
        if self._sel==idx: self._sel=None; self._inspector.clear()
        elif self._sel and self._sel>idx: self._sel-=1
        self._timeline._sel=self._sel; self._timeline.refresh()

    def _on_move(self, a, b):
        c=self._proj.clips; c[a],c[b]=c[b],c[a]
        self._sel=b; self._timeline.refresh(b)

    def _push_undo(self):
        """Snapshot current project state onto undo stack."""
        import copy
        state = json.dumps(self._proj.to_dict())
        self._undo_stack.append(state)
        if len(self._undo_stack) > 50:   # cap at 50 levels
            self._undo_stack.pop(0)
        safe_cfg(self._undo_btn,state="normal")

    def _undo(self):
        """Restore the previous project state."""
        if not self._undo_stack: return
        self._redo_stack.append(json.dumps(self._proj.to_dict()))
        state = json.loads(self._undo_stack.pop())
        self._proj.from_dict(state)
        for c in self._proj.clips: c.load_thumb()
        self._sel = None
        self._inspector.clear()
        self._timeline._proj = self._proj
        self._timeline.refresh()
        if self._get_clip(): self._preview.show(self._get_clip())
        self._sv.set("↩ Undo applied")
        safe_cfg(self._undo_btn, state="normal" if self._undo_stack else "disabled")
        if hasattr(self,"_redo_btn"):
            safe_cfg(self._redo_btn, state="normal")

    def _redo(self):
        """Re-apply last undone action."""
        if not self._redo_stack: return
        self._undo_stack.append(json.dumps(self._proj.to_dict()))
        state = json.loads(self._redo_stack.pop())
        self._proj.from_dict(state)
        for c in self._proj.clips: c.load_thumb()
        self._sel = None
        self._inspector.clear()
        self._timeline._proj = self._proj
        self._timeline.refresh()
        if self._get_clip(): self._preview.show(self._get_clip())
        self._sv.set("↪ Redo applied")
        safe_cfg(self._undo_btn, state="normal")
        if hasattr(self,"_redo_btn"):
            safe_cfg(self._redo_btn, state="normal" if self._redo_stack else "disabled")

    def _on_file_drop(self, event):
        """Handle files drag-dropped onto the window."""
        import re
        raw = event.data or ""
        # tkinterdnd2 gives paths as {/path with spaces} or /simple/path
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        paths = [a or b for a,b in paths]
        added = 0
        for p in paths:
            p = p.strip().strip("{}")
            if os.path.isfile(p):
                ext = os.path.splitext(p)[1].lower()
                if ext in ('.mp4','.mov','.avi','.mkv','.webm',
                           '.jpg','.jpeg','.png','.gif','.bmp','.webp'):
                    c = Clip(p); c.load_thumb()
                    self._proj.clips.append(c)
                    added += 1
        if added:
            self._timeline.refresh()
            self._on_change()
            Toast.show(self, f"Added {added} file{'s' if added>1 else ''} to timeline!", "success")

    def _on_scrub(self, clip, t):
        """Show a specific frame from a clip at time t (for scrubbing)."""
        if not PIL_AVAILABLE or not MOVIEPY_AVAILABLE: return
        import threading as _th
        def _grab():
            try:
                from moviepy import VideoFileClip
                if clip.is_image:
                    img = Image.open(clip.path).convert("RGB")
                else:
                    vc = VideoFileClip(clip.path)
                    frame = vc.get_frame(min(t, vc.duration - 0.01))
                    img = Image.fromarray(frame)
                    vc.close()
                self.after(0, lambda i=img: self._preview._show_pil(i))
            except Exception: pass
        _th.Thread(target=_grab, daemon=True).start()

    def _update_statusbar(self):
        """Refresh the smart status bar with live project stats."""
        try:
            n = len(self._proj.clips)
            dur = self._proj.total_dur()
            clip = self._get_clip()
            w,h = self._proj.res
            m2,s2 = divmod(int(dur),60)
            dur_str = f"{m2}:{s2:02d}" if m2 else (f"{dur:.1f}s" if dur>0 else "")
            self._sb_clips.config(text=f"{n} clip{'s' if n!=1 else ''}")
            self._sb_dur.config(text=dur_str)
            self._sb_res.config(text=f"{w}×{h}  ·  {self._proj.fps}fps")
            if clip:
                _defaults = {"exposure":0,"highlights":0,"shadows":0,"whites":0,"blacks":0,
                             "brightness":1,"contrast":1,"saturation":1,"vibrance":0,"hue_shift":0,
                             "temperature":0,"tint":0,"sharpness":0,"clarity":0,"noise_reduce":0,
                             "vignette":0,"grain":0,"lut":"None","filter":"None"}
                def _is_adj(k, v):
                    cur = getattr(clip, k, v)
                    if isinstance(v, float): return abs(cur - v) > 0.01
                    return cur != v
                adj_count = sum(1 for k,v in _defaults.items() if _is_adj(k,v))
                adj_str = f"  ✦{adj_count}" if adj_count > 0 else ""
                self._sb_sel.config(text=f"● {clip.filename[:18]}{adj_str}")
            else:
                self._sb_sel.config(text="")
        except Exception:
            pass

    def _on_change(self):
        self._timeline.refresh(self._sel)
        clip = self._get_clip()
        if clip: self._preview.show(clip)
        self._update_statusbar()
        # Mark title as modified
        t = self.title()
        if not t.startswith("*"):
            self.title("*" + t)

    def _show_about(self):
        """Professional About dialog with system info."""
        import platform, sys as _sys
        # Re-check at display time so PyInstaller bundles detect correctly
        def _check_pkg(name):
            try:
                import importlib
                importlib.import_module(name)
                return True
            except Exception:
                return False
        _mpy_ok  = MOVIEPY_AVAILABLE or _check_pkg("moviepy")
        _pil_ok  = PIL_AVAILABLE     or _check_pkg("PIL")
        _np_ok   = NUMPY_AVAILABLE   or _check_pkg("numpy")
        win = tk.Toplevel(self); win.title(f"About {APP_NAME}")
        win.configure(bg=WHITE); win.geometry("420x460"); win.grab_set()
        win.resizable(False, False)
        hdr = tk.Frame(win, bg=ACCENT, height=120); hdr.pack(fill="x"); safe_pp(hdr)
        tk.Label(hdr, text="✦", bg=ACCENT, fg=WHITE,
                 font=("Helvetica",36,"bold")).pack(pady=(18,2))
        tk.Label(hdr, text=APP_NAME, bg=ACCENT, fg=WHITE,
                 font=("Helvetica",16,"bold")).pack()
        tk.Label(hdr, text=f"Version {APP_VERSION}  ·  AI Video Editor",
                 bg=ACCENT, fg="#C4B5FD", font=("Helvetica",9)).pack(pady=(0,14))
        body = tk.Frame(win, bg=WHITE); body.pack(fill="both", expand=True, padx=24, pady=12)
        py_ver = f"{_sys.version_info.major}.{_sys.version_info.minor}.{_sys.version_info.micro}"
        rows = [
            ("Version",      APP_VERSION,    TEXT),
            ("Python",       py_ver,         TEXT),
            ("Platform",     f"{platform.system()} {platform.release()}", TEXT),
            ("Architecture", platform.machine(), TEXT),
            ("AI Providers", "OpenAI · Gemini · WaveSpeed · Sora", TEXT),
            ("MoviePy",      "✅ Installed" if _mpy_ok else "❌ Not installed",
                             GREEN if _mpy_ok else A2),
            ("Pillow / PIL", "✅ Installed" if _pil_ok else "❌ Not installed",
                             GREEN if _pil_ok else A2),
            ("NumPy",        "✅ Installed" if _np_ok else "❌ Not installed",
                             GREEN if _np_ok else A2),
        ]
        for label, value, color in rows:
            row = tk.Frame(body, bg=WHITE); row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=WHITE, fg=MUTED,
                     font=("Helvetica",9), width=15, anchor="w").pack(side="left")
            tk.Label(row, text=value, bg=WHITE, fg=color,
                     font=("Helvetica",9,"bold"), anchor="w").pack(side="left")
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=8)
        tk.Label(body, text="Powerful AI video editing for everyone.",
                 bg=WHITE, fg=MUTED, font=("Helvetica",8), justify="center").pack()
        btn_row = tk.Frame(win, bg=WHITE); btn_row.pack(fill="x", padx=24, pady=12)
        sys_text = "\n".join(f"{lb}: {vl}" for lb,vl,_ in rows)
        mkbtn(btn_row, "Copy System Info",
              lambda: (self.clipboard_clear(), self.clipboard_append(sys_text)),
              style="ghost", py=7).pack(side="left", expand=True, fill="x", padx=(0,4))
        mkbtn(btn_row, "Close", win.destroy,
              style="accent", py=7).pack(side="left", expand=True, fill="x")
        # Linux: offer to install desktop shortcut
        import sys as _sys2, platform as _pl2
        if _pl2.system() == "Linux":
            def _install_shortcut():
                import subprocess, os as _os
                script = _os.path.abspath(_sys2.argv[0])
                desktop_dir = _os.path.expanduser("~/.local/share/applications")
                _os.makedirs(desktop_dir, exist_ok=True)
                desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME}
Comment=AI-powered video editor v{APP_VERSION}
Exec=python3 {script}
Icon=video-display
Terminal=false
Categories=AudioVideo;Video;Graphics;
Keywords=video;editor;ai;
StartupWarningSilence=true
"""
                out = _os.path.join(desktop_dir, "proedit-studio.desktop")
                with open(out, "w") as f: f.write(desktop_content)
                subprocess.run(["chmod", "+x", out], check=False)
                messagebox.showinfo("Shortcut Installed",
                    f"Desktop shortcut installed!\n{out}\n\nYou can now launch from your app menu.",
                    parent=win)
            mkbtn(win, "🐧  Install Desktop Shortcut", _install_shortcut,
                  style="ghost", py=6).pack(fill="x", padx=24, pady=(0,8))

    def _show_settings(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.configure(bg=WHITE)
        win.resizable(True, True)
        win.geometry("580x860")
        win.grab_set()

        # Header — Canva style
        hdr = tk.Frame(win, bg=ACCENT, height=52)
        hdr.pack(fill="x"); safe_pp(hdr)
        tk.Label(hdr, text="  ⚙  Settings", bg=ACCENT, fg=WHITE,
                 font=("Helvetica",14,"bold")).pack(side="left", pady=12, padx=16)
        tk.Button(hdr, text="✕", bg=ACCENT, fg=WHITE, relief="flat", bd=0,
                  cursor="hand2", font=("Helvetica",14),
                  command=win.destroy,
                  activebackground="#5A52E0", activeforeground=WHITE
                  ).pack(side="right", padx=14)

        sf, body = scrollframe(win, bg=WHITE)
        sf.pack(fill="both", expand=True)

        def sec(title):
            f = tk.Frame(body, bg=WHITE)
            f.pack(fill="x", padx=16, pady=(12,2))
            tk.Label(f, text=title.upper(), bg=WHITE, fg=MUTED,
                     font=F["xs"]).pack(side="left")
            tk.Frame(f, bg=BORDER, height=1).pack(
                side="left", fill="x", expand=True, padx=(6,0), pady=4)

        # ── Provider selection ────────────────────────────────
        sec("App Preferences")
        pref_f = tk.Frame(body, bg=WHITE); pref_f.pack(fill="x", padx=16, pady=6)
        # Timeline default FPS
        fps_row = tk.Frame(pref_f, bg=WHITE); fps_row.pack(fill="x", pady=3)
        tk.Label(fps_row, text="Default FPS:", bg=WHITE, fg=TEXT,
                 font=F["sm"], width=16, anchor="w").pack(side="left")
        fps_v = tk.StringVar(value=str(_SETTINGS.get("default_fps", 30)))
        fps_menu = ttk.Combobox(fps_row, textvariable=fps_v, state="readonly",
                                 values=["24","25","30","60"], width=8)
        fps_menu.pack(side="left", padx=4)
        # Autosave interval
        as_row = tk.Frame(pref_f, bg=WHITE); as_row.pack(fill="x", pady=3)
        tk.Label(as_row, text="Autosave every:", bg=WHITE, fg=TEXT,
                 font=F["sm"], width=16, anchor="w").pack(side="left")
        as_v = tk.StringVar(value=str(_SETTINGS.get("autosave_mins", 3)))
        ttk.Combobox(as_row, textvariable=as_v, state="readonly",
                     values=["1","2","3","5","10","Never"], width=8).pack(side="left", padx=4)
        tk.Label(as_row, text="minutes", bg=WHITE, fg=MUTED,
                 font=F["xs"]).pack(side="left", padx=2)
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)

        sec("AI Provider  (for Analysis & Prompts)")
        tk.Label(body,
                 text="Image generation always uses Pollinations.AI — free, no key needed.",
                 bg=WHITE, fg=GREEN, font=F["xs"]).pack(padx=16, anchor="w", pady=(0,4))

        provider_var = tk.StringVar(value=_SETTINGS.get("active_provider","openai"))
        prov_frame = tk.Frame(body, bg=WHITE)
        prov_frame.pack(fill="x", padx=16, pady=4)

        for pid, pname, pdesc in [
            ("openai", "OpenAI  (Recommended)", "GPT-4o-mini · ~$0.01/analysis · most reliable"),
            ("gemini", "Google Gemini",          "Free tier · aistudio.google.com/app/apikey"),
        ]:
            row = tk.Frame(prov_frame, bg=CARD,
                           highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=3)
            tk.Radiobutton(row, text=pname, variable=provider_var, value=pid,
                           bg=CARD, fg=TEXT, activebackground=SEL,
                           selectcolor=WHITE, font=F["h3"],
                           cursor="hand2", pady=8, padx=10).pack(side="left")
            tk.Label(row, text=pdesc, bg=CARD, fg=MUTED,
                     font=F["xs"]).pack(side="left", padx=4)

        # ── OpenAI ────────────────────────────────────────────
        sec("OpenAI API Key")
        tk.Label(body, text="Get key: platform.openai.com/api-keys  |  Add $5 credit to activate",
                 bg=WHITE, fg=MUTED, font=F["xs"]).pack(padx=16, anchor="w", pady=(0,2))
        kf_o = tk.Frame(body, bg=WHITE); kf_o.pack(fill="x", padx=16, pady=4)
        openai_key_v = tk.StringVar(value=_SETTINGS.get("openai_api_key",""))
        oai_ent = tk.Entry(kf_o, textvariable=openai_key_v, bg=CARD, fg=TEXT,
                           insertbackground=TEXT, relief="flat",
                           font=F["sm"], show="*", width=40)
        oai_ent.pack(side="left", fill="x", expand=True)
        o_hidden = [True]
        def tog_oai():
            o_hidden[0] = not o_hidden[0]
            safe_cfg(oai_ent,show="*" if o_hidden[0] else "")
        mkbtn(kf_o, "👁", tog_oai, py=4, px=8).pack(side="left", padx=4)

        sec("OpenAI Model")
        openai_model_v = tk.StringVar(value=_SETTINGS.get("openai_model", OPENAI_MODEL_LABELS[0]))
        om_frame = tk.Frame(body, bg=WHITE); om_frame.pack(fill="x", padx=16, pady=2)
        for lbl_text in OPENAI_MODEL_LABELS:
            row = tk.Frame(om_frame, bg=WHITE); row.pack(fill="x", pady=1)
            tk.Radiobutton(row, text=lbl_text, variable=openai_model_v, value=lbl_text,
                           bg=WHITE, fg=TEXT, activebackground=SEL,
                           selectcolor=SEL, font=F["sm"],
                           cursor="hand2").pack(side="left", padx=4)
        tk.Label(body, text="💡 gpt-4o-mini is cheapest — about $0.01 per analysis.",
                 bg=WHITE, fg=MUTED, font=F["xs"]).pack(padx=16, anchor="w", pady=(0,6))

        # ── Google Gemini (backup) ─────────────────────────────
        sec("Google Gemini API Key  (backup option)")
        tk.Label(body, text="Free key: aistudio.google.com/app/apikey",
                 bg=WHITE, fg=MUTED, font=F["xs"]).pack(padx=16, anchor="w", pady=(0,2))
        kf_g = tk.Frame(body, bg=WHITE); kf_g.pack(fill="x", padx=16, pady=4)
        gemini_key_v = tk.StringVar(value=_SETTINGS.get("gemini_api_key",""))
        gem_ent = tk.Entry(kf_g, textvariable=gemini_key_v, bg=CARD, fg=TEXT,
                           insertbackground=TEXT, relief="flat",
                           font=F["sm"], show="*", width=40)
        gem_ent.pack(side="left", fill="x", expand=True)
        g_hidden = [True]
        def tog_gem():
            g_hidden[0] = not g_hidden[0]
            safe_cfg(gem_ent,show="*" if g_hidden[0] else "")
        mkbtn(kf_g, "👁", tog_gem, py=4, px=8).pack(side="left", padx=4)

        sec("Gemini Model")
        gemini_model_v = tk.StringVar(value=_SETTINGS.get("gemini_model", GEMINI_MODEL_LABELS[0]))
        gm_frame = tk.Frame(body, bg=WHITE); gm_frame.pack(fill="x", padx=16, pady=2)
        for lbl_text in GEMINI_MODEL_LABELS:
            row = tk.Frame(gm_frame, bg=WHITE); row.pack(fill="x", pady=1)
            tk.Radiobutton(row, text=lbl_text, variable=gemini_model_v, value=lbl_text,
                           bg=WHITE, fg=TEXT, activebackground=SEL,
                           selectcolor=SEL, font=F["sm"],
                           cursor="hand2").pack(side="left", padx=4)

        # ── Image Compression ─────────────────────────────────
        sec("Image Compression  (reduces API cost)")
        compress_var = tk.BooleanVar(value=_SETTINGS.get("compress_images", True))
        cf = tk.Frame(body, bg=WHITE); cf.pack(fill="x", padx=16, pady=3)
        tk.Checkbutton(cf, text="Compress images before sending",
                       variable=compress_var, bg=WHITE, activebackground=WHITE,
                       font=F["sm"], selectcolor=SEL, cursor="hand2").pack(side="left")
        qf = tk.Frame(body, bg=WHITE); qf.pack(fill="x", padx=16, pady=2)
        tk.Label(qf, text="JPEG Quality:", bg=WHITE, fg=TEXT, font=F["sm"]).pack(side="left")
        quality_var = tk.IntVar(value=_SETTINGS.get("compress_quality", 60))
        tk.Scale(qf, variable=quality_var, from_=20, to=95,
                 orient="horizontal", length=200, bg=WHITE,
                 troughcolor=BORDER, highlightthickness=0,
                 showvalue=True).pack(side="left", padx=6)
        tk.Label(qf, text="lower = cheaper", bg=WHITE, fg=MUTED, font=F["xs"]).pack(side="left")

        # ── Save / Cancel ─────────────────────────────────────
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=16, pady=12)
        btn_row = tk.Frame(body, bg=WHITE); btn_row.pack(pady=8)

        def save():
            _SETTINGS["active_provider"]  = provider_var.get()
            _SETTINGS["openai_api_key"]   = openai_key_v.get().strip()
            _SETTINGS["openai_model"]     = openai_model_v.get()
            _SETTINGS["gemini_api_key"]   = gemini_key_v.get().strip()
            _SETTINGS["gemini_model"]     = gemini_model_v.get()
            _SETTINGS["compress_images"]  = compress_var.get()
            _SETTINGS["compress_quality"] = quality_var.get()
            try: _SETTINGS["default_fps"] = int(fps_v.get())
            except: pass
            try:
                mins = as_v.get()
                _SETTINGS["autosave_mins"] = mins if mins == "Never" else int(mins)
            except: pass
            _save_config()   # ← persist API keys to disk
            prov = provider_var.get()
            provider_name = "OpenAI" if prov == "openai" else "Google Gemini"
            model = (openai_model_v.get() if prov == "openai" else gemini_model_v.get()).split()[0]
            self._sv.set(f"Settings saved — {provider_name} · {model}  ✅ Keys saved to disk")
            win.destroy()

        mkbtn(btn_row, "💾  Save Settings", save,
              style="accent", px=22, py=8).pack(side="left", padx=6)
        mkbtn(btn_row, "Cancel", win.destroy,
              style="ghost", px=16, py=8).pack(side="left", padx=6)


    # ── Keyboard shortcuts ───────────────────────────────────────────
    def _show_welcome(self):
        """First-run welcome screen."""
        win = tk.Toplevel(self); win.title(f"Welcome to {APP_NAME}")
        win.configure(bg=WHITE); win.geometry("480x460"); win.grab_set()
        win.resizable(False, False)
        hdr = tk.Frame(win, bg=ACCENT, height=110); hdr.pack(fill="x"); safe_pp(hdr)
        tk.Label(hdr, text="✦", bg=ACCENT, fg=WHITE,
                 font=("Helvetica",30,"bold")).pack(pady=(16,2))
        tk.Label(hdr, text=f"Welcome to {APP_NAME}", bg=ACCENT, fg=WHITE,
                 font=("Helvetica",14,"bold")).pack()
        tk.Label(hdr, text=f"Version {APP_VERSION}  ·  AI-Powered Video Editor",
                 bg=ACCENT, fg="#C4B5FD", font=("Helvetica",9)).pack(pady=(0,12))
        body = tk.Frame(win, bg=WHITE); body.pack(fill="both", expand=True, padx=20, pady=10)
        tk.Label(body, text="Get started:", bg=WHITE, fg=TEXT,
                 font=("Helvetica",10,"bold")).pack(anchor="w", pady=(0,6))
        for icon, title, desc in [
            ("📁", "Import media",        "Drag & drop or use the Media panel"),
            ("🎨", "Adjust & grade",      "Professional colour tools in Inspector"),
            ("🤖", "AI generation",       "WaveSpeed · Sora · Image Gen built in"),
            ("🎬", "Export anywhere",     "MP4 · GIF · Social presets"),
            ("⌨",  "Keyboard shortcuts",  "Press ? anytime for shortcuts"),
        ]:
            row = tk.Frame(body, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=icon, bg=CARD, font=("Helvetica",14),
                     width=3).pack(side="left", padx=8, pady=6)
            tf = tk.Frame(row, bg=CARD); tf.pack(side="left", pady=6)
            tk.Label(tf, text=title, bg=CARD, fg=TEXT,
                     font=("Helvetica",9,"bold"), anchor="w").pack(anchor="w")
            tk.Label(tf, text=desc, bg=CARD, fg=MUTED,
                     font=("Helvetica",8), anchor="w").pack(anchor="w")
        mkbtn(win, "Start Editing  →", win.destroy,
              style="accent", py=10).pack(fill="x", padx=20, pady=12)

    def _check_deps(self):
        """Check for optional dependencies and show tips."""
        missing = []
        if not MOVIEPY_AVAILABLE: missing.append("moviepy (video processing)")
        if not PIL_AVAILABLE:     missing.append("pillow (image processing)")
        if not NUMPY_AVAILABLE:   missing.append("numpy (waveforms)")
        if missing and len(missing) >= 2:
            self._sv.set(f"⚠ Optional: {', '.join(missing[:2])} — pip install as needed")

    def _on_quit(self):
        """Confirm quit if unsaved changes, then exit cleanly."""
        title = self.title()
        if title.startswith("*"):
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes.\nQuit without saving?",
                icon="warning"
            ):
                return
        self._playing = False  # stop any playback
        self.destroy()

    def _start_autosave(self):
        """Auto-save project every N minutes to a temp file."""
        import tempfile, time as _t
        autosave_path = os.path.join(
            tempfile.gettempdir(), "proedit_autosave.cvp")
        def _do_save():
            try:
                mins = _SETTINGS.get("autosave_mins", 3)
                if mins == "Never":
                    self.after(300000, _do_save); return
                if self._proj.clips:
                    with open(autosave_path, "w") as f:
                        json.dump(self._proj.to_dict(), f)
                    self._sv.set(
                        f"Auto-saved · {_t.strftime('%H:%M')}")
            except Exception: pass
            interval = 60000 * int(_SETTINGS.get("autosave_mins", 3))
            self.after(interval, _do_save)
        interval = 60000 * int(_SETTINGS.get("autosave_mins", 3))
        self.after(interval, _do_save)

    def _bind_keys(self):
        self.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.bind("<Control-z>",     lambda e: self._undo())
        self.bind("<Control-Z>",     lambda e: self._undo())
        self.bind("<Control-y>",     lambda e: self._redo())
        self.bind("<Control-Y>",     lambda e: self._redo())
        self.bind("<Control-Shift-z>", lambda e: self._redo())
        self.bind("<Control-Z>",     lambda e: self._undo())
        self.bind("<Control-s>",     lambda e: self._save())
        self.bind("<Control-S>",     lambda e: self._save_as())
        self.bind("<Control-n>",     lambda e: self._new())
        self.bind("<Control-o>",     lambda e: self._open())
        self.bind("<Control-e>",     lambda e: self._export())
        self.bind("<Delete>",        lambda e: self._del_selected())
        self.bind("<BackSpace>",     lambda e: self._del_selected())
        self.bind("<space>",         lambda e: self._play_pause())
        self.bind("<Left>",          lambda e: self._step_clip(-1))
        self.bind("<Right>",         lambda e: self._step_clip(1))
        self.bind("?",               lambda e: self._show_shortcuts())
        self.bind("<F1>",            lambda e: self._show_shortcuts())
        self.bind("<Control-q>",     lambda e: self._on_quit())
        self.bind("<Control-w>",     lambda e: self._on_quit())
        self.bind("<F5>",            lambda e: self._timeline.refresh())
        self.bind("<Control-d>",     lambda e: self._duplicate_selected())
        self.bind("<Control-i>",     lambda e: self._panels["media"]._import())


    def _duplicate_selected(self):
        """Duplicate the currently selected clip (Ctrl+D)."""
        if self._sel is not None:
            self._timeline._duplicate_clip(self._sel)
            self._on_change()

    def _del_selected(self):
        if self._sel is not None:
            self._on_del(self._sel)

    def _play_pause(self):
        self._sv.set("▶ Preview — import a clip and select it to play")

    def _step_clip(self, direction):
        if not self._proj.clips: return
        n = len(self._proj.clips)
        new_sel = 0 if self._sel is None else (self._sel + direction) % n
        self._on_sel(new_sel)

    # ── Dark/Light mode toggle ────────────────────────────────────────
    def _toggle_theme(self):
        new_mode = "light" if _SETTINGS.get("theme","dark")=="dark" else "dark"
        _apply_theme(new_mode)
        # Restart app to apply (simplest reliable approach)
        if messagebox.askyesno("Theme Changed",
            f"Switch to {new_mode} mode? The app will restart to apply the theme."):
            import sys, subprocess
            subprocess.Popen([sys.executable] + sys.argv)
            self.destroy()

    # ── Recent projects ───────────────────────────────────────────────
    def _add_recent(self, path):
        recents = _SETTINGS.get("recent_projects",[])
        if path in recents: recents.remove(path)
        recents.insert(0, path)
        _SETTINGS["recent_projects"] = recents[:10]
        _save_config()

    def _show_shortcuts(self):
        """Show keyboard shortcuts reference."""
        win = tk.Toplevel(self); win.title("Keyboard Shortcuts")
        win.configure(bg=WHITE); win.geometry("480x580"); win.grab_set()
        win.resizable(False, False)
        hdr = tk.Frame(win, bg=ACCENT, height=52); hdr.pack(fill="x"); safe_pp(hdr)
        tk.Label(hdr, text="⌨  Keyboard Shortcuts", bg=ACCENT, fg=WHITE,
                 font=("Helvetica",13,"bold")).pack(side="left", padx=16, pady=14)
        tk.Button(hdr, text="✕", bg=ACCENT, fg=WHITE, relief="flat", bd=0,
                  font=("Helvetica",14), command=win.destroy,
                  activebackground="#5A52E0").pack(side="right", padx=12)
        sf, body = scrollframe(win)
        sf.pack(fill="both", expand=True)
        groups = [
            ("File", [
                ("Ctrl+N",        "New project"),
                ("Ctrl+O",        "Open project"),
                ("Ctrl+S",        "Save project"),
                ("Ctrl+Shift+S",  "Save As…"),
                ("Ctrl+E",        "Export video"),
                ("Ctrl+Q / Ctrl+W","Quit"),
            ]),
            ("Edit", [
                ("Ctrl+Z",        "Undo"),
                ("Ctrl+Y / Ctrl+Shift+Z","Redo"),
                ("Ctrl+D",        "Duplicate selected clip"),
                ("Delete",        "Remove selected clip"),
            ]),
            ("Timeline", [
                ("Click",         "Select clip"),
                ("Shift+Click",   "Add to selection"),
                ("← →",          "Navigate between clips"),
                ("Drag timeline", "Scrub preview frame"),
                ("F5",            "Refresh timeline"),
            ]),
            ("Playback", [
                ("Space",         "Play / Pause"),
            ]),
            ("Import", [
                ("Ctrl+I",        "Import media files"),
                ("Drag & Drop",   "Drop files onto timeline"),
            ]),
            ("Help", [
                ("?  or  F1",     "This shortcuts dialog"),
                ("ℹ (toolbar)",   "About ProEdit Studio"),
            ]),
        ]
        for group, shortcuts in groups:
            tk.Label(body, text=group.upper(), bg=WHITE, fg=ACCENT,
                     font=("Helvetica",8,"bold")).pack(anchor="w", padx=20, pady=(14,2))
            tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=16)
            for key, desc in shortcuts:
                row = tk.Frame(body, bg=WHITE); row.pack(fill="x", padx=20, pady=3)
                kb = tk.Label(row, text=key, bg=CARD, fg=TEXT,
                              font=("Helvetica",8,"bold"), padx=6, pady=3,
                              highlightthickness=1, highlightbackground=BORDER)
                kb.pack(side="left")
                tk.Label(row, text=desc, bg=WHITE, fg=MUTED,
                         font=("Helvetica",9), anchor="w").pack(side="left", padx=10)
        mkbtn(win, "Close", win.destroy, style="accent", py=8
              ).pack(fill="x", padx=16, pady=12)

    def _show_recent(self):
        recents = [p for p in _SETTINGS.get("recent_projects",[]) if os.path.exists(p)]
        if not recents:
            messagebox.showinfo("Recent Projects","No recent projects found."); return
        win = tk.Toplevel(self); win.title("Recent Projects")
        win.configure(bg=WHITE); win.geometry("520x420"); win.grab_set()
        # Canva-style header
        hdr=tk.Frame(win,bg=ACCENT,height=52); hdr.pack(fill="x"); safe_pp(hdr)
        tk.Label(hdr,text="🕐  Recent Projects",bg=ACCENT,fg=WHITE,
                 font=("Helvetica",13,"bold")).pack(side="left",padx=16,pady=14)
        tk.Button(hdr,text="✕",bg=ACCENT,fg=WHITE,relief="flat",bd=0,cursor="hand2",
                  font=("Helvetica",14),command=win.destroy,
                  activebackground="#5A52E0").pack(side="right",padx=12)
        sf,body = scrollframe(win,bg=WHITE); sf.pack(fill="both",expand=True)
        for path in recents:
            name = os.path.basename(path)
            card = tk.Frame(body,bg=CARD,highlightthickness=1,highlightbackground=BORDER)
            card.pack(fill="x",padx=16,pady=4)
            lf=tk.Frame(card,bg=CARD); lf.pack(side="left",padx=12,pady=8,fill="x",expand=True)
            tk.Label(lf,text=f"📁  {name}",bg=CARD,fg=TEXT,
                     font=("Helvetica",10,"bold"),anchor="w").pack(anchor="w")
            tk.Label(lf,text=os.path.dirname(path)[:50],bg=CARD,fg=MUTED,
                     font=F["xs"],anchor="w").pack(anchor="w")
            def _open_recent(p=path,w=win):
                w.destroy(); self._open_path(p)
            # Show project thumbnail if available
            thumb_path = path.replace(".cvp", "_thumb.png")
            if os.path.exists(thumb_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(thumb_path).resize((60,34), Image.LANCZOS)
                    tk_img = ImageTk.PhotoImage(img)
                    thumb_lbl = tk.Label(card, image=tk_img, bg=CARD)
                    thumb_lbl.image = tk_img
                    thumb_lbl.pack(side="left", padx=8, pady=8)
                except Exception:
                    pass
            mkbtn(card,"Open",_open_recent,style="accent",py=5,px=14
                  ).pack(side="right",padx=8,pady=8)
        mkbtn(win,"Close",win.destroy,style="ghost",py=6,px=16
              ).pack(pady=8,fill="x",padx=16)

    def _open_path(self, path):
        self._current_save_path = path
        try:
            with open(path) as f: data = json.load(f)
            self._proj.from_dict(data)
            for c in self._proj.clips: c.load_thumb()
            self._sel=None; self._inspector.clear()
            self._timeline._proj=self._proj; self._timeline.refresh()
            self._add_recent(path)
            self.title(f"{APP_NAME} — {os.path.basename(path)}")
            self._sv.set(f"Opened: {os.path.basename(path)}")
        except Exception as ex:
            messagebox.showerror("Error","Could not open project:\n" + str(ex))

    # ── GIF Export ────────────────────────────────────────────────────
    def _export_gif(self):
        if not self._proj.clips:
            messagebox.showwarning("Empty","Add clips first!"); return
        if not PIL_AVAILABLE:
            messagebox.showwarning("Missing","Pillow required for GIF export."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".gif", initialfile="export.gif",
            filetypes=[("GIF","*.gif"),("All","*.*")])
        if not path: return
        win = tk.Toplevel(self); win.title("Export GIF")
        win.configure(bg=WHITE); win.geometry("420x340"); win.grab_set()
        # Header
        ghdr = tk.Frame(win, bg=ACCENT, height=48); ghdr.pack(fill="x"); safe_pp(ghdr)
        tk.Label(ghdr, text="🎞  Export GIF", bg=ACCENT, fg=WHITE,
                 font=("Helvetica",12,"bold")).pack(side="left", padx=16, pady=12)
        tk.Button(ghdr, text="✕", bg=ACCENT, fg=WHITE, relief="flat", bd=0,
                  font=("Helvetica",14), command=win.destroy,
                  activebackground="#5A52E0").pack(side="right", padx=12)
        # Options
        opt_f = tk.Frame(win, bg=WHITE); opt_f.pack(fill="x", padx=16, pady=12)
        # FPS
        fps_row = tk.Frame(opt_f, bg=WHITE); fps_row.pack(fill="x", pady=4)
        tk.Label(fps_row, text="Frame Rate:", bg=WHITE, fg=TEXT,
                 font=F["sm"], width=12, anchor="w").pack(side="left")
        fps_v = tk.IntVar(value=12)
        for fps_val, fps_lbl in [(8,"8fps - tiny"),(12,"12fps - balanced"),(15,"15fps - smooth"),(24,"24fps - large")]:
            tk.Radiobutton(fps_row, text=fps_lbl, variable=fps_v, value=fps_val,
                           bg=WHITE, fg=TEXT, selectcolor=SEL, font=F["xs"],
                           cursor="hand2").pack(side="left", padx=4)
        # Max dimension
        size_row = tk.Frame(opt_f, bg=WHITE); size_row.pack(fill="x", pady=4)
        tk.Label(size_row, text="Max Width:", bg=WHITE, fg=TEXT,
                 font=F["sm"], width=12, anchor="w").pack(side="left")
        size_v = tk.IntVar(value=480)
        for sv, sl in [(320,"320px"),(480,"480px"),(640,"640px"),(960,"960px")]:
            tk.Radiobutton(size_row, text=sl, variable=size_v, value=sv,
                           bg=WHITE, fg=TEXT, selectcolor=SEL, font=F["xs"],
                           cursor="hand2").pack(side="left", padx=4)
        # Loop
        loop_v = tk.BooleanVar(value=True)
        loop_row = tk.Frame(opt_f, bg=WHITE); loop_row.pack(fill="x", pady=4)
        tk.Checkbutton(loop_row, text="Loop GIF", variable=loop_v,
                       bg=WHITE, fg=TEXT, selectcolor=SEL, font=F["sm"],
                       cursor="hand2").pack(side="left")
        # Estimate size label
        def _est_size(*a):
            dur = self._proj.total_dur()
            fps_val = fps_v.get(); w_val = size_v.get()
            frames_n = int(dur * fps_val)
            # Rough estimate: each frame ~(w*h*0.1) bytes after GIF compression
            h_val = int(w_val * 9/16)
            est_kb = int(frames_n * w_val * h_val * 0.08 / 1024)
            est_str = f"{est_kb/1024:.1f}MB" if est_kb > 1024 else f"{est_kb}KB"
            safe_cfg(est_lbl, text=f"Estimated size: ~{est_str}  ({frames_n} frames)")
        est_lbl = tk.Label(opt_f, text="", bg=WHITE, fg=MUTED, font=F["xs"])
        est_lbl.pack(anchor="w", pady=2)
        fps_v.trace_add("write", _est_size); size_v.trace_add("write", _est_size)
        _est_size()
        # Progress
        pgs = tk.StringVar(value="Ready to export…")
        tk.Label(win, textvariable=pgs, fg=MUTED, font=F["xs"], bg=WHITE).pack(pady=4, padx=16, anchor="w")
        bar = ttk.Progressbar(win, mode="determinate", length=380)
        bar.pack(padx=16, pady=4)
        mkbtn(win, "🎞  Export GIF", lambda: _start_gif(), style="accent", py=8
              ).pack(fill="x", padx=16, pady=8)

        def _start_gif():
            bar.config(mode="indeterminate"); bar.start(10)
            threading.Thread(target=_go, daemon=True).start()
        def _go():
            try:
                frames = []
                fps    = fps_v.get()
                max_w  = size_v.get()
                w,h    = self._proj.res
                scale  = min(1.0, max_w / max(w, 1))
                w = int(w * scale); h = int(h * scale)
                for clip in self._proj.clips:
                    self.after(0,lambda n=clip.filename:
                        pgs.set(f"Processing {n[:30]}…"))
                    if clip.is_image:
                        img = Image.open(clip.path).convert("RGB")
                        img = adjust(img,clip)
                        img.thumbnail((w,h),Image.LANCZOS)
                        frames.extend([img]*int(clip.trimmed*fps))
                    elif MOVIEPY_AVAILABLE:
                        vc = VideoFileClip(clip.path)
                        sub = vc.subclipped(clip.start_cut,clip.end_cut)
                        for t in range(0,int(sub.duration*fps)):
                            f = Image.fromarray(sub.get_frame(t/fps)).convert("RGB")
                            f = adjust(f,clip); f.thumbnail((w,h),Image.LANCZOS)
                            frames.append(f)
                        vc.close()
                if not frames:
                    self.after(0,lambda: messagebox.showwarning("No frames","No frames to export.")); return
                self.after(0,lambda: pgs.set(f"Saving {len(frames)} frames…"))
                frames[0].save(path, save_all=True, append_images=frames[1:],
                               optimize=True, duration=int(1000/fps), loop=0)
                self.after(0,lambda: (bar.stop(),
                    pgs.set(f"✅ Saved {len(frames)} frames!"),
                    messagebox.showinfo("Done!",f"GIF saved!{path}",parent=win)))
            except Exception as ex:
                self.after(0,lambda m=str(ex): (bar.stop(),
                    messagebox.showerror("Failed",m,parent=win)))
        threading.Thread(target=_go,daemon=True).start()

    # ── Social Media Export Presets ───────────────────────────────────
    def _export_social(self, preset):
        presets = {
            "TikTok":     (720,1280,"tiktok_export.mp4"),
            "Instagram":  (1080,1080,"instagram_export.mp4"),
            "YouTube":    (1920,1080,"youtube_export.mp4"),
            "Twitter/X":  (1280,720,"twitter_export.mp4"),
            "Story":      (1080,1920,"story_export.mp4"),
        }
        if preset not in presets: return
        w,h,fname = presets[preset]
        orig_ar = self._proj.aspect_ratio
        orig_res = self._proj.res
        # Temporarily set resolution
        self._proj.aspect_ratio = f"Custom {w}x{h}"
        self._export()
        self._proj.aspect_ratio = orig_ar

    def _show_social_presets(self):
        win = tk.Toplevel(self); win.title("Social Media Export")
        win.configure(bg=WHITE); win.geometry("360x380"); win.grab_set()
        hdr=tk.Frame(win,bg=ACCENT,height=52); hdr.pack(fill="x"); safe_pp(hdr)
        tk.Label(hdr,text="📱  Social Media Export",bg=ACCENT,fg=WHITE,
                 font=("Helvetica",13,"bold")).pack(side="left",padx=16,pady=14)
        tk.Button(hdr,text="✕",bg=ACCENT,fg=WHITE,relief="flat",bd=0,cursor="hand2",
                  font=("Helvetica",14),command=win.destroy,
                  activebackground="#5A52E0").pack(side="right",padx=12)
        tk.Label(win,text="Choose your platform for optimal resolution.",
                 bg=WHITE,fg=MUTED,font=F["xs"],
                 wraplength=320,justify="left").pack(padx=20,anchor="w",pady=(12,4))
        tk.Frame(win,bg=BORDER,height=1).pack(fill="x",padx=16,pady=4)
        presets = [
            ("📱 TikTok / Reels",  "9:16",  "720×1280"),
            ("📸 Instagram Post",  "1:1",   "1080×1080"),
            ("▶  YouTube",         "16:9",  "1920×1080"),
            ("🐦 Twitter / X",     "16:9",  "1280×720"),
            ("📖 Stories",         "9:16",  "1080×1920"),
        ]
        for label, ratio, res in presets:
            card = tk.Frame(win, bg=CARD,
                            highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", padx=16, pady=3)
            lf = tk.Frame(card, bg=CARD); lf.pack(side="left", padx=12, pady=8)
            tk.Label(lf, text=label, bg=CARD, fg=TEXT,
                     font=("Helvetica",10,"bold"), anchor="w").pack(anchor="w")
            tk.Label(lf, text=f"{ratio}  ·  {res}", bg=CARD, fg=MUTED,
                     font=F["xs"]).pack(anchor="w")
            mkbtn(card, "Export", lambda l=label: (win.destroy(), self._export()),
                  style="accent", py=5, px=14).pack(side="right", padx=8, pady=8)
        mkbtn(win, "Cancel", win.destroy, style="ghost", py=6, px=16
              ).pack(pady=10, fill="x", padx=16)

    def _new(self):
        title = self.title()
        if title.startswith("*"):
            if not messagebox.askyesno("New Project",
                "You have unsaved changes.\nStart a new project anyway?",
                icon="warning"):
                return
        elif not messagebox.askyesno("New Project","Start fresh? Unsaved changes will be lost."):
            return
        self._proj=Project(); self._sel=None
        self._undo_stack.clear(); self._redo_stack.clear()
        self._inspector.clear()
        for p in self._panels.values():
            p._proj=self._proj
        self._timeline._proj=self._proj; self._timeline.refresh()
        self.title(f"{APP_NAME} {APP_VERSION} — AI Video Editor")
        safe_cfg(self._undo_btn, state="disabled")
        if hasattr(self,"_redo_btn"): safe_cfg(self._redo_btn, state="disabled")
        self._sv.set("New project created.")
        Toast.show(self, "New project ready!", "success")

    def _save_as(self):
        """Force Save As dialog regardless of existing path."""
        p = filedialog.asksaveasfilename(
            defaultextension=".cvp",
            filetypes=[("ProEdit Project","*.cvp"),("JSON","*.json")],
            title="Save Project As…")
        if p:
            self._current_save_path = p
            with open(p,"w") as f: json.dump(self._proj.to_dict(),f,indent=2)
            self._add_recent(p)
            self.title(f"{APP_NAME} — {os.path.basename(p)}")
            self._sv.set(f"Saved as: {os.path.basename(p)}")
            Toast.show(self, f"Saved — {os.path.basename(p)}", "success")

    def _save(self):
        # Use existing path if already saved, otherwise prompt
        existing = getattr(self,"_current_save_path", None)
        if existing and os.path.exists(existing):
            p = existing
        else:
            p = filedialog.asksaveasfilename(
                defaultextension=".cvp",
                filetypes=[("ProEdit Project","*.cvp"),("JSON","*.json")],
                title="Save Project")
        if p:
            self._current_save_path = p
            with open(p,"w") as f: json.dump(self._proj.to_dict(),f,indent=2)
            self._add_recent(p)
            # Save thumbnail of first clip
            try:
                if self._proj.clips and PIL_AVAILABLE:
                    c = self._proj.clips[0]
                    if c.is_image:
                        img = Image.open(c.path).resize((120,68), Image.LANCZOS)
                    elif MOVIEPY_AVAILABLE:
                        vc = VideoFileClip(c.path)
                        img = Image.fromarray(vc.get_frame(0)).resize((120,68), Image.LANCZOS)
                        vc.close()
                    else:
                        img = None
                    if img:
                        img.save(p.replace(".cvp","_thumb.png"))
            except Exception: pass
            self.title(f"{APP_NAME} — {os.path.basename(p)}")
            self._sv.set(f"Saved: {os.path.basename(p)}")
            Toast.show(self, f"✅ Saved — {os.path.basename(p)}", "success")

    def _open(self):
        p=filedialog.askopenfilename(
            filetypes=[("ProEdit Project","*.cvp"),("JSON","*.json")],
            title="Open Project")
        if p: self._open_path(p)

    def _export(self):
        if not self._proj.clips:
            messagebox.showwarning("Empty","Add clips first!"); return
        win=tk.Toplevel(self); win.title("Export Video")
        win.configure(bg=WHITE); win.resizable(False,False)
        win.geometry("520x560"); win.grab_set()
        # Canva-style export dialog header
        ehdr=tk.Frame(win,bg=ACCENT,height=52); ehdr.pack(fill="x"); safe_pp(ehdr)
        tk.Label(ehdr,text="🎬  Export Video",bg=ACCENT,fg=WHITE,
                 font=("Helvetica",13,"bold")).pack(side="left",padx=16,pady=14)
        tk.Button(ehdr,text="✕",bg=ACCENT,fg=WHITE,relief="flat",bd=0,cursor="hand2",
                  font=("Helvetica",14),command=win.destroy,
                  activebackground="#5A52E0").pack(side="right",padx=12)
        pv=tk.StringVar(value=os.path.expanduser("~/output.mp4"))
        # File path row
        frow=tk.Frame(win,bg=WHITE); frow.pack(fill="x",padx=16,pady=12)
        tk.Label(frow,text="Save to",bg=WHITE,fg=MUTED,
                 font=("Helvetica",9,"bold"),width=7,anchor="w").pack(side="left")
        entry(frow,pv,width=34).pack(side="left",padx=4)
        def browse():
            p=filedialog.asksaveasfilename(defaultextension=".mp4",
                                            filetypes=[("MP4","*.mp4"),("MOV","*.mov")])
            if p: pv.set(p)
        mkbtn(frow,"Browse",browse,py=4,px=8).pack(side="left",padx=4)
        # Project info badge
        w,h=self._proj.res
        info_f=tk.Frame(win,bg=CARD,highlightthickness=1,highlightbackground=BORDER)
        info_f.pack(fill="x",padx=16,pady=4)
        dur = self._proj.total_dur()
        bitrate_mb_s = (w * h) / (1920 * 1080) * 2.0
        est_mb = dur * bitrate_mb_s
        est_str = f"{est_mb:.0f} MB" if est_mb >= 1 else f"{est_mb*1024:.0f} KB"
        tk.Label(info_f,
                 text=f"  {self._proj.aspect_ratio}  ·  {w}×{h}  ·  {self._proj.fps}fps  ·  {dur:.1f}s  ·  ~{est_str}",
                 bg=CARD,fg=TEXT,font=F["xs"],pady=8).pack(anchor="w")
        # Quality / codec row
        qf = tk.Frame(win, bg=WHITE); qf.pack(fill="x", padx=16, pady=(0,4))
        qrow = tk.Frame(qf, bg=WHITE); qrow.pack(fill="x")
        tk.Label(qrow, text="Quality:", bg=WHITE, fg=TEXT,
                 font=F["sm"], width=9, anchor="w").pack(side="left")
        q_var = tk.StringVar(value="Balanced")
        for ql in ["Fast","Balanced","High","Max"]:
            tk.Radiobutton(qrow, text=ql, variable=q_var, value=ql,
                           bg=WHITE, fg=TEXT, selectcolor=SEL,
                           font=F["xs"], cursor="hand2").pack(side="left", padx=4)
        arow = tk.Frame(qf, bg=WHITE); arow.pack(fill="x", pady=2)
        tk.Label(arow, text="Audio:", bg=WHITE, fg=TEXT,
                 font=F["sm"], width=9, anchor="w").pack(side="left")
        ab_var = tk.StringVar(value="192k")
        for ab in ["96k","128k","192k","320k"]:
            tk.Radiobutton(arow, text=ab, variable=ab_var, value=ab,
                           bg=WHITE, fg=TEXT, selectcolor=SEL,
                           font=F["xs"], cursor="hand2").pack(side="left", padx=3)
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)
        pgv=tk.IntVar(value=0); pgs=tk.StringVar(value="Ready to export…")
        # Progress ring canvas
        ring_cv = tk.Canvas(win, width=90, height=90, bg=WHITE,
                            highlightthickness=0)
        ring_cv.pack(pady=(10,0))
        ring_cv.create_oval(10,10,80,80, outline=BORDER, width=8)
        ring_arc = ring_cv.create_arc(10,10,80,80, start=90, extent=0,
                                       outline=ACCENT, width=8, style="arc")
        ring_txt = ring_cv.create_text(45,45, text="0%",
                                        fill=TEXT, font=("Helvetica",11,"bold"))
        def _update_ring(pct):
            ring_cv.itemconfig(ring_arc, extent=-int(pct*3.6))
            ring_cv.itemconfig(ring_txt, text=f"{int(pct)}%")
        lbl(win,textvariable=pgs,fg=MUTED,font=F["xs"],bg=WHITE).pack(pady=4)
        eb=mkbtn(win,"🎬  Start Export",style="accent",px=24,py=10); eb.pack(pady=10)
        if not MOVIEPY_AVAILABLE:
            lbl(win,"⚠ MoviePy not installed — pip install moviepy",fg=A2,font=F["xs"],bg=WHITE).pack()
            safe_cfg(eb,state="disabled")
        def prog(pct,msg): pgv.set(pct); pgs.set(msg); win.update_idletasks()
        def done(ok,info):
            if ok:
                pgs.set(f"✅ {info}")
                # Show success with option to open folder
                out_path = pv.get().strip()
                folder = os.path.dirname(out_path)
                if messagebox.askyesno("Export Complete!",
                    f"Video exported!\n\n{info}\n\nOpen folder?",
                    parent=win):
                    try:
                        import subprocess, sys as _sys
                        if _sys.platform=="win32":
                            subprocess.Popen(["explorer", folder])
                        elif _sys.platform=="darwin":
                            subprocess.Popen(["open", folder])
                        else:
                            subprocess.Popen(["xdg-open", folder])
                    except Exception: pass
            else:
                pgs.set("❌ Failed")
                messagebox.showerror("Export Failed", info, parent=win)
            safe_cfg(eb,state="normal")
        def start():
            out=pv.get().strip()
            if not out: messagebox.showwarning("No path","Set output file.",parent=win); return
            safe_cfg(eb,state="disabled")
            Exporter.run(self._proj,out,prog,done)
        safe_cfg(eb,command=start)

# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    App().mainloop()
