# Conversations

Types:

```python
from agentlin_client.types import ConversationDeleteResponse
```

Methods:

- <code title="post /conversations">client.conversations.<a href="./src/agentlin_client/resources/conversations/conversations.py">create</a>(\*\*<a href="src/agentlin_client/types/conversation_create_params.py">params</a>) -> <a href="./src/agentlin_client/types/conversations/conversation_resource.py">ConversationResource</a></code>
- <code title="get /conversations/{conversation_id}">client.conversations.<a href="./src/agentlin_client/resources/conversations/conversations.py">retrieve</a>(conversation_id) -> <a href="./src/agentlin_client/types/conversations/conversation_resource.py">ConversationResource</a></code>
- <code title="post /conversations/{conversation_id}">client.conversations.<a href="./src/agentlin_client/resources/conversations/conversations.py">update</a>(conversation_id, \*\*<a href="src/agentlin_client/types/conversation_update_params.py">params</a>) -> <a href="./src/agentlin_client/types/conversations/conversation_resource.py">ConversationResource</a></code>
- <code title="delete /conversations/{conversation_id}">client.conversations.<a href="./src/agentlin_client/resources/conversations/conversations.py">delete</a>(conversation_id) -> <a href="./src/agentlin_client/types/conversation_delete_response.py">ConversationDeleteResponse</a></code>

## Items

Types:

```python
from agentlin_client.types.conversations import (
    CodeInterpreterToolCall,
    ComputerScreenshotImage,
    ComputerToolCall,
    ComputerToolCallOutputResource,
    ComputerToolCallSafetyCheck,
    ConversationItem,
    ConversationItemList,
    ConversationResource,
    CustomToolCall,
    CustomToolCallOutput,
    EasyInputMessage,
    FileSearchToolCall,
    FunctionAndCustomToolCallOutput,
    FunctionCallItemStatus,
    FunctionToolCall,
    FunctionToolCallOutputResource,
    FunctionToolCallResource,
    ImageGenToolCall,
    Includable,
    InputAudio,
    InputContent,
    InputFileContent,
    InputImageContent,
    InputItem,
    InputMessage,
    InputTextContent,
    LocalShellToolCall,
    LocalShellToolCallOutput,
    McpApprovalRequest,
    McpApprovalResponseResource,
    McpListTools,
    McpToolCall,
    OutputMessage,
    OutputTextContent,
    ReasoningItem,
    ReasoningTextContent,
    RefusalContent,
    WebSearchToolCall,
)
```

Methods:

- <code title="post /conversations/{conversation_id}/items">client.conversations.items.<a href="./src/agentlin_client/resources/conversations/items.py">create</a>(conversation_id, \*\*<a href="src/agentlin_client/types/conversations/item_create_params.py">params</a>) -> <a href="./src/agentlin_client/types/conversations/conversation_item_list.py">ConversationItemList</a></code>
- <code title="get /conversations/{conversation_id}/items/{item_id}">client.conversations.items.<a href="./src/agentlin_client/resources/conversations/items.py">retrieve</a>(item_id, \*, conversation_id, \*\*<a href="src/agentlin_client/types/conversations/item_retrieve_params.py">params</a>) -> <a href="./src/agentlin_client/types/conversations/conversation_item.py">ConversationItem</a></code>
- <code title="get /conversations/{conversation_id}/items">client.conversations.items.<a href="./src/agentlin_client/resources/conversations/items.py">list</a>(conversation_id, \*\*<a href="src/agentlin_client/types/conversations/item_list_params.py">params</a>) -> <a href="./src/agentlin_client/types/conversations/conversation_item_list.py">ConversationItemList</a></code>
- <code title="delete /conversations/{conversation_id}/items/{item_id}">client.conversations.items.<a href="./src/agentlin_client/resources/conversations/items.py">delete</a>(item_id, \*, conversation_id) -> <a href="./src/agentlin_client/types/conversations/conversation_resource.py">ConversationResource</a></code>

# Responses

Types:

```python
from agentlin_client.types import (
    McpToolFilter,
    ModelResponsePropertiesStandard,
    Response,
    ResponseProperties,
    ResponseTool,
    TextResponseFormatConfiguration,
    ResponseListInputItemsResponse,
)
```

Methods:

- <code title="post /responses">client.responses.<a href="./src/agentlin_client/resources/responses.py">create</a>(\*\*<a href="src/agentlin_client/types/response_create_params.py">params</a>) -> <a href="./src/agentlin_client/types/response.py">Response</a></code>
- <code title="get /responses/{response_id}">client.responses.<a href="./src/agentlin_client/resources/responses.py">retrieve</a>(response_id, \*\*<a href="src/agentlin_client/types/response_retrieve_params.py">params</a>) -> <a href="./src/agentlin_client/types/response.py">Response</a></code>
- <code title="delete /responses/{response_id}">client.responses.<a href="./src/agentlin_client/resources/responses.py">delete</a>(response_id) -> None</code>
- <code title="post /responses/{response_id}/cancel">client.responses.<a href="./src/agentlin_client/resources/responses.py">cancel</a>(response_id) -> <a href="./src/agentlin_client/types/response.py">Response</a></code>
- <code title="get /responses/{response_id}/input_items">client.responses.<a href="./src/agentlin_client/resources/responses.py">list_input_items</a>(response_id, \*\*<a href="src/agentlin_client/types/response_list_input_items_params.py">params</a>) -> <a href="./src/agentlin_client/types/response_list_input_items_response.py">ResponseListInputItemsResponse</a></code>
