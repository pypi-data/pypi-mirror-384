from nedo_vision_training.logger.Logger import Logger

logger = Logger(__name__)

class TrainerRegistry:
    _trainers = {}

    @classmethod
    def register_trainer(cls, key, trainer_class):
        normalized_key = key.lower()
        cls._trainers[normalized_key] = trainer_class

    @classmethod
    def get_trainer(cls, key):
        normalized_key = key.lower()
        trainer_class = cls._trainers.get(normalized_key)
        if not trainer_class:
            logger.info(f"Available trainers: {cls._trainers.keys()}")
            raise ValueError(f"No trainer registered with key: {key}")
        
        logger.info(f"🔍 Retrieved trainer for key: '{normalized_key}'.")
        return trainer_class

    @classmethod
    def get_all_trainers(cls):
        return list(cls._trainers.keys())
