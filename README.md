# HealNet — Multilingual AI Healthcare Chatbot on WhatsApp

**HealNet** is an AI-powered, multilingual healthcare chatbot integrated with WhatsApp (via Twilio) that provides instant medical guidance using text, voice, images, and location-based interactions.

Designed especially for **rural and semi-urban communities**, HealNet aims to bridge the gap in healthcare access caused by low literacy, poor connectivity, and lack of nearby medical facilities.

---

## Problem Statement

Limited healthcare access and awareness in rural and semi-urban areas, combined with low literacy and weak internet connectivity, prevent timely medical assistance.

👉 HealNet addresses this by providing an **accessible, voice-enabled, multilingual healthcare assistant directly on WhatsApp**, eliminating the need for app downloads.

---

## Features

### Multimodal Interaction
- Text-based conversations
- Voice input & responses (local language support)
- Image-based medical analysis
- Location-based healthcare guidance

### Healthcare Support
- Instant AI-powered medical guidance
- Emergency assistance at a single tap
- Nearby hospitals and clinics
- Financial aid resources for medical expenses
- Medical insurance exploration

### Medical Imaging Module
- Chest X-ray analysis using Deep Learning
- Detects pathologies with confidence scores
- Normal probability estimation

### Accessibility First
- Multilingual support
- Voice interaction for low-literacy users
- Works on low internet bandwidth
- No app installation required

---

## Unique Value Propositions

- Works directly on WhatsApp  
- Voice-based local language interaction  
- AI-driven medical reasoning  
- Image-based diagnosis support  
- Location-aware healthcare guidance  
- Inclusive healthcare for underserved regions  

---

## Tech Stack

### Backend
- Flask
- SQLite
- Docker
- AWS

### AI & ML
- TensorFlow DenseNet (Medical Imaging)
- Groq API (LLM)
- IndicTrans (Multilingual Translation)
- DenseNet Model (for image module)

### Integrations
- Twilio (WhatsApp / SMS)
- OpenStreetMap (Location services)

### Datasets
- WHO Global Health Observatory  
- MoHFW India  
- CDC  
- ICMR  
- NIH Chest X-Ray Dataset  

---

## System Architecture

User → WhatsApp → Twilio → Flask Backend → AI Modules → Response

Modules include:
- Chat & Guidance Engine
- Voice Processing
- Translation Module
- Image Analysis Module
- Location Services

---

## Existing Systems & Research

Existing healthcare chatbots often suffer from:
- Text-only interaction
- Limited language support
- Platform restrictions

HealNet bridges these gaps with multimodal, multilingual, and WhatsApp-based accessibility.

---

## Objectives

- Promote health literacy and early diagnosis  
- Provide instant medical guidance  
- Enable inclusive healthcare access  
- Reduce dependency on physical consultations for basic guidance  

---

## Installation & Setup

```bash
git clone https://github.com/your-username/healnet.git
cd healnet
pip install -r requirements.txt
python app.py
