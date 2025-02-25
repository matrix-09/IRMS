import requests
import re
import os

# API Endpoint and Key
API_URL = "https://open-ai21.p.rapidapi.com/conversationllama"  # Replace with actual API URL
API_KEY = "a991133e21mshc05b33ebc46179fp1b4923jsn421d38661c82"  # Replace with your API key

def evaluate_resume_with_llm(resume_text, job_description):
    """
    Uses an LLM to evaluate how well a resume matches a job description.
    Returns a score (0-100) and a short reason.
    """

    prompt = f"""
    You are an AI assistant helping HRs evaluate resumes. Given the job description and resume, score the candidate from 0 to 100 based on:
    1. **Skill match** (40%) - Does the candidate have the required skills?
    2. **Experience relevance** (30%) - Has the candidate worked in similar roles?
    3. **Education fit** (20%) - Does the degree match job requirements?
    4. **Certifications/Projects** (10%) - Relevant courses or projects?

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Provide output in this format:
    SCORE: (0-100)
    REASON: (Explain skill match, experience, education, and projects.)
    """

    payload = {
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "web_access": False
    }


    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "open-ai21.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        #response.raise_for_status()  # Raises HTTP errors (e.g., 400, 500)
        
        output_text = response.json().get("result")
        

        # Extract score and reason
        score_match = re.search(r"(?i)score[:\s-]+(\d+)", output_text)
        reason_match = re.search(r"REASON:\s*(.+)", output_text)

        score = int(score_match.group(1)) if score_match else 0
        reason = reason_match.group(1).strip() if reason_match else "No reason provided"

        return score, reason

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return 0, "Error in LLM response"

    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 0, "Unexpected error occurred"

