import sys
sys.path.append('.')

import psycopg2
import logging
from prompt.prompts import POSTGRES_CONFIG

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=POSTGRES_CONFIG['host'],
            port=POSTGRES_CONFIG['port'],
            dbname=POSTGRES_CONFIG['dbname'],
            user=POSTGRES_CONFIG['user'],
            password=POSTGRES_CONFIG['password']
        )
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
        return None

def check_table_exists(conn, table_name):
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                );
            """)
            exists = cur.fetchone()[0]
            return exists
    except Exception as e:
        logger.error(f"Failed to check table existence: {str(e)}")
        return False

def run_query(query: str, table_name: str = 'world_happiness_report') -> dict:
    conn = None
    try:
        if not query:
            return {'data': None, 'columns': [], 'error': "No query provided"}
        
        conn = get_db_connection()
        if conn is None:
            return {'data': None, 'columns': [], 'error': "Database connection failed"}
        
        if not check_table_exists(conn, table_name):
            return {'data': None, 'columns': [], 'error': f"Table '{table_name}' does not exist. Please create the table and load the data."}

        with conn.cursor() as cur:
            cur.execute(query)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()
                return {
                    'data': [dict(zip(columns, row)) for row in data],
                    'columns': columns,
                    'error': None
                }
            return {'data': None, 'columns': [], 'error': "No data returned"}
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        return {'data': None, 'columns': [], 'error': str(e)}
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

def convert_to_markdown_table(result: dict) -> str:
    if result.get('error'):
        return f"Error: {result['error']}"
    if not result.get('data'):
        return "Query ran successfully, no record found"

    data = result['data']
    columns = result['columns']
    if not columns:
        return "No columns returned"

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = ["| " + " | ".join(str(row.get(col, '')) for col in columns) + " |" for row in data]

    return "\n".join([header, separator] + rows)