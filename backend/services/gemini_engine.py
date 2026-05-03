"""
Gemini-powered resume analysis engine.
Replaces the old NLP engine, ranking engine, and explainability modules
with a single Gemini API call that returns structured JSON.
"""

import json
import re
import google.generativeai as genai
from core.config import settings
from models.schemas import GeminiAnalysisResult

# Configure the Gemini client
genai.configure(api_key=settings.GEMINI_API_KEY)

ANALYSIS_PROMPT = """You are an expert resume parser and recruiter assistant. Given a candidate's resume text and a job description, extract and return a structured JSON object with the following fields. Every field must be populated — if information is not found, return "Not specified" rather than null. Be factual, concise, and do not infer beyond what the resume states.

Return this exact JSON structure (NO markdown, NO code fences, ONLY raw JSON):

{
  "candidate": {
    "full_name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin_url": "",
    "portfolio_url": ""
  },

  "match": {
    "overall_score_percent": 0,
    "fit_tier": "Strong | Possible | Weak",
    "one_line_verdict": "e.g. 2 years short of requirement, missing React and system design experience",
    "skills_score_percent": 0,
    "experience_score_percent": 0,
    "semantic_relevance_score_percent": 0
  },

  "experience": {
    "total_years": 0,
    "current_role": "",
    "current_company": "",
    "career_progression": "e.g. Junior → Mid → Senior over 4 years",
    "industry_background": "",
    "notable_companies": []
  },

  "education": {
    "highest_degree": "",
    "field_of_study": "",
    "institution": "",
    "graduation_year": ""
  },

  "skills": {
    "matched_required_skills": [],
    "missing_required_skills": [],
    "bonus_skills": [],
    "tech_stack_summary": "e.g. Python, Django, PostgreSQL, AWS"
  },

  "red_flags": {
    "employment_gaps": "None | e.g. 8-month gap in 2022",
    "job_hopping": "None | e.g. 4 jobs in 3 years",
    "role_mismatch": "None | e.g. Claims senior role but only 1 year experience",
    "other_concerns": ""
  },

  "recruiter_tools": {
    "strengths_summary": "2–3 sentence plain-English summary of why this candidate stands out",
    "weaknesses_summary": "2–3 sentence plain-English summary of key gaps",
    "suggested_interview_questions": [
      "Question targeting gap 1",
      "Question targeting gap 2",
      "Question targeting gap 3"
    ],
    "recommended_action": "Phone Screen | Technical Round | Reject | Hold for Future Role"
  }
}

Resume text:
\"\"\"
{resume_text}
\"\"\"

Job description:
\"\"\"
{job_description}
\"\"\"

IMPORTANT: Return ONLY the raw JSON object. Do not wrap it in markdown code fences or add any other text.
"""


def _clean_json_response(text: str) -> str:
    """Strip markdown code fences and extract pure JSON from Gemini response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
    return text.strip()


def _robust_json_parse(text: str) -> dict:
    """Attempts to parse JSON, and if it fails (e.g. cut off), tries to repair it."""
    cleaned = _clean_json_response(text)
    
    # 1. Try standard parse
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError as e:
        original_error = e

    # 2. Try fixing trailing commas
    no_commas = re.sub(r',\s*([\}\]])', r'\1', cleaned)
    try:
        return json.loads(no_commas, strict=False)
    except json.JSONDecodeError:
        pass

    # 3. Try fixing cut-off JSON by appending closing characters
    # We will try appending various combinations of ", ], and }
    suffixes = [
        '"', '}', ']', '"}', '"]}', '"]}]}', ']}', '}]}'
    ]
    
    # Try adding up to 5 closing braces
    for suffix in suffixes:
        for braces in range(5):
            attempt = no_commas + suffix + ('}' * braces)
            try:
                return json.loads(attempt, strict=False)
            except:
                pass
                
    # If all repairs fail, raise the original error so we can see it
    raise original_error


async def analyze_resume_with_gemini(resume_text: str, job_title: str, job_description: str) -> GeminiAnalysisResult:
    """
    Send resume text + job description to Gemini and get structured analysis back.
    Returns a validated GeminiAnalysisResult pydantic model.
    """
    full_jd = f"{job_title}\n\n{job_description}"
    
    prompt = ANALYSIS_PROMPT.replace("{resume_text}", resume_text).replace("{job_description}", full_jd)
    
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,  # Low temp for factual extraction
                max_output_tokens=8192,
                response_mime_type="application/json",
            )
        )
        
        raw_text = response.text
        try:
            parsed = _robust_json_parse(raw_text)
        except Exception as e:
            print(f"⚠️  JSON parse error: {e}")
            print(f"Raw Gemini response:\n{raw_text[:500]}")
            result = GeminiAnalysisResult()
            result.match.one_line_verdict = f"JSON Parse Error: {str(e)}"
            return result
        
        # Validate with pydantic
        result = GeminiAnalysisResult(**parsed)
        return result
        
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        import traceback
        traceback.print_exc()
        result = GeminiAnalysisResult()
        result.match.one_line_verdict = f"Error: {str(e)}"
        return result
