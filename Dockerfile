FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY generator/ generator/
COPY pipeline/ pipeline/
CMD ["python", "pipeline/consumer_snowflake.py"]
