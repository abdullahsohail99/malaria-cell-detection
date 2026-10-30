import json
import os

import numpy as np
import streamlit as st
from PIL import Image

# ====== APNE LINKS YAHAN DAALEIN (jab ready ho jayein) ======
GITHUB_URL = "https://github.com/YOUR_USERNAME/malaria-cell-detection"
REPORT_URL = "PASTE_REPORT_LINK_HERE"
PPT_URL = "PASTE_PRESENTATION_LINK_HERE"
YOUTUBE_URL = "PASTE_YOUTUBE_LINK_HERE"
LINKEDIN_URL = "PASTE_LINKEDIN_POST_LINK_HERE"
VAL_ACCURACY = "92.85%"
# =============================================================

IMG_SIZE = (128, 128)
MODEL_PATH = "malaria_model.keras"
CLASSES_PATH = "class_names.json"

st.set_page_config(page_title="Malaria Cell Detection", page_icon="🔬", layout="wide")


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
    x = np.expand_dims(x, axis=0)  # model ke andar rescaling already hai
    p = float(model.predict(x, verbose=0)[0][0])  # probability of class index 1
    if p >= 0.5:
        return class_names[1], p
    return class_names[0], 1 - p


def link_line(label, url):
    if url.startswith("http") and "YOUR_USERNAME" not in url:
        st.markdown(f"- **{label}:** [{url}]({url})")
    else:
        st.markdown(f"- **{label}:** coming soon")


st.title("🔬 Malaria Cell Detection using Deep Learning")
st.caption("Blood cell image classification: Parasitized vs Uninfected (MobileNetV2 transfer learning)")

tab_demo, tab_data, tab_results, tab_links = st.tabs(
    ["🧪 Live Demo", "📦 Dataset & Code", "📈 Results", "🔗 Project Links"]
)

# ---------------- Live Demo ----------------
with tab_demo:
    st.subheader("Cell image upload karein aur prediction dekhein")
    left, right = st.columns(2)

    with left:
        uploaded = st.file_uploader("Image upload karein", type=["png", "jpg", "jpeg"])
        samples = []
        if os.path.isdir("sample_images"):
            samples = sorted(
                f for f in os.listdir("sample_images")
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            )
        chosen = None
        if samples:
            chosen = st.selectbox("Ya sample image chunein", ["-- none --"] + samples)

    image = None
    if uploaded is not None:
        image = Image.open(uploaded)
    elif chosen and chosen != "-- none --":
        image = Image.open(os.path.join("sample_images", chosen))

    with right:
        if image is not None:
            st.image(image, caption="Input image", width=250)
            label, conf = predict(image)
            if label == "Parasitized":
                st.error(f"Prediction: **{label}** (malaria parasite detected)")
            else:
                st.success(f"Prediction: **{label}** (no parasite detected)")
            st.write(f"Confidence: **{conf * 100:.2f}%**")
            st.progress(min(max(conf, 0.0), 1.0))
        else:
            st.info("Prediction dekhne ke liye image upload karein ya sample chunein.")

    st.caption("Note: Ye ek educational project hai, medical diagnosis ke liye nahi.")

# ---------------- Dataset & Code ----------------
with tab_data:
    st.subheader("Problem Statement")
    st.write(
        "Malaria ki traditional diagnosis microscope se blood smear dekh kar hoti hai, "
        "jo slow aur manual kaam hai. Is project mein deep learning se blood cell images ko "
        "Parasitized ya Uninfected classify kiya gaya hai."
    )
    st.subheader("Dataset")
    st.markdown(
        """
- **Name:** Cell Images for Detecting Malaria (Kaggle, NIH data)
- **Link:** https://www.kaggle.com/datasets/iarunava/cell-images-for-detecting-malaria
- **Size:** 27,558 images, 2 classes (13,779 Parasitized, 13,779 Uninfected), balanced
- **Split:** 80% training, 20% validation
- **Preprocessing:** images ko 128x128 par resize kiya, pixel values ko [-1, 1] mein scale kiya
"""
    )
    st.subheader("Model Architecture")
    st.markdown(
        """
- Base: **MobileNetV2** (ImageNet pretrained, frozen)
- Augmentation: random horizontal/vertical flip
- Head: GlobalAveragePooling2D, Dropout(0.3), Dense(1, sigmoid)
- Loss: binary crossentropy, Optimizer: Adam, Epochs: 5, Batch size: 64
- Framework: TensorFlow / Keras
"""
    )
    st.subheader("Code & Weights")
    st.markdown(
        f"Poora source code, notebook aur trained weights (`{MODEL_PATH}`) GitHub repository mein maujood hain."
    )
    link_line("GitHub Repository", GITHUB_URL)

# ---------------- Results ----------------
with tab_results:
    st.subheader("Training Results")
    c1, c2 = st.columns(2)
    c1.metric("Validation Accuracy", VAL_ACCURACY)
    c2.metric("Epochs", "5")
    if os.path.exists("accuracy_plot.png"):
        st.image("accuracy_plot.png", caption="Training vs Validation Accuracy", width=600)

# ---------------- Links ----------------
with tab_links:
    st.subheader("Project Links")
    link_line("GitHub Repository", GITHUB_URL)
    link_line("Project Report", REPORT_URL)
    link_line("Presentation", PPT_URL)
    link_line("YouTube Video", YOUTUBE_URL)
    link_line("LinkedIn Post", LINKEDIN_URL)
