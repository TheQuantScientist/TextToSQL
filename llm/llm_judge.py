import json, os, time, hashlib
from pathlib import Path
from typing import List, Dict
from groq import Groq
from tqdm import tqdm
import pandas as pd

# ========================= CONFIG =========================
BASE_DIR = Path("query/output")
MODEL_NAME = "gpt-oss-120b"
DATASETS = [
    "happiness_record",
    "global_development",
    "finance_economics",
    "country_income"
]
MODEL_FOLDERS = [
    "cogito_3b",
    "deepseek-r1_7b",
    "gemma3_4b",
    "gemma3n_e4b",
    "llama3.2",
    "mistral_7b",
    "phi3.5_3.8b",
    "phi4-mini_3.8b",
    "qwen2.5_3b",
    "qwen3_4b"
]
CACHE_DIR = Path("judge_cache_friendly")
OUTPUT_DIR = Path("judge_results_friendly")
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
BATCH_SIZE = 1
MAX_RETRIES = 3

# =========================================================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# ===================== FRIENDLY PROMPT =====================

SYSTEM_PROMPT = """
You are a user-experience evaluator for chatbot answers.
Your ONLY job is to decide if the answer is friendly, direct, professional, and straightforward.
Return **exactly** a JSON object:
{
  "judgment": "Qualified" or "Unqualified"
}
Qualified – the answer is:
  • Direct and to the point
  • Polite & professional tone
  • Not verbose, no unnecessary filler
  • Easy to read (proper grammar, no typos)
  • User friendly and approachable
Unqualified – the answer:
  • Rambling, repetitive, or overly long
  • Rude, sarcastic, or unprofessional
  • Evasive (doesn’t answer) or full of disclaimers
  • Contains excessive formatting, code, or jargon
Ignore factual correctness or whether a number is present.
"""
# =========================================================

def cache_path(model: str, dataset: str) -> Path:
    safe_m = "".join(c if c.isalnum() else "_" for c in model)
    safe_d = "".join(c if c.isalnum() else "_" for c in dataset)
    return CACHE_DIR / f"cache_{safe_m}_{safe_d}.json"

def load_cache(p: Path) -> Dict[str, str]:
    return json.load(open(p, "r", encoding="utf-8")) if p.exists() else {}

def save_cache(cache: Dict, p: Path):
    json.dump(cache, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def cache_key(q: str, a: str) -> str:
    return hashlib.md5((q + a).encode("utf-8")).hexdigest()

def call_groq(question: str, answer: str, cache: Dict, cpath: Path) -> str:
    key = cache_key(question, answer)
    if key in cache:
        return cache[key]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}\n\nAnswer: {answer}"}
    ]
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.0,
                max_tokens=60,
                response_format={"type": "json_object"}
            )
            data = json.loads(resp.choices[0].message.content.strip())
            judgment = data.get("judgment", "Unqualified")
            cache[key] = judgment
            save_cache(cache, cpath)
            return judgment
        except Exception:
            if attempt == MAX_RETRIES - 1:
                cache[key] = "Unqualified"
                save_cache(cache, cpath)
                return "Unqualified"
            time.sleep(2 ** attempt)
    return "Unqualified"

def load_qa(folder: Path) -> List[Dict]:
    items = []
    for fp in sorted(folder.glob("question_*.json")):
        try:
            d = json.load(open(fp, "r", encoding="utf-8"))
            q, a = d.get("question", "").strip(), d.get("answer", "").strip()
            if q and a:
                items.append({"file": fp.name, "question": q, "answer": a})
        except Exception:
            pass
    return items

def evaluate(model: str, dataset: str):
    res_dir = BASE_DIR / model / dataset / "natural_res"
    if not res_dir.exists():
        return None
    qa = load_qa(res_dir)
    if not qa:
        return None
    cpath = cache_path(model, dataset)
    cache = load_cache(cpath)
    rows = []
    for i in tqdm(range(0, len(qa), BATCH_SIZE), desc="judging", leave=False):
        for item in qa[i:i+BATCH_SIZE]:
            judgment = call_groq(item["question"], item["answer"], cache, cpath)
            rows.append({
                "model": model,
                "dataset": dataset,
                "file": item["file"],
                "question": item["question"],
                "answer": item["answer"],
                "judgment": judgment
            })
        time.sleep(0.1)
    df = pd.DataFrame(rows)
    out_csv = OUTPUT_DIR / f"friendly_{model}_{dataset}.csv"
    df.to_csv(out_csv, index=False)
    total = len(rows)
    qual = sum(1 for r in rows if r["judgment"] == "Qualified")
    return {
        "model": model,
        "dataset": dataset,
        "total": total,
        "qualified": qual,
        "qualified_pct": qual / total * 100 if total else 0
    }

def main():
    summary = []
    for m in MODEL_FOLDERS:
        for d in DATASETS:
            stat = evaluate(m, d)
            if stat:
                summary.append(stat)
    if summary:
        sum_df = pd.DataFrame(summary)
        sum_csv = OUTPUT_DIR / "FRIENDLY_SUMMARY_ALL.csv"
        sum_df.to_csv(sum_csv, index=False)
        print("\n" + "="*70)
        print("OVERALL FRIENDLINESS SUMMARY")
        print("="*70)
        print(sum_df[['model','dataset','total','qualified','qualified_pct']]
              .to_string(index=False, float_format="%.1f"))
        print(f"\nGlobal average Qualified: {sum_df['qualified_pct'].mean():.1f}%")
        print(f"Summary CSV → {sum_csv}")
        print("="*70)

if __name__ == "__main__":
    main()