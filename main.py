import pyttsx3
import speech_recognition as sr
import datetime
import os
import sys
import webbrowser
import shutil
import subprocess
from AppOpener import open as open_app, close as close_app
from google import genai
from google.genai import types
import ollama
from duckduckgo_search import DDGS

# --- 1. CONFIGURATION & DIAGNOSTICS ---
ASSISTANT_NAME = "Raj"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Replace with your actual key
LOCAL_MODEL = "llama3"                  # The model you pulled in Ollama

def check_env():
    print(f"--- {ASSISTANT_NAME} System Check ---")
    
    # Check Python
    print(f"[✓] Python: {sys.version.split()[0]}")

    # Check Gemini
    g_ready = False
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        g_ready = True
        print("[✓] Gemini API: Configured")
    else:
        print("[!] Gemini API: Missing (Cloud AI Disabled)")

    # Check Ollama
    o_ready = False
    try:
        ollama.list()
        o_ready = True
        print("[✓] Ollama: Running")
    except:
        print("[!] Ollama: Not found (Local AI Disabled)")

    return g_ready, o_ready

GEMINI_READY, OLLAMA_READY = check_env()

# --- 2. INITIALIZATION ---
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_READY else None
engine = pyttsx3.init()
engine.setProperty('rate', 185)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)

def speak(text):
    print(f"{ASSISTANT_NAME}: {text}")
    engine.say(text)
    engine.runAndWait()

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source, duration=0.7)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            print(f"User: {query}")
            return query.lower()
        except Exception:
            return "none"

# --- 3. TOOLS & FEATURES ---

def google_search_local(query):
    """Fallback search for local AI using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=2)]
            return "\n".join(results)
    except:
        return ""

def ask_ai(prompt):
    """Hybrid Brain: Gemini Cloud -> Ollama Local -> Error"""
    # 1. Try Gemini with Google Search Tool
    if GEMINI_READY and client:
        try:
            search_tool = types.Tool(google_search=types.GoogleSearch())
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(tools=[search_tool])
            )
            return response.text
        except:
            print("Gemini failed, trying Ollama...")

    # 2. Try Ollama Local with Scraping
    if OLLAMA_READY:
        try:
            context = google_search_local(prompt)
            full_prompt = f"Search Context: {context}\n\nUser: {prompt}"
            res = ollama.chat(model=LOCAL_MODEL, messages=[
                {'role': 'user', 'content': full_prompt}
            ])
            return res['message']['content']
        except:
            return "Local AI is having trouble. Is the model loaded?"

    return "No AI brains available. Please check your API key or Ollama service."

def manage_files(query):
    """Create, Read, Delete Files/Folders"""
    if "create file" in query:
        speak("What should I name the file?")
        name = take_command()
        if name != "none":
            with open(name, "w") as f: f.write("")
            speak(f"File {name} created.")
    
    elif "create folder" in query:
        speak("Folder name?")
        name = take_command()
        if name != "none":
            os.makedirs(name, exist_ok=True)
            speak(f"Folder {name} created.")

    elif "delete" in query:
        target = query.replace("delete", "").strip()
        if os.path.exists(target):
            if os.path.isfile(target): os.remove(target)
            else: shutil.rmtree(target)
            speak(f"Deleted {target}.")
        else:
            speak("Target not found.")

# --- 4. MAIN CONTROLLER ---
if __name__ == "__main__":
    hour = datetime.datetime.now().hour
    greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    speak(f"{greet} sir. Raj is online.")

    while True:
        query = take_command()
        if query == "none": continue

        # A. LOCAL APP CONTROL (Notepad, Chrome, WhatsApp, etc.)
        if "open" in query and "." not in query and "website" not in query:
            app_name = query.replace("open", "").strip()
            speak(f"Opening {app_name}")
            open_app(app_name, match_closest=True)

        elif "close" in query:
            app_name = query.replace("close", "").strip()
            speak(f"Closing {app_name}")
            close_app(app_name, match_closest=True)

        # B. WEB BROWSING
        elif "open website" in query:
            site = query.replace("open website", "").strip()
            webbrowser.open(f"https://{site}")
            speak(f"Opening {site}")

        # C. FILE MANAGEMENT
        elif any(w in query for w in ["file", "folder", "directory", "delete"]):
            manage_files(query)

        # D. TIME
        elif "time" in query:
            speak(datetime.datetime.now().strftime("%I:%M %p"))

        # E. EXIT
        elif any(w in query for w in ["exit", "stop", "offline", "bye"]):
            speak("Powering down. Goodbye!")
            sys.exit()

        # F. AI RESEARCH & CHAT (Default)
        else:
            answer = ask_ai(query)
            speak(answer)