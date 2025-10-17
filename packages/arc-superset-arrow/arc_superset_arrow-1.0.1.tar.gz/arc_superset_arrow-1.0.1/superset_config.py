"""
Superset configuration for Arc integration
"""
import os

# Secret key for sessions - change in production!
SECRET_KEY = os.getenv('SUPERSET_SECRET_KEY', 'your-secret-key-here-change-in-production')

# Database configuration for Superset metadata
SQLALCHEMY_DATABASE_URI = 'sqlite:////app/superset_home/superset.db'

# Enable feature flags
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_RBAC": True,
    "ALERTS_REPORTS": False,  # Disable for simplicity
}

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
}

# Custom CSS
EXTRA_CATEGORICAL_COLOR_SCHEMES = []

# Authentication
from superset.security import SupersetSecurityManager
AUTH_TYPE = 1  # AUTH_DB = 1 for database authentication

# CORS settings - disabled for simplicity
# ENABLE_CORS = True

# Logging
LOGGER_LEVEL = 'INFO'

# Arc dialect registration
# Manual registration required because SQLAlchemy doesn't always discover entry_points
# in containerized environments
try:
    import arc_dialect
    from sqlalchemy.dialects import registry

    # Register the dialect manually
    registry.register("arc", "arc_dialect", "ArcDialect")
    registry.register("arc.api", "arc_dialect", "ArcDialect")

    print("✅ Arc dialect registered successfully")
except ImportError as e:
    print(f"⚠️  Arc dialect import failed: {e}")
except Exception as e:
    print(f"⚠️  Arc dialect registration warning: {e}")

# Example connection string for Arc:
# arc://YOUR_API_KEY@arc-api:8000/default
# arc://YOUR_API_KEY@localhost:8000/default

# Optional: Set row limit for queries
ROW_LIMIT = 10000
SQL_MAX_ROW = 50000

# Optional: Enable query cost estimation
QUERY_COST_FORMATTERS_BY_ENGINE = {}

# Security settings
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_TIME_LIMIT = None

# Webserver configuration
WEBSERVER_THREADS = 8
WEBSERVER_TIMEOUT = 60

# Optional: Custom footer
CUSTOM_SECURITY_MANAGER = None

print("Superset configuration loaded for Arc integration")