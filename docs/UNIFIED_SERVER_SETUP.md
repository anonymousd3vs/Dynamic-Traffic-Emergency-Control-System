# Unified Dashboard Server - Complete Setup ✅

## What Changed

You now have a **single unified backend server** that handles **BOTH**:

- ✅ **Detection System** (traffic detection/counting)
- ✅ **Traffic Signals** (signal control/ambulance priority)

### Problem Solved

Previously:

- `run_dashboard.py` → used `server.py` → Detection worked ✅, Signals ❌
- `run_backend.bat` → used `app.py` → Signals worked ✅, Detection ❌

Now:

- `run_dashboard.py` → uses `unified_server.py` → **Both work!** ✅✅

## New File Created

**`dashboard/backend/unified_server.py`** - A unified aiohttp server combining:

- Detection API routes from `api_routes.py`
- Detection controller from `detection_controller.py`
- Traffic signal routes from `signal_routes.py`
- Signal controller from `traffic_signals/core/indian_traffic_signal.py`

## How to Run

### Option 1: Single Command (Recommended) ⭐

```bash
python run_dashboard.py
```

This starts everything automatically:

- Backend server on port 8765
- Frontend dev server on port 5173
- Both detection and signals enabled

### Option 2: Direct Backend

```bash
python dashboard/backend/unified_server.py --port 8765
```

### Option 3: With Frontend Separately

```bash
# Terminal 1 - Backend
python dashboard/backend/unified_server.py

# Terminal 2 - Frontend
cd dashboard/frontend
npm run dev
```

## API Endpoints

### Detection Endpoints

```
GET  /api/health              - Health check
GET  /api/status              - System status
GET  /api/metrics/current     - Current metrics
GET  /api/metrics/history     - Historical metrics
GET  /api/stream/stats        - Stream statistics
POST /api/stream/settings     - Update stream settings
GET  /api/config              - Server configuration
```

### Traffic Signal Endpoints

```
GET  /api/signals/status      - Get current signal status
POST /api/signals/ambulance   - Trigger ambulance (direction, confidence)
POST /api/signals/reset       - Reset signals
POST /api/signals/pause       - Pause signals
POST /api/signals/resume      - Resume signals
```

### WebSocket Events

```
connection_established    - Client connected
metrics_update           - Real-time metrics
frame_update             - Video frame
alert                    - Emergency alerts
server_status            - Server status
```

## Dashboard Access

- **Dashboard UI**: http://localhost:5173
- **WebSocket**: ws://localhost:8765
- **REST API**: http://localhost:8765/api
- **Signals API**: http://localhost:8765/api/signals

## Testing the Unified System

### Test Detection

```bash
curl http://localhost:8765/api/health
curl http://localhost:8765/api/status
```

### Test Signals

```bash
# Get signal status
curl http://localhost:8765/api/signals/status

# Trigger ambulance
curl -X POST http://localhost:8765/api/signals/ambulance \
  -H "Content-Type: application/json" \
  -d '{"direction":"north","confidence":0.95}'

# Reset signals
curl -X POST http://localhost:8765/api/signals/reset
```

## Modified Files

1. **`dashboard/backend/unified_server.py`** - Created (NEW)
2. **`run_dashboard.py`** - Updated to use `unified_server.py` instead of `server.py`

## Why This Works

The unified server:

1. **Initializes** both detection and signal systems in `__init__`
2. **Registers** all detection routes via `api.setup_routes()`
3. **Registers** all signal routes via `_setup_signal_routes()`
4. **Shares** the same aiohttp app instance
5. **Shares** the same port (8765)
6. **Runs** both systems concurrently in one process

## Migration Path (Optional)

Old approach:

```
run_backend.bat → app.py (Flask, port 5000)
server.py (aiohttp, port 8765)
run_dashboard.py
```

New approach:

```
run_dashboard.py → unified_server.py (aiohttp, port 8765) ✨
                   [detection + signals combined]
```

## Benefits

✅ Single command to start everything
✅ No port conflicts
✅ Better resource usage (one process instead of two)
✅ Easier debugging
✅ Consistent logging
✅ Seamless detection + signals integration
✅ Same WebSocket connection for both systems

## Troubleshooting

If backend doesn't start:

```bash
# Check Python path
python dashboard/backend/unified_server.py --debug

# Check dependencies
pip install -r dashboard/backend/requirements.txt

# Check port availability
netstat -ano | findstr :8765
```

If frontend doesn't connect:

```bash
# Check WebSocket connection
# Open browser console (F12) and look for ws://localhost:8765
# Should see "Connected to Traffic Control Dashboard"
```

---

**Status**: ✅ Complete and tested
**Version**: 1.0
**Last Updated**: 2025-10-25
