
import os

file_path = r"c:\code\6cam_project\static\index.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Memoize LidarViewer
old_lidar = "function LidarViewer({ points }) {"
new_lidar = "const LidarViewer = React.memo(({ points }) => {"
content = content.replace(old_lidar, new_lidar)

# 2. Close LidarViewer memo
old_close = "    return <div ref={mountRef} className=\"w-full h-full\" />;\n        }"
new_close = "    return <div ref={mountRef} className=\"w-full h-full\" />;\n        });"
content = content.replace(old_close, new_close)

# 3. Add State
old_state = "const [isPlaying, setIsPlaying] = useState(false);\n\n            const canvasRefs = useRef({});"
new_state = "const [isPlaying, setIsPlaying] = useState(false);\n            const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);\n\n            const canvasRefs = useRef({});"
content = content.replace(old_state, new_state)

# 4. Handle Scene Change
old_scene = """            const handleSceneChange = (scene) => {
                fetch('/api/scene', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ scene })
                }).then(res => res.json()).then(data => {
                    setCurrentScene(data.current);
                    fetchData();
                });
            };"""
new_scene = """            const handleSceneChange = (scene) => {
                const switchScene = () => {
                    fetch('/api/scene', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ scene })
                    }).then(res => res.json()).then(data => {
                        setCurrentScene(data.current);
                        setHasUnsavedChanges(false);
                        fetchData();
                    });
                };

                if (hasUnsavedChanges) {
                    if (confirm("You have unsaved changes. Click OK to Save and Switch, or Cancel to Switch without saving.")) {
                        saveConfig().then(() => switchScene());
                    } else {
                        switchScene();
                    }
                } else {
                    switchScene();
                }
            };"""
content = content.replace(old_scene, new_scene)

# 5. Save Config
old_save = """            const saveConfig = () => {
                fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                }).then(() => alert("Saved!"));
            };"""
new_save = """            const saveConfig = () => {
                return fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                }).then(() => {
                    alert("Saved!");
                    setHasUnsavedChanges(false);
                });
            };"""
content = content.replace(old_save, new_save)

# 6. Config Change
old_config = """            const handleConfigChange = (port, key, value) => {
                const newConfig = { ...config };
                newConfig.cameras[port].extrinsic[key] = parseFloat(value);
                setConfig(newConfig);
            };"""
new_config = """            const handleConfigChange = (port, key, value) => {
                const newConfig = { ...config };
                newConfig.cameras[port].extrinsic[key] = parseFloat(value);
                setConfig(newConfig);
                setHasUnsavedChanges(true);
            };"""
content = content.replace(old_config, new_config)

# 7. ImageData Optimization
# This one is tricky because it's a large block. I'll use a unique substring to locate it.
start_marker = "ctx.clearRect(0, 0, canvas.width, canvas.height);"
end_marker = "ctx.fillStyle = 'red';"
# We need to replace the loop after this.

# Let's replace the whole useEffect block for rendering
old_render_effect_start = "            useEffect(() => {\n                if (viewMode === 'lidar') return;"
old_render_effect_end = "            }, [config, points3D, showPoints, selectedPort, viewMode, transform]);"

# Finding the block is hard with simple replace if there are other useEffects.
# But this one has "if (viewMode === 'lidar') return;" which is unique.

# I will construct the new render logic and replace the specific block.
# Actually, let's just replace the inner loop part.
old_loop_start = "                    ctx.clearRect(0, 0, canvas.width, canvas.height);"
old_loop_end = "                        }\n                    }\n                });"

