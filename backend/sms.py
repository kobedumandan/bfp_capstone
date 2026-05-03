import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SEMAPHORE_API_KEY = os.getenv("SEMAPHORE_API_KEY")
SEMAPHORE_SENDER_NAME = os.getenv("SEMAPHORE_SENDER_NAME", "SEMAPHORE")
SEMAPHORE_API_URL = "https://api.semaphore.co/api/v4/messages"


def send_sms(to: str, message: str) -> dict:
    """Send an SMS via Semaphore. Returns the API response as a dict."""
    payload = {
        "apikey": SEMAPHORE_API_KEY,
        "number": to,
        "message": message,
        "sendername": SEMAPHORE_SENDER_NAME,
    }
    response = httpx.post(SEMAPHORE_API_URL, data=payload, timeout=10)
    response.raise_for_status()
    return response.json()
