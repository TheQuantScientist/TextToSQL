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
        # 'cogito:3b',
        # 'deepseek-r1:7b',
        # 'gemma3:4b',
        # 'gemma3n:e4b',
        # 'llama3.2:latest',
        # 'mistral:7b',
        'phi3.5:3.8b',
        'phi4-mini:3.8b',
        'qwen2.5:3b',
        'qwen3:4b',    
    ]

TABLE_NAME = "world_happiness_report"

OUTPUT_DIR = os.path.join(
     os.path.dirname(__file__),
     "..", "query", "output", "cogito:3b", "world_happiness_report", "pred_sql"
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
   "What is the positive affect of US in 2008?",
    "What is the life ladder of Vietnam in 2022?",
    "What is the long GDP per capita of China in 2009?",
    "What is the social support index of Germany in 2008?",
    "What is the Healthy Life Expectancy At Birth of Japan in 2020?",
    "What is the Freedom To Make Life Choices of Vietnam in 2018?",
    "What is the generiosity score of Singapore in 2022?",
    "What is the Perceptions Of Corruption of Ecuador in 2008?",
    "What is the negative affect of Japan in 2022?",
    "What is the Confidence In National Government of Singapore in 2022?",
    "What is the average positive affect of all countries in 2008?",
    "What is the average life ladder of Asia countries in 2022?",
    "Which country has the highest average long gdp per capita through years?",
    "Which country has the lowest average social support score over years?",
    "What is the average Healthy Life Expectancy At Birth of the world after 2020? ",
    "Which country has the highest freedom to make choices index? What region is it from? ",
    "How many countries have higher average generiosity over years compared to the world' average?",
    "Which region has the highest average perceptions of corruption?",
    "Which country has the highest average negative affect in 2022? ",
    "What is the average Confidence In National Government score of Vietnam over years?",
    "What are the countries having confidence in national goverment higher than world average in 2022?",
    "Interpret for me the current trend in positive affect of the world from 2008 to 2022?",
    "Comparing the life ladder of Asia and Europe to tell me which region is worth to live?",
    "Are countries with higher long gdp per capita likely to have higher positive effect over years? Comparing the data to evaluate ",
    "Does lack of social support lead to higher negative affect over years? ",
    "Analyze the trend of Healthy Life Expectancy At Birth by region (Asia, Europe, North America)",
    "Evaluate for me the relationship between freedom to make choices and positive affect of Asia and North America countries. Explain the reasons.",
    "What is the current movement of generiosity of Asian countries over years? Explain the reasons.",
    "What is the relationship of percptions of corruption and confidence in national government?",
    "Do high long gdp per capita countries have higher negative affects? Explain the results.",
    "How differences in Confidence In National Government score comparing all the regions? Evaluate the importance of governance trust on positive affects."
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
                if TABLE_NAME == 'world_happiness_report':
                    local_tablename = 'happiness_record'
                model_output = os.path.join(
                    os.path.dirname(__file__),
                    "..", "query", "output", model, local_tablename, "pred_sql"
                )
                save_ground_truth(state, idx, gen_time, model_output)
                logger.info(f"Saved: {model_output}/question_{idx}.json")
            except Exception as e:
                logger.error(f"Error processing question {idx}: {e}")