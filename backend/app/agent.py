import os

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from typing import Annotated
from typing_extensions import TypedDict


load_dotenv()

DEFAULT_MODEL = "gemini-3.6-flash"


class State(TypedDict):
    messages: Annotated[list, add_messages]


if not os.environ.get("GOOGLE_API_KEY"):
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. Copy backend/.env.example to backend/.env "
        "and add your key from https://aistudio.google.com/apikey"
    )

model = ChatGoogleGenerativeAI(
    model=os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
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