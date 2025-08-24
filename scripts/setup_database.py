import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def setup_database():
    """Setup database tables and initial data"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
        
        # Import and create tables
        from app.database import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        print("🎉 Database setup completed!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(setup_database())
