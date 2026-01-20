import re

def get_greeting_response(language='english'):
    if language == 'hindi':
        return """👋 *नमस्ते! मैं HealNet हूं - आपका AI स्वास्थ्य सहायक*

मैं आपकी कैसे मदद कर सकता हूं:
🔴 *लक्षण विश्लेषण*
💊 *रोग की जानकारी*
🏥 *पास की सुविधाएं खोजें*
🚨 *आपातकालीन संपर्क*
💰 *बीमा और सरकारी योजनाएं*
📸 *मेडिकल इमेज*

*आज मैं आपकी कैसे मदद कर सकता हूं?*"""
    else:
        return """👋 *Hello! I'm HealNet - Your AI Health Assistant*

I can help you with:
🔴 *Symptom Analysis*
💊 *Disease Information*
🏥 *Find Nearby Facilities*
🚨 *Emergency Contacts*
💰 *Insurance & Govt Schemes*
📸 *Medical Images*

*How can I help you today?*"""

def detect_language(text):
    hindi_chars = re.findall(r'[\u0900-\u097F]', text)
    if len(hindi_chars) > len(text) * 0.3:
        return 'hindi'
    return 'english'

def detect_emergency(message):
    emergency_keywords = [
        'emergency', 'urgent', 'help', 'ambulance', 'critical', 'accident', 
        'heart attack', 'stroke', 'bleeding', 'unconscious', 'suicide',
        'आपातकाल', 'तुरंत', 'मदद', 'एम्बुलेंस', 'दुर्घटना'
    ]
    return any(keyword in message.lower() for keyword in emergency_keywords)
