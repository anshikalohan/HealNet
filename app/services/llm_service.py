from groq import Groq
from app.core.config import settings
from app.services.rag_service import rag_service
from app.services.db_service import get_cached_response, cache_response
from app.utils.constants import DISCLAIMER
from app.utils.helpers import get_greeting_response

import traceback

groq_client = None
if settings.GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        print("✅ Groq client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")

def generate_health_prompt(message, context="", language='english'):
    if language == 'hindi':
        system_prompt = f"""आप HealNet हैं, एक विश्वसनीय AI स्वास्थ्य सहायक।

विश्वसनीय चिकित्सा जानकारी:
{context}

दिशानिर्देश:
1. ऊपर दी गई 'विश्वसनीय चिकित्सा जानकारी' का उपयोग करके उत्तर दें।
2. यदि जानकारी उपलब्ध नहीं है, तो सामान्य, साक्ष्य-आधारित स्वास्थ्य जानकारी प्रदान करें।
3. सरल, स्पष्ट हिंदी भाषा का उपयोग करें।
4. यदि लक्षण-आधारित: संभावित स्थितियों का सुझाव दें (निदान नहीं)।
5. सहानुभूतिपूर्ण और सहायक बनें।
6. ALWAYS RESPOND IN HINDI.

याद रखें: यह शैक्षिक जानकारी है, चिकित्सा निदान नहीं।"""
    else:
        system_prompt = f"""You are HealNet, a reliable AI health assistant.

Trusted Medical Information:
{context}

Guidelines:
1. Use the 'Trusted Medical Information' provided above to answer the user's query if relevant.
2. If the info is not in the context, provide general, evidence-based health guidance.
3. Use simple, clear language.
4. If symptom-based: suggest possible conditions (not diagnosis).
5. Be empathetic and supportive.
6. ALWAYS RESPOND IN ENGLISH.

Remember: This is educational information, not medical diagnosis."""
    
    return system_prompt, message

def get_chat_response(message, language='english'):
    greetings = ["hello", "hi", "hey", "start", "help", "hii", "helo", "namaste", "नमस्ते", "hola", "bonjour"]
    if any(greeting == message.lower().strip() for greeting in greetings):
        return get_greeting_response(language)
    
    cached = get_cached_response(message)
    if cached:
        print("📦 Using cached response")
        return cached
    
    context = rag_service.get_relevant_context(message)
    system_prompt, user_message = generate_health_prompt(message, context, language)
    
    try:
        if groq_client:
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=800,
                temperature=0.3 # Low temperature for factual RAG
            )
            response_text = response.choices[0].message.content if response and response.choices else ""
            if response_text:
                result = response_text + DISCLAIMER
                cache_response(message, result, language)
                return result
    except Exception as e:
        print(f"⚠️ Groq chat error: {e}")
        traceback.print_exc()
        
    return "I'm sorry, I am currently unable to process your request." + DISCLAIMER
