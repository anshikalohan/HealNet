# HealNet - AI Health Assistant 🩺

HealNet is an advanced, multilingual AI Health Assistant powered by Large Language Models (LLMs) and computer vision. Designed to bridge the gap in healthcare accessibility, it provides evidence-based health information, medical image analysis, and nearby facility routing. 

Recently refactored into a scalable, enterprise-ready **FastAPI** backend, HealNet now leverages a **Retrieval-Augmented Generation (RAG)** pipeline to ensure all AI responses are grounded in trusted, official medical guidelines (e.g., WHO, CDC).

## 🌟 Key Features

*   **RAG-Powered Chatbot**: Utilizes LangChain, ChromaDB, and Groq (LLaMA 3) to provide accurate, factual medical information grounded in official guidelines.
*   **Medical Image Analysis**: Integrates custom TensorFlow models (EfficientNet/Xception) to classify skin lesions, brain MRIs, and lung X-Rays.
*   **Multilingual Support**: Automatically detects and responds in English or Hindi.
*   **WhatsApp Integration**: Fully compatible with Twilio WhatsApp webhooks for seamless messaging experiences.
*   **Emergency Mode**: Built-in emergency keyword detection routes users to critical national helplines immediately.
*   **Scalable Architecture**: Built on FastAPI with a modular, domain-driven directory structure.

## 🏗️ Architecture

```text
HealNet/
├── app/
│   ├── api/          # FastAPI routes/endpoints
│   ├── core/         # Pydantic settings and configuration
│   ├── services/     # Business logic (LLM, RAG, Image Analysis, DB)
│   └── utils/        # Helper functions and constants
├── data/             # Vector DB persistence and trusted medical guidelines
├── models/           # Pre-trained ML weights (H5/Keras)
├── requirements.txt  # Project dependencies
└── run.py            # Uvicorn entry point
```

## 🛠️ Tech Stack

*   **Framework:** FastAPI, Uvicorn
*   **AI/LLM:** LangChain, Groq API (LLaMA-3.1-8b-instant), HuggingFace Sentence Transformers
*   **Vector Database:** ChromaDB
*   **Machine Learning:** TensorFlow, Keras, NumPy, Pillow
*   **Integrations:** Twilio (WhatsApp API)
*   **Database:** SQLite (Caching & Logging)

## 🚀 Getting Started

### Prerequisites

*   Python 3.10+
*   Groq API Key
*   Twilio Account (for WhatsApp integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/HealNet.git
   cd HealNet
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   MODELS_PATH=/path/to/your/ml/models
   ```

5. **Initialize the Knowledge Base**
   On first run, the RAG service will automatically parse `data/trusted_medical_guidelines.md` and build the ChromaDB vector index in `./chroma_db`.

6. **Run the API**
   ```bash
   python run.py
   ```
   The server will start at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

## 🛡️ Disclaimer

HealNet provides educational health information and is **not** a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed healthcare professional.

---
*Built to make healthcare knowledge more accessible.*
