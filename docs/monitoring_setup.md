# Database Monitoring Setup

## Status
As of April 15, 2025, the following components have been successfully set up:

✅ Signoz monitoring stack (ClickHouse, query service, frontend, OTLP collector)  
✅ Database connection and operations  
✅ Metrics collection and visualization  
✅ Trace collection and visualization  
✅ Custom metrics for database performance  

To access the dashboard, visit http://localhost:3301

## Overview
This document describes the monitoring setup for the database system, including Signoz monitoring, performance analysis, and alerting configuration.

## Components

### 1. Signoz Monitoring Stack
- **Frontend**: Accessible at http://localhost:3301
- **API Token**: Configured in `.env` file
- **OpenTelemetry Collector**: Running on port 4317 (gRPC) and 4318 (HTTP)
- **ClickHouse**: Used for metrics storage

### 2. Monitoring Dashboard
The dashboard includes the following metrics:
- Query Latency (95th percentile)
- Active Connections
- Query Throughput
- Slow Query Rate

### 3. Alerts Configuration
The following alerts are configured:
1. **High Query Latency**
   - Condition: 95th percentile > 1 second
   - Duration: 5 minutes
   - Severity: Critical

2. **Connection Pool Exhaustion**
   - Condition: Connected threads > 100
   - Duration: 5 minutes
   - Severity: Warning

3. **Slow Query Rate**
   - Condition: > 10 slow queries per minute
   - Duration: 5 minutes
   - Severity: Warning

## Performance Analysis Tools

### 1. Slow Query Analysis
The `analyze_slow_queries.py` script provides:
- Total slow queries in last 24h
- Average and maximum query times
- Top 10 slowest queries by database
- Index usage statistics

### 2. Index Optimization
The script identifies:
- Tables without primary keys
- Potential missing indexes
- Most used indexes

## Usage

### Setting up Monitoring
1. Start the Signoz stack:
   ```bash
   docker-compose up -d
   ```

2. Create dashboard and alerts:
   ```bash
   python3 scripts/setup_signoz_dashboard.py
   ```

3. Run performance analysis:
   ```bash
   python3 scripts/analyze_slow_queries.py
   ```

### Accessing Monitoring
- Dashboard: http://localhost:3301
- API Endpoint: http://localhost:3301/api
- API Token: See `.env` file

## Troubleshooting

### Common Issues
1. **Signoz not accessible**
   - Check if Docker containers are running: `docker ps`
   - Verify ports are not blocked
   - Check container logs: `docker-compose logs`

2. **High Query Latency**
   - Run slow query analysis
   - Check for missing indexes
   - Review query execution plans

3. **Connection Issues**
   - Verify database credentials
   - Check connection pool settings
   - Monitor active connections

### Log Files
- Slow query log: `/var/lib/mysql/slow.log`
- Error log: `/var/lib/mysql/error.log`
- Signoz logs: Available in Docker container logs

## Maintenance

### Regular Tasks
1. Review slow query logs weekly
2. Analyze index usage monthly
3. Update monitoring thresholds as needed
4. Backup monitoring data regularly

### Updating Configuration
1. Edit `docker-compose.yml` for stack changes
2. Update `otel-collector-config.yaml` for collector settings
3. Modify alert thresholds in `setup_signoz_dashboard.py`

## Security Considerations
1. Keep API tokens secure
2. Regularly rotate credentials
3. Monitor access logs
4. Implement rate limiting
5. Use secure connections (HTTPS) 