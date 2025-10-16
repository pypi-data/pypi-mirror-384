"""
Tutor class for managing chat sessions in Henotace AI Python SDK
"""

import json
import time
from typing import Dict, List, Optional, Any, Union

from .types import (
    SessionStudent, SessionTutor, SessionChat, SessionSubject, 
    StorageConnector, Logger, LogLevel
)
from .index import HenotaceAI


class Tutor:
    """
    Lightweight Tutor instance for managing chat sessions
    """
    
    def __init__(self, sdk: HenotaceAI, student_id: str, tutor_id: str, 
                 storage: Optional[StorageConnector] = None):
        self.sdk = sdk
        self.student_id = student_id
        self.tutor_id = tutor_id
        self.storage = storage or sdk.storage
        self.logger = sdk.get_logger()
        
        self.persistent_context = []
        self.persona = None
        self.user_profile = None
        self.metadata = None
        
        # Compression settings
        self.compression = {
            'max_turns': 12,
            'max_summary_chars': 1200,
            'checkpoint_every': 10
        }
        
        self.logger.debug('Tutor instance created', {
            'studentId': self.student_id,
            'tutorId': self.tutor_id
        })
    
    def set_context(self, context: Union[str, List[str]]) -> None:
        """Set persistent context for the tutor"""
        self.persistent_context = [context] if isinstance(context, str) else context
        
        # Persist to storage
        if self.storage:
            self._persist_to_storage()
    
    def set_persona(self, persona: str) -> None:
        """Set the tutor's persona"""
        self.persona = persona
        if self.storage:
            self._persist_to_storage()
    
    def set_user_profile(self, profile: Dict[str, Any]) -> None:
        """Set user profile information"""
        self.user_profile = profile
        if self.storage:
            self._persist_to_storage()
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metadata for the tutor"""
        self.metadata = metadata
        if self.storage:
            self._persist_to_storage()
    
    def set_compression(self, **options) -> None:
        """Configure compression settings"""
        self.compression.update(options)
    
    def _persist_to_storage(self) -> None:
        """Persist tutor data to storage"""
        try:
            tutors = self.storage.list_tutors(self.student_id)
            existing = None
            
            for t in tutors:
                if t.id == self.tutor_id:
                    existing = t
                    break
            
            if existing:
                # Update existing tutor
                existing.context = self.persistent_context
                existing.persona = self.persona
                existing.user_profile = self.user_profile
                existing.metadata = self.metadata
                self.storage.upsert_tutor(self.student_id, existing)
            else:
                # Create new tutor
                new_tutor = SessionTutor(
                    id=self.tutor_id,
                    name=self.tutor_id,
                    subject=SessionSubject(id='unknown', name='Unknown', topic=''),
                    context=self.persistent_context,
                    persona=self.persona,
                    user_profile=self.user_profile,
                    metadata=self.metadata
                )
                self.storage.upsert_tutor(self.student_id, new_tutor)
        except Exception as e:
            self.logger.warn('Failed to persist tutor data', {'error': str(e)})
    
    def _build_summary_from_chats(self, chats: List[SessionChat], max_chars: int) -> str:
        """Build a summary from chat history"""
        lines = []
        for chat in chats:
            sender = 'AI' if chat.is_reply else 'User'
            lines.append(f"{sender}: {chat.message}")
        
        summary = '\n'.join(lines)
        if len(summary) > max_chars:
            summary = summary[:max_chars - 3] + '...'
        
        return summary
    
    def _auto_compress_if_needed(self) -> None:
        """Auto-compress chat history if needed"""
        if not self.storage:
            return
        
        chats = self.storage.list_chats(self.student_id, self.tutor_id)
        if not chats:
            return
        
        should_checkpoint = len(chats) % self.compression['checkpoint_every'] == 0
        exceeds_window = len(chats) > self.compression['max_turns'] * 2
        
        if should_checkpoint or exceeds_window:
            self.compress_history()
    
    def compress_history(self) -> None:
        """Compress chat history by summarizing older messages"""
        if not self.storage:
            return
        
        chats = self.storage.list_chats(self.student_id, self.tutor_id)
        if not chats:
            return
        
        keep = self.compression['max_turns']
        if len(chats) <= keep:
            return
        
        # Keep recent messages, summarize older ones
        older_chats = chats[:-keep]
        recent_chats = chats[-keep:]
        
        summary_chunk = self._build_summary_from_chats(older_chats, self.compression['max_summary_chars'])
        
        # Update tutor metadata with summary
        tutors = self.storage.list_tutors(self.student_id)
        existing = None
        for t in tutors:
            if t.id == self.tutor_id:
                existing = t
                break
        
        if existing:
            existing_meta = existing.metadata or {}
            accumulated = existing_meta.get('summary', '')
            if accumulated:
                accumulated += f"\n---\n{summary_chunk}"
            else:
                accumulated = summary_chunk
            
            existing.metadata = {**existing_meta, 'summary': accumulated}
            self.storage.upsert_tutor(self.student_id, existing)
        
        # Replace chats with recent ones only
        self.storage.replace_chats(self.student_id, self.tutor_id, recent_chats)
    
    async def send(self, message: str, context: Optional[Union[str, List[str]]] = None, 
                  preset: Optional[str] = None) -> str:
        """
        Send a message to the tutor and get AI response
        
        Args:
            message: User's message
            context: Optional ephemeral context
            preset: Optional AI preset
            
        Returns:
            AI response text
        """
        self.logger.debug('Tutor send message', {
            'studentId': self.student_id,
            'tutorId': self.tutor_id,
            'messageLength': len(message),
            'hasContext': bool(context),
            'preset': preset
        })
        
        # Build history from storage
        history = []
        if self.storage:
            self._auto_compress_if_needed()
            chats = self.storage.list_chats(self.student_id, self.tutor_id)
            history = [
                {'role': 'assistant' if chat.is_reply else 'user', 'content': chat.message}
                for chat in chats
            ]
        
        # Add ephemeral context
        ephemeral = [context] if isinstance(context, str) else (context or [])
        merged_context = self.persistent_context + ephemeral
        
        if merged_context:
            clipped = merged_context[:5]  # Simple budget: top 5 snippets
            context_block = '\n'.join(['[CONTEXT]'] + [str(sn) for sn in clipped])
            history.append({'role': 'assistant', 'content': context_block})
        
        # Add persona, user profile, and metadata as context
        sdk_config = self.sdk.get_config()
        persona = self.persona or sdk_config.get('default_persona')
        user_profile = self.user_profile or sdk_config.get('default_user_profile')
        metadata = self.metadata or sdk_config.get('default_metadata')
        
        header_parts = []
        if persona:
            header_parts.append(f"[PERSONA] {persona}")
        if user_profile:
            header_parts.append(f"[USER] {json.dumps(user_profile)[:1000]}")
        if metadata:
            header_parts.append(f"[META] {json.dumps(metadata)[:1000]}")
        
        if header_parts:
            history.append({'role': 'assistant', 'content': '\n'.join(header_parts)})
        
        # Get AI response
        completion = self.sdk.complete_chat(
            history=history,
            input_text=message,
            preset=preset or sdk_config.get('default_preset', 'tutor_default')
        )
        
        ai_response = completion.get('ai_response', '')
        
        self.logger.info('Tutor response generated', {
            'studentId': self.student_id,
            'tutorId': self.tutor_id,
            'responseLength': len(ai_response)
        })
        
        # Store in session history
        if self.storage:
            now = int(time.time() * 1000)
            user_chat = SessionChat(message=message, is_reply=False, timestamp=now)
            self.storage.append_chat(self.student_id, self.tutor_id, user_chat)
            
            if ai_response:
                ai_chat = SessionChat(message=ai_response, is_reply=True, timestamp=now + 1)
                self.storage.append_chat(self.student_id, self.tutor_id, ai_chat)
        
        return ai_response
    
    def history(self) -> List[SessionChat]:
        """Get chat history for this tutor"""
        if not self.storage:
            return []
        return self.storage.list_chats(self.student_id, self.tutor_id)
    
    @property
    def ids(self) -> Dict[str, str]:
        """Get student and tutor IDs"""
        return {'student_id': self.student_id, 'tutor_id': self.tutor_id}


async def create_tutor(sdk: HenotaceAI, student_id: str, tutor_name: str = None, 
                      subject: SessionSubject = None, grade_level: str = None,
                      language: str = None, storage: Optional[StorageConnector] = None) -> Tutor:
    """
    Factory function to create a new tutor
    
    Args:
        sdk: HenotaceAI SDK instance
        student_id: Unique student identifier
        tutor_name: Optional tutor name
        subject: Optional subject information
        grade_level: Optional grade level
        language: Optional language preference
        storage: Optional storage connector
        
    Returns:
        Configured Tutor instance
    """
    logger = sdk.get_logger()
    tutor_id = tutor_name or f"tutor_{int(time.time())}"
    storage = storage or sdk.storage
    
    logger.info('Creating tutor', {
        'studentId': student_id,
        'tutorId': tutor_id,
        'tutorName': tutor_name,
        'subject': subject.name if subject else None,
        'topic': subject.topic if subject else None,
        'gradeLevel': grade_level,
        'language': language
    })
    
    # Ensure storage entries
    try:
        if storage:
            storage.upsert_student(SessionStudent(id=student_id))
            storage.upsert_tutor(student_id, SessionTutor(
                id=tutor_id,
                name=tutor_name or tutor_id,
                subject=subject or SessionSubject(id='general', name='General', topic='')
            ))
    except Exception as e:
        logger.warn('Failed to initialize storage', {'error': str(e)})
    
    # Create tutor instance
    tutor = Tutor(sdk, student_id, tutor_id, storage)
    
    # Load any previously saved context
    try:
        if storage:
            tutors = storage.list_tutors(student_id)
            existing = None
            for t in tutors:
                if t.id == tutor_id:
                    existing = t
                    break
            
            if existing and existing.context:
                tutor.set_context(existing.context)
    except Exception as e:
        logger.warn('Failed to load tutor context', {'error': str(e)})
    
    # Set initial context based on parameters
    if grade_level or language or (subject and subject.topic):
        meta = []
        if language:
            meta.append(f"Language: {language}")
        if grade_level:
            meta.append(f"Grade Level: {grade_level}")
        if subject and subject.topic:
            meta.append(f"Topic: {subject.topic}")
        
        if meta:
            tutor.set_context(meta)
    
    logger.info('Tutor created successfully', {
        'studentId': student_id,
        'tutorId': tutor_id
    })
    
    return tutor
