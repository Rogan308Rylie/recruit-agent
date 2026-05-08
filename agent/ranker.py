from typing import List
from models.schemas import CandidateScore

def rank_candidates(scores: List[CandidateScore]) -> List[CandidateScore]:
    return sorted(scores, key=lambda x: x.total_score, reverse=True)