#!/usr/bin/env python3
"""
Comprehensive Requirements Audit for Traffic Control System
Verifies all dependencies are properly installed and configured

Usage:
    python check_requirements.py
"""

import subprocess
import sys
from pathlib import Path
from importlib import import_module


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"🔍 {title}")
    print(f"{'=' * 80}\n")


def check_requirements_files():
    """Verify all requirements files exist and have content"""
    print_section("REQUIREMENTS FILES VERIFICATION")

    project_root = Path(__file__).parent

    files_to_check = [
        ('requirements.txt', 'Main runtime dependencies'),
        ('dashboard/backend/requirements.txt', 'Backend-specific dependencies'),
        ('dashboard/frontend/package.json', 'Frontend React dependencies'),
    ]

    all_ok = True

    for req_file, description in files_to_check:
        full_path = project_root / req_file

        if not full_path.exists():
            print(f"❌ MISSING: {req_file}")
            print(f"   Description: {description}")
            print(f"   Expected at: {full_path}")
            all_ok = False
            continue

        file_size = full_path.stat().st_size
        print(f"✅ {req_file}")
        print(f"   Description: {description}")
        print(f"   Size: {file_size} bytes")

        # Count packages
        with open(full_path, 'r') as f:
            lines = f.readlines()

        packages = [l.strip() for l in lines if l.strip()
                    and not l.strip().startswith('#')]
        print(f"   Packages: {len(packages)}")
        print()

    return all_ok


def check_backend_requirements():
    """Verify backend has all necessary packages"""
    print_section("BACKEND REQUIREMENTS AUDIT")

    required_packages = {
        'python-socketio': 'WebSocket communication',
        'python-engineio': 'Engine.IO transport',
        'aiohttp': 'Async web framework',
        'aiohttp-cors': 'CORS support',
        'eventlet': 'Async networking',
        'requests': 'HTTP client',
        'urllib3': 'URL utilities',
        'Pillow': 'Image processing',
        'opencv-python': 'Video frame processing',
        'numpy': 'Numerical operations',
        'PyJWT': 'JWT authentication',
    }

    backend_req = Path('dashboard/backend/requirements.txt')

    if not backend_req.exists():
        print("❌ CRITICAL: dashboard/backend/requirements.txt not found!")
        return False

    with open(backend_req, 'r') as f:
        content = f.read().lower()

    print("Checking for required packages:\n")

    missing = []
    found_count = 0

    for package, purpose in required_packages.items():
        # Check various forms
        variants = [
            package.lower(),
            package.lower().replace('-', '_'),
            package.lower().replace('_', '-'),
            package.split('>')[0].lower().replace('_', '-'),
        ]

        found = any(v in content for v in variants)

        if found:
            print(f"   ✅ {package:25} - {purpose}")
            found_count += 1
        else:
            print(f"   ❌ {package:25} - {purpose}")
            missing.append(package)

    print(f"\nResult: {found_count}/{len(required_packages)} packages found")

    if missing:
        print(f"\n⚠️  Missing packages:")
        for pkg in missing:
            print(f"   • {pkg}")
        return False

    return True


def check_installed_packages():
    """Check if critical packages are actually installed"""
    print_section("INSTALLED PACKAGES CHECK")

    critical_packages = {
        'aiohttp': 'Backend web framework',
        'socketio': 'WebSocket server (python-socketio)',
        'engineio': 'Engine.IO (python-engineio)',
        'cv2': 'OpenCV video processing',
        'numpy': 'Numerical operations',
        'PIL': 'Pillow image library',
        'torch': 'PyTorch ML framework',
        'ultralytics': 'YOLO models',
        'onnxruntime': 'ONNX inference engine',
    }

    print("Checking installed packages:\n")

    not_installed = []
    installed_count = 0

    for pkg_import, description in critical_packages.items():
        try:
            mod = import_module(pkg_import)
            version = getattr(mod, '__version__', 'unknown')
            print(f"   ✅ {pkg_import:20} {version:15} - {description}")
            installed_count += 1
        except ImportError as e:
            print(f"   ❌ {pkg_import:20} - {description} [NOT INSTALLED]")
            not_installed.append((pkg_import, pkg_import))

    print(
        f"\nResult: {installed_count}/{len(critical_packages)} packages installed")

    if not_installed:
        print(f"\n⚠️  Missing packages:")
        for import_name, display_name in not_installed:
            print(f"   • {display_name}")

        print(f"\n📦 Install with:")
        print(f"   pip install -r requirements.txt")
        print(f"   pip install -r dashboard/backend/requirements.txt")
        return False

    return True


