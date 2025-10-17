# Arc + Apache Superset Integration (Arrow Edition)

This is the **Apache Arrow-powered** SQLAlchemy dialect for integrating Apache Superset with the Arc time-series data warehouse. This version uses Arrow IPC for dramatically faster query performance compared to JSON-based queries.

## Features

- ✅ **Custom SQLAlchemy dialect** for Arc API with **Apache Arrow IPC**
- ✅ **28-75% faster queries** compared to JSON format (depending on dataset size)
- ✅ **Lower memory overhead** with zero-copy Arrow buffers
- ✅ **Authentication** via API keys (set and forget)
- ✅ **Full SQL support** for dashboard creation
- ✅ **Auto-discovery** of Arc tables and measurements
- ✅ **Docker Compose integration**

## Why Arrow?

This dialect uses Apache Arrow IPC (Inter-Process Communication) instead of JSON for query results, providing:

- **Performance**: 28-75% faster query execution
- **Efficiency**: Zero-copy data transfer with columnar format
- **Type Safety**: Preserve native data types (timestamps, integers, floats)
- **Scalability**: Better performance for large result sets

## Quick Start

### Option 1: Install in Existing Superset

```bash
# Install the Arc Arrow dialect package
pip install arc-superset-arrow

# Restart Superset
superset run -h 0.0.0.0 -p 8088
```

### Option 2: Docker Image (Recommended for Production)

Use the included Dockerfile to build a Superset image with Arc pre-installed:

```bash
# Clone the repository
git clone https://github.com/basekick-labs/arc-superset-arrow.git
cd arc-superset-arrow

# Build the image
docker build -t superset-arc:latest .

# Run Superset with Arc support
docker run -d \
  -p 8088:8088 \
  -v superset_home:/app/superset_home \
  --name superset-arc \
  superset-arc:latest

# Check logs
docker logs -f superset-arc
```

The Dockerfile includes:
- Arc dialect pre-installed
- Custom Superset configuration
- Automatic database initialization
- Default admin user (admin/admin - **change in production!**)

### Connect to Arc

1. **Access Superset**: http://localhost:8088 (admin/admin)

2. **Create Arc Connection**:
   - Go to **Settings** → **Database Connections**
   - Click **+ Database**
   - Select **Other** as database type
   - Use this connection string:
     ```
     arc://YOUR_API_KEY@arc-api:8000/default
     ```

3. **Replace `YOUR_API_KEY`** with your Arc token (see below)

## Getting Your API Key

Arc creates an initial admin token on first startup. Check the logs:

```bash
# Docker
docker logs arc-api | grep "Initial admin token"

# Native/systemd
journalctl -u arc | grep "Initial admin token"
```

Or create a new token using the Arc CLI or Python:

```bash
# Using Python directly
DB_PATH="./data/arc.db" python3 -c "
from api.auth import AuthManager
auth = AuthManager(db_path='./data/arc.db')
token = auth.create_token('superset-integration', description='Superset dashboard access')
print(f'Token: {token}')
"
```

Save the returned token - it's only shown once!

## Multi-Database Support

Arc supports multiple databases (namespaces) within a single instance. In Superset, databases are exposed as **schemas**:

### Database Structure
```
Schema: default
  ├── cpu (CPU metrics)
  ├── mem (Memory metrics)
  └── disk (Disk metrics)

Schema: production
  ├── cpu
  ├── mem
  └── disk

Schema: staging
  ├── cpu
  ├── mem
  └── disk
```

### Using Databases in Superset

1. **View All Databases (Schemas)**:
   - When creating a dataset, select the schema (database) from the dropdown
   - Each database appears as a separate schema in Superset

2. **Query Specific Database**:
   ```sql
   -- Query default database
   SELECT * FROM cpu WHERE timestamp > NOW() - INTERVAL 1 HOUR

   -- Query specific database
   SELECT * FROM production.cpu WHERE timestamp > NOW() - INTERVAL 1 HOUR

   -- Cross-database joins
   SELECT
       p.timestamp,
       p.usage_idle as prod_cpu,
       s.usage_idle as staging_cpu
   FROM production.cpu p
   JOIN staging.cpu s ON p.timestamp = s.timestamp
   WHERE p.timestamp > NOW() - INTERVAL 1 HOUR
   ```

### Available Commands

```sql
-- List all databases
SHOW DATABASES;

-- List all tables in current database
SHOW TABLES;
```

## Available Tables

The dialect auto-discovers all tables using `SHOW TABLES`. Common examples:

- `cpu` - CPU metrics
- `mem` - Memory metrics
- `disk` - Disk metrics
- Any custom measurements you've ingested

## Example Queries

### Basic Queries

```sql
-- Recent CPU metrics (use 'timestamp' column)
SELECT timestamp, host, usage_idle, usage_user
FROM cpu
WHERE timestamp > NOW() - INTERVAL 1 HOUR
ORDER BY timestamp DESC
LIMIT 100;

-- Average CPU usage by host
SELECT host, AVG(usage_idle) as avg_idle
FROM cpu
WHERE timestamp > NOW() - INTERVAL 24 HOUR
GROUP BY host
ORDER BY avg_idle DESC;
```

### Time-Series Aggregation

Arc supports DuckDB's powerful time functions:

