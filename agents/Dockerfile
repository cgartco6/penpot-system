FROM python:3.11-slim
WORKDIR /app
RUN pip install openai redis
COPY . .
CMD ["python", "worker.py"]
