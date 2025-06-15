import json
import re
import os
import sys
from datetime import datetime
import logging
import traceback
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate

sys.path.append('.')

from db_utils import run_query, convert_to_markdown_table
from llm_utils import get_llm_model
from prompt import SQL_QUERY_GEN_PROMPT, NL_RESPONSE_PROMPT, get_system_prompt

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class State(TypedDict):
    question: str
    query: str
    table_name: str
    query_result: str
    final_answer: str

def sql_gen_node(state: State) -> State:
    logger.info('Generating SQL query')
    llm = get_llm_model()
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

def query_execution_node(state: State) -> State:
    logger.info('Executing query')
    raw_result = run_query(state['query'], state['table_name'])
    state['query_result'] = convert_to_markdown_table(raw_result)
    return state

def response_generation_node(state: State) -> State:
    logger.info('Generating natural language response')
    llm = get_llm_model()
    if llm is None:
        state['final_answer'] = "Failed to generate response due to LLM initialization error"
        logger.error("No LLM available for response generation")
        return state

    response_prompt = ChatPromptTemplate.from_messages([
        ("system", NL_RESPONSE_PROMPT),
        ("human", "Question: {question}\nQuery Results:\n{query_result}")
    ])

    response_model = response_prompt | llm

    try:
        final_answer = response_model.invoke({
            "question": state['question'],
            "query_result": state['query_result']
        })
        state['final_answer'] = extract_natural_answer(final_answer) 

    except Exception as e:
        logger.error(f"Response generation failed: {str(e)}")
        traceback.print_exc()
        state['final_answer'] = "Failed to generate response. Please clarify your query."

    return state

# Create and record the output as a JSON file
def save_output_as_json(output: dict, question_index: int, output_dir: str = "outputs"):
    os.makedirs(output_dir, exist_ok=True)
    if "query" in output and isinstance(output["query"], str):
        output["query"] = output["query"].replace('\n', ' ').replace('\r', ' ').strip()
    filename = f"question_{question_index}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    return filepath

# Remove code block markers and extract the natural answer from the final answer
def extract_natural_answer(final_answer):
    
    if isinstance(final_answer, str):
        cleaned = final_answer.strip().strip('`')
        cleaned = re.sub(r'^json\s*', '', cleaned, flags=re.IGNORECASE).strip()
        
        try:
            answer_json = json.loads(cleaned)
            if isinstance(answer_json, dict) and 'answer' in answer_json:
                return answer_json['answer']
        except Exception:
            pass
        
        match = re.search(r'"answer"\s*:\s*"([^"]+)"', cleaned)
        if match:
            return match.group(1)
        return cleaned
    return str(final_answer)