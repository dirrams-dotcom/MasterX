# email_utils.py - Updated for ManaGuru Re-verification
import random
import string
import threading
import requests
from kivy.clock import Clock

# ============================================
# MUST MATCH THE SECRET_KEY IN GOOGLE SCRIPT!
# ============================================
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzE8qr7oZIDl1DdGTsTkWoXfHXqPtxml3XAaVx1pfPsEWKcESf2LV89o6V--7VrMFuG/exec"
SECRET_KEY = "TutorApp2024!@#"  # <-- Keep this consistent with your Apps Script


def generate_verification_code(length=6):
    """Generates a random numeric code for student/tutor verification."""
    return ''.join(random.choices(string.digits, k=length))


def send_verification_email(recipient_email, verification_code):
    """Sync function to send data to the Google Apps Script Web App."""
    try:
        data = {
            "email": recipient_email,
            "code": verification_code,
            "secret": SECRET_KEY
        }

        # Sending POST request to your Google Script URL
        response = requests.post(
            WEBAPP_URL,
            json=data,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('success', False)
        return False

    except Exception as e:
        print(f"Email Dispatch Error: {e}")
        return False


def resend_verification_code_async(recipient_email, db_manager, callback=None):
    """
    NEW FUNCTION: Generates a new code, updates the database,
    and sends the email in the background.
    """
    new_code = generate_verification_code(6)

    def task():
        # 1. Update the database (Local + Cloud) first
        db_success = db_manager.update_verification_code(recipient_email, new_code)

        # 2. Send the actual email
        email_success = False
        if db_success:
            email_success = send_verification_email(recipient_email, new_code)

        # 3. Inform the UI on the main thread
        if callback:
            Clock.schedule_once(lambda dt: callback(email_success))

    thread = threading.Thread(target=task)
    thread.daemon = True
    thread.start()


def send_verification_email_async(recipient_email, verification_code, callback=None):
    """Background task for the initial signup verification email."""

    def send():
        success = send_verification_email(recipient_email, verification_code)
        if callback:
            Clock.schedule_once(lambda dt: callback(success))

    thread = threading.Thread(target=send)
    thread.daemon = True
    thread.start()


def send_verification_email_safe(recipient_email, verification_code, callback=None):
    """Helper for safer background dispatch."""
    return send_verification_email_async(recipient_email, verification_code, callback)
