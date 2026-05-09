import json
import os
from dotenv import load_dotenv
from groq import Groq
from models.schemas import ParsedJD, ParsedResume, CandidateScore
from prompts.prompts import SCORER_PROMPT, clean_llm_response

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def score_candidate(jd: ParsedJD, resume: ParsedResume) -> CandidateScore:
    jd_summary = f"""
    Required Skills: {', '.join(jd.required_skills)}
    Preferred Skills: {', '.join(jd.preferred_skills)}
    Minimum Experience: {jd.min_experience_years} years
    Education: {jd.education_requirements}
    Responsibilities: {jd.responsibilities_summary}
    """

    candidate_profile = f"""
    Name: {resume.candidate_name}
    Skills: {', '.join(resume.skills)}
    Experience: {', '.join(resume.experience)}
    Education: {resume.education}
    Projects: {', '.join(resume.projects)}
    Certifications: {', '.join(resume.certifications)}
    """

    prompt = SCORER_PROMPT.format(
        jd_summary=jd_summary,
        candidate_profile=candidate_profile
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    raw = clean_llm_response(response.choices[0].message.content)

    data = json.loads(raw)

    weights = {
        "skills_match": 0.30,
        "experience_relevance": 0.25,
        "education_and_certs": 0.15,
        "project_portfolio": 0.20,
        "communication_quality": 0.10
    }

    total = sum(data[dim]["score"] * weight for dim, weight in weights.items())
    data["total_score"] = round(total, 2)
    data["recommendation"] = "HIRE" if total >= 6.0 else "NO HIRE"

    return CandidateScore(**data)