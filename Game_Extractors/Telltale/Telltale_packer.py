import os
import sys
import csv
import struct
import subprocess
import shutil

# =====================================================================
# Telltale_packer.py
# แพ็คไฟล์แปลกลับเข้าเกม Telltale
# Flow: CSV ที่แปลแล้ว + โฟลเดอร์ที่แตกไว้ → patch 0.ttarch2
# =====================================================================

def find_ttarchext():
    """ค้นหา ttarchext.exe"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    candidates = [
        os.path.join(script_dir, "ttarchext.exe"),
        os.path.join(script_dir, "..", "..", "..", "..", "Core", "telltale_tools", "ttarchext.exe"),
        os.path.join(script_dir, "..", "..", "..", "Core", "telltale_tools", "ttarchext.exe"),
    ]
    
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


def patch_landb(landb_path, translations_by_offset):
    """
    เขียนคำแปลทับลงในไฟล์ .landb binary โดยตรง
    
    Args:
        landb_path (str): path ของไฟล์ .landb ที่จะแก้ไข
        translations_by_offset (dict): {offset_int: translated_text}
    
    Returns:
        int: จำนวนที่แก้ไขสำเร็จ
    """
    with open(landb_path, 'rb') as f:
        data = bytearray(f.read())
    
    # เรียงลำดับจากท้ายไปหน้าเพื่อป้องกัน offset drift
    sorted_offsets = sorted(translations_by_offset.keys(), reverse=True)
    
    patched_count = 0
    for offset in sorted_offsets:
        translated = translations_by_offset[offset]
        if not translated.strip():
            continue
        
        try:
            orig_len = struct.unpack('<I', data[offset:offset+4])[0]
            new_bytes = translated.encode('utf-8')
            new_len = len(new_bytes)
            
            # สลับ length header
            data[offset:offset+4] = struct.pack('<I', new_len)
            # สลับ string content
            data[offset+4: offset+4+orig_len] = new_bytes
            patched_count += 1
        except Exception as e:
            print(f"Warning: Cannot patch offset {offset}: {e}")
    
    with open(landb_path, 'wb') as f:
        f.write(data)
    
    return patched_count


def pack_telltale(input_csv, extracted_folder, output_ttarch=None, game_id=None):
    """
    นำไฟล์ CSV ที่แปลแล้วไปเขียนทับในไฟล์ .landb ที่แตกไว้
    จากนั้นใช้ ttarchext.exe บีบอัดกลับเป็น 0.ttarch2 (patch file)
    
    Args:
        input_csv (str): path ของไฟล์ CSV ที่แปลแล้ว
        extracted_folder (str): โฟลเดอร์ที่แตกไฟล์ไว้ (มีไฟล์ .landb)
        output_ttarch (str): path ของไฟล์ผลลัพธ์ (ถ้าไม่ระบุจะสร้างอัตโนมัติ)
        game_id (int): รหัสเกม (ถ้าไม่ระบุจะใช้ 67)
    
    Returns:
        str: path ของไฟล์ผลลัพธ์
    """
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"ไม่พบไฟล์ CSV: {input_csv}")
    
    if not os.path.exists(extracted_folder):
        raise FileNotFoundError(f"ไม่พบโฟลเดอร์: {extracted_folder}")
    
    # ตั้งค่า output path
    if not output_ttarch:
        output_ttarch = os.path.join(os.path.dirname(extracted_folder), "0.ttarch2")
    
    if game_id is None:
        game_id = 67  # Default: Definitive Series
    
    # --- Step 1: อ่านคำแปลจาก CSV ---
    print(f"Loading translations from: {input_csv}")
    grouped = {}  # {filename: {offset: translated_text}}
    
    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            offset_id = row.get("ID", "").strip()
            translation = row.get("Translation", "").strip()
            source = row.get("Source", "").strip()
            text = translation if translation else source
            
            if not offset_id or not text:
                continue
            
            if ":" in offset_id:
                file_name, offset_str = offset_id.split(":", 1)
                offset = int(offset_str)
            else:
                continue
            
            if file_name not in grouped:
                grouped[file_name] = {}
            grouped[file_name][offset] = text
    
    if not grouped:
        raise ValueError("ไม่พบคำแปลใดๆ ในไฟล์ CSV")
    
    # --- Step 2: สร้างโฟลเดอร์ patch ชั่วคราว ---
    patch_folder = os.path.join(os.path.dirname(extracted_folder), "_patch_tmp")
    if os.path.exists(patch_folder):
        shutil.rmtree(patch_folder)
    os.makedirs(patch_folder)
    
    total_patched = 0
    
    for file_name, translations in grouped.items():
        src_path = os.path.join(extracted_folder, file_name)
        if not os.path.exists(src_path):
            print(f"Warning: ไม่พบไฟล์ {file_name} ในโฟลเดอร์")
            continue
        
        # Copy ไฟล์ไปโฟลเดอร์ patch ชั่วคราว
        dst_path = os.path.join(patch_folder, file_name)
        shutil.copy2(src_path, dst_path)
        
        # Patch ไฟล์ .landb
        if file_name.endswith('.landb'):
            count = patch_landb(dst_path, translations)
            total_patched += count
            print(f"  Patched {count} strings in: {file_name}")
    
    if total_patched == 0:
        shutil.rmtree(patch_folder)
        raise ValueError("ไม่มีข้อความที่ถูก Patch! ตรวจสอบว่า ID ใน CSV ตรงกับไฟล์ .landb หรือไม่")
    
    print(f"\nTotal patched: {total_patched} strings")
    
    # --- Step 3: บีบอัดกลับเป็น .ttarch2 ด้วย ttarchext ---
    ttarchext = find_ttarchext()
    if not ttarchext:
        print("\nWarning: ไม่พบ ttarchext.exe!")
        print("ไฟล์ .landb ที่แก้ไขแล้วถูกเก็บไว้ที่:")
        print(f"  {patch_folder}")
        print("คุณสามารถนำไปบีบอัดเองได้ด้วยคำสั่ง:")
        print(f"  ttarchext.exe -b -V 7 {game_id} output.ttarch2 {patch_folder}")
        return patch_folder
    
    print(f"\nBuilding patch archive: {output_ttarch}")
    cmd = [ttarchext, "-b", "-V", "7", str(game_id), output_ttarch, patch_folder]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    
    if result.returncode != 0:
        print("Warning: Build returned errors. Trying with -x flag...")
        cmd_x = [ttarchext, "-b", "-x", "-V", "7", str(game_id), output_ttarch, patch_folder]
        result = subprocess.run(cmd_x, capture_output=True, text=True)
        print(result.stdout)
    
    # Cleanup temp folder
    shutil.rmtree(patch_folder)
    
    if os.path.exists(output_ttarch):
        size_kb = os.path.getsize(output_ttarch) / 1024
        print(f"\nSuccess! Patch file created: {output_ttarch} ({size_kb:.1f} KB)")
        print("วางไฟล์นี้ในโฟลเดอร์ของเกม (ชื่อ 0.ttarch2) เพื่อใช้แปลภาษา")
    else:
        print("Warning: ไม่พบไฟล์ผลลัพธ์ อาจเกิดข้อผิดพลาดในการบีบอัด")
    
    return output_ttarch


if __name__ == '__main__':
    print("=== Telltale Packer ===")
    
    if len(sys.argv) < 3:
        print("\nUsage:")
        print("  python Telltale_packer.py <translated.csv> <extracted_folder> [output.ttarch2] [game_id]")
        print("\nExamples:")
        print("  python Telltale_packer.py translations.csv ./WDC_MenuSeason3_extracted ./0.ttarch2 67")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    extracted_folder = sys.argv[2]
    output_ttarch = sys.argv[3] if len(sys.argv) > 3 else None
    game_id = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    pack_telltale(input_csv, extracted_folder, output_ttarch, game_id)
