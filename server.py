import os
import json
import glob
import base64
import numpy as np
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional

from pcd_loader import load_pcd
from calibration_utils import project_points

app = FastAPI()

DATA_DIR = "data/test_2025-11-18-14-32-34/paired"
CONFIG_FILE = "config.json"

# Load Config
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Cache for PCD data to avoid reloading
pcd_cache = {}

@app.get("/api/frames")
def get_frames():
    # List all frames based on port_1 images
    # Assuming filenames match across folders
    port1_dir = os.path.join(DATA_DIR, "port_1")
    if not os.path.exists(port1_dir):
        return []
    files = sorted(glob.glob(os.path.join(port1_dir, "*.jpg")))
    frames = [os.path.basename(f).replace(".jpg", "") for f in files]
    return frames

@app.get("/api/image/{port}/{frame}")
def get_image(port: str, frame: str):
    # Serve image file
    img_path = os.path.join(DATA_DIR, port, f"{frame}.jpg")
    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img_path)

@app.get("/api/config")
def get_config_api():
    return load_config()

@app.post("/api/config")
def update_config(config: Dict = Body(...)):
    save_config(config)
    return {"status": "ok"}

@app.get("/api/points/{frame}")
def get_points(frame: str):
    # Load PCD
    pcd_path = os.path.join(DATA_DIR, "lidar_os2_pcd", f"{frame}.pcd")
    if not os.path.exists(pcd_path):
        raise HTTPException(status_code=404, detail="PCD not found")
    
    if pcd_path not in pcd_cache:
        try:
            pcd_cache[pcd_path] = load_pcd(pcd_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load PCD: {str(e)}")
            
    points_3d = pcd_cache[pcd_path]
    
    # Downsample for web performance (e.g., keep 30k points)
    # We can use a fixed random seed for stability across requests if needed, 
    # but for a single frame load it doesn't matter much.
    target_count = 30000
    if len(points_3d) > target_count:
        # Simple random downsampling
        indices = np.linspace(0, len(points_3d)-1, target_count, dtype=int)
        points_3d = points_3d[indices]
        
    return {
        "points": points_3d.tolist()
    }

# Serve static files (frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
