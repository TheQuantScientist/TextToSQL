from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
import time
import json
import os
import logging
import sys
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_utils import get_llm_model
from prompt.prompts import DATA_FIELDS_MEANING, get_system_prompt

# === LOGGER SETUP ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === CONFIGURATION ===
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "query", "output", "country_income", "pred_sql"
)
TABLE_NAME = "country_income"

# === GET DATA FIELDS MEANING ===
def get_data_fields_meaning(table_name: str) -> str:
    if table_name not in DATA_FIELDS_MEANING:
        raise ValueError(f"Table '{table_name}' non-existent in DATA_FIELDS_MEANING.")
    fields = DATA_FIELDS_MEANING[table_name]['fields']
    lines = [f"{k}: {v}" for k, v in fields.items()]
    return "\n".join(lines)

# === STATE CLASS ===
class State(TypedDict):
    question: str
    query: str
    table_name: str
    
# === REMOVE NEWLINES IN QUERY ===
def clean_query_newlines(state: State) -> State:
    if "query" in state and isinstance(state["query"], str):
        # Remove real newlines and extra spaces
        state["query"] = ' '.join(state["query"].split())
    return state

# === SQL GENERATION NODE ===
def sql_gen_node(state: State) -> State:
    logger.info('Generating SQL query')
    llm = get_llm_model()
    print(llm)
    if llm is None:
        state['query'] = ""
        logger.error("No LLM available for query generation")
        return state

    system_prompt = get_system_prompt(table_name=state['table_name'])

    sql_gen_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])

    try:
        question = state['question']
        if ',' in question:
            date, index_info = question.split(',', 1)
            date = date.strip()
            index_info = index_info.strip()
            question = f"{index_info} on {date}"

        raw_sql = llm.invoke(sql_gen_prompt.format_messages(question=question))
        if isinstance(raw_sql, dict):
            raw_sql = raw_sql.get('query', '')
        elif not isinstance(raw_sql, str):
            raw_sql = str(raw_sql)
        raw_sql = raw_sql.strip()
        if raw_sql.startswith('```'):
            raw_sql = raw_sql.replace('```sql', '').replace('```', '').strip()
        state['query'] = raw_sql

    except Exception as e:
        logger.error(f"SQL generation failed: {str(e)}")
        traceback.print_exc()
        state['query'] = ""

    logger.info(f"Generated SQL Query: {state['query']}")
    return state

# === SAVE OUTPUT ===
def save_ground_truth(state: State, idx, gen_time=None, output_dir=OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)
    output = {
        "question": state["question"],
        "query": state["query"]
    }
    # Remove all \n from the query - Format the query
    if "query" in output and isinstance(output["query"], str):
        output["query"] = output["query"].replace('\n', ' ').replace('\r', ' ').strip()
    if gen_time is not None:
        output["generation_time"] = round(gen_time, 4)
    filename = f"question_{idx}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

# === MAIN PIPELINE ===
if __name__ == "__main__":
    user_queries = [
        "What is the gini recalculated of Vietnam in 2015?",
        "What is the net income of d10 category of US in 2015?",
        "What is the net income of d1 category of Thailand in 2009?",
        "What is the net income of d10 group of Singapore in 1970?",
        "What is the population of China in 2000?",
        "What is the gdp per capita of Sweden in 2015?",
        "Distinct list of region ID",
        "All the countries have gini recalculated greater than 0.4 in 2015",
        "What is the gpd per capita, population and gini coefficient of Vietnam in 2010?",
        "What is the net income of each category of Vietnam in 2015?",
        "What is the average of gini recalcuated score of Vietnam by year?",
        "Top 5 country that have highest gini recalulated in 2015",
        "Top 5 country of which d1 category has highest net income in 2015",
        "How many countries have gini recalculated lower than the world average in 2015?",
        "What is the average of d10 net income of Vietnam over years?",
        "What is the total net income of d5 to d9 groups of Vietnam in 2015?",
        "What is the average gini recalculated score of top 5 countries having highest population in 2015?",
        "Calculate the average gini of countries by region ID in 2015",
        "What is the growth rate of gini recalculated of Vietnam for each year?",
        "The average gini recalculated of the world in 2015",
        "What is the ratio of net income of d10 to d1 group of Singapore in 2015?",
        "Vietnam released economic reformation policy named 'Doi Moi' from 1986 to 2000. Evaluate the effectiveness of the policy based on the gini score trend of the country in 2 phases: Before 1986 and after 1986",
        "Analyze the trend of world's income inequality across region from 1967 to 2015.",
        "Does higher gdp per capita posiviely correlated with high income inequality? Explain possible reasons",
        "The financial crisis happened in 2008. Evaluate the income inequality before and after the event in US.",
        "Analyze the trend of income inequality and gdp per capita of Singapore from 1970 onward.",
        "Does population affect income inequality? Analyze gini index of China through years to explain",
        "Comparing the gini index of China and US over years to evaluate which country has higher income inequality",
        "Which region ID has high income inequality? Explain reasons behind it",
        "What are the common patterns can be observed from countries with high income inequality in 2015, knowing gini greater than 0.4 is considered as high inequality",
        "Evaluate the net income gap between low income group d1 to d4, middle income group d5 to d9 and high income group d10 in Vietnam and propose improvement plan"
    ]
    if not user_queries:
        logger.error("No query provided. Please set a valid query in the code.")
        exit()

    for idx, question in enumerate(user_queries, 1):
        logger.info(f"Processing question {idx}: {question}")
        try:
            state: State = {
                "question": question,
                "query": "",
                "table_name": TABLE_NAME
            }
            start_time = time.time()
            state = sql_gen_node(state)
            end_time = time.time()
            gen_time = end_time - start_time
            save_ground_truth(state, idx, gen_time)
            logger.info(f"Saved: {OUTPUT_DIR}/question_{idx}.json")
        except Exception as e:
            logger.error(f"Error processing question {idx}: {e}")