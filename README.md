# AI Product Council Backend

A robust, production-ready FastAPI backend that uses multiple AI agents to refine product requirements and ideas.

## Features

- **Multi-Agent AI System**: Product Manager, Developer, and Market Analyst agents
- **Async Processing**: Background task processing with status tracking
- **Database Integration**: SQLAlchemy with session management
- **Structured Logging**: JSON-formatted logs with request tracing
- **Rate Limiting**: Built-in protection against abuse
- **Health Checks**: Comprehensive system health monitoring
- **Docker Support**: Full containerization with docker-compose
- **Error Handling**: Robust error handling with retry logic
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Quick Start

1. **Clone and Setup**:
   \`\`\`bash
   git clone <your-repo>
   cd ai-product-council-backend
   cp .env.example .env
   # Edit .env with your API keys
   \`\`\`

2. **Install Dependencies**:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Run the Server**:
   \`\`\`bash
   uvicorn app.main:app --reload
   \`\`\`

4. **Test the API**:
   \`\`\`bash
   curl -X POST "http://localhost:8000/refine/sync" \
   -H "Content-Type: application/json" \
   -d '{"idea": "A mobile app for tracking daily habits with AI coaching"}'
   \`\`\`

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /refine` - Async refinement (returns session ID)
- `POST /refine/sync` - Sync refinement (returns result immediately)
- `GET /refine/{session_id}` - Get refinement status/results
- `GET /refine` - List recent refinements
- `GET /docs` - Interactive API documentation

## Docker Deployment

\`\`\`bash
docker-compose up -d
\`\`\`

This starts the API, PostgreSQL database, and Redis cache.

## Architecture

The system uses a multi-agent approach:

1. **Product Manager Agent**: Focuses on user value and market fit
2. **Developer Agent**: Analyzes technical feasibility and architecture
3. **Market Analyst Agent**: Evaluates competitive landscape and business viability
4. **Synthesizer**: Combines all feedback into structured requirements

## Configuration

Key environment variables:

- `GOOGLE_API_KEY`: Required for Gemini AI
- `DATABASE_URL`: Database connection string
- `RATE_LIMIT_REQUESTS`: Requests per hour per IP
- `LOG_LEVEL`: Logging verbosity

## Production Considerations

- Set strong `SECRET_KEY` in production
- Configure CORS origins appropriately
- Use PostgreSQL instead of SQLite
- Set up proper logging aggregation
- Configure reverse proxy (nginx/traefik)
- Set up monitoring and alerting

## Development

Run tests and create sample data:

\`\`\`bash
python scripts/create_sample_data.py
\`\`\`

The API includes comprehensive error handling, structured logging, and monitoring capabilities for production use.
