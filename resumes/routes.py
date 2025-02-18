from flask import Blueprint, request, jsonify
import numpy as np
import faiss
from resumes.processing import extract_text_from_pdf, preprocess_text, get_embedding, build_faiss_index,extract_email
from resumes.mailer import send_email  # Import mailer module
#from resumes.processing import extract_email_from_text  # ✅ Import email extractor

resume_bp = Blueprint("resumes", __name__)

resume_embeddings = []
resume_files = []
resume_texts = []
resume_emails = []  # ✅ Ensure this list is used

@resume_bp.route("/upload", methods=["POST"])
def upload_resumes():
    """Uploads resumes, extracts text & emails, and stores embeddings."""
    global resume_embeddings, resume_files, resume_texts, resume_emails
    resume_embeddings = []
    resume_files = []
    resume_texts = []
    resume_emails = []  # ✅ Ensure it's reset for every upload

    files = request.files.getlist("resumes")
    if not files:
        return jsonify({"error": "No resumes uploaded"}), 400

    for file in files:
        resume_text = extract_text_from_pdf(file)
        processed_text = preprocess_text(resume_text)
        embedding = get_embedding(processed_text)

        # ✅ Extract Email and ensure alignment
        candidate_email = extract_email(resume_text)
        resume_emails.append(candidate_email if candidate_email else "No Email Found")  

        resume_embeddings.append(embedding)
        resume_files.append(file.filename)
        resume_texts.append(resume_text)

    return jsonify({"message": "Resumes uploaded successfully", "total": len(resume_files)})


@resume_bp.route("/match", methods=["POST"])
def match_resume():
    """Matches a job description to uploaded resumes and sends emails to shortlisted candidates."""
    job_description = request.json.get("job_description")
    if not resume_embeddings:
        return jsonify({"error": "No resumes uploaded"}), 400

    jd_embedding = get_embedding(preprocess_text(job_description))
    index = build_faiss_index(resume_embeddings)
    if index is None:
        return jsonify({"error": "No index found"}), 400

    D, I = index.search(np.array([jd_embedding]), k=len(resume_files))  # Find top matches
    results = []
    shortlisted_emails = []  # ✅ Store shortlisted candidate emails

    for rank, i in enumerate(I[0]):
        if i >= len(resume_files):  # ✅ Ensure valid index
            continue

        score = round(float(1 / (1 + D[0][rank])), 2)
        candidate_email = resume_emails[i] if i < len(resume_emails) else "No Email Found"

        results.append({"resume": resume_files[i], "email": candidate_email, "score": score})

        if candidate_email != "No Email Found":  # ✅ Skip if no valid email
            shortlisted_emails.append(candidate_email)

    # ✅ Send email to shortlisted candidates
    if shortlisted_emails:
        subject = "Congratulations! You have been shortlisted"
        body = "Dear Candidate,\n\nYou have been shortlisted for the job. Please stay tuned for further updates.\n\nBest regards,\nHR Team"
        for email in shortlisted_emails:
            send_email(email, subject, body)

    return jsonify({"matches": results, "emails_sent": len(shortlisted_emails)})
