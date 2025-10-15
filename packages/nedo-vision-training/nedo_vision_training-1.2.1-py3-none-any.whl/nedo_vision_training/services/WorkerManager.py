import logging

from ..client.TrainingAgentStatusClient import TrainingAgentStatusClient
from ..modules.trainer.Trainer import Trainer
from .DataSenderWorker import DataSenderWorker

logger = logging.getLogger(__name__)

class WorkerManager:
    def __init__(self, config):
        """Initialize all worker threads with the given config (from gRPC)."""
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

        self.status_client = TrainingAgentStatusClient(self.server_host, self.server_port, self.token)
        self.trainer = Trainer(config)
        self.data_sender_worker = DataSenderWorker(config)

    def _start_workers(self):
        """Start processing workers while keeping monitoring workers running."""
        try:
            self.data_sender_worker.start_updating()

            self.trainer.start()
            
            self._update_status("connected")

        except Exception as e:
            logger.error("🚨 Failed to start processing workers.", exc_info=True)

    def _stop_workers(self):
        """Stop processing workers while keeping monitoring workers running."""
        try:
            self.data_sender_worker.stop_updating()

            self.trainer.shutdown_handler()

            self._update_status("disconnected")

        except Exception as e:
            logger.error("🚨 Failed to stop processing workers.", exc_info=True)

    def start_all(self):
        """Start all workers including monitoring workers."""
        try:
            self.data_sender_worker.start()

            self._start_workers()

            logger.info("✅ All workers started successfully.")

        except Exception as e:
            logger.error("🚨 Failed to start all workers.", exc_info=True)

    def stop_all(self):
        """Stop all workers including monitoring workers."""
        try:
            self.data_sender_worker.stop()

            self._stop_workers()

            logger.info("✅ All workers stopped successfully.")

        except Exception as e:
            logger.error("🚨 Failed to stop all workers.", exc_info=True)
    
    def _update_status(self, status_code):
        """
        Update the worker status via gRPC.
        
        Args:
            status_code (str): Status code to report to the server
        """
        try:
            logger.info(f"📡 Updating worker status to {status_code}")
            result = self.status_client.update_status(status_code)
            if result:
                logger.info(f"✅ Status update successful.")
            else:
                logger.warning(f"⚠️ Status update failed.")
        except Exception as e:
            logger.error(f"🚨 Error updating worker status: {str(e)}")
