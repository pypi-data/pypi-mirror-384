from enum import StrEnum

class Key(StrEnum):
    """Defines valid keys in Cohere."""
    BASE_URL = 'base_url'
    IMAGE_URL = 'image_url'
    INPUT_TYPE = 'input_type'
    MAX_RETRIES = 'max_retries'
    MODEL = 'model'
    TIMEOUT = 'timeout'
    TYPE = 'type'
    URL = 'url'

class CohereInputType(StrEnum):
    """Defines valid embedding input types for Cohere embedding API."""
    CLASSIFICATION = 'classification'
    CLUSTERING = 'clustering'
    IMAGE = 'image'
    SEARCH_DOCUMENT = 'search_document'
    SEARCH_QUERY = 'search_query'
