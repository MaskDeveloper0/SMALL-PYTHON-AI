import os
import sys
import subprocess
import datetime
import shutil
import webbrowser

# --- 1. AUTO-DEPENDENCY INSTALLER (Runs first) ---
def install_dependencies():
    """Checks for required libraries and installs them if missing."""
    required = [
        "pyttsx3", 
        "SpeechRecognition", 
        "requests", 
        "google-genai", 
        "ollama", 
        "duckduckgo-search", 
        "AppOpener",
        "pyaudio"
    ]
    
    missing = []
    for lib in required:
        try:
            if lib == "google-genai": import google.genai
            elif lib == "duckduckgo-search": import duckduckgo_search
            else: __import__(lib.lower() if lib != "SpeechRecognition" else "speech_recognition")
        except ImportError:
            missing.append(lib)

    if missing:
        print(f"\n[!] Missing dependencies: {', '.join(missing)}")
        choice = input("Shall I install them for you? (y/n): ").lower()
        if choice == 'y':
            for lib in missing:
                print(f"Installing {lib}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            print("[✓] Installation complete. Restarting script...\n")
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            print("[!] Exiting. Cannot run without these libraries.")
            sys.exit()

# Trigger Installer
install_dependencies()

# --- 2. IMPORTS (After check) ---
import pyttsx3
import speech_recognition as sr
from AppOpener import open as open_app, close as close_app
from google import genai
from google.genai import types
import ollama
from duckduckgo_search import DDGS

# --- 3. CONFIGURATION & SYSTEM CHECK ---
ASSISTANT_NAME = "Raj"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" # <--- INSERT KEY HERE
LOCAL_MODEL = "llama3"                  # Pull this in Ollama: 'ollama pull llama3'

def run_diagnostics():
    print(f"--- {ASSISTANT_NAME} Diagnostic Mode ---")
    g_ready = False
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        g_ready = True
        print("[✓] Gemini AI: Configured")
    else:
        print("[!] Gemini AI: Key Missing (Cloud AI disabled)")

    o_ready = False
    try:
        ollama.list()
        o_ready = True
        print("[✓] Ollama: Service Running")
    except:
        print("[!] Ollama: Not Found (Local AI disabled)")
    
    return g_ready, o_ready

GEMINI_READY, OLLAMA_READY = run_diagnostics()

# --- 4. CORE ENGINE ---
engine = pyttsx3.init()
engine.setProperty('rate', 190)
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_READY else None

def speak(text):
    print(f"{ASSISTANT_NAME}: {text}")
    engine.say(text)
    engine.runAndWait()

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            query = r.recognize_google(audio, language='en-in')
            print(f"User: {query}")
            return query.lower()
        except: return "none"

# --- 5. AI BRAIN & TOOLS ---
def ask_ai(prompt):
    """Hybrid: Gemini (Cloud/Search) -> Ollama (Local/Scrape) -> Fallback"""
    if GEMINI_READY and client:
        try:
            search_tool = types.Tool(google_search=types.GoogleSearch())
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(tools=[search_tool])
            )
            return response.text
        except: pass

    if OLLAMA_READY:
        try:
            # Scrape web for local AI context
            with DDGS() as ddgs:
                results = [r['body'] for r in ddgs.text(prompt, max_results=1)]
            context = results[0] if results else "No live info."
            res = ollama.chat(model=LOCAL_MODEL, messages=[
                {'role': 'user', 'content': f"Context: {context}\n\nQuestion: {prompt}"}
            ])
            return res['message']['content']
        except: return "Local AI is struggling. Check Ollama logs."

    return "No AI brain is active. I can only do system tasks."

def manage_files(query):
    if "create file" in query:
        speak("File name?")
        name = take_command().replace(" ", "")
        if name != "none":
            with open(name, "w") as f: f.write("")
            speak(f"File {name} is created.")
    elif "create folder" in query:
        speak("Folder name?")
        name = take_command()
        if name != "none":
            os.makedirs(name, exist_ok=True)
            speak(f"Folder {name} is ready.")
    elif "delete" in query:
        target = query.replace("delete", "").strip()
        if os.path.exists(target):
            if os.path.isfile(target): os.remove(target)
            else: shutil.rmtree(target)
            speak("Target deleted.")

# --- 6. MAIN EXECUTION ---
if __name__ == "__main__":
    speak(f"All systems active. I am {ASSISTANT_NAME}.")

    while True:
        query = take_command()
        if query == "none": continue

        # Local App Control (Windows Apps)
        if "open" in query and "." not in query and "website" not in query:
            app = query.replace("open", "").strip()
            speak(f"Opening {app}")
            open_app(app, match_closest=True)

        elif "close" in query:
            app = query.replace("close", "").strip()
            speak(f"Closing {app}")
            close_app(app, match_closest=True)

        # Web Browsing
        elif "open website" in query:
            site = query.replace("open website", "").strip()
            webbrowser.open(f"https://{site}")
            speak(f"Opening {site}")

        # File Operations
        elif any(w in query for w in ["file", "folder", "directory", "delete"]):
            manage_files(query)

        # System Tasks
        elif "time" in query:
            speak(datetime.datetime.now().strftime("%I:%M %p"))

        elif any(w in query for w in ["exit", "bye", "offline", "stop"]):
            speak("Goodbye sir. Shutting down systems.")
            break

        # AI Chat/Knowledge
        else:
            answer = ask_ai(query)
            speak(answer)
            #end