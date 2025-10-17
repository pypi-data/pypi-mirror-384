#!/bin/bash
set -e

echo "🚀 Starting custom Superset with Arc integration..."

# Register the custom dialect
echo "📦 Registering Arc dialect..."
python3 -c "
try:
    from arc_dialect import register_arc_dialect
    register_arc_dialect()
    print('✅ Arc dialect registered successfully')
except Exception as e:
    print(f'❌ Failed to register Arc dialect: {e}')
    # Continue anyway - the dialect might still work
"

echo "🔧 Initializing Superset database..."

# Initialize Superset database
superset db upgrade

echo "👤 Creating admin user..."

# Create admin user (will skip if already exists)
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@superset.com \
    --password admin || echo "Admin user already exists"

echo "🔄 Initializing Superset..."

# Initialize Superset
superset init

echo "🌐 Starting Superset web server..."

# Start Superset
exec superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger