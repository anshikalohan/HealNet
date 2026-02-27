from app.utils.helpers import detect_language, detect_emergency

def test_detect_language_english():
    text = "Hello, I have a headache."
    assert detect_language(text) == 'english'

def test_detect_language_hindi():
    text = "नमस्ते, मुझे बुखार है।"
    assert detect_language(text) == 'hindi'

def test_detect_language_mixed():
    # If the text is heavily mixed, it falls back to english unless >30% are hindi chars
    text = "Hello, मुझे बुखार है।"
    assert detect_language(text) == 'hindi'

def test_detect_emergency_true():
    message = "I need an ambulance quickly!"
    assert detect_emergency(message) is True

def test_detect_emergency_false():
    message = "What are the symptoms of a cold?"
    assert detect_emergency(message) is False

def test_detect_emergency_hindi():
    message = "आपातकाल! मदद करें!"
    assert detect_emergency(message) is True
