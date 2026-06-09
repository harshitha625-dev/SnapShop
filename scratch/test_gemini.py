import sys
import os

print("Python version:", sys.version)

try:
    import google.generativeai as genai
    print("Successfully imported google.generativeai")
    
    # Check if a key is loaded in env
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        print("API Key found in environment:", key[:6] + "..." + key[-4:] if len(key) > 10 else "too short")
        genai.configure(api_key=key)
        # Try a tiny listing model call to test key validity
        try:
            models = genai.list_models()
            print("Gemini API key is valid. Successfully listed models:")
            for m in list(models)[:3]:
                print(f"  - {m.name}")
        except Exception as api_err:
            print("Gemini API call failed:", api_err)
    else:
        print("No GEMINI_API_KEY or GOOGLE_API_KEY found in environment.")
except ImportError as imp_err:
    print("Failed to import google.generativeai:", imp_err)
