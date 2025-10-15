import time
import multiprocessing
import signal
import sys

# Set multiprocessing start method to 'spawn' for CUDA compatibility
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    # Method already set, ignore
    pass

from nedo_vision_training.exceptions import GrpcClientError
from nedo_vision_training.client.ConnectionInfoClient import ConnectionInfoClient
from nedo_vision_training.client.SystemUsageClient import SystemUsageClient
from nedo_vision_training.client.TrainingAgentStatusClient import TrainingAgentStatusClient
from nedo_vision_training.logger.Logger import Logger
from nedo_vision_training.services.WorkerManager import WorkerManager


class TrainingService:
    """
    Main training service class that manages the training agent lifecycle.
    Uses token-based authentication only. No config file.
    """
    
    def __init__(
        self,
        token: str,
        server_host: str = "localhost",
        server_port: int = 50051,
        rest_api_port: int = 8081,
        system_usage_interval: int = 5,
        latency_check_interval: int = 10,
    ):
        """
        Initialize the training service.
        
        Args:
            token: Training agent token (required)
            server_host: Manager server host (default: 'localhost')
            server_port: Manager server gRPC port (default: 50051)
            rest_api_port: Manager REST API port (default: 8081)
            system_usage_interval: Interval for system usage reporting in seconds (default: 5)
            latency_check_interval: Interval for latency monitoring in seconds (default: 10)
        """
        self.logger = Logger()
        self.connection_info_client = None
        self.system_usage_client = None
        self.status_client = None
        self.worker_manager = None
        self.running = False
        self.token = token
        self.manager_host = server_host
        self.manager_port = server_port
        self.rest_api_port = rest_api_port
        self.system_usage_interval = system_usage_interval
        self.latency_check_interval = latency_check_interval
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize(self) -> bool:
        """
        Initialize the training service components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Training service initialization started")
            if not self.token:
                raise ValueError("Training agent token is required")

            # Fetch configuration from manager via gRPC
            self.connection_info_client = ConnectionInfoClient(
                host=self.manager_host,
                port=self.manager_port,
                token=self.token
            )
            connection_info = self.connection_info_client.get_connection_info()
            if not connection_info.get("success"):
                raise RuntimeError(f"Failed to fetch connection info: {connection_info.get('message')}")
            self.config = connection_info
            self.config["server_host"] = self.manager_host
            self.config["server_port"] = self.manager_port
            self.config["rest_api_port"] = self.rest_api_port
            self.config["token"] = self.token
            self.config["system_usage_interval"] = self.system_usage_interval
            self.config["latency_check_interval"] = self.latency_check_interval

            # Initialize gRPC clients
            self._initialize_grpc_clients()

            # Initialize WorkerManager
            self.worker_manager = WorkerManager(self.config)

            self.logger.info("Training service initialization completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize training service: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def _initialize_grpc_clients(self):
        """Initialize gRPC clients for communication with the manager"""
        try:
            # Initialize connection info client (already done in initialize)
            # Initialize system usage client
            self.system_usage_client = SystemUsageClient(
                host=self.manager_host,
                port=self.manager_port,
                token=self.token
            )
            # Initialize status client
            self.status_client = TrainingAgentStatusClient(
                host=self.manager_host,
                port=self.manager_port,
                token=self.token
            )

            self.logger.info("gRPC clients initialized and connected successfully")
        except Exception as e:
            import traceback
            self.logger.error(f"Failed to initialize gRPC clients: {e}")
            self.logger.error(traceback.format_exc())
            raise GrpcClientError(f"Failed to initialize gRPC clients: {e}")
    
    def start(self):
        """Start the training service"""
        if not self.running:
            self.running = True
            self.logger.info("Training service started")
            try:
                # Update status to connected
                self.status_client.update_status("connected")
                # Start all workers via WorkerManager
                self.worker_manager.start_all()
                # Block main thread to keep process alive
                while self.running:
                    time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in training service: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                self.stop()
        else:
            self.logger.info("Service already running.")
    
    def stop(self):
        """Stop the training service"""
        if self.running:
            self.running = False
            self.logger.info("Training service stopping...")
            try:
                # Update status to disconnected
                if self.status_client:
                    self.status_client.update_status("disconnected")
                # Stop all workers via WorkerManager
                if hasattr(self, 'worker_manager'):
                    self.worker_manager.stop_all()
                # Disconnect gRPC clients
                if self.connection_info_client:
                    self.connection_info_client.close()
                if self.system_usage_client:
                    self.system_usage_client.close()
                if self.status_client:
                    self.status_client.close()
                self.logger.info("Training service stopped")
            except Exception as e:
                self.logger.error(f"Error stopping training service: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
        else:
            self.logger.info("Service already stopped.")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def run(self):
        """Run the training service"""
        if self.initialize():
            self.start()
            sys.exit(1)


def main():
    """Main entry point for the training service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nedo Vision Training Service")
    parser.add_argument(
        "--token", 
        required=True,
        help="Training agent token (required)"
    )
    parser.add_argument(
        "--server-host", 
        required=True,
        help="Manager server host (required)"
    )
    parser.add_argument(
        "--server-port", 
        type=int,
        required=True,
        help="Manager server gRPC port (required)"
    )
    parser.add_argument(
        "--rest-api-port", 
        type=int,
        default=8081,
        help="Manager REST API port (default: 8081)"
    )
    parser.add_argument(
        "--system-usage-interval",
        type=int,
        default=5,
        help="System usage reporting interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--latency-check-interval",
        type=int,
        default=10,
        help="Latency monitoring interval in seconds (default: 10)"
    )
    args = parser.parse_args()
    
    service = TrainingService(
        token=args.token,
        server_host=args.server_host,
        server_port=args.server_port,
        rest_api_port=args.rest_api_port,
        system_usage_interval=args.system_usage_interval,
        latency_check_interval=args.latency_check_interval
    )
    service.run()


if __name__ == "__main__":
    main() 