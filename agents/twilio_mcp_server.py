"""
Twilio MCP Server
Sends SMS to emergency contacts autonomously
"""

import os
import json
import logging
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor
from twilio.rest import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio credentials (from environment variables)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Database credentials
DB_HOST = os.getenv("DB_HOST", "10.116.112.2")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def get_emergency_contacts(user_id: str) -> list:
    """
    Query database for emergency contacts
    Returns list of dicts with: name, phone_number, relationship
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT contact_name, phone_number, relationship
        FROM emergency_contacts
        WHERE user_id = %s
        """
        cur.execute(query, (user_id,))
        contacts = cur.fetchall()
        
        cur.close()
        conn.close()
        
        logger.info(f"[Twilio MCP] Found {len(contacts)} emergency contacts for {user_id}")
        return contacts
    
    except Exception as e:
        logger.error(f"[Twilio MCP] Error fetching contacts: {str(e)}")
        return []


def send_sms_to_contact(phone_number: str, message: str) -> dict:
    """
    Send SMS via Twilio to a single contact
    Returns: {'success': bool, 'message_sid': str, 'error': str}
    """
    try:
        logger.info(f"[Twilio MCP] Sending SMS to {phone_number}")
        
        message_obj = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        logger.info(f"[Twilio MCP] SMS sent successfully. SID: {message_obj.sid}")
        return {
            'success': True,
            'message_sid': message_obj.sid,
            'phone_number': phone_number,
            'error': None
        }
    
    except Exception as e:
        logger.error(f"[Twilio MCP] Error sending SMS: {str(e)}")
        return {
            'success': False,
            'message_sid': None,
            'phone_number': phone_number,
            'error': str(e)
        }


def send_emergency_sms(user_id: str, message: str) -> dict:
    """
    MCP Tool: Send SMS to all emergency contacts
    
    Args:
        user_id: User ID to get contacts for
        message: Message to send
    
    Returns:
        {
            'success': bool,
            'contacts_notified': [
                {'name': str, 'phone': str, 'sms_sent': bool}
            ],
            'total_contacts': int,
            'sms_successful': int,
            'sms_failed': int
        }
    """
    logger.info(f"[Twilio MCP] Starting emergency SMS for user {user_id}")
    
    # Get contacts from DB
    contacts = get_emergency_contacts(user_id)
    
    if not contacts:
        logger.warning(f"[Twilio MCP] No emergency contacts found for {user_id}")
        return {
            'success': False,
            'message': 'No emergency contacts found',
            'contacts_notified': [],
            'total_contacts': 0,
            'sms_successful': 0,
            'sms_failed': 0
        }
    
    # Send SMS to each contact
    notified = []
    successful_count = 0
    failed_count = 0
    
    for contact in contacts:
        phone = contact['phone_number']
        name = contact['contact_name']
        relationship = contact['relationship']
        
        # Send SMS
        result = send_sms_to_contact(phone, message)
        
        notified.append({
            'name': name,
            'relationship': relationship,
            'phone': phone,
            'sms_sent': result['success'],
            'message_sid': result.get('message_sid')
        })
        
        if result['success']:
            successful_count += 1
        else:
            failed_count += 1
    
    logger.info(f"[Twilio MCP] SMS complete: {successful_count} sent, {failed_count} failed")
    
    return {
        'success': successful_count > 0,
        'message': f'Sent {successful_count}/{len(contacts)} SMS messages',
        'contacts_notified': notified,
        'total_contacts': len(contacts),
        'sms_successful': successful_count,
        'sms_failed': failed_count
    }


def process_mcp_request(request: dict) -> dict:
    """
    Process MCP tool request
    Expected format:
    {
        'tool': 'send_emergency_sms',
        'user_id': 'user_001',
        'message': 'Emergency alert: ...'
    }
    """
    try:
        tool = request.get('tool')
        
        if tool == 'send_emergency_sms':
            user_id = request.get('user_id')
            message = request.get('message')
            
            if not user_id or not message:
                return {
                    'success': False,
                    'error': 'Missing required parameters: user_id, message'
                }
            
            result = send_emergency_sms(user_id, message)
            return result
        
        else:
            return {
                'success': False,
                'error': f'Unknown tool: {tool}'
            }
    
    except Exception as e:
        logger.error(f"[Twilio MCP] Error processing request: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# For testing locally
if __name__ == "__main__":
    # Test request
    test_request = {
        'tool': 'send_emergency_sms',
        'user_id': 'user_001',
        'message': '[TEST] Emergency Health Alert: You have been assessed as EMERGENCY level. Call ambulance immediately!'
    }
    
    result = process_mcp_request(test_request)
    print(json.dumps(result, indent=2))