import sys
import logging
from db_utils import get_db_connection, check_table_exists
from agent import sql_gen_node, query_execution_node, response_generation_node, State

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    user_queries = [
        "Which countries had the highest life ladder scores in 2020?",
        "Compare the average life ladder score between Western Europe and Sub-Saharan Africa in 2021. Which region had the higher score?",
        "Which countries in Latin America had above-average social support and also experienced below-average negative affect in 2020?",
        "Which countries showed a consistent increase in confidence in national government every year from 2018 to 2021?",
        "Find countries where positive affect was above 0.7 and negative affect was below 0.3 in 2021.",
        "What are the top 3 countries with the highest freedom to make life choices among those with a life ladder score below 5 in 2019?"
    ]

    conn = get_db_connection()
    if conn is None:
        logger.error("Please check your PostgreSQL configuration. Exiting...")
        sys.exit(1)
    if not check_table_exists(conn):
        logger.error("Table 'world_happiness_report' does not exist. Please create the table and load the data. Exiting...")
        conn.close()
        sys.exit(1)
    conn.close()

    if not user_queries:
        logger.error("No query provided. Please set a valid query in the code.")
        return

    state = {
        'question': user_queries,
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