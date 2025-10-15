import logging
import grpc
from nedo_vision_training.client.GrpcClientBase import GrpcClientBase
from nedo_vision_training.protos.TrainingJobService_pb2_grpc import TrainingJobServiceStub
from nedo_vision_training.protos.TrainingJobService_pb2 import (
    CreateStatusLogRequest,
    CreateCommandLogRequest,
    CreateMetricsLogRequest,
    UpdateModelFilePathRequest
)

logger = logging.getLogger(__name__)

class TrainingLoggerClient(GrpcClientBase):
    def __init__(self, server_host: str, server_port: int = 50051):
        """
        Initialize the training logger client.

        Args:
            server_host (str): The server hostname or IP address.
            server_port (int): The server port. Default is 50051.
        """
        super().__init__(server_host, server_port)

        try:
            self.connect(TrainingJobServiceStub)
        except Exception as e:
            logging.error(f"Failed to connect to gRPC server: {e}")
            self.stub = None

    def update_status(self, job_id: str, status: str) -> dict:
        """
        Update the training job status.

        Args:
            job_id (str): The ID of the training job.
            status (str): The new status to set.

        Returns:
            dict: A dictionary containing the result of the status update.
        """
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            request = CreateStatusLogRequest(
                job_id=job_id,
                status=status
            )
            
            response = self.handle_rpc(self.stub.CreateStatusLog, request)
            
            if response and response.success:
                return {"success": True, "message": response.message}
            return {"success": False, "message": response.message if response else "Unknown error"}

        except grpc.RpcError as e:
            error_message = getattr(e, "details", lambda: str(e))()
            logger.error(f"gRPC error while updating status: {error_message}")
            return {"success": False, "message": f"RPC error: {error_message}"}

        except Exception as e:
            logger.error(f"Unexpected error while updating status: {str(e)}")
            return {"success": False, "message": "An unexpected error occurred during status update."}

    def log_command(self, job_id: str, command: str) -> dict:
        """
        Log a training command.

        Args:
            job_id (str): The ID of the training job.
            command (str): The command to log.

        Returns:
            dict: A dictionary containing the result of the command logging.
        """
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            request = CreateCommandLogRequest(
                job_id=job_id,
                command=command
            )
            
            response = self.handle_rpc(self.stub.CreateCommandLog, request)
            
            if response and response.success:
                return {"success": True, "message": response.message}
            return {"success": False, "message": response.message if response else "Unknown error"}

        except grpc.RpcError as e:
            error_message = getattr(e, "details", lambda: str(e))()
            logger.error(f"gRPC error while logging command: {error_message}")
            return {"success": False, "message": f"RPC error: {error_message}"}

        except Exception as e:
            logger.error(f"Unexpected error while logging command: {str(e)}")
            return {"success": False, "message": "An unexpected error occurred during command logging."}

    def log_metrics(self, job_id: str, epoch: int, map_50: float, map_50_95: float, 
                   precision: float, recall: float, f1_score: float) -> dict:
        """
        Log training metrics.

        Args:
            job_id (str): The ID of the training job.
            epoch (int): Current training epoch.
            map_50 (float): mAP@0.50 metric.
            map_50_95 (float): mAP@0.50:0.95 metric.
            precision (float): Precision metric.
            recall (float): Recall metric.
            f1_score (float): F1 score metric.

        Returns:
            dict: A dictionary containing the result of the metrics logging.
        """
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            request = CreateMetricsLogRequest(
                job_id=job_id,
                epoch=epoch,
                map_50=map_50,
                map_50_95=map_50_95,
                precision=precision,
                recall=recall,
                f1_score=f1_score
            )
            
            response = self.handle_rpc(self.stub.CreateMetricsLog, request)
            
            if response and response.success:
                return {"success": True, "message": response.message}
            return {"success": False, "message": response.message if response else "Unknown error"}

        except grpc.RpcError as e:
            error_message = getattr(e, "details", lambda: str(e))()
            logger.error(f"gRPC error while logging metrics: {error_message}")
            return {"success": False, "message": f"RPC error: {error_message}"}

        except Exception as e:
            logger.error(f"Unexpected error while logging metrics: {str(e)}")
            return {"success": False, "message": "An unexpected error occurred during metrics logging."}

    def update_model_file_path(self, job_id: str, model_file_path: str) -> dict:
        """
        Update the model file path for a training job.

        Args:
            job_id (str): The ID of the training job.
            model_file_path (str): The path to the resulting model file.

        Returns:
            dict: A dictionary containing the result of the model file path update.
        """
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            request = UpdateModelFilePathRequest(
                job_id=job_id,
                model_file_path=model_file_path
            )
            
            response = self.handle_rpc(self.stub.UpdateModelFilePath, request)
            
            if response and response.success:
                return {"success": True, "message": response.message}
            return {"success": False, "message": response.message if response else "Unknown error"}

        except grpc.RpcError as e:
            error_message = getattr(e, "details", lambda: str(e))()
            logger.error(f"gRPC error while updating model file path: {error_message}")
            return {"success": False, "message": f"RPC error: {error_message}"}

        except Exception as e:
            logger.error(f"Unexpected error while updating model file path: {str(e)}")
            return {"success": False, "message": "An unexpected error occurred during model file path update."}