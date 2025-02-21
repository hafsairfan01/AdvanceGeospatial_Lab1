from dotenv import load_dotenv
load_dotenv()  # loads variables from .env into os.environ

import os
gemini_key = os.environ.get("GEMINI_API_KEY")
print("Gemini key:", os.environ.get("GEMINI_API_KEY"))
