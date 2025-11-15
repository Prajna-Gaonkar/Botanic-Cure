import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from datetime import datetime, timedelta

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_email(to_email, subject, body):
    """Send an email using SMTP"""
    # Get email credentials from environment variables
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    sender_email = os.environ.get('SMTP_EMAIL')
    sender_password = os.environ.get('SMTP_PASSWORD')

    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        raise ValueError("Email configuration is missing. Please set SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, and SMTP_PASSWORD environment variables.")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add body
    msg.attach(MIMEText(body, 'plain'))

    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_verification_email(user_email, verification_code):
    """Send verification email to user"""
    subject = "Verify Your Botanic Cure Account"
    body = f"""Welcome to Botanic Cure!
    
Your verification code is: {verification_code}

Please enter this code to verify your account. This code will expire in 30 minutes.

If you didn't create an account, please ignore this email.

Best regards,
Botanic Cure Team"""
    
    return send_email(user_email, subject, body)

def send_reset_password_email(user_email, reset_code):
    """Send password reset email to user"""
    subject = "Reset Your Botanic Cure Password"
    body = f"""Hello,
    
You requested to reset your password for Botanic Cure.

Your password reset code is: {reset_code}

Please enter this code to reset your password. This code will expire in 30 minutes.

If you didn't request a password reset, please ignore this email.

Best regards,
Botanic Cure Team"""
    
    return send_email(user_email, subject, body)

def send_feedback_email(feedback, user_info=None):
    """Send feedback email to owner"""
    owner_email = os.environ.get('OWNER_EMAIL', os.environ.get('SMTP_EMAIL'))  # Fallback to SMTP_EMAIL if OWNER_EMAIL not set
    
    subject = "New Feedback from Botanic Cure User"
    
    # Add user info if available
    user_details = ""
    if user_info:
        user_details = f"""
Submitted by:
Username: {user_info.get('username', 'Anonymous')}
Email: {user_info.get('email', 'Not provided')}
"""

    body = f"""New feedback received from Botanic Cure:

{feedback}

{user_details}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    return send_email(owner_email, subject, body)