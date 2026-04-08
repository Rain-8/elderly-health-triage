"""
Primary Agent: Orchestrator
Coordinates all sub-agents for elderly health triage
"""

import logging
from typing import Dict, Any
from agents.intake import IntakeAgent
from agents.history import HistoryAgent
from agents.assessment import AssessmentAgent
from agents.recommendation import RecommendationAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Orchestrator:
    """Primary agent that coordinates all sub-agents"""

    def __init__(self, db, gemini_client):
        """Initialize orchestrator with dependencies"""
        self.db = db
        self.gemini = gemini_client
        
        # Initialize sub-agents
        self.intake = IntakeAgent()
        self.history = HistoryAgent(db)
        self.assessment = AssessmentAgent(gemini_client)
        self.recommendation = RecommendationAgent()

    async def process_symptom_report(self, user_id: str, symptom_input: str) -> Dict[str, Any]:
        """
        Main orchestration flow:
        1. Intake: Parse symptoms
        2. History: Get medical history
        3. Assessment: Determine severity
        4. Recommendation: What to do + emergency options
        """
        
        logger.info(f"[Orchestrator] Starting triage for user {user_id}")
        logger.info(f"[Orchestrator] Symptoms reported: {symptom_input[:100]}...")

        try:
            # STEP 1: INTAKE - Parse symptoms
            logger.info("[Orchestrator] Step 1: Intake - Parsing symptoms")
            intake_result = self.intake.parse_symptoms(symptom_input)
            logger.info(f"[Orchestrator] Intake complete: {intake_result}")

            # STEP 2: HISTORY - Retrieve medical history
            logger.info("[Orchestrator] Step 2: History - Retrieving medical context")
            history_result = self.history.get_context(user_id)
            logger.info(f"[Orchestrator] History retrieved: {len(history_result.get('conditions', []))} conditions, "
                       f"{len(history_result.get('medications', []))} medications, "
                       f"{len(history_result.get('allergies', []))} allergies")

            # STEP 3: ASSESSMENT - Determine severity using Gemini
            logger.info("[Orchestrator] Step 3: Assessment - Determining severity")
            assessment_result = await self.assessment.assess_severity(
                symptoms=intake_result['symptoms'],
                medical_history=history_result,
                user_age=history_result.get('age'),
                user_gender=history_result.get('gender')
            )
            logger.info(f"[Orchestrator] Assessment complete: Severity = {assessment_result['severity_level']}")

            # STEP 4: RECOMMENDATION - Generate actions
            logger.info("[Orchestrator] Step 4: Recommendation - Generating actions")
            recommendation_result = self.recommendation.generate_actions(
                severity_level=assessment_result['severity_level'],
                symptoms=intake_result['symptoms'],
                medical_history=history_result,
                assessment_reasoning=assessment_result['reasoning']
            )
            logger.info(f"[Orchestrator] Recommendation complete: {len(recommendation_result['actions'])} actions")

            # SYNTHESIZE FINAL RESULT
            final_result = {
                'user_id': user_id,
                'symptoms_reported': symptom_input,
                'severity_level': assessment_result['severity_level'],
                'reasoning': assessment_result['reasoning'],
                'recommendations': {
                    'guidance': recommendation_result['guidance'],
                    'actions': recommendation_result['actions'],
                    'next_steps': recommendation_result['next_steps'],
                    'emergency_options': recommendation_result.get('emergency_options')
                },
                'intake_data': intake_result,
                'history_data': history_result,
                'assessment_data': assessment_result
            }
            # Save to database
            logger.info("[Orchestrator] Saving assessment to database")
            self.db.save_assessment(user_id, {
                'symptoms_reported': symptom_input,
                'severity_level': assessment_result['severity_level'],
                'reasoning': assessment_result['reasoning'],
                'recommendations': recommendation_result['guidance'],
                'actions_taken': str(recommendation_result['actions'])
            })

            logger.info(f"[Orchestrator] Triage complete for user {user_id}")
            return final_result

        except Exception as e:
            logger.error(f"[Orchestrator] Error during triage: {str(e)}")
            raise