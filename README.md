# 6-Camera Extrinsic Calibration Tool

A web-based tool for manual extrinsic calibration of 6 cameras relative to a LiDAR sensor.

## Features
- **Web Interface**: Visualizes 6 camera feeds and projected LiDAR points.
- **Client-side Projection**: Fast, real-time rendering using JavaScript.
- **Manual Adjustment**: 6DOF controls (Translation & Rotation) for each camera.
- **Depth Visualization**: LiDAR points are colored by depth (Red=Close, Blue=Far).

## Setup

1.  **Install Dependencies**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Data Preparation**:
    -   Place your data in `data/`.
    -   Ensure you have synchronized images and LiDAR PCD files.
    -   Update `server.py` `DATA_DIR` if needed.

3.  **Configuration**:
    -   Edit `config.json` to set your camera intrinsics.

4.  **Run**:
    ```bash
    source venv/bin/activate
    python server.py
    ```
    Open [http://localhost:8000](http://localhost:8000).

## License
MIT
