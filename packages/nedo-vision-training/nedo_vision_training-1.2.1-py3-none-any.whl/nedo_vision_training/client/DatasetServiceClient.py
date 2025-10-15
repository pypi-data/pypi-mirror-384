import logging
import grpc
from nedo_vision_training.protos.DatasetService_pb2 import GetDatasetRequest
from nedo_vision_training.protos.DatasetService_pb2_grpc import DatasetServiceStub
from nedo_vision_training.client.GrpcClientBase import GrpcClientBase

logger = logging.getLogger(__name__)

class DatasetServiceClient(GrpcClientBase):
    def __init__(self, server_host: str, server_port: int):
        """
        Initialize the DatasetServiceClient for fetching dataset information.
        Args:
            server_host (str): The gRPC server host.
            server_port (int): The gRPC server port.
        """
        super().__init__(server_host, server_port)
        try:
            self.connect(DatasetServiceStub)
        except Exception as e:
            logging.error(f"Failed to connect to gRPC server: {e}")
            self.stub = None
            
    def get_dataset(self, dataset_id: str) -> dict:
        """
        Fetch dataset information from the server.
        
        Args:
            dataset_id (str): The ID of the dataset to fetch.
            
        Returns:
            dict: Result of the dataset fetch operation containing:
                - success (bool): Whether the operation was successful
                - message (str): Additional information
                - data (list): List of dataset items if successful
        """
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}
        
        try:
            request = GetDatasetRequest(dataset_id=dataset_id)
            response = self.handle_rpc(self.stub.GetDataset, request)
            
            if response and response.success:
                return {
                    "success": True,
                    "message": response.message,
                    "data": response.data
                }
                
            return {
                "success": False,
                "message": response.message if response else "Unknown error",
                "data": None
            }
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error while fetching dataset {dataset_id}: {str(e)}")
            return {"success": False, "message": f"RPC error: {str(e)}", "data": None}
            
        except Exception as e:
            logger.error(f"Unexpected error while fetching dataset {dataset_id}: {str(e)}")
            return {"success": False, "message": f"An unexpected error occurred: {str(e)}", "data": None} 