import os
import re
import sys
import json
import time
import glob
import logging
from datetime import datetime, date
from decimal import Decimal
from groq import Groq  # Import Groq API client

from dotenv import load_dotenv
load_dotenv()

# ================== CONFIG ==================
BASE_PATH = r"/Users/ngannguyen/Documents/GitHub/TextToSQL/query/output"
GOLD_MODEL = "openai/gpt-oss-120b"  # Model for natural response via Groq API

# Prompt from /Users/admin/LG/TextToSQL/prompt/prompts.py
NL_RESPONSE_PROMPT = """
You are an expert data analyst. 
Given the query results, provide a clear, concise, and natural language response that answers the question using the queried results.
Use the query results to inform your answer and present the information in a user-friendly way.
"""

models = [
    'cogito:3b',  # Only process gemma3:4b as specified
]

DATASETS = [
    'country_income',
    'finance_economics',
    'global_development',
    'happiness_record'
]

DATASET_NAME_MAP = {
    "finance_economics": "finance_economics_dataset",
    "country_income": "country_income",
    "global_development": "global_development_indicators",
    "happiness_record": "world_happiness_report",
}

# Python paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from utils.db_utils import get_db_connection
from utils.agent import query_execution_node

# ================= LOGGER ===================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gold_natural_response_runner")

# ================= GROQ API RESPONSE GENERATION ==================
def groq_response_generation_node(state):
    """Wrapper for response_generation_node using Groq API with gpt-oss-120b and original NL_RESPONSE_PROMPT."""
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # Ensure GROQ_API_KEY is set
        question = state["question"]
        query_result = state["query_result"]

        # Use the exact NL_RESPONSE_PROMPT with question and query results
        prompt = f"{NL_RESPONSE_PROMPT}\n\nQuestion: {question}\nQuery Results: {json.dumps(ensure_jsonable(query_result), ensure_ascii=False)}"

        # Call Groq API with gpt-oss-120b
        response = client.chat.completions.create(
            model=GOLD_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant and expert data analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )

        state["final_answer"] = response.choices[0].message.content.strip()
        return state
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        state["final_answer"] = "Failed to generate a natural-language answer via Groq API."
        return state

# ================= HELPERS ==================
def ensure_jsonable(obj):
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: ensure_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [ensure_jsonable(x) for x in obj]
    return str(obj)

