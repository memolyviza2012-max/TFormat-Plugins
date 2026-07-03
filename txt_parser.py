import os
import csv
import json
import re

def convert_to_csv(filepath, parent_widget=None):
    base = os.path.splitext(filepath)[0]
    csv_out = base + '_parsed.csv'
    meta_out = base + '_parsed_meta.json'
    
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        raw_text = f.read()
        
    # Heuristic 1: Is it SRT? (Look for index followed by timestamp)
    if re.search(r'\d+\n\d{2}:\d{2}:\d{2}', raw_text):
        # Treat as SRT
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        import srt_parser
        return srt_parser.convert_to_csv(filepath, parent_widget)
        
    # Heuristic 2: Telltale format (N) Character \n Text)
    lines = raw_text.split('\n')
    id_pattern = re.compile(r'^(\d+)\)\s*(.*)')
    entries = []
    
    i = 0
    while i < len(lines):
        m = id_pattern.match(lines[i].strip())
        if m:
            line_id = m.group(1)
            character = m.group(2).strip()
            text = ''
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not id_pattern.match(next_line):
                    text = next_line
                    i += 1
            entries.append((line_id, character, text))
        i += 1
        
    if len(entries) >= 5:
        with open(csv_out, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Source", "Translation", "AI_Reference"])
            for (lid, char, text) in entries:
                if text:
                    row_id = f"{lid}_{char.replace(' ', '_')}" if char else str(lid)
                    writer.writerow([row_id, text, "", char])
        return csv_out
        
    raise ValueError(f"ไม่พบรูปแบบข้อความที่รองรับในไฟล์ .txt นี้ (รองรับเฉพาะ SRT หรือ Telltale format)")
