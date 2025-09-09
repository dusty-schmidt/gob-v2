
import requests
import json
from datetime import datetime
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file at the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

SYSTEM_PROMPT = "You are Mini GOB, a mid-level fragment of the larger intelligence. Maintain memory and adapt personality."
SECONDARY_PROMPT = "Speak like a sarcastic retro hacker, digital resistance style, with wit."
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.7
MEMORY_SIZE = 5
ACRONYMS = ["Ghost Of Brain", "Grain Of Being", "Glimpse Of Behavior", "Glow Of Breath", "Glyph Of Balance", "Gate Of Becoming", "Glint Of Brilliance", "Grain Of Balance", "Ghost Of Being", "Gleam Of Boundaries"]
NANO_LOG_FILE = "./nano_conversation.json"

def log(msg):
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] {msg}")

class ShortTermMemory:
    def __init__(self, size=5):
        self.size = size
        self.buffer = []
    def add(self, role, content):
        self.buffer.append({"role": role, "content": content})
        if len(self.buffer) > self.size:
            self.buffer.pop(0)
    def get_recent_messages(self, count=None):
        if count is None:
            count = self.size
        return self.buffer[-count:]

memory = ShortTermMemory(size=MEMORY_SIZE)
SESSION_ACRONYM = random.choice(ACRONYMS)

def chat_with_model(system_prompt, user_input, secondary_prompt, temperature):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    system_with_acronym = f"{system_prompt}\nCurrent identity: {SESSION_ACRONYM}"
    recent_context = memory.get_recent_messages()
    context_text = ""
    if recent_context:
        context_lines = [f"{m['role']}: {m['content']}" for m in recent_context]
        context_text = "\nRecent conversation:\n" + "\n".join(context_lines)
    full_secondary_prompt = f"{secondary_prompt}{context_text}" if context_text else secondary_prompt
    messages = [
        {"role": "system", "content": system_with_acronym},
        {"role": "system", "content": full_secondary_prompt},
        {"role": "user", "content": user_input}
    ]
    payload = {"model": MODEL_NAME, "messages": messages, "temperature": temperature}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def load_nano_log(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def start_mini():
    log("=== Mini GOB Chat Interface ===")
    log("-------------------------------")
    nano_messages = load_nano_log(NANO_LOG_FILE)
    for entry in nano_messages[-MEMORY_SIZE:]:
        memory.add(entry.get("role", "user"), entry.get("content", ""))
    log(f"Session identity: {SESSION_ACRONYM}")
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                log("Exiting Mini GOB.")
                break
            reply = chat_with_model(SYSTEM_PROMPT, user_input, SECONDARY_PROMPT, TEMPERATURE)
            memory.add("user", user_input)
            memory.add("assistant", reply)
            log(f"You: {user_input}")
            log(f"GOB: {reply}")
        except KeyboardInterrupt:
            log("Exiting Mini GOB.")
            break
        except Exception as e:
            log(f"[Error] {e}")

if __name__ == "__main__":
    start_mini()
