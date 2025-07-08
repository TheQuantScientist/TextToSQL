from typing_extensions import TypedDict
from groq import Groq
import time
import json
import os
import logging
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_utils import get_groq_llm_model
from prompt.prompts import GROQ_CONFIG, DATA_FIELDS_MEANING, get_system_prompt
# === LOGGER SETUP ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === CONFIGURATION ===
OUTPUT_DIR = "outputs"
TABLE_NAME = "world_happiness_report"

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

    llm_client = get_groq_llm_model()
    if not llm_client:
        logger.error("Groq LLM client could not be initialized. Exiting.")
        exit()
    
    # Get data fields meaning
    system_prompt = get_system_prompt(table_name=state['table_name'])

    response = llm_client.chat.completions.create(
        model=GROQ_CONFIG['model'],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a SQL query for the following question: {state['question']}"}
        ],
        temperature=0,
        max_tokens=512,
        top_p=1,
        stream=False
    )
    sql = response.choices[0].message.content.strip()
    if sql.startswith("```"):
        sql = sql.replace("```sql", "").replace("```", "").strip()
    state['query'] = sql
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
        "Which countries had the highest life ladder scores in 2020?",
        "Compare the average life ladder score between Western Europe and Sub-Saharan Africa in 2021. Which region had the higher score?",
        "Which countries in Latin America had above-average social support and also experienced below-average negative affect in 2020?",
        "Which countries showed a consistent increase in confidence in national government every year from 2018 to 2021?",
        "Find countries where positive affect was above 0.7 and negative affect was below 0.3 in 2021.",
        "What are the top 3 countries with the highest freedom to make life choices among those with a life ladder score below 5 in 2019?"
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
            logger.info(f"Generation time for question {idx}: {gen_time:.2f} seconds")
            print(f"Generation time for question {idx}: {gen_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error processing question {idx}: {e}")