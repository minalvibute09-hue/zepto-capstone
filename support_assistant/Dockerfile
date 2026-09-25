FROM python:3.12-slim

WORKDIR /app

COPY support_assistant/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY support_assistant/ .

ENV MOCK_LLM=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]