```sql
-- Time bucket aggregation (5-minute intervals)
SELECT
    time_bucket(INTERVAL '5 minutes', timestamp) as bucket,
    host,
    AVG(usage_idle) as avg_idle,
    MAX(usage_user) as max_user
FROM cpu
WHERE timestamp > NOW() - INTERVAL 6 HOUR
GROUP BY bucket, host
ORDER BY bucket DESC;

-- Daily aggregation with DATE_TRUNC
SELECT
    DATE_TRUNC('day', timestamp) as day,
    host,
    AVG(usage_idle) as avg_cpu_idle,
    COUNT(*) as samples
FROM cpu
WHERE timestamp > NOW() - INTERVAL 7 DAY
GROUP BY day, host
ORDER BY day DESC;
```

### Join Queries

Join multiple measurements for correlated analysis:

```sql
-- Correlate CPU and Memory usage
SELECT
    c.timestamp,
    c.host,
    c.usage_idle as cpu_idle,
    m.used_percent as mem_used
FROM cpu c
JOIN mem m ON c.timestamp = m.timestamp AND c.host = m.host
WHERE c.timestamp > NOW() - INTERVAL 10 MINUTE
ORDER BY c.timestamp DESC
LIMIT 1000;
```

### Window Functions

```sql
-- Moving average over last 6 data points
SELECT
    timestamp,
    host,
    usage_idle,
    AVG(usage_idle) OVER (
        PARTITION BY host
        ORDER BY timestamp
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    ) as moving_avg
FROM cpu
ORDER BY timestamp DESC
LIMIT 100;
```

## Architecture

```
Superset → Arrow Dialect → Arrow IPC → Arc API → DuckDB → Parquet Files → MinIO/S3
    ↓           ↓            ↓           ↓         ↓           ↓              ↓
Dashboard    SQL Query   Zero-Copy   API Key    Query    Columnar    Compacted    Object
                         Buffers      Auth      Engine    Storage      Files      Storage
```

**Arrow IPC Flow:**
1. Superset sends SQL query via dialect
2. Arc executes query with DuckDB
3. Results serialized to Arrow IPC format (columnar, zero-copy)
4. Dialect deserializes Arrow buffers directly to Python objects
5. 28-75% faster than JSON serialization/deserialization

## Connection String Format

```
arc://API_KEY@HOST:PORT/DATABASE
```

**Examples:**
```
# Local development
arc://your-api-key@localhost:8000/default

# Docker Compose
arc://your-api-key@arc-api:8000/default

# Remote server
arc://your-api-key@arc.example.com:8000/default
```

## Troubleshooting

### Connection Issues
- **Verify your API key is correct**: Test with `curl -H "Authorization: Bearer YOUR_KEY" http://host:8000/health`
- **Check that Arc API is running**: `docker logs arc-api` or check systemd logs
- **Ensure network connectivity**: Superset and Arc must be on the same network or accessible via hostname

### Query Issues
- **Check Arc API logs**: `docker logs arc-api` to see query execution
- **Verify table names exist**: Use `SHOW TABLES` in Arc to list available measurements
- **Use `LIMIT` clauses**: Always limit large queries for performance
- **Add time filters**: Time-series queries should filter by time range

### Performance Tips

- **Always use `LIMIT`** for exploratory queries to avoid loading millions of rows
- **Add time range filters** for time-series data: `WHERE timestamp > NOW() - INTERVAL 1 HOUR`
- **Use column names correctly**: Arc stores timestamps in `timestamp` column (not `time`)
- **Leverage query cache**: Arc caches query results for 60 seconds by default
- **Use compacted partitions**: Arc automatically merges small files for 10-50x faster queries
- **Optimize aggregations**: Use `time_bucket()` for time-series bucketing instead of `DATE_TRUNC` when possible
- **Partition filtering**: Include `host` or other tag filters to reduce data scanned

## Package Contents

- `arc_dialect.py` - Custom SQLAlchemy dialect for Arc API
- `setup.py` - PyPI package configuration
- `MANIFEST.in` - Package file manifest
- `README.md` - This documentation
- `PUBLISHING.md` - Publishing guide for PyPI

## Security Notes

- API keys are stored encrypted in Superset's database
- All queries go through Arc's authentication system
- **Change the default Superset admin password in production**
- **Set a strong `SUPERSET_SECRET_KEY` in production**
- Use HTTPS for production deployments

## Advanced Features

### Schema Support

Arc supports multiple schemas/databases:

```sql
-- Query specific database
SELECT * FROM my_database.cpu LIMIT 10;

-- List all databases
SHOW DATABASES;
```

### Advanced DuckDB Features

Arc leverages DuckDB's full SQL capabilities:

```sql
-- List all measurements (tables)
SHOW TABLES;

-- Get table schema
DESCRIBE cpu;

-- Count records by measurement
SELECT COUNT(*) as total_records FROM cpu;

-- Complex aggregations with FILTER
SELECT
    host,
    COUNT(*) FILTER (WHERE usage_idle > 90) as idle_count,
    COUNT(*) FILTER (WHERE usage_idle < 50) as busy_count,
    AVG(usage_idle) as avg_idle
FROM cpu
WHERE timestamp > NOW() - INTERVAL 1 HOUR
GROUP BY host;
```

## Development

To modify or extend the dialect:

1. Clone the repository:
   ```bash
   git clone https://github.com/basekick-labs/arc-superset-arrow.git
   cd arc-superset-arrow
   ```

2. Edit `arc_dialect.py`

3. Install locally for testing:
   ```bash
   pip install -e .
   ```

4. Test with Superset:
   ```bash
   superset run -h 0.0.0.0 -p 8088
   ```

5. Submit a PR if you add improvements!

## License

Same license as Arc Core (AGPL-3.0)
