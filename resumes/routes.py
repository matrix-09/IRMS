from flask import Blueprint, request, jsonify
import numpy as np
import faiss
import logging
from resumes.processing import (
    extract_text_from_pdf, preprocess_text, get_embedding, 
    extract_email, filter_resumes_with_llm
)
from resumes.mailer import send_email

resume_bp = Blueprint("resumes", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

@resume_bp.errorhandler(500)
def internal_error(error):
    """Handles internal server errors and ensures a JSON response."""
    logging.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error occurred"}), 500

@resume_bp.route("/upload_and_match", methods=["POST"])
def upload_and_match():
    """Uploads resumes, processes job description, matches candidates, and sends emails."""
    try:
        # Get resumes and job description from request
        files = request.files.getlist("resumes")
        job_description = request.form.get("job_description")

        if not files or not job_description:
            return jsonify({"error": "Both resumes and job description are required"}), 400

        # Process resumes
        resumes = []
        for file in files:
            if not file.filename.endswith(".pdf"):
                return jsonify({"error": f"Invalid file format: {file.filename}. Only PDFs are allowed."}), 400

            resume_text = extract_text_from_pdf(file)
            processed_text = preprocess_text(resume_text)
            embedding = get_embedding(processed_text)
            candidate_email = extract_email(resume_text)

            resumes.append({
                "filename": file.filename,
                "text": resume_text,
                "email": candidate_email if candidate_email else "No Email Found",
                "embedding": embedding
            })

        if not resumes:
            return jsonify({"error": "No valid resumes were processed"}), 400

        # Filter resumes using LLM
        shortlisted_resumes = filter_resumes_with_llm(resumes, job_description, threshold=50)

        # Prepare response data
        results = []
        shortlisted_emails = []

        for candidate in shortlisted_resumes:
            results.append({
                "resume": candidate["filename"],
                "email": candidate["email"],
                "score": candidate["score"],
                "reason": candidate["reason"]
            })

            if candidate["email"] != "No Email Found":
                shortlisted_emails.append(candidate["email"])

        # Send emails to shortlisted candidates
        if shortlisted_emails:
            subject = "Congratulations! You have been shortlisted"
            body = "Dear Candidate,\n\nYou have been shortlisted for the job. Please stay tuned for further updates.\n\nBest regards,\nHR Team"
            for email in shortlisted_emails:
                send_email(email, subject, body)

        return jsonify({
            "message": "Resumes processed and matched successfully",
            "matches": results,
            "emails_sent": len(shortlisted_emails)
        })

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500
