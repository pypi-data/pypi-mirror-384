import time
import json
import os
import tempfile
import zipfile
import shutil
import requests
from typing import List, Dict, Any
from nedo_vision_training.modules.dataset.DatasetHandler import DatasetHandler
from nedo_vision_training.logger.Logger import Logger

logger = Logger(__name__)

class COCODatasetHandler(DatasetHandler):
    def __init__(self, dataset_id: str, output_dir: str, 
                 train_ratio: float = 0.7, 
                 val_ratio: float = 0.15, 
                 test_ratio: float = 0.15,
                 seed: int = 42,
                 config: dict = None):
        super().__init__(dataset_id, output_dir, train_ratio, val_ratio, test_ratio, seed, config)
        self.val_dir = os.path.join(output_dir, "valid")
        
        if not config:
            raise ValueError("Config is required for COCODatasetHandler")
            
        self.server_host = config.get('server_host', 'localhost')
        self.rest_api_port = config.get('rest_api_port', 8081)
        self.token = config.get('token')
        
        self.api_base_url = f"http://{self.server_host}:{self.rest_api_port}/api/v1"
        
        if not self.token:
            raise ValueError("Training agent token is required. Ensure 'token' is set in config.")
    
    def _download_dataset_from_api(self, temp_dir: str) -> str:
        """
        Download dataset from API as zip file with COCO annotations
        
        Args:
            temp_dir (str): Temporary directory to download the zip file
            
        Returns:
            str: Path to the downloaded zip file
            
        Raises:
            Exception: If download fails or token is invalid
        """
        if not self.token:
            raise Exception("Training agent token is required to download dataset from API")
            
        download_url = f"{self.api_base_url}/dataset/{self.dataset_id}/training-agent/download-zip"
        headers = {
            "X-Training-Agent-Token": self.token
        }
        
        logger.info(f"Downloading dataset {self.dataset_id} from API: {download_url}")
        
        try:
            response = requests.get(download_url, headers=headers, stream=True, timeout=300)
            response.raise_for_status()
            
            timestamp = int(time.time() * 1000)
            process_id = os.getpid()
            zip_file_path = os.path.join(temp_dir, f"dataset_{self.dataset_id}_{timestamp}_{process_id}.zip")
            
            with open(zip_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            logger.info(f"Successfully downloaded dataset zip to: {zip_file_path}")
            return zip_file_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download dataset from API: {e}")
            raise Exception(f"Failed to download dataset: {e}")
    
    def _extract_dataset_zip(self, zip_file_path: str, extract_dir: str) -> Dict[str, Any]:
        """
        Extract dataset zip file and organize files by split
        
        Args:
            zip_file_path (str): Path to the zip file
            extract_dir (str): Directory to extract files to
            
        Returns:
            Dict[str, Any]: Information about extracted dataset including COCO annotations
        """
        try:
            logger.info(f"Extracting dataset zip file: {zip_file_path}")
            
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            coco_annotations_path = os.path.join(extract_dir, "_annotations.coco.json")
            
            if os.path.exists(coco_annotations_path):
                logger.info(f"Found COCO annotations file: {coco_annotations_path}")
                with open(coco_annotations_path, 'r') as f:
                    coco_data = json.load(f)
            else:
                logger.warning("No COCO annotations file found in the extracted dataset")
                coco_data = None
            
            image_files = []
            for file in os.listdir(extract_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')):
                    image_files.append(os.path.join(extract_dir, file))
            
            logger.info(f"Extracted {len(image_files)} image files from dataset")
            
            return {
                'extract_dir': extract_dir,
                'coco_data': coco_data,
                'image_files': image_files,
                'coco_annotations_path': coco_annotations_path
            }
            
        except Exception as e:
            logger.error(f"Failed to extract dataset zip: {e}")
            raise Exception(f"Failed to extract dataset: {e}")
        
    def process_dataset(self) -> Dict[str, Any]:
        """
        Process the dataset by downloading from manager API with COCO annotations and organizing into train/val/test splits
        
        Returns:
            Dict[str, Any]: Processing results including success status and metadata
        """
        try:
            self._ensure_output_dir()
            os.makedirs(self.val_dir, exist_ok=True)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"Processing dataset {self.dataset_id} using API download")
                
                zip_file_path = self._download_dataset_from_api(temp_dir)
                extraction_result = self._extract_dataset_zip(zip_file_path, os.path.join(temp_dir, "extracted"))
                
                coco_data = extraction_result['coco_data']
                image_files = extraction_result['image_files']
                extract_dir = extraction_result['extract_dir']
                
                if not coco_data:
                    logger.warning("No COCO annotations found, creating splits without annotations")
                    return self._process_without_annotations(image_files)
                
                return self._process_with_coco_annotations(coco_data, image_files, extract_dir)
                
        except Exception as e:
            logger.error(f"Failed to process dataset: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to process dataset: {e}"
            }
    
    def _process_with_coco_annotations(self, coco_data: Dict[str, Any], image_files: List[str], extract_dir: str) -> Dict[str, Any]:
        """
        Process dataset with existing COCO annotations and create train/val/test splits
        
        Args:
            coco_data (Dict[str, Any]): COCO format annotations
            image_files (List[str]): List of image file paths
            extract_dir (str): Directory where images were extracted
            
        Returns:
            Dict[str, Any]: Processing results
        """
        try:
            logger.info("Processing dataset with existing COCO annotations")
            
            # Create mapping from image filename to full path
            image_path_map = {os.path.basename(img_path): img_path for img_path in image_files}
            
            # Get images and annotations from COCO data
            images = coco_data.get('images', [])
            annotations = coco_data.get('annotations', [])
            categories = coco_data.get('categories', [])
            
            category_id_mapping = {}
            converted_categories = []
            for i, category in enumerate(categories):
                old_id = category['id']
                new_id = i
                category_id_mapping[old_id] = new_id
                
                converted_category = category.copy()
                converted_category['id'] = new_id
                converted_categories.append(converted_category)
            
            logger.info(f"Converted {len(categories)} categories from 1-based to 0-based indexing: {category_id_mapping}")
            converted_annotations = []
            for ann in annotations:
                converted_ann = ann.copy()
                old_category_id = ann.get('category_id')
                if old_category_id in category_id_mapping:
                    converted_ann['category_id'] = category_id_mapping[old_category_id]
                    converted_annotations.append(converted_ann)
                else:
                    logger.warning(f"Annotation has unknown category_id {old_category_id}, skipping")
            
            # Create image_id to annotations mapping
            image_annotations = {}
            for ann in converted_annotations:
                image_id = ann['image_id']
                if image_id not in image_annotations:
                    image_annotations[image_id] = []
                image_annotations[image_id].append(ann)
            
            # Split images into train/val/test
            images_copy = images.copy()
            train_images, val_images, test_images = self._split_dataset(images_copy)
            
            # Process each split
            splits = {
                "train": (train_images, self.train_dir),
                "val": (val_images, self.val_dir),
                "test": (test_images, self.test_dir)
            }
            
            all_split_data = {}
            
            for split_name, (split_images, split_dir) in splits.items():
                logger.info(f"Processing {split_name} split with {len(split_images)} images")
                
                # Create COCO data for this split
                split_coco_data = {
                    "images": [],
                    "annotations": [],
                    "categories": converted_categories,
                    "info": {
                        "description": f"{split_name} split of dataset {self.dataset_id}",
                        "version": "1.0", 
                        "year": 2024
                    }
                }
                
                # Copy images and their annotations to split directory
                for img in split_images:
                    img_filename = img['file_name']
                    if img_filename in image_path_map:
                        src_path = image_path_map[img_filename]
                        dst_path = os.path.join(split_dir, img_filename)
                        
                        try:
                            shutil.copy2(src_path, dst_path)
                            split_coco_data["images"].append(img)
                            
                            # Add annotations for this image
                            if img['id'] in image_annotations:
                                split_coco_data["annotations"].extend(image_annotations[img['id']])
                                
                        except Exception as e:
                            logger.error(f"Failed to copy image {img_filename}: {e}")
                            continue
                    else:
                        logger.warning(f"Image file not found: {img_filename}")
                
                # Save split annotations
                split_file = os.path.join(split_dir, "_annotations.coco.json")
                with open(split_file, 'w') as f:
                    json.dump(split_coco_data, f, indent=2)
                
                all_split_data[split_name] = split_coco_data
                logger.info(f"Created {split_name} split with {len(split_coco_data['images'])} images and {len(split_coco_data['annotations'])} annotations")
            
            logger.info("Dataset successfully processed with COCO annotations and split into train/val/test")
            
            return {
                "success": True,
                "message": "Dataset successfully processed with COCO annotations and split into train/val/test",
                "output_dir": self.output_dir,
                "categories": converted_categories,
                "splits": {
                    "train": len(all_split_data["train"]["images"]),
                    "val": len(all_split_data["val"]["images"]),
                    "test": len(all_split_data["test"]["images"])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process dataset with COCO annotations: {e}")
            raise
    
    def _process_without_annotations(self, image_files: List[str]) -> Dict[str, Any]:
        """
        Process dataset without annotations (images only) and create splits
        
        Args:
            image_files (List[str]): List of image file paths
            
        Returns:
            Dict[str, Any]: Processing results
        """
        try:
            logger.info("Processing dataset without annotations (images only)")
            
            # Split images into train/val/test
            train_images, val_images, test_images = self._split_dataset(image_files)
            
            # Process each split
            splits = {
                "train": (train_images, self.train_dir),
                "val": (val_images, self.val_dir), 
                "test": (test_images, self.test_dir)
            }
            
            for split_name, (split_image_files, split_dir) in splits.items():
                logger.info(f"Processing {split_name} split with {len(split_image_files)} images")
                
                # Copy images to split directory
                for img_path in split_image_files:
                    try:
                        dst_path = os.path.join(split_dir, os.path.basename(img_path))
                        shutil.copy2(img_path, dst_path)
                    except Exception as e:
                        logger.error(f"Failed to copy image {img_path}: {e}")
                        continue
                
                # Create empty COCO annotations file
                split_coco_data = {
                    "images": [],
                    "annotations": [],
                    "categories": [],
                    "info": {
                        "description": f"{split_name} split of dataset {self.dataset_id} (no annotations)",
                        "version": "1.0",
                        "year": 2024
                    }
                }
                
                split_file = os.path.join(split_dir, "_annotations.coco.json")
                with open(split_file, 'w') as f:
                    json.dump(split_coco_data, f, indent=2)
            
            logger.info("Dataset successfully processed without annotations and split into train/val/test")
            
            return {
                "success": True,
                "message": "Dataset successfully processed without annotations and split into train/val/test",
                "output_dir": self.output_dir,
                "categories": [],
                "splits": {
                    "train": len(train_images),
                    "val": len(val_images),
                    "test": len(test_images)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process dataset without annotations: {e}")
            raise
            
    def _convert_annotations(self, annotations: List[Any]) -> List[Any]:
        """
        Convert annotations to the required format (abstract method implementation)
        
        Args:
            annotations (List[Any]): Original annotations
            
        Returns:
            List[Any]: Converted annotations (pass-through in this implementation)
        """
        # Required by base class but not used since we handle COCO data directly
        return annotations 