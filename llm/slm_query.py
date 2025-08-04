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
    model: str

# === CONFIGURATION ===
models = [
        'cogito:3b',
        'deepseek-r1:7b',
        'gemma3:4b',
        'gemma3n:e4b',
        'llama3.2:latest',
        'mistral:7b',
        'phi3.5:3.8b',
        'phi4-mini:3.8b',
        'qwen2.5:3b',
        'qwen3:4b',    
    ]

TABLE_NAME = "global_development_indicators"

OUTPUT_DIR = os.path.join(
     os.path.dirname(__file__),
     "..", "query", "output", "falcon3", "global_development_indicators", "pred_sql"
 )
    
# === REMOVE NEWLINES IN QUERY ===
def clean_query_newlines(state: State) -> State:
    if "query" in state and isinstance(state["query"], str):
        # Remove real newlines and extra spaces
        state["query"] = ' '.join(state["query"].split())
    return state

# === SQL GENERATION NODE ===
def sql_gen_node(state: State) -> State:
    logger.info('Generating SQL query')
    llm = get_llm_model(state['model'])
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
    "What is the digital readiness score of South Asia in 2020?",
    "Country with the highest global development resilience score in 2020",
    "What is the human development index score of Vietnam in 2019?",
    "What is the inflation rate of Vietnam in 2009?",
    "What is the unemployment rate of Europe region in 2008?",
    "What is the life expectancy of Japan in 2020?",
    "What is the economic opportunity index of indebt countries group in 2020?",
    "What is the gpd per capita of OECD group in 2019?",
    "What is the green transition score of lower middle income group in 2020?",
    "What is the unemployment rate of US in 2020?",
    "To what extent has the world's GDP per capita grown between 2000 and 2020?",
    "What is the average economic opportunity index of low and indebt countries?",
    "How many countries has the gdp per capita lower than the world in 2019?",
    "Which country has the highest health expenditure per capita in 2020?",
    "How many countries are in lower middle income group as in 2020?",
    "What is the average digital readiness score of high income countries in 2019?",
    "Which country has the lowest global resilience score?",
    "What is the highest energy per capita score in 2020? In which country",
    "What country has the longest period of deflation? Deflation is known as when the inflation is negative",
    "Which country has the highest gdp per capita among lower middle income group?",
    "Number of countries have higher economic opportunity than the world",
    "Looking at the green transition score of all the countries and regions over the years, what is the common patterns?",
    "Explain for me the correlations of human development index and gdp per capita",
    "Evaluate the differences in digital readiness of South Asia compared to Europe region",
    "Is there any correlation between governance quality and digital readiness score of South Asia?",
    "Does the school enrolment in secondary affect the HDI in South Asia?",
    "What is the relationship of the FDI percentage of gdp and economic grow in middle and low income group?",
    "Compare the economic opportunity index of high income, middlie income groups and the world",
    "Is the weather vulnerability related to the child mortality in high income country?",
    "Do countries with high weather vulnerability score have higher green transition scores? Explain for me the implication",
    "What is the relationship between unemployment rate and inflation of US through years?"
    ]
    if not user_queries:
        logger.error("No query provided. Please set a valid query in the code.")
        exit()
    for model in models:
        for idx, question in enumerate(user_queries, 1):
            logger.info(f"Processing question {idx}: {question}")
            try:
                state: State = {
                    "question": question,
                    "query": "",
                    "table_name": TABLE_NAME,
                    "model": model
                }
                start_time = time.time()
                state = sql_gen_node(state)
                end_time = time.time()
                gen_time = end_time - start_time
                local_tablename = TABLE_NAME
                if local_tablename == 'global_development_indicators':
                    local_tablename = 'global_development'
                model_output = os.path.join(
                    os.path.dirname(__file__),
                    "..", "query", "output", model, local_tablename, "pred_sql"
                )
                save_ground_truth(state, idx, gen_time, model_output)
                logger.info(f"Saved: {model_output}/question_{idx}.json")
            except Exception as e:
                logger.error(f"Error processing question {idx}: {e}")
