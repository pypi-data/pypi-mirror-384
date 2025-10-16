from __future__ import annotations

import asyncio
import warnings
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Generic,
    Literal,
    ParamSpec,
    Set,
    Type,
    TypeVar,
)

from railtracks.built_nodes.concrete.response import LLMResponse
from railtracks.exceptions import LLMError, NodeCreationError
from railtracks.exceptions.errors import NodeInvocationError
from railtracks.interaction._call import call
from railtracks.llm import (
    AssistantMessage,
    Message,
    MessageHistory,
    ModelBase,
    ToolCall,
    ToolMessage,
    ToolResponse,
    UserMessage,
)
from railtracks.llm.response import Response
from railtracks.nodes.nodes import Node
from railtracks.validation.node_creation.validation import check_connected_nodes
from railtracks.validation.node_invocation.validation import check_max_tool_calls

from ._llm_base import LLMBase

_T = TypeVar("_T", bound=LLMResponse)
_P = ParamSpec("_P")
_TStream = TypeVar("_TStream", Literal[True], Literal[False])


class OutputLessToolCallLLM(LLMBase[_T, _T, Literal[False]], ABC, Generic[_T]):
    """A base class that is a node which contains
     an LLm that can make tool calls. The tool calls will be returned
    as calls or if there is a response, the response will be returned as an output"""

    def __init_subclass__(cls):
        super().__init_subclass__()
        # 3. Check if the tool_nodes is not empty, special case for ToolCallLLM
        # We will not check for abstract classes
        has_abstract_methods = any(
            getattr(getattr(cls, name, None), "__isabstractmethod__", False)
            for name in dir(cls)
        )
        if not has_abstract_methods:
            if "tool_nodes" in cls.__dict__ and not has_abstract_methods:
                method = cls.__dict__["tool_nodes"]
                try:
                    # Try to call the method as a classmethod (typical case)
                    node_set = method.__func__(cls)
                except AttributeError:
                    # If that fails, call it as an instance method (for easy_wrapper init)
                    dummy = object.__new__(cls)
                    node_set = method(dummy)
                # Validate that the returned node_set is correct and contains only Node/function instances
                check_connected_nodes(node_set, Node)

    def __init__(
        self,
        user_input: MessageHistory | UserMessage | str | list[Message],
        llm: ModelBase[Literal[False]] | None = None,
        max_tool_calls: int | None = None,
    ):
        super().__init__(llm=llm, user_input=user_input)
        # Set max_tool_calls for non easy usage wrappers
        if not hasattr(self, "max_tool_calls"):
            # Check max_tool_calls (including warning for None)
            check_max_tool_calls(max_tool_calls)
            self.max_tool_calls = max_tool_calls

        # Warn user that two max_tool_calls are set and we will use the parameter
        else:
            if max_tool_calls is not None:
                warnings.warn(
                    "You have provided max_tool_calls as a parameter and as a class variable. We will use the parameter."
                )
                check_max_tool_calls(max_tool_calls)
                self.max_tool_calls = max_tool_calls
            else:
                check_max_tool_calls(self.max_tool_calls)

    @classmethod
    def name(cls) -> str:
        return "Tool Call LLM"

    @classmethod
    @abstractmethod
    def tool_nodes(cls) -> Set[Type[Node]]: ...

    def create_node(self, tool_name: str, arguments: Dict[str, Any]) -> Node:
        """
        A function which creates a new instance of a node Class from a tool name and arguments.

        This function may be overwritten to fit the needs of the given node as needed.
        """
        node = [x for x in self.tool_nodes() if x.tool_info().name == tool_name]
        if node == []:
            raise LLMError(
                reason=f" Error creating a node from tool {tool_name}. The tool_name given by the LLM doesn't match any of the tool names in the connected nodes.",
                message_history=self.message_hist,
            )
        if len(node) > 1:
            raise NodeCreationError(
                message=f"Tool {tool_name} has multiple nodes, this is not allowed. Current Node include {[x.tool_info().name for x in self.tool_nodes()]}",
                notes=["Please check the tool names in the connected nodes."],
            )
        return node[0].prepare_tool(arguments)

    def tools(self):
        return [x.tool_info() for x in self.tool_nodes()]

    async def _on_max_tool_calls_exceeded(self):
        """force a final response. This function will add it to the message history and return the message. This function shoudld only be called on non streaming llms."""
        response = await asyncio.to_thread(
            self.llm_model.chat,
            self.message_hist,
        )

        if not isinstance(response.message, AssistantMessage):
            raise LLMError(
                reason=f"The LLM returned an unexpected message type. Expected AssistantMessage but got {type(response.message)}",
                message_history=self.message_hist,
            )

        return response.message

    async def _handle_tool_calls(self) -> tuple[bool, Message | None]:
        """
        Handles the execution of tool calls for the node, including LLM interaction and message history updates.

        This method:
        - Checks if the maximum number of tool calls has been reached and triggers a final response if so.
        - Interacts with the LLM to get a tool call request or final answers.
        - Executes a tool call and appends the results to the message history.
        - Handles malformed LLM responses and raises errors as needed.

        Returns:
            bool: True if more tool calls are expected (the tool call loop should continue),
                  False if the tool call process is finished and a final answer is available.

        Raises:
            LLMError: If the LLM returns an unexpected message type or the message is malformed.
        """
        current_tool_calls = len(
            [m for m in self.message_hist if isinstance(m, ToolMessage)]
        )
        allowed_tool_calls = (
            self.max_tool_calls - current_tool_calls
            if self.max_tool_calls is not None
            else None
        )
        if allowed_tool_calls is not None and allowed_tool_calls <= 0:
            message = await self._on_max_tool_calls_exceeded()
            return False, message

        # collect the response from the llm model
        response = await asyncio.to_thread(
            self.llm_model.chat_with_tools, self.message_hist, tools=self.tools()
        )

        response: Response

        if not isinstance(response.message, AssistantMessage):
            raise LLMError(
                reason=f"The LLM returned an unexpected message type. Expected AssistantMessage but got {type(response.message)}",
                message_history=self.message_hist,
            )

        return await self._handle_response(response.message, allowed_tool_calls)

    async def _handle_response(
        self, message: AssistantMessage, allowed_tool_calls: int | None
    ):
        # if the returned item is a list then it is a list of tool calls
        if isinstance(message.content, list):
            assert all(isinstance(x, ToolCall) for x in message.content)

            tool_calls = message.content
            if allowed_tool_calls is not None and len(tool_calls) > allowed_tool_calls:
                tool_calls = tool_calls[:allowed_tool_calls]

            # append the requested tool calls assistant message, once the tool calls have been verified and truncated (if needed)
            self.message_hist.append(AssistantMessage(content=tool_calls))

            tool_messages = await self._call_tools(tool_calls)
            for t_m in tool_messages:
                self.message_hist.append(t_m)

            return True, None
        else:
            # this means the tool call is finished
            self.message_hist.append(message)
            return False, message

    async def _call_tools(self, tool_calls: list[ToolCall]) -> list[ToolMessage]:
        contracts = []
        for t_c in tool_calls:
            contract = call(
                self.create_node,
                t_c.name,
                t_c.arguments,
            )
            contracts.append(contract)

        tool_responses = await asyncio.gather(*contracts, return_exceptions=True)
        tool_responses = [
            (
                x
                if not isinstance(x, Exception)
                else f"There was an error running the tool: \n Exception message: {x} "
            )
            for x in tool_responses
        ]
        tool_ids = [x.identifier for x in tool_calls]
        tool_names = [x.name for x in tool_calls]

        tool_messages = []

        for r_id, r_name, resp in zip(
            tool_ids,
            tool_names,
            tool_responses,
        ):
            tool_messages.append(
                ToolMessage(
                    ToolResponse(identifier=r_id, result=str(resp), name=r_name)
                )
            )

        return tool_messages

    async def invoke(self):
        if self.llm_model._stream:
            raise NodeInvocationError(
                "Streaming is not supported in ToolCallLLM nodes",
                notes=[
                    "See issue #756 for details.",
                ],
            )

        message = None
        while True:
            still_tool_calls, message = await self._handle_tool_calls()
            if not still_tool_calls:
                break

        return self.return_output(message)
