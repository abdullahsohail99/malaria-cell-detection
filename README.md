# Malaria Cell Detection using Deep Learning

Binary image classification of blood cell images: **Parasitized** vs **Uninfected**, using MobileNetV2 transfer learning, deployed as a one-page Streamlit web app.

## Project Links
- **Live app:** https://malaria-cell-detection-by-abdullah-sohail222.streamlit.app/
- **GitHub repository:** https://github.com/abdullahsohail99/malaria-cell-detection
- **Presentation:** https://docs.google.com/presentation/d/13W-JN3cPg9BupnFXJsGnwF9_dQk4NzO8/edit?usp=sharing
- **Project report:** https://docs.google.com/document/d/1yrGkvC2RCtqNjGZklubsDeO_BMYsIKqA/edit?usp=sharing
- **YouTube video:** (add link)
- **LinkedIn post:** (add link)

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
- Input size 128x128, 5 epochs, batch size 64, Adam, binary crossentropy
- Validation accuracy: **92.85%**
- Trained weights: `malaria_model.keras`
- Class names: `class_names.json` (index 0 = Parasitized, index 1 = Uninfected)

## Repository Structure
- `app.py`: one-page Streamlit web app (demo, project details, results, embedded slides and report)
- `.streamlit/config.toml`: light theme settings for the app
- `requirements.txt`: dependencies
- `malaria_model.keras`: trained model weights
- `class_names.json`: class labels
- `accuracy_plot.png`: training curves from Colab
- `sample_images/`: example cell images for the demo
- `*.ipynb`: training notebook

## Run Locally
```
pip install -r requirements.txt
streamlit run app.py
```

Note: Educational project, not for medical diagnosis.
