
import os

file_path = r"c:\code\6cam_project\static\index.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Target block to replace
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

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched index.html with ImageData optimization")
else:
    print("Could not find target block to replace")
    # Debug: print a small part of where it should be
    start_idx = content.find("ctx.clearRect(0, 0, canvas.width, canvas.height);")
    if start_idx != -1:
        print("Found start at index:", start_idx)
        print("Next 500 chars:", content[start_idx:start_idx+500])
    else:
        print("Could not find start of block")
