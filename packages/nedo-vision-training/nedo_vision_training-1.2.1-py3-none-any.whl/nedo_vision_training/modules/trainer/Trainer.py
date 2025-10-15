import json
import time
import os
import shutil
import multiprocessing
from threading import Thread, Event

import pika

from ...client.RabbitMQClient import RabbitMQClient
from ...logger.Logger import Logger
from nedo_vision_training.logger.TrainerLogger import TrainerLogger
from nedo_vision_training.modules.trainer.TrainerFactory import TrainerFactory
from .TrainerParams import TrainParams

def run_training_in_process_standalone(job_id, algorithm, dataset_id, epoch, batch_size, split_ratio, config):
    """
    Standalone function to run training in a separate process.
    This avoids pickling issues with the Trainer instance.
    
    Args:
        job_id: Training job ID
        algorithm: Algorithm name
        dataset_id: Dataset ID
        epoch: Number of epochs
        batch_size: Batch size
        split_ratio: Train/test split ratio
        config: Configuration dictionary
    """
    trainer_algorithm = None  # Initialize variable for cleanup
    try:
        # Create a new logger for the training process
        training_logger = Logger(f"TRAINING_PROCESS:{job_id}")
        training_logger.info(f"🚀 Starting training process for job {job_id}")
        
        # Create TrainParams object in the child process
        train_params = TrainParams(job_id, algorithm, dataset_id, epoch, batch_size, split_ratio)
    
        # Initialize trainer in the separate process
        trainer_class = TrainerFactory.get_trainer(train_params.algorithm)
        trainer_algorithm = trainer_class(config)
        trainer_algorithm.init(train_params)
        
        # Run training steps
        trainer_algorithm.train()
        trainer_algorithm.evaluate()
        trainer_algorithm.save_model()
        trainer_algorithm.upload_model()
        
        training_logger.info(f"✅ Training process completed successfully for job {job_id}")
        
    except Exception as e:
        # Log error and cleanup in the training process
        training_logger = Logger(f"TRAINING_PROCESS:{job_id}")
        training_logger.error(f"❌ Training process failed for job {job_id}: {e}")
        
        # Update status to failed
        if hasattr(trainer_algorithm, "trainer_logger"):
            trainer_logger = trainer_algorithm.trainer_logger
        else:
            trainer_logger = TrainerLogger()
        trainer_logger.log_status(job_id, "failed")
        trainer_logger.log_command(job_id, "Training process failed.")
        
    finally:
        try:
            if trainer_algorithm and hasattr(trainer_algorithm, 'cleanup_artifacts'):
                trainer_algorithm.cleanup_artifacts()
                training_logger.info(f"🧹 Cleanup completed for job {job_id}")
            else:
                training_logger.warning(f"⚠️ No trainer_algorithm available for cleanup of job {job_id}")
        except Exception as cleanup_error:
            training_logger.error(f"❌ Cleanup failed for job {job_id}: {cleanup_error}")

