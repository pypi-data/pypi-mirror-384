# Superset with Arc dialect pre-installed
FROM apache/superset:latest

USER root

# Install Arc dialect
# PyPI installation goes to system Python, not the venv, so we copy directly
COPY arc_dialect.py /app/.venv/lib/python3.10/site-packages/arc_dialect.py
RUN pip install --no-cache-dir "SQLAlchemy>=1.4.0,<3.0.0" "requests>=2.31.0"

# Alternative: Install from PyPI (but goes to system Python, not venv):
# RUN pip install --no-cache-dir arc-superset-dialect>=1.0.2

# Copy custom Superset configuration
COPY superset_config.py /app/superset_config.py
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER superset

ENTRYPOINT ["/app/entrypoint.sh"]