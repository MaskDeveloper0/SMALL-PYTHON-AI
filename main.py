import pyttsx3
import speech_recognition as sr
import datetime
import os
import sys
import requests
import webbrowser
from google import genai
from google.genai import types # For the Search Tool
import ollama
from duckduckgo_search import DDGS # For Local AI Web Search

# --- CONFIGURATION ---
ASSISTANT_NAME = "Raj"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
LOCAL_MODEL = "llama3"

# Initialize Gemini with GOOGLE_SEARCH tool enabled
client = None
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini Init Error: {e}")

# TTS Setup
engine = pyttsx3.init()
engine.setProperty('rate', 185)

def speak(audio):
    print(f"{ASSISTANT_NAME}: {audio}")
    engine.say(audio)
    engine.runAndWait()

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            query = r.recognize_google(audio, language='en-in')
            print(f"User: {query}")
            return query.lower()
        except: return "none"

# --- WEB SEARCH FOR LOCAL OLLAMA ---
def local_web_search(query):
    """Fetches snippets from the web for the local model to read."""
    with DDGS() as ddgs:
        results = [r['body'] for r in ddgs.text(query, max_results=3)]
        return "\n".join(results)

# --- AI BRAIN (With Search Capability) ---
def ask_ai(prompt):
    # 1. Gemini Cloud with Built-in Google Search
    if client:
        try:
            # We tell Gemini it is allowed to use Google Search
            google_search_tool = types.Tool(google_search=types.GoogleSearch())
            
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(tools=[google_search_tool])
            )
            return response.text
        except Exception as e:
            print(f"Gemini Search failed: {e}")

    # 2. Local Ollama with Manual Web Search
    try:
        speak("Searching the web locally...")
        web_context = local_web_search(prompt)
        combined_prompt = f"Using this info: {web_context}\n\nAnswer: {prompt}"
        
        response = ollama.chat(model=LOCAL_MODEL, messages=[
            {'role': 'user', 'content': combined_prompt},
        ])
        return response['message']['content']
    except Exception:
        return "I can't access the web right now. Please check Ollama."

# --- MAIN LOOP ---
if __name__ == "__main__":
    speak(f"Systems online. Web search enabled.")

    while True:
        query = take_command()
        if query == "none": continue

        # File Management (Simplified trigger)
        if any(word in query for word in ["file", "folder", "directory"]):
            # (Insert the manage_files function code here)
            pass

        # Manual Website Opening
        elif "open" in query and "google" not in query:
            site = query.replace("open", "").strip()
            webbrowser.open(f"https://{site}.com")
            speak(f"Opening {site}")

        # Exit
        elif "exit" in query or "bye" in query:
            speak("Goodbye!")
            break

        # AI Research (The default for everything else)
        else:
            answer = ask_ai(query)
            speak(answer)