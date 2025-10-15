import threading
import time

from ..logger.Logger import Logger
from ..modules.data_sync.SystemUsageManager import SystemUsageManager

logger = Logger(__name__)

class DataSenderWorker:
    def __init__(self, config: dict, send_interval=None, update_interval=10):
        """
        Initializes the Data Sender Worker.

        Args:
            config (dict): Configuration dictionary.
            send_interval (int): Interval (in seconds) for sending system usage & images. 
                               If None, uses 'system_usage_interval' from config (default: 5).
            update_interval (int): Interval (in seconds) for updating worker sources.
        """
        if not isinstance(config, dict):
            raise ValueError("⚠️ config must be a dictionary.")

        self.config = config
        self.server_host = self.config.get("server_host")
        self.server_port = self.config.get("server_port")
        self.token = self.config.get("token")

        if not self.server_host:
            raise ValueError("⚠️ Configuration is missing 'server_host'.")
        if not self.server_port:
            raise ValueError("⚠️ Configuration is missing 'server_port'.")
        if not self.token:
            raise ValueError("⚠️ Configuration is missing 'token'.")
        
        self.should_update = True

        # Use configurable interval from config, fallback to send_interval parameter or default
        self.send_interval = send_interval if send_interval is not None else self.config.get("system_usage_interval", 5)
        self.update_interval = update_interval

        self.main_thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        # Initialize services - pass latency interval to SystemUsageManager
        latency_interval = self.config.get("latency_check_interval", 10)
        self.system_usage_manager = SystemUsageManager(
            self.server_host, 
            self.server_port, 
            self.token, 
            latency_interval=latency_interval
        )

    def start(self):
        """Start the Data Sender Worker threads."""
        with self.lock:
            if self.main_thread and self.main_thread.is_alive():
                logger.warning("⚠️ Data Sender Worker is already running.")
                return

            self.stop_event.clear()

            # ✅ Start the main worker thread (System usage + Image upload)
            self.main_thread = threading.Thread(target=self._run_main_worker, daemon=True)
            self.main_thread.start()

            logger.info(f"🚀 Data Sender Worker started.")

    def stop(self):
        """Stop the Data Sender Worker and Worker Source Updater threads."""
        with self.lock:
            if not self.main_thread or not self.main_thread.is_alive():
                logger.warning("⚠️ Data Sender Worker is not running.")
                return

            self.stop_event.set()

            # ✅ Stop the main worker thread
            if self.main_thread:
                self.main_thread.join(timeout=5)

            self.main_thread = None

            logger.info(f"🛑 Data Sender Worker stopped.")

    def start_updating(self):
        """Start updating worker sources."""
        self.should_update = True

    def stop_updating(self):
        """Stop updating worker sources."""
        self.should_update = False

    def _run_main_worker(self):
        """Main loop for sending system usage and uploading images."""
        try:
            while not self.stop_event.is_set():
                self.system_usage_manager.process_system_usage()
                time.sleep(self.send_interval)
        except Exception as e:
            logger.error("🚨 Unexpected error in main worker loop.")
