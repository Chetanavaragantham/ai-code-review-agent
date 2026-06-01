FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by bandit/pylint subprocesses
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached layer — only rebuilds when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Gradio UI on 7860, FastAPI on 8000
EXPOSE 7860 8000

# Gradio app starts FastAPI in a background thread, then launches the UI
CMD ["python", "src/ui/app.py"]
