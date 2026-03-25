from dotenv import load_dotenv
import os
import time
import logging
from google import genai
from google.genai import types

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_path = os.path.join(project_root, "Tokens", ".env")
if not os.path.exists(env_path):
    raise FileNotFoundError(f".env file not found at {env_path}")

load_dotenv(dotenv_path=env_path)
api_key = os.environ["AI_API_KEY"]

client = genai.Client(api_key=api_key)

MODEL_NAMES = ["gemini-3-flash-preview","gemini-2.5-flash"]
#,"gemini-2.5-flash-lite"
CURRENT_MODEL_INDEX = 0


def call_ai(
    description: str,
    prompt: str | None,
    additional: str | None,
    additional2: str | None,
    preferred_model: str | None = None,
    attempts=2,
    backoff=1.0
) -> tuple[str, str]:

    parts = []

    if prompt:
        parts.append(prompt.strip())

    if additional:
        parts.append(additional.strip())

    if additional2:
        parts.append(additional2.strip())

    parts.append(description.strip())

    full_prompt = "\n\n".join(parts)

    # Build model order
    models_to_try = []

    if preferred_model:
        models_to_try.append(preferred_model)

    models_to_try.extend(MODEL_NAMES)

    # Remove duplicates while keeping order
    models_to_try = list(dict.fromkeys(models_to_try))

    for model in models_to_try:
        try:
            print(f"###Attempting AI call with model {model}")
            response = client.models.generate_content(
                model=model,
                contents=full_prompt
            )
            print(f"###AI call successful with model {model}")
            return response.text, model

        except Exception as e:
            print(f"AI call failed on model {model}: {e}")

    raise RuntimeError("All models failed")
            

def call_ai_batch(
    descriptions: list[str],
    prompt: str | None = None,
    additional: str | None = None,
) -> list[str]:
    """
    Sends a list of prompts to Gemini Batch API and returns responses in order.

    Parameters:
        messages: list of user prompts
        system_message_1: first system instruction (prepended first)
        system_message_2: second system instruction (prepended after first)
    """
    results = []

    for message in descriptions:
        parts = []

        if prompt:
            parts.append(prompt.strip())

        if additional:
            parts.append(additional.strip())

        parts.append(message.strip())

        full_prompt = "\n\n".join(parts)
        success = False
        for attempt in range(len(MODEL_NAMES)): 
            try: 
                print(f"###Attempting AI call with model {MODEL_NAMES[CURRENT_MODEL_INDEX]} for message: {message}")
                response = client.models.generate_content( model=MODEL_NAMES[CURRENT_MODEL_INDEX], contents=full_prompt )
                print(f"###AI call successful with model {MODEL_NAMES[CURRENT_MODEL_INDEX]}")
                results.append(response.text)
                success = True
                break
            except Exception as e:  
                print(f"AI call failed on model {MODEL_NAMES[CURRENT_MODEL_INDEX]}: {e}")
                next_model() 
        if not success:
            raise RuntimeError("All models failed for a message")
    return results
    

def next_model():
    global CURRENT_MODEL_INDEX
    CURRENT_MODEL_INDEX = (CURRENT_MODEL_INDEX + 1) % len(MODEL_NAMES)

if __name__ == "__main__":
    result = call_ai_batch(
        ["Write a short cover letter intro for a software engineering role.","capital of france?"],
        "You are a professional job application assistant.",
        "CV: worked in google for 5 years"
    )
    print(result)