def parse_question_index(filename: str) -> str:
    m = re.search(r"question_(\d+)\.json$", filename, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    base = os.path.splitext(os.path.basename(filename))[0]
    return re.sub(r'[^0-9a-zA-Z_-]+', '_', base)

def load_gold_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "question" not in data or "query" not in data:
        raise ValueError(f"Missing required keys in {path}. Need 'question' and 'query'.")
    if isinstance(data["query"], str):
        data["query"] = " ".join(data["query"].split())
    return data

def save_output(output_dir: str, question_key: str, payload: dict):
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"question_{question_key}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(ensure_jsonable(payload), f, ensure_ascii=False, indent=4)
    return out_path

def list_json_files(dir_path: str):
    pattern = os.path.join(dir_path, "*.json")
    files = glob.glob(pattern)
    files.sort()
    return files

def basename_without_ext(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]

def pending_files_for_dataset(model: str, dataset: str):
    gold_dir = os.path.join(BASE_PATH, model, dataset, "gold_sql")
    out_dir = os.path.join(BASE_PATH, model, dataset, "gold_natural_res")
    if not os.path.isdir(gold_dir):
        return [], gold_dir, out_dir

    gold_files = list_json_files(gold_dir)
    if not gold_files:
        return [], gold_dir, out_dir

    existing = set(basename_without_ext(p) for p in list_json_files(out_dir)) if os.path.isdir(out_dir) else set()
    pendings = [p for p in gold_files if basename_without_ext(p) not in existing]
    return pendings, gold_dir, out_dir

# ================= CORE =====================
def run_one_file(file_path: str, output_dir: str, table_name: str, model_for_answer: str):
    gold = load_gold_json(file_path)
    question = gold["question"]
    sql = gold["query"]
    qkey = parse_question_index(file_path)

    logger.info(f"[{qkey}] Q: {question}")
    logger.debug(f"[{qkey}] SQL: {sql}")

    state = {
        "question": question,
        "table_name": table_name,
        "query": sql,
        "query_result": "",
        "final_answer": "",
        "model": model_for_answer,
    }

    # 1) Execute SQL
    sql_start = time.time()
    try:
        state["sql_start_time"] = time.time()
        state = query_execution_node(state)
        state["sql_execution_time"] = round(time.time() - sql_start, 4)
    except Exception as e:
        logger.error(f"[{qkey}] SQL execution failed: {e}")
        state["query_result"] = {"error": str(e)}
        state["sql_execution_time"] = round(time.time() - sql_start, 4)

    # 2) Generate natural answer using Groq API
    nlp_start = time.time()
    try:
        state["nlp_start_time"] = time.time()
        state = groq_response_generation_node(state)  # Use Groq wrapper with NL_RESPONSE_PROMPT
        state["nlp_generation_time"] = round(time.time() - nlp_start, 4)
    except Exception as e:
        logger.error(f"[{qkey}] Answer generation failed: {e}")
        state["final_answer"] = "Failed to generate a natural-language answer."
        state["nlp_generation_time"] = round(time.time() - nlp_start, 4)

    total_time = (state.get("sql_execution_time", 0) + state.get("nlp_generation_time", 0))

    payload = {
        "question": state.get("question"),
        "query": state.get("query"),
        "raw_results": state.get("query_result"),
        "answer": state.get("final_answer"),
        "sql_execution_time": round(state.get("sql_execution_time", 0), 4),
        "nlp_generation_time": round(state.get("nlp_generation_time", 0), 4),
        "total_time": round(total_time, 4),
        "source_file": os.path.basename(file_path),
        "table_name": table_name,
        "model_for_answer": model_for_answer,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    out_path = save_output(output_dir, qkey, payload)
    logger.info(f"[{qkey}] Saved -> {out_path}")

def run_dataset(model: str, dataset: str) -> int:
    pending, gold_dir, out_dir = pending_files_for_dataset(model, dataset)
    logger.info(f"[{model}] [{dataset}] pending={len(pending)} | gold_dir={gold_dir} | out_dir={out_dir}")
    if not pending:
        return 0

    ok = 0
    for fp in pending:
        try:
            table_name = DATASET_NAME_MAP.get(dataset, dataset)
            run_one_file(fp, out_dir, table_name, model_for_answer=GOLD_MODEL)
            ok += 1
        except Exception as e:
            logger.exception(f"Failed processing {fp}: {e}")
    return ok

def run_one_model_then_stop(model: str) -> int:
    logger.info("=" * 80)
    logger.info(f"RUN MODEL: {model} (answer_model = {GOLD_MODEL})")
    total_ok = 0
    for dataset in DATASETS:
        ok = run_dataset(model, dataset)
        total_ok += ok
    logger.info(f"DONE MODEL: {model} | processed={total_ok}")
    return total_ok

# ================= MAIN =====================
def main():
    # DB check
    conn = get_db_connection()
    if conn is None:
        logger.error("Database connection failed. Check your PostgreSQL config in utils/db_utils.py'")
        sys.exit(1)
    conn.close()

    # Check for GROQ_API_KEY
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY environment variable not set. Please set it to use the Groq API.")
        sys.exit(1)

    # Run only for gemma3:4b as specified
    selected = 'cogito:3b'
    has_pending = False
    for d in DATASETS:
        pending, _, _ = pending_files_for_dataset(selected, d)
        if pending:
            has_pending = True
            break
    if not has_pending:
        logger.info("No pending gold_sql files for gemma3-4b. Nothing to do.")
        return

    run_one_model_then_stop(selected)

if __name__ == "__main__":
    main()