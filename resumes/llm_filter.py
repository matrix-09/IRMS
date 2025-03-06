import requests
import re
import hashlib
import json

# API Endpoint and Key
API_URL = "https://open-ai21.p.rapidapi.com/open-ai21.p.rapidapi.com"  # Replace with actual API URL
API_KEY = "71fdbe08f2msh32eb22d5522751ep186101jsn5a423cf3420b"  # Replace with your API key

# Cache dictionary to store fraud detection results
fraud_cache = {}

def hash_resume_text(resume_text):
    """Generate a unique hash for the resume text to use as a cache key."""
    return hashlib.md5(resume_text.encode()).hexdigest()

def evaluate_resumes_with_llm(resume_texts, job_description):
    """
    Uses LLM to evaluate multiple resumes at once.
    Caches results to avoid redundant API calls.
    """

    # Identify which resumes need evaluation
    resumes_to_check = []
    resume_hashes = {}

    for resume_text in resume_texts:
        resume_hash = hash_resume_text(resume_text)
        resume_hashes[resume_text] = resume_hash

        if resume_hash in fraud_cache:
            continue  # Skip if already cached
        resumes_to_check.append(resume_text)

    # If all resumes are cached, return results
    if not resumes_to_check:
        return {resume_text: fraud_cache[resume_hashes[resume_text]] for resume_text in resume_texts}

    # Construct LLM prompt for batch processing
    prompt = f"""
    You are an AI assistant helping HRs evaluate multiple resumes at once. Given a job description and resumes, perform:
    
    **1. Fraud Detection:** Identify if each resume contains:
    - Unrealistic job progressions or overlapping dates.
    - Suspicious formatting.
    - Fake experiences.

    **Job Description:**  
    {job_description}

    **Resumes:**  
    {json.dumps(resumes_to_check)}

    Provide output as a JSON dictionary where keys are resume indices (0, 1, 2...) and values are:
    {{
      "fraud_detected": true/false
    }}
    """

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "web_access": False
    }

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "open-ai21.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        output_json = response.json().get("result", "{}")

        # Parse LLM response
        fraud_results = json.loads(output_json)

        # Cache results
        for i, resume_text in enumerate(resumes_to_check):
            resume_hash = resume_hashes[resume_text]
            fraud_cache[resume_hash] = fraud_results.get(str(i), {"fraud_detected": False})

        # Return cached and new results
        return {resume_text: fraud_cache[resume_hashes[resume_text]] for resume_text in resume_texts}

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return {resume_text: {"fraud_detected": False} for resume_text in resume_texts}

    except Exception as e:
        print(f"Unexpected Error: {e}")
        return {resume_text: {"fraud_detected": False} for resume_text in resume_texts}
