import grpc
from nedo_vision_training.protos.TrainingAgentService_pb2 import (
    TrainingAgentSystemUsageRequest,
    TrainingAgentGPUUsage
)
from nedo_vision_training.protos.TrainingAgentService_pb2_grpc import TrainingAgentServiceStub
from nedo_vision_training.exceptions import GrpcClientError
from nedo_vision_training.client.GrpcClientBase import GrpcClientBase


class SystemUsageClient(GrpcClientBase):
    def __init__(self, host: str, port: int, token: str):
        super().__init__(host, port)
        self.token = token

        try:
            self.connect(TrainingAgentServiceStub)
        except Exception as e:
            self.stub = None
    
    def send_system_usage(self, cpu_usage: float, ram_usage: dict, gpu_usage: list, latency: float) -> dict:
        """
        Send system usage data to the server, including network latency.

        Args:
            cpu_usage (float): CPU usage percentage.
            ram_usage (dict): RAM usage details.
            gpu_usage (list): GPU usage details.
            latency (float): Measured network latency in milliseconds.

        Returns:
            dict: A dictionary containing the result of sending system usage.
        """
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            # Prepare the request
            request = TrainingAgentSystemUsageRequest(
                token=self.token,
                cpu_usage=cpu_usage,
                ram_usage_percent=ram_usage.get("percent", 0.0),
                ram_total=ram_usage.get("total", 0),
                ram_used=ram_usage.get("used", 0),
                ram_free=ram_usage.get("free", 0),
                latency_ms=latency, 
                gpu=[
                    TrainingAgentGPUUsage(
                        gpu_index=gpu.get("gpu_index", 0),
                        gpu_usage_percent=gpu.get("gpu_usage_percent", 0.0),
                        memory_usage_percent=gpu.get("memory_usage_percent", 0.0),
                        temperature_celsius=gpu.get("temperature_celsius", 0.0),
                        total_memory=gpu.get("total_memory", 0),
                        used_memory=gpu.get("used_memory", 0),
                        free_memory=gpu.get("free_memory", 0),
                    )
                    for gpu in (gpu_usage or [])  # Handle None or empty list
                ],
            )

            # Call the SendSystemUsage RPC
            response = self.handle_rpc(self.stub.SendSystemUsage, request)

            if response and response.success:
                return {"success": True, "message": response.message}

            return {"success": False, "message": response.message if response else "Unknown error"}

        except Exception as e:
            return {"success": False, "message": f"Error occurred: {e}"}

