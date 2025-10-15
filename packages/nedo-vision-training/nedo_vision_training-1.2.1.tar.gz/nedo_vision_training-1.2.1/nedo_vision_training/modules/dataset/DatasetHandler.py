from abc import ABC, abstractmethod
import os
import boto3
from typing import List, Dict, Any, Tuple
from nedo_vision_training.client.DatasetServiceClient import DatasetServiceClient
import logging
import random
import shutil
from nedo_vision_training.client.S3Client import S3Client

logger = logging.getLogger(__name__)

class DatasetHandler(ABC):
    def __init__(self, dataset_id: str, output_dir: str, 
                 train_ratio: float = 0.7, 
                 val_ratio: float = 0.15, 
                 test_ratio: float = 0.15,
                 seed: int = 42,
                 config: dict = None):
        """
        Initialize the dataset handler.
        
        Args:
            dataset_id (str): The ID of the dataset to fetch
            output_dir (str): Directory where dataset files will be saved
            train_ratio (float): Ratio of training data (default: 0.7)
            val_ratio (float): Ratio of validation data (default: 0.15)
            test_ratio (float): Ratio of test data (default: 0.15)
            seed (int): Random seed for reproducibility (default: 42)
            config (dict): Configuration for S3Client
            server_host (str): Server host for DatasetServiceClient
            server_port (int): Server port for DatasetServiceClient
        """
        if not (0 <= train_ratio <= 1 and 0 <= val_ratio <= 1 and 0 <= test_ratio <= 1):
            raise ValueError("Split ratios must be between 0 and 1")
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-10:
            raise ValueError("Split ratios must sum to 1")
            
        self.dataset_id = dataset_id
        self.output_dir = output_dir
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed
        
        # Set up random seed for reproducibility
        random.seed(seed)
        
        # Initialize clients
        self.s3_client = S3Client(config or {})
        host = config.get('server_host')
        port = config.get('server_port')
        self.dataset_service = DatasetServiceClient(host, port)
        
        # Set up split directories
        self.train_dir = os.path.join(output_dir, "train")
        self.val_dir = os.path.join(output_dir, "val")
        self.test_dir = os.path.join(output_dir, "test")
            
    def _ensure_output_dir(self):
        """Create output directories if they don't exist"""
        for directory in [self.output_dir, self.train_dir, self.val_dir, self.test_dir]:
            os.makedirs(directory, exist_ok=True)
            
    def _split_dataset(self, items: List[Any]) -> Tuple[List[Any], List[Any], List[Any]]:
        """
        Split dataset items into train, validation, and test sets
        
        Args:
            items (List[Any]): List of dataset items to split
            
        Returns:
            Tuple[List[Any], List[Any], List[Any]]: Train, validation, and test sets
        """
        # Always convert to list unless already a list/tuple
        if not isinstance(items, (list, tuple)):
            items = list(items)
        items = items.copy()
        random.shuffle(items)
        n_items = len(items)
        train_end = int(n_items * self.train_ratio)
        val_end = train_end + int(n_items * self.val_ratio)
        train_items = items[:train_end]
        val_items = items[train_end:val_end]
        test_items = items[val_end:]
        return train_items, val_items, test_items
        
    def _move_to_split_dir(self, file_path: str, split_dir: str):
        """
        Move a file to its split directory
        
        Args:
            file_path (str): Path to the file to move
            split_dir (str): Target directory for the split
        """
        filename = os.path.basename(file_path)
        target_path = os.path.join(split_dir, filename)
        shutil.move(file_path, target_path)
        return target_path
        
    @abstractmethod
    def process_dataset(self) -> Dict[str, Any]:
        """
        Process the dataset and convert it to the required format
        
        Returns:
            Dict[str, Any]: Processing results including success status and metadata
        """
        pass
        
    @abstractmethod
    def _convert_annotations(self, annotations: List[Any]) -> List[Any]:
        """
        Convert annotations to the required format
        
        Args:
            annotations (List[Any]): Original annotations
            
        Returns:
            List[Any]: Converted annotations
        """
        pass 