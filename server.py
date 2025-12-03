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

DATA_ROOT = "data"
# Initial default scene (will be updated dynamically)
CURRENT_SCENE = ""
DATA_DIR = ""
CONFIG_FILE = "config.json"

print(f"Server starting. Data Root: {DATA_ROOT}")

def get_scenes():
    if not os.path.exists(DATA_ROOT):
        return []
    # Only include directories that have a "paired" subdirectory
    scenes = []
    for d in os.listdir(DATA_ROOT):
        path = os.path.join(DATA_ROOT, d)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "paired")):
            scenes.append(d)
    return sorted(scenes)

# Initialize scene if possible
scenes = get_scenes()
if scenes:
    # Default to the last one (usually latest timestamp)
    CURRENT_SCENE = scenes[-1]
    DATA_DIR = os.path.join(DATA_ROOT, CURRENT_SCENE, "paired")
    print(f"Initialized with scene: {CURRENT_SCENE}")
else:
    print("Warning: No valid scenes found in data/ directory!")

# Load Config
def load_config():
    # Always load from root config to ensure global consistency
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
            
    # Fallback: Try to load from the current scene directory if global doesn't exist
    scene_config = os.path.join(DATA_DIR, "config.json")
    if os.path.exists(scene_config):
        with open(scene_config, 'r') as f:
            return json.load(f)
            
    return {}

def save_config(config):
    # Save to the global config file
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Cache for PCD data to avoid reloading
pcd_cache = {}

@app.get("/api/scenes")
def get_scenes_api():
    return {
        "scenes": get_scenes(),
        "current": CURRENT_SCENE
    }

@app.post("/api/scene")
def set_scene(payload: Dict = Body(...)):
    global CURRENT_SCENE, DATA_DIR, pcd_cache
    scene = payload.get("scene")
    print(f"Request to switch to scene: {scene}")
    
    if not scene or scene not in get_scenes():
        raise HTTPException(status_code=400, detail="Invalid scene")
    
    CURRENT_SCENE = scene
    DATA_DIR = os.path.join(DATA_ROOT, CURRENT_SCENE, "paired")
    pcd_cache = {} # Clear cache on scene switch
    print(f"SUCCESS: Switched to scene: {CURRENT_SCENE}")
    print(f"NEW DATA_DIR: {DATA_DIR}")
    return {"status": "ok", "current": CURRENT_SCENE}

@app.get("/api/frames")
def get_frames():
    print(f"get_frames called. Current DATA_DIR: {DATA_DIR}")
    # List all frames based on port_1 images
    port1_dir = os.path.join(DATA_DIR, "port_1")
    if not os.path.exists(port1_dir):
        print(f"ERROR: port_1 dir not found at {port1_dir}")
        return []
    files = glob.glob(os.path.join(port1_dir, "*.jpg"))
    
    # Sort numerically
    def get_frame_number(filepath):
        try:
            filename = os.path.basename(filepath)
            name_no_ext = os.path.splitext(filename)[0]
            return int(name_no_ext)
        except ValueError:
            return -1 

    files.sort(key=get_frame_number)
    
    frames = [os.path.basename(f).replace(".jpg", "") for f in files]
    print(f"Found {len(frames)} frames")
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
    
    # Downsample for web performance
    target_count = 150000
    if len(points_3d) > target_count:
        indices = np.linspace(0, len(points_3d)-1, target_count, dtype=int)
        points_3d = points_3d[indices]
        
    return {
        "points": points_3d.tolist()
    }

# Serve static files (frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
