# PROG8850 - Database Automation Project

## Group Members
- Nidhip Rameshbhai Kathiriya
- Rahi Rajendrakumar Patel

## Project Overview
This project implements a fully automated database management system with CI/CD, advanced monitoring, and performance optimization. The system manages a MySQL database for climate data with automated deployment, monitoring, and optimization capabilities.

### Features
- **CI/CD Pipeline**: Automated database deployments using GitHub Actions
- **Advanced Monitoring**: Real-time performance tracking with SigNoz
- **Performance Optimization**: Query optimization and database tuning
- **Alerting System**: Automated alerts for performance issues

## Database Schema
```sql
CREATE TABLE ClimateData (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    location VARCHAR(100) NOT NULL,
    record_date DATE NOT NULL,
    temperature FLOAT NOT NULL,
    precipitation FLOAT NOT NULL,
    humidity FLOAT DEFAULT 70.0
);
```

## Project Structure
```
.
├── .github/workflows/
│   └── ci_cd_pipeline.yml     # GitHub Actions workflow
├── sql/
│   ├── 01_initial_schema.sql  # Initial table creation
│   ├── 02_schema_update.sql   # Schema update (adds humidity column)
│   └── 03_sample_data.sql     # Sample data for testing
├── scripts/
│   ├── multi_thread_queries.py    # Concurrent database operations
│   ├── monitor_mysql.py           # MySQL monitoring script
│   ├── setup_signoz.py            # SigNoz configuration
│   ├── monitor_performance.py     # Performance monitoring
│   └── analyze_slow_queries.py    # Slow query analysis
├── mysql-slow-log.cnf         # MySQL slow query configuration
├── mysql-monitor-cron         # Cron job for monitoring
├── mysql-monitor.service      # Systemd service for monitoring
├── docker-compose.yml         # SigNoz Docker configuration
├── otel-collector-config.yaml # OpenTelemetry configuration
├── .env                       # Environment configuration
└── requirements.txt           # Python dependencies
```

## Setup Instructions

### Prerequisites
- MySQL Server
- Python 3.9+
- Docker (for SigNoz)
- GitHub Account

### Local Development Setup
1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables in `.env` file

### Database Setup
1. Create the database and initial schema:
   ```sql
   mysql -u username -p < sql/01_initial_schema.sql
   ```
2. Apply schema update:
   ```sql
   mysql -u username -p < sql/02_schema_update.sql
   ```
3. Seed sample data:
   ```sql
   mysql -u username -p < sql/03_sample_data.sql
   ```

### Monitoring Setup
1. Start SigNoz using Docker Compose:
   ```bash
   docker-compose up -d
   ```
2. Configure MySQL slow query log:
   ```bash
   sudo cp mysql-slow-log.cnf /etc/mysql/conf.d/
   sudo systemctl restart mysql
   ```
3. Run the monitoring script:
   ```bash
   python scripts/monitor_mysql.py
   ```

## CI/CD Pipeline
Our GitHub Actions workflow automates the entire database deployment process:

1. **Environment Setup**: Configures Python and MySQL
2. **Schema Deployment**: Creates tables and applies schema changes
3. **Data Seeding**: Populates with sample data
4. **Concurrent Testing**: Executes parallel operations to test performance
5. **Validation**: Verifies successful deployment and schema changes

## Monitoring Features
The SigNoz monitoring setup provides real-time visibility into:

- Query performance and latency
- Database connection usage
- Error rates and slow queries
- CPU and memory utilization

## Alert Configuration
The system includes alerts for:
- High query latency (> 5 seconds)
- Connection pool exhaustion (> 80% usage)
- Slow query rate (> 5 per minute)

## Performance Optimization
We've implemented various performance optimizations:
- Query tuning and rewriting
- Index management
- Connection pool configuration
- Cache optimization

## License
This project is for educational purposes as part of the PROG8850 course at Conestoga College. 