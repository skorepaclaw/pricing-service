FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8002
ENV SLOW_MODE=true
ENV SLOW_DELAY=4.5
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
