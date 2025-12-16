

# from crew import LlmCouncil

# def run_council():
#     # Ask question from user directly
#     user_question = input("\nEnter your question for the LLM Council:\n> ").strip()
    
#     if not user_question:
#         print("Error: Please provide a question.")
#         return

#     # Create LlmCouncil instance
#     llm_council = LlmCouncil()
#     crew = llm_council.crew()

#     # CrewAI requires dict input
#     result = crew.kickoff(inputs={"question": user_question})

#     # Show individual outputs from gather phase
#     print("\n" + "="*60)
#     print("=== INDIVIDUAL MODEL OUTPUTS (Gather Phase) ===")
#     print("="*60)
    
#     # First 3 tasks are gather tasks (gpt, claude, gemini)
#     gather_tasks = crew.tasks[:3]
    
#     for task in gather_tasks:
#         print(f"\n{'='*60}")
#         print(f"📝 {task.agent.role}")
#         print(f"{'='*60}")
#         print(task.output.raw if hasattr(task.output, 'raw') else task.output)

#     # Show final synthesized answer
#     print("\n" + "="*60)
#     print("===== FINAL SYNTHESIZED OUTPUT =====")
#     print("="*60)
#     print(result)
#     print("="*60 + "\n")

# if __name__ == "__main__":
#     run_council()


#!/usr/bin/env python
import sys
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .crew import LlmCouncil
except ImportError:
    from crew import LlmCouncil

# ============================================
# FastAPI Setup
# ============================================
app = FastAPI(
    title="LLM Council API",
    description="Multi-model AI council API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class QuestionRequest(BaseModel):
    question: str

class SimpleResponse(BaseModel):
    question: str
    answer: str
    timestamp: str
    execution_time: float

class TaskOutput(BaseModel):
    agent: str
    task_name: str
    output: str

class DetailedResponse(BaseModel):
    question: str
    timestamp: str
    individual_outputs: List[TaskOutput]
    final_answer: str
    execution_time: float

# ============================================
# FastAPI Endpoints
# ============================================
@app.get("/")
def root():
    return {
        "message": "LLM Council API",
        "version": "1.0.0",
        "endpoints": {
            "POST /ask": "Get final answer only",
            "POST /ask/detailed": "Get all outputs including critiques",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/ask", response_model=SimpleResponse)
def ask_council(request: QuestionRequest):
    """Submit a question and get the final synthesized answer"""
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        start_time = datetime.now()
        
        # Create and execute crew
        llm_council = LlmCouncil()
        crew = llm_council.crew()
        result = crew.kickoff(inputs={"question": request.question})
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return SimpleResponse(
            question=request.question,
            answer=str(result),
            timestamp=start_time.isoformat(),
            execution_time=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/detailed", response_model=DetailedResponse)
def ask_council_detailed(request: QuestionRequest):
    """Submit a question and get all outputs (initial answers + critiques + final)"""
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        start_time = datetime.now()
        
        # Create and execute crew
        llm_council = LlmCouncil()
        crew = llm_council.crew()
        result = crew.kickoff(inputs={"question": request.question})
        
        # Extract outputs
        task_names = [
            "GPT Initial Answer",
            "Claude Initial Answer", 
            "Gemini Initial Answer",
            "GPT Critique",
            "Claude Critique",
            "Gemini Critique",
            "Chairman Synthesis"
        ]
        
        individual_outputs = []
        for i, task in enumerate(crew.tasks):
            output_text = task.output.raw if hasattr(task.output, 'raw') else str(task.output)
            individual_outputs.append(TaskOutput(
                agent=task.agent.role,
                task_name=task_names[i] if i < len(task_names) else f"Task {i+1}",
                output=output_text
            ))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return DetailedResponse(
            question=request.question,
            timestamp=start_time.isoformat(),
            individual_outputs=individual_outputs,
            final_answer=str(result),
            execution_time=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CLI Functions
# ============================================
def run():
    """Run the crew in CLI mode"""
    print("LLM Council - Multi-Model Answer System")
    print("=" * 50)
    
    user_question = input("> ")
    
    if not user_question.strip():
        print("Error: Please provide a question.")
        sys.exit(1)
    
    print(f"\nProcessing question: {user_question}\n")
    
    llm_council = LlmCouncil()
    result = llm_council.crew().kickoff(inputs={"question": user_question})
    
    print("\n" + "=" * 50)
    print("===== FINAL OUTPUT =====")
    print("=" * 50)
    print(result)
    print("=" * 50)

def serve():
    """Start the FastAPI server"""
    import uvicorn
    print("🚀 Starting LLM Council API Server...")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print("\nPress CTRL+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============================================
# Main Entry Point
# ============================================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve()
    else:
        run()