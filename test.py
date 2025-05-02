import asyncio
from resumes.llm_filter import generate_llm_feedback  # Import LLM-based feedback function

# Define resume texts and job description
resume_texts = [
    "Mahideep, JAVA, SQL, Problem solving",
    "Nagsh, UI/UX, LOGO design"
]

job_description = """
A comprehensive position to build and solve new problems in the field of AI and ML.
The candidate should have a strong background in JAVA, SQL, and Problem solving.
"""

# Call the async function properly
res = asyncio.run(generate_llm_feedback(resume_texts, job_description))

# Print results
print(res)
