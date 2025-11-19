# Traffic Control System - Troubleshooting Guide

**Version:** 2.3  
**Last Updated:** November 9, 2025  
**Status:** Production Ready

## Quick Start - System Diagnostics

### 1. Verify Full System Health
```bash
python test_detection_system.py
```

This will check:
- ✅ Python version
- ✅ PyTorch/CUDA
- ✅ All dependencies installed
- ✅ Model files exist
- ✅ ONNX runtime works
- ✅ Camera access
- ✅ Detection system

#### 2. Verify Dependencies
```bash
pip install -r requirements.txt --upgrade
```

Make sure you have:
- `torch >= 2.0.0`
- `onnxruntime >= 1.16.0`
- `opencv-python >= 4.8.0`
- `aiohttp >= 3.8.0`

#### 3. Lower Confidence Threshold
If you see 0 detections, the confidence threshold might be too high:

```bash
# Edit config/detection_config.yaml
vehicle:
  confidence_threshold: 0.2  # Lower = more detections (but more false positives)
```

#### 4. Check Model Files
```bash
# Verify optimized models exist
ls -la optimized_models/
```

Must have:
- `yolo11n_optimized.onnx` (~10MB)
- `indian_ambulance_yolov11n_best_optimized.onnx` (~10MB)

#### 5. Test Detection Directly
```python
from core.detectors.traffic_detector import ONNXTrafficDetector
import cv2

detector = ONNXTrafficDetector(device='cpu')
frame = cv2.imread('test_image.jpg')
result = detector.process_frame(frame)
print(f"Detected {detector.vehicle_count} vehicles")
```

#### 6. Check GPU/CUDA
If CUDA is not available:
```bash
# Force CPU mode
export CUDA_VISIBLE_DEVICES=""
python run_dashboard.py
```

Or in code:
```python
import torch
torch.cuda.is_available()  # Should be False (OK for CPU)
```

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'onnxruntime'` | Missing ONNX Runtime | `pip install onnxruntime` |
| `Model file not found` | Models not in optimized_models/ | Run `git lfs pull` or download from hub |
| `0 vehicles detected` | Confidence threshold too high | Lower in detection_config.yaml |
| `Backend crashes silently` | Missing dependency or GPU issue | Run diagnostic test |
| `OpenCV error` | Incompatible OpenCV version | `pip install --upgrade opencv-python` |

### Detailed Debug Mode

Enable full logging:

```bash
export DEBUG=1
export LOG_LEVEL=DEBUG
python run_dashboard.py
```

### Still Broken?

1. Share output of `test_detection_system.py`
2. Check `dashboard/backend/traffic_control.log`
3. Look for error messages in console
4. Try CPU-only mode first (disable GPU)

---

## Common Issues by Component

### Dashboard Issues

#### Issue: Dashboard not loading (404 error)
**Solution:**
1. Verify frontend built: `ls dashboard/frontend/dist`
2. Rebuild if needed: `cd dashboard/frontend && npm run build`
3. Check server running: `http://localhost:8765`

#### Issue: No video feed showing
**Solution:**
1. Start detection first: Click "Detection System" → select video → Start
2. Check WebSocket connection: Browser DevTools → Network → WS tab
3. Verify backend logs for connection errors

#### Issue: Metrics not updating
**Solution:**
1. Confirm detection is running (video should be processing)
2. Check metrics API: `curl http://localhost:8765/api/signals/metrics`
3. Restart backend if stuck

### Traffic Signal Issues

#### Issue: Signals not responding to lane selection
**Solution:**
1. Test API: `curl -X POST http://localhost:8765/api/signals/select-lane -H "Content-Type: application/json" -d '{"lane": "east"}'
2. Check signal controller running: `pgrep -f traffic_signals`
3. Verify phase mapping in config

#### Issue: Dynamic timing not updating
**Solution:**
1. Ensure vehicle count is being detected (check video feed)
2. Verify lane is selected (frontend shows highlighted lane)
3. Check timing calculation: `curl http://localhost:8765/api/signals/dynamic-timing/status`
4. Timing values should change as vehicle count changes

