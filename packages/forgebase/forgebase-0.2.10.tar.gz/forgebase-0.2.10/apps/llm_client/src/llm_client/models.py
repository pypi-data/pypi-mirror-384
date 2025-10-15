from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, HttpUrl, model_validator


# --- Input Types ---
class InputText(BaseModel):
    type: Literal["input_text"]
    text: str


class InputImage(BaseModel):
    type: Literal["input_image"]
    image_url: HttpUrl


class InputAudio(BaseModel):
    type: Literal["input_audio"]
    audio_base64: str
    mime_type: Optional[str] = None


class InputFile(BaseModel):
    type: Literal["input_file"]
    file_id: str


InputItem = Union[InputText, InputImage, InputAudio, InputFile]

# --- Tool Result Input (for follow-up calls) ---
class InputToolResult(BaseModel):
    type: Literal["custom_tool_call_output"]
    call_id: str
    output: Union[str, List[Dict[str, Any]]]

# --- Tool Configuration ---
class Tool(BaseModel):
    type: Literal["function", "file_search", "web_search"]
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    strict: Optional[bool] = None

    @model_validator(mode="after")
    def _apply_responses_defaults(self) -> "Tool":
        """Ensure function tools match the Responses API contract."""
        if self.type == "function":
            if not self.name:
                raise ValueError("Function tools require a name")
            if self.strict is None:
                self.strict = True
        else:
            self.strict = None
        return self

# --- Text Output Format ---
class TextFormat(BaseModel):
    type: Literal["text", "json"]

class TextOutputConfig(BaseModel):
    format: Optional[TextFormat]

# --- Reasoning Config ---
class ReasoningConfig(BaseModel):
    effort: Optional[str] = None
    generate_summary: Optional[bool] = None

# --- Request Model ---
class ResponseRequest(BaseModel):
    model: str
    input: Union[str, List[Union[InputItem, InputToolResult, Dict[str, Any]]]]
    instructions: Optional[str] = None
    max_output_tokens: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None
    parallel_tool_calls: Optional[bool] = True
    previous_response_id: Optional[str] = None
    reasoning: Optional[ReasoningConfig] = None
    store: Optional[bool] = True
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    text: Optional[TextOutputConfig] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = "auto"
    tools: Optional[List[Tool]] = None
    top_p: Optional[float] = 1.0
    truncation: Optional[Literal["disabled", "auto"]] = "disabled"
    user: Optional[str] = None
    include: Optional[List[str]] = None

# --- Output Content ---
class ContentPart(BaseModel):
    type: str
    text: Optional[str] = None
    annotations: Optional[List[Dict[str, Any]]] = None
    # tool calling extras (Responses API)
    name: Optional[str] = None
    id: Optional[str] = None
    tool_use_id: Optional[str] = None
    input: Optional[Union[Dict[str, Any], str]] = None
    arguments: Optional[Union[Dict[str, Any], str]] = None


class OutputMessage(BaseModel):
    type: str
    id: str
    status: str
    role: str
    content: List[ContentPart]

# Function calling (Responses API) – item top-level
class FunctionCallItem(BaseModel):
    type: Literal["function_call"]
    name: str
    call_id: str
    arguments: Union[Dict[str, Any], str]

# Some Responses API variants may return top-level content parts or function calls directly.
# Put ContentPart/FunctionCallItem first para facilitar o parse quando faltam campos de mensagem.
OutputItem = Union[ContentPart, FunctionCallItem, OutputMessage]

# --- Usage Info ---
class UsageDetails(BaseModel):
    input_tokens: int
    input_tokens_details: Optional[Dict[str, int]]
    output_tokens: int
    output_tokens_details: Optional[Dict[str, int]]
    total_tokens: int

# --- Response Model ---
class ResponseResult(BaseModel):
    id: str
    object: str
    created_at: int
    status: str
    error: Optional[Dict[str, Any]]
    incomplete_details: Optional[Dict[str, Any]]
    instructions: Optional[str]
    max_output_tokens: Optional[int]
    model: str
    output: List[OutputItem]
    parallel_tool_calls: Optional[bool]
    previous_response_id: Optional[str]
    reasoning: Optional[ReasoningConfig]
    store: Optional[bool]
    temperature: Optional[float]
    text: Optional[TextOutputConfig]
    tool_choice: Optional[Union[str, Dict[str, Any]]]
    tools: Optional[List[Tool]]
    top_p: Optional[float]
    truncation: Optional[str]
    usage: Optional[UsageDetails]
    user: Optional[str]
    metadata: Optional[Dict[str, str]]