class Trainer:
    def __init__(self, config):
        self.threads = []
        self.config = config or {}
        self.token = self.config.get("token")
        self.agent_id = self.config.get("id") or self.token
        self.training_exchange = 'nedo.train'
        self.training_queue = f'nedo.train.queue.{self.agent_id}'
        self.on_training_request = self.process_training_request
        self.training_rabbitmq_client = None
        self.agent_rabbitmq_client = None
        self.training_listener_thread = None
        self.logger = Logger(__name__)
        self.trainer_logger = TrainerLogger(self.config)
        self.stop_event = Event()
        self.training_processes = {}  # Track running training processes

    def cleanup_completed_processes(self):
        """
        Clean up completed training processes from tracking.
        """
        completed_jobs = []
        for job_id, process in self.training_processes.items():
            if not process.is_alive():
                completed_jobs.append(job_id)
                process.join()  # Clean up the process
        
        # Remove completed processes from tracking
        for job_id in completed_jobs:
            del self.training_processes[job_id]
            self.logger.info(f"🧹 Cleaned up completed training process for job {job_id}")

    def shutdown_handler(self):
        """
        Handles `Ctrl+C` (SIGINT) or system termination (SIGTERM).
        """
        self.logger.info("🛑 Shutdown signal received. Stopping all listeners...")
        self.stop_event.set()

        # Terminate all running training processes
        for job_id, process in self.training_processes.items():
            if process.is_alive():
                self.logger.info(f"🛑 Terminating training process for job {job_id} (PID: {process.pid})")
                process.terminate()
                process.join(timeout=5)  # Wait up to 5 seconds
                if process.is_alive():
                    self.logger.warning(f"⚠️ Force killing training process for job {job_id}")
                    process.kill()
                    process.join()

        if self.training_rabbitmq_client:
            self.training_rabbitmq_client.close()

    def initialize_trainer_queue(self):
        self.training_rabbitmq_client = RabbitMQClient(self.config, heartbeat=3600, blocked_connection_timeout=600, name="training_request")
        self.training_rabbitmq_client.connect()
        self.training_rabbitmq_client.declare_exchange(self.training_exchange, exchange_type='direct')
        self.training_rabbitmq_client.declare_queue(self.training_queue)
        self.training_rabbitmq_client.bind_queue(self.training_exchange, self.training_queue, self.agent_id)

    def watch_training_requests(self):
        if not callable(self.on_training_request):
            raise ValueError("on_training_request callback must be callable")
        while not self.stop_event.is_set():  # Loop will break if stop_event is set
            try:
                self.initialize_trainer_queue()

                def on_message(ch, method, properties, body):
                    try:
                        if self.stop_event.is_set():
                            self.logger.info("🛑 Stop event received. Stopping message consumption.")
                            ch.stop_consuming()
                            return
                        
                        message_dict = json.loads(body)
                        job_id = message_dict.get("id")
                        algorithm = message_dict.get("algorithm")
                        dataset_id = message_dict.get("dataset_id")
                        epoch = message_dict.get("epoch")
                        batch_size = message_dict.get("batch_size")
                        split_ratio = message_dict.get("split_ratio")

                        self.on_training_request(job_id, algorithm, dataset_id, epoch, batch_size, split_ratio)
                        if not ch.is_closed:
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                        else:
                            self.logger.warning("Cannot ack message; channel is already closed.")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Invalid JSON message: {e}")
                        if not ch.is_closed:
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                        else:
                            self.logger.warning("Cannot ack message; channel is already closed.")
                    except Exception as e:
                        self.logger.error(f"Error processing training message: {e}")
                        if not ch.is_closed:
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                        else:
                            self.logger.warning("Cannot ack message; channel is already closed.")

                self.training_rabbitmq_client.channel.basic_qos(prefetch_count=1)
                self.training_rabbitmq_client.consume_messages(self.training_queue, on_message)
                self.logger.info("Waiting for training requests...")
                
                # Clean up completed processes periodically
                self.cleanup_completed_processes()
                
            except pika.exceptions.AMQPConnectionError as e:
                self.logger.error(f"Connection error: {e}. Reconnecting in 5 seconds...")
                time.sleep(5)
            except pika.exceptions.StreamLostError as e:
                self.logger.error(f"Stream connection lost: {e}. Reconnecting in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in watch_training_requests: {e}")
                break

    def cleanup_training_artifacts(self, job_id: str):
        """
        Clean up training artifacts for a failed training job.
        
        Args:
            job_id (str): The training job ID
        """
        try:
            # Clean up dataset artifacts
            dataset_dir = os.path.join(self.config.get("storage_path", ""), "artifacts", "datasets", str(job_id))
            if os.path.exists(dataset_dir):
                shutil.rmtree(dataset_dir)
                self.logger.info(f"🧹 Cleaned up dataset artifacts for job {job_id}")
            
            # Clean up model artifacts
            model_dir = os.path.join(self.config.get("storage_path", ""), "artifacts", "models", str(job_id))
            if os.path.exists(model_dir):
                shutil.rmtree(model_dir)
                self.logger.info(f"🧹 Cleaned up model artifacts for job {job_id}")
            
            # Clean up training artifacts
            train_dir = os.path.join(self.config.get("storage_path", ""), "artifacts", "train", str(job_id))
            if os.path.exists(train_dir):
                shutil.rmtree(train_dir)
                self.logger.info(f"🧹 Cleaned up training artifacts for job {job_id}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up artifacts for job {job_id}: {e}")

    def process_training_request(self, job_id, algorithm, dataset_id, epoch, batch_size, split_ratio):
        self.logger.info(
            f"\n📌 [TRAINING REQUEST] Received:\n"
            f"   ├── 🆔 ID           : {job_id}\n"
            f"   ├── 🧠 Algorithm    : {algorithm}\n"
            f"   ├── 📂 Dataset      : {dataset_id}\n"
            f"   ├── Epoch           : {epoch}\n"
            f"   ├── Batch Size      : {batch_size}\n"
            f"   ├── Split ratio     : {split_ratio}\n"
            f"   └── 🚀 Starting training in separate process..."
        )

        try:
            # Start training in a separate process
            training_process = multiprocessing.Process(
                target=run_training_in_process_standalone,
                args=(job_id, algorithm, dataset_id, epoch, batch_size, split_ratio, self.config),
                name=f"Training-{job_id}"
            )
            training_process.start()
            
            self.logger.info(f"🔄 Training process started (PID: {training_process.pid}) for job {job_id}")
            
            # Track the training process
            self.training_processes[job_id] = training_process
            
        except Exception as e:
            trainer_logger = TrainerLogger()
            trainer_logger.log_status(job_id, "failed")
            trainer_logger.log_command(job_id, "Training process failed.")
            self.logger.error(f"Error starting training process: {e}")
            
            # Clean up artifacts on failure
            self.logger.info(f"🧹 Starting cleanup for failed training job {job_id}")
            self.cleanup_training_artifacts(job_id)
            self.logger.info(f"✅ Cleanup completed for failed training job {job_id}")

    def start_training_request_listener(self):
        """Start the training request listener thread only if it's not running."""
        if self.training_listener_thread and self.training_listener_thread.is_alive():
            self.logger.warning("⚠️ Training request listener is already running.")
            return

        self.logger.info("📩 Starting training request listener...")
        
        self.training_listener_thread = Thread(target=self.watch_training_requests, daemon=True)
        self.threads.append(self.training_listener_thread)
        self.training_listener_thread.start()

    def start(self):
        """
        Starts the trainer and listens for `Ctrl+C` to exit gracefully.
        """
        if not callable(self.on_training_request):
            raise ValueError("on_training_request callback must be set before starting the trainer")

        self.logger.info("🚀 Starting Trainer...")

        self.start_training_request_listener()

