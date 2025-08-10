
import os
import re

def count_files(models, table_name, output_dir):
    for model in models:
        pred_path = f"{output_dir}/{model}/{table_name}/pred_sql"
        comp_path = f"{output_dir}/{model}/{table_name}/comparison"
        
        # Count pred_sql files
        pred_count = 0
        if os.path.exists(pred_path):
            pred_count = len([f for f in os.listdir(pred_path) if re.match(r'question_\d+\.json$', f)])
        
        # Count comparison files
        comp_count = 0
        if os.path.exists(comp_path):
            comp_count = len([f for f in os.listdir(comp_path) if f == "metrics.json"])
        
        # Print with emoji based on comparison count
        comp_emoji = "✅" if comp_count == 1 else "❓"
        print(f"{model}: Num Question: {pred_count}, Comparison: {comp_emoji}")

        if pred_count <31:
            print ("Missing questions")

# Input - modify these directly
models = ['cogito:3b',
        'deepseek-r1:7b',
        'gemma3:4b',
        'gemma3n:e4b',
        'llama3.2:latest',
        'mistral:7b',
        'phi3.5:3.8b',
        'phi4-mini:3.8b',
        'qwen2.5:3b',
        'qwen3:4b', ]

table_name = "happiness_record"
output_dir = "/Users/ngannguyen/Documents/GitHub/TextToSQL/query/output"

# Output
count_files(models, table_name, output_dir)