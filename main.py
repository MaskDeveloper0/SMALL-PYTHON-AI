import pyttsx3
import speech_recognition as sr
import datetime
import os
import sys
import subprocess
import requests
import webbrowser
import shutil
from google import genai
from google.genai import types
import ollama
from duckduckgo_search import DDGS

# --- 1. SYSTEM ENVIRONMENT CHECK ---
def check_environment():
    print("--- System Diagnostic ---")
    
    # Check Python Version
    py_version = sys.version.split()[0]
    print(f"[✓] Python Version: {py_version}")

    # Check Ollama Status
    ollama_ready = False
    try:
        # Try to list models to see if the service is running
        ollama.list()
        print("[✓] Ollama Service: Running")
        ollama_ready = True
    except Exception:
        print("[!] Ollama Service: Not found or not running. (Local AI disabled)")

    # Check Gemini API
    gemini_ready = False
    api_key = "YOUR_GEMINI_API_KEY" # <--- Put your key here
    if api_key and api_key != "YOUR_GEMINI_API_KEY":
        print("[✓] Gemini API: Key Configured")
        gemini_ready = True
    else:
        print("[!] Gemini API: Key missing. (Cloud AI disabled)")

    return gemini_ready, ollama_ready, api_key

# --- CONFIGURATION & INIT ---
ASSISTANT_NAME = "Raj"
GEMINI_READY, OLLAMA_READY, API_KEY = check_environment()

# Initialize Gemini Client if possible
client = None
if GEMINI_READY:
    client = genai.Client(api_key=API_KEY)

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
        except sr.UnknownValueError:
            return "none"
        except sr.RequestError:
            print("Check your internet connection for speech recognition.")
            return "none"
        except Exception as e:
            return "none"

# --- WEB SEARCH TOOLS ---
def local_web_search(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=2)]
            return "\n".join(results)
    except:
        return "No web results found."

# --- AI BRAIN (Hybrid & Optional) ---
def ask_ai(prompt):
    # Option 1: Gemini (Highest Priority)
    if GEMINI_READY and client:
        try:
            google_search_tool = types.Tool(google_search=types.GoogleSearch())
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(tools=[google_search_tool])
            )
            return response.text
        except Exception:
            print("Gemini failed, falling back...")

    # Option 2: Local Ollama (Secondary)
    if OLLAMA_READY:
        try:
            # Search web first for local context
            context = local_web_search(prompt)
            full_prompt = f"Context: {context}\n\nUser Question: {prompt}"
            
            response = ollama.chat(model='llama3', messages=[
                {'role': 'user', 'content': full_prompt},
            ])
            return response['message']['content']
        except Exception:
            return "Local AI error. Is the model 'llama3' pulled?"

    # Option 3: Basic fallback if NO AI is available
    return "I'm sorry, both Gemini and Ollama are unavailable. I can only perform local system tasks."

# --- FILE MANAGEMENT ---
def manage_files(query):
    if "create file" in query:
        speak("Name of file?")
        name = take_command()
        if name != "none":
            with open(name, "w") as f: f.write("")
            speak(f"Created {name}")
    elif "create folder" in query:
        speak("Folder name?")
        name = take_command()
        if name != "none":
            os.makedirs(name, exist_ok=True)
            speak(f"Created folder {name}")
    elif "delete" in query:
        name = query.replace("delete", "").strip()
        if os.path.exists(name):
            os.remove(name) if os.path.isfile(name) else shutil.rmtree(name)
            speak("Deleted.")

# --- MAIN LOOP ---
if __name__ == "__main__":
    # Final check before speaking
    if not GEMINI_READY and not OLLAMA_READY:
        print("\nWARNING: No AI brains available. Raj will work in 'Offline System Mode' only.")
    
    speak(f"Ready. I am {ASSISTANT_NAME}.")

    while True:
        query = take_command()
        if query == "none": continue

        # 1. System Commands
        if "time" in query:
            speak(datetime.datetime.now().strftime("%I:%M %p"))
        
        elif "open" in query:
            site = query.replace("open", "").strip()
            webbrowser.open(f"https://{site}.com")
            speak(f"Opening {site}")

        # 2. File Operations
        elif any(word in query for word in ["file", "folder", "directory", "delete"]):
            manage_files(query)

        # 3. Exit
        elif "exit" in query or "bye" in query:
            speak("Powering down.")
            break

        # 4. AI Query (Only if one is available)
        else:
            answer = ask_ai(query)
            speak(answer)

        