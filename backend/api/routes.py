from fastapi import APIRouter, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
import json

from models.schemas import JobDescription, CandidateProfile, CandidateInsight, GeminiAnalysisResult
from services.resume_parser import parse_resume
from services.gemini_engine import analyze_resume_with_gemini
from services.excel_export import generate_excel_report
from core.config import settings
from core.realtime_engine import manager

router = APIRouter()

# In-memory storage for prototype
store_candidates: dict[str, CandidateProfile] = {}
store_analyses: dict[str, GeminiAnalysisResult] = {}
store_job: Optional[JobDescription] = None


@router.get("/test-models")
async def test_models():
    import google.generativeai as genai
    from core.config import settings
    genai.configure(api_key=settings.GEMINI_API_KEY)
    models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)
        return {"models": models}
    except Exception as e:
        return {"error": str(e)}



class JobRequest(BaseModel):
    title: str
    description: str


@router.post("/analyze-job")
async def analyze_job(job: JobRequest):
    global store_job, store_analyses
    
    # Check if job actually changed
    is_new_job = True
    if store_job:
        if store_job.title == job.title and store_job.description == job.description:
            is_new_job = False
            
    store_job = JobDescription(title=job.title, description=job.description)
    
    if is_new_job:
        # Clear previous analyses only when job actually changes
        store_analyses = {}
        
    return {"message": "Job description saved.", "job": store_job}


@router.post("/upload-resumes")
async def upload_resumes(files: List[UploadFile] = File(...)):
    if not store_job:
        raise HTTPException(status_code=400, detail="Set a job description first.")
    
    results = []
    for file in files:
        # 1. Parse the resume text
        profile = await parse_resume(file, settings.UPLOAD_DIR)
        store_candidates[profile.id] = profile
        
        # 2. Run Gemini analysis
        analysis = await analyze_resume_with_gemini(
            resume_text=profile.text_content,
            job_title=store_job.title,
            job_description=store_job.description
        )
        store_analyses[profile.id] = analysis
        
        # Update profile name from Gemini if available
        if analysis.candidate.full_name and analysis.candidate.full_name != "Not specified":
            profile.name = analysis.candidate.full_name
            store_candidates[profile.id] = profile
        
        results.append({
            "id": profile.id,
            "name": profile.name,
            "score": analysis.match.overall_score_percent,
            "fit_tier": analysis.match.fit_tier,
            "source": profile.source
        })
    
    # Broadcast updated rankings
    await broadcast_rankings()
    
    return {"message": f"Successfully analyzed {len(files)} resumes with Gemini.", "candidates": results}


@router.get("/rank-candidates")
async def get_rankings():
    if not store_job:
        raise HTTPException(status_code=400, detail="Job description not set.")
    
    rankings = []
    for cid, profile in store_candidates.items():
        analysis = store_analyses.get(cid)
        if analysis:
            rankings.append({
                "id": cid,
                "name": profile.name,
                "score": analysis.match.overall_score_percent,
                "fit_tier": analysis.match.fit_tier,
                "verdict": analysis.match.one_line_verdict,
                "source": profile.source,
                "recommended_action": analysis.recruiter_tools.recommended_action
            })
    
    rankings.sort(key=lambda x: x["score"], reverse=True)
    return rankings


@router.get("/candidate-insights/{candidate_id}")
async def get_candidate_insights(candidate_id: str):
    if candidate_id not in store_candidates:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    if candidate_id not in store_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found. Re-upload the resume.")
    
    profile = store_candidates[candidate_id]
    analysis = store_analyses[candidate_id]
    
    return CandidateInsight(profile=profile, analysis=analysis)


@router.get("/export-excel")
async def export_excel():
    """Export all candidate analyses to a formatted Excel report."""
    if not store_job:
        raise HTTPException(status_code=400, detail="No job description set.")
    if not store_analyses:
        raise HTTPException(status_code=400, detail="No candidates analyzed yet.")
    
    analyses_data = []
    for cid, analysis in store_analyses.items():
        profile = store_candidates.get(cid)
        analyses_data.append({
            "candidate_name": profile.name if profile else "Unknown",
            "analysis": analysis.model_dump()
        })
    
    filepath = generate_excel_report(
        analyses=analyses_data,
        job_title=store_job.title,
        job_description=store_job.description,
        output_dir=settings.UPLOAD_DIR
    )
    
    return FileResponse(
        path=filepath,
        filename=filepath.split("\\")[-1].split("/")[-1],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/re-analyze/{candidate_id}")
async def re_analyze_candidate(candidate_id: str):
    """Re-run Gemini analysis for a specific candidate."""
    if candidate_id not in store_candidates:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    if not store_job:
        raise HTTPException(status_code=400, detail="No job description set.")
    
    profile = store_candidates[candidate_id]
    analysis = await analyze_resume_with_gemini(
        resume_text=profile.text_content,
        job_title=store_job.title,
        job_description=store_job.description
    )
    store_analyses[candidate_id] = analysis
    
    if analysis.candidate.full_name and analysis.candidate.full_name != "Not specified":
        profile.name = analysis.candidate.full_name
        store_candidates[candidate_id] = profile
    
    await broadcast_rankings()
    
    return CandidateInsight(profile=profile, analysis=analysis)


async def broadcast_rankings():
    if store_job and store_candidates:
        rankings = []
        for cid, profile in store_candidates.items():
            analysis = store_analyses.get(cid)
            if analysis:
                rankings.append({
                    "id": profile.id,
                    "name": profile.name,
                    "score": analysis.match.overall_score_percent,
                    "fit_tier": analysis.match.fit_tier,
                    "source": profile.source
                })
        rankings.sort(key=lambda x: x["score"], reverse=True)
        await manager.broadcast({"type": "rankings_update", "data": rankings})


@router.websocket("/ws/rank-updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
