"""
Twilio MCP Server - MOCK VERSION
Simulates sending SMS to emergency contacts (no real Twilio needed)
Perfect for demonstration and testing
"""

import os
import json
import logging
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database credentials
DB_HOST = os.getenv("DB_HOST", "10.116.112.2")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))

# Mock Twilio phone number (demonstration only)
MOCK_TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER", "+1-740-560-1120")


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


def send_mock_sms(phone_number: str, message: str) -> dict:
    """
    MOCK SMS: Simulate sending SMS without real Twilio
    This is for demonstration purposes
    
    In production, this would use real Twilio API:
    from twilio.rest import Client
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    message = client.messages.create(...)
    
    Returns: {'success': bool, 'message_sid': str, 'error': str}
    """
    try:
        logger.info(f"[Twilio MCP] MOCK SMS to {phone_number}")
        logger.info(f"[Twilio MCP] Message: {message[:50]}...")
        
        # Generate mock message SID (simulates Twilio response)
        import uuid
        mock_sid = f"SM{str(uuid.uuid4())[:28]}"
        
        logger.info(f"[Twilio MCP] MOCK SMS sent successfully. SID: {mock_sid}")
        return {
            'success': True,
            'message_sid': mock_sid,
            'phone_number': phone_number,
            'error': None,
            'is_mock': True,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"[Twilio MCP] Error in mock SMS: {str(e)}")
        return {
            'success': False,
            'message_sid': None,
            'phone_number': phone_number,
            'error': str(e),
            'is_mock': True
        }


def send_emergency_sms(user_id: str, message: str) -> dict:
    """
    MCP Tool: Send MOCK SMS to all emergency contacts
    
    This function:
    1. Queries database for emergency contacts of user_id
    2. Simulates sending SMS to each contact
    3. Returns status of each SMS attempt
    
    Args:
        user_id: User ID to get contacts for
        message: Message to send
    
    Returns:
        {
            'success': bool,
            'message': str,
            'contacts_notified': [
                {
                    'name': str,
                    'relationship': str,
                    'phone': str,
                    'sms_sent': bool,
                    'message_sid': str,
                    'is_mock': bool
                }
            ],
            'total_contacts': int,
            'sms_successful': int,
            'sms_failed': int,
            'note': str
        }
    """
    logger.info(f"[Twilio MCP] Starting MOCK emergency SMS for user {user_id}")
    
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
            'sms_failed': 0,
            'note': 'MOCK SMS System - No contacts in database'
        }
    
    # Send MOCK SMS to each contact
    notified = []
    successful_count = 0
    failed_count = 0
    
    for contact in contacts:
        phone = contact['phone_number']
        name = contact['contact_name']
        relationship = contact['relationship']
        
        # Send MOCK SMS
        result = send_mock_sms(phone, message)
        
        notified.append({
            'name': name,
            'relationship': relationship,
            'phone': phone,
            'sms_sent': result['success'],
            'message_sid': result.get('message_sid'),
            'is_mock': True,
            'timestamp': result.get('timestamp')
        })
        
        if result['success']:
            successful_count += 1
        else:
            failed_count += 1
    
    logger.info(f"[Twilio MCP] MOCK SMS complete: {successful_count} sent, {failed_count} failed")
    
    return {
        'success': successful_count > 0,
        'message': f'MOCK: Sent {successful_count}/{len(contacts)} SMS messages',
        'contacts_notified': notified,
        'total_contacts': len(contacts),
        'sms_successful': successful_count,
        'sms_failed': failed_count,
        'note': 'This is a MOCK SMS system for demonstration purposes. In production, replace with real Twilio API calls using credentials: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER'
    }


def process_mcp_request(request: dict) -> dict:
    """
    Process MCP tool request
    Expected format:
    {
        'tool': 'send_emergency_sms',
        'user_id': 'user_001',
        'message': 'Emergency alert message'
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


if __name__ == "__main__":
    # Test request
    test_request = {
        'tool': 'send_emergency_sms',
        'user_id': 'user_001',
        'message': '[EMERGENCY] Health Alert: User has been assessed as EMERGENCY level. CALL AMBULANCE IMMEDIATELY!'
    }
    
    result = process_mcp_request(test_request)
    print("\n" + "="*80)
    print("TWILIO MCP SERVER TEST - MOCK SMS")
    print("="*80)
    print(json.dumps(result, indent=2))
    print("="*80 + "\n")