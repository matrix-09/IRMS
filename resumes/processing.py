import pdfplumber
import re
import numpy as np
import faiss
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from resumes.llm_filter import evaluate_resumes_with_llm  # Import LLM fraud detection function

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file."""
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text.strip()

def extract_email(text):
    """Extracts the first email found in the resume text."""
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None

def preprocess_text(text):
    """Cleans and normalizes text."""
    if not isinstance(text, str):
        text = str(text)  # Convert non-string input to string
    
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text


def get_embedding(text):
    """Generates an embedding vector for the given text."""
    return model.encode(text, convert_to_numpy=True)


def calculate_similarity(resume_embeddings, job_embedding):
    """
    Computes cosine similarity scores between resumes and the job description.
    Returns scores in percentage (0-100).
    """
    resume_embeddings = np.array(resume_embeddings)  # Ensure numpy array
    job_embedding = job_embedding.reshape(1, -1)  # Reshape for compatibility

    scores = cosine_similarity(resume_embeddings, job_embedding).flatten() * 100  # Convert to percentage

    print(f"Cosine Similarity Scores: {scores}")  # Debugging Output

    return scores.tolist()

def match_resumes(resumes, threshold, job_description):
    """
    Matches resumes against a job description using cosine similarity.
    Uses batch processing for fraud detection to reduce LLM calls.
    """
    job_embedding = get_embedding(preprocess_text(job_description))
    resume_embeddings = [r["embedding"] for r in resumes]

    # Calculate similarity scores
    scores = calculate_similarity(resume_embeddings, job_embedding)

    # Shortlist resumes based on similarity score
    shortlisted_resumes = []
    shortlisted_texts = []

    for i, resume in enumerate(resumes):
        resume["score"] = round(scores[i], 2)  # Store rounded score

        if scores[i] >= threshold:  # Ensure correct thresholding
            shortlisted_resumes.append(resume)
            shortlisted_texts.append(resume["text"])  # Collect texts for batch fraud detection

    # Debugging: Check threshold filtering
    print(f"Threshold: {threshold}")
    print(f"Shortlisted Resume Scores: {[r['score'] for r in shortlisted_resumes]}")

    # Batch process fraud detection for shortlisted resumes
    fraud_results = evaluate_resumes_with_llm(shortlisted_texts, job_description)

    for resume in shortlisted_resumes:
        resume["is_fraudulent"] = fraud_results.get(resume["text"], {}).get("fraud_detected", False)

    return shortlisted_resumes
