import mysql.connector
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def analyze_slow_queries():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Enable slow query log
        cursor.execute("SET GLOBAL slow_query_log = 1")
        cursor.execute("SET GLOBAL long_query_time = 1")  # Log queries taking more than 1 second
        cursor.execute("SET GLOBAL log_queries_not_using_indexes = 1")
        
        # Get current slow query log file
        cursor.execute("SHOW VARIABLES LIKE 'slow_query_log_file'")
        slow_log_file = cursor.fetchone()['Value']
        
        # Get slow query statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_slow_queries,
                AVG(query_time) as avg_query_time,
                MAX(query_time) as max_query_time,
                SUM(query_time) as total_query_time
            FROM mysql.slow_log
            WHERE start_time >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """)
        stats = cursor.fetchone()
        
        logging.info(f"Slow Query Analysis:")
        logging.info(f"Total slow queries in last 24h: {stats['total_slow_queries']}")
        logging.info(f"Average query time: {stats['avg_query_time']:.2f}s")
        logging.info(f"Maximum query time: {stats['max_query_time']:.2f}s")
        logging.info(f"Total time spent in slow queries: {stats['total_query_time']:.2f}s")
        
        # Get top 10 slowest queries
        cursor.execute("""
            SELECT 
                db,
                COUNT(*) as query_count,
                AVG(query_time) as avg_time,
                MAX(query_time) as max_time,
                SUM(query_time) as total_time,
                GROUP_CONCAT(DISTINCT sql_text) as sample_queries
            FROM mysql.slow_log
            WHERE start_time >= DATE_SUB(NOW(), INTERVAL 1 DAY)
            GROUP BY db
            ORDER BY total_time DESC
            LIMIT 10
        """)
        
        logging.info("\nTop 10 Slowest Queries by Database:")
        for row in cursor.fetchall():
            logging.info(f"\nDatabase: {row['db']}")
            logging.info(f"Query Count: {row['query_count']}")
            logging.info(f"Average Time: {row['avg_time']:.2f}s")
            logging.info(f"Maximum Time: {row['max_time']:.2f}s")
            logging.info(f"Total Time: {row['total_time']:.2f}s")
            logging.info(f"Sample Query: {row['sample_queries'].split(',')[0][:200]}...")
        
        # Get index usage statistics
        cursor.execute("""
            SELECT 
                table_schema,
                table_name,
                index_name,
                COUNT(*) as usage_count
            FROM performance_schema.table_io_waits_summary_by_index_usage
            WHERE index_name IS NOT NULL
            GROUP BY table_schema, table_name, index_name
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        
        logging.info("\nTop 10 Most Used Indexes:")
        for row in cursor.fetchall():
            logging.info(f"Table: {row['table_schema']}.{row['table_name']}")
            logging.info(f"Index: {row['index_name']}")
            logging.info(f"Usage Count: {row['usage_count']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logging.error(f"Error analyzing slow queries: {e}")

def optimize_indexes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find tables without primary keys
        cursor.execute("""
            SELECT 
                table_schema,
                table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_name NOT IN (
                SELECT table_name
                FROM information_schema.table_constraints
                WHERE constraint_type = 'PRIMARY KEY'
                AND table_schema = %s
            )
        """, (os.getenv('DB_NAME'), os.getenv('DB_NAME')))
        
        tables_without_pk = cursor.fetchall()
        if tables_without_pk:
            logging.info("\nTables without Primary Keys:")
            for table in tables_without_pk:
                logging.info(f"{table['table_schema']}.{table['table_name']}")
        
        # Find potential missing indexes
        cursor.execute("""
            SELECT 
                table_schema,
                table_name,
                column_name
            FROM information_schema.columns
            WHERE table_schema = %s
            AND column_name IN ('id', 'created_at', 'updated_at', 'status')
            AND (table_schema, table_name, column_name) NOT IN (
                SELECT 
                    table_schema,
                    table_name,
                    column_name
                FROM information_schema.statistics
                WHERE table_schema = %s
            )
        """, (os.getenv('DB_NAME'), os.getenv('DB_NAME')))
        
        missing_indexes = cursor.fetchall()
        if missing_indexes:
            logging.info("\nPotential Missing Indexes:")
            for index in missing_indexes:
                logging.info(f"Table: {index['table_schema']}.{index['table_name']}")
                logging.info(f"Column: {index['column_name']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logging.error(f"Error optimizing indexes: {e}")

if __name__ == "__main__":
    logging.info("Starting database performance analysis...")
    analyze_slow_queries()
    optimize_indexes()
    logging.info("Analysis complete!") 