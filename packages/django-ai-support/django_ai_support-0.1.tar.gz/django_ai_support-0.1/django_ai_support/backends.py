from langchain_core.messages import HumanMessage

from .graphs import compiled_graph

def normal_chat_with_ai(user_message:str, session_id:str) -> str:

    config = {"configurable": {"thread_id": session_id}}

    messages = [
        HumanMessage(user_message)
    ]

    ai_response = compiled_graph.invoke({"messages": messages}, config=config)

    ai_response = ai_response["messages"][-1].content

    return ai_response

