import json
import os
import re

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# =====================  PROJECT LINKS (sirf yahan badlein)  =====================
APP_URL = "https://malaria-cell-detection-by-abdullah-sohail222.streamlit.app/"
GITHUB_URL = "https://github.com/abdullahsohail99/malaria-cell-detection"
PPT_URL = "https://docs.google.com/presentation/d/13W-JN3cPg9BupnFXJsGnwF9_dQk4NzO8/edit?usp=sharing"
REPORT_URL = "https://docs.google.com/document/d/1yrGkvC2RCtqNjGZklubsDeO_BMYsIKqA/edit?usp=sharing"
YOUTUBE_URL = ""   # YouTube link bana kar yahan paste karein, video page par khud embed ho jayegi
LINKEDIN_URL = ""  # LinkedIn post ka link yahan paste karein
KAGGLE_URL = "https://www.kaggle.com/datasets/iarunava/cell-images-for-detecting-malaria"
VAL_ACCURACY = "92.85%"
# ================================================================================

IMG_SIZE = (128, 128)
MODEL_PATH = "malaria_model.keras"
CLASSES_PATH = "class_names.json"

st.set_page_config(page_title="Malaria Cell Detection", page_icon="🔬", layout="wide",
                   initial_sidebar_state="collapsed")


def html(s: str) -> str:
    """Markdown ko HTML block todne se bachane ke liye: blank lines aur indentation hata do."""
    return "\n".join(line.strip() for line in s.splitlines() if line.strip())


def file_id(url: str):
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None


def drive_preview(url: str):
    fid = file_id(url)
    return f"https://drive.google.com/file/d/{fid}/preview" if fid else None


def drive_download(url: str):
    fid = file_id(url)
    return f"https://drive.google.com/uc?export=download&id={fid}" if fid else None


def youtube_embed(url: str):
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url or "")
    return f"https://www.youtube.com/embed/{m.group(1)}" if m else None


def embed(url: str, height: int):
    if hasattr(st, "iframe"):  # naya Streamlit (components.v1.html purana ho chuka hai)
        st.iframe(url, width="stretch", height=height)
    else:
        components.html(
            f'<style>html,body{{margin:0;background:transparent}}</style>'
            f'<iframe src="{url}" allowfullscreen loading="lazy" '
            f'style="width:100%;height:{height - 6}px;border:1px solid #e8eaed;border-radius:24px;background:#fff"></iframe>',
            height=height,
        )


# ------------------------------- Model helpers -------------------------------
@st.cache_resource
def load_model():
    import tensorflow as tf
    return tf.keras.models.load_model(MODEL_PATH)


@st.cache_data
def load_class_names():
    with open(CLASSES_PATH) as f:
        return json.load(f)


def predict(img: Image.Image):
    model = load_model()
    class_names = load_class_names()  # ["Parasitized", "Uninfected"]
    x = np.array(img.convert("RGB").resize(IMG_SIZE), dtype="float32")
    x = np.expand_dims(x, axis=0)  # rescaling model ke andar hai
    p = float(model.predict(x, verbose=0)[0][0])  # class index 1 (Uninfected) ki probability
    if p >= 0.5:
        return class_names[1], p
    return class_names[0], 1 - p


# --------------------------------- Charts (SVG) ---------------------------------
def line_svg(a, b, ymin, ymax, ticks, tick_fmt, end_fmt):
    W, H, L, R, T, B = 560, 320, 56, 74, 20, 44
    n = len(a)
    X = lambda i: L + i * (W - L - R) / (n - 1)
    Y = lambda v: T + (ymax - v) * (H - T - B) / (ymax - ymin)
    grid = "".join(
        f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="#e3e5e8"/>'
        f'<text x="{L - 10}" y="{Y(t) + 4:.1f}" text-anchor="end" font-size="12" fill="#5f6368">{tick_fmt(t)}</text>'
        for t in ticks)
    xl = "".join(f'<text x="{X(i):.1f}" y="{H - 22}" text-anchor="middle" font-size="12" fill="#5f6368">{i + 1}</text>' for i in range(n))
    xl += f'<text x="{(L + W - R) / 2:.1f}" y="{H - 4}" text-anchor="middle" font-size="12" fill="#5f6368">Epoch</text>'

    def series(v, c):
        pts = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(v))
        dots = "".join(f'<circle cx="{X(i):.1f}" cy="{Y(x):.1f}" r="5" fill="{c}" stroke="#fff" stroke-width="2"/>' for i, x in enumerate(v))
        lab = f'<text x="{X(n - 1) + 12:.1f}" y="{Y(v[-1]) + 4:.1f}" font-size="13" font-weight="600" fill="{c}">{end_fmt(v[-1])}</text>'
        return (f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="3" '
                f'stroke-linejoin="round" stroke-linecap="round"/>{dots}{lab}')

    return (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg">'
            f'{grid}{xl}{series(a, "#2a78d6")}{series(b, "#eb6834")}</svg>')


