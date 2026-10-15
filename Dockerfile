# Cloakix REST API with Arabic + English NER models baked in (runs offline).
#   docker build -t cloakix .
#   docker run -p 8000:8000 cloakix
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf-cache

WORKDIR /app
COPY pyproject.toml README.md LICENSE NOTICE ./
# The image redistributes the NER models, so their license texts ship with it.
COPY licenses ./licenses
COPY src ./src

# CPU-only PyTorch keeps the image small. Models are downloaded at build time.
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install ".[api,ner]" \
 && cloakix download-models \
 && useradd --system --uid 10001 cloakix

ENV HF_HUB_OFFLINE=1
USER cloakix
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["cloakix", "serve", "--host", "0.0.0.0", "--port", "8000"]
