from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .settings import api_settings

if api_settings.SYSTEM_PROMPT:
    system_prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", api_settings.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

else:
    system_prompt_template = None

def chat_node(state:MessagesState):
    
    if system_prompt_template:
        messages = system_prompt_template.invoke(state)
    else:
        messages = state["messages"]

    response = api_settings.LLM_MODEL.invoke(messages)

    return {"messages": response}


# TODO: maybe we need update this graph if some tools add or removed
# by these functions: append_tools, remove_tools
# check it and if this is true, handle it 
tool_node = ToolNode(api_settings.TOOLS)

memory = MemorySaver()

graph = StateGraph(MessagesState)
graph.add_node("chat", chat_node)
graph.add_node("tools", tool_node)

graph.add_conditional_edges(
    "chat",
    tools_condition
)

graph.add_edge(START, "chat")
graph.add_edge("tools", "chat")
graph.add_edge("chat", END)

compiled_graph = graph.compile(checkpointer=memory)

