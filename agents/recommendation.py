"""
Sub-Agent 4: Recommendation Agent
Generates actionable recommendations based on severity
"""

import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationAgent:
    """Generates recommendations and emergency options"""

    def generate_actions(
        self,
        severity_level: str,
        symptoms: List[str],
        medical_history: Dict[str, Any],
        assessment_reasoning: str
    ) -> Dict[str, Any]:
        """
        Generate recommendations based on severity
        """
        
        logger.info(f"[Recommendation] Generating recommendations for severity: {severity_level}")

        actions = []
        emergency_options = None
        
        if severity_level == 'casual':
            # Minor symptoms - home care
            guidance = "Your symptoms appear mild and not urgent. Here's what you can do:"
            actions = [
                "Rest and get adequate sleep",
                "Stay hydrated (drink water regularly)",
                "Monitor your symptoms - watch for any changes",
                "If symptoms persist beyond 24-48 hours, contact your doctor"
            ]
            next_steps = "Monitor symptoms. Call doctor if symptoms worsen or persist."
            
        elif severity_level == 'mild':
            # Mild symptoms - home care with monitoring
            guidance = "Your symptoms are mild but worth monitoring. Here's what you can do:"
            actions = [
                "Rest and avoid strenuous activity",
                "Stay hydrated",
                "Take over-the-counter pain relief (if not allergic)",
                "Monitor your symptoms closely",
                "Contact your doctor if symptoms worsen or last more than 1-2 days"
            ]
            next_steps = "Monitor at home. Call doctor tomorrow if symptoms persist."
            
        elif severity_level == 'moderate':
            # Moderate symptoms - needs doctor attention
            guidance = "Your symptoms require medical attention. Here's what you should do:"
            actions = [
                "Contact your doctor today",
                "If unable to reach doctor, visit an urgent care center",
                "Bring list of current medications",
                "Have your allergies ready to mention",
                "If symptoms worsen while waiting, don't hesitate to go to ER"
            ]
            next_steps = "Call your doctor today for an appointment or visit urgent care."
            
        elif severity_level == 'severe':
            # Severe symptoms - urgent care needed
            guidance = "Your symptoms are serious and need urgent medical attention:"
            actions = [
                "Call your doctor immediately",
                "If unable to reach doctor, go to nearest Urgent Care or ER",
                "Have emergency contacts nearby",
                "Bring all medications and allergy information"
            ]
            next_steps = "Go to urgent care or ER immediately. Call your doctor."
            emergency_options = {
                'type': 'severe',
                'options': [
                    {
                        'action': 'Call Emergency Contacts',
                        'description': 'Notify family/caregivers',
                        'button_text': 'Notify Family'
                    },
                    {
                        'action': 'Go to Urgent Care',
                        'description': 'Visit nearest urgent care facility',
                        'button_text': 'Urgent Care Now'
                    },
                    {
                        'action': 'Go to ER',
                        'description': 'Visit nearest Emergency Room',
                        'button_text': 'Go to ER'
                    }
                ]
            }
            
        elif severity_level == 'emergency':
            # Emergency - call 911/ambulance
            guidance = "🔴 EMERGENCY: You need immediate medical help. CALL AMBULANCE NOW!"
            actions = [
                "CALL LOCAL AMBULANCE IMMEDIATELY (911 or local emergency number)",
                "Do NOT wait",
                "Tell paramedics about your medical history and medications",
                "Alert your emergency contacts"
            ]
            next_steps = "CALL AMBULANCE NOW. Notify emergency contacts immediately."
            emergency_options = {
                'type': 'emergency',
                'options': [
                    {
                        'action': 'Call Ambulance',
                        'description': '🚑 Call emergency services (911)',
                        'button_text': 'CALL AMBULANCE NOW',
                        'urgent': True
                    },
                    {
                        'action': 'Notify Emergency Contacts',
                        'description': 'Send SMS/call family/caregivers',
                        'button_text': 'NOTIFY FAMILY NOW',
                        'urgent': True
                    }
                ]
            }
        else:
            # Unknown severity
            guidance = "Please contact your doctor for guidance."
            actions = ["Contact your doctor"]
            next_steps = "Contact your doctor."

        result = {
            'guidance': guidance,
            'actions': actions,
            'next_steps': next_steps,
            'emergency_options': emergency_options,
            'severity_level': severity_level,
            'reasoning': assessment_reasoning,
            'medical_context': {
                'conditions': medical_history.get('conditions', []),
                'medications': medical_history.get('medications', []),
                'allergies': medical_history.get('allergies', []),
                'emergency_contacts': medical_history.get('emergency_contacts', [])
            }
        }

        logger.info(f"[Recommendation] Recommendations generated")
        return result