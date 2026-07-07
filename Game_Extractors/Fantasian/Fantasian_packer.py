import os
import sys
import csv
import UnityPy

def pack_fantasian(input_csv, original_bundle, output_bundle=None):
    if not output_bundle:
        output_bundle = os.path.splitext(original_bundle)[0] + "_patched"

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

    print(f"Loading bundle {original_bundle}...")
    env = UnityPy.load(original_bundle)
    
    modified_count = 0
    
    for obj in env.objects:
        if obj.type.name == 'MonoBehaviour':
            try:
                tree = obj.read_typetree()
                if 'messageDictionary' in tree and 'entries' in tree['messageDictionary']:
                    entries = tree['messageDictionary']['entries']
                    changed = False
                    
                    for entry in entries:
                        key = entry.get('key', '')
                        if key in translations:
                            val_dict = entry.get('value', {})
                            original_msg = val_dict.get('Message', '')
                            new_msg = translations[key]
                            
                            if original_msg != new_msg:
                                entry['value']['Message'] = new_msg
                                changed = True
                                modified_count += 1
                                
                    if changed:
                        obj.save_typetree(tree)
            except Exception as e:
                # Normal for MonoBehaviours that aren't messageDictionaries
                pass
                    
    if modified_count == 0:
        print("Warning: No strings were replaced. Did the IDs match?")
    else:
        print(f"Replaced {modified_count} strings.")
        print(f"Saving to {output_bundle}...")
        with open(output_bundle, 'wb') as f:
            f.write(env.file.save())
        print("Successfully saved!")
        
    return True

if __name__ == '__main__':
    print("--- Fantasian Packer ---")
    if len(sys.argv) < 3:
        print("Usage: python Fantasian_packer.py <translated.csv> <original_bundle> [output_bundle]")
        sys.exit(1)
        
    input_csv = sys.argv[1]
    original_bundle = sys.argv[2]
    output_bundle = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        sys.exit(1)
        
    if not os.path.exists(original_bundle):
        print(f"File not found: {original_bundle}")
        sys.exit(1)
        
    pack_fantasian(input_csv, original_bundle, output_bundle)