#### Issue: Emergency ambulance not triggering all-green
**Solution:**
1. Verify ambulance model loaded: Check console for model loading message
2. Test detection on ambulance video: Should show "AMBULANCE DETECTED"
3. Check priority manager active: `curl http://localhost:8765/api/signals/status`

### Detection Issues

#### Issue: Vehicle count always 0
**Causes & Solutions:**
1. **Wrong video source** - Verify video path is correct
2. **Confidence threshold too high** - Lower in `config/detection_config.yaml`
3. **Model not loaded** - Check console for model loading errors
4. **Video format incompatible** - Try MP4 or MOV format

**Debug command:**
```bash
python run_detection.py --video test.mp4 --conf 0.3
```

#### Issue: Ambulance not detected
**Causes & Solutions:**
1. **Model not fine-tuned for your region** - Current model trained on Indian ambulances
2. **Lighting conditions** - Poor lighting reduces detection
3. **Ambulance model not loaded** - Verify file exists: `models/indian_ambulance_yolov11n_best.onnx`

**Test directly:**
```python
from core.detectors.traffic_detector import ONNXTrafficDetector
import cv2

detector = ONNXTrafficDetector(device='cpu')
frame = cv2.imread('ambulance.jpg')
detector.process_frame(frame)
print(f"Ambulance: {detector.ambulance_detected}")
```

#### Issue: Very slow detection (FPS < 5)
**Causes & Solutions:**
1. **Using CPU instead of GPU** - Install CUDA if GPU available
2. **High resolution video** - Downscale input or use lower resolution model (YOLOv11n vs v11m)
3. **Too many vehicles** - Zone filtering reduces processing
4. **Unnecessary features enabled** - Disable features you don't need

**Optimization:**
- Use Zone-Based mode (faster than line-crossing)
- Lower input resolution
- Increase detection interval (every Nth frame only)
- Enable GPU/CUDA if available

### Video Processing Issues

#### Issue: Video file not found
**Solution:**
```bash
# Verify video exists and is readable
file /path/to/video.mp4
ffmpeg -i /path/to/video.mp4 -f null - 2>&1 | head -20
```

#### Issue: Unsupported video codec
**Solution:**
```bash
# Convert video to H.264 (supported format)
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
```

#### Issue: Lane configuration not loading
**Solution:**
1. Verify config file exists: `ls config/lane_config.json`
2. Check format is valid JSON: `python -m json.tool config/lane_config.json`
3. Regenerate config: `python lane_config_tool.py --video video.mp4`

---

## System Requirements Verification

```bash
# Check Python version (3.8+)
python --version

# Check required packages
pip list | grep -E "torch|onnx|opencv|aiohttp"

# Check model files
ls -lh optimized_models/*.onnx

# Check GPU availability
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
```

---

## Performance Benchmarks (v2.3)

| Metric | Expected | Acceptable Range |
|--------|----------|------------------|
| Detection FPS (GPU) | 20-30 | 15+ |
| Detection FPS (CPU) | 5-15 | 3+ |
| Vehicle Detection Accuracy | 95%+ | 85%+ |
| Ambulance Detection Accuracy | 90%+ | 80%+ |
| Dashboard Response Time | <100ms | <200ms |
| Signal Update Latency | <500ms | <1s |

---

## Advanced Debugging

### Enable Full Debug Logging

```python
# In run_dashboard.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export PYTHONUNBUFFERED=1
export DEBUG=1
```

### Monitor System Resources

```bash
# Watch CPU/Memory
watch -n 1 'ps aux | grep python'

# Monitor GPU (if CUDA available)
nvidia-smi -l 1
```

### Inspect WebSocket Messages

Browser Console:
```javascript
// Check WebSocket connection
console.log(ws.readyState);  // 1 = OPEN, 0 = CONNECTING

// Log all messages
socket.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

---

## Getting Help

**For Issues, Include:**
1. Output of `test_detection_system.py`
2. Last 50 lines of `dashboard/backend/traffic_control.log`
3. Console output from `run_dashboard.py` start
4. OS and Python version
5. Detailed description of what you were doing

**System Status File:**
```bash
# Creates comprehensive status file
python check_requirements.py
python check_onnx_setup.py
```

---

**Status:** v2.3 Production Ready ✅  
**Last Updated:** November 9, 2025
