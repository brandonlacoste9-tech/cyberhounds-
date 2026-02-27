"""
Cyberhound Web API
Connects the website to the main Cyberhound hunting system
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Cyberhound Web", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CYBERHOUND_PATH = Path.home() / "Cyberhound"
LE_BUTIN_PATH = CYBERHOUND_PATH / "LE_BUTIN.json"

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class DeployRequest(BaseModel):
    pack: str  # "req", "labor", "tech", or "all"
    bridge: Optional[str] = "ws://localhost:8080"

class ForgeRequest(BaseModel):
    lead_id: str
    lead_data: dict

class StrikeRequest(BaseModel):
    to: str
    subject: str
    body: str

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the landing page"""
    html_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(content="<h1>Cyberhound Web</h1><p>Frontend not found</p>")

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CONNECTION TO MAIN CYBERHOUND SYSTEM
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@app.get("/api/hunts")
async def get_hunts():
    """Fetch hunts from main Cyberhound system (LE_BUTIN.json)"""
    try:
        if LE_BUTIN_PATH.exists():
            with open(LE_BUTIN_PATH) as f:
                data = json.load(f)
            return {
                "status": "success",
                "source": str(LE_BUTIN_PATH),
                "data": data
            }
        else:
            return {
                "status": "empty",
                "message": "No hunts yet. Deploy scouts first.",
                "data": {"bounties": [], "total_bounties": 0}
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get statistics from main system"""
    try:
        if LE_BUTIN_PATH.exists():
            with open(LE_BUTIN_PATH) as f:
                data = json.load(f)
            return {
                "total_bounties": data.get("total_bounties", 0),
                "by_type": data.get("bounties_by_type", {}),
                "last_update": data.get("started_at", "unknown")
            }
        return {"total_bounties": 0, "by_type": {}, "status": "no_data"}
    except Exception as e:
        return {"error": str(e), "total_bounties": 0}

@app.post("/api/deploy")
async def deploy_scouts(request: DeployRequest):
    """Deploy scout pack to main Cyberhound system"""
    try:
        # This calls the main Cyberhound system
        cmd = [
            "python3",
            str(CYBERHOUND_PATH / "agent_swarm_trigger.py"),
            "--pack", request.pack
        ]
        
        # Run asynchronously (don't wait for completion)
        subprocess.Popen(
            cmd,
            cwd=CYBERHOUND_PATH,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return {
            "status": "deployed",
            "pack": request.pack,
            "message": f"Deploying {request.pack} pack to Cyberhound main system",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forge")
async def forge_solution(request: ForgeRequest):
    """Generate solution via main Cyberhound forge_engine"""
    try:
        cmd = [
            "python3",
            str(CYBERHOUND_PATH / "forge_engine.py"),
            "--lead", json.dumps(request.lead_data)
        ]
        
        result = subprocess.run(
            cmd,
            cwd=CYBERHOUND_PATH,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {
                "status": "forged",
                "lead_id": request.lead_id,
                "solution": json.loads(result.stdout)
            }
        else:
            return {
                "status": "error",
                "error": result.stderr
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strike")
async def send_strike(request: StrikeRequest):
    """Send strike via main Cyberhound envoy_bot"""
    try:
        cmd = [
            "python3",
            str(CYBERHOUND_PATH / "envoy_bot.py"),
            "--to", request.to,
            "--subject", request.subject,
            "--body", request.body
        ]
        
        result = subprocess.run(
            cmd,
            cwd=CYBERHOUND_PATH,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "status": "sent" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr if result.stderr else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

@app.get("/api/health")
async def health_check():
    """Check connection to main Cyberhound system"""
    cyberhound_exists = CYBERHOUND_PATH.exists()
    le_butin_exists = LE_BUTIN_PATH.exists()
    
    return {
        "web_status": "operational",
        "cyberhound_path": str(CYBERHOUND_PATH),
        "cyberhound_exists": cyberhound_exists,
        "le_butin_exists": le_butin_exists,
        "connection_status": "connected" if cyberhound_exists else "disconnected"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