ACC_TR = [0.8532, 0.9038, 0.9122, 0.9141, 0.9163]
ACC_VA = [0.9136, 0.9238, 0.9251, 0.9278, 0.9285]
LOSS_TR = [0.3331, 0.2427, 0.2277, 0.2212, 0.2180]
LOSS_VA = [0.2241, 0.2008, 0.1937, 0.1886, 0.1877]
LEGEND = ('<div class="legend"><span><i style="background:#2a78d6"></i>Training</span>'
          '<span><i style="background:#eb6834"></i>Validation</span></div>')

# ----------------------------------- Styling -----------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');
:root{--ink:#0b0b0f;--muted:#5f6368;--line:#e8eaed;--card:#f4f6f8;}
html{scroll-behavior:smooth}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#fff!important;color:var(--ink)}
.stApp,.stApp p,.stApp label,.stApp button,.stApp h1,.stApp h2,.stApp h3,.stApp h4,
[data-testid="stMarkdownContainer"] *{font-family:'Google Sans','DM Sans',Arial,sans-serif}
#MainMenu,header[data-testid="stHeader"],footer,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1240px!important;padding:84px 32px 0!important}
[data-testid="stMarkdownContainer"] a{text-decoration:none}
iframe{border-radius:24px;border:1px solid #e8eaed}

.dm-nav{position:fixed;top:0;left:0;right:0;z-index:1000;height:68px;display:flex;align-items:center;justify-content:space-between;
padding:0 clamp(16px,4vw,40px);background:rgba(255,255,255,.86);backdrop-filter:saturate(180%) blur(16px);border-bottom:1px solid var(--line)}
.dm-brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:18px;color:var(--ink)!important}
.dm-dot{width:22px;height:22px;border-radius:50%;background:conic-gradient(from 200deg,#4285f4,#9b72cb,#d96570,#f6b26b,#4285f4)}
.dm-links{display:flex;gap:26px;align-items:center}
.dm-links a.l{color:var(--ink)!important;font-size:15px;font-weight:500;opacity:.75}
.dm-links a.l:hover{opacity:1}
.btn{display:inline-flex;align-items:center;gap:8px;padding:15px 28px;border-radius:999px;font-weight:600;font-size:16px;transition:.2s}
.btn-dark{background:var(--ink);color:#fff!important}.btn-dark:hover{background:#34343c}
.btn-line{border:1.5px solid var(--ink);color:var(--ink)!important;background:transparent}
.btn-line:hover{background:var(--ink);color:#fff!important}
.btn-sm{padding:9px 18px;font-size:14px}
.row{display:flex;gap:12px;flex-wrap:wrap}

.hero{position:relative;padding:64px 0 8px;overflow:hidden}
.orb{position:absolute;right:-140px;top:-80px;width:560px;height:560px;border-radius:50%;filter:blur(72px);opacity:.5;z-index:0;
background:radial-gradient(circle at 30% 30%,#4285f4,transparent 60%),radial-gradient(circle at 72% 38%,#d96570,transparent 55%),radial-gradient(circle at 50% 82%,#9b72cb,transparent 60%)}
.hero>*:not(.orb){position:relative;z-index:1}
.eyebrow{font-size:14px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:18px}
.hero h1{font-size:clamp(44px,8vw,104px);line-height:.98;letter-spacing:-.04em;font-weight:500;margin:0 0 26px;max-width:960px;padding:0}
.grad{background:linear-gradient(90deg,#4285f4,#9b72cb 55%,#d96570);-webkit-background-clip:text;background-clip:text;color:transparent}
.lead{font-size:clamp(18px,2vw,23px);line-height:1.45;color:var(--muted);max-width:700px;margin:0 0 34px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:52px}
.stat{background:var(--card);border-radius:28px;padding:28px}
.stat b{display:block;font-size:clamp(30px,4vw,52px);letter-spacing:-.03em;font-weight:500}
.stat span{color:var(--muted);font-size:15px}

.sec{padding-top:104px;scroll-margin-top:72px}
.sec h2{font-size:clamp(32px,5vw,58px);letter-spacing:-.035em;line-height:1.05;font-weight:500;margin:0 0 16px;padding:0}
.sub{color:var(--muted);font-size:clamp(17px,1.8vw,20px);max-width:680px;line-height:1.5;margin:0 0 30px}
.secbar{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:8px}

.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.card{border-radius:28px;padding:30px;min-height:290px;display:flex;flex-direction:column;justify-content:space-between}
.card h3{font-size:26px;letter-spacing:-.02em;font-weight:500;margin:0 0 10px;padding:0}
.card p{margin:0;color:#3c4043;font-size:16px;line-height:1.5}
.tag{font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#3c4043;opacity:.7}
.big{font-size:44px;letter-spacing:-.04em;font-weight:500}
.c1{background:#e8f0fe}.c2{background:#f3e8fd}.c3{background:#fce8e6}.c4{background:#e6f4ea}

.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel{background:var(--card);border-radius:28px;padding:32px}
.panel h3{font-size:24px;letter-spacing:-.02em;font-weight:500;margin:0 0 18px;padding:0}
.kv{display:flex;justify-content:space-between;gap:20px;padding:14px 0;border-bottom:1px solid #dadce0;font-size:16px}
.kv:last-child{border-bottom:none}.kv span:first-child{color:var(--muted)}.kv span:last-child{font-weight:500;text-align:right}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:22px}
.chip{background:#fff;border:1px solid var(--line);border-radius:999px;padding:10px 16px;font-size:15px;font-weight:500}
.chip.hi{background:var(--ink);color:#fff;border-color:var(--ink)}
.arrow{color:var(--muted)}
.legend{display:flex;gap:18px;font-size:14px;color:var(--muted);margin:-6px 0 8px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px}
.note{color:var(--muted);font-size:15px;line-height:1.5;margin-top:14px}

.st-key-demo_box,[data-testid="stVerticalBlockBorderWrapper"]{border-radius:32px!important;border:none!important;background:var(--card)!important;padding:20px!important}
[data-testid="stFileUploaderDropzone"]{background:#fff!important;border:1.5px dashed #c4c7c5!important;border-radius:20px!important}
[data-testid="stFileUploaderDropzone"] button{border-radius:999px!important;border:1.5px solid var(--ink)!important;background:#fff!important;color:var(--ink)!important}
[data-baseweb="select"]>div{border-radius:16px!important;background:#fff!important}
[data-testid="stImage"] img{border-radius:20px}
.res{background:#fff;border-radius:24px;padding:30px;min-height:250px}
.pill{display:inline-block;padding:8px 18px;border-radius:999px;font-weight:600;font-size:15px}
.pill.bad{background:#fce8e6;color:#c5221f}.pill.good{background:#e6f4ea;color:#137333}.pill.idle{background:#eef0f2;color:var(--muted)}
.res h3{font-size:clamp(34px,4vw,50px);letter-spacing:-.035em;font-weight:500;margin:18px 0 4px;padding:0}
.bar{height:10px;background:#e8eaed;border-radius:99px;overflow:hidden;margin:18px 0 10px}
.bar i{display:block;height:100%;border-radius:99px}

.vid{border-radius:24px;overflow:hidden}
.soon{background:var(--card);border-radius:28px;padding:48px;text-align:center;color:var(--muted);font-size:18px}

.foot{background:var(--ink);color:#fff;border-radius:36px;margin-top:120px;padding:60px clamp(24px,5vw,64px) 36px}
.foot-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px}
.foot h4{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#9aa0a6;margin:0 0 14px;font-weight:600;padding:0}
.foot a{display:block;color:#fff!important;opacity:.88;margin:10px 0;font-size:16px}
.foot a:hover{opacity:1}
.foot .brand{font-size:30px;letter-spacing:-.03em;font-weight:500;line-height:1.1;max-width:340px}
.foot small{display:block;margin-top:44px;color:#9aa0a6;font-size:14px;border-top:1px solid #3c4043;padding-top:22px;line-height:1.6}

@media(max-width:900px){
.cards{grid-template-columns:1fr 1fr}.two{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}
.foot-grid{grid-template-columns:1fr 1fr}.dm-links a.l{display:none}.orb{opacity:.35}
}
@media(max-width:560px){.cards{grid-template-columns:1fr}.block-container,[data-testid="stMainBlockContainer"]{padding:84px 16px 0!important}}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ------------------------------------ Nav + Hero ------------------------------------
st.markdown(html(f"""
<div class="dm-nav">
<a class="dm-brand" href="#top" target="_self"><span class="dm-dot"></span>Malaria Cell Detection</a>
<div class="dm-links">
<a class="l" href="#demo" target="_self">Demo</a>
<a class="l" href="#project" target="_self">Project</a>
<a class="l" href="#results" target="_self">Results</a>
<a class="l" href="#slides" target="_self">Slides</a>
<a class="l" href="#report" target="_self">Report</a>
<a class="l" href="#video" target="_self">Video</a>
<a class="btn btn-dark btn-sm" href="{GITHUB_URL}" target="_blank" rel="noopener">GitHub</a>
</div>
</div>
<div class="hero" id="top">
<div class="orb"></div>
<div class="eyebrow">Deep Learning Semester Project</div>
<h1>Detecting malaria,<br><span class="grad">one cell at a time.</span></h1>
<p class="lead">A MobileNetV2 transfer learning model that looks at a blood cell image and tells whether it is
parasitized or uninfected. Trained on 27,558 NIH cell images and deployed as this web app.</p>
<div class="row">
<a class="btn btn-dark" href="#demo" target="_self">Try the demo</a>
<a class="btn btn-line" href="{GITHUB_URL}" target="_blank" rel="noopener">View on GitHub</a>
</div>
<div class="stats">
<div class="stat"><b>{VAL_ACCURACY}</b><span>Validation accuracy</span></div>
<div class="stat"><b>27,558</b><span>Cell images</span></div>
<div class="stat"><b>2</b><span>Classes, perfectly balanced</span></div>
<div class="stat"><b>5</b><span>Epochs, a few minutes on a free GPU</span></div>
</div>
</div>
"""), unsafe_allow_html=True)

# ------------------------------------ Live demo ------------------------------------
st.markdown(html("""
<div class="sec" id="demo">
<div class="eyebrow">Live demo</div>
<h2>Try the model yourself</h2>
<p class="sub">Upload a blood cell image or pick a sample. The model returns a prediction and a confidence score.</p>
</div>
"""), unsafe_allow_html=True)

try:
    demo_box = st.container(border=True, key="demo_box")
except TypeError:
    demo_box = st.container(border=True)

with demo_box:
    left, right = st.columns(2, gap="large")
    image = None
    with left:
        uploaded = st.file_uploader("Upload a cell image", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        samples = []
        if os.path.isdir("sample_images"):
            samples = sorted(f for f in os.listdir("sample_images") if f.lower().endswith((".png", ".jpg", ".jpeg")))
        chosen = None
        if samples:
            chosen = st.selectbox("Or pick a sample image", ["None"] + samples)
        if uploaded is not None:
            image = Image.open(uploaded)
        elif chosen and chosen != "None":
            image = Image.open(os.path.join("sample_images", chosen))
        if image is not None:
            st.image(image, width=200)
    with right:
        if image is None:
            st.markdown(html("""
            <div class="res"><span class="pill idle">Waiting for an image</span>
            <h3>No prediction yet</h3>
            <p class="note">Upload an image on the left, or choose one of the sample images.</p></div>
            """), unsafe_allow_html=True)
        else:
            try:
                label, conf = predict(image)
                bad = label == "Parasitized"
                color = "#d93025" if bad else "#188038"
                msg = "Malaria parasite detected in this cell." if bad else "No malaria parasite detected in this cell."
                st.markdown(html(f"""
                <div class="res"><span class="pill {'bad' if bad else 'good'}">{'Parasitized' if bad else 'Uninfected'}</span>
                <h3>{conf * 100:.1f}% confident</h3>
                <div class="bar"><i style="width:{conf * 100:.1f}%;background:{color}"></i></div>
                <p class="note">{msg}</p></div>
                """), unsafe_allow_html=True)
            except Exception as e:  # model file missing etc.
                st.error(f"Prediction could not run: {e}")

st.markdown('<p class="note" style="margin-top:14px">Educational project. Not a medical diagnostic tool.</p>', unsafe_allow_html=True)

# ------------------------------------ Project ------------------------------------
st.markdown(html(f"""
<div class="sec" id="project">
<div class="eyebrow">The project</div>
<h2>From a Kaggle dataset to a live app</h2>
<p class="sub">Malaria is usually diagnosed by checking blood films under a microscope, a slow and manual job.
This project automates the decision for a single cell image.</p>
<div class="cards">
<div class="card c1"><div class="tag">Dataset</div><div><div class="big">27,558</div><h3>Cell images</h3><p>NIH blood cell images from Kaggle. 13,779 Parasitized and 13,779 Uninfected.</p></div></div>
<div class="card c2"><div class="tag">Model</div><div><div class="big">MobileNetV2</div><h3>Transfer learning</h3><p>ImageNet weights kept frozen, with a small classifier trained on top.</p></div></div>
<div class="card c3"><div class="tag">Training</div><div><div class="big">5 epochs</div><h3>Minutes, not hours</h3><p>Adam optimizer, batch size 64, 128 x 128 inputs on a Colab T4 GPU.</p></div></div>
<div class="card c4"><div class="tag">Deployment</div><div><div class="big">Streamlit</div><h3>Live from GitHub</h3><p>Code and weights are in a public repository and served on Streamlit Cloud.</p></div></div>
</div>
</div>
<div class="sec" style="padding-top:16px">
<div class="two">
<div class="panel"><h3>Dataset details</h3>
<div class="kv"><span>Source</span><span><a href="{KAGGLE_URL}" target="_blank" rel="noopener" style="color:#1a73e8">Kaggle, NIH data</a></span></div>
<div class="kv"><span>Images</span><span>27,558</span></div>
<div class="kv"><span>Classes</span><span>Parasitized 13,779 / Uninfected 13,779</span></div>
<div class="kv"><span>Input size</span><span>128 x 128 RGB</span></div>
<div class="kv"><span>Split</span><span>80% train (22,046) / 20% validation (5,512)</span></div>
</div>
<div class="panel"><h3>Model and code</h3>
<div class="flow"><span class="chip">Image 128x128</span><span class="arrow">&rarr;</span><span class="chip">Flip + Rescale</span><span class="arrow">&rarr;</span><span class="chip hi">MobileNetV2 (frozen)</span><span class="arrow">&rarr;</span><span class="chip">Avg Pool</span><span class="arrow">&rarr;</span><span class="chip">Dropout 0.3</span><span class="arrow">&rarr;</span><span class="chip">Dense 1 + sigmoid</span></div>
<div class="kv"><span>Loss / Optimizer</span><span>Binary cross-entropy / Adam</span></div>
<div class="kv"><span>Epochs / Batch</span><span>5 / 64</span></div>
<div class="kv"><span>Framework</span><span>TensorFlow and Keras</span></div>
<div class="kv"><span>Code and weights</span><span><a href="{GITHUB_URL}" target="_blank" rel="noopener" style="color:#1a73e8">GitHub repository</a></span></div>
</div>
</div>
</div>
"""), unsafe_allow_html=True)

# ------------------------------------ Results ------------------------------------
st.markdown(html(f"""
<div class="sec" id="results">
<div class="eyebrow">Results</div>
<h2>{VAL_ACCURACY} validation accuracy</h2>
<p class="sub">Both losses fall every epoch and the training and validation curves stay close, so there is no sign of overfitting yet.
Validation is a little higher than training because dropout and flips only apply while training.</p>
<div class="two">
<div class="panel"><h3>Accuracy per epoch</h3>{LEGEND}{line_svg(ACC_TR, ACC_VA, 0.84, 0.94, [0.84, 0.86, 0.88, 0.90, 0.92, 0.94], lambda t: f"{t * 100:.0f}%", lambda v: f"{v * 100:.2f}%")}</div>
<div class="panel"><h3>Loss per epoch</h3>{LEGEND}{line_svg(LOSS_TR, LOSS_VA, 0.15, 0.35, [0.15, 0.20, 0.25, 0.30, 0.35], lambda t: f"{t:.2f}", lambda v: f"{v:.4f}")}</div>
</div>
</div>
"""), unsafe_allow_html=True)

# ------------------------------------ Presentation ------------------------------------
ppt_prev, ppt_dl = drive_preview(PPT_URL), drive_download(PPT_URL)
st.markdown(html(f"""
<div class="sec" id="slides">
<div class="secbar"><div><div class="eyebrow">Presentation</div><h2>Project slides</h2></div>
<div class="row"><a class="btn btn-line btn-sm" href="{PPT_URL}" target="_blank" rel="noopener">Open in new tab</a>
{f'<a class="btn btn-dark btn-sm" href="{ppt_dl}" target="_blank" rel="noopener">Download</a>' if ppt_dl else ''}</div></div>
<p class="sub">The 10-slide deck used for the voiceover video.</p>
</div>
"""), unsafe_allow_html=True)
if ppt_prev:
    embed(ppt_prev, 640)

# ------------------------------------ Report ------------------------------------
rep_prev, rep_dl = drive_preview(REPORT_URL), drive_download(REPORT_URL)
st.markdown(html(f"""
<div class="sec" id="report">
<div class="secbar"><div><div class="eyebrow">Report</div><h2>Project report</h2></div>
<div class="row"><a class="btn btn-line btn-sm" href="{REPORT_URL}" target="_blank" rel="noopener">Open in new tab</a>
{f'<a class="btn btn-dark btn-sm" href="{rep_dl}" target="_blank" rel="noopener">Download</a>' if rep_dl else ''}</div></div>
<p class="sub">Problem statement, dataset, architecture, training details and results.</p>
</div>
"""), unsafe_allow_html=True)
if rep_prev:
    embed(rep_prev, 760)

# ------------------------------------ Video ------------------------------------
st.markdown(html("""
<div class="sec" id="video">
<div class="eyebrow">Video</div>
<h2>Walkthrough</h2>
<p class="sub">A voiceover explanation of the slides.</p>
</div>
"""), unsafe_allow_html=True)
yt = youtube_embed(YOUTUBE_URL)
if yt:
    embed(yt, 560)
else:
    st.markdown('<div class="soon">Video coming soon</div>', unsafe_allow_html=True)

# ------------------------------------ Footer ------------------------------------
yt_link = f'<a href="{YOUTUBE_URL}" target="_blank" rel="noopener">YouTube video</a>' if YOUTUBE_URL else ""
li_link = f'<a href="{LINKEDIN_URL}" target="_blank" rel="noopener">LinkedIn post</a>' if LINKEDIN_URL else ""
st.markdown(html(f"""
<div class="foot">
<div class="foot-grid">
<div class="brand">Malaria Cell Detection using Deep Learning</div>
<div><h4>Explore</h4><a href="#demo" target="_self">Live demo</a><a href="#project" target="_self">Project</a><a href="#results" target="_self">Results</a></div>
<div><h4>Resources</h4><a href="{GITHUB_URL}" target="_blank" rel="noopener">GitHub repository</a><a href="{KAGGLE_URL}" target="_blank" rel="noopener">Kaggle dataset</a><a href="{APP_URL}" target="_blank" rel="noopener">Live app</a></div>
<div><h4>Submission</h4><a href="{PPT_URL}" target="_blank" rel="noopener">Presentation</a><a href="{REPORT_URL}" target="_blank" rel="noopener">Project report</a>{yt_link}{li_link}</div>
</div>
<small>Deep Learning semester project. Built with TensorFlow, Keras and Streamlit. Educational use only, not a medical diagnostic tool.</small>
</div>
"""), unsafe_allow_html=True)