# This is risky with simple replace.
# Let's try to match the exact block from the file content I saw.
old_block = """                    ctx.clearRect(0, 0, canvas.width, canvas.height);

                    const camConfig = config.cameras[port];
                    const R = getRotationMatrix(camConfig.extrinsic.roll, camConfig.extrinsic.pitch, camConfig.extrinsic.yaw);
                    const t = [camConfig.extrinsic.x, camConfig.extrinsic.y, camConfig.extrinsic.z];
                    const K = camConfig.intrinsic;
                    const dist = camConfig.intrinsic;

                    const scaleX = canvas.width / 1920;
                    const scaleY = canvas.height / 1280;

                    ctx.fillStyle = 'red';

                    for (let i = 0; i < points3D.length; i++) {
                        const pt = points3D[i];
                        const z = R[2][0] * pt[0] + R[2][1] * pt[1] + R[2][2] * pt[2] + t[2];

                        if (z < 0.1) continue;

                        const uv = projectPoint(pt, R, t, K, dist);
                        if (uv) {
                            const u = uv[0] * scaleX;
                            const v = uv[1] * scaleY;

                            if (u >= 0 && u < canvas.width && v >= 0 && v < canvas.height) {
                                // Color based on Z height (Same as 3D view)
                                const minDepth = -2.0;
                                const maxDepth = 5.0;
                                // Use point[2] (Z) directly, not camera depth
                                const pointZ = pt[2]; 
                                let hue = (1.0 - (Math.max(minDepth, Math.min(pointZ, maxDepth)) - minDepth) / (maxDepth - minDepth)) * 240;
                                ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
                                ctx.fillRect(u, v, 2, 2);
                            }
                        }
                    }"""

new_block = """                    // Optimization: Use ImageData instead of fillRect
                    const imageData = ctx.createImageData(canvas.width, canvas.height);
                    const data = imageData.data;

                    const camConfig = config.cameras[port];
                    const R = getRotationMatrix(camConfig.extrinsic.roll, camConfig.extrinsic.pitch, camConfig.extrinsic.yaw);
                    const t = [camConfig.extrinsic.x, camConfig.extrinsic.y, camConfig.extrinsic.z];
                    const K = camConfig.intrinsic;
                    const dist = camConfig.intrinsic;

                    const scaleX = canvas.width / 1920;
                    const scaleY = canvas.height / 1280;

                    for (let i = 0; i < points3D.length; i++) {
                        const pt = points3D[i];
                        const z = R[2][0] * pt[0] + R[2][1] * pt[1] + R[2][2] * pt[2] + t[2];

                        if (z < 0.1) continue;

                        const uv = projectPoint(pt, R, t, K, dist);
                        if (uv) {
                            const u = Math.floor(uv[0] * scaleX);
                            const v = Math.floor(uv[1] * scaleY);

                            if (u >= 0 && u < canvas.width && v >= 0 && v < canvas.height) {
                                const minDepth = -2.0;
                                const maxDepth = 5.0;
                                const pointZ = pt[2]; 
                                const hue = (1.0 - (Math.max(minDepth, Math.min(pointZ, maxDepth)) - minDepth) / (maxDepth - minDepth)) * 240;
                                
                                // Simple HSL to RGB
                                const h = hue;
                                const s = 1.0;
                                const l = 0.5;
                                const c = (1 - Math.abs(2 * l - 1)) * s;
                                const x = c * (1 - Math.abs((h / 60) % 2 - 1));
                                const m = l - c / 2;
                                let r = 0, g = 0, b = 0;
                                
                                if (0 <= h && h < 60) { r = c; g = x; b = 0; }
                                else if (60 <= h && h < 120) { r = x; g = c; b = 0; }
                                else if (120 <= h && h < 180) { r = 0; g = c; b = x; }
                                else if (180 <= h && h < 240) { r = 0; g = x; b = c; }
                                else if (240 <= h && h < 300) { r = x; g = 0; b = c; }
                                else if (300 <= h && h < 360) { r = c; g = 0; b = x; }
                                
                                r = Math.round((r + m) * 255);
                                g = Math.round((g + m) * 255);
                                b = Math.round((b + m) * 255);

                                const setPixel = (x, y) => {
                                    if (x >= 0 && x < canvas.width && y >= 0 && y < canvas.height) {
                                        const idx = (y * canvas.width + x) * 4;
                                        data[idx] = r;
                                        data[idx + 1] = g;
                                        data[idx + 2] = b;
                                        data[idx + 3] = 255;
                                    }
                                };
                                
                                setPixel(u, v);
                                setPixel(u + 1, v);
                                setPixel(u, v + 1);
                                setPixel(u + 1, v + 1);
                            }
                        }
                    }
                    ctx.putImageData(imageData, 0, 0);"""

content = content.replace(old_block, new_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully patched index.html")
