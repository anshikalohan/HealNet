"""
Utility functions and health data for HealNet
"""

HEALTH_FAQ = {
    "fever": {
        "en": "Fever is usually a sign your body is fighting an infection. Rest, drink plenty of fluids, and monitor your temperature. Seek medical help if fever exceeds 103°F (39.4°C) or lasts more than 3 days.",
        "hi": "बुखार आमतौर पर संक्रमण से लड़ने का संकेत है। आराम करें, तरल पदार्थ पिएं और तापमान की निगरानी करें। यदि बुखार 103°F से अधिक हो या 3 दिन से अधिक रहे तो डॉक्टर से संपर्क करें।"
    },
    "headache": {
        "en": "Headaches can be caused by stress, dehydration, lack of sleep, or tension. Try rest, hydration, and over-the-counter pain relievers. Consult a doctor for severe, frequent, or persistent headaches.",
        "hi": "सिरदर्द तनाव, निर्जलीकरण, नींद की कमी से हो सकता है। आराम, पानी और दर्द निवारक दवाएं लें। गंभीर या लगातार सिरदर्द के लिए डॉक्टर से परामर्श करें।"
    },
    "cough": {
        "en": "Cough can be due to cold, allergies, or respiratory irritation. Stay hydrated, use honey (for adults), avoid irritants. See a doctor if persistent, producing blood, or accompanied by chest pain.",
        "hi": "खांसी सर्दी, एलर्जी या श्वसन जलन के कारण हो सकती है। पानी पिएं, शहद का उपयोग करें। यदि खांसी लगातार हो, खून आए या सीने में दर्द हो तो डॉक्टर से मिलें।"
    },
    "cold": {
        "en": "Common cold symptoms include runny nose, congestion, sore throat, and mild fever. Rest, stay hydrated, use steam inhalation. Symptoms typically resolve in 7-10 days.",
        "hi": "सामान्य सर्दी के लक्षणों में नाक बहना, गले में खराश शामिल हैं। आराम करें, पानी पिएं, भाप लें। लक्षण आमतौर पर 7-10 दिनों में ठीक हो जाते हैं।"
    },
    "stomach_pain": {
        "en": "Stomach pain can have many causes: indigestion, gas, constipation, or food intolerance. Try rest, light diet, and avoid spicy foods. Seek immediate help for severe pain, vomiting blood, or high fever.",
        "hi": "पेट दर्द के कई कारण हो सकते हैं: अपच, गैस, कब्ज। हल्का भोजन करें, मसालेदार खाना न खाएं। गंभीर दर्द, खून की उल्टी या तेज बुखार के लिए तुरंत डॉक्टर से संपर्क करें।"
    },
    "diarrhea": {
        "en": "Diarrhea is often caused by viral infections, food poisoning, or dietary changes. Stay hydrated with ORS, eat bland foods. See a doctor if it lasts more than 2 days, blood in stool, or severe dehydration.",
        "hi": "दस्त अक्सर वायरल संक्रमण या खाद्य विषाक्तता के कारण होता है। ORS से हाइड्रेटेड रहें, सादा भोजन खाएं। यदि 2 दिन से अधिक रहे या मल में खून हो तो डॉक्टर से मिलें।"
    },
    "diabetes": {
        "en": "Diabetes is a condition where blood sugar levels are too high. Symptoms include frequent urination, excessive thirst, fatigue. Management includes diet, exercise, and medication. Regular monitoring is essential.",
        "hi": "डायबिटीज में रक्त शर्करा का स्तर बहुत अधिक होता है। लक्षणों में बार-बार पेशाब, अत्यधिक प्यास शामिल हैं। प्रबंधन में आहार, व्यायाम और दवा शामिल है।"
    },
    "hypertension": {
        "en": "High blood pressure (hypertension) often has no symptoms but increases risk of heart disease and stroke. Management includes low-salt diet, regular exercise, stress management, and medication if prescribed.",
        "hi": "उच्च रक्तचाप में अक्सर कोई लक्षण नहीं होते लेकिन हृदय रोग का खतरा बढ़ता है। प्रबंधन में कम नमक का आहार, नियमित व्यायाम और दवा शामिल है।"
    }
}

LANGUAGE_PATTERNS = {
    "hi": ["है", "में", "को", "का", "की", "से", "मैं", "दर्द", "बुखार"],
    "es": ["el", "la", "de", "en", "es", "dolor", "fiebre", "médico"],
    "fr": ["le", "la", "de", "je", "est", "douleur", "fièvre", "médecin"],
    "bn": ["আমি", "এটা", "হয়", "আছে", "ব্যথা", "জ্বর"],
    "te": ["నాకు", "ఉంది", "నొప్పి", "జ్వరం"],
    "ta": ["எனக்கு", "உள்ளது", "வலி", "காய்ச்சல்"],
}

