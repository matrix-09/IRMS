from flask import Blueprint, request, jsonify
import logging
from resumes.processing import (
    extract_text_from_pdf, preprocess_text, get_embedding, 
    extract_email, match_resumes
)
from resumes.mailer import send_email

resume_bp = Blueprint("resumes", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

@resume_bp.route("/upload_and_match", methods=["POST"])
def upload_and_match():
    """Uploads resumes, processes job description, matches candidates, and sends emails."""
    try:
        # Get resumes and job description from request
        files = request.files.getlist("resumes")
        job_description = request.form.get("job_description")
        threshold = request.form.get("strictness")
        
        # Convert threshold to float safely
        try:
            threshold = float(threshold)
        except ValueError:
            return jsonify({"error": "Invalid threshold value. Must be a number."}), 400

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

        # Match resumes with job description
        shortlisted_resumes = match_resumes(resumes, threshold, job_description)

        # Prepare response
        results = []
        shortlisted_emails = []

        for candidate in shortlisted_resumes:
            results.append({
                "resume": candidate["filename"],
                "email": candidate["email"],
                "score": candidate["score"],
                "is_fraudulent": candidate["is_fraudulent"]
            })

            if candidate["email"] != "No Email Found" and not candidate["is_fraudulent"]:
                shortlisted_emails.append(candidate["email"])

        # Send emails to shortlisted, non-fraudulent candidates
        if shortlisted_emails:
            subject = "Congratulations! You have been shortlisted"
            body = "Dear Candidate,\n\nYou have been shortlisted. Further updates will be shared soon.\n\nBest regards,\nHR Team"
            for email in shortlisted_emails:
                send_email(email, subject, body)

        return jsonify({
            "message": "Resumes processed successfully",
            "matches": results,
            "emails_sent": len(shortlisted_emails)
        })

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500