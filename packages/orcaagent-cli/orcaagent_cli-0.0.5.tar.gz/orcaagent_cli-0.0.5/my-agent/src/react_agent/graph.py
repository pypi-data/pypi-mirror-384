"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

import logging
from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field
from typing import List as TypingList

from react_agent.context import Context
from react_agent.prompts import TOOL_MATCHING_PROMPT, REFUSAL_RESPONSE_PROMPT
from react_agent.state import InputState, State
from react_agent.tools import get_tools
from react_agent.utils import load_chat_model, get_message_text

logger = logging.getLogger(__name__)

# Define the function that calls the model


async def tool_matcher(state: State, runtime: Runtime[Context]) -> Dict[str, List[str]]:
    """Match appropriate tools based on user query using LLM and update state.

    This function uses a language model to intelligently match user queries
    with available tools, updating the match_tools field in the state.
    """
    # Get the latest user message (assuming it's the last message in the conversation)
    if not state.messages:
        return {"match_tools": []}

    latest_message = state.messages[-1]
    if not hasattr(latest_message, "type") or latest_message.type != "human":
        return {"match_tools": []}

    # Get available tools
    available_tools = await get_tools()

    # Extract tool names and descriptions for matching
    tool_info = []
    for tool in available_tools:
        tool_name = getattr(tool, "name", str(tool))
        tool_desc = getattr(tool, "description", "")
        tool_info.append((tool_name, tool_desc))

    if not tool_info:
        return {"match_tools": []}

    # Create structured output schema for tool selection
    class ToolSelection(BaseModel):
        match_tools: TypingList[str] = Field(
            description="List of tool names that are most relevant to the user's query"
        )

    # Create tool selection prompt for LLM
    user_text = get_message_text(latest_message)
    tools_description = "\n".join([f"- {name}: {desc}" for name, desc in tool_info])

    tool_selection_prompt = TOOL_MATCHING_PROMPT.format(
        user_text=user_text, tools_description=tools_description
    )

    try:
        # Use LLM with structured output to select appropriate tools
        model = load_chat_model(runtime.context.model)
        structured_model = model.with_structured_output(ToolSelection)
        response = await structured_model.ainvoke(
            [{"role": "user", "content": tool_selection_prompt}]
        )

        # Validate that all selected tools exist in available tools
        available_tool_names = [name for name, _ in tool_info]
        validated_tools = [
            tool for tool in response.match_tools if tool in available_tool_names
        ]

        if validated_tools:
            return {"match_tools": validated_tools}
        else:
            # Fallback to all available tools if no valid tools selected
            return {"match_tools": []}

    except Exception as e:
        # Fallback to all available tools if LLM matching fails
        logger.warning(f"Tool matching failed: {e}")
        return {"match_tools": [tool_name for tool_name, _ in tool_info]}


async def refuse_answer(
    state: State, runtime: Runtime[Context]
) -> Dict[str, List[AIMessage]]:
    """Refuse to answer when no appropriate tools are available.

    This function uses LLM to generate a refusal message with detailed capability information.
    """
    # Get available tools information
    available_tools = await get_tools()
    tool_names = [getattr(tool, "name", str(tool)) for tool in available_tools]
    tool_descriptions = [getattr(tool, "description", "") for tool in available_tools]

    capability_info = "\n".join(
        [f"- {name}: {desc}" for name, desc in zip(tool_names, tool_descriptions)]
    )

    # Get the user's question from the latest message
    user_question = ""
    if state.messages:
        latest_message = state.messages[-1]
        if hasattr(latest_message, "type") and latest_message.type == "human":
            user_question = get_message_text(latest_message)

    # Create prompt for LLM to generate refusal message
    refusal_prompt = REFUSAL_RESPONSE_PROMPT.format(
        user_question=user_question, capability_info=capability_info
    )

    # Use LLM to generate refusal message
    model = load_chat_model(runtime.context.model)
    response = await model.ainvoke([{"role": "user", "content": refusal_prompt}])

    # Return the LLM-generated refusal message
    return {"messages": [response]}


async def call_model(
    state: State, runtime: Runtime[Context]
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        runtime (Runtime[Context]): Runtime configuration containing context.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    # Get available tools based on configuration
    available_tools = await get_tools()

    # Filter tools based on match_tools if specified in state
    if state.match_tools:
        # Filter available tools to only include matched tools
        matched_tool_names = set(state.match_tools)
        filtered_tools = []
        for tool in available_tools:
            tool_name = getattr(tool, "name", str(tool))
            if tool_name in matched_tool_names:
                filtered_tools.append(tool)
        available_tools = filtered_tools

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(runtime.context.model).bind_tools(available_tools)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = runtime.context.system_prompt.format(
        system_time=datetime.now(tz=UTC).isoformat()
    )

    # Get the model's response
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}


async def dynamic_tools_node(
    state: State, runtime: Runtime[Context]
) -> Dict[str, List[ToolMessage]]:
    """Execute tools dynamically based on configuration.

    This function gets the available tools based on the current configuration
    and executes the requested tool calls from the last message.
    """
    # Get available tools based on configuration
    available_tools = await get_tools()

    # Create a ToolNode with the available tools
    tool_node = ToolNode(available_tools)

    # Execute the tool node
    result = await tool_node.ainvoke(state)

    return cast(Dict[str, List[ToolMessage]], result)


# Define a new graph

builder = StateGraph(State, input_schema=InputState, context_schema=Context)

# Define the nodes
builder.add_node("tool_matcher", tool_matcher)
builder.add_node("refuse_answer", refuse_answer)
builder.add_node("call_model", call_model)
builder.add_node("tools", dynamic_tools_node)

# Set the entrypoint as `tool_matcher` to match tools first
builder.add_edge(START, "tool_matcher")


def route_tool_only_check(
    state: State, runtime: Runtime[Context]
) -> Literal["refuse_answer", "call_model"]:
    """Determine the next node based on tool-only check result.

    Args:
        state (State): The current state of the conversation.
        runtime (Runtime[Context]): Runtime configuration containing context.

    Returns:
        str: The name of the next node to call ("refuse_answer" or "call_model").
    """
    # Check if we should refuse to answer
    if runtime.context.tool_only and not state.match_tools:
        return "refuse_answer"

    # Otherwise, continue to call_model
    return "call_model"


# Add conditional edge from tool_only_check
builder.add_conditional_edges(
    "tool_matcher",
    route_tool_only_check,
)

# Add edge from refuse_answer to end
builder.add_edge("refuse_answer", END)


def route_model_output(state: State) -> Literal[END, "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )

    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return END
    # Otherwise we execute the requested actions
    return "tools"


# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    # After call_model finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Add a normal edge from `tools` to `call_model`
# This creates a cycle: after using tools, we always return to the model
builder.add_edge("tools", "call_model")

# Compile the builder into an executable graph
graph = builder.compile(name="ReAct Agent")
