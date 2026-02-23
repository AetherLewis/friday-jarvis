import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional

@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str) -> str:
    """
    Get the current weather for a given city.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}." 

@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str) -> str:
    """
    Search the web using DuckDuckGo.
    """
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search results for '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"An error occurred while searching the web for '{query}'."    

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    from_account: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Sends an email via Gmail SMTP using the selected account.
    """
    # Define email accounts from environment variables
    email_accounts = {
        "miguel13": {
            "user": os.getenv("GMAIL_USER_1"),
            "password": os.getenv("GMAIL_PASS_1", "").strip() if os.getenv("GMAIL_PASS_1") else None
        },
        "miguel07": {
            "user": os.getenv("GMAIL_USER_2"),
            "password": os.getenv("GMAIL_PASS_2", "").strip() if os.getenv("GMAIL_PASS_2") else None
        },
        "miguellewis": {
            "user": os.getenv("GMAIL_USER_3"),
            "password": os.getenv("GMAIL_PASS_3", "").strip() if os.getenv("GMAIL_PASS_3") else None
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