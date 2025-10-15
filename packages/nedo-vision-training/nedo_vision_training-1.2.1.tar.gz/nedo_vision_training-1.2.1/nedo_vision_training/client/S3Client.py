import boto3
from nedo_vision_training.logger.Logger import Logger

logger = Logger(__name__)

class S3Client:
    """A reusable S3 client for interacting with S3-compatible storage."""
    
    def __init__(self, config):
        """Initialize the S3 client using credentials from configuration."""
        self.client = None
        self.bucket_name = None
        self._init_client(config)
    
    def _init_client(self, config):
        """Initialize S3 client using credentials from configuration."""
        try:
            s3_access_key = config.get("s3_access_key")
            s3_secret_key = config.get("s3_secret_key")
            s3_region = config.get("s3_region")
            s3_endpoint = config.get("s3_endpoint")
            self.bucket_name = config.get("s3_bucket")
            if not self.bucket_name:
                raise ValueError("Missing 's3_bucket' in S3 config")
            self.client = boto3.client(
                's3',
                region_name=s3_region,
                endpoint_url=s3_endpoint,
                aws_access_key_id=s3_access_key,
                aws_secret_access_key=s3_secret_key,
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def download_file(self, s3_path: str, local_path: str):
        """
        Download a file from S3 to local path.
        
        Args:
            s3_path (str): Full S3 path of the file
            local_path (str): Local path where file will be saved
        """
        try:
            self.client.download_file(self.bucket_name, s3_path, local_path)
            logger.info(f"Successfully downloaded {s3_path} to {local_path}")
        except Exception as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise
    
    def upload_file(self, local_path: str, s3_path: str):
        """
        Upload a file from local path to S3.
        
        Args:
            local_path (str): Local path of the file to upload
            s3_path (str): Full S3 path where file will be saved
        """
        try:
            self.client.upload_file(local_path, self.bucket_name, s3_path)
            logger.info(f"Successfully uploaded {local_path} to {s3_path}")
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise
    
    def list_objects(self, prefix: str = ""):
        """
        List objects in the S3 bucket with optional prefix.
        
        Args:
            prefix (str): Optional prefix to filter objects
            
        Returns:
            list: List of object keys
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            logger.error(f"Failed to list objects in S3: {e}")
            raise
    
    def delete_object(self, s3_path: str):
        """
        Delete an object from S3.
        
        Args:
            s3_path (str): Full S3 path of the object to delete
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_path
            )
            logger.info(f"Successfully deleted {s3_path}")
        except Exception as e:
            logger.error(f"Failed to delete object from S3: {e}")
            raise