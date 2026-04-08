"""
Sub-Agent 3: Assessment Agent
Uses Gemini to assess severity based on symptoms and medical history
"""

import logging
import json
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssessmentAgent:
    """Uses Gemini to assess symptom severity"""

    def __init__(self, gemini_client):
        """Initialize with Gemini client"""
        self.gemini = gemini_client

    async def assess_severity(
        self,
        symptoms: List[str],
        medical_history: Dict[str, Any],
        user_age: int = None,
        user_gender: str = None
    ) -> Dict[str, Any]:
        """
        Use Gemini to assess severity level
        Returns: severity_level (casual/mild/moderate/severe/emergency), reasoning
        """
        
        logger.info("[Assessment] Starting severity assessment")

        try:
            # Build context for Gemini
            conditions_str = ", ".join(medical_history.get('conditions', [])) or "none"
            medications_str = "; ".join([
                f"{m['name']} ({m['dosage']})"
                for m in medical_history.get('medications', [])
            ]) or "none"
            allergies_str = ", ".join([
                f"{a['allergen']} ({a['severity']})"
                for a in medical_history.get('allergies', [])
            ]) or "none"
            
            symptoms_str = ", ".join(symptoms)

            # Craft prompt for Gemini
            prompt = f"""You are an experienced elderly health triage specialist. Assess the severity of the following patient's condition.

PATIENT INFORMATION:
- Age: {user_age if user_age else 'Unknown'}
- Gender: {user_gender if user_gender else 'Unknown'}

REPORTED SYMPTOMS:
{symptoms_str}

MEDICAL HISTORY:
- Existing Conditions: {conditions_str}
- Current Medications: {medications_str}
- Allergies: {allergies_str}

SEVERITY LEVELS:
1. CASUAL: Minor symptoms, not health-threatening (e.g., mild headache, minor fatigue)
2. MILD: Uncomfortable but manageable, no immediate danger (e.g., mild fever, minor cough)
3. MODERATE: Noticeable symptoms requiring attention within hours/day (e.g., moderate pain, significant fatigue)
4. SEVERE: Serious symptoms requiring urgent medical attention (e.g., high fever, severe pain, difficulty breathing that's manageable)
5. EMERGENCY: Life-threatening, requires immediate emergency services (e.g., chest pain with heart disease, severe breathing difficulty, unconsciousness)

IMPORTANT CONSIDERATIONS FOR ELDERLY:
- Age itself increases risk (over 70-75 is higher risk)
- Multiple medications indicate complex conditions (drug interactions possible)
- Existing heart disease makes any chest/breathing symptoms serious
- Allergies (especially severe) limit treatment options
- Falls are serious for elderly (bone fractures, head injuries)
- Confusion or cognitive changes are red flags
- Weakness + falls + known heart disease = HIGH RISK

Provide your assessment in this exact JSON format (ONLY the JSON, no other text):
{{
    "severity_level": "casual|mild|moderate|severe|emergency",
    "reasoning": "2-3 sentences explaining why this severity level",
    "red_flags": ["flag1", "flag2", ...],
    "contributing_factors": ["factor1", "factor2", ...],
    "recommendation_type": "home_care|doctor_visit|urgent_care|emergency"
}}"""

            # Call Gemini
            logger.info("[Assessment] Calling Gemini for severity assessment")
            response = self.gemini.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.info(f"[Assessment] Gemini response: {response_text[:200]}...")

            # Parse JSON response
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            assessment_json = json.loads(response_text)

            result = {
                'severity_level': assessment_json.get('severity_level', 'moderate'),
                'reasoning': assessment_json.get('reasoning', ''),
                'red_flags': assessment_json.get('red_flags', []),
                'contributing_factors': assessment_json.get('contributing_factors', []),
                'recommendation_type': assessment_json.get('recommendation_type', 'doctor_visit')
            }

            logger.info(f"[Assessment] Assessment complete: {result['severity_level']}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[Assessment] Failed to parse Gemini response: {str(e)}")
            # Fallback to moderate if parsing fails
            return {
                'severity_level': 'moderate',
                'reasoning': 'Could not assess severity. Recommend consulting a doctor.',
                'red_flags': [],
                'contributing_factors': [],
                'recommendation_type': 'doctor_visit'
            }
        except Exception as e:
            logger.error(f"[Assessment] Error during assessment: {str(e)}")
            raise