import os
import requests

def summarize_with_gemini(description):
    """
    Summarizes the given 'description' text to under 50 words using 
    Google's Gemini 1.5 Flash API. Returns the summarized text or None.
    """
    # 1) The base Gemini endpoint
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    # 2) Retrieve your Gemini API key from an environment variable or config
    api_key = os.environ.get("GEMINI_API_KEY")  
    # e.g. set GEMINI_API_KEY=abcdefg in your environment

    if not api_key:
        print("Gemini API key not found in environment.")
        return None

    # 3) Construct the query parameters with your key
    params = {"key": api_key}

    # 4) Build the JSON body (the prompt telling Gemini what to do)
    prompt_text = f"summarize this text using less than 50 words: {description}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt_text}
            ]
        }]
    }

    headers = {"Content-Type": "application/json"}

    try:
        # 5) Make the POST request
        response = requests.post(url, params=params, headers=headers, json=payload)
        response.raise_for_status()  # raise error if status != 200
        data = response.json()
        
        # The response typically contains an array "candidates" with summarized text
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                return parts[0].get("text")  # The actual summarized text
        return None

    except requests.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return None
