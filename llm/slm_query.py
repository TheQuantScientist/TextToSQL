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

TABLE_NAME = "finance_economics"

OUTPUT_DIR = os.path.join(
     os.path.dirname(__file__),
     "..", "query", "output", "cogito:3b", "finance_economics", "pred_sql"
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
    "The inflation rate of November 28, 2008",
    "The open price, close price, trading volume of Feb 20, 2000",
    "The gold price, crude oil price, real estate index of Jan 1, 2008",
    "The consumer confidence index of 24 December, 2007",
    "The date, stock index on which stock index reached the highest Daily High",
    "The date, gold price, crude oil price and gdp growth where unemployment rate reached the highest",
    "The date, forex US/EUR, US/JPY where gdp growth is negative",
    "The date where trading volumne is the largest",
    "The date, consumer confidence index, consumer spending where the bankruptcy rate is highest",
    "The unemployment rate, interest rate, inflation rate, the date where Dow Jones has top trading volume",
    "Number of days which the closing price is higher than the open price of Dow Jones, S&P 500, NASDAQ",
    "The annual consumer spending from 2000 to 2008",
    "The annual growth rate of consumer confidence index from 2000 to 2008",
    "Ratio of days having negative gdp growth to total days",
    "The average bankruptcy rate and M&A deals by year",
    "Number of days where the gdp growth is negative",
    "Average monthly trading volume of NASDAQ, S&P 500, Dow Jones",
    "Which year has the highest average consumer confidence index?",
    "The annual average venture capital funding by year",
    "The ratio of government debt to consumer spending by year",
    "Average gold price by year",
    "2008 was the year of global financial crisis. Evaluate some indicators that signaled this recession, and propose a risk mitigation strategy for stock investing",
    "Does government debt effect GDP growth? Analyze the given data and recommend policymakers on how to create positive gdp growth",
    "Low interest rate leads to risky money flow into stock and consumer spending. Evaluate the data to verify the accuracy of this statement. ",
    "Analyze the past performance of all the asset types, stock, commodity, real estate, forex and propose which type of asset is worth to invest in based on investors' risk apetite",
    "Evaluate the relationship between inflation rate and consumer spending",
    "Which stock indexes should investors invest in? Analyze NASDAQ, S&P 500, Dow Jones performances",
    "What is the relationship between interest rate, unemployment rate and corporate profits? Propose strategy for policymakers to promote corporate activities",
    "venture capital funding is private fundraising, wheras stock index activities is public fundraising. Which fundraising channel is more active in US, explain the reasons",
    "Recommend asset classes to invest when the USD currency is appreciated, and when it is depreciated",
    "When it is best to invest in real estate in terms of interest rate environment, stock performance and unemployment context?"
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
                if local_tablename == 'finance_economics':
                    local_tablename = 'finance_economics'
                model_output = os.path.join(
                    os.path.dirname(__file__),
                    "..", "query", "output", model, local_tablename, "pred_sql"
                )
                save_ground_truth(state, idx, gen_time, model_output)
                logger.info(f"Saved: {model_output}/question_{idx}.json")
            except Exception as e:
                logger.error(f"Error processing question {idx}: {e}")
