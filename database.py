"""
Database module for elderly health triage system
Connects to AlloyDB (PostgreSQL)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    def __init__(self, host: str, user: str, password: str, dbname: str, port: int = 5432):
        """Initialize database connection"""
        self.conn = None
        self.host = host
        self.user = user
        self.password = password
        self.dbname = dbname
        self.port = port
        self._connect()

    def _connect(self):
        """Connect to AlloyDB"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.dbname,
                port=self.port
            )
            logger.info(f"Connected to AlloyDB: {self.dbname}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user profile"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            return None

    def get_medical_conditions(self, user_id: str) -> List[Dict]:
        """Get all active medical conditions for user"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT condition_name, status FROM medical_conditions WHERE user_id = %s AND status = %s",
                    (user_id, 'active')
                )
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching conditions: {str(e)}")
            return []

    def get_medications(self, user_id: str) -> List[Dict]:
        """Get all medications for user"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT drug_name, dosage, frequency, reason FROM medications WHERE user_id = %s",
                    (user_id,)
                )
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching medications: {str(e)}")
            return []

    def get_allergies(self, user_id: str) -> List[Dict]:
        """Get all allergies for user"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT allergen, severity, reaction FROM allergies WHERE user_id = %s",
                    (user_id,)
                )
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching allergies: {str(e)}")
            return []

    def get_emergency_contacts(self, user_id: str) -> List[Dict]:
        """Get all emergency contacts for user"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT contact_name, phone_number, relationship FROM emergency_contacts WHERE user_id = %s",
                    (user_id,)
                )
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching emergency contacts: {str(e)}")
            return []

    def save_assessment(self, user_id: str, assessment_data: Dict) -> bool:
        """Save assessment to database"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO assessments 
                    (user_id, symptoms_reported, severity_level, assessment_reasoning, recommendations, actions_taken)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        assessment_data.get('symptoms_reported', ''),
                        assessment_data.get('severity_level', ''),
                        assessment_data.get('reasoning', ''),
                        assessment_data.get('recommendations', ''),
                        assessment_data.get('actions_taken', '')
                    )
                )
                self.conn.commit()
                logger.info(f"Assessment saved for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving assessment: {str(e)}")
            self.conn.rollback()
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")