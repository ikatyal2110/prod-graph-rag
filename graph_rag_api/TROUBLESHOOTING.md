# Troubleshooting Guide

## numpy/pandas Binary Incompatibility Error

**Error:**
```
ValueError: numpy.dtype size changed, may indicate binary incompatibility. 
Expected 96 from C header, got 88 from PyObject
```

**Cause:**
The neo4j Python driver imports pandas as an optional dependency. If pandas was compiled against a different version of numpy than what's currently installed, you'll get this error.

**Solution:**
```bash
# Uninstall existing versions
pip uninstall -y numpy pandas

# Install compatible versions
pip install "numpy>=1.24.0,<2.0.0" "pandas>=2.0.0,<3.0.0"
```

**Verify the fix:**
```bash
python3 -c "import numpy; import pandas; import neo4j; print('All imports successful')"
```

## APOC Plugin Not Found

**Error:**
```
Neo4j error: Procedure call does not provide the required number of arguments
or: Unknown procedure 'apoc.path.expandConfig'
```

**Solution:**
APOC plugin must be installed in your Neo4j instance:
1. Download APOC from https://github.com/neo4j/apoc/releases
2. Copy the JAR file to Neo4j's `plugins` directory
3. Restart Neo4j

Or use Neo4j Desktop which includes APOC by default.

## Connection Refused

**Error:**
```
ServiceUnavailable: Failed to establish connection to Neo4j
```

**Solution:**
1. Verify Neo4j is running: `neo4j status`
2. Check connection URI in `.env`: `NEO4J_URI=bolt://localhost:7687`
3. Verify credentials: `NEO4J_USER` and `NEO4J_PASSWORD`
4. Check firewall settings

## Database Not Found

**Error:**
```
Database 'neo4j' does not exist
```

**Solution:**
1. Check database name in `.env`: `NEO4J_DB=neo4j`
2. List available databases in Neo4j Browser: `SHOW DATABASES`
3. Update `.env` with correct database name
