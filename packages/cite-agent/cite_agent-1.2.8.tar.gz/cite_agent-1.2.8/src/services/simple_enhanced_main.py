"""
Simple Enhanced Main Application - Working version with core capabilities
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import our enhanced services
from services.reasoning_engine.reasoning_engine import ReasoningEngine
from services.tool_framework.tool_manager import ToolManager
from services.context_manager.advanced_context import AdvancedContextManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nocturnal Archive API - Enhanced",
    description="Production-grade AI-powered research platform with advanced reasoning capabilities",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize enhanced services
tool_manager = ToolManager()
context_manager = AdvancedContextManager()
reasoning_engine = ReasoningEngine()

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_advanced_reasoning: Optional[bool] = True

class ResearchRequest(BaseModel):
    topic: str
    max_results: Optional[int] = 10
    use_advanced_reasoning: Optional[bool] = True

class ReasoningRequest(BaseModel):
    problem_description: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class ToolExecutionRequest(BaseModel):
    tool_name: Optional[str] = None
    task_description: str
    context: Optional[Dict[str, Any]] = None
    auto_select_tool: Optional[bool] = True

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Nocturnal Archive API - Enhanced",
        "version": "3.0.0",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "capabilities": [
            "Advanced Reasoning Engine",
            "Dynamic Tool Framework", 
            "Code Execution Environment",
            "Advanced Context Management",
            "Academic Research & Synthesis",
            "Multi-LLM Integration"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "timestamp": _utc_timestamp(),
        "services": {
            "reasoning_engine": "operational",
            "tool_framework": "operational",
            "context_manager": "operational"
        }
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "operational",
        "services": {
            "reasoning": "operational",
            "tools": "operational",
            "context": "operational"
        }
    }

# Enhanced Reasoning Endpoints
@app.post("/api/reasoning/solve")
async def solve_problem(request: ReasoningRequest):
    """Solve complex problems using advanced reasoning."""
    try:
        # Solve the problem using reasoning engine
        result = await reasoning_engine.solve_problem(
            problem_description=request.problem_description,
            context=request.context,
            user_id=request.user_id
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Reasoning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reasoning failed: {str(e)}")

# Enhanced Tool Framework Endpoints
@app.post("/api/tools/execute")
async def execute_tool(request: ToolExecutionRequest):
    """Execute a tool with dynamic selection."""
    try:
        # Execute tool
        if request.auto_select_tool:
            result = await tool_manager.execute_with_auto_selection(
                task_description=request.task_description,
                context=request.context
            )
        else:
            if not request.tool_name:
                raise HTTPException(status_code=400, detail="Tool name required when auto_select_tool is False")
            
            result = await tool_manager.execute_tool(
                tool_name=request.tool_name,
                task_description=request.task_description,
                context=request.context
            )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@app.get("/api/tools/available")
async def get_available_tools():
    """Get list of available tools."""
    try:
        tools = tool_manager.get_available_tools()
        tool_capabilities = {}
        
        for tool in tools:
            tool_capabilities[tool] = tool_manager.get_tool_capabilities(tool)
        
        return {
            "status": "success",
            "tools": tools,
            "capabilities": tool_capabilities
        }
    except Exception as e:
        logger.error(f"Failed to get available tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get available tools: {str(e)}")

# Enhanced Context Management Endpoints
@app.post("/api/context/process")
async def process_context(request: ChatRequest):
    """Process interaction and update context."""
    try:
        session_id = request.session_id or "default_session"
        
        # Generate response (this would integrate with existing chat logic)
        response = f"Enhanced response to: {request.message}"
        
        # Process interaction in context manager
        result = await context_manager.process_interaction(
            user_input=request.message,
            response=response,
            session_id=session_id,
            user_id="anonymous"
        )
        
        return {
            "status": "success",
            "response": response,
            "context_result": result
        }
        
    except Exception as e:
        logger.error(f"Context processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context processing failed: {str(e)}")

@app.get("/api/context/retrieve")
async def retrieve_context(query: str, session_id: Optional[str] = None):
    """Retrieve relevant context for a query."""
    try:
        result = await context_manager.retrieve_relevant_context(
            query=query,
            session_id=session_id,
            user_id="anonymous"
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Context retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")

# Enhanced Chat Endpoint with Advanced Reasoning
@app.post("/api/enhanced-chat")
async def enhanced_chat_endpoint(request: ChatRequest):
    """Enhanced chat endpoint with advanced reasoning capabilities."""
    try:
        session_id = request.session_id or "enhanced_session"
        
        # Use advanced reasoning if requested
        if request.use_advanced_reasoning:
            # Solve as a reasoning problem
            reasoning_result = await reasoning_engine.solve_problem(
                problem_description=request.message,
                context={"session_id": session_id, "user_id": "anonymous"},
                user_id="anonymous"
            )
            
            response = reasoning_result.get("solution", "No solution generated")
        else:
            # Use simple response
            response = f"Standard response to: {request.message}"
        
        # Process interaction in context manager
        await context_manager.process_interaction(
            user_input=request.message,
            response=str(response),
            session_id=session_id,
            user_id="anonymous"
        )
        
        return {
            "response": response,
            "session_id": session_id,
            "timestamp": _utc_timestamp(),
            "mode": "enhanced_reasoning" if request.use_advanced_reasoning else "standard"
        }
        
    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)