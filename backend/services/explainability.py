from models.schemas import CandidateProfile, JobDescription, ReasonCard, RankingScore
from services.nlp_engine import nlp_engine

# Score band thresholds
STRONG_THRESHOLD = 75
MODERATE_THRESHOLD = 50
WEAK_THRESHOLD = 30


def _get_score_band(score: float) -> str:
    """Return a human-readable label for a score."""
    if score >= STRONG_THRESHOLD:
        return "Strong"
    elif score >= MODERATE_THRESHOLD:
        return "Moderate"
    elif score >= WEAK_THRESHOLD:
        return "Weak"
    else:
        return "Very Weak"


def _get_recommendation(score: float) -> str:
    """Return a hiring recommendation based on overall score."""
    if score >= 80:
        return "Strongly Recommended"
    elif score >= 65:
        return "Recommended"
    elif score >= 50:
        return "Worth Considering"
    elif score >= 35:
        return "Below Average"
    else:
        return "Not Recommended"


def generate_insights(profile: CandidateProfile, job: JobDescription, score: RankingScore) -> ReasonCard:
    job_text = job.title + " " + job.description
    job_skills = set([s.lower() for s in nlp_engine.extract_skills(job_text)])
    profile_skills = set([s.lower() for s in profile.skills])

    missing_skills = sorted(list(job_skills - profile_skills))
    matched_skills = sorted(list(job_skills.intersection(profile_skills)))
    extra_skills = sorted(list(profile_skills - job_skills))

    # Extract education info for richer insights
    edu_info = nlp_engine.extract_education_keywords(profile.text_content)
    years_exp = nlp_engine.extract_experience_years(profile.text_content)

    # ---- Build Strengths ----
    strengths = []

    if matched_skills:
        if len(matched_skills) >= 3:
            strengths.append(f"Strong alignment with {len(matched_skills)} required skills: {', '.join(s.title() for s in matched_skills[:5])}")
        else:
            strengths.append(f"Matches required skills: {', '.join(s.title() for s in matched_skills)}")

    if score.skill_match_score >= 70:
        strengths.append(f"Excellent skill coverage — {score.skill_match_score}% of required skills found on resume.")
    elif score.skill_match_score >= 50:
        strengths.append(f"Decent skill coverage at {score.skill_match_score}%, covering core requirements.")

    if score.context_score >= 70:
        strengths.append("Resume content is highly relevant to the job description based on semantic analysis.")
    elif score.context_score >= 50:
        strengths.append("Resume shows moderate contextual relevance to the role.")

    if score.experience_score >= 70:
        if years_exp > 0:
            strengths.append(f"Strong experience profile with {int(years_exp)}+ years of relevant work history.")
        else:
            strengths.append("Experience section shows high relevance to the target role.")

    if edu_info["degrees"]:
        degree_str = ", ".join(edu_info["degrees"])
        if edu_info["fields"]:
            strengths.append(f"Holds a {degree_str} in {', '.join(edu_info['fields'][:2])}.")
        else:
            strengths.append(f"Educational background includes: {degree_str}.")

    if extra_skills and len(extra_skills) >= 3:
        strengths.append(f"Brings {len(extra_skills)} additional skills beyond requirements: {', '.join(s.title() for s in extra_skills[:4])}")

    # If still no strengths, provide at least one based on what we have
    if not strengths:
        if score.score >= 40:
            strengths.append("Resume shows some general relevance to the role, though specific skill matches are limited.")
        else:
            strengths.append("Resume was successfully parsed and analyzed.")

    # ---- Build Weaknesses ----
    weaknesses = []

    if missing_skills:
        if len(missing_skills) >= 3:
            weaknesses.append(f"Missing {len(missing_skills)} key required skills: {', '.join(s.title() for s in missing_skills[:5])}")
        else:
            weaknesses.append(f"Missing required skills: {', '.join(s.title() for s in missing_skills)}")

    if score.skill_match_score < 40:
        weaknesses.append(f"Low skill alignment at only {score.skill_match_score}% — most job requirements are not reflected in the resume.")
    elif score.skill_match_score < 60:
        weaknesses.append(f"Partial skill match ({score.skill_match_score}%) — some important requirements are missing.")

    if score.context_score < 40:
        weaknesses.append("Resume content has low semantic similarity to the job description — the candidate's background may be in a different domain.")
    elif score.context_score < 55:
        weaknesses.append("Moderate-to-low contextual relevance — candidate's experience may not directly transfer to this role.")

    if score.experience_score < 40:
        if years_exp == 0:
            weaknesses.append("No explicit years of experience detected — may be a recent graduate or career changer.")
        else:
            weaknesses.append(f"Experience relevance is low despite {int(years_exp)} years mentioned — may be in a different field.")

    if score.education_score < 40:
        weaknesses.append("No strong educational credentials detected for this role.")

    if not weaknesses:
        if score.score < 80:
            weaknesses.append("While the candidate is generally qualified, there may be room for stronger alignment in specific areas.")

    # ---- Build Explainability Text ----
    recommendation = _get_recommendation(score.score)
    overall_band = _get_score_band(score.score)

    parts = [f"Overall Match: {score.score}% ({overall_band}) — Recommendation: {recommendation}."]

    # Score breakdown narrative
    dimensions = [
        ("Skills", score.skill_match_score),
        ("Experience", score.experience_score),
        ("Semantic Relevance", score.context_score),
        ("Education", score.education_score),
    ]
    best_dim = max(dimensions, key=lambda x: x[1])
    worst_dim = min(dimensions, key=lambda x: x[1])

    parts.append(f"Strongest dimension: {best_dim[0]} at {best_dim[1]}%. Weakest: {worst_dim[0]} at {worst_dim[1]}%.")

    if matched_skills:
        parts.append(f"Matched {len(matched_skills)} out of {len(job_skills)} required skills ({', '.join(s.title() for s in matched_skills[:4])}).")

    if missing_skills:
        parts.append(f"Key gaps: {', '.join(s.title() for s in missing_skills[:3])}.")

    if score.score >= 75:
        parts.append("This candidate shows strong potential and should be prioritized for interview.")
    elif score.score >= 50:
        parts.append("Consider this candidate if the missing skills can be learned on the job or if other candidates are limited.")
    else:
        if missing_skills:
            parts.append(f"Consider asking specifically about experience with {missing_skills[0].title()} during screening.")

    explainability_text = " ".join(parts)

    return ReasonCard(
        strengths=strengths,
        weaknesses=weaknesses,
        missing_skills=[s.title() for s in missing_skills],
        match_percentage=score.score,
        explainability_text=explainability_text
    )
