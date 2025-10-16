"""
Dataset format converters for Aegis Vision
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class COCOConverter:
    """Convert COCO format datasets to YOLO format"""
    
    def __init__(
        self,
        annotations_file: str,
        images_dir: str,
        output_dir: str,
        labels_filter: Optional[List[str]] = None,
        min_object_size: int = 0,
        train_split: float = 0.8,
    ):
        """
        Initialize COCO to YOLO converter
        
        Args:
            annotations_file: Path to COCO annotations.json
            images_dir: Directory containing images
            output_dir: Output directory for YOLO dataset
            labels_filter: Optional list of labels to include (None = all)
            min_object_size: Minimum bounding box size (pixels)
            train_split: Fraction of data for training (rest for validation)
        """
        self.annotations_file = Path(annotations_file)
        self.images_dir = Path(images_dir)
        self.output_dir = Path(output_dir)
        self.labels_filter = labels_filter
        self.min_object_size = min_object_size
        self.train_split = train_split
        
        # Statistics
        self.stats = {
            "total_images": 0,
            "total_annotations": 0,
            "filtered_annotations": 0,
            "train_images": 0,
            "val_images": 0,
            "categories": []
        }
    
    def convert(self) -> Dict:
        """
        Perform conversion
        
        Returns:
            Dictionary containing conversion statistics
        """
        logger.info(f"Converting COCO dataset from {self.annotations_file}")
        
        # Load COCO annotations
        with open(self.annotations_file, 'r') as f:
            coco_data = json.load(f)
        
        # Extract categories
        categories = {cat['id']: cat['name'] for cat in coco_data.get('categories', [])}
        
        # Filter categories if specified
        if self.labels_filter:
            filtered_cats = {
                cat_id: name for cat_id, name in categories.items()
                if name in self.labels_filter
            }
            categories = filtered_cats
        
        self.stats['categories'] = list(categories.values())
        
        # Create output structure
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'images' / 'train').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'images' / 'val').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'labels' / 'train').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'labels' / 'val').mkdir(parents=True, exist_ok=True)
        
        # Create class mapping (YOLO uses 0-indexed classes)
        class_mapping = {cat_id: idx for idx, cat_id in enumerate(categories.keys())}
        
        # Group annotations by image
        image_annotations = {}
        for ann in coco_data.get('annotations', []):
            cat_id = ann.get('category_id')
            if cat_id not in categories:
                continue
            
            image_id = ann['image_id']
            if image_id not in image_annotations:
                image_annotations[image_id] = []
            image_annotations[image_id].append(ann)
        
        # Process images
        images = coco_data.get('images', [])
        self.stats['total_images'] = len(images)
        
        train_count = int(len(images) * self.train_split)
        
        for idx, img_info in enumerate(images):
            split = 'train' if idx < train_count else 'val'
            self._process_image(
                img_info,
                image_annotations.get(img_info['id'], []),
                categories,
                class_mapping,
                split
            )
        
        # Create dataset.yaml
        self._create_dataset_yaml(categories, class_mapping)
        
        logger.info(f"✅ Conversion complete: {self.stats}")
        return self.stats
    
    def _process_image(
        self,
        img_info: Dict,
        annotations: List[Dict],
        categories: Dict,
        class_mapping: Dict,
        split: str
    ):
        """Process a single image and its annotations"""
        img_filename = img_info['file_name']
        img_width = img_info['width']
        img_height = img_info['height']
        
        # Copy image (or create symlink)
        src_path = self.images_dir / img_filename
        dst_path = self.output_dir / 'images' / split / img_filename
        
        if src_path.exists():
            import shutil
            shutil.copy2(src_path, dst_path)
        
        # Convert annotations to YOLO format
        yolo_annotations = []
        for ann in annotations:
            bbox = ann['bbox']  # [x, y, width, height]
            
            # Filter small objects
            if bbox[2] < self.min_object_size or bbox[3] < self.min_object_size:
                self.stats['filtered_annotations'] += 1
                continue
            
            # Convert to YOLO format (normalized center x, y, width, height)
            x_center = (bbox[0] + bbox[2] / 2) / img_width
            y_center = (bbox[1] + bbox[3] / 2) / img_height
            width = bbox[2] / img_width
            height = bbox[3] / img_height
            
            class_id = class_mapping[ann['category_id']]
            yolo_annotations.append(f"{class_id} {x_center} {y_center} {width} {height}")
            self.stats['total_annotations'] += 1
        
        # Write label file
        if yolo_annotations:
            label_path = self.output_dir / 'labels' / split / f"{Path(img_filename).stem}.txt"
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_annotations))
        
        if split == 'train':
            self.stats['train_images'] += 1
        else:
            self.stats['val_images'] += 1
    
    def _create_dataset_yaml(self, categories: Dict, class_mapping: Dict):
        """Create YOLO dataset.yaml configuration"""
        yaml_content = f"""# Aegis Vision - YOLO Dataset Configuration
# Auto-generated from COCO format

path: {self.output_dir.absolute()}
train: images/train
val: images/val

# Classes
nc: {len(categories)}  # number of classes
names: {list(categories.values())}  # class names
"""
        
        yaml_path = self.output_dir / 'dataset.yaml'
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        logger.info(f"✅ Created dataset.yaml at {yaml_path}")
    
    def validate(self) -> bool:
        """Validate the converted dataset"""
        # Check if required files exist
        required_paths = [
            self.output_dir / 'dataset.yaml',
            self.output_dir / 'images' / 'train',
            self.output_dir / 'images' / 'val',
            self.output_dir / 'labels' / 'train',
            self.output_dir / 'labels' / 'val',
        ]
        
        for path in required_paths:
            if not path.exists():
                logger.error(f"Missing required path: {path}")
                return False
        
        logger.info("✅ Dataset validation passed")
        return True
    
    def get_statistics(self) -> Dict:
        """Get conversion statistics"""
        return self.stats


