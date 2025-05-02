import requests
import re
import hashlib
import json
import aiohttp
# API Endpoint and Key
API_URL = "https://open-ai21.p.rapidapi.com/conversationllama"  # Replace with actual API URL
API_KEY = "a991133e21mshc05b33ebc46179fp1b4923jsn421d38661c82"  # Replace with your API key

def hash_resume_text(resume_text):
    """Generate a unique hash for the resume text to use as a cache key."""
    return hashlib.md5(resume_text.encode()).hexdigest()

async def fetch_llm_feedback(session, resumes_to_check, job_description):
    """Fetch personalized feedback for resumes using LLM."""
    
    prompt = f"""
    You are an AI HR assistant. Your job is to analyze each resume and provide 
    **personalized constructive feedback** based on the job description.

    ### **Job Description:**  
    {job_description}

    ### **Resumes to Analyze (JSON Format):**  
    {json.dumps(resumes_to_check)}

    ### **Expected Output (JSON Dictionary):**  
    Return structured JSON feedback like this:
    ```json
    {{
        "0": "Your resume is strong but lacks AI/ML experience. Consider adding projects in this area.",
        "1": "Your resume does not match the job description. Consider learning JAVA, SQL."
        and so on for each resume.
    }}
    ```
    
    **Ensure the response is in JSON format and does not contain 'No feedback available'.**
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

    async with session.post(API_URL, json=payload, headers=headers) as response:
        api_response = await response.json()

        # Debug: Log API response
        print("API Response:", json.dumps(api_response, indent=2))

        return api_response  


async def generate_llm_feedback(resume_texts, job_description):
    """Generate structured feedback from LLM response."""

    async with aiohttp.ClientSession() as session:
        response_json = await fetch_llm_feedback(session, resume_texts, job_description)

    # Extract LLM content safely
    try:
        raw_content = response_json["result"]  # << Correct key: "result"

        # Remove triple backticks and parse JSON inside
        json_match = re.search(r"```json\s*(\{.*\})\s*```", raw_content, re.DOTALL)
        clean_json_str = json_match.group(1) if json_match else raw_content

        # Parse JSON safely
        feedback_dict = json.loads(clean_json_str)

    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        return {i: "Feedback unavailable" for i in range(len(resume_texts))}

    return {i: feedback_dict.get(str(i), "Feedback unavailable") for i in range(len(resume_texts))}
  # Return raw API output for further processing
