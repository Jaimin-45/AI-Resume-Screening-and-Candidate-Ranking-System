from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class JobDescription(BaseModel):
    title: str
    description: str


class CandidateProfile(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    text_content: str
    source: str = "resume"  # 'resume' or 'linkedin'


# --- Gemini-powered structured analysis output ---

class CandidateInfo(BaseModel):
    full_name: str = "Not specified"
    email: str = "Not specified"
    phone: str = "Not specified"
    location: str = "Not specified"
    linkedin_url: str = "Not specified"
    portfolio_url: str = "Not specified"


class MatchScores(BaseModel):
    overall_score_percent: float = 0
    fit_tier: str = "Weak"  # Strong | Possible | Weak
    one_line_verdict: str = ""
    skills_score_percent: float = 0
    experience_score_percent: float = 0
    semantic_relevance_score_percent: float = 0


class ExperienceInfo(BaseModel):
    total_years: float = 0
    current_role: str = "Not specified"
    current_company: str = "Not specified"
    career_progression: str = "Not specified"
    industry_background: str = "Not specified"
    notable_companies: List[str] = []


class EducationInfo(BaseModel):
    highest_degree: str = "Not specified"
    field_of_study: str = "Not specified"
    institution: str = "Not specified"
    graduation_year: str = "Not specified"


class SkillsAnalysis(BaseModel):
    matched_required_skills: List[str] = []
    missing_required_skills: List[str] = []
    bonus_skills: List[str] = []
    tech_stack_summary: str = "Not specified"


class RedFlags(BaseModel):
    employment_gaps: str = "None"
    job_hopping: str = "None"
    role_mismatch: str = "None"
    other_concerns: str = ""


class RecruiterTools(BaseModel):
    strengths_summary: str = ""
    weaknesses_summary: str = ""
    suggested_interview_questions: List[str] = []
    recommended_action: str = "Hold for Future Role"


class GeminiAnalysisResult(BaseModel):
    candidate: CandidateInfo = CandidateInfo()
    match: MatchScores = MatchScores()
    experience: ExperienceInfo = ExperienceInfo()
    education: EducationInfo = EducationInfo()
    skills: SkillsAnalysis = SkillsAnalysis()
    red_flags: RedFlags = RedFlags()
    recruiter_tools: RecruiterTools = RecruiterTools()


class CandidateInsight(BaseModel):
    profile: CandidateProfile
    analysis: GeminiAnalysisResult
