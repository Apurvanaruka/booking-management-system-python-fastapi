"""
OTP Service — Dev mode uses static OTP '123456'.
Replace with Twilio integration for production.
"""
import logging
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.otp_request import OTPRequest

logger = logging.getLogger(__name__)

# Dev mode flag — set to False and configure Twilio for production
DEV_MODE = True
DEV_OTP = "123456"

# OTP settings
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3


def generate_otp() -> str:
    """Generate a random 6-digit OTP. In dev mode, always returns '123456'."""
    if DEV_MODE:
        return DEV_OTP
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


def send_otp_sms(phone_number: str, otp_code: str) -> bool:
    """
    Send OTP via SMS.
    Dev mode: logs OTP to console.
    Production: integrate with Twilio.
    """
    if DEV_MODE:
        logger.info(f"[DEV MODE] OTP for {phone_number}: {otp_code}")
        print(f"\n{'='*50}")
        print(f"  DEV MODE — OTP for {phone_number}: {otp_code}")
        print(f"{'='*50}\n")
        return True

    # TODO: Twilio integration
    # from twilio.rest import Client
    # client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    # message = client.messages.create(
    #     body=f"Your OTP is: {otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes.",
    #     from_=TWILIO_PHONE_NUMBER,
    #     to=phone_number
    # )
    # return message.sid is not None

    logger.error("Twilio not configured. Set DEV_MODE=False and configure Twilio credentials.")
    return False


def create_otp_request(db: Session, phone_number: str) -> Optional[OTPRequest]:
    """Create a new OTP request and send the OTP."""
    otp_code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Invalidate any existing un-verified OTPs for this phone
    existing = db.query(OTPRequest).filter(
        OTPRequest.phone_number == phone_number,
        OTPRequest.is_verified == False,
    ).all()
    for old_otp in existing:
        db.delete(old_otp)

    # Create new OTP request
    otp_request = OTPRequest(
        phone_number=phone_number,
        otp_code=otp_code,
        expires_at=expires_at,
    )
    db.add(otp_request)
    db.commit()
    db.refresh(otp_request)

    # Send via SMS
    sent = send_otp_sms(phone_number, otp_code)
    if not sent:
        logger.error(f"Failed to send OTP to {phone_number}")

    return otp_request


def verify_otp(db: Session, phone_number: str, otp_code: str) -> bool:
    """Verify an OTP code for a given phone number."""
    otp_request = db.query(OTPRequest).filter(
        OTPRequest.phone_number == phone_number,
        OTPRequest.is_verified == False,
    ).order_by(OTPRequest.created_at.desc()).first()

    if not otp_request:
        return False

    # Check expiry
    if datetime.now(timezone.utc) > otp_request.expires_at:
        return False

    # Check max attempts
    if otp_request.attempts >= MAX_OTP_ATTEMPTS:
        return False

    # Increment attempts
    otp_request.attempts += 1

    # Verify
    if otp_request.otp_code != otp_code:
        db.commit()
        return False

    # Mark as verified
    otp_request.is_verified = True
    db.commit()
    return True
