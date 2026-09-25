import json
import os
from typing import TypedDict

import requests
from langgraph.graph import END, START, StateGraph

from support_assistant.models import AssistantResponse
from support_assistant.rag import PolicyRetriever


POLICY_KEYWORDS = [
    "delivery",
    "return",
    "refund",
    "membership",
    "tracking",
    "cancel",
    "gift card",
    "support hours",
]


STRUCTURED_PROMPT = """
ROLE:
You are a Zepto customer-support assistant.

CONTEXT:
Answer using only the Zepto policy context provided below.
{context}

TASK:
Answer the customer's question using the provided policy context.

FORMAT:
Return a JSON object with exactly these fields:
- answer: string
- sources: list of source document or chunk IDs
- confidence: float between 0 and 1

LENGTH:
Keep the answer concise and directly relevant to the customer's question.

NEGATIVE CONSTRAINT:
Do not answer using information that is not present in the provided context.
Do not invent or assume Zepto policies.

FEW-SHOT EXAMPLE:
Customer question:
"What is the delivery fee for orders below INR 149?"

Context:
"Standard delivery is free on orders over INR 149; orders below this threshold incur a flat INR 25 delivery fee."

Expected response:
{{
  "answer": "Orders below INR 149 incur a flat INR 25 delivery fee.",
  "sources": ["doc_01.txt"],
  "confidence": 1.0
}}

Customer question:
{query}
"""


retriever = PolicyRetriever()


class GraphState(TypedDict, total=False):
    query: str
    intent: str
    retrieved: list[dict]
    response: dict


def classify_intent(state: GraphState) -> GraphState:
    query = state["query"].lower()

    intent = "general_question"

    for keyword in POLICY_KEYWORDS:
        if keyword in query:
            intent = "policy_question"
            break

    return {
        **state,
        "intent": intent,
    }


def call_real_llm(prompt: str) -> dict:
    api_url = os.getenv("LLM_API_URL")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")

    if not api_url or not api_key or not model:
        raise RuntimeError(
            "MOCK_LLM=0 requires LLM_API_URL, LLM_API_KEY, and LLM_MODEL."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0,
    }

    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    parsed = json.loads(content)

    validated = AssistantResponse(**parsed)

    return validated.model_dump()


def generate_with_retry(prompt: str) -> dict:
    last_error = None

    for attempt in range(3):
        try:
            return call_real_llm(prompt)

        except Exception as exc:
            last_error = exc

            if attempt == 2:
                break

            prompt = (
                prompt
                + "\n\n"
                "IMPORTANT CORRECTION:\n"
                "Your previous response was invalid. "
                "Return ONLY valid JSON matching exactly this schema:\n"
                '{"answer": "string", "sources": ["string"], "confidence": 0.0}'
            )

    return {
        "answer": (
            "The assistant could not produce a valid structured response "
            "after three attempts."
        ),
        "sources": [],
        "confidence": 0.0,
        "error": str(last_error),
    }


def retrieve_and_answer(state: GraphState) -> GraphState:
    query = state["query"]

    retrieved = retriever.retrieve(query, top_k=3)

    sources = [item["source"] for item in retrieved]

    if os.getenv("MOCK_LLM", "1") == "1":
        if retrieved:
            top_chunk_snippet = retrieved[0]["text"][:200]
            answer = f"Based on the retrieved context: {top_chunk_snippet}"
            confidence = 1.0
        else:
            answer = (
                "Based on the retrieved context: "
                "No relevant policy context was found."
            )
            confidence = 0.0

        response = AssistantResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
        )

        return {
            **state,
            "retrieved": retrieved,
            "response": response.model_dump(),
        }

    context = "\n\n".join(
        f"[{item['source']}]\n{item['text']}" for item in retrieved
    )

    prompt = STRUCTURED_PROMPT.format(
        context=context,
        query=query,
    )

    response = generate_with_retry(prompt)

    return {
        **state,
        "retrieved": retrieved,
        "response": response,
    }


def direct_answer(state: GraphState) -> GraphState:
    if os.getenv("MOCK_LLM", "1") == "1":
        response = AssistantResponse(
            answer=(
                "I'm Zepto's support assistant. I can help with questions "
                "about delivery, returns, refunds, memberships, tracking, "
                "cancellations, gift cards, and support."
            ),
            sources=[],
            confidence=0.95,
        )

        return {
            **state,
            "response": response.model_dump(),
        }

    prompt = """
ROLE:
You are a Zepto customer-support assistant.

CONTEXT:
No policy retrieval was performed because this was classified as a general question.

TASK:
Answer the customer's general question helpfully without inventing specific Zepto policies.

FORMAT:
Return a JSON object with exactly these fields:
- answer: string
- sources: list of source document or chunk IDs
- confidence: float between 0 and 1

LENGTH:
Keep the answer concise.

NEGATIVE CONSTRAINT:
Do not invent specific Zepto policies or factual claims that are not supported by provided context.

FEW-SHOT EXAMPLE:
Customer question:
"Hello"

Expected response:
{
  "answer": "Hello! How can I help you?",
  "sources": [],
  "confidence": 1.0
}

Customer question:
""" + state["query"]

    response = generate_with_retry(prompt)

    return {
        **state,
        "response": response,
    }


def route_by_intent(state: GraphState) -> str:
    if state["intent"] == "policy_question":
        return "retrieve_and_answer"

    return "direct_answer"


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("retrieve_and_answer", retrieve_and_answer)
    workflow.add_node("direct_answer", direct_answer)

    workflow.add_edge(START, "classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "retrieve_and_answer": "retrieve_and_answer",
            "direct_answer": "direct_answer",
        },
    )

    workflow.add_edge("retrieve_and_answer", END)
    workflow.add_edge("direct_answer", END)

    return workflow.compile()