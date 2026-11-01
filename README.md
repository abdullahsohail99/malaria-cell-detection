# Malaria Cell Detection using Deep Learning

Binary image classification of blood cell images: **Parasitized** vs **Uninfected**, using MobileNetV2 transfer learning, deployed as a one-page Streamlit web app with optional user accounts and an admin dashboard.

## Project Links
- **Live app:** https://malaria-cell-detection-by-abdullah-sohail222.streamlit.app/
- **GitHub repository:** https://github.com/abdullahsohail99/malaria-cell-detection
- **Presentation:** https://docs.google.com/presentation/d/13W-JN3cPg9BupnFXJsGnwF9_dQk4NzO8/edit?usp=sharing
- **Project report:** https://docs.google.com/document/d/1yrGkvC2RCtqNjGZklubsDeO_BMYsIKqA/edit?usp=sharing
- **YouTube video:** (add link)
- **LinkedIn post:** (add link)

## Features
- **Public demo:** upload a blood cell image (or pick a sample) and get a prediction with a confidence score. No login needed.
- **User accounts:** sign up / sign in, personal dashboard with prediction history, CSV export, profile, password change, account deletion.
- **Admin dashboard:** usage overview and charts, user management (roles, suspend, reset password, delete), prediction log, model info and health check, site settings (sign-ups, maintenance mode, announcement banner, confidence threshold), audit log, system info, database backup and restore.
- **Security:** PBKDF2-SHA256 hashed passwords with per-user salt, lockout after 5 failed logins, server-side role checks, admin credentials kept in Streamlit secrets.

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
- `app.py`: entry point and page router
- `home.py`: public one-page site and live demo
- `auth_ui.py`: sign in, sign up, user dashboard, top bar
- `admin_ui.py`: admin dashboard
- `db.py`: SQLite data layer (users, predictions, settings, audit log)
- `ui.py`: shared styling and helpers
- `.streamlit/config.toml`: light theme
- `.streamlit/secrets.toml.example`: template for the admin credentials (the real `secrets.toml` is never committed)
- `requirements.txt`, `malaria_model.keras`, `class_names.json`, `accuracy_plot.png`, `sample_images/`, `*.ipynb`

## Admin setup
1. In Streamlit Cloud open **Manage app, Settings, Secrets** and paste:
   ```toml
   ADMIN_USERNAME = "your-admin-name"
   ADMIN_PASSWORD = "a-long-strong-password"
   ```
2. Reboot the app, then sign in with those credentials. An **Admin** button appears in the top bar.
3. Without secrets, a built-in demo admin is created and the dashboard shows a red warning until you change it.

Data is stored in a local SQLite file (`data/app.db`, not committed). Streamlit Cloud can erase local files when the app restarts, so use **Admin, System, Download database backup** regularly.

## Run Locally
```
pip install -r requirements.txt
streamlit run app.py
```

Note: Educational project, not for medical diagnosis.
