#!/usr/bin/env python3
"""
Re-optimize ONNX models for Raspberry Pi 5
Uses basic optimizations without custom operators
"""

import onnxruntime as ort
from pathlib import Path
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_model(input_path, output_path, model_name=""):
    """Optimize ONNX model with basic optimizations only."""
    try:
        logger.info(f"Loading {model_name} from {input_path}")
        
        # Configure session options for basic optimizations
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        sess_options.optimized_model_filepath = str(output_path)
        
        # Create session with basic optimizations
        session = ort.InferenceSession(str(input_path), sess_options, 
                                     providers=['CPUExecutionProvider'])
        
        logger.info(f"✅ Model optimized and saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error optimizing {model_name}: {str(e)}")
        return False

def main():
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "models"
    optimized_dir = project_root / "optimized_models"
    
    # Ensure directories exist
    optimized_dir.mkdir(exist_ok=True)
    
    # Models to optimize
    models = {
        "Vehicle Detection": ("yolo11n.onnx", "yolo11n_optimized.onnx"),
        "Ambulance Detection": ("indian_ambulance_yolov11n_best.onnx", 
                              "indian_ambulance_yolov11n_best_optimized.onnx")
    }
    
    print("\n=== ONNX Model Optimizer for Raspberry Pi 5 ===")
    
    success = True
    for model_name, (src, dst) in models.items():
        src_path = models_dir / src
        dst_path = optimized_dir / dst
        
        # Backup existing optimized model if it exists
        if dst_path.exists():
            backup_path = dst_path.with_suffix('.onnx.bak')
            logger.info(f"Backing up existing {dst} to {backup_path.name}")
            shutil.move(dst_path, backup_path)
        
        if optimize_model(src_path, dst_path, model_name):
            logger.info(f"✅ {model_name} optimization successful")
        else:
            success = False
            logger.error(f"❌ {model_name} optimization failed")
    
    if success:
        print("\n✅ All models optimized successfully for Raspberry Pi 5!")
    else:
        print("\n❌ Some models failed to optimize. Check the logs above.")

if __name__ == "__main__":
    main()