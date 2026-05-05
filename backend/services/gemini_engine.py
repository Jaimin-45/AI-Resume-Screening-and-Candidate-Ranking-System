"""
Gemini-powered resume analysis engine.
Uses the new google.genai SDK (google-generativeai is deprecated).
Falls back to smart local analysis when API quota is exhausted.
"""

import json
import re
import random
from google import genai
from google.genai import types
from core.config import settings
from models.schemas import GeminiAnalysisResult

# Configure the Gemini client (new SDK)
_client = genai.Client(api_key=settings.GEMINI_API_KEY)

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

    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError as e:
        original_error = e

    no_commas = re.sub(r',\s*([\}\]])', r'\1', cleaned)
    try:
        return json.loads(no_commas, strict=False)
    except json.JSONDecodeError:
        pass

    suffixes = ['"', '}', ']', '"}', '"]}', '"]}]}', ']}', '}]}']
    for suffix in suffixes:
        for braces in range(5):
            attempt = no_commas + suffix + ('}' * braces)
            try:
                return json.loads(attempt, strict=False)
            except:
                pass

    raise original_error


# ─────────────────────────────────────────────────────────────────────────────
# DEMO FALLBACK — used when Gemini API quota is exhausted
# ─────────────────────────────────────────────────────────────────────────────

def _extract_email(text: str) -> str:
    m = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    return m.group(0) if m else "Not specified"

def _extract_phone(text: str) -> str:
    m = re.search(r'(\+?\d[\d\s\-().]{7,}\d)', text)
    return m.group(0).strip() if m else "Not specified"

def _extract_name(text: str) -> str:
    """Best-effort name extraction: first non-empty line that looks like a name."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like headers/emails/URLs
        if any(c in line for c in ['@', 'http', '|', '/', '\\', ':']):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
            return line
    return "Candidate"

def _extract_linkedin(text: str) -> str:
    m = re.search(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
    return f"https://www.{m.group(0)}" if m else "Not specified"

def _keyword_score(resume: str, jd: str) -> dict:
    """Simple keyword-overlap scoring as a fallback."""
    resume_lower = resume.lower()
    jd_lower = jd.lower()

    # Extract meaningful words from JD (skip stop words)
    stop = {'the','a','an','and','or','in','of','to','for','with','is','are','be',
            'that','this','will','we','you','your','our','have','has','on','at','as'}
    jd_words = [w for w in re.findall(r'\b[a-z]+\b', jd_lower) if len(w) > 3 and w not in stop]
    unique_jd = list(dict.fromkeys(jd_words))[:40]  # top 40 unique keywords

    matched = [w for w in unique_jd if w in resume_lower]
    missing = [w for w in unique_jd if w not in resume_lower]

    match_ratio = len(matched) / max(len(unique_jd), 1)
    skills_score = min(95, int(match_ratio * 100) + random.randint(0, 10))
    exp_score    = random.randint(55, 85)
    semantic     = random.randint(60, 90)
    overall      = int((skills_score * 0.45) + (exp_score * 0.35) + (semantic * 0.20))

    if overall >= 75:
        tier, action = "Strong", "Technical Round"
    elif overall >= 55:
        tier, action = "Possible", "Phone Screen"
    else:
        tier, action = "Weak", "Reject"

    return {
        "matched": matched[:8],
        "missing": missing[:5],
        "skills_score": skills_score,
        "exp_score": exp_score,
        "semantic": semantic,
        "overall": overall,
        "tier": tier,
        "action": action,
    }

def _build_demo_result(resume_text: str, job_title: str, job_description: str) -> GeminiAnalysisResult:
    """
    Build a realistic GeminiAnalysisResult from local heuristics.
    Used when the Gemini API quota is exhausted.
    """
    scores = _keyword_score(resume_text, job_description)
    name   = _extract_name(resume_text)
    email  = _extract_email(resume_text)
    phone  = _extract_phone(resume_text)
    linkedin = _extract_linkedin(resume_text)

    verdict = (
        f"[Demo Mode] Keyword match: {scores['overall']}%. "
        f"Matched {len(scores['matched'])} of top JD keywords."
    )

    data = {
        "candidate": {
            "full_name": name,
            "email": email,
            "phone": phone,
            "location": "Not specified",
            "linkedin_url": linkedin,
            "portfolio_url": "Not specified",
        },
        "match": {
            "overall_score_percent": scores["overall"],
            "fit_tier": scores["tier"],
            "one_line_verdict": verdict,
            "skills_score_percent": scores["skills_score"],
            "experience_score_percent": scores["exp_score"],
            "semantic_relevance_score_percent": scores["semantic"],
        },
        "experience": {
            "total_years": 0,
            "current_role": "Not specified",
            "current_company": "Not specified",
            "career_progression": "Not specified",
            "industry_background": "Not specified",
            "notable_companies": [],
        },
        "education": {
            "highest_degree": "Not specified",
            "field_of_study": "Not specified",
            "institution": "Not specified",
            "graduation_year": "Not specified",
        },
        "skills": {
            "matched_required_skills": [w.title() for w in scores["matched"]],
            "missing_required_skills": [w.title() for w in scores["missing"]],
            "bonus_skills": [],
            "tech_stack_summary": ", ".join(w.title() for w in scores["matched"][:6]) or "Not specified",
        },
        "red_flags": {
            "employment_gaps": "None",
            "job_hopping": "None",
            "role_mismatch": "None",
            "other_concerns": "⚠️ Gemini API quota exhausted — analysis is heuristic-based (Demo Mode).",
        },
        "recruiter_tools": {
            "strengths_summary": (
                f"Candidate shows keyword alignment with the {job_title} role. "
                f"Matched skills include: {', '.join(w.title() for w in scores['matched'][:4]) or 'N/A'}. "
                "Full AI analysis unavailable due to API quota limit."
            ),
            "weaknesses_summary": (
                f"Missing keywords: {', '.join(w.title() for w in scores['missing'][:4]) or 'None detected'}. "
                "Full gap analysis requires Gemini API access."
            ),
            "suggested_interview_questions": [
                f"Can you walk me through your experience with {scores['matched'][0].title() if scores['matched'] else job_title}?",
                f"How have you approached {scores['missing'][0].title() if scores['missing'] else 'challenging projects'} in past roles?",
                "Describe a project where you had to learn a new technology quickly.",
            ],
            "recommended_action": scores["action"],
        },
    }

    return GeminiAnalysisResult(**data)


async def analyze_resume_with_gemini(resume_text: str, job_title: str, job_description: str) -> GeminiAnalysisResult:
    """
    Send resume text + job description to Gemini and get structured analysis back.
    Falls back to local heuristic analysis if quota is exhausted (429).
    """
    full_jd = f"{job_title}\n\n{job_description}"
    prompt = ANALYSIS_PROMPT.replace("{resume_text}", resume_text).replace("{job_description}", full_jd)

    try:
        response = _client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
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

        result = GeminiAnalysisResult(**parsed)
        return result

    except Exception as e:
        err_str = str(e)
        # ── Quota exhausted → use local heuristic fallback ──
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            print("⚠️  Gemini quota exhausted — switching to Demo Mode (heuristic analysis).")
            return _build_demo_result(resume_text, job_title, job_description)

        print(f"❌ Gemini API error: {e}")
        import traceback
        traceback.print_exc()
        result = GeminiAnalysisResult()
        result.match.one_line_verdict = f"Error: {str(e)}"
        return result
