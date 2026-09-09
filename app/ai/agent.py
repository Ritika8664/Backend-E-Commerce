from typing import Any

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from app.ai.tools import AgentContext, SUPPORT_TOOLS
from app.core.config import settings


SYSTEM_PROMPT = """You are a read-only customer support agent for this store.
Only answer questions about products, prices, stock, product availability, and the authenticated customer's order status.
Only answer using tool results. If a tool returns no match, say so honestly. Never invent prices, stock, or order status.
For every factual product or order question, call the relevant tool and answer only from its result.
Never invent products or order IDs.
Never claim to create, change, cancel, or pay for an order. Keep responses short and factual.
For requests outside this scope, briefly say you can only help with products and order status."""


model = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    google_api_key=settings.google_api_key,
    temperature=0,
    timeout=20,
    max_retries=2,
)

support_agent = create_agent(
    model=model,
    tools=SUPPORT_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    context_schema=AgentContext,
)


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        if parts:
            return "".join(parts)
    return str(content)


def run_support_agent(message: str, user_id: str) -> str:
    result = support_agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        context=AgentContext(user_id=user_id),
    )
    return _message_text(result["messages"][-1].content)
