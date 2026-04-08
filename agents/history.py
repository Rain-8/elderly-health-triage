"""
Sub-Agent 2: History Agent
Retrieves user's medical history from database
"""

import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoryAgent:
    """Retrieves medical history and context"""

    def __init__(self, db):
        """Initialize with database connection"""
        self.db = db

    def get_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete medical context for user
        Returns: age, gender, conditions, medications, allergies, emergency contacts
        """
        
        logger.info(f"[History] Retrieving context for user {user_id}")

        try:
            # Get user basic info
            user = self.db.get_user(user_id)
            if not user:
                logger.warning(f"[History] User {user_id} not found")
                return {
                    'user_found': False,
                    'age': None,
                    'gender': None,
                    'conditions': [],
                    'medications': [],
                    'allergies': [],
                    'emergency_contacts': []
                }

            # Get all medical info
            conditions = self.db.get_medical_conditions(user_id)
            medications = self.db.get_medications(user_id)
            allergies = self.db.get_allergies(user_id)
            contacts = self.db.get_emergency_contacts(user_id)

            result = {
                'user_found': True,
                'user_id': user_id,
                'name': user.get('name'),
                'age': user.get('age'),
                'gender': user.get('gender'),
                'conditions': [c.get('condition_name') for c in conditions],
                'medications': [
                    {
                        'name': m.get('drug_name'),
                        'dosage': m.get('dosage'),
                        'frequency': m.get('frequency'),
                        'reason': m.get('reason')
                    }
                    for m in medications
                ],
                'allergies': [
                    {
                        'allergen': a.get('allergen'),
                        'severity': a.get('severity'),
                        'reaction': a.get('reaction')
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

            logger.info(f"[History] Context retrieved:")
            logger.info(f"  - Age: {result['age']}, Gender: {result['gender']}")
            logger.info(f"  - Conditions: {', '.join(result['conditions']) if result['conditions'] else 'none'}")
            logger.info(f"  - Medications: {len(result['medications'])}")
            logger.info(f"  - Allergies: {len(result['allergies'])}")
            logger.info(f"  - Emergency contacts: {len(result['emergency_contacts'])}")

            return result

        except Exception as e:
            logger.error(f"[History] Error retrieving context: {str(e)}")
            return {
                'user_found': False,
                'error': str(e),
                'conditions': [],
                'medications': [],
                'allergies': [],
                'emergency_contacts': []
            }