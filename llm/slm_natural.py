import os
import re
import sys
import json
import time
import glob
import logging
from datetime import datetime, date
from decimal import Decimal

# ================== CONFIG ==================
BASE_PATH = r"/Users/ngannguyen/Documents/GitHub/TextToSQL/query/output"


models = [
    'cogito:3b',
    'deepseek-r1:7b',
    'gemma3:4b',
    'gemma3n:e4b',
    'llama3.2',
    'mistral:7b',
    'phi3.5:3.8b',
    'phi4-mini:3.8b',
    'qwen2.5:3b',
    'qwen3:4b',
]

DATASETS = ['country_income', 
    'finance_economics', 
    'global_development', 
    'happiness_record']


DATASET_NAME_MAP = {
    "finance_economics":"finance_economics_dataset",
    "country_income": "country_income",
    "global_development": "global_development_indicators",
    "happiness_record":"world_happiness_report",
}

# Python paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from utils.db_utils import get_db_connection
from utils.agent import (
    query_execution_node,
    response_generation_node,
)

# ================= LOGGER ===================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("natural_response_runner")

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
    pred_dir = os.path.join(BASE_PATH, model, dataset, "pred_sql")
    out_dir  = os.path.join(BASE_PATH, model, dataset, "natural_res")
    if not os.path.isdir(pred_dir):
        return [], pred_dir, out_dir

    pred_files = list_json_files(pred_dir)
    if not pred_files:
        return [], pred_dir, out_dir

    existing = set(basename_without_ext(p) for p in list_json_files(out_dir)) if os.path.isdir(out_dir) else set()
    pendings = [p for p in pred_files if basename_without_ext(p) not in existing]
    return pendings, pred_dir, out_dir

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

    # 2) Generate natural answer
    nlp_start = time.time()
    try:
        state["nlp_start_time"] = time.time()
        state = response_generation_node(state)
        state["nlp_generation_time"] = round(time.time() - nlp_start, 4)
    except Exception as e:
        logger.error(f"[{qkey}] Answer generation failed: {e}")
        state["final_answer"] = "Failed to generate a natural-language answer."
        state["nlp_generation_time"] = round(time.time() - nlp_start, 4)

    total_time = (state.get("sql_execution_time") or 0) + (state.get("nlp_generation_time") or 0)

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
    pending, pred_dir, out_dir = pending_files_for_dataset(model, dataset)
    logger.info(f"[{model}] [{dataset}] pending={len(pending)} | pred_dir={pred_dir} | out_dir={out_dir}")
    if not pending:
        return 0

    ok = 0
    for fp in pending:
        try:
            table_name = DATASET_NAME_MAP.get(dataset, dataset)
            run_one_file(fp, out_dir, table_name, model_for_answer=model)
            ok += 1
        except Exception as e:
            logger.exception(f"Failed processing {fp}: {e}")
    return ok

def run_one_model_then_stop(model: str) -> int:
 
    logger.info("=" * 80)
    logger.info(f"RUN MODEL: {model} (answer_model = same)")
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
        logger.error("Database connection failed. Check your PostgreSQL config in utils/db_utils.py")
        sys.exit(1)
    conn.close()

    # Find first model that is pending, then run and stop
    selected = None
    for m in models:

        has_pending = False
        for d in DATASETS:
            pending, _, _ = pending_files_for_dataset(m, d)
            if pending:
                has_pending = True
                break
        if has_pending:
            selected = m
            break

    if selected is None:
        logger.info("No pending work in any model/dataset. Nothing to do.")
        return

    run_one_model_then_stop(selected)

if __name__ == "__main__":
    main()