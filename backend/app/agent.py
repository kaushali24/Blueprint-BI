from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from typing import Annotated
from typing_extensions import TypedDict


load_dotenv()


class State(TypedDict):
    messages: Annotated[list, add_messages]


model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
)


def chatbot(state: State):
    response = model.invoke(state["messages"])

    return {
        "messages": [response]
    }


builder = StateGraph(State)

builder.add_node("chatbot", chatbot)

builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

graph = builder.compile()