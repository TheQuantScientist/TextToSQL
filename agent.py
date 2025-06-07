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
    except Exception as e:
        logger.error(f"Response generation failed: {str(e)}")
        traceback.print_exc()
        state['final_answer'] = "Failed to generate response. Please clarify your query."

    return state
