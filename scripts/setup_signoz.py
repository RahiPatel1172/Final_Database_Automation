import os
import json
import requests
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API URL and ensure it doesn't end with /api
SIGNOZ_API_URL = os.getenv('SIGNOZ_API_URL', 'http://localhost:8080')
if SIGNOZ_API_URL.endswith('/api'):
    SIGNOZ_API_URL = SIGNOZ_API_URL[:-4]  # Remove /api from the end

# Get the JWT secret key from the environment variables or use the hardcoded value from the container
JWT_SECRET = "mysupersecretjwtkey"

def get_auth_token():
    """Generate JWT token for SigNoz authentication."""
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow(),
        'sub': 'admin',
        'name': 'admin',
        'email': 'admin@example.com',
        'role': 'Admin'
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    print(f"Generated JWT token with secret key: {JWT_SECRET}")
    return token

def check_auth_required():
    """Check if authentication is required by the API"""
    try:
        # Try to access a protected endpoint without authentication
        response = requests.get(f'{SIGNOZ_API_URL}/api/v1/dashboards')
        if response.status_code == 200:
            print("Authentication is not required. API is accessible without JWT.")
            return False
        else:
            print(f"Authentication check result: {response.status_code} - {response.text}")
            return True
    except requests.exceptions.RequestException as e:
        print(f"Error checking authentication: {e}")
        return True

def create_dashboard(auth_token=None):
    """Create a MySQL performance monitoring dashboard."""
    headers = {}
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    headers['Content-Type'] = 'application/json'
    
    dashboard_config = {
        'title': 'MySQL Performance Dashboard',
        'description': 'Monitoring MySQL database performance metrics',
        'tags': ['mysql', 'database'],
        'layout': 'horizontal',
        'widgets': [
            {
                'title': 'Query Latency',
                'description': 'Average query execution time',
                'query': 'rate(mysql_query_latency_seconds_sum[5m])',
                'panelType': 'timeseries'
            },
            {
                'title': 'Active Connections',
                'description': 'Number of active database connections',
                'query': 'mysql_active_connections',
                'panelType': 'gauge'
            },
            {
                'title': 'Slow Queries',
                'description': 'Number of slow queries per minute',
                'query': 'rate(mysql_slow_queries_total[5m])',
                'panelType': 'timeseries'
            }
        ]
    }
    
    try:
        # First check if the API is accessible
        response = requests.get(f'{SIGNOZ_API_URL}/api/v1/version')
        print(f"Version API check: {response.status_code} - {response.text}")
        
        # Then try to create the dashboard
        print(f"Sending request to {SIGNOZ_API_URL}/api/v1/dashboards")
        print(f"Headers: {headers}")
        print(f"Dashboard config: {json.dumps(dashboard_config)}")
        
        response = requests.post(
            f'{SIGNOZ_API_URL}/api/v1/dashboards',
            headers=headers,
            json=dashboard_config
        )
        
        print(f"Dashboard creation response: {response.status_code} - {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("Dashboard created successfully")
            return response.json()
        else:
            print(f"Failed to create dashboard: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def setup_alerts(auth_token=None):
    """Set up monitoring alerts."""
    headers = {}
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    headers['Content-Type'] = 'application/json'
    
    alerts = [
        {
            'name': 'High Query Latency',
            'description': 'Alert when query latency exceeds threshold',
            'condition': 'rate(mysql_query_latency_seconds_sum[5m]) > 1',
            'labels': {'severity': 'warning'},
            'annotations': {'summary': 'High query latency detected'}
        },
        {
            'name': 'Connection Pool Exhaustion',
            'description': 'Alert when connection pool is near capacity',
            'condition': 'mysql_active_connections > mysql_max_connections * 0.8',
            'labels': {'severity': 'critical'},
            'annotations': {'summary': 'Database connection pool near capacity'}
        },
        {
            'name': 'Slow Query Rate',
            'description': 'Alert on high rate of slow queries',
            'condition': 'rate(mysql_slow_queries_total[5m]) > 10',
            'labels': {'severity': 'warning'},
            'annotations': {'summary': 'High rate of slow queries detected'}
        }
    ]
    
    for alert in alerts:
        try:
            print(f"Sending request to {SIGNOZ_API_URL}/api/v1/rules")
            print(f"Headers: {headers}")
            print(f"Alert config: {json.dumps(alert)}")
            
            response = requests.post(
                f'{SIGNOZ_API_URL}/api/v1/rules',
                headers=headers,
                json=alert
            )
            
            print(f"Alert creation response: {response.status_code} - {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
                print(f"Alert '{alert['name']}' created successfully")
            else:
                print(f"Failed to create alert '{alert['name']}': {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error creating alert '{alert['name']}': {e}")
            if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")

def configure_mysql_logging():
    """Configure MySQL logging for Signoz"""
    mysql_config = """
[mysqld]
slow_query_log = 1
slow_query_log_file = /var/log/mysql/mysql-slow.log
long_query_time = 5
log_output = FILE
"""
    
    print("Add the following configuration to your MySQL configuration file:")
    print(mysql_config)
    print("\nThen restart MySQL service to apply changes.")

def main():
    """Main function to set up SigNoz monitoring."""
    try:
        auth_required = check_auth_required()
        auth_token = None
        
        if auth_required:
            auth_token = get_auth_token()
            print("Using authentication token for API requests")
        else:
            print("Attempting API requests without authentication")
        
        dashboard = create_dashboard(auth_token)
        if dashboard:
            setup_alerts(auth_token)
        configure_mysql_logging()
        print("SigNoz monitoring setup completed")
    except Exception as e:
        print(f"Error setting up SigNoz monitoring: {e}")

if __name__ == '__main__':
    main() 