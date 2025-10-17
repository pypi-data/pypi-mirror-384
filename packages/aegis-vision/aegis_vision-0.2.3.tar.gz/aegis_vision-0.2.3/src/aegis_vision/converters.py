"""
Dataset converters for Aegis Vision
"""

import json
import random
import shutil
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


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


class DatasetMerger:
    """
    Merge multiple datasets (COCO or YOLO format) into a single unified dataset
    """
    
    def __init__(self, output_dir: str, train_split: float = 0.8):
        """
        Initialize dataset merger
        
        Args:
            output_dir: Path to output directory for merged dataset
            train_split: Fraction of data for training (default: 0.8)
        """
        self.output_dir = Path(output_dir)
        self.train_split = train_split
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def merge(self, dataset_paths: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Merge multiple datasets into one
        
        Args:
            dataset_paths: List of tuples (dataset_path, format) where format is 'coco' or 'yolo'
            
        Returns:
            Statistics dictionary with merge results
        """
        all_images = []
        all_labels_data = []  # Store (image_path, label_path, dataset_name, dataset_labels)
        unified_label_set = set()
        
        # Temporary directory for converted datasets
        temp_dir = self.output_dir / "temp_converted"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each dataset
        for idx, (dataset_path, dataset_format) in enumerate(dataset_paths):
            ds_path = Path(dataset_path)
            ds_name = ds_path.name
            
            print(f"📁 Processing {ds_name} ({dataset_format} format)...")
            
            if dataset_format.lower() == "coco":
                # Convert COCO to YOLO format first
                converted_dir = temp_dir / f"converted_{idx}_{ds_name}"
                converter = COCOConverter(
                    annotations_file=str(ds_path / "annotations.json"),
                    images_dir=str(ds_path / "images"),
                    output_dir=str(converted_dir),
                    train_split=1.0  # Don't split yet
                )
                stats = converter.convert()
                print(f"  ✅ Converted: {stats['images_processed']} images")
                
                # Get labels
                ds_labels = stats['labels']
                unified_label_set.update(ds_labels)
                
                # Collect images and labels
                img_dir = converted_dir / "images" / "train"
                lbl_dir = converted_dir / "labels" / "train"
                
                for img_file in img_dir.glob("*.*"):
                    lbl_file = lbl_dir / (img_file.stem + ".txt")
                    if lbl_file.exists():
                        all_images.append(img_file)
                        all_labels_data.append((img_file, lbl_file, ds_name, ds_labels))
            
            elif dataset_format.lower() == "yolo":
                # Load YOLO dataset configuration
                yolo_yaml_path = ds_path / "dataset.yaml"
                if not yolo_yaml_path.exists():
                    print(f"  ⚠️  Warning: dataset.yaml not found in {ds_path}")
                    continue
                
                with open(yolo_yaml_path, 'r') as f:
                    ds_config = yaml.safe_load(f)
                    ds_labels = ds_config.get('names', [])
                    unified_label_set.update(ds_labels)
                
                # Collect images and labels from train/val
                for split in ['train', 'val']:
                    img_dir = ds_path / "images" / split
                    lbl_dir = ds_path / "labels" / split
                    
                    if img_dir.exists() and lbl_dir.exists():
                        for img_file in img_dir.glob("*.*"):
                            lbl_file = lbl_dir / (img_file.stem + ".txt")
                            if lbl_file.exists():
                                all_images.append(img_file)
                                all_labels_data.append((img_file, lbl_file, ds_name, ds_labels))
        
        print(f"📊 Found {len(all_images)} images from {len(dataset_paths)} datasets")
        
        # Create unified label list (sorted for consistency)
        unified_labels = sorted(list(unified_label_set))
        unified_label_map = {label: idx for idx, label in enumerate(unified_labels)}
        
        print(f"🏷️  Unified labels ({len(unified_labels)}): {unified_labels}")
        
        # Copy images and remap labels
        print("📋 Copying images and remapping labels...")
        temp_merged_images = self.output_dir / "temp_merged_images"
        temp_merged_labels = self.output_dir / "temp_merged_labels"
        temp_merged_images.mkdir(parents=True, exist_ok=True)
        temp_merged_labels.mkdir(parents=True, exist_ok=True)
        
        for img_file, lbl_file, ds_name, ds_labels in all_labels_data:
            # Create unique filename with dataset prefix
            new_img_name = f"{ds_name}_{img_file.name}"
            new_lbl_name = f"{ds_name}_{img_file.stem}.txt"
            
            # Copy image
            shutil.copy2(img_file, temp_merged_images / new_img_name)
            
            # Remap and copy labels
            with open(lbl_file, 'r') as f:
                lines = f.readlines()
            
            remapped_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    old_class_id = int(parts[0])
                    # Get the label name from old dataset
                    if old_class_id < len(ds_labels):
                        old_label = ds_labels[old_class_id]
                        # Map to new unified class ID
                        new_class_id = unified_label_map.get(old_label)
                        if new_class_id is not None:
                            parts[0] = str(new_class_id)
                            remapped_lines.append(' '.join(parts))
            
            with open(temp_merged_labels / new_lbl_name, 'w') as f:
                f.write('\n'.join(remapped_lines))
        
        print(f"✅ Copied and remapped {len(all_labels_data)} images")
        
        # Split into train/val
        print("🔀 Splitting merged dataset into train/val...")
        all_merged_images = list(temp_merged_images.glob("*.*"))
        random.shuffle(all_merged_images)
        
        split_idx = int(len(all_merged_images) * self.train_split)
        train_images = all_merged_images[:split_idx]
        val_images = all_merged_images[split_idx:]
        
        # Create train/val directories
        train_img_dir = self.output_dir / "images" / "train"
        val_img_dir = self.output_dir / "images" / "val"
        train_lbl_dir = self.output_dir / "labels" / "train"
        val_lbl_dir = self.output_dir / "labels" / "val"
        
        for directory in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Move files to train/val
        for img in train_images:
            lbl = temp_merged_labels / (img.stem + ".txt")
            shutil.move(str(img), str(train_img_dir / img.name))
            if lbl.exists():
                shutil.move(str(lbl), str(train_lbl_dir / lbl.name))
        
        for img in val_images:
            lbl = temp_merged_labels / (img.stem + ".txt")
            shutil.move(str(img), str(val_img_dir / img.name))
            if lbl.exists():
                shutil.move(str(lbl), str(val_lbl_dir / lbl.name))
        
        print(f"✅ Split complete: {len(train_images)} train, {len(val_images)} val")
        
        # Clean up temporary directories
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(temp_merged_images, ignore_errors=True)
        shutil.rmtree(temp_merged_labels, ignore_errors=True)
        
        # Create dataset.yaml for merged dataset
        self._create_dataset_yaml(unified_labels)
        
        print(f"✅ Created merged dataset.yaml")
        
        return {
            "total_images": len(all_merged_images),
            "train_count": len(train_images),
            "val_count": len(val_images),
            "num_classes": len(unified_labels),
            "labels": unified_labels,
            "datasets_merged": len(dataset_paths)
        }
    
    def _create_dataset_yaml(self, labels: List[str]) -> Path:
        """
        Create dataset.yaml file for YOLO training
        
        Args:
            labels: List of class labels
            
        Returns:
            Path to created dataset.yaml
        """
        yaml_content = f"""# Merged Aegis Vision Dataset
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


class AdvancedCOCOtoYOLOMerger:
    """
    Advanced COCO to YOLO converter with multi-dataset merging support
    
    Features:
    - Handles multiple COCO datasets with different class mappings
    - Creates unified class mapping across all datasets
    - Uses symlinks instead of copying images (efficient)
    - Proper class ID remapping for consistent training
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize converter
        
        Args:
            output_dir: Output directory for merged YOLO dataset
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def convert_bbox_to_yolo(img_width: int, img_height: int, bbox: List[float]) -> Tuple[float, float, float, float]:
        """
        Convert COCO bbox [x, y, w, h] to YOLO format [x_center, y_center, w, h] (normalized)
        """
        x, y, w, h = bbox
        x_center = (x + w / 2) / img_width
        y_center = (y + h / 2) / img_height
        w_norm = w / img_width
        h_norm = h / img_height
        return x_center, y_center, w_norm, h_norm
    
    def process_coco_annotations(
        self,
        anno_path: Path,
        images_source_dir: Path,
        output_labels_dir: Path,
        output_images_dir: Path,
        class_id_map: Dict[int, int]
    ) -> Tuple[int, int]:
        """
        Process COCO annotations and create YOLO labels + image symlinks
        
        Args:
            anno_path: Path to COCO annotation JSON
            images_source_dir: Source directory for images
            output_labels_dir: Output directory for YOLO label files
            output_images_dir: Output directory for image symlinks
            class_id_map: Dict mapping COCO category_id -> sequential YOLO class_id
            
        Returns:
            Tuple of (image_count, label_count)
        """
        if not anno_path or not anno_path.exists():
            return 0, 0
        
        try:
            from pycocotools.coco import COCO
        except ImportError:
            raise ImportError("pycocotools is required. Install with: pip install pycocotools")
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"   Processing {anno_path.name}...")
        
        coco = COCO(str(anno_path))
        
        img_count = 0
        label_count = 0
        
        for img_id in coco.getImgIds():
            img_info = coco.loadImgs([img_id])[0]
            img_filename = img_info['file_name']
            img_source_path = images_source_dir / img_filename
            
            if not img_source_path.exists():
                continue
            
            # Symlink image (no copying!)
            img_dest_path = output_images_dir / img_filename
            try:
                if not img_dest_path.exists():
                    img_dest_path.symlink_to(img_source_path)
                img_count += 1
            except Exception as e:
                logger.warning(f"   ⚠️ Could not link {img_filename}: {e}")
                continue
            
            # Create YOLO label file
            img_width, img_height = img_info['width'], img_info['height']
            annotations = coco.loadAnns(coco.getAnnIds(imgIds=[img_id]))
            
            label_file = output_labels_dir / f"{img_filename.rsplit('.', 1)[0]}.txt"
            with open(label_file, 'w') as f:
                seen_labels = set()
                for ann in annotations:
                    if 'bbox' in ann:
                        coco_cat_id = ann['category_id']
                        
                        # Map COCO category_id to sequential YOLO class_id
                        if coco_cat_id not in class_id_map:
                            continue  # Skip unknown classes
                        
                        yolo_class_id = class_id_map[coco_cat_id]
                        
                        bbox = self.convert_bbox_to_yolo(img_width, img_height, ann['bbox'])
                        label_str = f"{yolo_class_id} {' '.join(f'{v:.6f}' for v in bbox)}\n"
                        
                        if label_str not in seen_labels:
                            f.write(label_str)
                            seen_labels.add(label_str)
                            label_count += 1
        
        return img_count, label_count
    
    def merge_and_convert(
        self,
        preprocessed_datasets: List[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """
        Merge multiple COCO datasets and convert to YOLO format
        
        Args:
            preprocessed_datasets: List of (dataset_path, format) tuples
            
        Returns:
            Dictionary with merge results containing dataset_yaml path and statistics
        """
        try:
            from pycocotools.coco import COCO
        except ImportError:
            raise ImportError("pycocotools is required. Install with: pip install pycocotools")
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Create output directories
        output_labels_train = self.output_dir / "labels" / "train"
        output_labels_val = self.output_dir / "labels" / "val"
        output_images_train = self.output_dir / "images" / "train"
        output_images_val = self.output_dir / "images" / "val"
        
        for d in [output_labels_train, output_labels_val, output_images_train, output_images_val]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Build unified class mapping
        logger.info("📋 Building unified class mapping...")
        
        all_categories = {}
        
        for idx, (ds_path, ds_format) in enumerate(preprocessed_datasets):
            ds_path = Path(ds_path)
            
            if ds_format in ["coco", "coco_standard"]:
                if ds_format == "coco_standard":
                    anno_dir = ds_path / "annotations"
                    anno_files = list(anno_dir.glob("instances_*.json"))
                    if not anno_files:
                        anno_files = list(anno_dir.glob("*.json"))
                else:
                    anno_files = [ds_path / "annotations.json"]
                
                if anno_files and anno_files[0].exists():
                    coco = COCO(str(anno_files[0]))
                    categories = coco.loadCats(coco.getCatIds())
                    
                    for cat in categories:
                        cat_name = cat['name']
                        if cat_name not in all_categories:
                            all_categories[cat_name] = (cat['id'], idx)
                    
                    logger.info(f"   • Dataset {idx + 1}: {ds_path.name} - {len(categories)} classes")
        
        # Create sequential YOLO class IDs
        unified_class_names = {}
        for yolo_id, (cat_name, _) in enumerate(sorted(all_categories.items())):
            unified_class_names[yolo_id] = cat_name
        
        logger.info(f"✅ Unified mapping: {len(unified_class_names)} unique classes")
        
        # Step 2: Create per-dataset mappings
        dataset_mappings = []
        
        for idx, (ds_path, ds_format) in enumerate(preprocessed_datasets):
            ds_path = Path(ds_path)
            
            if ds_format in ["coco", "coco_standard"]:
                if ds_format == "coco_standard":
                    anno_dir = ds_path / "annotations"
                    anno_files = list(anno_dir.glob("instances_*.json"))
                    if not anno_files:
                        anno_files = list(anno_dir.glob("*.json"))
                else:
                    anno_files = [ds_path / "annotations.json"]
                
                if anno_files and anno_files[0].exists():
                    coco = COCO(str(anno_files[0]))
                    categories = coco.loadCats(coco.getCatIds())
                    
                    coco_to_yolo = {}
                    for cat in categories:
                        cat_name = cat['name']
                        for yolo_id, name in unified_class_names.items():
                            if name == cat_name:
                                coco_to_yolo[cat['id']] = yolo_id
                                break
                    
                    dataset_mappings.append((ds_path, ds_format, coco_to_yolo))
        
        # Step 3: Process all datasets
        logger.info("⚡ Converting datasets to YOLO format...")
        
        total_train_imgs = 0
        total_train_labels = 0
        total_val_imgs = 0
        total_val_labels = 0
        
        for idx, (ds_path, ds_format, class_id_map) in enumerate(dataset_mappings):
            dataset_name = ds_path.name
            
            logger.info(f"📦 Processing dataset {idx + 1}/{len(dataset_mappings)}: {dataset_name}")
            
            if ds_format == "coco_standard":
                anno_dir = ds_path / "annotations"
                train_anno = list(anno_dir.glob("instances_train*.json"))
                val_anno = list(anno_dir.glob("instances_val*.json"))
                
                train_images = ds_path / "train2017" if (ds_path / "train2017").exists() else None
                val_images = ds_path / "val2017" if (ds_path / "val2017").exists() else None
                
                if not train_anno:
                    train_anno = list(anno_dir.glob("*train*.json")) or list(anno_dir.glob("*.json"))
            else:
                train_anno = [ds_path / "annotations.json"]
                val_anno = []
                train_images = ds_path / "images"
                val_images = None
            
            if train_anno and train_anno[0].exists() and train_images:
                train_imgs, train_labels = self.process_coco_annotations(
                    train_anno[0], train_images, output_labels_train, output_images_train, class_id_map
                )
                total_train_imgs += train_imgs
                total_train_labels += train_labels
            
            if val_anno and val_anno[0].exists() and val_images:
                val_imgs, val_labels = self.process_coco_annotations(
                    val_anno[0], val_images, output_labels_val, output_images_val, class_id_map
                )
                total_val_imgs += val_imgs
                total_val_labels += val_labels
        
        # Create dataset.yaml
        logger.info(f"📝 Creating merged dataset.yaml...")
        dataset_yaml = self.output_dir / "dataset.yaml"
        with open(dataset_yaml, 'w') as f:
            f.write(f"# YOLO Merged Dataset Configuration\n")
            f.write(f"# Generated from {len(preprocessed_datasets)} dataset(s)\n\n")
            f.write(f"path: {self.output_dir}\n")
            f.write(f"train: images/train\n")
            f.write(f"val: images/{'val' if total_val_imgs > 0 else 'train'}\n\n")
            f.write(f"nc: {len(unified_class_names)}\n\n")
            f.write(f"names:\n")
            for class_id in sorted(unified_class_names.keys()):
                f.write(f"  {class_id}: {unified_class_names[class_id]}\n")
        
        logger.info(f"✅ Dataset merging complete!")
        logger.info(f"   • Total train: {total_train_imgs} images, {total_train_labels} labels")
        logger.info(f"   • Total val: {total_val_imgs} images, {total_val_labels} labels")
        logger.info(f"   • Total classes: {len(unified_class_names)}")
        
        return {
            'dataset_yaml': dataset_yaml,
            'train_images': total_train_imgs,
            'train_labels': total_train_labels,
            'val_images': total_val_imgs,
            'val_labels': total_val_labels,
            'classes': len(unified_class_names),
            'class_names': list(unified_class_names.values())
        }
