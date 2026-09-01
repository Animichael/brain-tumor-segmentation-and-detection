# Hugging Face Spaces (Docker SDK) image for the NeuroScan AI Flask app.
# HF's free CPU hardware gives 2 vCPU + 16 GB RAM, which is comfortably above
# this app's ~1 GB inference peak, so no model surgery is needed.
FROM python:3.11.9-slim

# libgl1 / libglib2.0-0: OpenCV (pulled in by ultralytics) needs these at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# HF Spaces runs containers as UID 1000 - create that user and give it /app.
RUN useradd -m -u 1000 appuser

ENV HOME=/home/appuser \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HF_HOME=/app/model-cache \
    YOLO_CONFIG_DIR=/app/model-cache/ultralytics \
    MPLCONFIGDIR=/app/model-cache/mpl

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download both model checkpoints at build time so they are baked into the
# image. Without this, the first prediction (and every wake-from-sleep) would
# re-download ~600 MB from the Hugging Face Hub onto the ephemeral disk.
RUN python -c "from app.ml.inference import _get_classifier, _get_segmenter; _get_classifier(); _get_segmenter()" && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 7860

CMD ["bash", "startup.sh"]
