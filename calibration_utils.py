import numpy as np
import cv2

def get_rotation_matrix(roll, pitch, yaw):
    """
    Returns 3x3 rotation matrix from Euler angles (in degrees).
    Order: Roll -> Pitch -> Yaw (Extrinsic rotation usually)
    But for camera extrinsics, it depends on definition.
    Here we assume R = Rz(yaw) * Ry(pitch) * Rx(roll)
    """
    roll = np.radians(roll)
    pitch = np.radians(pitch)
    yaw = np.radians(yaw)

    rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])

    ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])

    rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])

    return rz @ ry @ rx

def project_points(points_3d, intrinsic, extrinsic):
    """
    Project 3D points (LiDAR frame) to 2D image plane.
    
    points_3d: (N, 3) numpy array
    intrinsic: dict with fx, fy, cx, cy, k1, k2, etc.
    extrinsic: dict with x, y, z, roll, pitch, yaw
    
    Returns:
        points_2d: (N, 2) pixels
        mask: (N,) boolean mask of valid points (in front of camera)
    """
    # Extrinsic: LiDAR to Camera transform
    # Usually extrinsic is defined as Transform from LiDAR to Camera
    # T_cam_lidar = [R | t]
    
    R = get_rotation_matrix(extrinsic['roll'], extrinsic['pitch'], extrinsic['yaw'])
    t = np.array([[extrinsic['x']], [extrinsic['y']], [extrinsic['z']]])
    
    # Transform points to camera coordinate system
    # P_cam = R * P_lidar + t
    points_cam = (R @ points_3d.T + t).T  # (N, 3)
    
    # Filter points behind camera (z < 0)
    # Standard camera frame: Z forward, X right, Y down
    # But LiDAR is usually: X forward, Y left, Z up
    # The extrinsic R should handle the coordinate system change + rotation.
    
    mask = points_cam[:, 2] > 0.1
    points_cam = points_cam[mask]
    
    if len(points_cam) == 0:
        return np.array([]), mask

    # Project
    K = np.array([
        [intrinsic['fx'], 0, intrinsic['cx']],
        [0, intrinsic['fy'], intrinsic['cy']],
        [0, 0, 1]
    ])
    
    dist_coeffs = np.array([
        intrinsic.get('k1', 0), intrinsic.get('k2', 0), 
        intrinsic.get('p1', 0), intrinsic.get('p2', 0), 
        intrinsic.get('k3', 0)
    ])
    
    # Use OpenCV for projection (handles distortion)
    # cv2.projectPoints expects (N, 1, 3) or (N, 3)
    # It also takes rvec and tvec. Since we already transformed points, 
    # we can pass rvec=0, tvec=0 and pass points_cam as object points.
    
    # However, cv2.projectPoints projects 3D points given camera pose.
    # Since points_cam are already in camera frame, we can just project them with Identity pose.
    
    points_2d, _ = cv2.projectPoints(
        points_cam, 
        np.zeros(3), np.zeros(3), 
        K, dist_coeffs
    )
    
    points_2d = points_2d.reshape(-1, 2)
    
    # We need to return the mask to know which original points were valid
    # But we filtered points_cam.
    # Let's return the filtered 2D points. The caller might want to know indices, 
    # but for visualization we just need the 2D points.
    
    return points_2d, mask
