from typing import Dict, Any
from nedo_vision_training.logger.TrainerLogger import TrainerLogger


def safe_index(lst, index):
    """Safely get an item from a list by index."""
    try:
        return lst[index] if lst and len(lst) > index else None
    except (IndexError, TypeError):
        return None


class RFDETRMetricsCallback:
    def __init__(self, logger: TrainerLogger, run_id):
        self.job_id = run_id
        self.logger = logger
        self.current_epoch = 0
        self.end_of_train = False

    def on_fit_epoch_end(self, log_stats):
        """Called at the end of each training epoch."""
        self.current_epoch = log_stats.get('epoch', self.current_epoch) + 1
        self.logger.log_command(self.job_id, f"Epoch {self.current_epoch} ended.")
        
        # Format and log metrics
        metrics = self._format_metrics(log_stats)
        self.logger.log_metric(self.job_id, metrics)

    def _format_metrics(self, log_stats: Dict[str, Any]) -> dict:
        """Formats the metrics for logging."""
        # Extract mAP values from COCO evaluation using safe indexing
        coco_eval = log_stats.get('test_coco_eval_bbox', [])
        # Handle different possible structures of coco_eval
        mAP_50_95 = 0
        mAP_50 = 0
        
        if isinstance(coco_eval, (list, tuple)):
            # If it's a list/tuple, try to access by index
            mAP_50_95 = safe_index(coco_eval, 0)  # mAP50-95
            mAP_50 = safe_index(coco_eval, 1)     # mAP50
        elif isinstance(coco_eval, dict):
            # If it's a dict, try to access by key
            mAP_50_95 = coco_eval.get('mAP50-95', 0)
            mAP_50 = coco_eval.get('mAP50', 0)
        else:
            # If it's something else, try to convert to list
            try:
                coco_list = list(coco_eval) if hasattr(coco_eval, '__iter__') else [coco_eval]
                mAP_50_95 = safe_index(coco_list, 0)
                mAP_50 = safe_index(coco_list, 1)
            except Exception as e:
                print(f"⚠️ Error converting coco_eval to list: {e}")
                mAP_50_95 = 0
                mAP_50 = 0
        
        # Use 0 as default if values are None
        mAP_50_95 = mAP_50_95 if mAP_50_95 is not None else 0
        mAP_50 = mAP_50 if mAP_50 is not None else 0
        
        # Calculate precision and recall or approximate them if not available
        test_stats = {k: v for k, v in log_stats.items() if k.startswith('test_')}
        precision = test_stats.get('precision', coco_eval[1])
        recall = test_stats.get('recall', coco_eval[8])
        
        # Calculate F1 score
        if precision + recall > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0.0
        
        return {
            "epoch": self.current_epoch,
            "map_50": round(mAP_50, 4),
            "map_50_95": round(mAP_50_95, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4)
        } 