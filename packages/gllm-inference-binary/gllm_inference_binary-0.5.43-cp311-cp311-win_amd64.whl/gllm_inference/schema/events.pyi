from gllm_core.constants import EventLevel
from gllm_core.schema import Event
from gllm_inference.schema.activity import Activity as Activity
from gllm_inference.schema.enums import EmitDataType as EmitDataType
from typing import Literal

class ActivityEvent(Event):
    """Event schema for model-triggered activities (e.g. web search, MCP).

    Attributes:
        id (str): The unique identifier for the activity event. Defaults to an empty string.
        type (Literal): The type of event, always 'activity'.
        value (Activity): The activity data containing message and type.
        level (EventLevel): The severity level of the event. Defined through the EventLevel constants.
    """
    id: str
    type: Literal[EmitDataType.ACTIVITY]
    value: Activity
    level: EventLevel

class CodeEvent(Event):
    """Event schema for model-triggered code execution.

    Attributes:
        id (str): The unique identifier for the code event. Defaults to an empty string.
        type (Literal): The type of event (code, code_start, or code_end).
        value (str): The code content.
        level (EventLevel): The severity level of the event. Defined through the EventLevel constants.
    """
    id: str
    type: Literal[EmitDataType.CODE, EmitDataType.CODE_START, EmitDataType.CODE_END]
    value: str
    level: EventLevel
    @classmethod
    def start(cls, id_: str | None = '') -> CodeEvent:
        """Create a code start event.

        Args:
            id_ (str | None): The unique identifier for the code event. Defaults to an empty string.

        Returns:
            CodeEvent: The code start event.
        """
    @classmethod
    def content(cls, id_: str | None = '', value: str = '') -> CodeEvent:
        """Create a code content event.

        Args:
            id_ (str | None): The unique identifier for the code event. Defaults to an empty string.
            value (str): The code content.

        Returns:
            CodeEvent: The code value event.
        """
    @classmethod
    def end(cls, id_: str | None = '') -> CodeEvent:
        """Create a code end event.

        Args:
            id_ (str | None): The unique identifier for the code event. Defaults to an empty string.

        Returns:
            CodeEvent: The code end event.
        """

class ThinkingEvent(Event):
    """Event schema for model thinking.

    Attributes:
        id (str): The unique identifier for the thinking event. Defaults to an empty string.
        type (Literal): The type of thinking event (thinking, thinking_start, or thinking_end).
        value (str): The thinking content or message.
        level (EventLevel): The severity level of the event. Defined through the EventLevel constants.
    """
    id: str
    type: Literal[EmitDataType.THINKING, EmitDataType.THINKING_START, EmitDataType.THINKING_END]
    value: str
    level: EventLevel
    @classmethod
    def start(cls, id_: str | None = '') -> ThinkingEvent:
        """Create a thinking start event.

        Args:
            id_ (str | None): The unique identifier for the thinking event. Defaults to an empty string.

        Returns:
            ThinkingEvent: The thinking start event.
        """
    @classmethod
    def content(cls, id_: str | None = '', value: str = '') -> ThinkingEvent:
        """Create a thinking value event.

        Args:
            id_ (str | None): The unique identifier for the thinking event. Defaults to an empty string.
            value (str): The thinking content or message.

        Returns:
            ThinkingEvent: The thinking value event.
        """
    @classmethod
    def end(cls, id_: str | None = '') -> ThinkingEvent:
        """Create a thinking end event.

        Args:
            id_ (str | None): The unique identifier for the thinking event. Defaults to an empty string.

        Returns:
            ThinkingEvent: The thinking end event.
        """
