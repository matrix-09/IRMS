from flask import Blueprint, request, jsonify
from resumes.llm_filter import generate_llm_feedback
import logging
from resumes.processing import (
    extract_text_from_pdf, preprocess_text, get_embedding, 
    extract_email, match_resumes
)
from resumes.mailer import send_email

resume_bp = Blueprint("resumes", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
import asyncio
from resumes.llm_filter import generate_llm_feedback  # Import LLM-based feedback function

@resume_bp.route("/upload_and_match", methods=["POST"])
def upload_and_match():
    """Uploads resumes, processes job description, matches candidates, and sends emails."""
    try:
        files = request.files.getlist("resumes")
        job_description = request.form.get("job_description")
        threshold = request.form.get("strictness")

        try:
            threshold = float(threshold)
        except ValueError:
            return jsonify({"error": "Invalid threshold value. Must be a number."}), 400

        if not files or not job_description:
            return jsonify({"error": "Both resumes and job description are required"}), 400

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

        # Match resumes
        shortlisted_resumes = match_resumes(resumes, threshold, job_description)
        #shortlisted_resumes = match_resumes(resumes, threshold, job_description)

        # Initialize all necessary variables
        matches = []
        n=0
        shortlisted_count = 0
        non_shortlisted_count = 0
        emails_sent = 0
        missing_emails = 0
        shortlisted_emails = []
        non_shortlisted_emails = []

        for candidate in resumes:
            is_shortlisted = any(sc["filename"] == candidate["filename"] for sc in shortlisted_resumes)
            score = next((sc.get("score", 0) for sc in shortlisted_resumes if sc["filename"] == candidate["filename"]), 0)
            
            if is_shortlisted:
                shortlisted_count += 1
            else:
                non_shortlisted_count += 1

            if candidate["email"] == "No Email Found":
                missing_emails += 1
            n+=1
            matches.append({
                "resume": candidate["filename"],
                "email": candidate["email"],
                "score": score,
                "status": "shortlisted" if is_shortlisted else "not_shortlisted"
            })
        # Prepare results with status information

            if candidate["email"] != "No Email Found":
                if is_shortlisted:
                    shortlisted_emails.append(candidate["email"])
                else:
                    non_shortlisted_emails.append(candidate["email"])

        # Send emails to shortlisted candidates
        if shortlisted_emails:
            emails_sent += len(shortlisted_emails)
            subject = "Congratulations! You have been shortlisted"
            body = "Dear Candidate,\n\nYou have been shortlisted. Further updates will be shared soon.\n\nBest regards,\nHR Team"
            for email in shortlisted_emails:
                send_email(email, subject, body)

        # Get LLM-generated feedback for non-shortlisted candidates
        if non_shortlisted_emails:
            emails_sent += len(non_shortlisted_emails)
            non_shortlisted_texts = [c["text"] for c in resumes if c["email"] in non_shortlisted_emails]
            feedback_results = asyncio.run(generate_llm_feedback(non_shortlisted_texts, job_description))
            text_string = "Thank you for applying..."
            
            for i, candidate in enumerate([c for c in resumes if c["email"] in non_shortlisted_emails]):
                feedback_subject = "Your Application Status"
                feedback_body = f"Dear Candidate,\n{text_string}\n\nFeedback:\n{feedback_results.get(i, 'No feedback available')}\n\nBest regards,\nHR Team"
                send_email(candidate["email"], feedback_subject, feedback_body)

        return jsonify({
            "message": "Resumes processed successfully",
            "matches": matches,  # All candidates with their status
            "total_candidates": n,
            "shortlisted_count": shortlisted_count,
            "non_shortlisted_count": non_shortlisted_count,
            "emails_sent": emails_sent,
            "missing_emails": missing_emails,
            "success": True  # Explicit success flag
        })

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500