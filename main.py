"""
FastAPI main application for elderly health triage system
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from database import Database
from agents.orchestrator import Orchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Elderly Health Triage System",
    description="AI-powered health triage for elderly care",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Initialize Services
# ============================================================================

# Initialize Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not set in .env")

genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel('gemini-pro')

# Initialize Database
db_config = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", ""),
    'dbname': os.getenv("DB_NAME", "elderly_care"),
    'port': int(os.getenv("DB_PORT", "5432"))
}

try:
    db = Database(**db_config)
    logger.info("Database connected successfully")
except Exception as e:
    logger.error(f"Failed to connect to database: {str(e)}")
    logger.info("NOTE: Make sure AlloyDB is running and credentials are correct")
    db = None

# Initialize Orchestrator
orchestrator = Orchestrator(db, gemini_model) if db else None

# ============================================================================
# Request/Response Models
# ============================================================================

class SymptomReport(BaseModel):
    """User reports symptoms"""
    user_id: str
    symptoms: str
    additional_info: Optional[str] = None


class TriageResponse(BaseModel):
    """Triage assessment response"""
    user_id: str
    severity_level: str
    guidance: str
    actions: List[str]
    next_steps: str
    emergency_options: Optional[dict] = None
    assessment_reasoning: str


class UserProfile(BaseModel):
    """User profile response"""
    user_id: str
    name: str
    age: int
    gender: str
    conditions: List[str]
    medications: List[dict]
    allergies: List[dict]
    emergency_contacts: List[dict]


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    database_connected: bool
    gemini_available: bool


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database_connected": db is not None,
        "gemini_available": gemini_model is not None
    }


@app.post("/api/triage", response_model=TriageResponse)
async def submit_symptoms(report: SymptomReport, background_tasks: BackgroundTasks):
    """
    Main triage endpoint
    User reports symptoms, system assesses severity and returns guidance
    """
    
    if not orchestrator:
        raise HTTPException(status_code=500, detail="System not properly initialized")

    try:
        logger.info(f"Symptom report from user {report.user_id}")
        logger.info(f"Symptoms: {report.symptoms}")

        # Run orchestrator
        result = await orchestrator.process_symptom_report(
            user_id=report.user_id,
            symptom_input=report.symptoms
        )

        # Prepare response
        response = TriageResponse(
            user_id=result['user_id'],
            severity_level=result['severity_level'],
            guidance=result['recommendations']['guidance'],
            actions=result['recommendations']['actions'],
            next_steps=result['recommendations']['next_steps'],
            emergency_options=result['recommendations'].get('emergency_options'),
            assessment_reasoning=result['reasoning']
        )

        logger.info(f"Triage complete for {report.user_id}: {result['severity_level']}")
        return response

    except Exception as e:
        logger.error(f"Triage failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Triage assessment failed: {str(e)}")


@app.get("/api/user/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get user's medical profile"""
    
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        conditions = db.get_medical_conditions(user_id)
        medications = db.get_medications(user_id)
        allergies = db.get_allergies(user_id)
        contacts = db.get_emergency_contacts(user_id)

        return {
            'user_id': user_id,
            'name': user.get('name'),
            'age': user.get('age'),
            'gender': user.get('gender'),
            'conditions': [c.get('condition_name') for c in conditions],
            'medications': [
                {
                    'name': m.get('drug_name'),
                    'dosage': m.get('dosage'),
                    'frequency': m.get('frequency')
                }
                for m in medications
            ],
            'allergies': [
                {
                    'allergen': a.get('allergen'),
                    'severity': a.get('severity')
                }
                for a in allergies
            ],
            'emergency_contacts': [
                {
                    'name': c.get('contact_name'),
                    'phone': c.get('phone_number'),
                    'relationship': c.get('relationship')
                }
                for c in contacts
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/emergency-notify/{user_id}")
async def notify_emergency_contacts(user_id: str, background_tasks: BackgroundTasks):
    """
    Notify emergency contacts (mock for now)
    Later: integrate with Twilio for real SMS/calls
    """
    
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        contacts = db.get_emergency_contacts(user_id)
        
        if not contacts:
            return {
                "status": "no_contacts",
                "message": "No emergency contacts configured"
            }

        # Mock notification
        notification_log = []
        for contact in contacts:
            message = f"[MOCK] SMS sent to {contact.get('contact_name')} ({contact.get('phone_number')}): Emergency alert from health monitoring system"
            logger.info(message)
            notification_log.append({
                'contact': contact.get('contact_name'),
                'phone': contact.get('phone_number'),
                'status': 'simulated'
            })

        return {
            "status": "success",
            "contacts_notified": len(notification_log),
            "notifications": notification_log,
            "note": "This is a simulation. In production, SMS would be sent via Twilio."
        }

    except Exception as e:
        logger.error(f"Emergency notification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/assessments/{user_id}")
async def get_assessment_history(user_id: str, limit: int = 10):
    """Get recent assessments for a user"""
    
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        # Note: Would need to implement this method in database.py
        # For now, return placeholder
        return {
            "user_id": user_id,
            "assessments": [],
            "note": "Assessment history feature coming soon"
        }

    except Exception as e:
        logger.error(f"Failed to get assessments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    if db:
        db.close()
        logger.info("Database connection closed")


# ============================================================================
# Root
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Elderly Health Triage System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "triage": "/api/triage",
            "user_profile": "/api/user/{user_id}",
            "emergency_notify": "/api/emergency-notify/{user_id}",
            "assessments": "/api/assessments/{user_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)