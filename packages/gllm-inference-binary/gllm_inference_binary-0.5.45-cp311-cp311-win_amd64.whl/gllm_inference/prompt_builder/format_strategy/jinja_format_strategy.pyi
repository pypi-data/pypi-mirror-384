from _typeshed import Incomplete
from gllm_inference.prompt_builder.format_strategy.format_strategy import BasePromptFormattingStrategy as BasePromptFormattingStrategy
from gllm_inference.schema import JinjaEnvType as JinjaEnvType
from jinja2.sandbox import SandboxedEnvironment
from typing import Any

JINJA_DEFAULT_BLACKLISTED_FILTERS: list[str]
JINJA_DEFAULT_SAFE_GLOBALS: dict[str, Any]
JINJA_DANGEROUS_PATTERNS: list[str]
PROMPT_BUILDER_VARIABLE_START_STRING: str
PROMPT_BUILDER_VARIABLE_END_STRING: str

class JinjaFormatStrategy(BasePromptFormattingStrategy):
    """Jinja2 template engine for formatting prompts.

    Attributes:
        jinja_env (SandboxedEnvironment): The Jinja environment for rendering templates.
        key_defaults (dict[str, str]): The default values for the keys.
    """
    jinja_env: Incomplete
    def __init__(self, environment: JinjaEnvType | SandboxedEnvironment = ..., key_defaults: dict[str, str] | None = None) -> None:
        """Initialize the JinjaFormatStrategy.

        Args:
            environment (JinjaEnvType | SandboxedEnvironment, optional): The environment for Jinja rendering.
                It can be one of the following:
                1. `JinjaEnvType.RESTRICTED`: Uses a minimal, restricted Jinja environment.
                        Safest for most cases.
                2. `JinjaEnvType.JINJA_DEFAULT`: Uses the full Jinja environment. Allows more powerful templating,
                        but with fewer safety restrictions.
                3. `SandboxedEnvironment` instance: A custom Jinja `SandboxedEnvironment` object provided by the
                        user. Offers fine-grained control over template execution.
                Defaults to `JinjaEnvType.RESTRICTED`
            key_defaults (dict[str, str], optional): The default values for the keys. Defaults to None, in which
                case no default values are used.
        """
    def extract_keys(self, template: str | None) -> set[str]:
        """Extract keys from Jinja template using AST analysis.

        Args:
            template (str | None): The template to extract keys from.

        Returns:
            set[str]: The set of keys found in the template.
        """
