import sys
import logging
import time
from datetime import datetime

sys.path.append('.')

from utils.db_utils import get_db_connection, check_table_exists
from utils.agent import sql_gen_node, query_execution_node, response_generation_node, State, save_output_as_json

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    user_queries = [
        "1|Which countries had the highest life ladder scores in 2020?",
        "2|Compare the average life ladder score between Western Europe and Sub-Saharan Africa in 2021. Which region had the higher score?",
        "3|Which countries in Latin America had above-average social support and also experienced below-average negative affect in 2020?",
        "4|Which countries showed a consistent increase in confidence in national government every year from 2018 to 2021?",
        "5|Find countries where positive affect was above 0.7 and negative affect was below 0.3 in 2021.",
        "6|What are the top 3 countries with the highest freedom to make life choices among those with a life ladder score below 5 in 2019?"
    ]

    table_name = "world_happiness_report"
    conn = get_db_connection()
    if conn is None:
        logger.error("Please check your PostgreSQL configuration. Exiting...")
        sys.exit(1)
    if not check_table_exists(conn, table_name):
        logger.error(f"Table '{table_name}' does not exist. Please create the table and load the data. Exiting...")
        conn.close()
        sys.exit(1)
    conn.close()

    if not user_queries:
        logger.error("No query provided. Please set a valid query in the code.")
        return
    for idx, question in enumerate(user_queries, 1):
        state = {
            'question': question,
            'table_name': table_name,
            'query': '',
            'query_result': '',
            'final_answer': ''
        }

        try:
            state = sql_gen_node(state)
            state = query_execution_node(state)
            state = response_generation_node(state)
            total_time = state.get('sql_execution_time', 0)+ state.get('nlp_generation_time')

            output = {
                "question": state['question'],
                "query": state['query'],
                "answer": state['final_answer'],
                "sql_execution_time": round(state.get('sql_execution_time', 0),2),
                "nlp_generation_time": round(state.get('nlp_generation_time', 0),2),
                "total_time":round(total_time,2)
            }
            save_output_as_json(output, idx)
            
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