def check_backend_imports():
    """Verify backend modules can be imported"""
    print_section("BACKEND MODULES IMPORT CHECK")

    modules_to_check = [
        ('dashboard.backend._path_setup', 'Path setup'),
        ('dashboard.backend.stream_manager', 'Stream manager'),
        ('dashboard.backend.websocket_server', 'WebSocket server'),
        ('dashboard.backend.detection_controller', 'Detection controller'),
        ('dashboard.backend.detection_runner', 'Detection runner'),
        ('dashboard.backend.unified_server', 'Unified server'),
    ]

    print("Testing backend module imports:\n")

    all_imports_ok = True

    for module_path, description in modules_to_check:
        try:
            import_module(module_path)
            print(f"   ✅ {module_path:45} - {description}")
        except Exception as e:
            print(f"   ❌ {module_path:45} - {description}")
            print(f"      Error: {type(e).__name__}: {str(e)}")
            all_imports_ok = False

    return all_imports_ok


def check_core_modules():
    """Verify core detection modules are accessible"""
    print_section("CORE DETECTION MODULES CHECK")

    modules_to_check = [
        ('core.detectors.onnx_detector', 'ONNX detector'),
        ('core.detectors.traffic_detector', 'Traffic detector'),
        ('core.detectors.traffic_detector.ONNXTrafficDetector', 'Traffic detector class'),
    ]

    print("Testing core module imports:\n")

    all_imports_ok = True

    for module_path, description in modules_to_check:
        try:
            parts = module_path.split('.')
            if len(parts) > 3:  # Class import
                module_import = '.'.join(parts[:-1])
                class_name = parts[-1]
                mod = import_module(module_import)
                getattr(mod, class_name)
                print(f"   ✅ {module_path:45} - {description}")
            else:
                import_module(module_path)
                print(f"   ✅ {module_path:45} - {description}")
        except Exception as e:
            print(f"   ❌ {module_path:45} - {description}")
            print(f"      Error: {type(e).__name__}: {str(e)}")
            all_imports_ok = False

    return all_imports_ok


def check_onnx_models():
    """Check if ONNX model files exist"""
    print_section("ONNX MODELS CHECK")

    project_root = Path(__file__).parent
    models_dir = project_root / "optimized_models"

    models = {
        'yolo11n_optimized.onnx': 'Vehicle detection model',
        'indian_ambulance_yolov11n_best_optimized.onnx': 'Ambulance detection model',
    }

    print(f"Models directory: {models_dir}\n")

    all_models_ok = True

    for model_file, description in models.items():
        model_path = models_dir / model_file

        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {model_file:50} - {description}")
            print(f"      Size: {size_mb:.2f} MB")
        else:
            print(f"   ❌ {model_file:50} - {description}")
            print(f"      Expected at: {model_path}")
            all_models_ok = False

    if all_models_ok:
        print(f"\n✅ All models present and ready")
    else:
        print(f"\n⚠️  Some models missing - detection may not work")

    return all_models_ok


def generate_summary(results):
    """Generate final summary report"""
    print_section("AUDIT SUMMARY")

    checks = [
        ("Requirements files exist", results.get('req_files', False)),
        ("Backend requirements complete", results.get('backend_reqs', False)),
        ("Critical packages installed", results.get('installed', False)),
        ("Backend modules importable", results.get('backend_imports', False)),
        ("Core modules importable", results.get('core_imports', False)),
        ("ONNX models available", results.get('models', False)),
    ]

    print("Audit Results:\n")

    passed = 0
    for check_name, status in checks:
        symbol = "✅" if status else "❌"
        print(f"   {symbol} {check_name}")
        if status:
            passed += 1

    print(f"\nTotal: {passed}/{len(checks)} checks passed\n")

    if passed == len(checks):
        print("🎉 ALL CHECKS PASSED - System is ready!")
        print("\nYou can now run:")
        print("   python run_dashboard.py")
        return 0
    else:
        print("⚠️  ISSUES DETECTED - Please see above for details\n")
        print("To fix, run:")
        print("   pip install -r requirements.txt")
        print("   pip install -r dashboard/backend/requirements.txt")
        print("   cd dashboard/frontend && npm install")
        return 1


def main():
    """Run complete audit"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 +
          "REQUIREMENTS AUDIT - TRAFFIC CONTROL SYSTEM" + " " * 20 + "║")
    print("╚" + "=" * 78 + "╝")

    results = {}

    # Run checks
    results['req_files'] = check_requirements_files()
    results['backend_reqs'] = check_backend_requirements()
    results['installed'] = check_installed_packages()
    results['backend_imports'] = check_backend_imports()
    results['core_imports'] = check_core_modules()
    results['models'] = check_onnx_models()

    # Generate summary
    exit_code = generate_summary(results)

    print("=" * 80 + "\n")

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
