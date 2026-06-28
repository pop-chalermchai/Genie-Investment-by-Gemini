import os
import sys

# Print environment variables starting with GOOGLE or GEMINI
print("--- Active Environment Variables ---")
for key, val in os.environ.items():
    if key.startswith("GOOGLE_") or key.startswith("GEMINI_"):
        # Hide the middle of the value for safety
        if len(val) > 8:
            masked_val = f"{val[:4]}...{val[-4:]}"
        else:
            masked_val = "***"
        print(f"{key}: {masked_val}")

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package is not installed.")
    sys.exit(1)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is not set.")
    sys.exit(1)

print(f"\nConfiguring new google-genai Client with API key starting with: '{api_key[:10]}...'")
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Failed to instantiate client: {e}")
    sys.exit(1)

print("\n--- Trying simple generation with gemini-2.5-flash ---")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Say hello in Thai',
    )
    print(f"Success! Response: '{response.text.strip()}'")
except Exception as e:
    print(f"Failed to generate content: {e}")
