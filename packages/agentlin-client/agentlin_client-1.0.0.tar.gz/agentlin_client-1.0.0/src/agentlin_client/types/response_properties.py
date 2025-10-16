# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .response_tool import ResponseTool
from .conversations.input_file_content import InputFileContent
from .conversations.input_text_content import InputTextContent
from .conversations.input_image_content import InputImageContent
from .text_response_format_configuration import TextResponseFormatConfiguration

__all__ = [
    "ResponseProperties",
    "Prompt",
    "PromptVariables",
    "Reasoning",
    "Text",
    "ToolChoice",
    "ToolChoiceToolChoiceOptions",
    "ToolChoiceAllowedTools",
    "ToolChoiceToolChoiceTypes",
    "ToolChoiceFunction",
    "ToolChoiceMcp",
    "ToolChoiceCustom",
]

PromptVariables: TypeAlias = Union[str, InputTextContent, InputImageContent, InputFileContent]


class Prompt(BaseModel):
    id: str
    """The unique identifier of the prompt template to use."""

    variables: Optional[Dict[str, PromptVariables]] = None
    """Optional map of values to substitute in for variables in your prompt.

    The substitution values can either be strings, or other Response input types
    like images or files.
    """

    version: Optional[str] = None
    """Optional version of the prompt template."""


class Reasoning(BaseModel):
    effort: Optional[Literal["minimal", "low", "medium", "high"]] = None
    """
    Constrains effort on reasoning for
    [reasoning models](https://platform.openai.com/docs/guides/reasoning). Currently
    supported values are `minimal`, `low`, `medium`, and `high`. Reducing reasoning
    effort can result in faster responses and fewer tokens used on reasoning in a
    response.

    Note: The `gpt-5-pro` model defaults to (and only supports) `high` reasoning
    effort.
    """

    generate_summary: Optional[Literal["auto", "concise", "detailed"]] = None
    """**Deprecated:** use `summary` instead.

    A summary of the reasoning performed by the model. This can be useful for
    debugging and understanding the model's reasoning process. One of `auto`,
    `concise`, or `detailed`.
    """

    summary: Optional[Literal["auto", "concise", "detailed"]] = None
    """A summary of the reasoning performed by the model.

    This can be useful for debugging and understanding the model's reasoning
    process. One of `auto`, `concise`, or `detailed`.
    """


class Text(BaseModel):
    format: Optional[TextResponseFormatConfiguration] = None
    """An object specifying the format that the model must output.

    Configuring `{ "type": "json_schema" }` enables Structured Outputs, which
    ensures the model will match your supplied JSON schema. Learn more in the
    [Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs).

    The default format is `{ "type": "text" }` with no additional options.

    **Not recommended for gpt-4o and newer models:**

    Setting to `{ "type": "json_object" }` enables the older JSON mode, which
    ensures the message the model generates is valid JSON. Using `json_schema` is
    preferred for models that support it.
    """

    verbosity: Optional[Literal["low", "medium", "high"]] = None
    """Constrains the verbosity of the model's response.

    Lower values will result in more concise responses, while higher values will
    result in more verbose responses. Currently supported values are `low`,
    `medium`, and `high`.
    """


class ToolChoiceToolChoiceOptions(BaseModel):
    type: Literal["none", "auto", "required"]
    """Controls which (if any) tool is called by the model.

    `none` means the model will not call any tool and instead generates a message.

    `auto` means the model can pick between generating a message or calling one or
    more tools.

    `required` means the model must call one or more tools.

    Allowed values are:

    - `none`
    - `auto`
    - `required`
    """


class ToolChoiceAllowedTools(BaseModel):
    mode: Literal["auto", "required"]
    """Constrains the tools available to the model to a pre-defined set.

    `auto` allows the model to pick from among the allowed tools and generate a
    message.

    `required` requires the model to call one or more of the allowed tools.
    """

    tools: List[Dict[str, object]]
    """A list of tool definitions that the model should be allowed to call.

    For the Responses API, the list of tool definitions might look like:

    ```json
    [
      { "type": "function", "name": "get_weather" },
      { "type": "mcp", "server_label": "deepwiki" },
      { "type": "image_generation" }
    ]
    ```
    """

    type: Literal["allowed_tools"]
    """Allowed tool configuration type. Always `allowed_tools`."""


class ToolChoiceToolChoiceTypes(BaseModel):
    type: Literal[
        "file_search",
        "web_search_preview",
        "computer_use_preview",
        "web_search_preview_2025_03_11",
        "image_generation",
        "code_interpreter",
    ]
    """The type of hosted tool the model should to use.

    Learn more about
    [built-in tools](https://platform.openai.com/docs/guides/tools).

    Allowed values are:

    - `file_search`
    - `web_search_preview`
    - `computer_use_preview`
    - `code_interpreter`
    - `image_generation`
    """


