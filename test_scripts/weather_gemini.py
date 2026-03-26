#!/usr/bin/env python3
"""
Simple script to get today's weather using Google Gemini API
"""

import google.genai as genai
import os

# Configure the API key
# Make sure to set your GOOGLE_API_KEY environment variable
# or replace with your API key directly
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it and try again.")

client = genai.Client(api_key=api_key)

# Ask for today's weather
prompt = "What is today's weather in Sofia, Bulgaia? Please provide a brief summary."

try:
    response = client.models.generate_content(
        model="models/gemini-flash-lite-latest",
        contents=prompt
    )
    print("Gemini API Response:")
    print("-" * 50)
    print(response.text)
except Exception as e:
    print(f"Error: {e}")

