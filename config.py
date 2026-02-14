"""
Configuration management for HealNet
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'healnet-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'wav', 'mp3', 'ogg'}
    
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'healnet.db')
    CACHE_SIZE = int(os.getenv('CACHE_SIZE', '10'))
    
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '20'))
    
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')
    SUPPORTED_LANGUAGES = ['en', 'hi', 'es', 'fr', 'bn', 'te', 'ta', 'mr', 'gu', 'kn']
    
    EMERGENCY_CONTACTS = {
        'IN': {
            'ambulance': '108',
            'police': '100',
            'fire': '101',
            'women_helpline': '181',
            'child_helpline': '1098',
            'disaster_management': '108',
            'national_helpline': '104'
        },
        'US': {
            'emergency': '911',
            'poison_control': '1-800-222-1222',
            'suicide_prevention': '988'
        },
        'UK': {
            'emergency': '999',
            'nhs': '111'
        }
    }
    
    MEDICAL_DISCLAIMER = "\n\n⚠️ *Disclaimer:* This information is for educational purposes only. Always consult a licensed healthcare professional for medical advice, diagnosis, or treatment."
    
    RESPONSE_TEMPLATES = {
        'greeting': "Hello! I'm HealNet, your AI health assistant. 👋\n\nI can help you with:\n• Symptom analysis\n• Disease information\n• Health guidance\n• Find nearby hospitals\n• Emergency contacts\n\nHow can I assist you today?",
        
        'error': "I apologize, but I'm experiencing technical difficulties. Please try again in a moment or contact emergency services if urgent.",
        
        'offline': "I'm currently in offline mode. I'll provide information from my cache. For urgent medical needs, please contact emergency services.",
        
        'image_received': "📷 Image received! Analyzing... Please note: This is not a medical diagnosis. For accurate evaluation, consult a healthcare professional.",
        
        'voice_received': "🎤 Voice message received! Processing...",
        
        'location_request': "To find nearby facilities, please:\n1. Share your location (attachment icon → Location)\nOR\n2. Type your area/city name\n\nExample: 'Find hospitals in Delhi'"
    }
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'healnet.log')
    
    ENABLE_VOICE = os.getenv('ENABLE_VOICE', 'True').lower() == 'true'
    ENABLE_IMAGE_ANALYSIS = os.getenv('ENABLE_IMAGE_ANALYSIS', 'True').lower() == 'true'
    ENABLE_LOCATION_SERVICES = os.getenv('ENABLE_LOCATION_SERVICES', 'True').lower() == 'true'
    ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'True').lower() == 'true'
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        required = [
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'GEMINI_API_KEY'
        ]
        
        missing = []
        for key in required:
            if not os.getenv(key):
                missing.append(key)
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DATABASE_PATH = 'test_healnet.db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])