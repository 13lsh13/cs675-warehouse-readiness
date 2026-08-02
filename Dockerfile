FROM apache/spark:3.5.1-python3
USER root
WORKDIR /opt/project
COPY src/readiness_pipeline.py /opt/project/src/readiness_pipeline.py
COPY data/sample /opt/project/data/sample
RUN mkdir -p /opt/project/data/processed && chown -R spark:spark /opt/project
USER spark
ENTRYPOINT ["/opt/spark/bin/spark-submit", "src/readiness_pipeline.py", "--input", "data/sample", "--output", "data/processed", "--as-of-date", "2026-08-01"]
