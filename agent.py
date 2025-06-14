import logging
import traceback
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from db_utils import run_query, convert_to_markdown_table
from llm_utils import get_llm_model
from prompts import get_system_prompt, NL_RESPONSE_PROMPT

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class State(TypedDict):
    question: str
    table_name: str
    query: str
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
        state['final_answer'] = final_answer

        # Export to JSON after successful response generation
        if state['query_result'] and state['query_result'].strip():
            json_filepath = export_to_json(state)
            if json_filepath:
                state['final_answer'] += f"\n\n📁 Query results exported to: {json_filepath}"

    except Exception as e:
        logger.error(f"Response generation failed: {str(e)}")
        traceback.print_exc()
        state['final_answer'] = "Failed to generate response. Please clarify your query."

    return state


import json
import os
from datetime import datetime

def export_to_json(state: State, output_dir: str = "query_exports") -> str:
    """Export query results to JSON file"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"query_results_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Prepare export data
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "question": state['question'],
            "sql_query": state['query'],
            "query_results": state['query_result'],
            "natural_language_response": state['final_answer']
        }
        
        # Write to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Query results exported to: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to export JSON: {str(e)}")
        return ""