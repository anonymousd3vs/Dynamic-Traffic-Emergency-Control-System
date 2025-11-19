# 🚦 Traffic Control System Dashboard

**Real-time web dashboard for traffic monitoring and emergency vehicle detection**

## Status: ✅ **IMPLEMENTED**

A fully functional real-time dashboard with video streaming, metrics tracking, and emergency alerts.

---

## 🌟 Features

### Real-Time Monitoring

- ✅ **Live Video Stream** - Processed video feed with detection overlays (5 FPS optimized)
- ✅ **System Metrics** - FPS, vehicle count, active vehicles, frame count
- ✅ **Emergency Alerts** - Visual and audio alerts for ambulance detection
- ✅ **Traffic Flow Charts** - Historical data visualization (last 10 minutes)
- ✅ **WebSocket Communication** - Sub-second latency updates
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile

### Dashboard Components

- **VideoFeed** - Live stream with overlays (FPS, frame count, source info)
- **MetricsPanel** - Real-time and historical statistics
- **EmergencyAlert** - Prominent ambulance detection alerts with sound
- **TrafficFlowChart** - Interactive charts using Recharts

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Traffic Detection System                  │
│                  (core/detectors/traffic_detector.py)       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    Integration Layer
                    (backend/integration.py)
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
   ┌────▼─────┐                          ┌─────▼────┐
   │ Backend  │◄────── WebSocket ────────┤ Frontend │
   │ (Python) │                          │  (React) │
   └──────────┘                          └──────────┘
   - WebSocket Server                    - Real-time UI
   - Stream Manager                      - Video Display
   - API Routes                          - Charts & Metrics
   - Frame Encoding                      - Alerts
```

---

## 📦 Tech Stack

### Backend (Python)

- **Socket.IO** - WebSocket communication
- **aiohttp** - Async web server
- **OpenCV** - Video frame processing
- **Base64** - Frame encoding for transmission

### Frontend (React)

- **React 18** - UI framework
- **Vite** - Fast build tool
- **Tailwind CSS** - Styling framework
- **Socket.IO Client** - WebSocket client
- **Recharts** - Chart library
- **Zustand** - State management
- **Lucide React** - Icon library

---

## 📁 Directory Structure

```
dashboard/
├── backend/
│   ├── __init__.py
│   ├── websocket_server.py    # ✅ WebSocket server with Socket.IO
│   ├── stream_manager.py      # ✅ Video frame encoding & compression
│   ├── api_routes.py           # ✅ REST API endpoints
│   ├── integration.py          # ✅ Detection system integration
│   ├── server.py               # ✅ Standalone server launcher
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # ✅ React components
│   │   │   ├── VideoFeed.jsx
│   │   │   ├── MetricsPanel.jsx
│   │   │   ├── EmergencyAlert.jsx
│   │   │   └── TrafficFlowChart.jsx
│   │   ├── services/           # ✅ WebSocket service
│   │   │   └── websocket.js
│   │   ├── stores/             # ✅ Zustand state management
│   │   │   └── dashboardStore.js
│   │   ├── App.jsx             # ✅ Main application
│   │   └── index.css           # ✅ Tailwind CSS
│   ├── package.json
│   ├── tailwind.config.js      # ✅ Tailwind configuration
│   └── vite.config.js
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with virtual environment
- **Node.js 20+** and npm
- **Running traffic detection system** (optional for testing)

### Installation

#### 1. Install Backend Dependencies

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source .venv/bin/activate   # Linux/Mac

# Install Python packages
pip install python-socketio aiohttp eventlet pyjwt
```

#### 2. Install Frontend Dependencies

```bash
cd dashboard/frontend
npm install
```

### Running the Dashboard

#### Option 1: Use the Launcher Script (Recommended)

```bash
# From project root
python run_dashboard.py

# Custom ports
python run_dashboard.py --backend-port 9000 --frontend-port 3000

# Check dependencies only
python run_dashboard.py --check-only
```

#### Option 2: Manual Start

**Terminal 1 - Backend:**

```bash
python -m dashboard.backend.server
# or with custom port
python -m dashboard.backend.server --port 8765
```

**Terminal 2 - Frontend:**

```bash
cd dashboard/frontend
npm run dev
```

#### Option 3: Backend Only (for testing)

```bash
python -m dashboard.backend.server --host 0.0.0.0 --port 8765
```

### Access the Dashboard

Open your browser to:

- **Dashboard UI**: http://localhost:5173
- **API Health**: http://localhost:8765/api/health
- **API Status**: http://localhost:8765/api/status

---

## 🔌 Integration with Detection System

### Method 1: Using Integration Helper

```python
from core.detectors.traffic_detector import ONNXTrafficDetector
from dashboard.backend.integration import add_dashboard_to_detector

# Create detector
detector = ONNXTrafficDetector(
    device='cpu',
    video_source='videos/traffic.mp4'
)

# Add dashboard (auto-starts server)
dashboard = add_dashboard_to_detector(
    detector,
    host='localhost',
    port=8765,
    stream_fps=5
)

