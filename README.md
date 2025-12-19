# Dynamic Traffic Emergency Control System (D-TECS)

[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()
[![Version](https://img.shields.io/badge/Version-3.0.0-blue.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

**A Next-Generation Intelligent Traffic Management Solution** designed to optimize urban traffic flow and prioritize emergency vehicles in real-time.

---

## 📖 Overview

The **Dynamic Traffic Emergency Control System (D-TECS)** is an advanced AI-powered platform that revolutionizes how traffic intersections are managed. By leveraging computer vision and machine learning, the system analyzes live video feeds to detect vehicle density and identify emergency vehicles (ambulances) instantly.

Unlike traditional static timers, D-TECS dynamically adjusts signal timings based on real-time traffic conditions and automatically creates a "Green Corridor" for emergency vehicles, ensuring rapid response times and reducing urban congestion.

## ✨ Key Features

### 🧠 Intelligent Traffic Analysis
-   **Real-Time Vehicle Detection**: Utilizes state-of-the-art **YOLOv11** models optimized with **ONNX** for high-performance detection.
-   **Dynamic Signal Timing**: Algorithms automatically adjust traffic light duration (Green/Red) based on live vehicle density per lane.
-   **Adaptive Phase Control**: Implements realistic **Indian Traffic Signal Logic** (Clockwise N→E→S→W) with variable phase timings.

### 🚑 Emergency Priority System (EPS)
-   **Ambulance Recognition**: Dedicated AI models detect ambulances via visual identifiers.
-   **Green Corridor Activation**: Instantly overrides normal signal cycles to provide a clear path for approaching emergency vehicles.
-   **Auto-Recovery**: Seamlessly returns to normal operation once the emergency vehicle clears the junction.

### 🖥️ Professional Command Dashboard
-   **Monochrome User Interface**: A sleek, high-contrast, professional-grade UI designed for traffic control centers.
-   **Live Video Analytics**: View real-time video feeds with overlaid detection data and lane analytics.
-   **Interactive Controls**: Manual override capabilities, system reset, and emergency triggering simulation.
-   **Comprehensive Metrics**: Real-time display of active vehicles, peak counts, and system stability status.

---

## 🏗️ System Architecture

The project follows a modern, decoupled architecture:

1.  **AI/Core Engine (Python)**:
    -   Processes video feeds using OpenCV and YOLOv11 (ONNX).
    -   Handles object tracking (ByteTrack) and lane filtering.
    -   Calculates optimal signal timings.
2.  **Backend Server (AIOHTTP/Socket.IO)**:
    -   Orchestrates data flow between the AI engine and the dashboard.
    -   Manages WebSocket connections for low-latency updates.
3.  **Frontend Dashboard (React + Vite)**:
    -   Displays live feeds, metrics, and visualization components.
    -   Communicates with the backend via WebSockets.

---

## 🛠️ Technology Stack

-   **Computer Vision**: OpenCV, YOLOv11, ONNX Runtime, ByteTrack
-   **Backend**: Python, AIOHTTP, Python-SocketIO
-   **Frontend**: React.js, Tailwind CSS, Lucide Icons, Zustand (State Management)
-   **Protocols**: WebSockets (Real-time data), REST API

---

## 🚀 Installation & Setup

### Prerequisites
-   Python 3.10+
-   Node.js & npm (for frontend development)
-   Git

### Quick Start

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/anonymousd3vs/Dynamic-Traffic-Emergency-Control-System.git
    cd Dynamic-Traffic-Emergency-Control-System
    ```

2.  **Install Python Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the System (Unified Dashboard)**
    This command launches both the backend server and the frontend interface automatically.
    ```bash
    python run_dashboard.py
    ```

4.  **Access the Dashboard**
    Open your browser and navigate to: `http://localhost:5173`

---

## 🎮 Usage Guide

### Dashboard Interface
-   **Live Feed**: Displays the active video source with bounding boxes around detected vehicles.
-   **Detection Controls**: Select video sources, toggle lane filtering, and start/stop detection.
-   **Traffic Junction**: Visualizes the current state of traffic lights (Red/Yellow/Green) and timers for all roads.
-   **Metrics Panel**: Shows real-time data including vehicle counts and mode status.

### Simulation Controls
-   **Trigger Ambulance**: Simulates an ambulance detection event to test the emergency override logic.
-   **Reset System**: Clears all alerts and resets signal timers to default.

---

## 📁 Project Structure

```
traffic_control/
├── core/                   # Core AI detection modules
│   ├── detectors/          # YOLO & ONNX detector implementations
│   └── trackers/           # Object tracking logic
├── dashboard/
│   ├── backend/            # Python backend server
│   └── frontend/           # React frontend application
├── traffic_signals/        # Traffic signal logic controllers
├── run_dashboard.py        # Main entry point
└── requirements.txt        # Python dependencies
```

---

## 🤝 Contribution

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

---

**Developed by AnonymousD3vs** | *Optimizing Traffic, Saving Lives.*
