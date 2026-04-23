#!/usr/bin/env python
"""
Test script to verify Brevo email configuration
Run with: python manage.py shell < test_brevo_email.py
Or: python test_brevo_email.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.conf import settings
from hello.views import send_email_via_brevo_api

def test_brevo_configuration():
    """Test Brevo email configuration"""
    
    print("=" * 60)
    print("BREVO EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # Check if API key is set
    print(f"\n1. Checking BREVO_API_KEY...")
    if settings.BREVO_API_KEY:
        print(f"   ✓ API Key is configured")
        print(f"   Key starts with: {settings.BREVO_API_KEY[:20]}...")
    else:
        print(f"   ✗ API Key is NOT configured")
        print(f"   Please set BREVO_API_KEY in your .env file")
        return False
    
    # Check from email
    print(f"\n2. Checking DEFAULT_FROM_EMAIL...")
    if settings.DEFAULT_FROM_EMAIL:
        print(f"   ✓ From Email: {settings.DEFAULT_FROM_EMAIL}")
        if settings.DEFAULT_FROM_EMAIL == "your-verified-email@example.com":
            print(f"   ✗ WARNING: This is the default placeholder!")
            print(f"   Please update DEFAULT_FROM_EMAIL to your verified Brevo sender email")
            return False
    else:
        print(f"   ✗ From Email is NOT configured")
        return False
    
    # Check email timeout
    print(f"\n3. Checking EMAIL_TIMEOUT...")
    print(f"   Timeout: {settings.EMAIL_TIMEOUT} seconds")
    
    # Try sending test email
    print(f"\n4. Attempting to send test email...")
    try:
        result = send_email_via_brevo_api(
            subject="ASSIST Email Test",
            message="This is a test email from your ASSIST system. If you received this, your Brevo configuration is working correctly!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipients=[settings.DEFAULT_FROM_EMAIL]
        )
        print(f"   ✓ Email sent successfully!")
        print(f"   Response: {result}")
        return True
    except Exception as e:
        print(f"   ✗ Failed to send email")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_brevo_configuration()
    print("\n" + "=" * 60)
    if success:
        print("✓ BREVO CONFIGURATION IS WORKING CORRECTLY!")
    else:
        print("✗ BREVO CONFIGURATION HAS ISSUES - SEE ABOVE FOR DETAILS")
    print("=" * 60)
