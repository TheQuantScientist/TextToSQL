import json
import os
import sqlparse
from difflib import SequenceMatcher
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def load_sql_from_json(file_path):
    """Load SQL query from JSON file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get('query', '')
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return ''

def fuzzy_string_similarity(gold_sql, pred_sql):
    """Calculate Fuzzy String Similarity score using Levenshtein ratio."""
    try:
        gold_normalized = ' '.join(gold_sql.strip().lower().split())
        pred_normalized = ' '.join(pred_sql.strip().lower().split())
        matcher = SequenceMatcher(None, gold_normalized, pred_normalized)
        return matcher.ratio()
    except Exception as e:
        print(f"Error in fuzzy string similarity: {e}")
        return 0.0

def ast_similarity(gold_sql, pred_sql):
    """Calculate AST Similarity score."""
    try:
        gold_ast = sqlparse.parse(gold_sql)[0]
        pred_ast = sqlparse.parse(pred_sql)[0]
        
        def ast_to_string(node):
            return str(node).lower()
        
        gold_str = ast_to_string(gold_ast)
        pred_str = ast_to_string(pred_ast)
        
        matcher = SequenceMatcher(None, gold_str, pred_str)
        return matcher.ratio()
    except Exception as e:
        print(f"Error in AST similarity: {e}")
        return 0.0

def jaccard_component_similarity(gold_sql, pred_sql):
    """Calculate Jaccard Component Similarity score."""
    try:
        gold_parsed = sqlparse.parse(gold_sql)[0]
        pred_parsed = sqlparse.parse(pred_sql)[0]
        
        def extract_components(parsed_query):
            components = {
                'select': set(), 'from': set(), 'where': set(), 'join': set(), 'group_by': set(), 'order_by': set()
            }
            tokens = parsed_query.tokens
            i = 0
            while i < len(tokens):
                token = tokens[i]
                if isinstance(token, sqlparse.sql.Token) and token.ttype and 'keyword' in str(token.ttype).lower():
                    value = str(token).lower()
                    if value in ['select', 'from', 'where', 'join', 'group by', 'order by']:
                        j = i + 1
                        while j < len(tokens) and tokens[j].ttype in (sqlparse.tokens.Whitespace, sqlparse.tokens.Comment):
                            j += 1
                        if j < len(tokens):
                            key = value.replace(' ', '_')
                            comp_str = str(tokens[j]).strip().lower()
                            if key == 'where':
                                components[key].update([c.strip() for c in re.split(r'\s+and\s+|\s+or\s+', comp_str)])
                            else:
                                components[key].add(comp_str)
                        i = j if j > i else i + 1
                    else:
                        i += 1
                else:
                    i += 1
            return components
        
        gold_components = extract_components(gold_parsed)
        pred_components = extract_components(pred_parsed)
        
        def jaccard(a, b):
            if not a and not b:
                return 1.0
            intersection = len(a & b)
            union = len(a | b)
            return intersection / union if union > 0 else 0.0
        
        similarities = []
        for component in gold_components:
            if gold_components[component] or pred_components[component]:
                similarities.append(jaccard(gold_components[component], pred_components[component]))
        
        return np.mean(similarities) if similarities else 0.0
    except Exception as e:
        print(f"Error in Jaccard component similarity: {e}")
        return 0.0

def fuzzy_logical_form_similarity(gold_sql, pred_sql):
    """Calculate Fuzzy Logical Form Similarity score."""
    try:
        def extract_logical_form(sql):
            form = {
                'columns': [],
                'tables': [],
                'conditions': []
            }
            select_pattern = r'SELECT\s+(.+?)\s+FROM'
            from_pattern = r'FROM\s+(.+?)(?:\s+WHERE|\s+JOIN|$)'
            where_pattern = r'WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|$)'
            
            select_match = re.search(select_pattern, sql, re.IGNORECASE)
            from_match = re.search(from_pattern, sql, re.IGNORECASE)
            where_match = re.search(where_pattern, sql, re.IGNORECASE)
            
            if select_match:
                form['columns'] = [col.strip().lower() for col in select_match.group(1).split(',')]
            if from_match:
                form['tables'] = [tbl.strip().lower() for tbl in from_match.group(1).split(',')]
            if where_match:
                form['conditions'] = [cond.strip().lower() for cond in where_match.group(1).split('AND')]
            
            return form
        
        gold_form = extract_logical_form(gold_sql)
        pred_form = extract_logical_form(pred_sql)
        
        def average_fuzzy_similarity(gold_list, pred_list):
            if not gold_list and not pred_list:
                return 1.0
            if not gold_list or not pred_list:
                return 0.0
            similarities = []
            for g in gold_list:
                max_sim = max(SequenceMatcher(None, g, p).ratio() for p in pred_list)
                similarities.append(max_sim)
            return np.mean(similarities)
        
        similarities = []
        for key in ['columns', 'tables', 'conditions']:
            sim = average_fuzzy_similarity(gold_form[key], pred_form[key])
            similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    except Exception as e:
        print(f"Error in fuzzy logical form similarity: {e}")
        return 0.0

def cosine_similarity_score(gold_sql, pred_sql):
    """Calculate Cosine Similarity score using sentence-transformers."""
    try:
        model = SentenceTransformer('all-mpnet-base-v2')
        gold_embedding = model.encode(gold_sql.strip(), convert_to_tensor=False)
        pred_embedding = model.encode(pred_sql.strip(), convert_to_tensor=False)
        similarity = cosine_similarity([gold_embedding], [pred_embedding])[0][0]
        return float(similarity)
    except Exception as e:
        print(f"Error in cosine similarity: {e}")
        return 0.0

def evaluate_sql_metrics(gold_path, pred_path):
    """Evaluate all metrics for given gold and predicted SQL queries."""
    gold_sql = load_sql_from_json(gold_path)
    pred_sql = load_sql_from_json(pred_path)
    
    if not gold_sql or not pred_sql:
        return {
            'fuzzy_string_similarity': 0.0,
            'ast_similarity': 0.0,
            'jaccard_component_similarity': 0.0,
            'fuzzy_logical_form_similarity': 0.0,
            'cosine_similarity': 0.0
        }
    
    metrics = {
        'fuzzy_string_similarity': fuzzy_string_similarity(gold_sql, pred_sql),
        'ast_similarity': ast_similarity(gold_sql, pred_sql),
        'jaccard_component_similarity': jaccard_component_similarity(gold_sql, pred_sql),
        'fuzzy_logical_form_similarity': fuzzy_logical_form_similarity(gold_sql, pred_sql),
        'cosine_similarity': cosine_similarity_score(gold_sql, pred_sql)
    }
    
    return metrics

def main():
    base_path = r"/Users/admin/LG/TextToSQL/query/output"
    
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
    
    datasets = ['country_income', 'finance_economics', 'global_development', 'happiness_record']

    for model in models:
        for dataset in datasets:
            gold_dir = os.path.join(base_path, model, dataset, 'gold_sql')
            pred_dir = os.path.join(base_path, model, dataset, 'pred_sql')
            
            if os.path.exists(gold_dir) and os.path.exists(pred_dir):
                gold_files = [f for f in os.listdir(gold_dir) if f.endswith('.json')]
                pred_files = [f for f in os.listdir(pred_dir) if f.endswith('.json')]
                
                gold_files.sort()
                pred_files.sort()
                
                max_questions = min(31, len(gold_files), len(pred_files))
                
                all_metrics = {}
                
                for i in range(max_questions):
                    gold_file = os.path.join(gold_dir, gold_files[i])
                    pred_file = os.path.join(pred_dir, pred_files[i])
                    
                    metrics = evaluate_sql_metrics(gold_file, pred_file)
                    question_key = f"question_{i + 1}"
                    all_metrics[question_key] = metrics
                
                output_dir = os.path.join(base_path, model, dataset, 'comparison')
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, 'metrics.json')
                
                with open(output_file, 'w') as f:
                    json.dump(all_metrics, f, indent=4)
                print(f"Metrics saved to {output_file} for Model: {model}, Dataset: {dataset}")
            else:
                print(f"Directories not found for Model: {model}, Dataset: {dataset}")

if __name__ == "__main__":
    main()