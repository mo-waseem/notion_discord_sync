#!/usr/bin/env python3
"""
Server runner for the Notion to Discord webhook integration service.
This script properly starts the FastAPI application using uvicorn.
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", "5000"))
    
    # Start the FastAPI app with uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )