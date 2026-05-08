from pydantic import BaseModel, Field
from typing import List, Optional

class ParsedJD(BaseModel):
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience_years: int
    education_requirements: str
    responsibilities_summary: str

class ParsedResume(BaseModel):
    candidate_name: str
    skills: List[str]
    experience: List[str]
    education: str
    projects: List[str]
    certifications: List[str]

class DimensionScore(BaseModel):
    score: float = Field(ge=0, le=10)
    justification: str

class CandidateScore(BaseModel):
    candidate_name: str
    skills_match: DimensionScore
    experience_relevance: DimensionScore
    education_and_certs: DimensionScore
    project_portfolio: DimensionScore
    communication_quality: DimensionScore
    total_score: float
    recommendation: str

class OverrideLog(BaseModel):
    candidate_name: str
    dimension: str
    original_score: float
    new_score: float
    reason: str
    timestamp: str