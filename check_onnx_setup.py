#!/usr/bin/env python3
"""
Diagnostic script to check ONNX Runtime setup and model compatibility.
Run this first if you experience crashes during model loading.

Usage:
    python check_onnx_setup.py
"""

import sys
import os
import platform
from pathlib import Path

print("=" * 80)
print("🔍 ONNX Runtime & Model Compatibility Check")
print("=" * 80)

# 1. Check Python version
print("\n1️⃣  Python Environment")
print(f"   Python version: {sys.version}")
print(f"   Platform: {platform.platform()}")
print(f"   Architecture: {platform.machine()}")

# 2. Check ONNX Runtime
print("\n2️⃣  ONNX Runtime Status")
try:
    import onnxruntime as ort
    print(f"   ✅ ONNX Runtime installed")
    print(f"   Version: {ort.__version__}")
    print(f"   Available providers: {ort.get_available_providers()}")
    
    # Check for GPU support
    if 'CUDAExecutionProvider' in ort.get_available_providers():
        print(f"   ✅ CUDA support: Available")
    else:
        print(f"   ⚠️  CUDA support: Not available (GPU inference disabled)")
        print(f"   💡 Tip: Install CUDA to enable GPU acceleration")
    
    # Check CPU support
    if 'CPUExecutionProvider' in ort.get_available_providers():
        print(f"   ✅ CPU support: Available (fallback)")
    else:
        print(f"   ❌ CPU support: Not available (this should never happen!)")
        
except ImportError as e:
    print(f"   ❌ ONNX Runtime NOT installed")
    print(f"   Error: {e}")
    print(f"   Fix: pip install onnxruntime")
    sys.exit(1)

# 3. Check required dependencies
print("\n3️⃣  Required Dependencies")
dependencies = ['numpy', 'opencv-python', 'requests']
for dep in dependencies:
    try:
        mod = __import__(dep.replace('-', '_'))
        version = getattr(mod, '__version__', 'unknown')
        print(f"   ✅ {dep}: {version}")
    except ImportError:
        print(f"   ❌ {dep}: NOT installed")
        print(f"   Fix: pip install {dep}")

# 4. Check model files
print("\n4️⃣  Model Files")
project_root = Path(__file__).parent
optimized_models_dir = project_root / "optimized_models"

models = {
    'Vehicle Model': "yolo11n_optimized.onnx",
    'Ambulance Model': "indian_ambulance_yolov11n_best_optimized.onnx"
}

all_models_ok = True
for model_name, model_file in models.items():
    model_path = optimized_models_dir / model_file
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ {model_name}: {model_file}")
        print(f"      Size: {size_mb:.2f} MB")
        print(f"      Path: {model_path}")
    else:
        print(f"   ❌ {model_name}: {model_file} NOT FOUND")
        print(f"      Expected at: {model_path}")
        all_models_ok = False

if not all_models_ok:
    print(f"\n   ⚠️  Some models are missing!")
    print(f"   Make sure all .onnx files are in: {optimized_models_dir}")

# 5. Test ONNX model loading
print("\n5️⃣  Model Loading Test")

vehicle_model_path = optimized_models_dir / "yolo11n_optimized.onnx"
ambulance_model_path = optimized_models_dir / "indian_ambulance_yolov11n_best_optimized.onnx"

def test_model_loading(model_path, model_name):
    """Test loading a single model"""
    if not model_path.exists():
        print(f"   ⏭️  Skipping {model_name} (file not found)")
        return False
    
    try:
        print(f"   Loading {model_name}...")
        import onnxruntime as ort
        
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        providers = [p for p in providers if p in ort.get_available_providers()]
        
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        session = ort.InferenceSession(str(model_path), sess_options, providers=providers)
        
        print(f"   ✅ {model_name} loaded successfully!")
        print(f"      Providers used: {session.get_providers()}")
        
        # Get input details
        input_name = session.get_inputs()[0].name
        input_shape = session.get_inputs()[0].shape
        output_names = [out.name for out in session.get_outputs()]
        
        print(f"      Input: {input_name} {input_shape}")
        print(f"      Outputs: {len(output_names)} output(s)")
        
        # Test warmup
        import numpy as np
        print(f"      Running warmup inference...")
        dummy_input = np.zeros((1, 3, 640, 640), dtype=np.float32)
        outputs = session.run(None, {input_name: dummy_input})
        print(f"      ✅ Warmup successful, got {len(outputs)} output(s)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error loading {model_name}: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return False

vehicle_ok = test_model_loading(vehicle_model_path, "Vehicle Model")
print()
ambulance_ok = test_model_loading(ambulance_model_path, "Ambulance Model")

# 6. Summary and recommendations
print("\n" + "=" * 80)
print("📋 Summary")
print("=" * 80)

if vehicle_ok and ambulance_ok:
    print("✅ All checks passed! Your system is ready for traffic detection.")
    print("\nYou can now run:")
    print("  python run_dashboard.py")
elif vehicle_ok and not ambulance_ok:
    print("⚠️  Vehicle model OK, but ambulance model failed to load")
    print("   - You can still detect vehicles")
    print("   - Ambulance detection will be disabled")
    print("   - This may indicate ONNX Runtime or model compatibility issue")
else:
    print("❌ Critical issues found!")
    print("\nCommon fixes:")
    print("   1. Reinstall dependencies:")
    print("      pip install --upgrade onnxruntime numpy opencv-python")
    print("")
    print("   2. Verify model files exist:")
    print(f"      ls {optimized_models_dir}/")
    print("")
    print("   3. Check Python version (requires Python 3.8+):")
    print("      python --version")
    print("")
    print("   4. If using GPU, ensure CUDA is properly installed:")
    print("      Check NVIDIA GPU drivers")
    print("")
    print("   5. Try CPU-only mode by removing GPU providers")

print("\n" + "=" * 80)
