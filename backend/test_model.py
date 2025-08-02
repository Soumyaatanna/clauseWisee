import os
from dotenv import load_dotenv
from transformers import pipeline

print("--- Loading environment variables...")
load_dotenv()
HUGGING_FACE_HUB_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN") # Not needed for public models, but we leave it

print("--- Attempting to download a PUBLIC model (distilgpt2)...")
try:
    # Using a simple, public model for this test
    generator = pipeline(
        "text-generation",
        model="distilgpt2",
    )
    print("\n✅✅✅ SUCCESS! Public model loaded correctly. ✅✅✅")
    print("\nThis means your general connection is OK, but something is blocking access to gated models.")
except Exception as e:
    print(f"\n❌❌❌ FAILED. General connection to Hugging Face might be the issue. Error: {e} ❌❌❌")