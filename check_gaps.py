import os
import glob

DATA_ROOT = "data"

def check_scene(scene_name):
    port1_dir = os.path.join(DATA_ROOT, scene_name, "paired", "port_1")
    if not os.path.exists(port1_dir):
        return "No port_1 dir"
    
    files = glob.glob(os.path.join(port1_dir, "*.jpg"))
    if not files:
        return "No images"
        
    frame_nums = []
    for f in files:
        try:
            name = os.path.basename(f).replace(".jpg", "")
            frame_nums.append(int(name))
        except:
            pass
            
    frame_nums.sort()
    
    if not frame_nums:
        return "No valid numbered frames"
        
    gaps = []
    expected = frame_nums[0]
    for num in frame_nums:
        if num != expected:
            gaps.append((expected, num - 1))
            expected = num
        expected += 1
        
    return gaps

print("Checking scenes for gaps...")
scenes = [d for d in os.listdir(DATA_ROOT) if os.path.isdir(os.path.join(DATA_ROOT, d))]
for scene in scenes:
    if os.path.exists(os.path.join(DATA_ROOT, scene, "paired")):
        gaps = check_scene(scene)
        if gaps:
            print(f"Scene {scene}: GAPS FOUND -> {gaps}")
        else:
            print(f"Scene {scene}: OK")
