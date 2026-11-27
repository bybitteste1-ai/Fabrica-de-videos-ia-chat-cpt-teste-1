FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip blender ffmpeg ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/fabrica
COPY . /workspace/fabrica
CMD ["python3", "producer.py", "list"]
