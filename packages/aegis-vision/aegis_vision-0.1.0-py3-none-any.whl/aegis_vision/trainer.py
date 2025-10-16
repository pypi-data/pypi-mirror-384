"""
YOLO Trainer for Aegis Vision
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)


class YOLOTrainer:
    """
    YOLO model trainer with Wandb integration and multi-format export
    """
    
    def __init__(
        self,
        model_variant: str = "yolov8n",
        dataset_path: str = None,
        epochs: int = 100,
        batch_size: int = 16,
        img_size: int = 640,
        learning_rate: float = 0.01,
        momentum: float = 0.937,
        weight_decay: float = 0.0005,
        warmup_epochs: int = 3,
        patience: int = 50,
        output_formats: Optional[List[str]] = None,
        training_mode: str = "fine_tune",
        device: str = "0",
    ):
        """
        Initialize YOLO trainer
        
        Args:
            model_variant: YOLO model variant (yolov8n, yolov11l, etc.)
            dataset_path: Path to dataset.yaml file
            epochs: Number of training epochs
            batch_size: Batch size for training
            img_size: Input image size
            learning_rate: Initial learning rate
            momentum: SGD momentum
            weight_decay: Weight decay for regularization
            warmup_epochs: Number of warmup epochs
            patience: Early stopping patience
            output_formats: List of export formats ['onnx', 'coreml', etc.]
            training_mode: 'fine_tune' or 'from_scratch'
            device: Device ID ('0' for GPU, 'cpu' for CPU)
        """
        self.model_variant = model_variant
        self.dataset_path = Path(dataset_path) if dataset_path else None
        self.epochs = epochs
        self.batch_size = batch_size
        self.img_size = img_size
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.warmup_epochs = warmup_epochs
        self.patience = patience
        self.output_formats = output_formats or []
        self.training_mode = training_mode
        self.device = device
        
        # State
        self.model = None
        self.results = None
        self.wandb_run = None
        self.output_dir = Path("/kaggle/working") if Path("/kaggle").exists() else Path("runs")
        
        logger.info(f"YOLOTrainer initialized: {model_variant}, {epochs} epochs")
    
    def setup_wandb(
        self,
        project: str,
        entity: Optional[str] = None,
        api_key: Optional[str] = None,
        run_name: Optional[str] = None,
    ):
        """
        Setup Wandb experiment tracking
        
        Args:
            project: Wandb project name
            entity: Wandb entity/team name
            api_key: Wandb API key
            run_name: Custom run name
        """
        try:
            import wandb
            import os
            
            # Set environment variables
            if api_key:
                os.environ['WANDB_API_KEY'] = api_key
            
            # Login
            wandb.login(key=api_key, relogin=True)
            
            # Initialize run
            self.wandb_run = wandb.init(
                project=project,
                entity=entity,
                name=run_name or f"{self.model_variant}_training",
                config={
                    'model': self.model_variant,
                    'epochs': self.epochs,
                    'batch_size': self.batch_size,
                    'img_size': self.img_size,
                    'learning_rate': self.learning_rate,
                    'training_mode': self.training_mode,
                },
                tags=['yolo', self.model_variant, 'aegis-vision']
            )
            
            # Enable Wandb in Ultralytics
            from ultralytics import settings
            settings.update({'wandb': True})
            
            logger.info(f"✅ Wandb initialized: {project}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Wandb: {e}")
            return False
    
    def train(self) -> Dict[str, Any]:
        """
        Train the YOLO model
        
        Returns:
            Training results dictionary
        """
        try:
            from ultralytics import YOLO
            
            logger.info(f"🤖 Loading model: {self.model_variant}")
            
            # Load model
            if self.training_mode == "from_scratch":
                model_path = f"{self.model_variant}.yaml"
            else:
                model_path = f"{self.model_variant}.pt"
            
            self.model = YOLO(model_path)
            logger.info(f"✅ Model loaded: {model_path}")
            
            # Train
            logger.info(f"🚀 Starting training...")
            self.results = self.model.train(
                data=str(self.dataset_path),
                epochs=self.epochs,
                imgsz=self.img_size,
                batch=self.batch_size,
                project=str(self.output_dir),
                name="train",
                patience=self.patience,
                save=True,
                save_period=10,
                device=self.device,
                workers=8,
                exist_ok=True,
                pretrained=(self.training_mode == "fine_tune"),
                optimizer="auto",
                lr0=self.learning_rate,
                momentum=self.momentum,
                weight_decay=self.weight_decay,
                warmup_epochs=self.warmup_epochs,
                augment=True,
            )
            
            logger.info("✅ Training completed!")
            
            return {
                "success": True,
                "model_path": str(self.output_dir / "train" / "weights" / "best.pt"),
                "metrics": self._extract_metrics(),
            }
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    def export(self, formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export trained model to multiple formats
        
        Args:
            formats: List of formats ['onnx', 'coreml', 'openvino', etc.]
            
        Returns:
            Export results dictionary
        """
        if not self.model:
            raise RuntimeError("Model not trained yet. Call train() first.")
        
        formats = formats or self.output_formats
        if not formats:
            logger.info("No export formats specified")
            return {"success": True, "exported": []}
        
        logger.info(f"📤 Exporting to {len(formats)} formats: {', '.join(formats)}")
        
        successful = []
        failed = []
        
        for fmt in formats:
            try:
                logger.info(f"⏳ Exporting to {fmt.upper()}...")
                self.model.export(format=fmt)
                logger.info(f"✅ Successfully exported to {fmt.upper()}")
                successful.append(fmt)
            except Exception as e:
                logger.error(f"❌ Failed to export {fmt.upper()}: {e}")
                failed.append(fmt)
        
        logger.info(f"📊 Export Summary: {len(successful)}/{len(formats)} successful")
        
        return {
            "success": len(failed) == 0,
            "successful": successful,
            "failed": failed,
        }
    
    def validate(self) -> Dict[str, Any]:
        """
        Run validation on trained model
        
        Returns:
            Validation metrics
        """
        if not self.model:
            raise RuntimeError("Model not trained yet. Call train() first.")
        
        logger.info("📊 Running validation...")
        metrics = self.model.val()
        
        return {
            "map50": metrics.box.map50,
            "map50_95": metrics.box.map,
            "precision": metrics.box.mp,
            "recall": metrics.box.mr,
        }
    
    def prepare_kaggle_output(self, output_dir: Path = None):
        """
        Prepare model outputs for Kaggle download
        
        Args:
            output_dir: Output directory (default: /kaggle/working/trained_models)
        """
        if output_dir is None:
            output_dir = Path("/kaggle/working/trained_models")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        weights_dir = self.output_dir / "train" / "weights"
        
        if not weights_dir.exists():
            logger.warning(f"Weights directory not found: {weights_dir}")
            return
        
        logger.info(f"📦 Copying models to {output_dir}")
        
        # Copy all files from weights directory
        for item in weights_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, output_dir / item.name)
                logger.info(f"✅ Copied: {item.name}")
            elif item.is_dir():
                # Handle directory exports (e.g., CoreML .mlpackage)
                dst = output_dir / item.name
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(item, dst)
                logger.info(f"✅ Copied directory: {item.name}")
        
        # Make files readable
        for item in output_dir.iterdir():
            if item.is_file():
                os.chmod(item, 0o644)
            elif item.is_dir():
                os.chmod(item, 0o755)
        
        logger.info(f"✅ Models prepared for download at {output_dir}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get training metrics"""
        return self._extract_metrics()
    
    def _extract_metrics(self) -> Dict[str, Any]:
        """Extract metrics from training results"""
        if not self.results:
            return {}
        
        try:
            # Try to extract metrics from results
            metrics = {}
            if hasattr(self.results, 'results_dict'):
                metrics = self.results.results_dict
            elif hasattr(self.results, 'metrics'):
                metrics = self.results.metrics
            
            return {
                "map50": metrics.get('metrics/mAP50(B)', 0),
                "map50_95": metrics.get('metrics/mAP50-95(B)', 0),
                "precision": metrics.get('metrics/precision(B)', 0),
                "recall": metrics.get('metrics/recall(B)', 0),
            }
        except Exception as e:
            logger.warning(f"Failed to extract metrics: {e}")
            return {}
