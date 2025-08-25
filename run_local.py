#!/usr/bin/env python3
"""
Local development startup script for AI Product Council Backend
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print("⚠️  No .env file found. Using system environment variables.")

# Check for required environment variables
required_vars = ['GOOGLE_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please create a .env file with the required variables.")
    print("You can copy from env.example and fill in your values.")
    sys.exit(1)

# Set default values for development
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite:///./ai_council.db'
    print("📊 Using SQLite database for local development")

if not os.getenv('REDIS_URL'):
    os.environ['REDIS_URL'] = 'redis://localhost:6379'
    print("🔴 Using local Redis (make sure Redis is running)")

if not os.getenv('CORS_ORIGINS'):
    os.environ['CORS_ORIGINS'] = '["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]'
    print("🌐 CORS configured for local frontend development")

print("🚀 Starting AI Product Council Backend...")
print(f"📡 API will be available at: http://localhost:8000")
print(f"📚 Documentation: http://localhost:8000/docs")
print(f"🏥 Health check: http://localhost:8000/health")

# Import and run the FastAPI app
try:
    import uvicorn
    from app.main import app
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting server: {e}")
    sys.exit(1)
