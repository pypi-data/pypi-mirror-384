import logging
import re
import uuid
from nedo_vision_training.logger.Logger import Logger
from nedo_vision_training.utils.platform_detector import PlatformDetector
from nedo_vision_training.utils.networking import Networking

logger = Logger()

class AppInitializer:
    @staticmethod
    def validate_uuid(value):
        """Validate if the provided value is a valid UUID."""
        try:
            uuid.UUID(value)
            return value
        except ValueError:
            raise ValueError(f"Invalid device ID format: {value}. Must be a valid UUID.")

    @staticmethod
    def validate_server_host(value):
        """Validate if the server host is a valid domain name or IP address."""
        domain_regex = (
            r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*"
            r"([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
        )
        ip_regex = (
            r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        )
        if re.match(domain_regex, value) or re.match(ip_regex, value):
            return value
        raise ValueError(f"Invalid server host: {value}. Must be a valid domain or IP address.")

    def initialize(self):
        """
        Placeholder for any future initialization logic. No registration is performed.
        """
        logger.info("AppInitializer: No registration logic required. Initialization complete.")
