import os
import importlib
from importlib.util import find_spec
from ...logger.Logger import Logger
from nedo_vision_training.modules.trainer.TrainerRegistry import TrainerRegistry
from nedo_vision_training.modules.algorithm.RFDETR.RFDETRTrainer import RFDETRTrainer

logger = Logger(__name__)

class TrainerFactory:
    _trainers_loaded = False

    @classmethod
    def _load_trainers(cls, algorithm_path='nedo_vision_training.modules.algorithm'):
        """Private method to load trainers dynamically."""
        if cls._trainers_loaded:
            return

        # Locate the base directory of the algorithm module
        spec = find_spec(algorithm_path)
        if not spec or not spec.submodule_search_locations:
            raise ModuleNotFoundError(f"Cannot locate module: {algorithm_path}")

        base_path = spec.submodule_search_locations[0]

        # Walk through the base directory
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith("Trainer.py"):
                    # Construct the module path
                    relative_path = os.path.relpath(root, base_path)
                    module_name = (
                        f"{algorithm_path}.{relative_path.replace(os.sep, '.')}.{file[:-3]}"
                        if relative_path != "."
                        else f"{algorithm_path}.{file[:-3]}"
                    )
                    trainer_class_name = file.replace(".py", "")  # Class name matches the file name

                    try:
                        # Import the module and get the trainer class
                        module = importlib.import_module(module_name)
                        trainer_class = getattr(module, trainer_class_name)
                        TrainerRegistry.register_trainer(trainer_class_name.lower(), trainer_class)

                    except (ImportError, AttributeError) as e:
                        logger.error(f"Error loading trainer {trainer_class_name} from {module_name}: {e}")

        cls._trainers_loaded = True

    @staticmethod
    def get_trainer(algorithm_type):
        """Get a trainer by name, loading trainers if necessary."""
        TrainerFactory._load_trainers()
        return TrainerRegistry.get_trainer(algorithm_type)
