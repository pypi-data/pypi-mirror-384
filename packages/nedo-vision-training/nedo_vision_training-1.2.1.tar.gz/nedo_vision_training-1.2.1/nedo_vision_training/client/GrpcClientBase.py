import grpc
import time
from grpc import StatusCode

from ..logger.Logger import Logger

logger = Logger(__name__)

class GrpcClientBase:
    def __init__(self, server_host: str, server_port: int = 50051, max_retries: int = 3):
        """
        Initialize the gRPC client base.

        Args:
            server_host (str): The server hostname or IP address.
            server_port (int): The server port. Default is 50051.
            max_retries (int): Maximum number of reconnection attempts.
        """
        self.server_address = f"{server_host}:{server_port}"
        self.channel = None
        self.stub = None
        self.connected = False
        self.max_retries = max_retries

    def connect(self, stub_class, retry_interval: int = 2):
        """
        Create a gRPC channel and stub, with retry logic if the server is unavailable.

        Args:
            stub_class: The gRPC stub class for the service.
            retry_interval (int): Initial time in seconds between reconnection attempts.
        """
        attempts = 0
        while attempts < self.max_retries and not self.connected:
            try:
                self.channel = grpc.insecure_channel(self.server_address, [('grpc.max_send_message_length', -1), ('grpc.max_receive_message_length', -1)])
                future = grpc.channel_ready_future(self.channel)
                try:
                    future.result(timeout=30)
                except grpc.FutureTimeoutError:
                    raise grpc.RpcError("gRPC connection timed out.")

                self.stub = stub_class(self.channel)
                self.connected = True
                logger.info(f"🚀 Successfully connected to gRPC server at {self.server_address}")
                return  # Exit if successful

            except grpc.RpcError as e:
                attempts += 1
                self.connected = False

                error_message = getattr(e, "details", lambda: str(e))()
                logger.error(f"⚠️ Failed to connect ({attempts}/{self.max_retries}): {error_message}")

                if attempts < self.max_retries:
                    sleep_time = retry_interval * (2 ** (attempts - 1))  # Exponential backoff
                    logger.info(f"⏳ Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.critical("❌ Maximum retries reached. Could not connect to gRPC server.")

            except Exception as e:
                logger.critical(f"🚨 Unexpected error during gRPC initialization: {str(e)}")
                break  # Stop retrying if an unexpected error occurs

    def close(self):
        """
        Close the gRPC channel.
        """
        if self.channel:
            self.channel.close()
            self.connected = False
            logger.info("🔌 gRPC channel closed.")

    def handle_rpc(self, rpc_call, *args, **kwargs):
        """
        Handle an RPC call with error handling.

        Args:
            rpc_call: The RPC method to call.
            *args: Positional arguments for the RPC call.
            **kwargs: Keyword arguments for the RPC call.

        Returns:
            The RPC response or None if an error occurs.
        """
        try:
            response = rpc_call(*args, **kwargs)
            return response

        except grpc.RpcError as e:
            status_code = e.code()

            # ✅ Extract only the meaningful part of the error message
            error_message = getattr(e, "details", lambda: str(e))()
            error_clean = error_message.split("debug_error_string")[0].strip()

            self.connected = False  # Mark as disconnected for reconnection

            if status_code == StatusCode.UNAVAILABLE:
                logger.warning(f"⚠️ Server unavailable. Attempting to reconnect... (Error: {error_clean})")
                self.connect(type(self.stub))  # Attempt to reconnect
            elif status_code == StatusCode.DEADLINE_EXCEEDED:
                logger.error(f"⏳ RPC timeout error. (Error: {error_clean})")
            elif status_code == StatusCode.PERMISSION_DENIED:
                logger.error(f"🚫 RPC call failed: Permission denied. (Error: {error_clean})")
            elif status_code == StatusCode.UNAUTHENTICATED:
                logger.error(f"🔑 Authentication failed. (Error: {error_clean})")
            elif status_code == StatusCode.INVALID_ARGUMENT:
                logger.error(f"⚠️ Invalid argument in RPC call. (Error: {error_clean})")
            elif status_code == StatusCode.NOT_FOUND:
                logger.error(f"🔍 Requested resource not found. (Error: {error_clean})")
            elif status_code == StatusCode.INTERNAL:
                logger.error(f"💥 Internal server error encountered. (Error: {error_clean})")
            else:
                logger.error(f"❌ Unhandled gRPC error: {error_clean} (Code: {status_code})")

            return None  # Ensure the caller handles the failure

    @staticmethod
    def get_error_message(response):
        """
        Extract only the meaningful part of the error message.

        Args:
            response: The RPC response.

        Returns:
            str: The error message.
        """
        if response and response.get("success"):
            return None
        
        return response.get("message", "Unknown error") if response else "Unknown error"