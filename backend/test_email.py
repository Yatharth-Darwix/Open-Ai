import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email():
    print("--- Testing SMTP Configuration ---")
    
    smtp_user = os.getenv("SMTP_EMAIL")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    
    # If ALERT_RECIPIENT_EMAIL is not set, default to self (smtp_user)
    recipient = os.getenv("ALERT_RECIPIENT_EMAIL", smtp_user)

    print(f"Server:    {smtp_server}:{smtp_port}")
    print(f"User:      {smtp_user}")
    print(f"Recipient: {recipient}")
    
    if not smtp_user or not smtp_pass:
        print("ERROR: SMTP_EMAIL or SMTP_PASSWORD is missing in .env")
        return

    msg = EmailMessage()
    msg["Subject"] = "Test Email from OpenAI Monitor"
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg.set_content("This is a test email to verify your SMTP credentials/App Password are working correctly.")

    try:
        print(f"\nConnecting to {smtp_server}...")
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            
        print("\nSUCCESS: Test email sent successfully!")
        print(f"Please check the inbox for: {recipient}")
        
    except Exception as e:
        print(f"\nFAILURE: Could not send email.")
        print(f"Error: {e}")
        print("\nTroubleshooting Tips:")
        print("1. Check if 'SMTP_PASSWORD' is a valid Google App Password (not your Gmail login password).")
        print("2. Ensure '2-Step Verification' is ON for your Google Account.")
        print("3. Verify there are no extra spaces in the .env file.")

if __name__ == "__main__":
    test_email()
