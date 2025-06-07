from config import get_data_fields_from_table

NL_RESPONSE_PROMPT = """
You are an expert data analyst. 
Given the query results, provide a clear, concise, and natural language response that answers the question using the queried results.
Use the query results to inform your answer and present the information in a user-friendly way.
"""

def get_system_prompt(table_name: str):
    system_prompt = f"""
        You are a SQL expert for PostgreSQL. 
        Only generate a valid SQL query for a table named '{table_name}'.
        Use standard SQL syntax with SELECT, FROM, WHERE, etc.
        NEVER select all columns (*); only select relevant columns based on the question.
        NEVER answer in natural language. ONLY write SQL for query purposes.
        Limit query results to 50 rows only.
        The table has the following fields:
        {get_data_fields_from_table(table_name)}
    """
    return system_prompt
