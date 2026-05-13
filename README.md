# 🧠 HWellbeing – AI Healthcare Assistant

An intelligent, full-stack healthcare system that provides **AI-powered symptom analysis, disease prediction, voice interaction, and skin disease detection**.

Built as a **production-level final year project**, combining **Machine Learning, NLP, Computer Vision, and Real-Time Systems**.

---

## 🚀 Features

### 🩺 AI Triage System

* Symptom-based disease prediction
* Clinical rule engine + ML hybrid approach
* Confidence scoring & risk analysis

### 🎙️ Voice Assistant

* Real-time voice interaction
* Speech-to-Text (STT) + Text-to-Speech (TTS)
* Conversational AI engine

### 🧴 Skin Disease Detection

* CNN-based image classification
* Upload or capture skin images
* Fast and accurate predictions

### 📊 Risk Prediction (ML Models)

* Lung disease risk prediction
* NLP-based triage classification
* Pre-trained ML pipelines

### 🧑‍⚕️ Doctor Recommendation (Planned / Extendable)

* Location-based doctor suggestions
* Integration-ready module

---

## 🛠 Tech Stack

### Frontend

* React (Vite)
* Tailwind CSS
* Framer Motion

### Backend

* FastAPI
* Python

### AI / ML

* Scikit-learn
* TensorFlow / CNN
* NLP Pipelines

### Database & Infra

* SAP HANA Cloud
* Redis (Caching)
* Docker

---

## 📂 Project Structure

```
HWellbeing/
│
├── frontend/               # React Frontend
├── src/
│   ├── conversational_module/
│   ├── decision/
│   ├── ml_engine/
│   ├── predictions_api/
│   ├── db/
│   └── core/
│
├── data/                   # Datasets
├── static/                 # Generated audio files
├── temp_images/            # Temporary images
├── temp_audio/             # Temporary audio
│
├── requirements.txt
├── Dockerfile
└── main.py
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/RajshekharDK/Health_care_wellbeing.git
cd Hwellbeing
```

---

### 2️⃣ Backend Setup

```bash
pip install -r requirements.txt
```

Create `.env` file:

```bash
cp .env.example .env
```

Run backend:

```bash
uvicorn main:app --reload
```

---

### 3️⃣ Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 📌 Key Highlights

* Hybrid AI system (ML + Rule-based decision engine)
* Real-time voice interaction
* CNN-based image classification
* Modular and scalable backend architecture
* Industry-level folder structure

---

## 🚀 Future Enhancements

* Live deployment (AWS / Render)
* Mobile application
* Advanced medical dataset integration
* Doctor booking system
* Real-time monitoring dashboard

---

## 👨‍💻 Author

**Rajshekhar**

* LinkedIn:  https://www.linkedin.com/in/rajshekhar-dk-239191401

* GitHub: https://github.com/RajshekharDK

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!

---
