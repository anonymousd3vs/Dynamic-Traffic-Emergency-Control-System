# 🚀 Dashboard Quick Start Guide

**Get the Traffic Control Dashboard running in 5 minutes!**

---

## ✅ Prerequisites Check

Before starting, ensure you have:

- ✅ Python 3.8+ (check: `python --version`)
- ✅ Node.js 20+ (check: `node --version`)
- ✅ npm (check: `npm --version`)
- ✅ Virtual environment activated (`.venv\Scripts\Activate.ps1` on Windows)

---

## 🎯 3-Step Setup

### Step 1: Install Backend Dependencies

```powershell
# Make sure you're in the project root and virtual environment is activated
pip install python-socketio aiohttp eventlet pyjwt
```

### Step 2: Install Frontend Dependencies

```powershell
cd dashboard/frontend
npm install
cd ../..
```

### Step 3: Start the Dashboard

```powershell
python run_dashboard.py
```

That's it! 🎉

---

## 📱 Access the Dashboard

Once started, open your browser to:

**Dashboard UI**: http://localhost:5173

You should see:

- Video feed placeholder (will show video when detection runs)
- Metrics panels (showing 0 initially)
- Traffic flow charts (empty until data arrives)

---

## 🧪 Test Without Detection System

The dashboard will work without the detection system running - it will just show "waiting for data" messages.

To see it fully functional:

1. Keep dashboard running
2. In another terminal, run the detection system:
   ```powershell
   python run_detection.py --video videos/your_video.mp4
   ```
3. The dashboard will automatically start showing data!

---

## 🔧 Troubleshooting

### Port Already in Use

```powershell
# Use different ports
python run_dashboard.py --backend-port 9000 --frontend-port 3001
```

### Dependencies Missing

```powershell
# Check what's missing
python run_dashboard.py --check-only

# Reinstall if needed
pip install -r dashboard/backend/requirements.txt
cd dashboard/frontend && npm install
```

### Dashboard Shows "Disconnected"

1. Make sure backend server is running (check terminal output)
2. Refresh the browser page
3. Check browser console for errors (F12)

---

## 📊 What to Expect

### When Dashboard Starts (No Detection)

- ✅ Green "Connected" indicator
- ⏳ "Waiting for video stream..." message
- 📉 Empty charts
- 0️⃣ Metrics showing zeros

### When Detection Runs

- 🎥 Live video feed appears
- 📈 Metrics update in real-time
- 📊 Charts start filling with data
- 🚨 Ambulance alerts (if detected)

---

## 🎨 Dashboard Features

### Live Video Feed

- Shows processed video with detection boxes
- FPS counter overlay
- Frame count display
- Video source name

### Metrics Panel

- Current FPS
- Active vehicles
- Total vehicle count
- Average FPS (1 minute)
- Vehicle statistics (5 minutes)

### Emergency Alerts

- Red banner when ambulance detected
- Confidence score display
- Stability indicator
- Optional audio alerts (click 🔊 to enable)
- Alert history log

### Traffic Flow Charts

- Vehicle count over time (10 minutes)
- System performance (FPS graph)
- Peak/average/current statistics

---

## ⚡ Quick Commands

```powershell
# Start dashboard
python run_dashboard.py

# Start with custom ports
python run_dashboard.py --backend-port 9000 --frontend-port 3001

# Check dependencies only
python run_dashboard.py --check-only

# Stop dashboard
# Press Ctrl+C in the terminal
```

---

## 📝 Next Steps

1. ✅ Dashboard is running
2. ✅ Browser shows UI
3. 🔄 Run detection system to see live data
4. 🎯 Explore the features:
   - Enable audio alerts
   - Watch metrics update
   - View historical charts
   - Test ambulance detection

---

## 💡 Pro Tips

1. **Multiple Videos**: Stop detection (Ctrl+C), start with new video
2. **Performance**: Lower FPS if dashboard is slow (edit `stream_manager.py`)
3. **Remote Access**: Use `--backend-host 0.0.0.0` to access from other devices
4. **Production**: Run `npm run build` in frontend folder for optimized build

---

## 🆘 Need Help?

Check the full documentation:

- **Dashboard README**: `dashboard/README.md`
- **Project ROADMAP**: `ROADMAP.md`
- **Colleague Spec**: `docs/Colleague_Work_Spec.md`

---

## 🎉 Success Checklist

- [ ] Backend server started without errors
- [ ] Frontend accessible at http://localhost:5173
- [ ] "Connected" indicator shows green
- [ ] No errors in browser console (F12)
- [ ] Ready to run detection system!

---

**Happy Monitoring!** 🚦✨