def detect_language(text):
    """
    Simple language detection based on common words
    Returns ISO 639-1 language code
    """
    text_lower = text.lower()
    
    for lang_code, patterns in LANGUAGE_PATTERNS.items():
        if any(pattern in text_lower for pattern in patterns):
            return lang_code
    
    return "en"  

def get_language_name(code):
    """Get full language name from code"""
    languages = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "bn": "Bengali",
        "te": "Telugu",
        "ta": "Tamil",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada"
    }
    return languages.get(code, "English")

def extract_symptoms(message):
    """
    Extract potential symptoms from user message
    """
    symptom_keywords = {
        "fever": ["fever", "temperature", "hot", "बुखार", "fiebre"],
        "headache": ["headache", "head pain", "सिरदर्द", "dolor de cabeza"],
        "cough": ["cough", "coughing", "खांसी", "tos"],
        "cold": ["cold", "runny nose", "congestion", "सर्दी", "resfriado"],
        "pain": ["pain", "ache", "दर्द", "dolor"],
        "nausea": ["nausea", "vomit", "throw up", "मतली", "náusea"],
        "fatigue": ["tired", "fatigue", "weakness", "थकान", "fatiga"],
        "dizziness": ["dizzy", "vertigo", "चक्कर", "mareo"]
    }
    
    detected_symptoms = []
    message_lower = message.lower()
    
    for symptom, keywords in symptom_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_symptoms.append(symptom)
    
    return detected_symptoms

def get_intent(message):
    """
    Classify user intent from message
    """
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["emergency", "urgent", "help", "ambulance", "critical", "आपातकाल", "मदद"]):
        return "emergency"
    
    if any(word in message_lower for word in ["hospital", "clinic", "doctor", "pharmacy", "near", "अस्पताल", "डॉक्टर"]):
        return "find_facility"
    
    symptoms = extract_symptoms(message)
    if symptoms:
        return "symptom_check"
    
    disease_keywords = ["diabetes", "hypertension", "asthma", "cancer", "disease", "condition", "मधुमेह", "बीमारी"]
    if any(keyword in message_lower for keyword in disease_keywords):
        return "disease_info"
    
    if any(word in message_lower for word in ["medicine", "medication", "drug", "tablet", "pill", "दवा", "दवाई"]):
        return "medication_info"
    
    return "general_health"

def format_response_for_whatsapp(text):
    """
    Format text for better WhatsApp readability
    """
    text = text.replace("Symptoms:", "🔴 *Symptoms:*")
    text = text.replace("Causes:", "🔍 *Causes:*")
    text = text.replace("Treatment:", "💊 *Treatment:*")
    text = text.replace("Precautions:", "⚠️ *Precautions:*")
    text = text.replace("When to see a doctor:", "👨‍⚕️ *When to see a doctor:*")
    
    return text

def validate_phone_number(number):
    """
    Validate phone number format
    """
    import re
    number = number.replace("whatsapp:", "")
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, number))

def sanitize_input(text):
    """
    Sanitize user input to prevent injection attacks
    """
    import html
    text = html.escape(text)
    max_length = 1000
    if len(text) > max_length:
        text = text[:max_length]
    return text.strip()

MEDICAL_SPECIALTIES = {
    "cardiology": ["heart", "cardiac", "chest pain", "palpitation", "हृदय"],
    "dermatology": ["skin", "rash", "acne", "eczema", "त्वचा"],
    "orthopedics": ["bone", "joint", "fracture", "arthritis", "हड्डी"],
    "neurology": ["brain", "nerve", "seizure", "migraine", "मस्तिष्क"],
    "pediatrics": ["child", "baby", "infant", "kid", "बच्चा"],
    "gynecology": ["women", "pregnancy", "menstrual", "महिला"],
    "psychiatry": ["mental", "depression", "anxiety", "stress", "मानसिक"],
    "gastroenterology": ["stomach", "digestive", "intestine", "पेट"]
}

def suggest_specialty(message):
    """
    Suggest medical specialty based on symptoms
    """
    message_lower = message.lower()
    
    for specialty, keywords in MEDICAL_SPECIALTIES.items():
        if any(keyword in message_lower for keyword in keywords):
            return specialty.title()
    
    return "General Medicine"