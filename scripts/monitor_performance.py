#!/usr/bin/env python3
import os
import time
import mysql.connector
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'project_db')

def connect_to_database():
    """Connect to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        logger.info(f"Successfully connected to database {DB_NAME}")
        return connection
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def get_performance_metrics(connection):
    """Collect MySQL performance metrics."""
    metrics = {}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get global status
        cursor.execute("SHOW GLOBAL STATUS")
        status_rows = cursor.fetchall()
        
        # Convert to dictionary
        status = {row['Variable_name']: row['Value'] for row in status_rows}
        
        # Calculate key metrics
        metrics['threads_connected'] = status.get('Threads_connected', '0')
        metrics['queries_per_second'] = status.get('Queries', '0')
        metrics['slow_queries'] = status.get('Slow_queries', '0')
        metrics['uptime'] = status.get('Uptime', '0')
        
        # Get table statistics
        cursor.execute(f"SELECT COUNT(*) as row_count FROM {DB_NAME}.ClimateData")
        table_stats = cursor.fetchone()
        metrics['row_count'] = table_stats['row_count']
        
        cursor.close()
        return metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return {}

def log_metrics(metrics):
    """Log performance metrics."""
    logger.info("=== MySQL Performance Metrics ===")
    logger.info(f"Connected Threads: {metrics.get('threads_connected', 'N/A')}")
    logger.info(f"Queries Executed: {metrics.get('queries_per_second', 'N/A')}")
    logger.info(f"Slow Queries: {metrics.get('slow_queries', 'N/A')}")
    logger.info(f"Server Uptime (seconds): {metrics.get('uptime', 'N/A')}")
    logger.info(f"Row Count in ClimateData: {metrics.get('row_count', 'N/A')}")
    logger.info("===============================")

def run_test_queries(connection):
    """Run some test queries to generate load."""
    try:
        cursor = connection.cursor()
        
        # Simple SELECT query
        cursor.execute("SELECT * FROM ClimateData LIMIT 100")
        cursor.fetchall()
        logger.info("Successfully executed SELECT query")
        
        # Basic aggregation
        cursor.execute("SELECT AVG(temperature), AVG(humidity) FROM ClimateData")
        cursor.fetchall()
        logger.info("Successfully executed aggregation query")
        
        # GROUP BY query
        cursor.execute("SELECT location, COUNT(*) FROM ClimateData GROUP BY location")
        cursor.fetchall()
        logger.info("Successfully executed GROUP BY query")
        
        cursor.close()
    except Exception as e:
        logger.error(f"Error executing test queries: {e}")

def main():
    """Main function to monitor MySQL performance."""
    logger.info("Starting MySQL performance monitoring")
    
    # Connect to database
    connection = connect_to_database()
    if not connection:
        logger.error("Failed to connect to database. Exiting.")
        return
    
    try:
        # Continuous monitoring loop
        while True:
            # Run some test queries
            run_test_queries(connection)
            
            # Get and log performance metrics
            metrics = get_performance_metrics(connection)
            log_metrics(metrics)
            
            # Wait 10 seconds before next check
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main() 