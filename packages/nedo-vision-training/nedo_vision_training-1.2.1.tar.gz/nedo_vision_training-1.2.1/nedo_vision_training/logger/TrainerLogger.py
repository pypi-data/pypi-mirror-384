from threading import Lock
from ..client.TrainingLoggerClient import TrainingLoggerClient
from .Logger import Logger

class TrainerLogger:
    """
    TrainerLogger is responsible for logging training activity using gRPC.
    It ensures that training-related logs such as commands, metrics, and statuses
    are published reliably.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        """
        Ensure only one instance of TrainerLogger is created.
        """
        if not cls._instance:
            with cls._lock:  # Thread-safe initialization
                if not cls._instance:  # Double-checked locking
                    cls._instance = super(TrainerLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, config=None):
        """
        Initializes the gRPC client and logger.
        """
        if not hasattr(self, "initialized"):
            self.logger = Logger()
            self.logger.info("🚀 Initializing TrainerLogger...")
            self.config = config or {}
            self.server_host = self.config.get("server_host", "localhost")
            self.server_port = int(self.config.get("server_port", "50051"))
            
            self.logger.info(f"🔗 TrainerLogger connecting to {self.server_host}:{self.server_port}")
            self.grpc_client = TrainingLoggerClient(self.server_host, self.server_port)
            self.prev_status = None

            self.logger.info("✅ TrainerLogger initialized successfully.")
            self.initialized = True

    def log_command(self, job_id: str, command: str) -> None:
        """
        Logs a command executed during training.

        Args:
            project_id (str): The ID of the project.
            job_id (str): The ID of the training run.
            command (str): The command executed.
        """
        try:
            response = self.grpc_client.log_command(job_id, command)
            if response["success"]:
                self.logger.info(f"📜 Command log sent: {command}")
            else:
                self.logger.error(f"❌ Failed to log command: {response['message']}")
        except Exception as e:
            self.logger.error(f"❌ Failed to log command: {e}")
    
    def log_metric(self, job_id: str, metrics: dict) -> None:
        """
        Logs training metrics.

        Args:
            project_id (str): ID of the project.
            job_id (str): ID of the training run.
            metrics (dict): Training metrics data containing epoch, map_50, map_50_95, precision, recall, and f1_score.
        """
        try:
            response = self.grpc_client.log_metrics(
                job_id=job_id,
                epoch=metrics.get("epoch", 0),
                map_50=metrics.get("map_50", 0.0),
                map_50_95=metrics.get("map_50_95", 0.0),
                precision=metrics.get("precision", 0.0),
                recall=metrics.get("recall", 0.0),
                f1_score=metrics.get("f1_score", 0.0)
            )
            if response["success"]:
                self.logger.info(f"📈 Metrics log sent for epoch {metrics.get('epoch', 0)}")
            else:
                self.logger.error(f"❌ Failed to log metrics: {response['message']}")
        except Exception as e:
            self.logger.error(f"❌ Failed to log metrics: {e}")

    def log_model_file_path(self, job_id: str, model_file_path: str) -> None:
        """
        Logs the model file path after training completion.

        Args:
            job_id (str): ID of the training run.
            model_file_path (str): Path to the resulting model file.
        """
        try:
            response = self.grpc_client.update_model_file_path(job_id, model_file_path)
            if response["success"]:
                self.logger.info(f"📁 Model file path updated: {model_file_path}")
            else:
                self.logger.error(f"❌ Failed to update model file path: {response['message']}")
        except Exception as e:
            self.logger.error(f"❌ Failed to update model file path: {e}")

    def log_status(self, job_id: str, status: str) -> None:
        """
        Logs training status updates (e.g., 'Started', 'In Progress', 'Completed').

        - Stops the previous status update thread when a new status is received.
        - Starts a new thread that continuously sends the latest status at 1-second intervals.

        Args:
            project_id (str): ID of the project.
            job_id (str): Training run ID.
            status (str): Training status.
        """
        if status == self.prev_status:
            return
    
        response = self.grpc_client.update_status(job_id, status)
                    
        if response["success"]:
            self.logger.info(f"🚦 Status changed: {self.prev_status} ➝ {status}")
            self.prev_status = status

            if status == "completed":
                self.logger.info(f"✅ Status thread for {job_id} completed.")
        else:
            self.logger.error(f"❌ Failed to update status: {response['message']}")
