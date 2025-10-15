import os
import shutil
import tempfile
from rfdetr import RFDETRBase

from nedo_vision_training.logger.Logger import Logger
from nedo_vision_training.logger.TrainerLogger import TrainerLogger
from nedo_vision_training.modules.trainer.BaseTrainer import BaseTrainer
from nedo_vision_training.modules.dataset.COCODatasetHandler import COCODatasetHandler
from nedo_vision_training.modules.algorithm.RFDETR.RFDETRMetricsCallback import RFDETRMetricsCallback
from nedo_vision_training.client.S3Client import S3Client
from nedo_vision_training.modules.trainer.TrainerRegistry import TrainerRegistry

class RFDETRTrainer(BaseTrainer):
    """
    Trainer class for fine-tuning and evaluating RF-DETR models for object detection.
    Handles model training, evaluation, and model uploads.
    """
    def __init__(self, config):
        super().__init__(config)
        self.logger = Logger(__name__)
        self.s3_client = S3Client(config)
        self.trainer_logger = TrainerLogger(config)
        self.model = None
        self.train_data = None
        self.test_data = None
        self.labels = None
        self.dataset_handler = None
        self.metrics_callback = None

    def init(self, training_job):
        """
        Initialize the RFDETRTrainer with dataset, labels, and training configuration.
        """
        self.training_job = training_job  # Store the training job
        self.job_id = training_job.id
        self.trainer_logger.log_status(self.job_id, "initializing")
        self.trainer_logger.log_command(self.job_id, "Initialization started.")

        # Handle the train/test split ratio from C# service
        # C# sends split_ratio as the training portion (e.g., 0.8 = 80% train, 20% test)
        # But RF-DETR needs train/val/test, so we need to create validation from the training portion
        original_train_ratio = training_job.split_ratio
        
        # If split_ratio is too high (>= 0.95), we need to ensure validation data exists
        if original_train_ratio >= 0.95:
            self.logger.warning(f"⚠️ Split ratio {original_train_ratio} is too high for RF-DETR training. Adjusting to ensure validation set.")
            # Use 80/20 split to ensure validation data
            train_ratio = 0.8
            val_ratio = 0.2
            test_ratio = 0.0
        else:
            # Take 10% from training data for validation to ensure RF-DETR can evaluate
            # Original: train_ratio = 0.8, remaining = 0.2 (intended for test)
            # Adjusted: train_ratio = 0.7, val_ratio = 0.1, test_ratio = 0.2
            validation_from_train = min(0.1, original_train_ratio * 0.125)  # Take 12.5% of training for validation, max 10%
            train_ratio = original_train_ratio - validation_from_train
            val_ratio = validation_from_train
            test_ratio = 1.0 - original_train_ratio
        
        self.logger.info(f"📊 Dataset split configuration: Train={train_ratio:.2f}, Val={val_ratio:.2f}, Test={test_ratio:.2f}")

        # Initialize dataset handler with train/test split ratios
        self.dataset_handler = COCODatasetHandler(
            dataset_id=training_job.dataset_id,
            output_dir=os.path.join("artifacts", "datasets", str(training_job.dataset_id)),
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            config=self.config
        )
        
        # Initialize RF-DETR model
        try:
            self.model = RFDETRBase()
            self.logger.info("📦 RFDETRBase initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Error during RFDETRBase initialization: {e}")
            self.model = RFDETRBase()
            self.logger.info("📦 RFDETRBase initialized (fallback after error)")
        
        # Initialize metrics callback
        self.metrics_callback = RFDETRMetricsCallback(self.trainer_logger, self.job_id)
        
        self.trainer_logger.log_command(self.job_id, "Initialization completed.")

    def train(self):
        """
        Train the RF-DETR model using the training data.
        """
        self.trainer_logger.log_status(self.job_id, "running")
        self.trainer_logger.log_command(self.job_id, "Training started.")

        try:
            # Process dataset into COCO format
            self.logger.info(f"🔍 Processing dataset for job {self.job_id}")
            dataset_info = self.dataset_handler.process_dataset()
            
            if not dataset_info.get("success", False):
                raise Exception(f"Failed to process dataset: {dataset_info.get('error')}")
            
            # Validate dataset splits
            splits = dataset_info.get("splits", {})
            train_count = splits.get("train", 0)
            val_count = splits.get("val", 0)
            
            self.logger.info(f"📊 Dataset split results: Train={train_count}, Val={val_count}")
            
            if train_count == 0:
                raise Exception("Training set is empty. Cannot proceed with training.")
            
            if val_count == 0:
                self.logger.warning("⚠️ Validation set is empty. RF-DETR requires validation data for proper training.")
                raise Exception("Validation set is empty. RF-DETR requires validation data to prevent evaluation errors.")
            
            batch_size = self.training_job.batch_size or 1  # Default to 1 if None or 0
            if batch_size <= 0:
                batch_size = 1
                self.logger.warning(f"⚠️ Invalid batch size {self.training_job.batch_size}, using default value of 1")
            
            epochs = self.training_job.epoch or 1  # Default to 1 if None or 0
            if epochs <= 0:
                epochs = 1
                self.logger.warning(f"⚠️ Invalid epoch count {self.training_job.epoch}, using default value of 1")
            
            grad_accum_steps = max(1, int(16 / batch_size))


            # Add metrics callback
            self.model.callbacks["on_fit_epoch_end"].append(self.metrics_callback.on_fit_epoch_end)
            # Train the model with callback
            self.logger.info(f"🚀 Starting training with batch_size={batch_size}, epochs={epochs}, grad_accum_steps={grad_accum_steps}")
            
            try:
                # Prepare training arguments based on validation data availability
                train_kwargs = {
                    "dataset_dir": self.dataset_handler.output_dir,
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "grad_accum_steps": grad_accum_steps,
                    "lr": 1e-4,
                    "output_dir": os.path.join("artifacts", "train", self.job_id),
                    "early_stopping": True
                }
                
                self.model.train(**train_kwargs)
            except Exception as e:
                import traceback
                self.logger.error(f"❌ Training failed: {e}")
                self.logger.error(f"❌ Full stack trace:")
                self.logger.error(traceback.format_exc())
                raise
            
            self.trainer_logger.log_command(self.job_id, "Training completed.")
            self.logger.info("✅ Training completed successfully")
                
        except Exception as e:
            self.logger.error(f"Error during training: {e}")
            # Clean up artifacts on training failure
            self.logger.info(f"🧹 Cleaning up artifacts due to training failure for job {self.job_id}")
            # self.cleanup_artifacts()
            raise

    def evaluate(self):
        """
        Evaluate the model on the test dataset.
        """
        self.trainer_logger.log_status(self.job_id, "evaluating")
        self.trainer_logger.log_command(self.job_id, "Evaluation started.")

        try:
            # Check if test data is available
            if self.test_data is None:
                self.logger.warning("⚠️ No test data available for evaluation, skipping evaluation step")
                self.trainer_logger.log_command(self.job_id, "Evaluation skipped - no test data available")
                return
            
            # Evaluate the model
            try:
                metrics = self.model.evaluate(self.test_data)
            except Exception as eval_error:
                import traceback
                self.logger.error(f"❌ Model evaluation failed: {eval_error}")
                self.logger.error(f"❌ Evaluation stack trace:")
                self.logger.error(traceback.format_exc())
                raise
            
            # Log the evaluation metrics
            if metrics:
                self.trainer_logger.log_metric(self.job_id, metrics)
            
            self.logger.info(f"Evaluation results: {metrics}")
            self.trainer_logger.log_command(self.job_id, "Evaluation completed.")
        except Exception as e:
            self.logger.error(f"Error during evaluation: {e}")
            # Clean up artifacts on evaluation failure
            self.logger.info(f"🧹 Cleaning up artifacts due to evaluation failure for job {self.job_id}")
            self.cleanup_artifacts()
            raise

    def save_model(self):
        """
        Save the trained model checkpoint.
        """
        self.trainer_logger.log_status(self.job_id, "saving")
        model_dir = os.path.join("artifacts", "models", self.job_id)
        os.makedirs(model_dir, exist_ok=True)

        try:
            # The checkpoint is saved in the output_dir used during training
            train_output_dir = os.path.join("artifacts", "train", self.job_id)
            checkpoint_path = os.path.join(train_output_dir, "checkpoint_best_total.pth")
            if not os.path.exists(checkpoint_path):
                self.logger.error(f"❌ No checkpoint found at {checkpoint_path}")
                raise ValueError("No checkpoint found after training")
            # Copy checkpoint to model_dir
            shutil.copy2(checkpoint_path, os.path.join(model_dir, "checkpoint_best_total.pth"))
            self.trainer_logger.log_command(self.job_id, "Model saving completed.")
            self.logger.info(f"✅ Model checkpoint saved to {model_dir}/checkpoint_best_total.pth")
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
            self.logger.info(f"🧹 Cleaning up artifacts due to save failure for job {self.job_id}")
            self.cleanup_artifacts()
            raise

    def upload_model(self):
        """
        Upload the trained model to S3 storage and update model information.
        """
        self.trainer_logger.log_command(self.job_id, "Model uploading started.")
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_file_path = os.path.join(tmp_dir, f"{self.job_id}.zip")
            
            model_dir = os.path.join("artifacts", "models", self.job_id)
            shutil.make_archive(zip_file_path.replace(".zip", ""), 'zip', model_dir)            
            zip_file_path = zip_file_path.replace(".zip", "") + ".zip"
            self.logger.info(f"Created model archive at {zip_file_path}")
            
            try:
                # Check if zip file exists
                if not os.path.exists(zip_file_path):
                    self.logger.error(f"❌ Model archive not found at {zip_file_path}")
                    raise ValueError("Model archive not found for upload")
                s3_path = f"model/{self.job_id}.zip"
                self.s3_client.upload_file(zip_file_path, s3_path)
                self.logger.info("Model successfully uploaded to S3.")
                
                self.trainer_logger.log_model_file_path(self.job_id, s3_path)
            except Exception as e:
                self.logger.error(f"An error occurred during model upload: {str(e)}")
                raise
        
        self.trainer_logger.log_command(self.job_id, "Model uploading completed.")
        self.trainer_logger.log_status(self.job_id, "completed")

    def cleanup_artifacts(self):
        """
        Clean up training artifacts for this job.
        """
        try:
            # Clean up dataset artifacts
            if self.dataset_handler and hasattr(self.dataset_handler, 'output_dir'):
                dataset_dir = self.dataset_handler.output_dir
                if os.path.exists(dataset_dir):
                    shutil.rmtree(dataset_dir)
                    self.logger.info(f"🧹 Cleaned up dataset artifacts for job {self.job_id}")
            
            # Clean up model artifacts
            model_dir = os.path.join("artifacts", "models", self.job_id)
            if os.path.exists(model_dir):
                shutil.rmtree(model_dir)
                self.logger.info(f"🧹 Cleaned up model artifacts for job {self.job_id}")
            
            # Clean up training artifacts
            train_dir = os.path.join("artifacts", "train", self.job_id)
            if os.path.exists(train_dir):
                shutil.rmtree(train_dir)
                self.logger.info(f"🧹 Cleaned up training artifacts for job {self.job_id}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up artifacts for job {self.job_id}: {e}")

    def load_model(self, file_path):
        """
        Load a trained RF-DETR model from checkpoint.
        """
        self.trainer_logger.log_command(self.job_id, f"Model loading started from {file_path}.")
        try:
            self.model = RFDETRBase(pretrain_weights=file_path)
            self.trainer_logger.log_command(self.job_id, "Model loading completed.")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise 

TrainerRegistry.register_trainer('RFDETR', RFDETRTrainer)