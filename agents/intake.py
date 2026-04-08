"""
Sub-Agent 1: Intake Agent
Parses symptom descriptions and extracts structured data
"""

import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntakeAgent:
    """Parses raw symptom input into structured data"""

    def parse_symptoms(self, symptom_input: str) -> Dict[str, Any]:
        """
        Parse raw symptom text and extract structure
        For prototype: simple pattern matching
        Later: Could use Gemini for more sophisticated parsing
        """
        
        logger.info(f"[Intake] Parsing symptoms: {symptom_input[:100]}...")
        
        # For now: simple extraction
        # Real version would use NLP/Gemini
        
        symptoms_list = []
        duration = "unknown"
        severity_self_reported = "moderate"
        
        # Simple keyword extraction
        input_lower = symptom_input.lower()
        
        # Symptom keywords
        symptom_keywords = {
            'chest pain': 'chest pain',
            'chest': 'chest pain',
            'heart': 'heart-related',
            'shortness of breath': 'shortness of breath',
            'breathing': 'breathing difficulty',
            'dizzy': 'dizziness',
            'dizziness': 'dizziness',
            'headache': 'headache',
            'head pain': 'headache',
            'nausea': 'nausea',
            'vomiting': 'vomiting',
            'fever': 'fever',
            'cold': 'cold/chills',
            'pain': 'pain',
            'weakness': 'weakness',
            'fatigue': 'fatigue',
            'confusion': 'confusion',
            'fell': 'fall/injury',
            'fall': 'fall/injury',
            'broken': 'bone injury',
            'cut': 'bleeding/cut',
            'bleeding': 'bleeding',
            'unconscious': 'loss of consciousness',
            'fainted': 'fainting',
            'swollen': 'swelling',
            'rash': 'rash',
        }
        
        # Extract symptoms
        for keyword, symptom in symptom_keywords.items():
            if keyword in input_lower:
                if symptom not in symptoms_list:
                    symptoms_list.append(symptom)
        
        # Duration keywords
        if 'hours' in input_lower:
            if '24' in input_lower or 'day' in input_lower:
                duration = "1 day"
            elif '12' in input_lower:
                duration = "12 hours"
            elif '6' in input_lower:
                duration = "6 hours"
            elif '2' in input_lower:
                duration = "2 hours"
            else:
                duration = "few hours"
        elif 'minutes' in input_lower:
            duration = "minutes"
        elif 'week' in input_lower:
            duration = "1 week"
        
        # Self-reported severity
        if any(word in input_lower for word in ['severe', 'very', 'intense', 'unbearable', 'emergency']):
            severity_self_reported = "severe"
        elif any(word in input_lower for word in ['mild', 'slight', 'little']):
            severity_self_reported = "mild"
        else:
            severity_self_reported = "moderate"
        
        result = {
            'symptoms': symptoms_list if symptoms_list else ['general health concern'],
            'duration': duration,
            'severity_self_reported': severity_self_reported,
            'raw_input': symptom_input,
            'parsed_successfully': len(symptoms_list) > 0
        }
        
        logger.info(f"[Intake] Parsed: {result}")
        return result