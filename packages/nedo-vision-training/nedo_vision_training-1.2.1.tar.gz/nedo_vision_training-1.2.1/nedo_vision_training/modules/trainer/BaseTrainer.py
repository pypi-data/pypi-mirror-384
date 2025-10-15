from abc import ABC, abstractmethod

class BaseTrainer(ABC):
    def __init__(self, config=None):
        self.config = config
        self._rabbitmq_config = config or {}
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None

    @property
    def rabbitmq_config(self):
        return self._rabbitmq_config

    @abstractmethod
    def train(self, data, labels):
        pass

    @abstractmethod
    def evaluate(self, test_data):
        pass

    @abstractmethod
    def save_model(self, file_path):
        pass

    @abstractmethod
    def load_model(self, file_path):
        pass