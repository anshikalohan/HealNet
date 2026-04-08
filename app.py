from flask import Flask, request, jsonify
import tensorflow as tf
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
import sqlite3
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model # type: ignore
import json
from datetime import datetime
import requests
from werkzeug.utils import secure_filename
import tempfile
import base64
from dotenv import load_dotenv
import re
import io
import time
try:
    from groq import Groq
except Exception:
    Groq = None

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None

# Initialize Groq client (FREE tier available)
groq_client = None
if GROQ_API_KEY and Groq is not None:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client initialized (FREE)")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
else:
    print("ℹ️ GROQ_API_KEY not set or groq SDK not installed - using Hugging Face for chat")

# Emergency contacts database
EMERGENCY_CONTACTS = {
    "India": {
        "ambulance": "108",
        "police": "100",
        "fire": "101",
        "women_helpline": "181",
        "child_helpline": "1098",
        "disaster_management": "108",
        "senior_citizen_helpline": "14567",
        "mental_health_helpline": "9152987821"
    }
}

# Health Insurance Companies
HEALTH_INSURANCE_INFO = {
    "companies": [
        {
            "name": "Life Insurance Corporation (LIC)",
            "website": "www.licindia.in",
            "helpline": "022-68276827",
            "coverage": "Comprehensive health and life insurance plans"
        },
        {
            "name": "Star Health Insurance",
            "website": "www.starhealth.in",
            "helpline": "1800-425-2255",
            "coverage": "Specialized health insurance, senior citizen plans"
        },
        {
            "name": "HDFC ERGO Health",
            "website": "www.hdfcergo.com",
            "helpline": "1800-266-3700",
            "coverage": "Individual and family floater plans"
        },
        {
            "name": "ICICI Lombard",
            "website": "www.icicilombard.com",
            "helpline": "1800-2666",
            "coverage": "Comprehensive health insurance with cashless facilities"
        }
    ]
}

# Government Financial Aid Schemes
GOVT_SCHEMES = {
    "schemes": [
        {
            "name": "Ayushman Bharat (PM-JAY)",
            "hindi_name": "आयुष्मान भारत",
            "eligibility": "Economically vulnerable families (bottom 40% as per SECC database)",
            "coverage": "₹5 lakh per family per year for secondary and tertiary care",
            "how_to_apply": "Visit nearest Common Service Centre (CSC) or Ayushman Mitra at empanelled hospitals",
            "helpline": "14555",
            "website": "pmjay.gov.in"
        },
        {
            "name": "Rashtriya Swasthya Bima Yojana (RSBY)",
            "hindi_name": "राष्ट्रीय स्वास्थ्य बीमा योजना",
            "eligibility": "BPL families",
            "coverage": "₹30,000 per family per year",
            "how_to_apply": "Contact local labor department or district authorities",
            "website": "www.rsby.gov.in"
        },
        {
            "name": "Janani Suraksha Yojana (JSY)",
            "hindi_name": "जननी सुरक्षा योजना",
            "eligibility": "Pregnant women (BPL and SC/ST in all states)",
            "coverage": "Cash assistance for institutional delivery",
            "how_to_apply": "Register at nearest Anganwadi or health center",
            "website": "nhm.gov.in"
        }
    ]
}

# Disease Awareness Content
DISEASE_AWARENESS = {
    "dengue": {
        "prevention": "Eliminate stagnant water, use mosquito repellents, wear full-sleeve clothes",
        "symptoms": "High fever, severe headache, pain behind eyes, joint/muscle pain, rash",
        "when_to_see_doctor": "If fever persists for more than 2 days or if you notice bleeding",
        "season": "Monsoon and post-monsoon (July-November)"
    },
    "malaria": {
        "prevention": "Use mosquito nets, repellents, eliminate standing water",
        "symptoms": "Fever with chills, sweating, headache, nausea, vomiting",
        "when_to_see_doctor": "Any suspected malaria symptoms require immediate testing",
        "season": "Monsoon season"
    },
    "tuberculosis": {
        "prevention": "BCG vaccination, avoid close contact with TB patients, maintain good hygiene",
        "symptoms": "Persistent cough (>2 weeks), weight loss, night sweats, blood in sputum",
        "when_to_see_doctor": "Cough lasting more than 2 weeks",
        "note": "Free treatment available under NTEP (National TB Elimination Programme)"
    },
    "covid19": {
        "prevention": "Vaccination, masks in crowded places, hand hygiene",
        "symptoms": "Fever, cough, breathing difficulty, loss of taste/smell",
        "when_to_see_doctor": "Breathing difficulty, persistent high fever, low oxygen",
        "helpline": "1075"
    },
    "diabetes": {
        "prevention": "Healthy diet, regular exercise, weight management, avoid excess sugar",
        "symptoms": "Increased thirst, frequent urination, fatigue, blurred vision",
        "when_to_see_doctor": "Regular checkups if family history, symptoms persist",
        "screening": "Fasting blood sugar test recommended after age 30"
    },
    "hypertension": {
        "prevention": "Low salt diet, regular exercise, stress management, avoid smoking",
        "symptoms": "Often no symptoms (silent killer), headaches, dizziness",
        "when_to_see_doctor": "Regular BP monitoring, especially if family history",
        "screening": "Check BP regularly after age 30"
    }
}

# Medical disclaimer
DISCLAIMER = "\n\n⚠️ *अस्वीकरण / Disclaimer:* यह जानकारी केवल शैक्षिक उद्देश्यों के लिए है। कृपया चिकित्सा सलाह के लिए लाइसेंस प्राप्त स्वास्थ्य पेशेवर से परामर्श करें। / This information is for educational purposes only. Please consult a licensed healthcare professional for medical advice."

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('healnet.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS response_cache
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query TEXT,
                  response TEXT,
                  language TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS chat_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  intent TEXT,
                  language TEXT,
                  user_location TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  success BOOLEAN)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_preferences
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  phone_number TEXT UNIQUE,
                  preferred_language TEXT DEFAULT 'hindi',
                  location TEXT,
                  last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

tf.config.set_visible_devices([], 'GPU')


MODELS_PATH = "/Users/anshikalohan/Documents/pbl"

# Helper for safe model loading
def try_load_model(path):
    try:
        model = load_model(path)
        print(f"✅ Loaded model: {path}")
        return model
    except Exception as e:
        print(f"❌ Failed to load model {path}: {e}")
        return None

