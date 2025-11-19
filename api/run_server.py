#!/usr/bin/env python3
"""
FastAPI Server Launcher for AI Research Assistant
Run this file to start the API server
"""

import uvicorn
import sys
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("="*80)
    print("🚀 Starting AI Research Assistant API Server")
    print("="*80)
    print("\n📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📊 Alternative docs: http://localhost:8000/redoc")
    print("\n⏹️  Press CTRL+C to stop the server\n")
    print("="*80 + "\n")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )