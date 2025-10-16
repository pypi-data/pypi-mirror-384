"""
In-memory storage connector for Henotace AI Python SDK
"""

from typing import Dict, List
from ..types import StorageConnector, SessionStudent, SessionTutor, SessionChat


class InMemoryConnector(StorageConnector):
    """
    In-memory storage connector for testing and simple use cases
    """
    
    def __init__(self):
        self.storage = {'students': []}
    
    def get_all(self) -> Dict[str, List[SessionStudent]]:
        return self.storage
    
    def set_all(self, schema: Dict[str, List[SessionStudent]]) -> None:
        self.storage = schema
    
    def list_students(self) -> List[SessionStudent]:
        return self.storage.get('students', [])
    
    def upsert_student(self, student: SessionStudent) -> None:
        students = self.storage.get('students', [])
        existing_index = None
        
        for i, s in enumerate(students):
            if s.id == student.id:
                existing_index = i
                break
        
        if existing_index is not None:
            students[existing_index] = student
        else:
            students.append(student)
        
        self.storage['students'] = students
    
    def delete_student(self, student_id: str) -> None:
        students = self.storage.get('students', [])
        self.storage['students'] = [s for s in students if s.id != student_id]
    
    def list_tutors(self, student_id: str) -> List[SessionTutor]:
        students = self.storage.get('students', [])
        for student in students:
            if student.id == student_id:
                return student.tutors
        return []
    
    def upsert_tutor(self, student_id: str, tutor: SessionTutor) -> None:
        students = self.storage.get('students', [])
        
        for student in students:
            if student.id == student_id:
                # Update existing tutor or add new one
                existing_index = None
                for i, t in enumerate(student.tutors):
                    if t.id == tutor.id:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    student.tutors[existing_index] = tutor
                else:
                    student.tutors.append(tutor)
                return
        
        # Student doesn't exist, create it
        new_student = SessionStudent(id=student_id, tutors=[tutor])
        students.append(new_student)
        self.storage['students'] = students
    
    def delete_tutor(self, student_id: str, tutor_id: str) -> None:
        students = self.storage.get('students', [])
        
        for student in students:
            if student.id == student_id:
                student.tutors = [t for t in student.tutors if t.id != tutor_id]
                return
    
    def list_chats(self, student_id: str, tutor_id: str) -> List[SessionChat]:
        tutors = self.list_tutors(student_id)
        for tutor in tutors:
            if tutor.id == tutor_id:
                return tutor.chats
        return []
    
    def append_chat(self, student_id: str, tutor_id: str, chat: SessionChat) -> None:
        tutors = self.list_tutors(student_id)
        for tutor in tutors:
            if tutor.id == tutor_id:
                tutor.chats.append(chat)
                self.upsert_tutor(student_id, tutor)
                return
        
        # Tutor doesn't exist, create it
        new_tutor = SessionTutor(
            id=tutor_id,
            name=tutor_id,
            subject=SessionSubject(id='unknown', name='Unknown', topic=''),
            chats=[chat]
        )
        self.upsert_tutor(student_id, new_tutor)
    
    def replace_chats(self, student_id: str, tutor_id: str, chats: List[SessionChat]) -> None:
        tutors = self.list_tutors(student_id)
        for tutor in tutors:
            if tutor.id == tutor_id:
                tutor.chats = chats
                self.upsert_tutor(student_id, tutor)
                return