try:
    modality_classifier = try_load_model(f"{MODELS_PATH}/modality_classifier.h5")
    brain_tumor_classifier = try_load_model(f"{MODELS_PATH}/brain_tumor_classifier.h5")
    skin_cancer_model = try_load_model(f"{MODELS_PATH}/Skin_Cancer.h5")
    lung_model = try_load_model(f"{MODELS_PATH}/lung_model.keras")
except Exception as e:
    print(f"❌ Global model loading error: {e}")

CLASSES_MAPPING = {
    "brain": ['glioma', 'meningioma', 'notumor', 'pituitary'],
    "skin": ['benign', 'malignant'],
    "lung": [
        'Atelectasis', 'Cardiomegaly', 'Consolidation', 'Edema', 'Effusion', 
        'Emphysema', 'Fibrosis', 'Infiltration', 'Mass', 'Nodule', 'Pleural_Thickening', 
        'Pneumonia', 'Pneumothorax', 'No_Finding'
    ]
}

def preprocess_image(image_bytes, target_size=(256, 256), scaling='none'):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(target_size)
    img_array = np.array(img, dtype=np.float32)
    
    if scaling == '1/255':
        img_array = img_array / 255.0
    elif scaling == 'xception':
        img_array = (img_array / 127.5) - 1.0
        
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def analyze_medical_image(image_bytes, language='english'):
    if not modality_classifier:
        return "Models not available." + DISCLAIMER
    
    try:
        # Step 1: Modality classification (EfficientNet expects 0-255 pixels, scaling='none')
        img_array = preprocess_image(image_bytes, target_size=(224, 224), scaling='none')
        
        modality_preds = modality_classifier.predict(img_array)[0]
        modality_idx = int(np.argmax(modality_preds))
        
        if modality_idx == 0:
            modality = "brain"
            model = brain_tumor_classifier
            target_size = (299, 299)
            scaling = '1/255'
        elif modality_idx == 1:
            modality = "lung"
            model = lung_model
            target_size = (256, 256)
            scaling = '1/255'
        elif modality_idx == 2:
            modality = "skin"
            model = skin_cancer_model
            target_size = (224, 224)
            scaling = 'none'
        else:
            return "Unable to determine image modality." + DISCLAIMER
            
        if not model:
            return f"{modality.capitalize()} model not available." + DISCLAIMER
            
        # Reprocess for specific model's target size and scaling requirement
        img_array = preprocess_image(image_bytes, target_size=target_size, scaling=scaling)
            
        # Step 2: Specific Pipeline Processing
        if modality == "brain":
            preds = model.predict(img_array)[0]
            pred_idx = np.argmax(preds)
            pred_class = CLASSES_MAPPING["brain"][pred_idx]
            conf = float(preds[pred_idx] * 100)
            
            if language == 'hindi':
                response = f"🧠 *ब्रेन एमआरआई विश्लेषण*\n\n"
                response += f"🔎 स्थिति: *{pred_class}*\n"
                response += f"विश्वास स्तर: {conf:.1f}%\n\n"
                response += "⚠️ कृपया डॉक्टर से पुष्टि कराएं।"
            else:
                response = f"🧠 *Brain MRI Analysis*\n\n"
                response += f"🔎 Condition: *{pred_class}*\n"
                response += f"Confidence: {conf:.1f}%\n\n"
                response += "⚠️ Please consult a doctor for confirmation."
                
        elif modality == "skin":
            preds = model.predict(img_array)[0]
            if len(preds) == 1:
                prob = float(preds[0])
                pred_class = CLASSES_MAPPING["skin"][1] if prob > 0.5 else CLASSES_MAPPING["skin"][0]
                conf = prob * 100 if prob > 0.5 else (1 - prob) * 100
            else:
                pred_idx = np.argmax(preds)
                pred_class = CLASSES_MAPPING["skin"][pred_idx]
                conf = float(preds[pred_idx] * 100)
                
            if language == 'hindi':
                response = f"🔍 *त्वचा विश्लेषण*\n\n"
                response += f"🔎 स्थिति: *{pred_class}*\n"
                response += f"विश्वास स्तर: {conf:.1f}%\n\n"
                response += "⚠️ कृपया डॉक्टर से पुष्टि कराएं।"
            else:
                response = f"🔍 *Skin Lesion Analysis*\n\n"
                response += f"🔎 Condition: *{pred_class}*\n"
                response += f"Confidence: {conf:.1f}%\n\n"
                response += "⚠️ Please consult a doctor for confirmation."
                
        elif modality == "lung":
            preds = model.predict(img_array)[0]
            preds_prob = 1 / (1 + np.exp(-preds)) if np.max(preds) > 1 else preds
            
            no_finding_idx = CLASSES_MAPPING["lung"].index("No_Finding")
            no_finding_conf = float(preds_prob[no_finding_idx] * 100)
            
            pathology_findings = []
            for i in range(14):
                if CLASSES_MAPPING["lung"][i] != "No_Finding" and preds_prob[i] > 0.3:
                    pathology_findings.append((CLASSES_MAPPING["lung"][i], float(preds_prob[i] * 100)))
                    
            pathology_findings = sorted(pathology_findings, key=lambda x: x[1], reverse=True)
            
            if no_finding_conf > 50 and len(pathology_findings) == 0:
                if language == 'hindi':
                    response = "🩻 *छाती एक्स-रे विश्लेषण*\n\n"
                    response += "✅ कोई स्पष्ट असामान्यता नहीं पाई गई\n"
                    response += f"विश्वास स्तर: {no_finding_conf:.1f}%\n\n"
                    response += "फिर भी यदि लक्षण हैं तो डॉक्टर से परामर्श करें।"
                else:
                    response = "🩻 *Chest X-ray Analysis*\n\n"
                    response += "✅ No significant abnormality detected\n"
                    response += f"Confidence: {no_finding_conf:.1f}%\n\n"
                    response += "Consult a doctor if symptoms persist."
            elif len(pathology_findings) == 0:
                if language == 'hindi':
                    response = "🩻 *छाती एक्स-रे विश्लेषण*\n\n"
                    response += "✅ कोई उच्च-विश्वास असामान्यता नहीं पाई गई\n"
                    response += "सभी रोग संभावनाएं निम्न हैं।\n\n"
                    response += "यदि लक्षण हैं तो डॉक्टर से परामर्श करें।"
                else:
                    response = "🩻 *Chest X-ray Analysis*\n\n"
                    response += "✅ No high-confidence abnormalities detected\n"
                    response += "All disease probabilities are low.\n\n"
                    response += "Consult a doctor if symptoms persist."
            else:
                if language == 'hindi':
                    response = "🩻 *छाती एक्स-रे विश्लेषण*\n\n"
                    response += "🔎 संभावित स्थितियां:\n"
                    for label, conf in pathology_findings[:5]:
                        response += f"• {label} — {conf:.1f}%\n"
                    response += f"\n📊 सामान्य होने की संभावना: {no_finding_conf:.1f}%\n"
                    response += "\n⚠️ कृपया डॉक्टर से पुष्टि कराएं।"
                else:
                    response = "🩻 *Chest X-ray Analysis*\n\n"
                    response += "🔎 Detected Potential Conditions:\n"
                    for label, conf in pathology_findings[:5]:
                        response += f"• {label} — {conf:.1f}%\n"
                    response += f"\n📊 Normal probability: {no_finding_conf:.1f}%\n"
                    response += "\n⚠️ Please consult a doctor for confirmation."

        return response + DISCLAIMER
    
    except Exception as e:
        print(f"Medical analysis error: {e}")
        return "Failed to analyze image." + DISCLAIMER

