AI Product  - Backend Development Plan
This document outlines the step-by-step process for building the robust FastAPI backend for our Multi-Agent AI system. Our goal is to create a fast, scalable, and reliable service that will power our winning frontend experience.

Phase 0: Project Setup & Foundation
First, let's set up our development environment. A clean setup is crucial for speed and avoiding bugs.

1. Create the Project Directory:

mkdir ai-product-council-backend
cd ai-product-council-backend


2. Set Up a Python Virtual Environment:

This isolates our project's dependencies.

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`


3. Install Dependencies:

We'll install FastAPI for the server, Uvicorn to run it, LangChain for our AI logic, and a few other essentials.

pip install fastapi uvicorn python-dotenv langchain langchain-google-genai pydantic


4. Create the File Structure:

A logical structure makes development much easier.

/ai-product-council-backend
├── /app/
│   ├── __init__.py
│   ├── main.py           # Our main FastAPI app file
│   ├── agents.py         # Logic for our AI agents
│   ├── schemas.py        # Pydantic schemas for data validation
│   └── services.py       # Business logic and agent orchestration
├── .env                  # To store our secret API keys
└── requirements.txt      # To list our dependencies


5. Set Up Environment Variables:

Create a file named .env in the root directory. This is where you'll put your Gemini API key. Never commit this file to Git.

# .env
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"


Phase 1: Defining the Agents & Data Structures
Now, let's define the "brains" of our operation: the AI agents and the data they will output.

1. Define the Output Schema (app/schemas.py):

This tells LangChain exactly what JSON structure we want back from our final agent. Using Pydantic ensures our data is always clean and predictable.

# app/schemas.py
from pydantic import BaseModel, Field
from typing import List

class AgentFeedback(BaseModel):
    agent_name: str = Field(description="Name of the AI agent providing the feedback.")
    feedback: str = Field(description="The detailed feedback or analysis from the agent.")

class RefinedProductRequirement(BaseModel):
    refined_requirement: str = Field(description="The final, detailed, and actionable product requirement.")
    key_changes_summary: List[str] = Field(description="A bulleted list summarizing the most critical changes made to the original idea.")
    user_stories: List[str] = Field(description="Clear, structured user stories in the format 'As a [user], I want [action], so that [benefit].'")
    technical_tasks: List[str] = Field(description="A list of high-level technical tasks for the development team.")
    agent_debate: List[AgentFeedback] = Field(description="A log of the conversation and feedback from each agent.")


2. Create the Agent Logic (app/agents.py):

Here, we'll create the prompts and chains for each specialized agent.

# app/agents.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from .schemas import RefinedProductRequirement

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

# --- AGENT 1: PRODUCT MANAGER ---
pm_prompt = PromptTemplate.from_template(
    """
    ROLE: You are a world-class Product Manager.
    TASK: Analyze the following raw product idea and refine it. Focus on the user value, target audience, and potential user stories.
    IDEA: {idea}
    """
)
pm_chain = pm_prompt | llm

# --- AGENT 2: DEVELOPER ---
dev_prompt = PromptTemplate.from_template(
    """
    ROLE: You are a pragmatic Senior Software Engineer.
    TASK: Analyze the following product requirement from a technical perspective. Identify potential technical challenges, required data models, and high-level tasks.
    REQUIREMENT: {requirement}
    """
)
dev_chain = dev_prompt | llm

# --- AGENT 3: MARKET ANALYST ---
market_prompt = PromptTemplate.from_template(
    """
    ROLE: You are a sharp Market Analyst.
    TASK: Analyze the following product idea for market fit and competitive advantages. Identify key differentiators.
    IDEA: {idea}
    """
)
market_chain = market_prompt | llm

# --- FINAL AGENT: THE SYNTHESIZER ---
def get_synthesizer_chain():
    parser = PydanticOutputParser(pydantic_object=RefinedProductRequirement)

    synthesizer_prompt = PromptTemplate(
        template="""
        ROLE: You are an expert Technical Program Manager.
        TASK: Synthesize the original idea and the feedback from the Product Manager, Developer, and Market Analyst into a single, structured requirement document.
        ORIGINAL IDEA: {idea}
        PRODUCT MANAGER FEEDBACK: {pm_feedback}
        DEVELOPER FEEDBACK: {dev_feedback}
        MARKET ANALYST FEEDBACK: {market_feedback}

        {format_instructions}
        """,
        input_variables=["idea", "pm_feedback", "dev_feedback", "market_feedback"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    return synthesizer_prompt | llm | parser


Phase 2: Building the API Endpoint
Let's create the FastAPI server and the endpoint that will orchestrate our agents.

1. Create the Orchestration Logic (app/services.py):

This service will run the agents in sequence and gather their feedback.

# app/services.py
from .agents import pm_chain, dev_chain, market_chain, get_synthesizer_chain

async def refine_requirement(idea: str):
    # Run agents in parallel for efficiency where possible
    pm_feedback = await pm_chain.ainvoke({"idea": idea})
    market_feedback = await market_chain.ainvoke({"idea": idea})

    # The developer agent needs the PM's feedback
    dev_feedback = await dev_chain.ainvoke({"requirement": pm_feedback.content})

    # Run the final synthesizer
    synthesizer_chain = get_synthesizer_chain()
    final_result = await synthesizer_chain.ainvoke({
        "idea": idea,
        "pm_feedback": pm_feedback.content,
        "dev_feedback": dev_feedback.content,
        "market_feedback": market_feedback.content
    })

    return final_result


2. Create the Main App and Endpoint (app/main.py):

This is our main server file.

# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from .services import refine_requirement
from .schemas import RefinedProductRequirement

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="AI Product Council API",
    description="An API for refining product requirements using a multi-agent AI system."
)

class RefineRequest(BaseModel):
    idea: str

@app.post("/refine", response_model=RefinedProductRequirement)
async def refine_product_idea(request: RefineRequest):
    """
    Accepts a raw product idea and returns a structured, refined requirement.
    """
    if not request.idea.strip():
        raise HTTPException(status_code=400, detail="Product idea cannot be empty.")
    try:
        result = await refine_requirement(request.idea)
        return result
    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Failed to refine the product requirement.")

@app.get("/")
def read_root():
    return {"status": "AI Product Council API is running."}


Phase 3: Running and Testing
Now, let's bring our backend to life.

1. Run the Server:

From your root directory (ai-product-council-backend), run the following command in your terminal:

uvicorn app.main:app --reload


--reload will automatically restart the server whenever you save a file, which is great for development.

2. Test the Endpoint:

You can use a tool like Postman, Insomnia, or the command-line tool curl to test your API.

Using curl:

curl -X POST "http://127.0.0.1:8000/refine" \
-H "Content-Type: application/json" \
-d '{"idea": "a feature to let users save their favorite items in an e-commerce app"}'


You should receive a beautifully structured JSON response with the refined requirement, user stories, and all the other details.

You now have a fully functional, robust, and scalable backend for the AI Product Council. The next step is to connect this API to your stunning Next.js frontend.
