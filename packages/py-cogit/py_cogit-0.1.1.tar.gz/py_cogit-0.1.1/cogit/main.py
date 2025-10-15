import json
import os
import subprocess
import sys

from dotenv import load_dotenv
from .defaults import DEFAULT_PROMPT
import google.generativeai as genai

load_dotenv()

command = ["git", "diff", "--staged"]
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except KeyError:
    print("A error occurred with GOOGLE_API_KEY.")
    
def get_staged_modifications():
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding="utf-8")
        return result.stdout
    except subprocess.CalledProcessError:
        print("Error: The 'cogit' command must be run inside a valid Git repository.", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Error: Git command not found. Please install Git and ensure it's in your system's PATH.", file=sys.stderr)
        return None
        
def build_prompt(modifications):
    user_prompt = os.getenv("PROMPT")
    prompt_template = user_prompt if user_prompt else DEFAULT_PROMPT
    return prompt_template.format(modifications=modifications)

def analyze_code_with_gemini(modifications):
    if not modifications:
        print("No modifications.")
        return
    generation_config = {
        "response_mime_type": "application/json"
    }
    
    model = genai.GenerativeModel(os.getenv("GEMINI_VERSION"), generation_config=generation_config)
    try:
        response = model.generate_content(build_prompt(modifications))
        analysis = json.loads(response.text)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"A error occurred: {e}")

def main():       
    modifications = get_staged_modifications()

    if modifications is not None:
        analyze_code_with_gemini(modifications)

if __name__ == "__main__":
    main()