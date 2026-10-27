FROM apache/airflow:2.10.2-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    pandera>=0.18.0 \
    pydantic>=2.6.0 \
    requests>=2.31.0 \
    psycopg2-binary>=2.9.9
