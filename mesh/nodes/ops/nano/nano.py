# File: /home/ds/sambashare/GOB/GOB-system/gob-nano/nano.py

import requests
from datetime import datetime
import random
from nanoconfig import SYSTEM_PROMPT, API_KEY, MODEL_NAME, SECONDARY_PROMPT, TEMPERATURE, ACRONYMS

# -----------------------------
# Minimal Logger
# -----------------------------
def log(msg):
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] {msg}")

# -----------------------------
# Chat function
# -----------------------------
def chat_with_model(system_prompt: str, user_input: str, secondary_prompt: str, temperature: float):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Randomly pick an acronym from the config for flavor
    chosen_acronym = random.choice(ACRONYMS)
    system_with_acronym = f"{system_prompt}\nCurrent identity: {chosen_acronym}"

    messages = [{"role": "system", "content": system_with_acronym}]
    
    # Inject secondary prompt if provided
    if secondary_prompt.strip():
        messages.append({"role": "system", "content": secondary_prompt})
    
    messages.append({"role": "user", "content": user_input})
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"], chosen_acronym

# -----------------------------
# Main Loop
# -----------------------------
def start_chat():
    log("=== Nano GOB Chat Interface ===")
    log("-------------------------------")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                log("Exiting Nano GOB.")
                break

            reply, acronym = chat_with_model(SYSTEM_PROMPT, user_input, SECONDARY_PROMPT, TEMPERATURE)

            # Log conversation
            log(f"You: {user_input}")
            log(f"GOB ({acronym}): {reply}")

        except KeyboardInterrupt:
            log("Exiting Nano GOB.")
            break
        except Exception as e:
            log(f"[Error] {e}")

if __name__ == "__main__":
    start_chat()
