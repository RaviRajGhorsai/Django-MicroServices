FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install netcat (nc) for waiting on Postgres
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
    
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies directly to system Python (NO .venv!)
RUN uv pip install --system -r pyproject.toml 

# Copy application code
COPY . /app


EXPOSE 8666

CMD ["python", "-u", "manage.py", "runserver", "0.0.0.0:8666"]  


