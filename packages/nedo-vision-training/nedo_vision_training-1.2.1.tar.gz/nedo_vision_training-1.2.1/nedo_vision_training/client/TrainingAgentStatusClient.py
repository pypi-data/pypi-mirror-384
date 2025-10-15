from nedo_vision_training.client.GrpcClientBase import GrpcClientBase
from nedo_vision_training.protos.TrainingAgentService_pb2 import UpdateTrainingAgentStatusRequest
from nedo_vision_training.protos.TrainingAgentService_pb2_grpc import TrainingAgentServiceStub
from nedo_vision_training.exceptions import GrpcClientError
import time
import logging

logger = logging.getLogger(__name__)

class TrainingAgentStatusClient(GrpcClientBase):
    def __init__(self, host: str, port: int, token: str):
        """
        Initialize the TrainingAgentStatusClient for updating trainingagent status.
        
        Args:
            host (str): The gRPC server host.
            port (int): The gRPC server port.
            token (str): Authentication token for the training agent.
        """
        super().__init__(host, port)
        self.token = token
        self.connect(TrainingAgentServiceStub)

    def update_status(self, status_code: str) -> bool:
        """
        Update training agent status
        
        Args:
            status_code: Status code to update to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.stub:
                raise GrpcClientError("Not connected to manager")

            # Create request
            request = UpdateTrainingAgentStatusRequest(
                token=self.token,
                status_code=status_code,
                timestamp=int(time.time() * 1000)  # Current timestamp in milliseconds
            )

            # Send request using base class error handling
            response = self.handle_rpc(self.stub.UpdateStatus, request)
            return response.success if response else False

        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return False