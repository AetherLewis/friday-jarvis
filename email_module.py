import os
import logging
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from dotenv import load_dotenv
import warnings

# Suppress the FutureWarning about google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure Gemini AI
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logging.error("GOOGLE_API_KEY not found in environment variables")
else:
    genai.configure(api_key=api_key)

# Use gemini-2.5-flash model which is available and performant
model = genai.GenerativeModel('gemini-2.5-flash')

async def send_email(
    to_email: str,
    subject: str,
    message: str,
    from_account: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Sends an email via Gmail SMTP using the selected account.

    Parameters:
    - to_email: Recipient's email address
    - subject: Email subject
    - message: Email body content
    - from_account: Account identifier ('miguel13', 'miguel07', 'miguellewis')
    - cc_email: Optional CC email address

    Returns:
    - Success or error message
    """
    # Define email accounts from environment variables
    email_accounts = {
        "miguel13": {
            "user": os.getenv("GMAIL_USER_1"),
            "password": os.getenv("GMAIL_PASS_1", "").strip()
        },
        "miguel07": {
            "user": os.getenv("GMAIL_USER_2"),
            "password": os.getenv("GMAIL_PASS_2", "").strip()
        },
        "miguellewis": {
            "user": os.getenv("GMAIL_USER_3"),
            "password": os.getenv("GMAIL_PASS_3", "").strip()
        }
    }

    # Validate account selection
    account = email_accounts.get(from_account.lower())
    if not account or not account["user"] or not account["password"]:
        error_msg = "Invalid email account selected or credentials missing."
        logging.error(error_msg)
        return error_msg

    gmail_user = account["user"]
    gmail_password = account["password"]

    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        if cc_email:
            msg['Cc'] = cc_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)

        # Send the email
        to_addrs = [to_email]
        if cc_email:
            to_addrs.append(cc_email)
        text = msg.as_string()
        server.sendmail(gmail_user, to_addrs, text)
        server.quit()

        success_msg = f"Email sent successfully from {gmail_user} to {to_email}"
        logging.info(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logging.error(error_msg)
        return error_msg

async def generate_email(
    to_email: str,
    subject: str,
    topic: str,
    from_account: str
) -> str:
    """
    Generates professional email content using Gemini AI based on the topic.

    Parameters:
    - to_email: Recipient's email address
    - subject: Email subject
    - topic: Topic or description of what the email should be about
    - from_account: Account identifier for personalization

    Returns:
    - Generated email message content
    """
    try:
        # Create prompt for Gemini
        prompt = f"""
        Write a professional email from {from_account} to {to_email} with subject "{subject}" about: {topic}.
        Make it polite, clear, and concise. Include appropriate greeting and closing.
        """

        # Generate content using Gemini
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            model.generate_content, 
            prompt
        )
        generated_message = response.text.strip()

        logging.info(f"Email generated successfully for topic: {topic}")
        return generated_message

    except Exception as e:
        error_msg = f"Failed to generate email: {str(e)}"
        logging.error(error_msg)
        return error_msg

async def summarize_email(email_body: str) -> str:
    """
    Summarizes the given email body into 3 bullet points using Gemini AI.

    Parameters:
    - email_body: The full text of the email to summarize

    Returns:
    - 3-bullet-point summary
    """
    try:
        # Create prompt for Gemini
        prompt = f"""
        Summarize the following email into exactly 3 bullet points:
        {email_body}
        """

        # Generate summary using Gemini
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            model.generate_content, 
            prompt
        )
        summary = response.text.strip()

        logging.info("Email summarized successfully")
        return summary

    except Exception as e:
        error_msg = f"Failed to summarize email: {str(e)}"
        logging.error(error_msg)
        return error_msg

async def generate_and_send_email(
    to_email: str,
    subject: str,
    topic: str,
    from_account: str,
    cc_email: Optional[str] = None
) -> None:
    """
    Helper function that generates an email using AI and sends it.

    Parameters:
    - to_email: Recipient's email address
    - subject: Email subject
    - topic: Topic for email generation
    - from_account: Account identifier
    - cc_email: Optional CC email address
    """
    print(f"Generating email for topic: {topic}")
    generated_message = await generate_email(to_email, subject, topic, from_account)

    if "Failed to generate" in generated_message:
        print(generated_message)
        return

    print("Sending email...")
    result = await send_email(to_email, subject, generated_message, from_account, cc_email)
    print(result)

async def main():
    """
    Example main function demonstrating the email functionality.
    Note: This example generates emails but does not send them to avoid accidental emails.
    Uncomment the send_email calls if you want to actually send the emails.
    """
    print("=== Email Module Demonstration ===\n")

    # Example 1: Generate email from each account (not sending to avoid spam)
    accounts = ["miguel13", "miguel07", "miguellewis"]
    for account in accounts:
        print(f"--- Generating email from {account} ---")
        generated_message = await generate_email(
            to_email="example@example.com",
            subject="Test Email",
            topic="This is a test email to demonstrate the functionality",
            from_account=account
        )
        print("Generated Email Content:")
        print(generated_message)
        print()

        # Uncomment below to actually send the email
        # result = await send_email("example@example.com", "Test Email", generated_message, account)
        # print(f"Send Result: {result}")
        # print()

    # Example 2: Summarize a sample email
    sample_email = """
    Dear Professor,

    I hope this email finds you well. I am writing to request an extension for the assignment due next week.
    Unfortunately, I have been dealing with some personal matters that have affected my ability to complete the work on time.
    I would greatly appreciate it if you could grant me an additional week to submit the assignment.

    Thank you for your understanding.

    Best regards,
    Student
    """

    print("--- Summarizing Sample Email ---")
    summary = await summarize_email(sample_email)
    print("Summary:")
    print(summary)

if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())