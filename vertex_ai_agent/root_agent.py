"""
Elderly Health Triage Agent - Google ADK Implementation
Root agent with proper ADK structure
"""

import os
import logging
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

import requests

# Setup Logging and Environment
load_dotenv()

# Environment variables
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION")
TRIAGE_API_URL = os.getenv("TRIAGE_API_URL")
SMS_API_URL = os.getenv("SMS_API_URL")
MODEL = os.getenv("MODEL", "gemini-2.0-flash")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Tool 1: Save symptoms to state
def save_symptoms_to_state(
    tool_context: ToolContext, user_id: str, symptoms: str
) -> dict[str, str]:
    """Saves the user's symptoms to the state."""
    tool_context.state["USER_ID"] = user_id
    tool_context.state["SYMPTOMS"] = symptoms
    logger.info(f"[State] Saved - User: {user_id}, Symptoms: {symptoms}")
    return {
        "status": "success",
        "message": f"Received symptoms for user {user_id}: {symptoms}"
    }


# Tool 2: Call Triage API
def call_triage_assessment(tool_context: ToolContext) -> dict:
    """Calls the triage API to assess symptoms."""
    try:
        user_id = tool_context.state.get("USER_ID", "user_001")
        symptoms = tool_context.state.get("SYMPTOMS", "")
        
        logger.info(f"[Triage] Calling API for {user_id}")
        
        payload = {
            "user_id": user_id,
            "symptoms": symptoms
        }
        
        response = requests.post(TRIAGE_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        tool_context.state["TRIAGE_RESULT"] = result
        
        severity = result.get("severity_level", "unknown")
        logger.info(f"[Triage] Severity: {severity}")
        
        return {
            "status": "success",
            "severity": severity,
            "guidance": result.get("guidance", ""),
            "actions": result.get("actions", [])
        }
    
    except Exception as e:
        logger.error(f"[Triage] Error: {str(e)}")
        return {"status": "error", "message": str(e)}


# Tool 3: Send Emergency SMS
def send_emergency_sms(tool_context: ToolContext) -> dict:
    """Sends emergency SMS if severity is high."""
    try:
        user_id = tool_context.state.get("USER_ID", "user_001")
        triage_result = tool_context.state.get("TRIAGE_RESULT", {})
        severity = triage_result.get("severity_level", "")
        
        if severity not in ["severe", "emergency"]:
            logger.info(f"[SMS] Severity {severity} - SMS not needed")
            return {"status": "skipped", "reason": f"Severity {severity} does not require SMS"}
        
        logger.info(f"[SMS] Sending alert for {user_id}")
        
        endpoint = f"{SMS_API_URL}/{user_id}"
        response = requests.post(endpoint, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        tool_context.state["SMS_RESULT"] = result
        
        logger.info(f"[SMS] Sent to {result.get('sms_successful', 0)} contacts")
        
        return {
            "status": "success",
            "sms_sent": result.get("sms_successful", 0),
            "contacts": result.get("total_contacts", 0)
        }
    
    except Exception as e:
        logger.error(f"[SMS] Error: {str(e)}")
        return {"status": "error", "message": str(e)}


# Agent 1: Symptom Intake
symptom_intake_agent = Agent(
    name="symptom_intake_agent",
    model=MODEL,
    description="Collects patient symptoms.",
    instruction="""You are the intake agent. Greet the user, ask for symptoms, and use the 'save_symptoms_to_state' tool to save their information.""",
    tools=[save_symptoms_to_state]
)


# Agent 2: Assessment
assessment_agent = Agent(
    name="assessment_agent",
    model=MODEL,
    description="Assesses symptoms and determines severity.",
    instruction="""You are the assessment agent. Use 'call_triage_assessment' tool to get the medical assessment and present the severity level and guidance.""",
    tools=[call_triage_assessment]
)


# Agent 3: Emergency Response
emergency_agent = Agent(
    name="emergency_agent",
    model=MODEL,
    description="Handles emergency notifications.",
    instruction="""You are the emergency agent. If severity is SEVERE or EMERGENCY, use 'send_emergency_sms' tool to alert contacts.""",
    tools=[send_emergency_sms]
)


# Sequential Workflow
triage_workflow = SequentialAgent(
    name="triage_workflow",
    description="Complete triage workflow",
    sub_agents=[
        symptom_intake_agent,
        assessment_agent,
        emergency_agent
    ]
)


# Root Agent (Entry Point)
root_agent = Agent(
    name="elderly_health_triage",
    model=MODEL,
    description="Elderly Health Triage System",
    instruction="""Welcome to Elderly Health Triage. I will assess your symptoms and provide guidance. If serious, I'll alert your emergency contacts.""",
    sub_agents=[triage_workflow]
)