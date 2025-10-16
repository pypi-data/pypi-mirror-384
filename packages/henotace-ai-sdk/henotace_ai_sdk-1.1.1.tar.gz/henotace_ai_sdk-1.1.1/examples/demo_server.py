#!/usr/bin/env python3
"""
Interactive web demo for the Henotace AI Python SDK
Similar to the Node.js demo but built with Python/Flask
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
sys.path.append('..')
from src.henotace_ai import HenotaceAI, create_tutor, SessionSubject, InMemoryConnector

app = Flask(__name__)
CORS(app)

# Global storage for demo sessions
sessions = {}
storage = InMemoryConnector()

# Initialize SDK
api_key = os.getenv('HENOTACE_API_KEY', 'test_key')
sdk = HenotaceAI(api_key=api_key)

@app.route('/')
def index():
    """Serve the main demo page"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Check API status"""
    try:
        if sdk.get_status_ok():
            return jsonify({
                'success': True,
                'status': 'ok',
                'message': 'API is available'
            })
        else:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'API is not available'
            }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/session', methods=['POST'])
def create_session():
    """Create a new chat session"""
    try:
        data = request.get_json() or {}
        
        session_id = data.get('sessionId', f'session_{int(datetime.now().timestamp() * 1000)}')
        tutor_name = data.get('tutorName', 'AI Tutor')
        subject_name = data.get('subject', 'general')
        grade_level = data.get('gradeLevel', 'high_school')
        topic = data.get('topic', '')
        
        # Create session data
        session_data = {
            'id': session_id,
            'tutorName': tutor_name,
            'subject': subject_name,
            'gradeLevel': grade_level,
            'topic': topic,
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        sessions[session_id] = session_data
        
        return jsonify({
            'success': True,
            'data': session_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/sessions')
def list_sessions():
    """List all chat sessions"""
    try:
        session_list = [
            {
                'id': session_id,
                'tutorName': session['tutorName'],
                'subject': session['subject'],
                'messageCount': len(session['messages']),
                'created_at': session['created_at'],
                'last_activity': session['last_activity']
            }
            for session_id, session in sessions.items()
        ]
        
        # Sort by last activity
        session_list.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': session_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/session/<session_id>')
def get_session(session_id):
    """Get a specific session"""
    try:
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': sessions[session_id]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
async def chat():
    """Send a message to the AI tutor"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        session_id = data.get('sessionId')
        message = data.get('message')
        
        if not session_id or not message:
            return jsonify({
                'success': False,
                'message': 'sessionId and message are required'
            }), 400
        
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
        
        session = sessions[session_id]
        
        # Create tutor if not exists
        tutor_id = f"tutor_{session_id}"
        
        # Add user message to session
        user_message = {
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        session['messages'].append(user_message)
        
        # Create tutor instance
        tutor = await create_tutor(
            sdk=sdk,
            student_id=session_id,
            tutor_id=tutor_id,
            subject=SessionSubject(
                id=session['subject'],
                name=session['subject'].title(),
                topic=session['topic']
            ),
            storage=storage
        )
        
        # Set context based on session data
        context_parts = []
        if session['gradeLevel']:
            context_parts.append(f"Grade Level: {session['gradeLevel']}")
        if session['topic']:
            context_parts.append(f"Topic: {session['topic']}")
        
        if context_parts:
            tutor.set_context(context_parts)
        
        # Set persona
        tutor.set_persona(
            f"You are {session['tutorName']}, a helpful AI tutor specializing in {session['subject']}. "
            f"You provide clear explanations, use examples, and encourage learning."
        )
        
        # Send message to AI
        response = await tutor.send(message)
        
        # Add AI response to session
        ai_message = {
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        }
        session['messages'].append(ai_message)
        session['last_activity'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'data': {
                'reply': response,
                'sessionId': session_id
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a chat session"""
    try:
        if session_id in sessions:
            del sessions[session_id]
            return jsonify({
                'success': True,
                'message': 'Session deleted'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Henotace AI Python Demo Server")
    print("📡 API Key:", "***" + api_key[-4:] if len(api_key) > 4 else "***")
    print("🌐 Server will be available at: http://localhost:5000")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
