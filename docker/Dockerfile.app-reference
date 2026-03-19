FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    viennarna muscle ncbi-blast+ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install uv && uv pip install --system -r requirements.txt

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
