# PROG8850 - Database Automation Project
## Group Members
- Kathiriya, Nidhip Rameshbhai
- Patel, Rahi Rajendrakumar

## Project Overview
This project implements a fully automated database management system with CI/CD, advanced monitoring, and performance optimization. The system manages a MySQL database for climate data with automated deployment, monitoring, and optimization capabilities.

## Project Structure
```
.
├── .github/
│   └── workflows/
│       └── ci_cd_pipeline.yml
├── sql/
│   ├── 01_initial_schema.sql
│   ├── 02_schema_update.sql
│   └── 03_sample_data.sql
├── scripts/
│   └── multi_thread_queries.py
├── .gitignore
└── README.md
```

## Setup Instructions

### Prerequisites
- MySQL Server
- Python 3.x
- GitHub Account
- Signoz Account

### Local Development Setup
1. Clone the repository
2. Create a `.secrets` file with the following structure:
   ```
   DB_HOST=your_host
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_NAME=project_db
   ```
3. Install Python dependencies:
   ```bash
   pip install mysql-connector-python python-dotenv
   ```

### Database Setup
1. Create the database:
   ```sql
   CREATE DATABASE project_db;
   ```
2. Run the SQL scripts in order:
   ```bash
   mysql -u your_user -p project_db < sql/01_initial_schema.sql
   mysql -u your_user -p project_db < sql/02_schema_update.sql
   mysql -u your_user -p project_db < sql/03_sample_data.sql
   ```

## Monitoring Setup
1. Set up Signoz monitoring
2. Configure MySQL logs to be sent to Signoz
3. Set up the dashboard and alerts as described in the project requirements

## License
This project is for educational purposes only. 