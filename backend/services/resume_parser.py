import os
import pdfplumber
import docx
from fastapi import UploadFile
from models.schemas import CandidateProfile
import uuid
import re


def _extract_name_from_text(text: str) -> str:
    """Simple heuristic: first non-empty line is usually the candidate name."""
    lines = text.strip().split('\n')
    for line in lines:
        cleaned = line.strip()
        # Skip empty lines and very long lines (likely paragraphs)
        if cleaned and len(cleaned) < 60 and not cleaned.startswith(('http', 'www', '+', '(')):
            # Check it's not an email or phone
            if '@' not in cleaned and not re.match(r'^[\d\s\-\+\(\)]+$', cleaned):
                return cleaned
    return "Unknown Candidate"


async def parse_resume(file: UploadFile, save_path: str) -> CandidateProfile:
    file_extension = os.path.splitext(file.filename)[1].lower()
    text = ""

    # Save temporarily to read it
    os.makedirs(save_path, exist_ok=True)
    temp_file_path = os.path.join(save_path, file.filename)
    with open(temp_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    if file_extension == '.pdf':
        with pdfplumber.open(temp_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif file_extension in ['.doc', '.docx']:
        doc = docx.Document(temp_file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    # Extract name with simple heuristic
    name = _extract_name_from_text(text)
    if name == "Unknown Candidate":
        name = file.filename.split('.')[0]  # Fallback to filename

    # Clean up text (preserve structure but remove excessive whitespace)
    text = "\n".join(line.strip() for line in text.split('\n') if line.strip())

    candidate_id = str(uuid.uuid4())
    
    return CandidateProfile(
        id=candidate_id,
        name=name,
        skills=[],  # Gemini will extract skills
        text_content=text,
        source="resume"
    )
