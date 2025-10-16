#!/usr/bin/env python3
"""
Advanced features example for the Henotace AI Python SDK
Demonstrates context, personas, user profiles, and metadata usage
"""

import asyncio
import os
import sys
sys.path.append('..')
from src.henotace_ai import HenotaceAI, create_tutor, SessionSubject


async def advanced_features_demo():
    """Demonstrate advanced features of the SDK"""
    
    # Get API key
    api_key = os.getenv('HENOTACE_API_KEY')
    if not api_key:
        print("❌ Please set HENOTACE_API_KEY environment variable")
        return
    
    print("🚀 Advanced Features Demo")
    print("=" * 50)
    
    # Initialize SDK
    sdk = HenotaceAI(api_key=api_key)
    
    # Check API status
    if not sdk.get_status_ok():
        print("❌ API is not available")
        return
    
    print("✅ API is available")
    
    # Create a specialized tutor
    tutor = await create_tutor(
        sdk=sdk,
        student_id="advanced_student_001",
        tutor_name="Advanced Physics Tutor",
        subject=SessionSubject(
            id="physics",
            name="Physics",
            topic="Quantum Mechanics"
        ),
        grade_level="university",
        language="en"
    )
    
    print(f"✅ Created tutor: {tutor.tutor_id}")
    
    # Set advanced persona
    print("\n🎭 Setting advanced persona...")
    tutor.set_persona("""
    You are Dr. Quantum, an expert physics professor with 20+ years of experience 
    in quantum mechanics. You have a passion for making complex physics concepts 
    accessible through analogies and real-world examples. You're patient, 
    encouraging, and love to see the 'aha!' moments in students' eyes. You always 
    break down complex problems into manageable steps and provide multiple 
    perspectives on difficult concepts.
    """)
    
    # Set comprehensive context
    print("📚 Setting comprehensive context...")
    tutor.set_context([
        "The student is a university sophomore studying quantum mechanics for the first time.",
        "They have a strong foundation in classical physics and mathematics.",
        "The student learns best through visual analogies and step-by-step derivations.",
        "Current focus: Understanding wave-particle duality and the uncertainty principle.",
        "The student prefers when concepts are connected to real-world applications."
    ])
    
    # Set detailed user profile
    print("👤 Setting user profile...")
    tutor.set_user_profile({
        "name": "Alex Chen",
        "age": 20,
        "grade": "Sophomore",
        "major": "Physics",
        "learning_style": "visual_kinesthetic",
        "difficulty_level": "intermediate_advanced",
        "interests": ["astrophysics", "quantum_computing", "mathematical_physics"],
        "previous_knowledge": ["classical_mechanics", "thermodynamics", "electromagnetism"],
        "goals": ["understand_quantum_foundations", "prepare_for_advanced_courses"],
        "preferred_examples": ["practical_applications", "historical_context", "mathematical_derivations"]
    })
    
    # Set metadata for tracking
    print("📊 Setting metadata...")
    tutor.set_metadata({
        "course_code": "PHYS-301",
        "semester": "Fall 2024",
        "instructor": "Dr. Quantum",
        "textbook": "Griffiths Introduction to Quantum Mechanics",
        "session_type": "tutoring",
        "difficulty_target": "university_level",
        "learning_objectives": [
            "Understand wave-particle duality",
            "Master the uncertainty principle",
            "Apply quantum mechanics to simple systems"
        ]
    })
    
    # Demonstrate conversation with rich context
    print("\n💬 Starting advanced conversation...")
    print("-" * 50)
    
    # First message - introducing the topic
    response = await tutor.send(
        "Hi Dr. Quantum! I'm struggling to understand wave-particle duality. "
        "How can light be both a wave and a particle? It seems contradictory.",
        context="This is our first session on quantum mechanics. The student has been reading about the double-slit experiment."
    )
    print(f"👤 Student: Hi Dr. Quantum! I'm struggling to understand wave-particle duality...")
    print(f"🤖 Dr. Quantum: {response}")
    print()
    
    # Second message - follow-up question
    response = await tutor.send(
        "That analogy with the water waves and boats was helpful! But what about the "
        "uncertainty principle? How does that relate to wave-particle duality?",
        context="The student seems to be making connections between concepts."
    )
    print(f"👤 Student: That analogy with the water waves and boats was helpful! But what about the uncertainty principle...")
    print(f"🤖 Dr. Quantum: {response}")
    print()
    
    # Third message - asking for mathematical explanation
    response = await tutor.send(
        "Can you show me the mathematical formulation of the uncertainty principle? "
        "I'd like to see how it's derived.",
        context="The student is ready for mathematical details after understanding the conceptual framework."
    )
    print(f"👤 Student: Can you show me the mathematical formulation of the uncertainty principle...")
    print(f"🤖 Dr. Quantum: {response}")
    print()
    
    # Show conversation history
    print("\n📜 Conversation History:")
    history = tutor.history()
    for i, chat in enumerate(history, 1):
        sender = "👤 Student" if not chat.is_reply else "🤖 Dr. Quantum"
        preview = chat.message[:100] + "..." if len(chat.message) > 100 else chat.message
        print(f"  {i}. {sender}: {preview}")
    
    print(f"\n✅ Demo completed! Total messages: {len(history)}")


async def compression_demo():
    """Demonstrate chat history compression"""
    
    api_key = os.getenv('HENOTACE_API_KEY')
    if not api_key:
        return
    
    print("\n🗜️  Chat History Compression Demo")
    print("=" * 50)
    
    sdk = HenotaceAI(api_key=api_key)
    
    # Create tutor with compression settings
    tutor = await create_tutor(
        sdk=sdk,
        student_id="compression_demo",
        tutor_name="Compression Demo Tutor"
    )
    
    # Configure compression
    tutor.set_compression(
        max_turns=5,  # Keep only 5 recent messages
        max_summary_chars=500,  # Limit summary to 500 characters
        checkpoint_every=3  # Compress every 3 messages
    )
    
    # Simulate a long conversation
    topics = [
        "What is gravity?",
        "How does gravity work on Earth?",
        "What about gravity in space?",
        "Can you explain black holes?",
        "How do black holes form?",
        "What happens inside a black hole?",
        "Tell me about Hawking radiation.",
        "How does Hawking radiation work?",
        "What's the information paradox?",
        "Can you explain quantum entanglement?",
        "How does quantum entanglement relate to black holes?",
        "What are wormholes?",
    ]
    
    print("📝 Simulating long conversation...")
    
    for i, topic in enumerate(topics, 1):
        response = await tutor.send(f"Question {i}: {topic}")
        print(f"  Message {i}: {len(tutor.history())} total messages")
        
        # Show compression in action
        if len(tutor.history()) > 8:
            print(f"    🔄 Auto-compression triggered!")
    
    print(f"\n✅ Final history length: {len(tutor.history())} messages")
    print("   (Old messages were compressed into summaries)")


if __name__ == "__main__":
    async def main():
        await advanced_features_demo()
        await compression_demo()
    
    asyncio.run(main())
