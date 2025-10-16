from gllm_inference.schema.attachment import Attachment as Attachment
from gllm_inference.schema.reasoning import Reasoning as Reasoning
from gllm_inference.schema.tool_call import ToolCall as ToolCall
from gllm_inference.schema.tool_result import ToolResult as ToolResult
from pydantic import BaseModel
from typing import Any

ResponseSchema = dict[str, Any] | type[BaseModel]
MessageContent = str | Attachment | ToolCall | ToolResult | Reasoning
EMContent = str | Attachment | tuple[str | Attachment, ...]
Vector = list[float]
