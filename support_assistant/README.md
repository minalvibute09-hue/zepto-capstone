# Zepto Support Assistant

## Overview

This module implements a policy-grounded Zepto customer-support assistant using:

- Sentence Transformers (`all-MiniLM-L6-v2`) for embeddings
- ChromaDB for vector storage and cosine-similarity retrieval
- LangGraph for intent routing and answer generation
- Pydantic for structured response validation
- FastAPI for the `/ask` HTTP API
- Docker for local containerized execution

The system uses a deterministic mock mode by default, so no paid LLM service is required.

---

## Architecture

```text
8 Zepto policy documents
        |
        v
Document loading
        |
        v
all-MiniLM-L6-v2 embeddings
        |
        v
ChromaDB vector collection
        |
        v
User query
        |
        v
LangGraph StateGraph
        |
        +------------------------------+
        |                              |
        v                              v
classify_intent                 classify_intent
policy_question                 general_question
        |                              |
        v                              v
retrieve_and_answer             direct_answer
        |                              |
        v                              v
Top-3 ChromaDB retrieval        Fixed mock response
        |                              |
        +--------------+---------------+
                       |
                       v
              Pydantic response
                       |
                       v
                  FastAPI /ask
