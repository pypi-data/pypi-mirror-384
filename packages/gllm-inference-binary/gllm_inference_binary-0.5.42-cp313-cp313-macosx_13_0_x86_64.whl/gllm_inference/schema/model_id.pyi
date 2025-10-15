from _typeshed import Incomplete
from enum import StrEnum
from gllm_inference.utils import validate_string_enum as validate_string_enum
from pydantic import BaseModel

PROVIDER_SEPARATOR: str
PATH_SEPARATOR: str
URL_NAME_REGEX_PATTERN: str

class ModelProvider(StrEnum):
    """Defines the supported model providers."""
    ANTHROPIC = 'anthropic'
    AZURE_OPENAI = 'azure-openai'
    BEDROCK = 'bedrock'
    DATASAUR = 'datasaur'
    GOOGLE = 'google'
    JINA = 'jina'
    LANGCHAIN = 'langchain'
    LITELLM = 'litellm'
    OPENAI = 'openai'
    OPENAI_CHAT_COMPLETIONS = 'openai-chat-completions'
    OPENAI_COMPATIBLE = 'openai-compatible'
    TWELVELABS = 'twelvelabs'
    VOYAGE = 'voyage'
    XAI = 'xai'

OPTIONAL_PATH_PROVIDERS: Incomplete
PATH_SUPPORTING_PROVIDERS: Incomplete

class ModelId(BaseModel):
    '''Defines a representation of a valid model id.

    Attributes:
        provider (ModelProvider): The provider of the model.
        name (str | None): The name of the model.
        path (str | None): The path of the model.

    Provider-specific examples:
        # Using Anthropic
        ```python
        model_id = ModelId.from_string("anthropic/claude-sonnet-4-20250514")
        ```

        # Using Bedrock
        ```python
        model_id = ModelId.from_string("bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0")
        ```

        # Using Datasaur
        ```python
        model_id = ModelId.from_string("datasaur/https://deployment.datasaur.ai/api/deployment/teamId/deploymentId/")
        ```

        # Using Google
        ```python
        model_id = ModelId.from_string("google/gemini-2.5-flash-lite")
        ```

        # Using Jina
        ```python
        model_id = ModelId.from_string("jina/jina-embeddings-v2-large")
        ```
        For the list of supported models, please refer to the following page:
        https://jina.ai/models

        # Using OpenAI
        ```python
        model_id = ModelId.from_string("openai/gpt-5-nano")
        ```

        # Using OpenAI with Chat Completions API
        ```python
        model_id = ModelId.from_string("openai-chat-completions/gpt-5-nano")
        ```

        # Using OpenAI Responses API-compatible endpoints (e.g. SGLang)
        ```python
        model_id = ModelId.from_string("openai/https://my-sglang-url:8000/v1:my-model-name")
        ```

        # Using OpenAI Chat Completions API-compatible endpoints (e.g. Groq)
        ```python
        model_id = ModelId.from_string("openai-chat-completions/https://api.groq.com/openai/v1:llama3-8b-8192")
        ```

        # Using Azure OpenAI
        ```python
        model_id = ModelId.from_string("azure-openai/https://my-resource.openai.azure.com/openai/v1:my-deployment")
        ```

        # Using Voyage
        ```python
        model_id = ModelId.from_string("voyage/voyage-3.5-lite")
        ```

        # Using TwelveLabs
        ```python
        model_id = ModelId.from_string("twelvelabs/Marengo-retrieval-2.7")
        ```

        # Using LangChain
        ```python
        model_id = ModelId.from_string("langchain/langchain_openai.ChatOpenAI:gpt-4o-mini")
        ```
        For the list of supported providers, please refer to the following table:
        https://python.langchain.com/docs/integrations/chat/#featured-providers

        # Using LiteLLM
        ```python
        model_id = ModelId.from_string("litellm/openai/gpt-4o-mini")
        ```
        For the list of supported providers, please refer to the following page:
        https://docs.litellm.ai/docs/providers/

        # Using xAI
        ```python
        model_id = ModelId.from_string("xai/grok-4-0709")
        ```
        For the list of supported models, please refer to the following page:
        https://docs.x.ai/docs/models

    Custom model name validation example:
        ```python
        validation_map = {
            ModelProvider.ANTHROPIC: {"claude-sonnet-4-20250514"},
            ModelProvider.GOOGLE: {"gemini-2.5-flash-lite"},
            ModelProvider.OPENAI: {"gpt-4.1-nano", "gpt-5-nano"},
        }

        model_id = ModelId.from_string("...", validation_map)
        ```
    '''
    provider: ModelProvider
    name: str | None
    path: str | None
    @classmethod
    def from_string(cls, model_id: str, validation_map: dict[str, set[str]] | None = None) -> ModelId:
        """Parse a model id string into a ModelId object.

        Args:
            model_id (str): The model id to parse. Must be in the format defined in the following page:
                https://gdplabs.gitbook.io/sdk/resources/supported-models
            validation_map (dict[str, set[str]] | None, optional): An optional dictionary that maps provider names to
                sets of valid model names. For the defined model providers, the model names will be validated against
                the set of valid model names. For the undefined model providers, the model name will not be validated.
                Defaults to None.

        Returns:
            ModelId: The parsed ModelId object.

        Raises:
            ValueError: If the provided model id is invalid or if the model name is not valid for the provider.
        """
    def to_string(self) -> str:
        """Convert the ModelId object to a string.

        Returns:
            str: The string representation of the ModelId object. The format is defined in the following page:
                https://gdplabs.gitbook.io/sdk/resources/supported-models
        """
