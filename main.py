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
        "1|What is the digital readiness score of South Asia in 2020?",
        "2|Country with the highest global development resilience score in 2020?",
        "3|What is the human development index score of Vietnam in 2019?",
        "4|What is the inflation rate of Vietnam in 2009?",
        "5|What is the unemployment rate of Europe region in 2008?",
        "6|What is the life expectancy of Japan in 2020?",
        "7|What is the economic opportunity index of indebt countries group in 2020?",
        "8|What is the gdp per capita of OECD group in 2019?",
        "9|What is the green transition score of lower middle income group in 2020?",
        "10|What is the unemployment rate of US in 2020?",
        "11|To what extent has the world's GDP per capita grown between 2000 and 2020?",
        "12|What is the average economic opportunity index of low and indebt countries?",
        "13|How many countries has the gdp per capita lower than the world in 2019?",
        "14|Which country has the highest health expenditure per capita in 2020?",
        "15|How many countries are in lower middle income group as in 2020?",
        "16|What is the average digital readiness score of high income countries in 2019?",
        "17|Which country has the lowest global resilience score?",
        "18|What is the highest energy per capita score in 2020? In which country",
        "19|What country has the longest period of deflation? Deflation is known as when the inflation is negative",
        "20|Which country has the highest gdp per capita among lower middle income group?",
        "21|Number of countries have higher economic opportunity than the world",
        "22|Looking at the green transition score of all the countries and regions over the years, what is the common patterns?",
        "23|Explain for me the correlations of human development index and gdp per capita",
        "24|Evaluate the differences in digital readiness of South Asia compared to Europe region",
        "25|Is there any correlation between governance quality and digital readiness score of South Asia?",
        "26|Does the school enrolment in secondary affect the HDI in South Asia?",
        "27|What is the relationship of the FDI percentage of gdp and economic grow in middle and low income group?",
        "28|Compare the economic opportunity index of high income, middlie income groups and the world",
        "29|Is the weather vulnerability related to the child mortality in high income country?",
        "30|Do countries with high weather vulnerability score have higher green transition scores? Explain for me the implication",
        "31|What is the relationship between unemployment rate and inflation of US through years?"
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