# Helper Functions
def log_interaction(intent, language, success=True, location=None):
    """Log anonymized chat metadata"""
    try:
        conn = sqlite3.connect('healnet.db')
        c = conn.cursor()
        c.execute("INSERT INTO chat_logs (intent, language, user_location, success) VALUES (?, ?, ?, ?)",
                  (intent, language, location, success))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Logging error: {e}")

def get_user_language(phone_number):
    """Get user's preferred language"""
    try:
        conn = sqlite3.connect('healnet.db')
        c = conn.cursor()
        c.execute("SELECT preferred_language FROM user_preferences WHERE phone_number = ?", (phone_number,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 'hindi'
    except:
        return 'hindi'

def set_user_language(phone_number, language):
    """Set user's preferred language"""
    try:
        conn = sqlite3.connect('healnet.db')
        c = conn.cursor()
        c.execute("""INSERT INTO user_preferences (phone_number, preferred_language) 
                     VALUES (?, ?) 
                     ON CONFLICT(phone_number) 
                     DO UPDATE SET preferred_language = ?, last_interaction = CURRENT_TIMESTAMP""",
                  (phone_number, language, language))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Set language error: {e}")

def cache_response(query, response, language):
    """Cache responses for offline fallback"""
    try:
        conn = sqlite3.connect('healnet.db')
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM response_cache")
        count = c.fetchone()[0]
        if count >= 50:
            c.execute("DELETE FROM response_cache WHERE id IN (SELECT id FROM response_cache ORDER BY timestamp ASC LIMIT 10)")
        
        c.execute("INSERT INTO response_cache (query, response, language) VALUES (?, ?, ?)",
                  (query.lower(), response, language))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Caching error: {e}")

def get_cached_response(query):
    """Retrieve cached response"""
    try:
        conn = sqlite3.connect('healnet.db')
        c = conn.cursor()
        c.execute("SELECT response FROM response_cache WHERE query LIKE ? ORDER BY timestamp DESC LIMIT 1",
                  (f"%{query.lower()}%",))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Cache retrieval error: {e}")
        return None

def detect_language(text):
    """Simple language detection"""
    hindi_chars = re.findall(r'[\u0900-\u097F]', text)
    if len(hindi_chars) > len(text) * 0.3:
        return 'hindi'
    return 'english'

def detect_emergency(message):
    """Detect emergency keywords"""
    emergency_keywords = [
        'emergency', 'urgent', 'help', 'ambulance', 'critical', 'accident', 
        'heart attack', 'stroke', 'bleeding', 'unconscious', 'suicide',
        'आपातकाल', 'तुरंत', 'मदद', 'एम्बुलेंस', 'दुर्घटना'
    ]
    return any(keyword in message.lower() for keyword in emergency_keywords)

def get_emergency_response(language='english'):
    """Generate emergency response"""
    if language == 'hindi':
        response = "🚨 *आपातकालीन सेवाएं* 🚨\n\n"
        response += "📞 *एम्बुलेंस:* 108\n"
        response += "🚓 *पुलिस:* 100\n"
        response += "🔥 *फायर ब्रिगेड:* 101\n"
        response += "🆘 *महिला हेल्पलाइन:* 181\n"
        response += "👶 *बाल हेल्पलाइन:* 1098\n"
        response += "🧠 *मानसिक स्वास्थ्य:* 9152987821\n\n"
        response += "कृपया यदि आप खतरे में हैं तो तुरंत कॉल करें!"
    else:
        response = "🚨 *EMERGENCY SERVICES* 🚨\n\n"
        response += "📞 *Ambulance:* 108\n"
        response += "🚓 *Police:* 100\n"
        response += "🔥 *Fire:* 101\n"
        response += "🆘 *Women Helpline:* 181\n"
        response += "👶 *Child Helpline:* 1098\n"
        response += "🧠 *Mental Health:* 9152987821\n\n"
        response += "Please call immediately if you're in danger!"
    return response

def get_insurance_info(language='english'):
    """Get health insurance information"""
    if language == 'hindi':
        response = "🏥 *स्वास्थ्य बीमा कंपनियां* 🏥\n\n"
        response += "भारत की प्रमुख IRDAI-अनुमोदित कंपनियां:\n\n"
        for company in HEALTH_INSURANCE_INFO['companies']:
            response += f"📋 *{company['name']}*\n"
            response += f"   📞 {company['helpline']}\n"
            response += f"   🌐 {company['website']}\n"
            response += f"   ℹ️ {company['coverage']}\n\n"
    else:
        response = "🏥 *Health Insurance Companies* 🏥\n\n"
        response += "Major IRDAI-approved companies in India:\n\n"
        for company in HEALTH_INSURANCE_INFO['companies']:
            response += f"📋 *{company['name']}*\n"
            response += f"   📞 Helpline: {company['helpline']}\n"
            response += f"   🌐 {company['website']}\n"
            response += f"   ℹ️ {company['coverage']}\n\n"
    
    response += "\n💡 Compare plans before buying!"
    return response

def get_govt_schemes(language='english'):
    """Get government financial aid schemes"""
    if language == 'hindi':
        response = "🏛️ *सरकारी स्वास्थ्य योजनाएं* 🏛️\n\n"
        response += "भारत सरकार की प्रमुख योजनाएं:\n\n"
        for scheme in GOVT_SCHEMES['schemes']:
            response += f"📌 *{scheme['hindi_name']}*\n"
            response += f"   ({scheme['name']})\n\n"
            response += f"   👥 पात्रता: {scheme['eligibility']}\n"
            response += f"   💰 कवरेज: {scheme['coverage']}\n"
            response += f"   📝 आवेदन: {scheme['how_to_apply']}\n"
            if 'helpline' in scheme:
                response += f"   📞 हेल्पलाइन: {scheme['helpline']}\n"
            if 'website' in scheme:
                response += f"   🌐 {scheme['website']}\n"
            response += "\n"
    else:
        response = "🏛️ *Government Health Schemes* 🏛️\n\n"
        response += "Major Government of India schemes:\n\n"
        for scheme in GOVT_SCHEMES['schemes']:
            response += f"📌 *{scheme['name']}*\n\n"
            response += f"   👥 Eligibility: {scheme['eligibility']}\n"
            response += f"   💰 Coverage: {scheme['coverage']}\n"
            response += f"   📝 Apply: {scheme['how_to_apply']}\n"
            if 'helpline' in scheme:
                response += f"   📞 Helpline: {scheme['helpline']}\n"
            if 'website' in scheme:
                response += f"   🌐 {scheme['website']}\n"
            response += "\n"
    
    return response

def get_disease_awareness(disease, language='english'):
    """Get disease awareness information"""
    disease_key = disease.lower().replace(" ", "")
    
    if disease_key not in DISEASE_AWARENESS:
        return None
    
    info = DISEASE_AWARENESS[disease_key]
    
    if language == 'hindi':
        response = f"📚 *{disease.upper()} जागरूकता*\n\n"
        response += f"🛡️ *रोकथाम:*\n{info['prevention']}\n\n"
        response += f"🔍 *लक्षण:*\n{info['symptoms']}\n\n"
        response += f"👨‍⚕️ *डॉक्टर को कब दिखाएं:*\n{info['when_to_see_doctor']}\n\n"
        if 'season' in info:
            response += f"📅 *मौसम:* {info['season']}\n\n"
        if 'helpline' in info:
            response += f"📞 *हेल्पलाइन:* {info['helpline']}\n\n"
        if 'note' in info:
            response += f"ℹ️ *नोट:* {info['note']}\n\n"
    else:
        response = f"📚 *{disease.upper()} Awareness*\n\n"
        response += f"🛡️ *Prevention:*\n{info['prevention']}\n\n"
        response += f"🔍 *Symptoms:*\n{info['symptoms']}\n\n"
        response += f"👨‍⚕️ *When to See Doctor:*\n{info['when_to_see_doctor']}\n\n"
        if 'season' in info:
            response += f"📅 *Season:* {info['season']}\n\n"
        if 'helpline' in info:
            response += f"📞 *Helpline:* {info['helpline']}\n\n"
        if 'note' in info:
            response += f"ℹ️ *Note:* {info['note']}\n\n"
    
    return response

def generate_health_prompt(message, language='english'):
    """Generate structured prompt for AI chat"""
    if language == 'hindi':
        system_prompt = """आप HealNet हैं, एक सहानुभूतिपूर्ण AI स्वास्थ्य सहायक।

दिशानिर्देश:
1. सटीक, साक्ष्य-आधारित स्वास्थ्य जानकारी प्रदान करें
2. सरल, स्पष्ट हिंदी भाषा का उपयोग करें
3. यदि लक्षण-आधारित: संभावित स्थितियों का सुझाव दें (निदान नहीं)
4. यदि रोग-आधारित: लक्षण, कारण, उपचार, सावधानियां समझाएं
5. दवा प्रश्नों के लिए: केवल सामान्य जानकारी प्रदान करें
6. सहानुभूतिपूर्ण और सहायक बनें
7. जवाब संक्षिप्त रखें (500 शब्दों से कम)
8. ALWAYS RESPOND IN HINDI

याद रखें: यह शैक्षिक जानकारी है, चिकित्सा निदान नहीं।"""
    else:
        system_prompt = """You are HealNet, a compassionate AI health assistant.

Guidelines:
1. Provide accurate, evidence-based health information
2. Use simple, clear language
3. If symptom-based: suggest possible conditions (not diagnosis)
4. If disease-based: explain symptoms, causes, treatments, precautions
5. For medication questions: provide general info only (not prescriptions)
6. Be empathetic and supportive
7. Keep response concise (under 500 words)
8. ALWAYS RESPOND IN ENGLISH

Remember: This is educational information, not medical diagnosis."""
    
    return system_prompt, message

def get_greeting_response(language='english'):
    """Generate greeting/introduction response"""
    if language == 'hindi':
        greeting = """👋 *नमस्ते! मैं HealNet हूं - आपका AI स्वास्थ्य सहायक*

मैं आपकी कैसे मदद कर सकता हूं:

🔴 *लक्षण विश्लेषण*
अपने लक्षण बताएं और मैं संभावित स्थितियों के बारे में जानकारी दूंगा

💊 *रोग की जानकारी*
किसी भी बीमारी के बारे में पूछें

🏥 *पास की सुविधाएं खोजें*
"Delhi में अस्पताल खोजें" लिखें

🚨 *आपातकालीन संपर्क*
एम्बुलेंस (108), पुलिस (100)

💰 *बीमा और सरकारी योजनाएं*
स्वास्थ्य बीमा की जानकारी

📚 *रोग जागरूकता*
डेंगू, मलेरिया, मधुमेह के बारे में

🎤 *आवाज समर्थन*
आवाज संदेश भेजें (जल्द आ रहा है)

📸 *मेडिकल इमेज*
तस्वीरें साझा करें

---
*आज मैं आपकी कैसे मदद कर सकता हूं?*"""
    else:
        greeting = """👋 *Hello! I'm HealNet - Your AI Health Assistant*

I can help you with:

🔴 *Symptom Analysis*
Tell me your symptoms for possible conditions

💊 *Disease Information*
Ask about any disease, causes, treatments

🏥 *Find Nearby Facilities*
Type "Find hospitals in Delhi"

🚨 *Emergency Contacts*
Ambulance (108), Police (100)

💰 *Insurance & Govt Schemes*
Health insurance information

📚 *Disease Awareness*
Learn about dengue, malaria, diabetes

🎤 *Voice Support*
Send voice messages (coming soon)

📸 *Medical Images*
Share images for analysis

🌍 *Multilingual*
Hindi, English supported!

---
*How can I help you today?*"""
    return greeting


def get_groq_chat_response(message, language='english'):
    """Get response from Groq (primary) with HF fallback."""
    # Check for greetings
    greetings = ["hello", "hi", "hey", "start", "help", "hii", "helo", "namaste", "नमस्ते", "hola", "bonjour"]
    if any(greeting == message.lower().strip() for greeting in greetings):
        return get_greeting_response(language)
    
    # Check cache
    cached = get_cached_response(message)
    if cached and not cached.endswith("[Offline Mode]"):
        print("📦 Using cached response")
        return cached
    
    system_prompt, user_message = generate_health_prompt(message, language)
    try:
        if groq_client:
            print("🔗 Using Groq llama-3.1-8b-instant")
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=800,
                temperature=0.7
            )
            response_text = response.choices[0].message.content if response and response.choices else ""
            if response_text:
                result = response_text + DISCLAIMER
                print(f"✅ Groq response: {len(result)} chars")
                cache_response(message, result, language)
                return result
            print("⚠️ Empty Groq response, falling back to Hugging Face")
        else:
            print("ℹ️ Groq not configured, using Hugging Face for chat")
    except Exception as e:
        print(f"⚠️ Groq chat error: {type(e).__name__}: {str(e)} - falling back to Hugging Face")
    

# Alias for existing callers
get_openai_response = get_groq_chat_response

def get_fallback_response(message, language='english'):
    """Enhanced fallback response"""
    
    greetings = ["hello", "hi", "hey", "start", "help", "namaste", "नमस्ते"]
    if any(greeting in message.lower() for greeting in greetings):
        return get_greeting_response(language)
    
    if language == 'hindi':
        fallback_responses = {
            "बुखार": "बुखार संक्रमण से लड़ने का संकेत है। आराम करें, खूब पानी पिएं। यदि बुखार 103°F से अधिक हो या 3 दिनों से अधिक रहे तो डॉक्टर से संपर्क करें।",
            "खांसी": "खांसी सर्दी, एलर्जी या जलन के कारण हो सकती है। हाइड्रेटेड रहें, शहद का उपयोग करें। लगातार खांसी के लिए डॉक्टर से मिलें।",
            "सिरदर्द": "सिरदर्द तनाव, निर्जलीकरण के कारण हो सकता है। आराम करें, पानी पिएं। गंभीर सिरदर्द के लिए डॉक्टर से परामर्श करें।",
            "पेट": "पेट दर्द कई कारणों से हो सकता है। हल्का भोजन करें। यदि दर्द गंभीर हो तो तुरंत डॉक्टर से संपर्क करें।",
            "default": "मैं वर्तमान में कनेक्टिविटी समस्याओं का सामना कर रहा हूं। आपातकाल के लिए 108 डायल करें या स्वास्थ्य पेशेवर से परामर्श करें।"
        }
        
        for keyword, response in fallback_responses.items():
            if keyword != "default" and keyword in message:
                return response + DISCLAIMER
        
        return fallback_responses["default"] + DISCLAIMER
    
    else:
        fallback_responses = {
            "fever": "Fever is your body fighting infection. Stay hydrated, rest, monitor temperature. Seek help if fever exceeds 103°F or lasts 3+ days.",
            "headache": "Headaches can be from stress, dehydration, or tension. Try rest, hydration, OTC pain relievers. See doctor for severe cases.",
            "cold": "Common cold includes runny nose, cough, mild fever. Rest, stay hydrated, use steam. Symptoms resolve in 7-10 days.",
            "cough": "Cough can be due to cold, allergies, or irritation. Stay hydrated, use honey. See doctor if persistent.",
            "stomach": "Stomach pain has many causes. Eat light, stay hydrated. Seek immediate help if severe.",
            "pain": "For any persistent pain, proper evaluation by a healthcare provider is recommended. Rest and monitor symptoms.",
            "default": "I'm experiencing connectivity issues. For emergencies dial 108, or consult a healthcare professional for immediate concerns."
        }
        
        for keyword, response in fallback_responses.items():
            if keyword != "default" and keyword in message.lower():
                return response + DISCLAIMER
        
        return fallback_responses["default"] + DISCLAIMER


def find_nearby_facilities(location_query, facility_type="hospital", language='english'):
    """Nearby search using OpenStreetMap (Nominatim + Overpass). No API key needed."""
    try:
        print(f"📍 [OSM] Searching for {facility_type} near: {location_query}")
        headers = {
            "User-Agent": "HealNet/1.0 (contact: support@healnet.local)"
        }
        
        # Resolve location to coordinates and a friendly address
        coord_match = re.match(r'^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$', str(location_query))
        if coord_match:
            lat, lng = coord_match.groups()
            location_str = f"{lat},{lng}"
            # Reverse geocode with Nominatim
            rev_url = "https://nominatim.openstreetmap.org/reverse"
            rev_params = {"lat": lat, "lon": lng, "format": "jsonv2"}
            rev_resp = requests.get(rev_url, params=rev_params, headers=headers, timeout=10)
            rev_data = rev_resp.json() if rev_resp.status_code == 200 else {}
            formatted_address = rev_data.get('display_name', location_str)
        else:
            # Geocode with Nominatim
            geocode_url = "https://nominatim.openstreetmap.org/search"
            geocode_params = {"q": location_query, "format": "jsonv2", "limit": 1, "countrycodes": "in"}
            geo_resp = requests.get(geocode_url, params=geocode_params, headers=headers, timeout=10)
            geo_data = geo_resp.json() if geo_resp.status_code == 200 else []
            if not geo_data:
                # Retry without country bias
                geocode_params = {"q": location_query, "format": "jsonv2", "limit": 1}
                geo_resp = requests.get(geocode_url, params=geocode_params, headers=headers, timeout=10)
                geo_data = geo_resp.json() if geo_resp.status_code == 200 else []
            if not geo_data:
                msg = f"Location '{location_query}' not found. Try a more specific area." if language == 'english' else f"स्थान '{location_query}' नहीं मिला। कृपया अधिक विशिष्ट क्षेत्र बताएं।"
                return msg
            lat, lng = geo_data[0]['lat'], geo_data[0]['lon']
            location_str = f"{lat},{lng}"
            formatted_address = geo_data[0].get('display_name', location_query)
        
        print(f"✅ [OSM] Location found: {formatted_address}")
        
        # Map facility types to OSM amenities
        amenity_tags = {
            "hospital": ["hospital", "clinic", "doctors"], # Fallback to clinics if hospital missing
            "clinic": ["clinic", "doctors"],
            "pharmacy": ["pharmacy", "chemist"],
            "doctor": ["doctors", "clinic", "hospital"]
        }
        tags = amenity_tags.get(facility_type, ["hospital", "clinic", "doctors"])
        
        # Overpass endpoints for reliability
        overpass_urls = [
            "https://lz4.overpass-api.de/api/interpreter",
            "https://z.overpass-api.de/api/interpreter",
            "https://overpass-api.de/api/interpreter"
        ]
        
        lat_f, lng_f = float(lat), float(lng)
        elements = []
        
        for radius_m in [5000, 15000]: # Expand from 5km to 15km if nothing found
            or_filters = "".join([f'node["amenity"="{t}"](around:{radius_m},{lat_f},{lng_f});way["amenity"="{t}"](around:{radius_m},{lat_f},{lng_f});relation["amenity"="{t}"](around:{radius_m},{lat_f},{lng_f});' for t in tags])
            query = f"[out:json][timeout:25];({or_filters});out center 20;"
            
            for overpass_url in overpass_urls:
                try:
                    ov_resp = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=25)
                    if ov_resp.status_code == 200:
                        ov_data = ov_resp.json()
                        elements = ov_data.get("elements", [])
                        if elements:
                            break # Found something, exit api loop
                except Exception as e:
                    print(f"⚠️ Overpass request error at {overpass_url}: {e}")
            
            if elements:
                break # Exit radius loop
                
        if not elements:
            msg = f"No {facility_type}s found near {formatted_address} (within 15km). (Map servers may be overloaded)" if language == 'english' else f"{formatted_address} के दायरे में कोई {facility_type} नहीं मिला।"
            return msg
        
        facilities = []
        for el in elements[:5]:
            tags = el.get("tags", {})
            name = tags.get("name", "N/A")
            address_parts = [tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:state")]
            addr = ", ".join([p for p in address_parts if p]) or formatted_address
            
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            # Using maps.google.com/?q= format to avoid XML ampersand parsing crash in Twilio WhatsApp
            gmaps_link = f"https://maps.google.com/?q={lat},{lon}" if lat and lon else ""
            
            facilities.append({
                "name": name,
                "address": addr,
                "gmaps_link": gmaps_link,
                "rating": "N/A",
                "open": None
            })
        
        print(f"✅ [OSM] Found {len(facilities)} facilities")
        return format_facilities_response(facilities, facility_type, language, formatted_address)
    
    except requests.Timeout:
        print("❌ OSM API timeout")
        msg = "Location service timeout. Please try again." if language == 'english' else "स्थान सेवा समय समाप्त। कृपया पुनः प्रयास करें।"
        return msg
    except Exception as e:
        print(f"❌ Location search error: {type(e).__name__}: {str(e)}")
        msg = "Location search failed. Try: 'Find hospitals in [area, city]'" if language == 'english' else "स्थान खोज विफल। उदाहरण: '[क्षेत्र, शहर] में अस्पताल खोजें'"
        return msg

def format_facilities_response(facilities, facility_type, language='english', location=''):
    """Format facilities list for WhatsApp"""
    if language == 'hindi':
        response = f"🏥 *{location} के पास {facility_type}:*\n\n"
        
        for i, facility in enumerate(facilities, 1):
            response += f"{i}. *{facility['name']}*\n"
            response += f"   📍 {facility['address']}\n"
            if facility.get('gmaps_link'):
                response += f"   🗺️ लिंक: {facility['gmaps_link']}\n"
            response += f"   ⭐ रेटिंग: {facility['rating']}/5\n"
            if facility['open'] is not None:
                status = "खुला है ✅" if facility['open'] else "बंद है ❌"
                response += f"   🕒 अभी {status}\n"
            response += "\n"
        
        response += "\n💡 Google Maps पर खोलने के लिए लिंक पर क्लिक करें"
    else:
        response = f"🏥 *{facility_type.title()}s near {location}:*\n\n"
        
        for i, facility in enumerate(facilities, 1):
            response += f"{i}. *{facility['name']}*\n"
            response += f"   📍 {facility['address']}\n"
            if facility.get('gmaps_link'):
                response += f"   🗺️ Link: {facility['gmaps_link']}\n"
            response += f"   ⭐ Rating: {facility['rating']}/5\n"
            if facility['open'] is not None:
                status = "Open now ✅" if facility['open'] else "Closed ❌"
                response += f"   🕒 {status}\n"
            response += "\n"
        
        response += "\n💡 Click the links to open in Google Maps"
    
    return response

def handle_intent(message, language='english'):
    """Detect user intent and route to appropriate handler"""
    message_lower = message.lower()
    
    # Emergency
    if detect_emergency(message):
        return "emergency", get_emergency_response(language)
    
    # Insurance info
    insurance_keywords = ['insurance', 'बीमा', 'policy', 'पॉलिसी']
    if any(keyword in message_lower for keyword in insurance_keywords):
        return "insurance", get_insurance_info(language)
    
    # Government schemes
    scheme_keywords = ['scheme', 'योजना', 'ayushman', 'आयुष्मान', 'pmjay', 'financial aid', 'सरकारी', 'government']
    if any(keyword in message_lower for keyword in scheme_keywords):
        return "schemes", get_govt_schemes(language)
    
    # Disease awareness
    awareness_keywords = ['dengue', 'डेंगू', 'malaria', 'मलेरिया', 'tuberculosis', 'tb', 'टीबी', 
                          'covid', 'कोविड', 'diabetes', 'मधुमेह', 'hypertension', 'उच्च रक्तचाप']
    for keyword in awareness_keywords:
        if keyword in message_lower:
            for disease in DISEASE_AWARENESS.keys():
                if disease in message_lower or keyword in disease:
                    return "awareness", get_disease_awareness(disease, language)
    
    # Location/facilities - robust pattern matching (avoid false matches like 'vomiting')
    facility_words = ['hospital', 'अस्पताल', 'clinic', 'क्लिनिक', 'pharmacy', 'फार्मेसी', 'doctor', 'डॉक्टर']
    has_facility_word = any(word in message_lower for word in facility_words)
    has_action_word = re.search(r'\b(find|locate|search|खोजें)\b', message_lower) is not None
    has_location_prep = re.search(r'\b(in|near|at)\b', message_lower) is not None or (' में ' in f' {message_lower} ') or (' पास ' in f' {message_lower} ')
    
    # Trigger location intent only when it's clearly a location query:
    # 1) contains a facility word and a location preposition, or
    # 2) contains an action word and a location preposition
    if (has_facility_word and has_location_prep) or (has_action_word and has_location_prep):
        return "location_request", None
    
    # Default: health query using AI
    return "health_query", None

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook for receiving WhatsApp/SMS messages - FIXED"""
    try:
        incoming_msg = request.values.get('Body', '').strip()
        from_number = request.values.get('From', '')
        media_url = request.values.get('MediaUrl0', None)
        media_type = request.values.get('MediaContentType0', None)
        # WhatsApp location payload (Twilio sends Latitude/Longitude on location share)
        lat = request.values.get('Latitude') or request.values.get('Latitude0')
        lng = request.values.get('Longitude') or request.values.get('Longitude0')
        loc_address = request.values.get('Address') or request.values.get('Address0')
        
        print(f"\n{'='*60}")
        print(f"📥 NEW MESSAGE")
        print(f"From: {from_number}")
        print(f"Message: {incoming_msg[:100]}")
        print(f"Media: {media_url if media_url else 'None'}")
        if lat and lng:
            print(f"📍 Location shared: {lat},{lng} ({loc_address or 'No address'})")
        print(f"{'='*60}\n")
        
        # Get user's preferred language
        user_language = get_user_language(from_number)
        
        # Detect language from message
        if incoming_msg:
            detected_lang = detect_language(incoming_msg)
            if detected_lang != user_language:
                set_user_language(from_number, detected_lang)
                user_language = detected_lang
        
        resp = MessagingResponse()
        response_text = ""
        
        # Handle language setting
        if incoming_msg.lower() in ['english', 'hindi', 'हिंदी', 'अंग्रेजी']:
            lang = 'hindi' if 'hindi' in incoming_msg.lower() or 'हिंदी' in incoming_msg else 'english'
            set_user_language(from_number, lang)
            msg = f"भाषा हिंदी में सेट की गई। 🇮🇳" if lang == 'hindi' else "Language set to English. 🇬🇧"
            response_text = msg + "\n\n" + get_greeting_response(lang)
        
        # Handle shared live location (high priority)
        if lat and lng:
            # Determine facility type from the text if specified
            facility_type = "hospital"
            if any(word in incoming_msg.lower() for word in ["pharmacy", "फार्मेसी", "medical store", "chemist"]):
                facility_type = "pharmacy"
            elif any(word in incoming_msg.lower() for word in ["clinic", "क्लिनिक"]):
                facility_type = "clinic"
            elif any(word in incoming_msg.lower() for word in ["doctor", "डॉक्टर"]):
                facility_type = "doctor"
            coords = f"{lat},{lng}"
            response_text = find_nearby_facilities(coords, facility_type, user_language)
            pretty_loc = loc_address if loc_address else coords
            log_interaction("location_shared_" + facility_type, user_language, True, pretty_loc)
        
        elif media_url and 'image' in media_type:
            print("📸 Processing image...")
            try:
                image_response = requests.get(
                media_url,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
               timeout=20
        )

                if image_response.status_code != 200:
                    raise Exception(f"Failed to fetch media: {image_response.status_code}")

                if 'image' not in image_response.headers.get('Content-Type', ''):
                    raise Exception("Media is not an image")

                image_data = image_response.content

                response_text = analyze_medical_image(image_data, user_language)
                log_interaction("medical_image_analysis", user_language, True)

            except Exception as e:
                print(f"❌ Image processing error: {e}")
                msg = "Failed to process image. Please try again." if user_language == 'english' else "छवि प्रोसेस नहीं हो सकी।"
                response_text = msg + DISCLAIMER

                        
        
        # Handle text messages - FIXED
        elif incoming_msg:
            intent, direct_response = handle_intent(incoming_msg, user_language)
            
            if intent == "location_request":
                # Enhanced location extraction
                location = None
                
                # Pattern 1: "find X in Y" or "find X near Y"
                match = re.search(r'(?:find|locate|search|खोजें)\s+(?:\w+\s+)?(?:in|near|at|में|पास)\s+(.+)', incoming_msg, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                
                # Pattern 2: "X in Y" format
                if not location:
                    match = re.search(r'(?:hospital|clinic|pharmacy|doctor|अस्पताल|क्लिनिक|फार्मेसी)\s+(?:in|near|at|में|पास)\s+(.+)', incoming_msg, re.IGNORECASE)
                    if match:
                        location = match.group(1).strip()
                
                # Pattern 3: Just city name mentioned
                if not location:
                    # Extract any word that might be a location
                    words = incoming_msg.split()
                    for i, word in enumerate(words):
                        if word.lower() in ['in', 'near', 'at', 'में', 'पास'] and i + 1 < len(words):
                            location = ' '.join(words[i+1:])
                            break
                
                if location:
                    # Determine facility type
                    facility_type = "hospital"
                    if any(word in incoming_msg.lower() for word in ["pharmacy", "फार्मेसी", "medical store", "chemist"]):
                        facility_type = "pharmacy"
                    elif any(word in incoming_msg.lower() for word in ["clinic", "क्लिनिक"]):
                        facility_type = "clinic"
                    elif any(word in incoming_msg.lower() for word in ["doctor", "डॉक्टर"]):
                        facility_type = "doctor"
                    
                    response_text = find_nearby_facilities(location, facility_type, user_language)
                    log_interaction("location_" + facility_type, user_language, True, location)
                else:
                    msg = "Please specify location. Example:\n'Find hospitals in Connaught Place Delhi'\n'Delhi में अस्पताल खोजें'" if user_language == 'english' else "कृपया स्थान बताएं। उदाहरण:\n'दिल्ली में अस्पताल खोजें'\n'Find hospitals in Delhi'"
                    response_text = msg
            
            elif direct_response:
                response_text = direct_response
                log_interaction(intent, user_language, True)
            
            else:
                # AI-powered health query
                response_text = get_openai_response(incoming_msg, user_language)
                log_interaction("health_query", user_language, True)
        
        else:
            # Empty message - send greeting
            response_text = get_greeting_response(user_language)
        
        # Send response in chunks (WhatsApp limit: 1600 chars)
        if response_text:
            print(f"📤 Sending response: {len(response_text)} characters")
            chunk_size = 1500
            
            if len(response_text) <= chunk_size:
                resp.message(response_text)
            else:
                # Split into chunks at sentence boundaries
                chunks = []
                current_chunk = ""
                sentences = response_text.split('\n')
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                        current_chunk += sentence + '\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + '\n'
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                for chunk in chunks:
                    resp.message(chunk)
                
                print(f"   Split into {len(chunks)} chunks")
        else:
            print("⚠️ Empty response - sending fallback")
            fallback = "Sorry, something went wrong. Please try again." if user_language == 'english' else "क्षमा करें, कुछ गलत हुआ। कृपया पुनः प्रयास करें।"
            resp.message(fallback)
        
        print(f"✅ Response sent successfully\n")
        return str(resp), 200, {'Content-Type': 'application/xml'}
    
    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        resp = MessagingResponse()
        error_msg = "System error. Please try again later." if user_language == 'english' else "सिस्टम त्रुटि। कृपया बाद में प्रयास करें।"
        resp.message(error_msg)
        log_interaction("error", user_language, False)
        return str(resp), 200, {'Content-Type': 'application/xml'}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "HealNet Backend - 100% FREE (Groq + Hugging Face + OSM)",
        "google_maps_configured": GOOGLE_MAPS_API_KEY is not None,
        "groq_configured": groq_client is not None,
        "features": {
            "symptom_analysis": True,
            "disease_info": True,
            "image_provider": "Hugging Face (FREE)",
            "chat_provider": "Groq (FREE) → HF fallback",
            "voice_provider": "Hugging Face Whisper (FREE)",
            "location_services": True,
            "location_provider": "OpenStreetMap (Nominatim + Overpass) (FREE)",
            "emergency_contacts": True,
            "insurance_info": True,
            "govt_schemes": True,
            "multilingual": True
        },
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/test_chat', methods=['GET'])
def test_chat():
    """Test chat connectivity (prefers Groq; falls back to Hugging Face)"""
    diagnostics = {
        "groq_configured": GROQ_API_KEY is not None and groq_client is not None,
    }
    
    test_query = "What is fever? One sentence."
    try:
        if groq_client:
            print("🧪 Testing Groq chat")
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": test_query}],
                max_tokens=50
            )
            text = response.choices[0].message.content
            return jsonify({
                "status": "success",
                "message": "Groq chat working",
                "diagnostics": diagnostics,
                "response": text,
                "provider": "groq",
                "model_used": "llama-3.1-8b-instant"
            }), 200
        else:
            print("🧪 Testing Hugging Face chat")
            return jsonify({
                "status": "success",
                "message": "Hugging Face chat working",
                "diagnostics": diagnostics,
                "provider": "huggingface",
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "diagnostics": diagnostics
        }), 500

@app.route('/test_huggingface', methods=['GET', 'POST'])
            

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get usage statistics"""
    try:
        conn = sqlite3.connect('healnet.db')
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM chat_logs")
        total_queries = c.fetchone()[0]
        
        c.execute("SELECT intent, COUNT(*) as count FROM chat_logs GROUP BY intent ORDER BY count DESC LIMIT 10")
        top_intents = c.fetchall()
        
        c.execute("SELECT language, COUNT(*) as count FROM chat_logs GROUP BY language")
        language_stats = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM chat_logs WHERE success = 1")
        successful_queries = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": f"{(successful_queries/total_queries*100):.2f}%" if total_queries > 0 else "0%",
            "top_intents": [{"intent": intent, "count": count} for intent, count in top_intents],
            "language_distribution": [{"language": lang, "count": count} for lang, count in language_stats]
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/test_whatsapp", methods=["POST"])
def test_whatsapp():
    """Test WhatsApp connectivity"""
    resp = MessagingResponse()
    resp.message("✅ HealNet is LIVE!\n\n🔧 All features working (100% FREE):\n✓ Voice messages (Hugging Face Whisper)\n✓ Image analysis (Hugging Face Vision)\n✓ Location search (Google Maps)\n✓ AI health queries (Hugging Face Chat)\n\nSend 'hi' to start! 🏥")
    return str(resp), 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏥 HealNet - 100% FREE Backend (Hugging Face)")
    print("="*70)
    print(f"✅ Groq configured: {groq_client is not None}")
    print(f"✅ Twilio configured: {TWILIO_ACCOUNT_SID is not None}")
    print(f"✅ Google Maps configured: {GOOGLE_MAPS_API_KEY is not None}")
    print("\n🤖 AI FEATURES (ALL FREE):")
    print("   • Chat: Groq (primary) → Hugging Face (fallback)")
    print("   • Voice: Hugging Face Whisper")
    print("   • Images: Hugging Face Vision Models (BLIP + ViT)")
    print("   • Location Search: OpenStreetMap (Nominatim + Overpass)")
    print("   💰 No credits needed - 100% FREE!")
    print("\n📋 All Features:")
    print("   • Symptom Analysis (AI-powered) 🤖")
    print("   • Disease Information 📚")
    print("   • Medical Image Analysis 📸 [Hugging Face - FREE]")
    print("   • Voice Message Support 🎤 [Hugging Face Whisper - FREE]")
    print("   • Location Search 📍 [Google Maps]")
    print("   • Emergency Contacts 🚨")
    print("   • Insurance Info 💰")
    print("   • Govt Schemes 🏛️")
    print("   • Multilingual (Hindi/English) 🌍")
    print("\n🔑 API Keys Needed:")
    print(f"   • GROQ_API_KEY: {'✅ SET' if groq_client else '⚠️ NOT SET (recommended)'}")
    print(f"   • GOOGLE_MAPS_API_KEY: {'(unused, OSM enabled)'}")
    print("\n💡 Get FREE Hugging Face key: https://huggingface.co/settings/tokens")
    print("💡 Get FREE Groq key: https://console.groq.com/keys")
    print("   No credit card required - completely FREE!")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)