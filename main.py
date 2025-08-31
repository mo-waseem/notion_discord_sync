import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    print(os.getenv("DISCORD_LIVE_ISSUES_WEBHOOK_URL"))
    from app import app
    uvicorn.run(app, host="0.0.0.0", port=5000)
