import sys
import logging
from db_utils import get_db_connection, check_table_exists
from agent import sql_gen_node, query_execution_node, response_generation_node, State

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

finance_query = "Calculate and come up with a trading strategy for gold and stock, provide clear analysis"
country_query = "What is the average gini of Vietnam from 2000 to 2008? How it is related to gdp per capita"

def main():
    user_query = country_query
    table_name = "country_income"

    conn = get_db_connection()
    if conn is None:
        logger.error("Please check your PostgreSQL configuration. Exiting...")
        sys.exit(1)

    # Check table existed or not in database
    if not check_table_exists(conn, table_name):
        logger.error(f"Table '{table_name}' does not exist. Please create the table and load the data. Exiting...")
        conn.close()
        sys.exit(1)
    conn.close()

    if not user_query:
        logger.error("No query provided. Please set a valid query in the code.")
        return

    state = {
        'question': user_query,
        'table_name': table_name,
        'query': '',
        'query_result': '',
        'final_answer': ''
    }

    try:
        state = sql_gen_node(state)
        state = query_execution_node(state)
        state = response_generation_node(state)

        print("\n=== Results ===")
        print(f"Query: {state['query']}")
        print("Raw Results:")
        print(state['query_result'])
        print("\nFinal Answer:")
        print(state['final_answer'])
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()