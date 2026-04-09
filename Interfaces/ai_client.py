from dotenv import load_dotenv
from google import genai
import os

# ---- setup ----

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, "Tokens", ".env")

if not os.path.exists(env_path):
    raise FileNotFoundError(f".env file not found at {env_path}")

load_dotenv(dotenv_path=env_path)

raw_keys = os.getenv("AI_API_KEY", "")
API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

if not API_KEYS:
    raise ValueError("No API keys found in AI_API_KEY")

MODEL_NAMES = ["gemini-3-flash-preview", "gemini-2.5-flash"]


def make_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def build_prompt(description: str, prompt: str | None = None,
                 additional: str | None = None,
                 additional2: str | None = None) -> str:
    parts = [
        p.strip()
        for p in [prompt, additional, additional2, description]
        if p and p.strip()
    ]
    return "\n\n".join(parts)


def call_ai(
    description: str,
    prompt: str | None = None,
    additional: str | None = None,
    additional2: str | None = None,
    preferred_model: str | None = None,
) -> tuple[str, str]:
    full_prompt = build_prompt(description, prompt, additional, additional2)

    models_to_try = []
    if preferred_model:
        models_to_try.append(preferred_model)
    models_to_try.extend(MODEL_NAMES)

    # remove duplicates while keeping order
    models_to_try = list(dict.fromkeys(models_to_try))

    for model in models_to_try:
        for api_key in API_KEYS:
            try:
                print(f"Trying model={model} with one API key...")
                client = make_client(api_key)
                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                )
                return response.text, model
            except Exception as e:
                print(f"Failed model={model} with one key: {e}")

        print(f"All API keys failed for {model}, trying next model...")

    raise RuntimeError("All API keys failed for all models")


if __name__ == "__main__":
    result = call_ai(
        [
            "Write a short cover letter intro for a software engineering role.",
            "capital of france?",
        ],
        prompt="You are a professional job application assistant.",
        additional="CV: worked in google for 5 years",
    )
    print(result)