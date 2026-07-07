import os
import sys
import csv
import re

def pack_alien_isolation(input_csv, original_txt, output_txt=None):
    if not output_txt:
        output_txt = os.path.splitext(original_txt)[0] + "_patched.TXT"

    print(f"Loading translations from {input_csv}...")
    translations = {}
    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get("ID", "").strip()
            translation = row.get("Translation", "").strip()
            source = row.get("Source", "").strip()
            if key:
                translations[key] = translation if translation else source
                
    if not translations:
        print("Error: No translations found in CSV.")
        return False

    print(f"Loading original TXT {original_txt}...")
    # Determine encoding by sniffing BOM
    with open(original_txt, 'rb') as f:
        raw_bytes = f.read(4)
        
    if raw_bytes.startswith(b'\xff\xfe'):
        encoding = 'utf-16-le'
        has_bom = True
    elif raw_bytes.startswith(b'\xfe\xff'):
        encoding = 'utf-16-be'
        has_bom = True
    else:
        encoding = 'utf-8-sig'
        has_bom = False
        
    with open(original_txt, 'r', encoding=encoding, errors='replace') as f:
        raw_text = f.read()
    
    modified_count = 0
    
    # We will use regex to find each block and replace the content.
    # Pattern: [KEY]\n{VALUE}
    def replace_block(match):
        nonlocal modified_count
        key = match.group(1).strip()
        original_value = match.group(2)
        
        if key in translations:
            new_value = translations[key]
            if new_value != original_value.strip():
                modified_count += 1
            return f"[{key}]\n{{{new_value}}}"
        return match.group(0) # Keep original
        
    patched_text = re.sub(r'\[(.*?)\]\s*\n\s*\{(.*?)\}', replace_block, raw_text, flags=re.DOTALL)
                    
    if modified_count == 0:
        print("Warning: No strings were replaced. Did the IDs match?")
    else:
        print(f"Replaced {modified_count} strings.")
        
    print(f"Saving to {output_txt} (Encoding: {encoding})...")
    # Python's 'utf-16-le' doesn't write BOM automatically, but if we use 'utf-16', it writes LE with BOM on Windows.
    # We should explicitly write the BOM if the original had it.
    with open(output_txt, 'wb') as f:
        if encoding == 'utf-16-le' and has_bom:
            f.write(b'\xff\xfe')
        elif encoding == 'utf-16-be' and has_bom:
            f.write(b'\xfe\xff')
            
    with open(output_txt, 'a', encoding=encoding) as f:
        f.write(patched_text)
        
    print("Successfully saved!")
    return True

if __name__ == '__main__':
    print("--- Alien: Isolation Packer ---")
    if len(sys.argv) < 3:
        print("Usage: python Alien_packer.py <translated.csv> <original.TXT> [output.TXT]")
        sys.exit(1)
        
    input_csv = sys.argv[1]
    original_txt = sys.argv[2]
    output_txt = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        sys.exit(1)
        
    if not os.path.exists(original_txt):
        print(f"File not found: {original_txt}")
        sys.exit(1)
        
    pack_alien_isolation(input_csv, original_txt, output_txt)
