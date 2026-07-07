import os
import sys
import csv
import UnityPy

def unpack_fantasian(input_file, output_csv=None):
    if not output_csv:
        output_csv = os.path.splitext(input_file)[0] + ".csv"

    print(f"Loading {input_file}...")
    env = UnityPy.load(input_file)
    
    extracted = []
    
    for obj in env.objects:
        if obj.type.name == 'MonoBehaviour':
            try:
                tree = obj.read_typetree()
                if 'messageDictionary' in tree and 'entries' in tree['messageDictionary']:
                    entries = tree['messageDictionary']['entries']
                    for entry in entries:
                        key = entry.get('key', '')
                        val_dict = entry.get('value', {})
                        message = val_dict.get('Message', '')
                        if key and message:
                            extracted.append([key, message, "", ""])
            except Exception as e:
                # Some MonoBehaviours don't have typetrees or are not messageDictionaries
                pass
                    
    if not extracted:
        print("Error: No messageDictionary entries found in this file.")
        return False
        
    print(f"Extracted {len(extracted)} translation strings.")
    
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Source", "Translation", "AI_Reference"])
        for row in extracted:
            writer.writerow(row)
            
    print(f"Successfully saved to {output_csv}")
    return True

if __name__ == '__main__':
    print("--- Fantasian Unpacker ---")
    if len(sys.argv) < 2:
        print("Usage: python Fantasian_unpacker.py <input_bundle> [output.csv]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        sys.exit(1)
        
    unpack_fantasian(input_file, output_csv)
