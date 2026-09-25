from fastapi import FastAPI
from pydantic import BaseModel, Field

from support_assistant.graph import build_graph
from support_assistant.models import AssistantResponse


class AskRequest(BaseModel):
    query: str = Field(min_length=1)


app = FastAPI(
    title="Zepto Support Assistant",
    version="1.0.0",
)

graph = build_graph()


@app.post("/ask", response_model=AssistantResponse)
def ask(request: AskRequest) -> AssistantResponse:
    result = graph.invoke({"query": request.query})
    return AssistantResponse(**result["response"])