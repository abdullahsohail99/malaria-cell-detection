# Malaria Cell Detection using Deep Learning

Binary image classification of blood cell images: **Parasitized** vs **Uninfected**, using MobileNetV2 transfer learning. Deployed as a Streamlit web app.

## Dataset
- Cell Images for Detecting Malaria (NIH data on Kaggle): https://www.kaggle.com/datasets/iarunava/cell-images-for-detecting-malaria
- 27,558 images, 2 balanced classes (13,779 each)
- The dataset is not stored in this repo because of its size (~339 MB). Download it from the link above, or in Python:

```python
import kagglehub
path = kagglehub.dataset_download("iarunava/cell-images-for-detecting-malaria")
```

## Model
- MobileNetV2 (ImageNet weights, frozen) + GlobalAveragePooling + Dropout(0.3) + Dense(1, sigmoid)
- Input size 128x128, 5 epochs, Adam, binary crossentropy
- Validation accuracy: **92.85%**
- Trained weights: `malaria_model.keras`
- Class names: `class_names.json` (index 0 = Parasitized, index 1 = Uninfected)

## Repository Structure
- `app.py`: Streamlit web app
- `requirements.txt`: dependencies
- `malaria_model.keras`: trained model weights
- `class_names.json`: class labels
- `accuracy_plot.png`: training curves
- `sample_images/`: example cell images for the demo
- `*.ipynb`: training notebook

## Run Locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Links
- Live app: PASTE_STREAMLIT_URL_HERE
- Report: PASTE_REPORT_LINK_HERE
- Presentation: PASTE_PRESENTATION_LINK_HERE
- YouTube video: PASTE_YOUTUBE_LINK_HERE
- LinkedIn post: PASTE_LINKEDIN_POST_LINK_HERE

Note: Educational project, not for medical diagnosis.
