import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def reset_database():
    """Reset database tables to match new schema"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Drop existing tables
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS agent_debates CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS agent_responses CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS refinement_sessions CASCADE"))
            conn.commit()
            print("✅ Dropped existing tables")
        
        # Import and create new tables
        from app.database import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Created new tables with updated schema")
        
        print("🎉 Database reset completed!")
        
    except Exception as e:
        print(f"❌ Database reset failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(reset_database())
