import threading
import time
from nedo_vision_training.client.GrpcClientBase import GrpcClientBase
from nedo_vision_training.client.SystemUsageClient import SystemUsageClient
from nedo_vision_training.logger.Logger import Logger
from nedo_vision_training.utils.system_monitor import SystemMonitor
from nedo_vision_training.utils.networking import Networking
# from client.SystemUsageClient import SystemUsageClient

logger = Logger(__name__)

class SystemUsageManager:
    def __init__(self, server_host: str, port: int, auth_token: str, latency_interval: int = 10):
        """
        Handles system usage monitoring, latency tracking, and reporting.

        Args:
            server_host (str): The gRPC server host.
            port (int): The gRPC server port.
            auth_token (str): Authentication token for the training agent.
            latency_interval (int): Interval in seconds for latency monitoring (default: 10).
        """
        if not auth_token:
            raise ValueError("⚠️ 'auth_token' cannot be empty.")

        self.system_monitor = SystemMonitor()
        self.system_usage_client = SystemUsageClient(server_host, port, auth_token)
        self.server_host = server_host
        self.port = port
        self.auth_token = auth_token
        self.latency_interval = latency_interval
        self.latency = None
        self.latency_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.latency_thread = None  

        self._start_latency_monitoring()

    def _start_latency_monitoring(self):
        """Starts a background thread to monitor network latency."""
        if self.latency_thread and self.latency_thread.is_alive():
            logger.warning("⚠️ Latency monitoring thread is already running.")
            return

        self.latency_thread = threading.Thread(target=self._monitor_latency, daemon=True)
        self.latency_thread.start()
        logger.info("📡 Latency monitoring started.")

    def _monitor_latency(self):
        """Periodically checks the network latency using gRPC and updates the latency variable."""
        server_port = 50051  # Default gRPC port

        while not self.stop_event.is_set():
            try:
                latency_value = Networking.check_grpc_latency(self.server_host, server_port)
                with self.latency_lock:
                    self.latency = latency_value
                # logger.info(f"🔄 Updated network latency: {latency_value} ms")

            except Exception as e:
                logger.error("🚨 Error checking gRPC latency.", exc_info=True)
                with self.latency_lock:
                    self.latency = None  
            time.sleep(self.latency_interval) 

    def process_system_usage(self):
        """Collect and send system usage data to the server, including network latency."""
        try:
            usage = self.system_monitor.get_system_usage()
            cpu_usage = usage["cpu"]["usage_percent"]
            ram_usage = usage["ram"]
            gpu_usage = usage.get("gpu", [])

            with self.latency_lock:
                latency = self.latency if self.latency is not None else -1

            response = self.system_usage_client.send_system_usage(
                cpu_usage=cpu_usage,
                ram_usage=ram_usage,
                gpu_usage=gpu_usage,
                latency=latency,
            )

            error_message = GrpcClientBase.get_error_message(response)
            if error_message:
                logger.error(f"❌ Failed to send system usage: {error_message}")
            #else:
            #    logger.info("✅ System usage sent successfully.")

        except Exception as e:
            print(e)
            logger.error("🚨 Error sending system usage.")

    def close(self):
        """Closes the system usage client and stops the latency thread."""
        self.stop_event.set()

        if self.latency_thread and self.latency_thread.is_alive():
            self.latency_thread.join()
            logger.info("🔌 Latency monitoring thread stopped.")

        if self.system_usage_client:
            self.system_usage_client.close_client()
            logger.info("✅ SystemUsageClient closed.")
