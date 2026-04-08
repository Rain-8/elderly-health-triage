"""
Elderly Health Triage Agent - Google ADK Implementation
Main agent file for deployment to Cloud Run
"""

import os
import json
import logging
from typing import Any
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION")
AGENT_NAME = os.getenv("AGENT_NAME")
TRIAGE_API_URL = os.getenv("TRIAGE_API_URL")
SMS_API_URL = os.getenv("SMS_API_URL")


class ElderlyHealthTriageAgent:
    """
    Elderly Health Triage Agent - Google ADK
    
    Features:
    - Assess elderly patient symptoms
    - Determine severity level (casual, mild, moderate, severe, emergency)
    - Autonomously send SMS to emergency contacts for severe/emergency cases
    - Provide medical guidance and next steps
    - Integrated with FastAPI backend for data and Gemini for AI assessment
    """
    
    def __init__(self):
        """Initialize the agent"""
        self.name = "Elderly Health Triage Agent"
        self.version = "1.0"
        self.project_id = PROJECT_ID
        self.region = REGION
        
        logger.info(f"[Agent] Initialized: {self.name} v{self.version}")
        logger.info(f"[Agent] Project: {self.project_id}, Region: {self.region}")
        logger.info(f"[Agent] API URLs configured:")
        logger.info(f"  - Triage: {TRIAGE_API_URL}")
        logger.info(f"  - SMS: {SMS_API_URL}")
    
    def assess_symptoms(self, user_id: str, symptoms: str) -> dict:
        """
        Tool 1: Assess symptoms using triage API
        
        This tool:
        - Takes user ID and symptom description
        - Calls the backend FastAPI /api/triage endpoint
        - Uses multi-agent system (Intake, History, Assessment, Recommendation agents)
        - Calls Gemini AI for severity assessment
        - Returns severity level and medical guidance
        
        Args:
            user_id: User ID (e.g., 'user_001')
            symptoms: Description of symptoms
        
        Returns:
            Triage assessment with:
            - severity_level (casual, mild, moderate, severe, emergency)
            - guidance (medical guidance)
            - actions (recommended actions)
            - next_steps (what to do)
            - assessment_reasoning (AI reasoning)
        """
        try:
            logger.info(f"[Agent Tool] Assessing symptoms for {user_id}")
            logger.info(f"[Agent Tool] Symptoms: {symptoms}")
            
            payload = {
                "user_id": user_id,
                "symptoms": symptoms
            }
            
            response = requests.post(TRIAGE_API_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            severity = result.get('severity_level', 'unknown')
            
            logger.info(f"[Agent Tool] Assessment complete - Severity: {severity}")
            
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"[Agent Tool] API error: {str(e)}")
            return {"success": False, "error": f"Triage API error: {str(e)}"}
        except Exception as e:
            logger.error(f"[Agent Tool] Unexpected error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_emergency_alert(self, user_id: str) -> dict:
        """
        Tool 2: Send emergency SMS to contacts
        
        This tool:
        - Automatically triggered for severe/emergency severity levels
        - Queries database for emergency contacts
        - Sends SMS to all contacts (real or mock depending on Twilio setup)
        - Logs all SMS attempts
        
        Args:
            user_id: User ID to send SMS for
        
        Returns:
            SMS delivery status with:
            - success (bool)
            - contacts_notified (list of contacts)
            - sms_successful (count)
            - sms_failed (count)
        """
        try:
            logger.info(f"[Agent Tool] Sending emergency alert for {user_id}")
            
            endpoint = f"{SMS_API_URL}/{user_id}"
            response = requests.post(endpoint, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            successful = result.get('sms_successful', 0)
            total = result.get('total_contacts', 0)
            
            logger.info(f"[Agent Tool] SMS alert sent to {successful}/{total} contacts")
            
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"[Agent Tool] SMS API error: {str(e)}")
            return {"success": False, "error": f"SMS API error: {str(e)}"}
        except Exception as e:
            logger.error(f"[Agent Tool] Unexpected error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def process(self, user_id: str, symptoms: str) -> dict:
        """
        Main agent orchestration logic
        
        Flow:
        1. User provides symptoms
        2. Call assess_symptoms tool (calls backend API)
        3. Get severity level and assessment
        4. IF severity is severe/emergency:
           - Autonomously call send_emergency_alert tool
           - Send SMS to all emergency contacts
        5. Return complete assessment with SMS status
        
        Args:
            user_id: User ID
            symptoms: Symptom description
        
        Returns:
            Complete assessment with:
            - success (bool)
            - user_id, symptoms
            - triage_assessment (from API)
            - sms_automation (triggered status and result)
        """
        logger.info(f"[Agent] ========================================")
        logger.info(f"[Agent] STARTING ASSESSMENT FOR {user_id}")
        logger.info(f"[Agent] ========================================")
        
        try:
            # Step 1: Assess symptoms
            logger.info(f"[Agent] STEP 1: Calling assess_symptoms tool...")
            triage = self.assess_symptoms(user_id, symptoms)
            
            if not triage or "error" in triage:
                logger.error("[Agent] Assessment failed")
                return {"success": False, "error": "Assessment failed"}
            
            # Step 2: Check severity and trigger SMS if needed
            severity = triage.get("severity_level", "unknown")
            logger.info(f"[Agent] STEP 2: Severity level = {severity}")
            
            sms_result = None
            sms_triggered = False
            
            if severity in ["severe", "emergency"]:
                logger.info(f"[Agent] STEP 3: HIGH SEVERITY ({severity}) - Triggering SMS autonomously...")
                sms_triggered = True
                sms_result = self.send_emergency_alert(user_id)
            else:
                logger.info(f"[Agent] STEP 3: Severity is {severity}, SMS not needed")
            
            # Step 4: Return complete result
            logger.info(f"[Agent] STEP 4: Compiling final result...")
            
            result = {
                "success": True,
                "agent": self.name,
                "version": self.version,
                "user_id": user_id,
                "symptoms": symptoms,
                "triage_assessment": triage,
                "sms_automation": {
                    "triggered": sms_triggered,
                    "severity_threshold": ["severe", "emergency"],
                    "result": sms_result
                }
            }
            
            logger.info(f"[Agent] ========================================")
            logger.info(f"[Agent] ASSESSMENT COMPLETE")
            logger.info(f"[Agent] ========================================")
            
            return result
        
        except Exception as e:
            logger.error(f"[Agent] Processing error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_tools(self) -> dict:
        """
        Return tool definitions for ADK framework
        
        Returns:
            Dictionary of available tools with descriptions and parameters
        """
        return {
            "assess_symptoms": {
                "function": self.assess_symptoms,
                "description": "Assess elderly patient symptoms using AI and determine severity level (casual, mild, moderate, severe, emergency). Queries patient history from database and uses Gemini AI for assessment.",
                "parameters": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (e.g., 'user_001')"
                    },
                    "symptoms": {
                        "type": "string",
                        "description": "Description of patient symptoms"
                    }
                }
            },
            "send_emergency_alert": {
                "function": self.send_emergency_alert,
                "description": "Send emergency SMS alert to all emergency contacts for a user. Automatically triggered for severe/emergency severity levels. Queries emergency contacts from database and sends SMS via Twilio.",
                "parameters": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to send SMS alert for"
                    }
                }
            }
        }


# Initialize agent instance
agent = ElderlyHealthTriageAgent()


def run_agent(user_id: str, symptoms: str) -> dict:
    """
    Entry point for ADK deployment
    Called by ADK framework when deployed to Cloud Run
    """
    return agent.process(user_id, symptoms)


if __name__ == "__main__":
    # Test the agent locally
    print("\n" + "="*80)
    print("ELDERLY HEALTH TRIAGE AGENT - VERTEX AI ADK")
    print("="*80 + "\n")
    
    # Test case 1: Emergency severity
    print("TEST CASE 1: CHEST PAIN (Expected: EMERGENCY)")
    print("-" * 80)
    result1 = agent.process("user_001", "chest pain and shortness of breath")
    print(json.dumps(result1, indent=2))
    
    # Test case 2: Mild severity
    print("\n\nTEST CASE 2: MILD HEADACHE (Expected: MILD)")
    print("-" * 80)
    result2 = agent.process("user_001", "mild headache")
    print(json.dumps(result2, indent=2))
    
    print("\n" + "="*80 + "\n")