class Key:
    """Defines valid keys in Bedrock."""
    ACCEPT: str
    CONTENT_TYPE: str
    HTTP_STATUS_CODE: str
    INPUT_TEXT: str
    INPUT_TYPE: str
    MODEL_ID: str
    RESPONSE_METADATA: str
    TEXTS: str

class InputType:
    """Defines valid input types in Bedrock."""
    APPLICATION_JSON: str
    SEARCH_DOCUMENT: str
    SEARCH_QUERY: str

class OutputType:
    """Defines valid output types in Bedrock."""
    BODY: str
    EMBEDDING: str
    EMBEDDINGS: str
