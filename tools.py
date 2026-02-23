"""
Tools module for the Friday AI Assistant.
Contains tool functions for weather, web search, and email sending.
"""

import os
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv
from duckduckgo_search import DDGS
import requests
from email_module import send_email as _send_email, generate_email

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# ========================
# TOOL 1: Get Weather
# ========================
def get_weather(location: str) -> str:
    """
    Fetches weather information for a given location using Open-Meteo API (free, no key required).
    
    Parameters:
    - location: City name (e.g., "San Francisco")
    
    Returns:
    - Weather information as a formatted string
    """
    try:
        # Get coordinates from location name using forward geocading
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        
        if not geo_response.get('results'):
            return f"Could not find location: {location}"
        
        # Extract coordinates
        result = geo_response['results'][0]
        latitude = result['latitude']
        longitude = result['longitude']
        
        # Get weather data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        weather_response = requests.get(weather_url).json()
        
        current = weather_response['current']
        
        # Format weather info
        weather_desc = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Foggy",
            51: "Light drizzle",
            61: "Slight rain",
            80: "Slight showers",
            95: "Thunderstorm"
        }
        
        code = current['weather_code']
        description = weather_desc.get(code, "Unknown")
        
        return (
            f"Weather in {location}:\n"
            f"Temperature: {current['temperature_2m']}°C\n"
            f"Humidity: {current['relative_humidity_2m']}%\n"
            f"Condition: {description}\n"
            f"Wind Speed: {current['wind_speed_10m']} km/h"
        )
    
    except Exception as e:
        logging.error(f"Weather error: {str(e)}")
        return f"Failed to get weather for {location}: {str(e)}"


# ========================
# TOOL 2: Search Web
# ========================
def search_web(query: str, max_results: int = 5) -> str:
    """
    Searches the web using DuckDuckGo (no API key required).
    
    Parameters:
    - query: Search query string
    - max_results: Maximum number of results to return (default: 5)
    
    Returns:
    - Formatted search results as a string
    """
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)
        
        if not results:
            return f"No results found for: {query}"
        
        formatted_results = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            formatted_results += f"{i}. {result['title']}\n"
            formatted_results += f"   URL: {result['href']}\n"
            formatted_results += f"   {result['body']}\n\n"
        
        return formatted_results
    
    except Exception as e:
        logging.error(f"Web search error: {str(e)}")
        return f"Failed to search web for '{query}': {str(e)}"


# ========================
# TOOL 3: Send Email
# ========================
async def send_email(
    to_email: str,
    subject: str,
    message: str,
    from_account: str = "miguel13",
    cc_email: Optional[str] = None
) -> str:
    """
    Sends an email via Gmail using one of the configured accounts.
    
    Parameters:
    - to_email: Recipient's email address
    - subject: Email subject
    - message: Email body content
    - from_account: Account identifier ('miguel13', 'miguel07', 'miguellewis') - default: 'miguel13'
    - cc_email: Optional CC email address
    
    Returns:
    - Success or error message
    
    Note: This tool uses the email_module to handle SMTP configuration and multi-account support.
    """
    try:
        # Use the email module's send_email function
        result = await _send_email(
            to_email=to_email,
            subject=subject,
            message=message,
            from_account=from_account,
            cc_email=cc_email
        )
        logging.info(f"Email sent to {to_email} from {from_account}")
        return result
    
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logging.error(error_msg)
        return error_msg


# ========================
# HELPER: Email Generation
# ========================
async def generate_and_send_email(
    to_email: str,
    subject: str,
    topic: str,
    from_account: str = "miguel13",
    cc_email: Optional[str] = None
) -> str:
    """
    Generates an email using AI and sends it via Gmail.
    
    Parameters:
    - to_email: Recipient's email address
    - subject: Email subject
    - topic: Topic for AI email generation
    - from_account: Account identifier - default: 'miguel13'
    - cc_email: Optional CC email address
    
    Returns:
    - Success or error message
    """
    try:
        # Generate email using AI
        generated_message = await generate_email(to_email, subject, topic, from_account)
        
        if "Failed" in generated_message:
            return generated_message
        
        # Send the generated email
        result = await send_email(to_email, subject, generated_message, from_account, cc_email)
        return result
    
    except Exception as e:
        error_msg = f"Failed to generate and send email: {str(e)}"
        logging.error(error_msg)
        return error_msg


if __name__ == "__main__":
    # Example usage of tools
    print("=== Friday AI Assistant Tools ===\n")
    
    # Test weather tool
    print("Testing Weather Tool:")
    print(get_weather("London"))
    print("\n" + "="*50 + "\n")
    
    # Test web search tool
    print("Testing Web Search Tool:")
    print(search_web("Python programming", max_results=3))
    print("\n" + "="*50 + "\n")
    
    # Test email tool (async)
    async def test_email():
        print("Testing Email Tool:")
        # Uncomment below to test (requires valid Gmail setup)
        # result = await send_email(
        #     to_email="test@example.com",
        #     subject="Test Email from Friday",
        #     message="This is a test email from your Friday assistant.",
        #     from_account="miguel13"
        # )
        # print(result)
        print("Email tool available (requires Gmail credentials)")
    
    asyncio.run(test_email())