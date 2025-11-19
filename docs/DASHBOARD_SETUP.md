# Traffic Signal Dashboard - Frontend & Backend Setup

## Quick Start

### 1. Start the Python Backend (Terminal 1)

**Windows (PowerShell):**

```pwsh
.\run_backend.ps1
```

**Windows (CMD):**

```cmd
run_backend.bat
```

**Linux/Mac:**

```bash
python dashboard/backend/app.py
```

The backend will start at `http://localhost:5000`

### 2. Start the React Frontend (Terminal 2)

```bash
cd dashboard/frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173` (or similar)

## API Endpoints

The backend exposes the following REST API endpoints:

### Get Signal Status

```
GET /api/signals/status
```

Returns current signal states, phase info, and statistics.

**Response:**

```json
{
  "signals": {
    "north": {
      "state": "RED",
      "elapsed": 2.5,
      "timeRemaining": 32.5,
      "isAmbulance": false
    },
    "south": {
      "state": "GREEN",
      "elapsed": 5.2,
      "timeRemaining": 29.8,
      "isAmbulance": false
    },
    "east": {
      "state": "RED",
      "elapsed": 0,
      "timeRemaining": 35,
      "isAmbulance": false
    },
    "west": {
      "state": "RED",
      "elapsed": 0,
      "timeRemaining": 35,
      "isAmbulance": false
    }
  },
  "statistics": {
    "currentPhase": "PHASE_1",
    "isRunning": true,
    "totalAmbulances": 2,
    "completedAmbulances": 1,
    "activeEmergencies": 1
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Trigger Ambulance

```
POST /api/signals/ambulance
Content-Type: application/json

{
  "direction": "south",
  "confidence": 0.95
}
```

### Reset Signals

```
POST /api/signals/reset
```

### Pause Signals

```
POST /api/signals/pause
```

### Resume Signals

```
POST /api/signals/resume
```

### Health Check

```
GET /health
```

## Architecture

```
Traffic Control System Project
├── traffic_signals/
│   └── core/
│       └── indian_traffic_signal.py  (Core signal controller)
├── dashboard/
│   ├── backend/
│   │   ├── app.py                     (Flask server)
│   │   └── signal_routes.py           (API route handlers)
│   └── frontend/
│       └── src/components/
│           └── TrafficSignalVisualizer.jsx  (React visualization)
├── run_backend.bat / run_backend.ps1  (Backend startup)
└── requirements.txt                    (Python dependencies)
```

## Features

- **4-Way Intersection Control:** Manages North, South, East, West lanes
- **9-Phase Sequential Cycle:** Indian traffic signal standard
  - Phase 1-2: SOUTH (35s GREEN + 5s YELLOW)
  - Phase 3-4: WEST (35s GREEN + 5s YELLOW)
  - Phase 5-6: NORTH (35s GREEN + 5s YELLOW)
  - Phase 7-8: EAST (35s GREEN + 5s YELLOW)
  - Phase 9: ALL RED (2s safety clearance)
- **Ambulance Priority:** 45-second emergency override
- **Real-time Visualization:** SVG-based interactive dashboard
- **REST API:** Full control and monitoring

## Dependencies

- **Backend:** Flask, flask-cors, Python 3.12+
- **Frontend:** React, Vite, Tailwind CSS, Lucide React
- **Core:** Custom traffic_signals package

## Troubleshooting

**Backend won't start:**

- Ensure Python 3.12+ is installed
- Check virtual environment is activated
- Verify Flask and flask-cors are installed: `pip install -r requirements.txt`
- Port 5000 might be in use: `netstat -ano | findstr :5000`

**Frontend can't connect to backend:**

- Verify backend is running on localhost:5000
- Check CORS is enabled (flask-cors is installed)
- Browser console might show CORS errors - this is normal during dev
- Try refreshing the frontend

**Signals not updating:**

- Check backend logs for errors
- Verify `/api/signals/status` endpoint is responding: `curl http://localhost:5000/api/signals/status`
- Frontend polling interval is 500ms - may take up to 1 second to see updates

## Development

To extend the system:

1. Edit signal logic in `traffic_signals/core/indian_traffic_signal.py`
2. Add new API endpoints in `dashboard/backend/signal_routes.py`
3. Update React component in `dashboard/frontend/src/components/TrafficSignalVisualizer.jsx`
