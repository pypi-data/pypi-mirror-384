#!/usr/bin/env python3
"""
Basic usage example for the Henotace AI Python SDK
"""

import asyncio
import os
import sys
sys.path.append('..')
from src.henotace_ai import HenotaceAI, create_tutor, SessionSubject


async def main():
    # Get API key from environment variable
    api_key = os.getenv('HENOTACE_API_KEY')
    if not api_key:
        print("❌ Please set HENOTACE_API_KEY environment variable")
        return
    
    print("🚀 Starting Henotace AI Python SDK Demo")
    print("=" * 50)
    
    # Initialize the SDK
    print("📡 Initializing SDK...")
    sdk = HenotaceAI(api_key=api_key)
    
    # Check API status
    print("🔍 Checking API status...")
    try:
        if sdk.get_status_ok():
            print("✅ API is available and ready!")
        else:
            print("❌ API is not available")
            return
    except Exception as e:
        print(f"❌ Error checking API status: {e}")
        return
    
    # Create a math tutor
    print("\n👨‍🏫 Creating Math Tutor...")
    tutor = await create_tutor(
        sdk=sdk,
        student_id="demo_student_001",
        tutor_name="Math Tutor",
        subject=SessionSubject(
            id="mathematics",
            name="Mathematics",
            topic="Algebra"
        ),
        grade_level="high_school",
        language="en"
    )
    
    print(f"✅ Created tutor: {tutor.tutor_id}")
    print(f"📚 Student ID: {tutor.student_id}")
    
    # Set up the tutor with persona and context
    print("\n🎭 Setting up tutor persona...")
    tutor.set_persona(
        "You are an enthusiastic math tutor who loves to help students understand "
        "algebra. You explain concepts clearly, use examples, and encourage students "
        "to think step by step. You're patient and supportive."
    )
    
    tutor.set_context([
        "The student is learning algebra for the first time.",
        "They prefer step-by-step explanations with examples.",
        "Focus on building understanding, not just giving answers."
    ])
    
    # Interactive chat session
    print("\n💬 Starting interactive chat session...")
    print("Type 'quit' to exit the demo")
    print("-" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Thanks for trying the Henotace AI SDK!")
                break
            
            if not user_input:
                continue
            
            # Send message to tutor
            print("🤖 Tutor: ", end="", flush=True)
            response = await tutor.send(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break
    
    # Show chat history
    print(f"\n📜 Chat history ({len(tutor.history())} messages):")
    for i, chat in enumerate(tutor.history()[-5:], 1):  # Show last 5 messages
        sender = "👤 You" if not chat.is_reply else "🤖 Tutor"
        print(f"  {i}. {sender}: {chat.message[:100]}{'...' if len(chat.message) > 100 else ''}")


if __name__ == "__main__":
    asyncio.run(main())
