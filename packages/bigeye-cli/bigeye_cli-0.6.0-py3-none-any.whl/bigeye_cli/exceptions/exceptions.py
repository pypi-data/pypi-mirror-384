class InvalidConfigurationException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidEntityException(Exception):
    def __init__(self, message: str):
        self.message = message


class MissingArgumentException(Exception):
    def __init__(self, message: str):
        self.message = message


class ResourceNotFoundException(Exception):
    def __init__(self, message: str):
        self.message = message
