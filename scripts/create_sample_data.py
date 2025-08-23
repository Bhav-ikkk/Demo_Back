import asyncio
import sys
import os

# Add the parent directory to the path so we can import our app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.services import refinement_service

async def create_sample_refinements():
    """Create some sample refinement sessions for testing"""
    
    db = SessionLocal()
    
    sample_ideas = [
        "A mobile app that helps users track their daily water intake with gamification elements",
        "An AI-powered code review tool that integrates with GitHub and provides intelligent suggestions",
        "A platform for small businesses to manage their social media presence across multiple channels",
        "A virtual reality fitness app that makes working out feel like playing video games",
        "A collaborative whiteboard tool specifically designed for remote software development teams"
    ]
    
    try:
        for idea in sample_ideas:
            print(f"Creating refinement for: {idea[:50]}...")
            
            # Create session
            session = await refinement_service.create_refinement_session(db, idea)
            
            # Process refinement
            try:
                result = await refinement_service.process_refinement(db, session.id, idea)
                print(f"✅ Successfully refined session {session.id}")
            except Exception as e:
                print(f"❌ Failed to refine session {session.id}: {e}")
        
        print("\n🎉 Sample data creation completed!")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_sample_refinements())