# Detection loop
cap = cv2.VideoCapture('videos/traffic.mp4')
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Process frame
    result_frame = detector.process_frame(frame)

    # Update dashboard
    dashboard.update_from_detector(detector)
    dashboard.stream_frame(result_frame, detector)

    cv2.imshow('Traffic', result_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
dashboard.stop()
cap.release()
cv2.destroyAllWindows()
```

### Method 2: Manual Integration

```python
from dashboard.backend.integration import DashboardIntegration

# Create dashboard integration
dashboard = DashboardIntegration(host='localhost', port=8765)
dashboard.start()

# In your detection loop
dashboard.update_from_detector(detector)  # Every frame or every N frames
dashboard.stream_frame(frame, detector)   # Every 5th frame recommended

# Cleanup
dashboard.stop()
```

---

## 📡 API Reference

### WebSocket Events

#### Client → Server

| Event            | Description           |
| ---------------- | --------------------- |
| `connect`        | Client connection     |
| `disconnect`     | Client disconnection  |
| `ping`           | Health check ping     |
| `request_status` | Request server status |

#### Server → Client

| Event                    | Data                                  | Description             |
| ------------------------ | ------------------------------------- | ----------------------- |
| `connection_established` | `{sid, timestamp, message}`           | Connection confirmation |
| `metrics_update`         | `{type, timestamp, data}`             | Real-time metrics       |
| `frame_update`           | `{type, timestamp, frame, metadata}`  | Video frame (base64)    |
| `alert`                  | `{type, alert_type, timestamp, data}` | Emergency alert         |
| `server_status`          | `{connected_clients, uptime, ...}`    | Server statistics       |
| `pong`                   | `{timestamp}`                         | Ping response           |

### REST API Endpoints

| Method | Endpoint                         | Description            |
| ------ | -------------------------------- | ---------------------- |
| GET    | `/api/health`                    | Health check           |
| GET    | `/api/status`                    | System status          |
| GET    | `/api/metrics/current`           | Current metrics        |
| GET    | `/api/metrics/history?limit=100` | Historical metrics     |
| GET    | `/api/stream/stats`              | Stream statistics      |
| POST   | `/api/stream/settings`           | Update stream settings |
| GET    | `/api/config`                    | Server configuration   |

---

## ⚙️ Configuration

### Backend Settings

Edit `dashboard/backend/server.py` or use command-line arguments:

```bash
python -m dashboard.backend.server \
  --host 0.0.0.0 \
  --port 8765 \
  --debug
```

### Frontend Settings

Edit `dashboard/frontend/src/App.jsx`:

```javascript
const [serverUrl, setServerUrl] = useState("http://localhost:8765");
```

### Stream Settings

Adjust in `dashboard/backend/stream_manager.py`:

```python
StreamManager(
    target_fps=5,        # Frames per second
    jpeg_quality=80,     # 0-100
    max_width=1280       # Maximum frame width
)
```

---

## 🧪 Testing

### Test Backend Server

```bash
python -m dashboard.backend.server --debug
```

Visit `http://localhost:8765/api/health` - should return `{"status": "healthy"}`

### Test Frontend

```bash
cd dashboard/frontend
npm run dev
```

Visit `http://localhost:5173` - should show dashboard UI

### Test Integration

```bash
# Terminal 1: Start dashboard
python run_dashboard.py

# Terminal 2: Run detection with dashboard
python run_detection.py --video videos/test.mp4 --dashboard
```

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check dependencies
pip install python-socketio aiohttp eventlet

# Check port availability
netstat -ano | findstr :8765  # Windows
lsof -i :8765                  # Linux/Mac
```

### Frontend won't start

```bash
# Reinstall dependencies
cd dashboard/frontend
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 20+
```

### Dashboard shows "Disconnected"

1. Ensure backend server is running
2. Check firewall settings
3. Verify WebSocket URL in frontend settings
4. Check browser console for errors

### No video stream

1. Ensure detection system is running
2. Check `dashboard.stream_frame()` is called
3. Verify frame encoding (check backend logs)
4. Reduce stream FPS if bandwidth is limited

---

## 📈 Performance Tips

1. **Optimize Stream FPS**: Lower FPS (3-5) reduces bandwidth
2. **Adjust JPEG Quality**: 70-80 is usually sufficient
3. **Limit History**: Reduce `maxHistoryLength` in store
4. **Use Production Build**: `npm run build` for frontend
5. **Enable Compression**: Configure nginx/apache for production

---

## 🚧 Known Limitations

- Video streaming at 5 FPS (by design, to reduce bandwidth)
- Historical data limited to last 10 minutes (configurable)
- No authentication (add JWT for production)
- Single video source at a time
- No video recording capability

---

## 🔮 Future Enhancements

- [ ] Multi-camera support
- [ ] User authentication & authorization
- [ ] Video recording & playback
- [ ] Email/SMS alert notifications
- [ ] Database integration for long-term storage
- [ ] Analytics & reporting module
- [ ] Mobile app (React Native)
- [ ] Traffic signal integration (Phase 2)

---

## 📚 Additional Documentation

- **Project Roadmap**: `../ROADMAP.md`
- **Colleague Specification**: `../docs/Colleague_Work_Spec.md`
- **Detection System**: `../core/detectors/README.md`

---

## 📝 License

Part of the Traffic Control System project.

---

## 🤝 Contributing

This dashboard was built according to the specifications in `docs/Colleague_Work_Spec.md` (Task 1).

For questions or improvements, please refer to the project documentation.

---

**Last Updated**: October 22, 2025
**Status**: Production Ready ✅
