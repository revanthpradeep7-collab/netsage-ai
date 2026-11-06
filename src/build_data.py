import os
import json
import csv
from src.cases_data import CASES

def build_datasets():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    json_path = os.path.join(data_dir, "cases.json")
    csv_path = os.path.join(data_dir, "cases.csv")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(CASES, f, indent=2)
        
    fieldnames = [
        "case_id", "title", "symptom", "topology_note", "show_outputs", 
        "expected_fault", "osi_layer", "concept_tag", "severity", 
        "recommended_fix_steps", "verification_command"
    ]
    
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in CASES:
            writer.writerow(c)
            
    print(f"Successfully generated {len(CASES)} cases in:")
    print(f" - JSON: {json_path}")
    print(f" - CSV:  {csv_path}")

if __name__ == "__main__":
    build_datasets()