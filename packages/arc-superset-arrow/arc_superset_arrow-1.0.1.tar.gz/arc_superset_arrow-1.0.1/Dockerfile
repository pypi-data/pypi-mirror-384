# Superset with Arc dialect pre-installed
FROM apache/superset:latest

USER root

# Install Arc Arrow dialect dependencies
RUN pip install --no-cache-dir "SQLAlchemy>=1.4.0,<3.0.0" "requests>=2.31.0" "pyarrow>=21.0.0"

# Copy Arc Arrow dialect file directly to venv
COPY arc_dialect.py /app/.venv/lib/python3.10/site-packages/arc_dialect.py

# Alternative: Install from PyPI once published:
# RUN pip install --no-cache-dir arc-superset-arrow>=1.0.0

# Copy custom Superset configuration
COPY superset_config.py /app/superset_config.py
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER superset

ENTRYPOINT ["/app/entrypoint.sh"]