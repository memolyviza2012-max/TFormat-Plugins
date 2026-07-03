import os
import csv
import json

def convert_to_csv(filepath, parent_widget=None):
    with open(filepath, 'r', encoding='utf-8') as f:
        jdata = json.load(f)
        
    entries = []
    
    # 1. c2dictionary (Construct 2/3)
    if isinstance(jdata, dict) and jdata.get("c2dictionary") is True and "data" in jdata:
        for k, v in jdata["data"].items():
            entries.append((k, str(v)))
            
    # 2. Flat dict: {"key": "value"}
    elif isinstance(jdata, dict):
        for k, v in jdata.items():
            if isinstance(v, (str, int, float, bool)):
                entries.append((k, str(v)))
                
    # 3. List of dicts
    elif isinstance(jdata, list):
        for i, item in enumerate(jdata):
            if isinstance(item, dict):
                if "id" in item and "text" in item:
                    entries.append((str(item["id"]), str(item["text"])))
                elif "key" in item and "value" in item:
                    entries.append((str(item["key"]), str(item["value"])))
                else:
                    entries.append((f"row_{i}", json.dumps(item, ensure_ascii=False)))
            elif isinstance(item, str):
                entries.append((f"row_{i}", item))
                
    if not entries:
        raise ValueError(f"ไม่พบรูปแบบ JSON ที่รองรับในไฟล์ {os.path.basename(filepath)}")
        
    base = os.path.splitext(filepath)[0]
    csv_out = base + '_parsed.csv'
    
    with open(csv_out, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Source", "Translation", "AI_Reference"])
        for lid, text in entries:
            writer.writerow([lid, text, '', ''])
            
    return csv_out