class ToolChoiceFunction(BaseModel):
    name: str
    """The name of the function to call."""

    type: Literal["function"]
    """For function calling, the type is always `function`."""


class ToolChoiceMcp(BaseModel):
    server_label: str
    """The label of the MCP server to use."""

    type: Literal["mcp"]
    """For MCP tools, the type is always `mcp`."""

    name: Optional[str] = None
    """The name of the tool to call on the server."""


class ToolChoiceCustom(BaseModel):
    name: str
    """The name of the custom tool to call."""

    type: Literal["custom"]
    """For custom tool calling, the type is always `custom`."""


ToolChoice: TypeAlias = Annotated[
    Union[
        ToolChoiceToolChoiceOptions,
        ToolChoiceAllowedTools,
        ToolChoiceToolChoiceTypes,
        ToolChoiceFunction,
        ToolChoiceMcp,
        ToolChoiceCustom,
    ],
    PropertyInfo(discriminator="type"),
]


class ResponseProperties(BaseModel):
    background: Optional[bool] = None
    """
    Whether to run the model response in the background.
    [Learn more](https://platform.openai.com/docs/guides/background).
    """

    max_output_tokens: Optional[int] = None
    """
    An upper bound for the number of tokens that can be generated for a response,
    including visible output tokens and
    [reasoning tokens](https://platform.openai.com/docs/guides/reasoning).
    """

    max_tool_calls: Optional[int] = None
    """
    The maximum number of total calls to built-in tools that can be processed in a
    response. This maximum number applies across all built-in tool calls, not per
    individual tool. Any further attempts to call a tool by the model will be
    ignored.
    """

    model: Optional[
        Literal[
            "o1-pro",
            "o1-pro-2025-03-19",
            "o3-pro",
            "o3-pro-2025-06-10",
            "o3-deep-research",
            "o3-deep-research-2025-06-26",
            "o4-mini-deep-research",
            "o4-mini-deep-research-2025-06-26",
            "computer-use-preview",
            "computer-use-preview-2025-03-11",
            "gpt-5-codex",
            "gpt-5-pro",
            "gpt-5-pro-2025-10-06",
        ]
    ] = None
    """Model ID used to generate the response, like `gpt-4o` or `o3`.

    OpenAI offers a wide range of models with different capabilities, performance
    characteristics, and price points. Refer to the
    [model guide](https://platform.openai.com/docs/models) to browse and compare
    available models.
    """

    previous_response_id: Optional[str] = None
    """The unique ID of the previous response to the model.

    Use this to create multi-turn conversations. Learn more about
    [conversation state](https://platform.openai.com/docs/guides/conversation-state).
    Cannot be used in conjunction with `conversation`.
    """

    prompt: Optional[Prompt] = None
    """
    Reference to a prompt template and its variables.
    [Learn more](https://platform.openai.com/docs/guides/text?api-mode=responses#reusable-prompts).
    """

    reasoning: Optional[Reasoning] = None
    """**gpt-5 and o-series models only**

    Configuration options for
    [reasoning models](https://platform.openai.com/docs/guides/reasoning).
    """

    text: Optional[Text] = None
    """Configuration options for a text response from the model.

    Can be plain text or structured JSON data. Learn more:

    - [Text inputs and outputs](https://platform.openai.com/docs/guides/text)
    - [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
    """

    tool_choice: Optional[ToolChoice] = None
    """
    How the model should select which tool (or tools) to use when generating a
    response. See the `tools` parameter to see how to specify which tools the model
    can call.
    """

    tools: Optional[List[ResponseTool]] = None
    """An array of tools the model may call while generating a response.

    You can specify which tool to use by setting the `tool_choice` parameter.

    We support the following categories of tools:

    - **Built-in tools**: Tools that are provided by OpenAI that extend the model's
      capabilities, like
      [web search](https://platform.openai.com/docs/guides/tools-web-search) or
      [file search](https://platform.openai.com/docs/guides/tools-file-search).
      Learn more about
      [built-in tools](https://platform.openai.com/docs/guides/tools).
    - **MCP Tools**: Integrations with third-party systems via custom MCP servers or
      predefined connectors such as Google Drive and SharePoint. Learn more about
      [MCP Tools](https://platform.openai.com/docs/guides/tools-connectors-mcp).
    - **Function calls (custom tools)**: Functions that are defined by you, enabling
      the model to call your own code with strongly typed arguments and outputs.
      Learn more about
      [function calling](https://platform.openai.com/docs/guides/function-calling).
      You can also use custom tools to call your own code.
    """

    truncation: Optional[Literal["auto", "disabled"]] = None
    """The truncation strategy to use for the model response.

    - `auto`: If the input to this Response exceeds the model's context window size,
      the model will truncate the response to fit the context window by dropping
      items from the beginning of the conversation.
    - `disabled` (default): If the input size will exceed the context window size
      for a model, the request will fail with a 400 error.
    """
