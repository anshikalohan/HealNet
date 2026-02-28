from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to HealNet API"
    assert data["status"] == "online"

def test_chat_endpoint_structure():
    # This just tests if the endpoint accepts the correct structure
    # and returns a valid response format. It doesn't mock the LLM
    # so it might hit the Groq API or return the fallback if no key is present.
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "language": "english"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
