from fastapi import APIRouter, UploadFile, File, Form, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from app.services.llm_service import get_chat_response
from app.services.image_service import analyze_medical_image
from app.utils.helpers import detect_language, detect_emergency
from app.services.db_service import log_interaction
import requests

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: Request):
    """
    Endpoint for Web or Mobile app integration.
    Expects JSON: {"message": "Hello", "language": "english"}
    """
    data = await request.json()
    message = data.get("message", "")
    language = data.get("language", detect_language(message))
    
    response_text = get_chat_response(message, language)
    
    log_interaction("chat", language, success=True)
    return {"response": response_text}

@router.post("/whatsapp")
async def whatsapp_endpoint(
    Body: str = Form(""),
    NumMedia: int = Form(0),
    From: str = Form(""),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None)
):
    """
    Endpoint for Twilio WhatsApp webhook integration.
    """
    message_body = Body.strip()
    language = detect_language(message_body)
    
    twilio_resp = MessagingResponse()
    
    if detect_emergency(message_body):
        # Could provide emergency response here
        pass

    try:
        # Handle Image
        if NumMedia > 0 and MediaUrl0 and MediaContentType0:
            if MediaContentType0.startswith('image/'):
                media_resp = requests.get(MediaUrl0)
                if media_resp.status_code == 200:
                    image_bytes = media_resp.content
                    analysis_result = analyze_medical_image(image_bytes, language)
                    twilio_resp.message(analysis_result)
                    log_interaction("image_analysis", language, success=True)
                    return Response(content=str(twilio_resp), media_type="application/xml")
        
        # Handle Text
        if message_body:
            ai_response = get_chat_response(message_body, language)
            twilio_resp.message(ai_response)
            log_interaction("chat", language, success=True)
            return Response(content=str(twilio_resp), media_type="application/xml")
            
    except Exception as e:
        print(f"WhatsApp error: {e}")
        twilio_resp.message("I encountered an error processing your request. Please try again later.")
        
    return Response(content=str(twilio_resp), media_type="application/xml")

@router.post("/analyze-image")
async def analyze_image_endpoint(file: UploadFile = File(...), language: str = Form("english")):
    """
    Direct image analysis API endpoint.
    """
    image_bytes = await file.read()
    result = analyze_medical_image(image_bytes, language)
    return {"analysis": result}
