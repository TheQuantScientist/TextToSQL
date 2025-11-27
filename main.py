import sys
import logging
import time
import re
from datetime import datetime

sys.path.append('.')

from utils.db_utils import get_db_connection, check_table_exists
from utils.agent import sql_gen_node, query_execution_node, response_generation_node, State, save_output_as_json

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    user_queries = [
        "1|What is the digital readiness score of South Asia in 2020?"
    ]

    table_name = "global_development_indicators"
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
    
    def sanitize_fs_name(s: str) -> str:
        s = re.sub(r'[<>:"/\\|?*]', '_', s)
        return s.rstrip(' .')  
    
    models = [
        #'qwen2.5:3b',
        #'falcon3:3b',
        # 'phi3.5:3.8b',
        # 'mistral:7b',
        # 'llama3.2:latest',
        'gemma3:4b'
    ]
    
    for model in models:
        logger.info(f"Running model {model}...")
        safe_dir = f"{sanitize_fs_name(model)}_{sanitize_fs_name(table_name)}"
        for idx, question in enumerate(user_queries, 1):
            state = {
                'question': question,
                'table_name': table_name,
                'query': '',
                'query_result': '',
                'final_answer': '',
                'model': model
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
                    "raw-results": state['query_result'],
                    "sql_execution_time": round(state.get('sql_execution_time', 0),2),
                    "nlp_generation_time": round(state.get('nlp_generation_time', 0),2),
                    "total_time":round(total_time,2)
                }
                question_num = question.split('|')[0]
                save_output_as_json(output, question_num, safe_dir)
                
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
