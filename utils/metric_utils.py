import json
import os
import sqlparse
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
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

def exact_match(gold_sql, pred_sql):
    """Calculate Exact Match score."""
    gold_normalized = ' '.join(gold_sql.strip().lower().split())
    pred_normalized = ' '.join(pred_sql.strip().lower().split())
    return 1.0 if gold_normalized == pred_normalized else 0.0

def bleu_score(gold_sql, pred_sql):
    """Calculate BLEU score with smoothing."""
    gold_tokens = gold_sql.strip().lower().split()
    pred_tokens = pred_sql.strip().lower().split()
    reference = [gold_tokens]
    smoothie = SmoothingFunction().method1
    return sentence_bleu(reference, pred_tokens, smoothing_function=smoothie)

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

def component_accuracy(gold_sql, pred_sql):
    """Calculate Component Accuracy score."""
    try:
        gold_parsed = sqlparse.parse(gold_sql)[0]
        pred_parsed = sqlparse.parse(pred_sql)[0]
        
        def extract_components(parsed_query):
            components = {
                'select': [], 'from': [], 'where': [], 'join': [], 'group_by': [], 'order_by': []
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
                            components[key].append(str(tokens[j]).strip())
                        i = j if j > i else i + 1
                    else:
                        i += 1  # Skip unhandled keywords
                else:
                    i += 1
            return components
        
        gold_components = extract_components(gold_parsed)
        pred_components = extract_components(pred_parsed)
        
        total_components = 0
        matching_components = 0
        
        for component in gold_components:
            gold_comp = set(gold_components[component])
            pred_comp = set(pred_components[component])
            if gold_comp:
                total_components += 1
                if gold_comp == pred_comp:
                    matching_components += 1
        
        return matching_components / total_components if total_components > 0 else 0.0
    except Exception as e:
        print(f"Error in component accuracy: {e}")
        return 0.0

def logical_form_accuracy(gold_sql, pred_sql):
    """Calculate Logical Form Accuracy score."""
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
                form['columns'] = [col.strip() for col in select_match.group(1).split(',')]
            if from_match:
                form['tables'] = [tbl.strip() for tbl in from_match.group(1).split(',')]
            if where_match:
                form['conditions'] = [cond.strip() for cond in where_match.group(1).split('AND')]
            
            return form
        
        gold_form = extract_logical_form(gold_sql)
        pred_form = extract_logical_form(pred_sql)
        
        total_elements = 0
        matching_elements = 0
        
        for key in ['columns', 'tables', 'conditions']:
            gold_set = set(gold_form[key])
            pred_set = set(pred_form[key])
            if gold_set:
                total_elements += 1
                if gold_set == pred_set:
                    matching_elements += 1
        
        return matching_elements / total_elements if total_elements > 0 else 0.0
    except Exception as e:
        print(f"Error in logical form accuracy: {e}")
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
            'exact_match': 0.0,
            'bleu': 0.0,
            'ast_similarity': 0.0,
            'component_accuracy': 0.0,
            'logical_form_accuracy': 0.0,
            'cosine_similarity': 0.0
        }
    
    metrics = {
        'exact_match': exact_match(gold_sql, pred_sql),
        'bleu': bleu_score(gold_sql, pred_sql),
        'ast_similarity': ast_similarity(gold_sql, pred_sql),
        'component_accuracy': component_accuracy(gold_sql, pred_sql),
        'logical_form_accuracy': logical_form_accuracy(gold_sql, pred_sql),
        'cosine_similarity': cosine_similarity_score(gold_sql, pred_sql)
    }
    
    return metrics

def main():
    base_path = r"/Users/admin/LG/TextToSQL/query/output"
    
    # Fixed model name (change this manually as needed)
    model = 'gemma3'
    
    # List of datasets
    datasets = ['country_income']
    
    for dataset in datasets:
        gold_dir = os.path.join(base_path, model, dataset, 'gold_sql')
        pred_dir = os.path.join(base_path, model, dataset, 'pred_sql')
        
        if os.path.exists(gold_dir) and os.path.exists(pred_dir):
            # Collect all JSON files
            gold_files = [f for f in os.listdir(gold_dir) if f.endswith('.json')]
            pred_files = [f for f in os.listdir(pred_dir) if f.endswith('.json')]
            
            # Sort files to ensure consistent pairing
            gold_files.sort()
            pred_files.sort()
            
            # Limit to 31 questions (adjust if needed)
            max_questions = min(31, len(gold_files), len(pred_files))
            
            # Dictionary to store all metrics
            all_metrics = {}
            
            for i in range(max_questions):
                gold_file = os.path.join(gold_dir, gold_files[i])
                pred_file = os.path.join(pred_dir, pred_files[i])
                
                metrics = evaluate_sql_metrics(gold_file, pred_file)
                question_key = f"question_{i + 1}"
                all_metrics[question_key] = metrics
            
            # Save metrics to a single JSON file
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
