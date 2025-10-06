import os
import re
import sys
import json
import time
import glob
import logging
from datetime import datetime, date
from decimal import Decimal


BASE_PATH = r"D:\AI Practice\project_TextToSQL\TextToSQL\query\output"

MODELS = [
    'cogito-3b',
    'deepseek-r1-7b',
    'gemma3-4b',
    'gemma3n-e4b',
    'llama3.2-3b',
    'mistral-7b',
    'phi3.5-3.8b',
    'phi4-mini-3.8b',
    'qwen2.5-3b',
    'qwen3-4b',
]

DATASETS = ['country_income', 'finance_economics', 'global_development', 'happiness_record']

MODEL_FOR_ANSWER = 'gemma3:4b'

USE_SAME_MODEL_FOR_ANSWER = False


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from utils.db_utils import get_db_connection 
from utils.agent import (
    query_execution_node,
    response_generation_node,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("run_from_gold_loop")

# ---------- Helpers ----------

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

# ---------- Core runner ----------

def run_one_file(
    file_path: str,
    output_dir: str,
    table_name: str,
    model_for_answer: str,
):

    gold = load_gold_json(file_path)
    question = gold["question"]
    sql = gold["query"]
    qkey = parse_question_index(file_path)

    logger.info(f"[{qkey}] Running SQL from: {os.path.basename(file_path)}")
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

    sql_start = time.time()
    try:
        state["sql_start_time"] = time.time()
        state = query_execution_node(state) 
    except Exception as e:
        logger.error(f"[{qkey}] SQL execution failed: {e}")
        state["query_result"] = {"error": str(e)}
        state["sql_execution_time"] = round(time.time() - sql_start, 4)

   
    nlp_start = time.time()
    try:
        state["nlp_start_time"] = time.time()
        state = response_generation_node(state) 
    except Exception as e:
        logger.error(f"[{qkey}] Answer generation failed: {e}")
        state["final_answer"] = "Failed to generate a natural-language answer."
        state["nlp_generation_time"] = round(time.time() - nlp_start, 4)

    total_time = (state.get("sql_execution_time") or 0) + (state.get("nlp_generation_time") or 0)

    # Output JSON
    output_payload = {
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

    out_path = save_output(output_dir, qkey, output_payload)
    logger.info(f"[{qkey}] Saved -> {out_path}\n")
    return out_path

def list_json_files(input_dir: str) -> list[str]:
    pattern = os.path.join(input_dir, "*.json")
    def _sort_key(p: str):
        idx = parse_question_index(p)
        return (idx.isdigit(), int(idx) if idx.isdigit() else 1, p)
    return sorted(glob.glob(pattern), key=_sort_key)

def run_folder(input_dir: str, output_dir: str, table_name: str, model_for_answer: str) -> int:
   
    files = list_json_files(input_dir)
    if not files:
        logger.warning(f"No JSON files found in: {input_dir}")
        return 0

    logger.info(f"[{table_name}] Found {len(files)} file(s) in {input_dir}. Output -> {output_dir}")
    success = 0
    for fp in files:
        try:
            run_one_file(fp, output_dir, table_name, model_for_answer)
            success += 1
        except Exception as e:
            logger.exception(f"Failed processing {fp}: {e}")
    return success

def main():
    
    conn = get_db_connection()
    if conn is None:
        logger.error("Database connection failed. Check your PostgreSQL config in utils/db_utils.py")
        sys.exit(1)
    conn.close()

    grand_total = 0
    grand_ok = 0

    for model in MODELS:
        for dataset in DATASETS:
            
            input_dir = os.path.join(BASE_PATH, model, dataset, "pred_sql")
            output_dir = os.path.join(BASE_PATH, model, dataset, "natural_res")

            logger.info("=" * 80)
            logger.info(f"MODEL: {model} | TABLE: {dataset}")
            logger.info(f"Input:  {input_dir}")
            logger.info(f"Output: {output_dir}")

            if not os.path.isdir(input_dir):
                logger.warning(f"Skip (not found): {input_dir}")
                continue

            model_for_answer = model if USE_SAME_MODEL_FOR_ANSWER else MODEL_FOR_ANSWER

            ok = run_folder(input_dir, output_dir, dataset, model_for_answer=model_for_answer)
            total_files = len(list_json_files(input_dir))
            grand_ok += ok
            grand_total += total_files

    logger.info("=" * 80)
    logger.info(f"ALL DONE. Success: {grand_ok}/{grand_total} file(s) across {len(MODELS)} model(s) × {len(DATASETS)} table(s).")

if __name__ == "__main__":
    main()
