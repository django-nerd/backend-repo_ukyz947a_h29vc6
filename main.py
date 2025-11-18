import os
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Clarity API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExplainRequest(BaseModel):
    text: str

class ExplainResponse(BaseModel):
    original: str
    explanation: str
    tips: Optional[List[str]] = None


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.post("/api/explain", response_model=ExplainResponse)
def explain_text(payload: ExplainRequest):
    """
    Lightweight heuristic explainer that simplifies jargon and shortens phrasing.
    This is a demo-friendly stand-in for a real LLM.
    """
    original = payload.text.strip()
    if not original:
        return ExplainResponse(original=payload.text, explanation="Please provide some text to explain.")

    # Common jargon -> simpler terms
    replacements = {
        "utilize": "use",
        "leverage": "use",
        "in the event that": "if",
        "notwithstanding": "despite",
        "commence": "start",
        "terminate": "end",
        "endeavor": "try",
        "subsequent": "next",
        "prior to": "before",
        "pursuant to": "under",
        "facilitate": "help",
        "endeavour": "try",
        "approximately": "about",
        "modality": "way",
        "methodology": "method",
        "mitigate": "reduce",
        "ameliorate": "improve",
        "expedite": "speed up",
        "commensurate": "matching",
        "endeavour": "try",
        "aforementioned": "mentioned above",
        "henceforth": "from now on",
        "therein": "in it",
        "thereof": "of it",
        "heretofore": "until now",
    }

    simplified = original
    for k, v in replacements.items():
        simplified = simplified.replace(k, v).replace(k.capitalize(), v.capitalize())

    # Shorten overly long sentences
    import re
    sentences = re.split(r"(?<=[.!?])\s+", simplified)
    clean_sentences = []
    tips: List[str] = []
    for s in sentences:
        s2 = s.strip()
        if not s2:
            continue
        # Remove filler phrases
        fillers = [
            "it should be noted that",
            "for the avoidance of doubt",
            "in order to",
            "as per",
            "with respect to",
        ]
        for f in fillers:
            s2 = s2.replace(f, "").replace(f.capitalize(), "")
        # Trim to ~24 words max while keeping meaning
        words = s2.split()
        if len(words) > 24:
            tips.append("Long sentence shortened for clarity")
            s2 = " ".join(words[:24]) + "…"
        clean_sentences.append(s2)

    explanation = " ".join(clean_sentences)
    if explanation == original:
        explanation = (
            "In simple terms: " + explanation
            if len(explanation.split()) < 30
            else "Here's the gist: " + explanation
        )

    return ExplainResponse(original=original, explanation=explanation, tips=tips or None)


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
