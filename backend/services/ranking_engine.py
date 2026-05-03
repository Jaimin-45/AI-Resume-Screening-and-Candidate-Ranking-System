from models.schemas import CandidateProfile, JobDescription, RankingScore
from services.nlp_engine import nlp_engine
from core.config import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
    except:
        return 0.0

def calculate_education_score(profile: CandidateProfile, job: JobDescription) -> float:
    """Score education based on degree level and field relevance."""
    edu_info = nlp_engine.extract_education_keywords(profile.text_content)
    job_text = job.title + " " + job.description
    job_edu = nlp_engine.extract_education_keywords(job_text)

    score = 0.0

    # Degree level scoring
    degree_weights = {
        "PhD": 1.0,
        "Master's": 0.85,
        "Bachelor's": 0.7,
        "Associate's": 0.5,
        "Diploma": 0.4,
        "Certification": 0.35,
    }

    if edu_info["degrees"]:
        best_degree_score = max(degree_weights.get(d, 0.3) for d in edu_info["degrees"])
        score += best_degree_score * 0.6
    else:
        score += 0.2  # Some base score even without detected degree

    # Field relevance — check if candidate's field matches job context
    if edu_info["fields"]:
        field_text = " ".join(edu_info["fields"])
        field_relevance = nlp_engine.calculate_similarity(field_text, job_text)
        score += field_relevance * 0.3
    else:
        score += 0.1

    # Institution mentioned gives a small bonus
    if edu_info["institutions_mentioned"]:
        score += 0.1

    return min(1.0, score)

def calculate_experience_score(profile: CandidateProfile, job: JobDescription) -> float:
    """Score experience using semantic similarity and detected years."""
    job_text = job.title + " " + job.description

    # Semantic similarity of experience content
    semantic_score = nlp_engine.calculate_similarity(profile.text_content, job_text)

    # Years of experience bonus
    years = nlp_engine.extract_experience_years(profile.text_content)
    if years >= 10:
        years_bonus = 1.0
    elif years >= 5:
        years_bonus = 0.8
    elif years >= 3:
        years_bonus = 0.6
    elif years >= 1:
        years_bonus = 0.4
    else:
        years_bonus = 0.2  # Fresh graduate / no years detected

    # Combine: 60% semantic relevance, 40% years
    score = (semantic_score * 0.6) + (years_bonus * 0.4)
    return min(1.0, score)


def rank_candidate(profile: CandidateProfile, job: JobDescription) -> RankingScore:
    job_text = job.title + " " + job.description

    # 1. Semantic Similarity (Context) - Sentence Transformers
    semantic_score = nlp_engine.calculate_similarity(profile.text_content, job_text)

    # 2. TF-IDF Similarity (Keyword Match)
    tfidf_score = calculate_tfidf_similarity(profile.text_content, job_text)

    # Hybrid text similarity
    context_score = (semantic_score * 0.7) + (tfidf_score * 0.3)

    # 3. Skills Match
    job_skills = set([s.lower() for s in nlp_engine.extract_skills(job_text)])
    profile_skills = set([s.lower() for s in profile.skills])

    if len(job_skills) > 0:
        matched_skills = job_skills.intersection(profile_skills)
        skill_score = len(matched_skills) / len(job_skills)
    else:
        skill_score = 0.5 # Default if no skills extracted from JD

    # 4. Education Score
    education_score = calculate_education_score(profile, job)

    # 5. Experience Score
    experience_score = calculate_experience_score(profile, job)

    final_score = (
        (skill_score * settings.WEIGHT_SKILLS) +
        (experience_score * settings.WEIGHT_EXPERIENCE) +
        (context_score * settings.WEIGHT_CONTEXT) +
        (education_score * settings.WEIGHT_EDUCATION)
    )

    # Normalize final score to percentage
    final_score = round(final_score * 100, 2)

    return RankingScore(
        candidate_id=profile.id,
        score=final_score,
        skill_match_score=round(skill_score * 100, 2),
        experience_score=round(experience_score * 100, 2),
        context_score=round(context_score * 100, 2),
        education_score=round(education_score * 100, 2)
    )
