import os
import time
import mysql.connector
import requests
import random
from dotenv import load_dotenv
import logging
from concurrent.futures import ThreadPoolExecutor
import json

# Import OpenTelemetry modules
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants and configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'climate_data')
MAX_THREADS = 5
METRICS_ENDPOINT = "http://localhost:4318/v1/metrics"
OTLP_ENDPOINT = os.getenv('OTLP_ENDPOINT', 'http://localhost:4317')

# Set up OpenTelemetry tracing
resource = Resource(attributes={
    SERVICE_NAME: "mysql-monitoring"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Get a tracer
tracer = trace.get_tracer(__name__)

def execute_query(query, params=None):
    """Execute a database query with error handling and metrics."""
    with tracer.start_as_current_span("execute_query") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", DB_NAME)
        span.set_attribute("db.user", DB_USER)
        span.set_attribute("db.statement", query)
        
        start_time = time.time()
        connection = None
        cursor = None
        rows = []
        success = False
        
        try:
            connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            cursor = connection.cursor()
            
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                span.set_attribute("db.operation", "SELECT")
                span.set_attribute("db.rows_fetched", len(rows))
            else:
                connection.commit()
                span.set_attribute("db.operation", query.strip().upper().split()[0])
                if cursor.rowcount > 0:
                    span.set_attribute("db.rows_affected", cursor.rowcount)
                
            success = True
            return rows, success
        except Exception as e:
            logger.error(f"Database error: {e}")
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            if connection:
                connection.rollback()
            return [], False
        finally:
            query_time = time.time() - start_time
            span.set_attribute("db.query_time_seconds", query_time)
            
            if cursor:
                cursor.close()
            if connection:
                connection.close()
            
            # Log query metrics
            query_type = query.strip().upper().split()[0]
            logger.info(f"{query_type} query {'successful' if success else 'failed'} in {query_time:.2f} seconds")

def run_select_query():
    """Run a sample SELECT query for monitoring."""
    with tracer.start_as_current_span("run_select_query"):
        query = "SELECT * FROM ClimateData LIMIT 1000"
        rows, success = execute_query(query)
        return len(rows), success, "SELECT"

def run_insert_query():
    """Run a sample INSERT query for monitoring."""
    with tracer.start_as_current_span("run_insert_query"):
        temperature = round(random.uniform(-10, 40), 1)
        precipitation = round(random.uniform(0, 100), 1)
        humidity = round(random.uniform(0, 100), 1)
        
        query = """
        INSERT INTO ClimateData 
        (location, record_date, temperature, precipitation, humidity) 
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            f"Location-{random.randint(1, 1000)}",
            time.strftime('%Y-%m-%d'),
            temperature,
            precipitation,
            humidity
        )
        
        _, success = execute_query(query, params)
        return 1 if success else 0, success, "INSERT"

def run_update_query():
    """Run a sample UPDATE query for monitoring."""
    with tracer.start_as_current_span("run_update_query"):
        query = """
        UPDATE ClimateData 
        SET humidity = %s 
        WHERE record_id = %s
        LIMIT 1
        """
        
        # First get a random record_id
        select_query = "SELECT record_id FROM ClimateData ORDER BY RAND() LIMIT 1"
        rows, success = execute_query(select_query)
        
        if not success or not rows:
            return 0, False, "UPDATE"
        
        record_id = rows[0][0]
        params = (round(random.uniform(0, 100), 1), record_id)
        
        _, success = execute_query(query, params)
        return 1 if success else 0, success, "UPDATE"

def worker(task_func):
    """Worker function for thread pool."""
    with tracer.start_as_current_span(f"worker_{task_func.__name__}"):
        return task_func()

def run_concurrent_queries():
    """Run multiple database queries concurrently."""
    with tracer.start_as_current_span("run_concurrent_queries"):
        tasks = [run_select_query] * 3 + [run_insert_query] * 3 + [run_update_query] * 2
        random.shuffle(tasks)
        
        rows_read = 0
        rows_inserted = 0
        total_queries = 0
        successful_queries = 0
        
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            results = list(executor.map(worker, tasks))
            
        for rows, success, query_type in results:
            total_queries += 1
            if success:
                successful_queries += 1
                if query_type == "SELECT":
                    rows_read += rows
                elif query_type == "INSERT":
                    rows_inserted += rows
        
        return {
            "connected_threads": MAX_THREADS,
            "rows_read": rows_read,
            "rows_inserted": rows_inserted,
            "total_queries": total_queries,
            "successful_queries": successful_queries
        }

def send_metrics_to_signoz(metrics):
    """Send metrics to SigNoz OTLP endpoint."""
    with tracer.start_as_current_span("send_metrics_to_signoz"):
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Format metrics for SigNoz
            timestamp = int(time.time() * 1_000_000_000)  # Convert to nanoseconds
            
            payload = {
                "resourceMetrics": [
                    {
                        "resource": {
                            "attributes": [
                                {"key": "service.name", "value": {"stringValue": "mysql-monitoring"}},
                                {"key": "host.name", "value": {"stringValue": os.uname().nodename}}
                            ]
                        },
                        "scopeMetrics": [
                            {
                                "metrics": [
                                    {
                                        "name": "mysql.threads.connected",
                                        "description": "Number of connected threads",
                                        "gauge": {
                                            "dataPoints": [
                                                {
                                                    "timeUnixNano": timestamp,
                                                    "asInt": metrics["connected_threads"]
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "name": "mysql.rows.read",
                                        "description": "Number of rows read",
                                        "sum": {
                                            "dataPoints": [
                                                {
                                                    "timeUnixNano": timestamp,
                                                    "asInt": metrics["rows_read"]
                                                }
                                            ],
                                            "aggregationTemporality": 2,
                                            "isMonotonic": True
                                        }
                                    },
                                    {
                                        "name": "mysql.rows.inserted",
                                        "description": "Number of rows inserted",
                                        "sum": {
                                            "dataPoints": [
                                                {
                                                    "timeUnixNano": timestamp,
                                                    "asInt": metrics["rows_inserted"]
                                                }
                                            ],
                                            "aggregationTemporality": 2,
                                            "isMonotonic": True
                                        }
                                    },
                                    {
                                        "name": "mysql.queries.total",
                                        "description": "Total number of queries",
                                        "sum": {
                                            "dataPoints": [
                                                {
                                                    "timeUnixNano": timestamp,
                                                    "asInt": metrics["total_queries"]
                                                }
                                            ],
                                            "aggregationTemporality": 2,
                                            "isMonotonic": True
                                        }
                                    },
                                    {
                                        "name": "mysql.queries.success_rate",
                                        "description": "Query success rate",
                                        "gauge": {
                                            "dataPoints": [
                                                {
                                                    "timeUnixNano": timestamp,
                                                    "asDouble": metrics["successful_queries"] / max(metrics["total_queries"], 1)
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(METRICS_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Metrics sent to SigNoz successfully: {response.status_code}")
            
            # Print metrics for demonstration
            print("\nPerformance Metrics:")
            print(f"Connected Threads: {metrics['connected_threads']}")
            print(f"Rows Read: {metrics['rows_read']}")
            print(f"Rows Inserted: {metrics['rows_inserted']}")
            print(f"Total Queries: {metrics['total_queries']}")
            print(f"Success Rate: {100 * metrics['successful_queries'] / max(metrics['total_queries'], 1):.1f}%")
            
            return True
        except Exception as e:
            logger.error(f"Error sending metrics to SigNoz: {e}")
            return False

def main():
    """Main function to run the monitoring."""
    with tracer.start_as_current_span("main"):
        try:
            # Check if database exists, create if not
            connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            connection.commit()
            
            # Switch to database
            cursor.execute(f"USE {DB_NAME}")
            
            # Create table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ClimateData (
                record_id INT PRIMARY KEY AUTO_INCREMENT,
                location VARCHAR(100) NOT NULL,
                record_date DATE NOT NULL,
                temperature FLOAT NOT NULL,
                precipitation FLOAT NOT NULL,
                humidity FLOAT DEFAULT 70.0
            )
            """)
            connection.commit()
            
            # Close initial connection
            cursor.close()
            connection.close()
            
            # Seed the table with initial data if empty
            connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            cursor = connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM ClimateData")
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info("Seeding initial data...")
                locations = ["New York", "Tokyo", "London", "Sydney", "Moscow", "Cape Town", "Rio", "Berlin"]
                
                for i in range(100):
                    location = random.choice(locations)
                    # Generate a random date between last year and now
                    year = 2024
                    month = random.randint(1, 12)
                    day = random.randint(1, 28)
                    date = f"{year}-{month:02d}-{day:02d}"
                    
                    temperature = round(random.uniform(-10, 40), 1)
                    precipitation = round(random.uniform(0, 100), 1)
                    humidity = round(random.uniform(0, 100), 1)
                    
                    cursor.execute(
                        "INSERT INTO ClimateData (location, record_date, temperature, precipitation, humidity) VALUES (%s, %s, %s, %s, %s)",
                        (location, date, temperature, precipitation, humidity)
                    )
                
                connection.commit()
                logger.info(f"Initial data seeded: {cursor.rowcount} rows")
            
            cursor.close()
            connection.close()
            
            logger.info("Starting MySQL monitoring")
            
            # Run multiple concurrent queries
            metrics = run_concurrent_queries()
            
            # Send metrics to SigNoz
            send_metrics_to_signoz(metrics)
            
            logger.info("All concurrent queries completed")
            
        except Exception as e:
            logger.error(f"Error in main function: {e}")
            trace.get_current_span().record_exception(e)
            trace.get_current_span().set_status(trace.StatusCode.ERROR, str(e))

if __name__ == "__main__":
    main() 