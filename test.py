from resumes.llm_filter import evaluate_resume_with_llm

resume_text = "java python c++"
job_description = "java python"

response = evaluate_resume_with_llm(resume_text, job_description)
print(response)