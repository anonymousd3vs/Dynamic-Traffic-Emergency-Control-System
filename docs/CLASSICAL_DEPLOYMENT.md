# Classical Deployment Guide

**Traditional GitHub clone and manual setup for developers and advanced users.**

> **For:** Developers who want to modify code, understand internals, or don't want to use Docker.

---

## 🚀 Quick Start (15-20 Minutes)

### Prerequisites

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/))
- **4GB+ RAM**
- **2GB+ free disk space**

### Step-by-Step Setup

```bash
# 1. Clone repository
git clone https://github.com/anonymousd3vs/Traffic_Control.git
cd Traffic_Control

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt
pip install -r dashboard/backend/requirements.txt

# 5. Install Node.js dependencies
cd dashboard/frontend
npm install
cd ../..

# 6. Run backend (in one terminal)
python run_backend.py

# 7. Run frontend (in another terminal)
cd dashboard/frontend
npm run dev

# 8. Open browser
# Frontend: http://localhost:5173
# Backend: http://localhost:8765
```

---

## 📋 Platform-Specific Installation

### Windows Setup

#### Prerequisites

1. **Python 3.10+**

   ```bash
   python --version  # Should be 3.10 or higher
   ```

2. **Node.js 18+**

   ```bash
   node --version    # Should be v18 or higher
   npm --version     # Should be 9 or higher
   ```

3. **Git**
   ```bash
   git --version
   ```

#### Installation

```bash
# Clone
git clone https://github.com/anonymousd3vs/Traffic_Control.git
cd Traffic_Control

# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Command Prompt)
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
pip install -r dashboard/backend/requirements.txt

# Install frontend dependencies
cd dashboard/frontend
npm install
cd ../..

# Start backend
python run_backend.py

# In another PowerShell/CMD, start frontend
cd dashboard/frontend
npm run dev
```

#### Open Browser

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8765

---

### Linux Setup

#### Prerequisites (Ubuntu/Debian)

```bash
# Update package manager
sudo apt update

# Install Python
sudo apt install python3.10 python3.10-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install Git
sudo apt install git
```

#### Installation

```bash
# Clone
git clone https://github.com/anonymousd3vs/Traffic_Control.git
cd Traffic_Control

# Create virtual environment
python3.10 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r dashboard/backend/requirements.txt

# Install frontend dependencies
cd dashboard/frontend
npm install
cd ../..

# Start backend
python run_backend.py

# In another terminal, start frontend
cd dashboard/frontend
npm run dev
```

#### Open Browser

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8765

---

### macOS Setup

#### Prerequisites

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.10

# Install Node.js
brew install node

# Install Git
brew install git
```

#### Installation

```bash
# Clone
git clone https://github.com/anonymousd3vs/Traffic_Control.git
cd Traffic_Control

# Create virtual environment
python3.10 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r dashboard/backend/requirements.txt

# Install frontend dependencies
cd dashboard/frontend
npm install
cd ../..

# Start backend
python run_backend.py

# In another terminal, start frontend
cd dashboard/frontend
npm run dev
```

#### Open Browser

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8765

---

### Raspberry Pi 5 Setup

#### Prerequisites

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip

# Install Node.js (ARM64)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install optional dependencies for better performance
sudo apt install libatlas-base-dev libjasper-dev libtiff5 libjasper1 libharfbuzz0b libwebp6
```

#### Installation

```bash
# Clone
git clone https://github.com/anonymousd3vs/Traffic_Control.git
cd Traffic_Control

# Create virtual environment
python3.10 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies (may take 5-10 minutes on RPi)
pip install -r requirements.txt
pip install -r dashboard/backend/requirements.txt

# Install frontend dependencies
cd dashboard/frontend
npm install
cd ../..

# Optional: Install for GPU acceleration (if using Coral TPU)
pip install --index-url https://google-coral.github.io/py-repo coral-edgetpu

# Start backend
python run_backend.py

# In another terminal, start frontend
cd dashboard/frontend
npm run dev
```

#### Performance Tips for RPi

```bash
# Use zone-based mode (faster)
export DETECTION_MODE=zone

# Lower frame resolution
export MAX_FRAME_WIDTH=640
export MAX_FRAME_HEIGHT=480

# Reduce dashboard update frequency
export DASHBOARD_UPDATE_INTERVAL=500
```

#### Open Browser

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8765

---

## 📁 Project Structure

```
Traffic_Control/
├── .venv/                    # Python virtual environment
├── core/                     # Detection & tracking core
├── dashboard/
│   ├── backend/             # Python Flask/aiohttp server
│   │   └── requirements.txt
│   └── frontend/            # React + Vite dashboard
│       ├── package.json
│       └── node_modules/
├── traffic_signals/         # Signal control system
├── shared/                  # Shared utilities
├── config/                  # Configuration files
├── optimized_models/        # ONNX models
├── videos/                  # Input videos
├── output/                  # Output videos
├── requirements.txt         # Main Python dependencies
└── run_backend.py          # Start backend server
```

---

## 🎯 Configuration

### Backend Configuration

Edit `config/development.yaml`:

```yaml
detection:
  mode: zone # zone or line
  confidence: 0.5
  gpu_enabled: false
  frame_width: 1280
  frame_height: 720

models:
  vehicle: optimized_models/yolo11n.onnx
  ambulance: optimized_models/indian_ambulance_yolov11n_best.onnx

backend:
  host: 0.0.0.0
  port: 8765
  workers: 4
  debug: true
```

