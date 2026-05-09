import json
import os
from datetime import datetime
from models.schemas import CandidateScore, OverrideLog
os.makedirs("logs", exist_ok=True)

OVERRIDE_LOG_PATH = "logs/overrides.json"

DIMENSION_WEIGHTS = {
    "skills_match": 0.30,
    "experience_relevance": 0.25,
    "education_and_certs": 0.15,
    "project_portfolio": 0.20,
    "communication_quality": 0.10
}

def apply_override(
    candidate: CandidateScore,
    dimension: str,
    new_score: float,
    reason: str
) -> CandidateScore:
    original_score = getattr(candidate, dimension).score

    # Apply new score
    getattr(candidate, dimension).score = new_score
    getattr(candidate, dimension).justification += f" [OVERRIDDEN: {reason}]"

    # Recalculate total
    total = sum(
        getattr(candidate, dim).score * weight
        for dim, weight in DIMENSION_WEIGHTS.items()
    )
    candidate.total_score = round(total, 2)
    candidate.recommendation = "HIRE" if total >= 6.0 else "NO HIRE"

    # Log the override
    log = OverrideLog(
        candidate_name=candidate.candidate_name,
        dimension=dimension,
        original_score=original_score,
        new_score=new_score,
        reason=reason,
        timestamp=datetime.now().isoformat()
    )

    logs = []
    if os.path.exists(OVERRIDE_LOG_PATH):
        with open(OVERRIDE_LOG_PATH, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append(log.model_dump())

    with open(OVERRIDE_LOG_PATH, "w") as f:
        json.dump(logs, f, indent=2)

    return candidate