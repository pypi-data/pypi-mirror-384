"""
Henotace AI SDK for Python
==========================

A Python SDK for integrating with Henotace AI's educational API.
Supports AI tutoring, assessment grading, content generation, and educational games.

Author: Henotace AI Team
Version: 1.0.0
"""

import requests
import json
from typing import Dict, List, Optional, Union
from datetime import datetime
import time


class HenotaceAPIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class HenotaceSDK:
    """
    Henotace AI SDK for Python
    
    This SDK provides easy access to all Henotace AI API endpoints including:
    - AI Tutoring sessions and chat
    - Assessment grading
    - Content generation
    - Educational games
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000/api/external"):
        """
        Initialize the Henotace SDK
        
        Args:
            api_key (str): Your API key from Henotace AI
            base_url (str): Base URL for the API (default: localhost for development)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """
        Make a request to the API
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            data (Dict): Request data for POST requests
            params (Dict): Query parameters for GET requests
            
        Returns:
            Dict: API response data
            
        Raises:
            HenotaceAPIError: If the API request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_data = response.json()
            
            if not response.ok:
                error_message = response_data.get('error', f'API request failed with status {response.status_code}')
                raise HenotaceAPIError(
                    message=error_message,
                    status_code=response.status_code,
                    response_data=response_data
                )
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            raise HenotaceAPIError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise HenotaceAPIError(f"Invalid JSON response: {str(e)}")
    
    def get_status(self) -> Dict:
        """
        Get API status and client information
        
        Returns:
            Dict: Status information including client details and remaining API calls
        """
        return self._make_request('GET', '/working/status/')
    
    # AI Tutoring Methods
    
    def create_tutoring_session(self, student_id: str, subject: str, grade_level: str, 
                              topic: str = "", language: str = "en") -> Dict:
        """
        Create a new AI tutoring session
        
        Args:
            student_id (str): Unique identifier for the student
            subject (str): Subject area (e.g., 'mathematics', 'science', 'english')
            grade_level (str): Grade level (e.g., 'primary', 'secondary', 'university')
            topic (str): Specific topic to focus on (optional)
            language (str): Language for the session (default: 'en')
            
        Returns:
            Dict: Session information including session_id
        """
        data = {
            'student_id': student_id,
            'subject': subject,
            'grade_level': grade_level,
            'topic': topic,
            'language': language
        }
        return self._make_request('POST', '/working/tutoring/session/', data=data)
    
    def chat_with_tutor(self, session_id: str, message: str, context: Dict = None) -> Dict:
        """
        Send a message to the AI tutor
        
        Args:
            session_id (str): Session ID from create_tutoring_session
            message (str): Student's message/question
            context (Dict): Additional context (optional)
            
        Returns:
            Dict: AI tutor's response
        """
        data = {
            'message': message,
            'context': context or {}
        }
        return self._make_request('POST', f'/working/tutoring/session/{session_id}/chat/', data=data)
    
    # Assessment Methods
    
    def grade_assignment(self, student_id: str, assignment_type: str, subject: str,
                        questions: List[Dict], answers: List[Dict]) -> Dict:
        """
        Grade an assignment using AI
        
        Args:
            student_id (str): Student identifier
            assignment_type (str): Type of assignment (e.g., 'quiz', 'homework', 'exam')
            subject (str): Subject area
            questions (List[Dict]): List of question objects
            answers (List[Dict]): List of answer objects
            
        Returns:
            Dict: Grading results including score, grade, and feedback
        """
        data = {
            'student_id': student_id,
            'assignment_type': assignment_type,
            'subject': subject,
            'questions': questions,
            'answers': answers
        }
        return self._make_request('POST', '/working/assessment/grade/', data=data)
    
    # Content Generation Methods
    
    def generate_content(self, content_type: str, subject: str, grade_level: str,
                        topic: str, requirements: str = "") -> Dict:
        """
        Generate educational content
        
        Args:
            content_type (str): Type of content ('lesson_plan', 'questions', 'explanation')
            subject (str): Subject area
            grade_level (str): Target grade level
            topic (str): Topic for the content
            requirements (str): Additional requirements (optional)
            
        Returns:
            Dict: Generated content
        """
        data = {
            'content_type': content_type,
            'subject': subject,
            'grade_level': grade_level,
            'topic': topic,
            'requirements': requirements
        }
        return self._make_request('POST', '/working/content/generate/', data=data)
    
    def generate_lesson_plan(self, subject: str, grade_level: str, topic: str, 
                           requirements: str = "") -> Dict:
        """
        Generate a lesson plan
        
        Args:
            subject (str): Subject area
            grade_level (str): Target grade level
            topic (str): Topic for the lesson
            requirements (str): Additional requirements (optional)
            
        Returns:
            Dict: Generated lesson plan
        """
        return self.generate_content('lesson_plan', subject, grade_level, topic, requirements)
    
    def generate_quiz_questions(self, subject: str, grade_level: str, topic: str,
                              requirements: str = "") -> Dict:
        """
        Generate quiz questions
        
        Args:
            subject (str): Subject area
            grade_level (str): Target grade level
            topic (str): Topic for the questions
            requirements (str): Additional requirements (optional)
            
        Returns:
            Dict: Generated questions
        """
        return self.generate_content('questions', subject, grade_level, topic, requirements)
    
    # Educational Games Methods
    
    def get_game_questions(self, game_id: int) -> Dict:
        """
        Get questions for an educational game
        
        Args:
            game_id (int): Game identifier
            
        Returns:
            Dict: Game questions and metadata
        """
        return self._make_request('GET', f'/working/edugames/{game_id}/questions/')
    
    def submit_game_answers(self, game_id: int, student_id: str, answers: List[Dict]) -> Dict:
        """
        Submit answers for an educational game
        
        Args:
            game_id (int): Game identifier
            student_id (str): Student identifier
            answers (List[Dict]): List of answer objects
            
        Returns:
            Dict: Scoring results and feedback
        """
        data = {
            'game_id': game_id,
            'student_id': student_id,
            'answers': answers
        }
        return self._make_request('POST', '/working/edugames/submit/', data=data)
    
    # Utility Methods
    
    def get_remaining_calls(self) -> int:
        """
        Get remaining API calls for the current client
        
        Returns:
            int: Number of remaining API calls
        """
        status = self.get_status()
        return status.get('data', {}).get('api_calls_remaining', 0)
    
    def is_healthy(self) -> bool:
        """
        Check if the API is healthy and accessible
        
        Returns:
            bool: True if API is healthy, False otherwise
        """
        try:
            self.get_status()
            return True
        except HenotaceAPIError:
            return False


# Convenience functions for quick usage

def create_client(api_key: str, base_url: str = "http://localhost:8000/api/external") -> HenotaceSDK:
    """
    Create a Henotace SDK client
    
    Args:
        api_key (str): Your API key
        base_url (str): API base URL
        
    Returns:
        HenotaceSDK: Configured SDK client
    """
    return HenotaceSDK(api_key, base_url)


# Example usage
if __name__ == "__main__":
    # Example usage of the SDK
    api_key = "your_api_key_here"
    client = create_client(api_key)
    
    try:
        # Check API status
        status = client.get_status()
        print(f"API Status: {status['data']['status']}")
        print(f"Remaining calls: {client.get_remaining_calls()}")
        
        # Create a tutoring session
        session = client.create_tutoring_session(
            student_id="student_123",
            subject="mathematics",
            grade_level="secondary",
            topic="algebra"
        )
        print(f"Created session: {session['data']['session_id']}")
        
        # Chat with the tutor
        chat_response = client.chat_with_tutor(
            session_id=session['data']['session_id'],
            message="Can you help me solve 2x + 5 = 13?",
            context={"previous_messages": []}
        )
        print(f"Tutor response: {chat_response['data']['ai_response']}")
        
        # Generate a lesson plan
        lesson_plan = client.generate_lesson_plan(
            subject="science",
            grade_level="primary",
            topic="photosynthesis",
            requirements="Simple explanation for 8-year-olds"
        )
        print(f"Generated lesson plan: {lesson_plan['data']['generated_content'][:100]}...")
        
    except HenotaceAPIError as e:
        print(f"API Error: {e.message}")
        if e.status_code:
            print(f"Status Code: {e.status_code}")

