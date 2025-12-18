
# import sys
# from datetime import datetime
# from typing import List, Optional

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# try:
#     from .crew import LlmCouncil
# except ImportError:
#     from crew import LlmCouncil

# # ============================================
# # FastAPI Setup
# # ============================================
# app = FastAPI(
#     title="LLM Council API",
#     description="Multi-model AI council API",
#     version="1.0.0"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Request/Response Models
# class QuestionRequest(BaseModel):
#     question: str

# class SimpleResponse(BaseModel):
#     question: str
#     answer: str
#     timestamp: str
#     execution_time: float

# class TaskOutput(BaseModel):
#     agent: str
#     task_name: str
#     output: str

# class DetailedResponse(BaseModel):
#     question: str
#     timestamp: str
#     individual_outputs: List[TaskOutput]
#     final_answer: str
#     execution_time: float

# # ============================================
# # FastAPI Endpoints
# # ============================================
# @app.get("/")
# def root():
#     return {
#         "message": "LLM Council API",
#         "version": "1.0.0",
#         "endpoints": {
#             "POST /ask": "Get final answer only",
#             "POST /ask/detailed": "Get all outputs including critiques",
#             "GET /health": "Health check",
#             "GET /docs": "API documentation"
#         }
#     }

# @app.get("/health")
# def health_check():
#     return {"status": "healthy"}

# @app.post("/ask", response_model=SimpleResponse)
# def ask_council(request: QuestionRequest):
#     """Submit a question and get the final synthesized answer"""
    
#     if not request.question.strip():
#         raise HTTPException(status_code=400, detail="Question cannot be empty")
    
#     try:
#         start_time = datetime.now()
        
#         # Create and execute crew
#         llm_council = LlmCouncil()
#         crew = llm_council.crew()
#         result = crew.kickoff(inputs={"question": request.question})
        
#         execution_time = (datetime.now() - start_time).total_seconds()
        
#         return SimpleResponse(
#             question=request.question,
#             answer=str(result),
#             timestamp=start_time.isoformat(),
#             execution_time=execution_time
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/ask/detailed", response_model=DetailedResponse)
# def ask_council_detailed(request: QuestionRequest):
#     """Submit a question and get all outputs (initial answers + critiques + final)"""
    
#     if not request.question.strip():
#         raise HTTPException(status_code=400, detail="Question cannot be empty")
    
#     try:
#         start_time = datetime.now()
        
#         # Create and execute crew
#         llm_council = LlmCouncil()
#         crew = llm_council.crew()
#         result = crew.kickoff(inputs={"question": request.question})
        
#         # Extract outputs
#         task_names = [
#             "GPT Initial Answer",
#             "Claude Initial Answer", 
#             "Gemini Initial Answer",
#             "GPT Critique",
#             "Claude Critique",
#             "Gemini Critique",
#             "Chairman Synthesis"
#         ]
        
#         individual_outputs = []
#         for i, task in enumerate(crew.tasks):
#             output_text = task.output.raw if hasattr(task.output, 'raw') else str(task.output)
#             individual_outputs.append(TaskOutput(
#                 agent=task.agent.role,
#                 task_name=task_names[i] if i < len(task_names) else f"Task {i+1}",
#                 output=output_text
#             ))
        
#         execution_time = (datetime.now() - start_time).total_seconds()
        
#         return DetailedResponse(
#             question=request.question,
#             timestamp=start_time.isoformat(),
#             individual_outputs=individual_outputs,
#             final_answer=str(result),
#             execution_time=execution_time
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # ============================================
# # CLI Functions
# # ============================================
# def run():
#     """Run the crew in CLI mode"""
#     print("LLM Council - Multi-Model Answer System")
#     print("=" * 50)
    
#     user_question = input("> ")
    
#     if not user_question.strip():
#         print("Error: Please provide a question.")
#         sys.exit(1)
    
#     print(f"\nProcessing question: {user_question}\n")
    
#     llm_council = LlmCouncil()
#     result = llm_council.crew().kickoff(inputs={"question": user_question})
    
#     print("\n" + "=" * 50)
#     print("===== FINAL OUTPUT =====")
#     print("=" * 50)
#     print(result)
#     print("=" * 50)

# def serve():
#     """Start the FastAPI server"""
#     import uvicorn
#     print("🚀 Starting LLM Council API Server...")
#     print("📖 API Docs: http://localhost:8000/docs")
#     print("🏥 Health Check: http://localhost:8000/health")
#     print("\nPress CTRL+C to stop\n")
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# # ============================================
# # Main Entry Point
# # ============================================
# if __name__ == "__main__":
#     if len(sys.argv) > 1 and sys.argv[1] == "serve":
#         serve()
#     else:
#         run()


"""
Rate limiting implementation for LLM Council API
Install: pip install slowapi redis
"""

