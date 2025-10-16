from enum import StrEnum

class InputType(StrEnum):
    """Defines the supported input types for the Jina AI embedding API."""
    IMAGE_URL = 'image_url'
    TEXT = 'text'

class Key(StrEnum):
    """Defines key constants used in the Jina AI API payloads."""
    DATA = 'data'
    EMBEDDING = 'embedding'
    ERROR = 'error'
    IMAGE_URL = 'image_url'
    INPUT = 'input'
    JSON = 'json'
    MESSAGE = 'message'
    MODEL = 'model'
    RESPONSE = 'response'
    STATUS = 'status'
    TASK = 'task'
    TEXT = 'text'
    TYPE = 'type'
    URL = 'url'

class OutputType(StrEnum):
    """Defines the expected output types returned by the Jina AI embedding API."""
    DATA = 'data'
    EMBEDDING = 'embedding'
