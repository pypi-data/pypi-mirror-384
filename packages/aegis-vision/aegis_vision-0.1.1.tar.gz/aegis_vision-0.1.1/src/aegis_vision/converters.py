"""
Dataset converters for Aegis Vision
"""

import json
import random
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


class COCOConverter:
    """
    Convert COCO format annotations to YOLO format
    """
    
    def __init__(
        self,
        annotations_file: str,
        images_dir: str,
        output_dir: str,
        train_split: float = 0.8
    ):
        """
        Initialize COCO to YOLO converter
        
        Args:
            annotations_file: Path to COCO JSON file
            images_dir: Path to images directory
            output_dir: Path to output directory
            train_split: Fraction of data for training (default: 0.8)
        """
        self.annotations_file = Path(annotations_file)
        self.images_dir = Path(images_dir)
        self.output_dir = Path(output_dir)
        self.train_split = train_split
        
        # Validate inputs
        if not self.annotations_file.exists():
            raise FileNotFoundError(f"Annotations file not found: {annotations_file}")
        if not self.images_dir.exists():
            raise FileNotFoundError(f"Images directory not found: {images_dir}")
    
    def convert(self) -> Dict[str, Any]:
        """
        Convert COCO annotations to YOLO format
        
        Returns:
            Statistics dictionary
        """
        # Load COCO data
        with open(self.annotations_file, 'r') as f:
            coco_data = json.load(f)
        
        # Extract categories
        categories = {cat['id']: cat['name'] for cat in coco_data.get('categories', [])}
        labels = list(categories.values())
        label_to_id = {label: idx for idx, label in enumerate(labels)}
        
        # Create temporary output directory
        temp_output = self.output_dir / "temp"
        temp_labels_dir = temp_output / "labels"
        temp_images_dir = temp_output / "images"
        temp_labels_dir.mkdir(parents=True, exist_ok=True)
        temp_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert annotations
        images_processed = 0
        annotations_converted = 0
        
        for image_data in coco_data.get('images', []):
            image_id = image_data['id']
            image_filename = image_data['file_name']
            image_width = image_data['width']
            image_height = image_data['height']
            
            # Get annotations for this image
            image_annotations = [
                ann for ann in coco_data.get('annotations', [])
                if ann['image_id'] == image_id
            ]
            
            if not image_annotations:
                continue
            
            # Convert to YOLO format
            yolo_annotations = []
            for ann in image_annotations:
                category_id = ann['category_id']
                category_name = categories.get(category_id)
                
                if not category_name or category_name not in label_to_id:
                    continue
                
                # Convert bbox from [x, y, w, h] to YOLO format (normalized)
                bbox = ann['bbox']
                x_center = (bbox[0] + bbox[2] / 2) / image_width
                y_center = (bbox[1] + bbox[3] / 2) / image_height
                width = bbox[2] / image_width
                height = bbox[3] / image_height
                
                class_id = label_to_id[category_name]
                
                yolo_annotations.append(
                    f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                )
                annotations_converted += 1
            
            if yolo_annotations:
                # Copy image
                src_image = self.images_dir / image_filename
                dst_image = temp_images_dir / image_filename
                if src_image.exists():
                    shutil.copy2(src_image, dst_image)
                    
                    # Write YOLO annotation file
                    label_filename = Path(image_filename).stem + '.txt'
                    label_path = temp_labels_dir / label_filename
                    with open(label_path, 'w') as f:
                        f.write('\n'.join(yolo_annotations))
                    
                    images_processed += 1
        
        # Split dataset into train/val
        image_files = list(temp_images_dir.glob("*.jpg")) + \
                     list(temp_images_dir.glob("*.png")) + \
                     list(temp_images_dir.glob("*.jpeg"))
        
        random.shuffle(image_files)
        split_idx = int(len(image_files) * self.train_split)
        train_images = image_files[:split_idx]
        val_images = image_files[split_idx:]
        
        # Create final directory structure
        train_images_dir = self.output_dir / "images" / "train"
        val_images_dir = self.output_dir / "images" / "val"
        train_labels_dir = self.output_dir / "labels" / "train"
        val_labels_dir = self.output_dir / "labels" / "val"
        
        for directory in [train_images_dir, val_images_dir, train_labels_dir, val_labels_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Move files to train/val splits
        for img in train_images:
            shutil.move(str(img), str(train_images_dir / img.name))
            label_file = temp_labels_dir / (img.stem + '.txt')
            if label_file.exists():
                shutil.move(str(label_file), str(train_labels_dir / label_file.name))
        
        for img in val_images:
            shutil.move(str(img), str(val_images_dir / img.name))
            label_file = temp_labels_dir / (img.stem + '.txt')
            if label_file.exists():
                shutil.move(str(label_file), str(val_labels_dir / label_file.name))
        
        # Clean up temp directory
        shutil.rmtree(temp_output)
        
        # Create dataset.yaml
        self._create_dataset_yaml(labels)
        
        return {
            "images_processed": images_processed,
            "annotations_converted": annotations_converted,
            "train_count": len(train_images),
            "val_count": len(val_images),
            "num_classes": len(labels),
            "labels": labels,
        }
    
    def _create_dataset_yaml(self, labels: List[str]) -> Path:
        """
        Create dataset.yaml file for YOLO training
        
        Args:
            labels: List of class labels
            
        Returns:
            Path to created dataset.yaml
        """
        yaml_content = f"""# Aegis Vision Dataset Configuration
path: {self.output_dir.absolute()}
train: images/train
val: images/val

# Classes
nc: {len(labels)}
names: {labels}
"""
        
        yaml_path = self.output_dir / "dataset.yaml"
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        return yaml_path
