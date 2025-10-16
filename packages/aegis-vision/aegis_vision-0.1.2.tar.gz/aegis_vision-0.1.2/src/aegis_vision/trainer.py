"""
YOLO Trainer for Aegis Vision
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class YOLOTrainer:
    """
    Unified YOLO trainer supporting YOLOv8-v11
    """
    
    def __init__(
        self,
        model_variant: str = "yolov8n",
        dataset_path: Optional[str] = None,
        epochs: int = 10,
        batch_size: int = 16,
        img_size: int = 640,
        output_formats: Optional[List[str]] = None,
        learning_rate: float = 0.01,
        momentum: float = 0.937,
        weight_decay: float = 0.0005,
        warmup_epochs: int = 3,
        patience: int = 50,
    ):
        """
        Initialize YOLO trainer
        
        Args:
            model_variant: Model variant (e.g., "yolov8n", "yolo11l")
            dataset_path: Path to dataset.yaml
            epochs: Number of training epochs
            batch_size: Batch size
            img_size: Input image size
            output_formats: List of export formats (e.g., ["onnx", "coreml"])
            learning_rate: Initial learning rate
            momentum: SGD momentum
            weight_decay: Weight decay factor
            warmup_epochs: Number of warmup epochs
            patience: Early stopping patience
        """
        self.model_variant = model_variant
        self.dataset_path = dataset_path
        self.epochs = epochs
        self.batch_size = batch_size
        self.img_size = img_size
        self.output_formats = output_formats or []
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.warmup_epochs = warmup_epochs
        self.patience = patience
        
        self.model = None
        self.results = None
        self.wandb_enabled = False
        
        # Auto-detect Kaggle environment
        self.working_dir = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path.cwd()
        self.output_dir = self.working_dir / "runs"
    
    def setup_wandb(
        self,
        project: str,
        entity: Optional[str] = None,
        api_key: Optional[str] = None,
        run_name: Optional[str] = None,
    ) -> None:
        """
        Setup Weights & Biases tracking
        
        Args:
            project: Wandb project name
            entity: Wandb entity/username
            api_key: Wandb API key
            run_name: Name for this run
        """
        try:
            import wandb
            import ultralytics
            
            # Set environment variables
            if api_key:
                os.environ['WANDB_API_KEY'] = api_key
            if project:
                os.environ['WANDB_PROJECT'] = project
            if entity:
                os.environ['WANDB_ENTITY'] = entity
            if run_name:
                os.environ['WANDB_NAME'] = run_name
            
            # Prevent RANK errors
            os.environ['RANK'] = '-1'
            os.environ['WANDB_MODE'] = 'online'
            
            # Login to wandb
            if api_key:
                wandb.login(key=api_key)
            
            # Initialize wandb run
            wandb.init(
                project=project,
                entity=entity,
                name=run_name,
                config={
                    "model_variant": self.model_variant,
                    "epochs": self.epochs,
                    "batch_size": self.batch_size,
                    "img_size": self.img_size,
                    "learning_rate": self.learning_rate,
                    "momentum": self.momentum,
                    "weight_decay": self.weight_decay,
                }
            )
            
            # Enable wandb in Ultralytics settings
            ultralytics.settings.update({'wandb': True})
            
            self.wandb_enabled = True
            logger.info(f"✅ Wandb tracking enabled: {project}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup Wandb: {e}")
            self.wandb_enabled = False
    
    def train(self) -> Dict[str, Any]:
        """
        Train the YOLO model
        
        Returns:
            Training results dictionary
        """
        from ultralytics import YOLO
        
        logger.info(f"🤖 Initializing {self.model_variant} model...")
        
        # Try different model naming conventions (yolov11l vs yolo11l)
        # YOLOv11 models use 'yolo11' not 'yolov11'
        model_variants_to_try = []
        
        # For v11 models, try yolo11 first (correct naming)
        if 'v11' in self.model_variant:
            alternative = self.model_variant.replace('yolov11', 'yolo11')
            model_variants_to_try = [alternative, self.model_variant]
        else:
            model_variants_to_try = [self.model_variant]
        
        last_error = None
        for variant in model_variants_to_try:
            try:
                model_path = f'{variant}.pt'
                logger.info(f"⬇️ Attempting to load: {model_path}")
                self.model = YOLO(model_path)
                logger.info(f"✅ Loaded model: {model_path}")
                break
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Failed to load {variant}.pt: {str(e)}")
                continue
        
        if self.model is None:
            raise FileNotFoundError(
                f"Model not found after trying: {', '.join([f'{v}.pt' for v in model_variants_to_try])}\n"
                f"Valid models: yolov8n/s/m/l/x, yolov9t/s/m/c/e, yolov10n/s/m/b/l/x, yolo11n/s/m/l/x\n"
                f"Last error: {last_error}"
            )
        
        logger.info(f"🚀 Starting training for {self.epochs} epochs...")
        
        # Train the model
        self.results = self.model.train(
            data=self.dataset_path,
            epochs=self.epochs,
            batch=self.batch_size,
            imgsz=self.img_size,
            lr0=self.learning_rate,
            momentum=self.momentum,
            weight_decay=self.weight_decay,
            warmup_epochs=self.warmup_epochs,
            patience=self.patience,
            project=str(self.output_dir),
            name="train",
            exist_ok=True,
            verbose=True,
        )
        
        logger.info("✅ Training completed!")
        
        return {
            "success": True,
            "output_dir": str(self.output_dir / "train"),
        }
    
    def export(self, formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export model to various formats
        
        Args:
            formats: List of export formats (onnx, coreml, openvino, tensorrt, tflite)
            
        Returns:
            Export results dictionary
        """
        if not self.model:
            raise RuntimeError("Model not trained yet. Call train() first.")
        
        formats = formats or self.output_formats
        if not formats:
            logger.info("No export formats specified, skipping export")
            return {"exported": []}
        
        logger.info(f"📤 Exporting model to {len(formats)} formats...")
        
        exported = []
        failed = []
        
        for fmt in formats:
            try:
                logger.info(f"  Exporting to {fmt.upper()}...")
                self.model.export(format=fmt)
                exported.append(fmt)
                logger.info(f"  ✅ {fmt.upper()} export successful")
            except Exception as e:
                failed.append(fmt)
                logger.warning(f"  ⚠️ {fmt.upper()} export failed: {str(e)}")
                
                # Provide specific guidance for known issues
                if fmt == "tensorrt":
                    logger.warning("  💡 TensorRT requires specific GPU architecture (SM 75+)")
                elif fmt == "tflite":
                    logger.warning("  💡 TFLite may fail due to CuDNN version or onnx2tf issues")
        
        logger.info(f"✅ Export complete: {len(exported)} succeeded, {len(failed)} failed")
        
        return {
            "exported": exported,
            "failed": failed,
            "total": len(formats),
        }
    
    def prepare_kaggle_output(self, output_dir: Optional[Path] = None) -> None:
        """
        Prepare models for Kaggle output download
        
        Args:
            output_dir: Output directory (default: /kaggle/working/trained_models)
        """
        if not self.model:
            raise RuntimeError("Model not trained yet. Call train() first.")
        
        output_dir = output_dir or (self.working_dir / "trained_models")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📦 Preparing models for download...")
        
        # Source directory (where training outputs are)
        weights_dir = self.output_dir / "train" / "weights"
        
        if not weights_dir.exists():
            logger.warning(f"⚠️ Weights directory not found: {weights_dir}")
            return
        
        # Copy all model files
        copied_count = 0
        for file_path in weights_dir.iterdir():
            try:
                dst = output_dir / file_path.name
                
                if file_path.is_dir():
                    # Handle directories (e.g., .mlpackage)
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(file_path, dst)
                else:
                    # Handle regular files
                    shutil.copy2(file_path, dst)
                
                logger.info(f"✅ Copied {file_path.name} to {output_dir}")
                copied_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to copy {file_path.name}: {e}")
        
        logger.info(f"✅ Prepared {copied_count} model files for download")
