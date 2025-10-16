import pathlib

from dotenv import load_dotenv
from freeplay_python_langgraph import FreeplayLangGraph
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

current_dir = pathlib.Path(__file__).parent
env_path = current_dir.parent.parent.parent / ".env"
load_dotenv(str(env_path))

# Ensure OPENAI_API_KEY is set in your environment (as per API Key Setup section)
# if not os.getenv("OPENAI_API_KEY"):
#     raise ValueError("OPENAI_API_KEY not set. Please set it before running.")

FreeplayLangGraph.initialize_observability(log_spans_to_console=True)


@tool
def search(query: str):
    """Simulates a search tool."""
    print(f"Searching for: {query}")
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy in San Francisco."
    return "It's 90 degrees and sunny elsewhere."


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


def call_model(state: MessagesState):
    messages = state["messages"]
    # Ensure your OPENAI_API_KEY has access to the model you choose
    model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo").bind_tools(tools)
    response = model.invoke(messages)
    return {"messages": [response]}


tools = [search]
tool_node = ToolNode(tools)

# Define a new graph
workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    "agent",
    should_continue,
    # We define a mapping that specifies if the last message has a tool call, then we call the tools node
    # Otherwise, we end the graph.
    # {
    #     "tools": "tools",
    #     END: END,
    # }, # Older versions of langgraph used a dict here.
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("tools", "agent")

# Initialize memory to persist state between graph runs
checkpointer = MemorySaver()

# Finally, we compile it!
# This compiles it into a LangChain Runnable, meaning you can use it as you would any other runnable
# We add the checkpointer here to LangGraph to persist state
app = workflow.compile(checkpointer=checkpointer)

# Run the LangGraph application
try:
    final_state = app.invoke(
        {
            "messages": [
                HumanMessage(content="what is the weather in sf? And what about LA?")
            ]
        },
        config={
            "configurable": {"thread_id": "my_conversation_42"}
        },  # thread_id for conversation tracking
    )
    if final_state and "messages" in final_state and final_state["messages"]:
        print(f"Final response: {final_state['messages'][-1].content}")
    else:
        print("No final message content found or final_state is not as expected.")
        print(f"Final state: {final_state}")
except Exception as e:
    print(f"Error invoking LangGraph app: {e}")