import sys
from datetime import datetime
from typing import List, Optional
import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

try:
    from .crew import LlmCouncil
except ImportError:
    from crew import LlmCouncil

# ============================================
# Rate Limiting Setup
# ============================================
# Option 1: In-memory rate limiting (simpler, single instance)
limiter = Limiter(key_func=get_remote_address)

# Option 2: Redis-based (for production with multiple instances)
# from slowapi.util import get_remote_address
# limiter = Limiter(
#     key_func=get_remote_address,
#     storage_uri="redis://localhost:6379"
# )

# ============================================
# Concurrent Request Limiter
# ============================================
class ConcurrentRequestLimiter:
    """Limit total concurrent requests to prevent resource exhaustion"""
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests = 0
    
    async def __aenter__(self):
        self.active_requests += 1
        await self.semaphore.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()
        self.active_requests -= 1
    
    def get_active_count(self):
        return self.active_requests

# Global concurrent limiter (max 5 questions being processed at once)
concurrent_limiter = ConcurrentRequestLimiter(max_concurrent=5)

# ============================================
# FastAPI Setup
# ============================================
app = FastAPI(
    title="LLM Council API",
    description="Multi-model AI council API with rate limiting",
    version="1.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
    rate_limit_info: Optional[dict] = None

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
    rate_limit_info: Optional[dict] = None

# ============================================
# FastAPI Endpoints
# ============================================
@app.get("/")
def root():
    return {
        "message": "LLM Council API",
        "version": "1.0.0",
        "rate_limits": {
            "per_user": "10 requests per hour",
            "concurrent": "5 max concurrent requests",
            "cost_per_question": "7 LLM API calls"
        },
        "endpoints": {
            "POST /ask": "Get final answer only (rate limited)",
            "POST /ask/detailed": "Get all outputs (rate limited)",
            "GET /health": "Health check",
            "GET /status": "Rate limit status",
            "GET /docs": "API documentation"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/status")
def status_check(request: Request):
    """Check current rate limit status"""
    return {
        "active_concurrent_requests": concurrent_limiter.get_active_count(),
        "max_concurrent_requests": 5,
        "your_ip": get_remote_address(request),
        "rate_limit": "10 requests per hour per IP"
    }

@app.post("/ask", response_model=SimpleResponse)
@limiter.limit("10/hour")  # 10 requests per hour per IP
async def ask_council(request: Request, question_req: QuestionRequest):
    """
    Submit a question and get the final synthesized answer
    
    Rate Limits:
    - 10 requests per hour per IP address
    - Max 5 concurrent requests across all users
    """
    
    if not question_req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Check concurrent request limit
    if concurrent_limiter.active_requests >= 5:
        raise HTTPException(
            status_code=429,
            detail="Server is at capacity. Please try again in a moment."
        )
    
    try:
        async with concurrent_limiter:
            start_time = datetime.now()
            
            # Create and execute crew (this runs in executor to avoid blocking)
            llm_council = LlmCouncil()
            crew = llm_council.crew()
            result = await asyncio.to_thread(
                crew.kickoff,
                inputs={"question": question_req.question}
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return SimpleResponse(
                question=question_req.question,
                answer=str(result),
                timestamp=start_time.isoformat(),
                execution_time=execution_time,
                rate_limit_info={
                    "limit": "10 per hour",
                    "ip": get_remote_address(request)
                }
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/detailed", response_model=DetailedResponse)
@limiter.limit("5/hour")  # Stricter limit for detailed endpoint (more data)
async def ask_council_detailed(request: Request, question_req: QuestionRequest):
    """
    Submit a question and get all outputs (initial answers + critiques + final)
    
    Rate Limits:
    - 5 requests per hour per IP address (stricter than /ask)
    - Max 5 concurrent requests across all users
    """
    
    if not question_req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Check concurrent request limit
    if concurrent_limiter.active_requests >= 5:
        raise HTTPException(
            status_code=429,
            detail="Server is at capacity. Please try again in a moment."
        )
    
    try:
        async with concurrent_limiter:
            start_time = datetime.now()
            
            # Create and execute crew
            llm_council = LlmCouncil()
            crew = llm_council.crew()
            result = await asyncio.to_thread(
                crew.kickoff,
                inputs={"question": question_req.question}
            )
            
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
                question=question_req.question,
                timestamp=start_time.isoformat(),
                individual_outputs=individual_outputs,
                final_answer=str(result),
                execution_time=execution_time,
                rate_limit_info={
                    "limit": "5 per hour",
                    "ip": get_remote_address(request)
                }
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
    print("⚡ Rate Limiting Enabled:")
    print("   • 10 requests/hour per IP (/ask)")
    print("   • 5 requests/hour per IP (/ask/detailed)")
    print("   • Max 5 concurrent requests")
    print("\n📖 API Docs: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print("📊 Status: http://localhost:8000/status")
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