### Frontend Configuration

Edit `dashboard/frontend/vite.config.js`:

```javascript
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8765",
        changeOrigin: true,
      },
    },
  },
});
```

---

## 🚀 Running the System

### Terminal 1: Backend

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Run backend
python run_backend.py

# Expected output:
# Backend server running on http://0.0.0.0:8765
```

### Terminal 2: Frontend

```bash
# Navigate to frontend
cd dashboard/frontend

# Start development server
npm run dev

# Expected output:
# VITE v5.0.0 ready in 500 ms
# ➜  Local: http://localhost:5173/
```

### Terminal 3: Detection (Optional)

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Run detection on a video
python run_detection.py --source videos/your_video.mp4

# Or process camera
python run_detection.py --source 0
```

---

## 📊 Common Commands

### Virtual Environment

```bash
# Create
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Deactivate
deactivate

# Delete
rmdir .venv  # Windows
rm -rf .venv  # Linux/Mac
```

### Python Dependencies

```bash
# Install all
pip install -r requirements.txt
pip install -r dashboard/backend/requirements.txt

# Install specific package
pip install opencv-python==4.8.0

# List installed
pip list

# Freeze current environment
pip freeze > requirements.txt

# Update all
pip install --upgrade pip
pip install -U -r requirements.txt
```

### Node.js Dependencies

```bash
# Install
npm install

# Install specific
npm install axios@latest

# Update
npm update

# Clean install
rm -rf node_modules package-lock.json
npm install
```

### Run Scripts

```bash
# Backend
python run_backend.py

# Dashboard (separate terminal)
cd dashboard/frontend && npm run dev

# Detection
python run_detection.py --source videos/test.mp4

# Tests
python -m pytest tests/

# Lane configuration
python -m shared.config.lane_config_tool --video videos/test.mp4
```

---

## 🔧 Troubleshooting

### Python Version Issues

```bash
# Check Python version
python --version

# If wrong version, specify explicitly
python3.10 --version
python3.10 -m venv .venv

# If python3.10 not available
sudo apt install python3.10  # Linux
brew install python@3.10     # macOS
```

### Port Already in Use

```bash
# Windows - Find process on port 8765
netstat -ano | findstr :8765
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8765
kill -9 <PID>

# Or use different port
python run_backend.py --port 9000
```

### Module Not Found

```bash
# Ensure virtual environment is activated
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### npm Build Errors

```bash
# Clear npm cache
npm cache clean --force

# Clean install
rm -rf node_modules package-lock.json
npm install

# Try again
npm run dev
```

### GPU Issues (Optional)

```bash
# Install CUDA (for GPU support) - check NVIDIA website
# Then install GPU-enabled packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 📈 Performance Optimization

### Backend Performance

```bash
# Enable faster mode
export DETECTION_MODE=zone

# Increase worker threads
export BACKEND_WORKERS=8

# Lower resolution for faster processing
export MAX_FRAME_WIDTH=640
export MAX_FRAME_HEIGHT=480
```

### Frontend Performance

```bash
# Build optimized version
cd dashboard/frontend
npm run build

# Serve production build
npm install -g serve
serve -s dist
```

### System Performance

```bash
# Monitor resource usage
# Windows
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10

# Linux
top
htop

# macOS
top
```

---

## 🐛 Development Workflow

### Making Changes

```bash
# Backend: Edit files in core/, dashboard/backend/
# Changes auto-reload if you have watchdog installed

# Frontend: Edit files in dashboard/frontend/src/
# Changes auto-reload with Vite (HMR)
```

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/

# Run specific test
pytest tests/unit/test_detector.py

# Run with coverage
pytest --cov=core tests/
```

### Debugging

```bash
# Backend debug mode
DEBUG=true python run_backend.py

# Frontend debug mode
cd dashboard/frontend
npm run dev  # Vite dev server shows errors

# Python debugger
python -m pdb run_backend.py
```

---

## 🚀 Deployment (Production)

### Build Frontend for Production

```bash
cd dashboard/frontend
npm run build

# Output: dist/ folder
```

### Run Backend in Production

```bash
# Use production config
export ENV=production

# Run with gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8765 dashboard.backend.unified_server:app
```

### Using a Process Manager

```bash
# Using systemd (Linux)
sudo vim /etc/systemd/system/traffic-control.service

# Copy this:
[Unit]
Description=Traffic Control System
After=network.target

[Service]
Type=simple
User=traffic
WorkingDirectory=/home/traffic/Traffic_Control
ExecStart=/home/traffic/Traffic_Control/.venv/bin/python run_backend.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable traffic-control
sudo systemctl start traffic-control
```

---

## 📚 Related Documentation

- [`DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md) - Docker-based deployment
- [`README.md`](README.md) - Main project documentation
- [`dashboard/README.md`](dashboard/README.md) - Dashboard guide
- [`docs/`](docs/) - Detailed documentation

---

## 💡 Tips & Best Practices

✅ **DO:**

- Use virtual environment for Python
- Keep models in `optimized_models/` folder
- Use zone-based mode for better performance
- Regular git pull for updates
- Monitor resource usage

❌ **DON'T:**

- Install packages globally (use venv)
- Store videos in git repo
- Run as root (Linux)
- Ignore error messages
- Leave multiple instances running

---

**Version:** 2.2  
**Last Updated:** October 26, 2025  
**Repository:** [github.com/anonymousd3vs/Traffic_Control](https://github.com/anonymousd3vs/Traffic_Control)
