# Cognitive Load Detector

An AI-assisted web application designed to analyze student cognitive load during online assessments using behavioral tracking, webcam-based face detection, and performance analytics.

The system monitors user interaction patterns such as focus changes, idle time, mouse activity, response switching behavior, and quiz performance to estimate cognitive load levels in real time.

---

# 🚀 Features

* 🔐 User Authentication System
* 🧠 Cognitive Load Estimation
* 📷 Webcam-Based Face Monitoring
* 📊 Interactive Dashboard & Analytics
* 📝 Online Quiz / Assessment Module
* 🎯 Real-Time Behavioral Tracking
* ♿ Dyslexia-Friendly Accessibility Support
* 🔊 Voice Assistance using Speech Synthesis
* 📈 Performance Visualization with Charts
* 🎨 Responsive Modern UI

---

# 🛠️ Tech Stack

## Backend

* Python
* Django
* SQLite3 Database

---

## Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap 5
* Django Templates

---

## AI / Computer Vision

* MediaPipe Face Detection (Pre-trained Model)
* Browser FaceDetector API (Fallback Detection)

---

## Browser & Camera APIs

* `navigator.mediaDevices.getUserMedia()` for webcam access
* JavaScript Video Element for live preview
* Page Focus / Blur Detection
* Mouse Movement Tracking
* Idle Time Monitoring
* Option Switch Tracking

---

## Dashboard & Visualization

* Chart.js for analytics and graphs

---

## Authentication

* Django Built-in Authentication System
* Django User Model
* Login, Logout & Registration Views

---

## Accessibility & Learning Support

* OpenDyslexic Font Integration
* Browser Speech Synthesis API
* Dyslexia Font Toggle using `localStorage`

---

## Version Control

* Git
* GitHub

---

# 🧠 Cognitive Load Estimation Method

The project currently uses:

## ✅ Pre-trained AI Model

The application uses **MediaPipe Face Detection**, a pre-trained computer vision model developed by Google, to detect face visibility during assessments.

## ✅ Rule-Based Cognitive Load Scoring

Instead of training a custom machine learning model, the system estimates cognitive load using behavioral and performance metrics such as:

* Quiz Accuracy
* Time Taken
* Attention Score
* Idle Time
* Mouse Movement Patterns
* Window Focus Changes
* Face Missing Events
* Option Switching Frequency

These signals are combined using a rule-based scoring algorithm to classify cognitive load levels.

---

# 🤖 Future AI Enhancements

Future versions may include:

* Machine Learning-based Cognitive Load Prediction
* Custom AI Model Training
* Real-time Emotion Detection
* Eye Tracking Integration
* Deep Learning Analytics
* Personalized Learning Recommendations

## Proposed ML Stack

* scikit-learn
* Random Forest / Logistic Regression
* Dataset-driven Cognitive Load Classification
* Model Serialization using `.pkl`

---

# 📁 Project Structure

```bash
Cognitive-Load-Detector/
│
├── accounts/
├── cognitive_load_project/
├── static/
├── templates/
├── testapp/
├── users/
├── media/
├── manage.py
├── db.sqlite3
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation & Setup

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Manushree-S/Cognitive-Load-Detector.git
```

---

## 2️⃣ Navigate to the Project Directory

```bash
cd Cognitive-Load-Detector
```

---

## 3️⃣ Create Virtual Environment

```bash
python -m venv venv
```

---

## 4️⃣ Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

## 5️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 6️⃣ Run Database Migrations

```bash
python manage.py migrate
```

---

## 7️⃣ Start Development Server

```bash
python manage.py runserver
```

---

# 🌐 Run the Application

Open your browser and visit:

```bash
http://127.0.0.1:8000/
```

---

# 📸 Screenshots

Add screenshots for:

* Home Page
* Login & Registration
* Assessment Interface
* Dashboard
* Cognitive Load Analytics
* Webcam Monitoring

---

# 🎯 Future Improvements

* Cloud Deployment
* Real-time AI Analytics
* Adaptive Difficulty System
* Student Performance Reports
* Teacher/Admin Dashboard
* Multi-user Monitoring
* AI Recommendation Engine

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---

# 📜 License

This project is developed for educational and research purposes.

---

# 👨‍💻 Author

**Manushree S**
CSE Student | AI & Full Stack Development Enthusiast

GitHub: https://github.com/Manushree-S/Cognitive-Load-Detector.git
