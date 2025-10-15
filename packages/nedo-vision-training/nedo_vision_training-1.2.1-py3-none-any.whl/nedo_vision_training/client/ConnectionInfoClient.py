import logging
from nedo_vision_training.client.GrpcClientBase import GrpcClientBase
from nedo_vision_training.protos.TrainingAgentService_pb2_grpc import TrainingAgentServiceStub
from nedo_vision_training.protos.TrainingAgentService_pb2 import GetConnectionInfoRequest
from nedo_vision_training.exceptions import GrpcClientError

class ConnectionInfoClient(GrpcClientBase):
    """
    Client for fetching connection information using token-based authentication.
    """
    
    def __init__(self, host: str, port: int, token: str):
        """
        Initialize the connection info client.

        Args:
            host (str): The server hostname or IP address.
            port (int): The server port. Default is 50051.
            token (str): Authentication token for the training agent.
        """
        super().__init__(host, port)
        self.token = token
        self.connect(TrainingAgentServiceStub)

    def get_connection_info(self) -> dict:
        """
        Fetch connection information from the server using token authentication.

        Returns:
            dict: A dictionary containing the connection information and result.
        """
        try:
            if not self.stub:
                raise GrpcClientError("Not connected to manager")

            # Prepare the request
            request = GetConnectionInfoRequest(token=self.token)

            # Call the GetConnectionInfo RPC using base class error handling
            response = self.handle_rpc(self.stub.GetConnectionInfo, request)

            # Handle response
            if response and response.success:
                return {
                    "success": True, 
                    "message": response.message,
                    "rabbitmq_host": response.rabbitmq_host,
                    "rabbitmq_port": response.rabbitmq_port,
                    "rabbitmq_username": response.rabbitmq_username,
                    "rabbitmq_password": response.rabbitmq_password,
                    "s3_endpoint": response.s3_endpoint,
                    "s3_bucket": response.s3_bucket,
                    "s3_access_key": response.s3_access_key,
                    "s3_secret_key": response.s3_secret_key,
                    "s3_region": response.s3_region,
                    "id": getattr(response, "id", None)
                }

            return {"success": False, "message": response.message if response else "Unknown error"}

        except Exception as e:
            logging.error(f"Failed to fetch connection info: {e}")
            return {"success": False, "message": f"Failed to fetch connection info: {e}"}