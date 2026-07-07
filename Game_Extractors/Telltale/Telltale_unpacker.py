import os
import sys
import subprocess
import shutil

# =====================================================================
# Telltale_unpacker.py
# แตกไฟล์ .ttarch2 ของเกมตระกูล Telltale ออกมาเป็นโฟลเดอร์
# โดยใช้ ttarchext.exe เป็นตัวแตกไฟล์
# =====================================================================

# GameID mapping สำหรับเกมที่รองรับ
GAME_IDS = {
    "walking_dead_s1":    52,  # The Walking Dead: A New Day (Season 1)
    "walking_dead_s2":    55,  # The Walking Dead: Season 2
    "walking_dead_s3":    61,  # The Walking Dead: A New Frontier (Season 3)
    "walking_dead_definitive": 67, # The Walking Dead: Definitive Series
    "wolf_among_us":      54,  # The Wolf Among Us
    "tales_borderlands":  56,  # Tales from the Borderlands
    "game_of_thrones":    57,  # Game of Thrones
    "minecraft_sm":       58,  # Minecraft: Story Mode
    "walking_dead_michonne": 59, # The Walking Dead: Michonne
    "batman_s1":          60,  # Batman: The Telltale Series
    "batman_s2":          64,  # Batman: The Enemy Within
    "guardians_galaxy":   62,  # Marvel's Guardians of the Galaxy
}

def find_ttarchext():
    """ค้นหา ttarchext.exe ใน path ที่เกี่ยวข้อง"""
    # Look relative to this script
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

def unpack_ttarch(input_file, output_folder=None, game_id=None):
    """
    แตกไฟล์ .ttarch / .ttarch2 ออกมาเป็นโฟลเดอร์
    
    Args:
        input_file (str): path ของไฟล์ .ttarch2
        output_folder (str): โฟลเดอร์ปลายทาง (ถ้าไม่ระบุจะสร้างอัตโนมัติ)
        game_id (int): รหัสเกม (ถ้าไม่ระบุจะลองหาจากชื่อไฟล์)
    
    Returns:
        str: path ของโฟลเดอร์ผลลัพธ์
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"ไม่พบไฟล์: {input_file}")
    
    # หา ttarchext.exe
    ttarchext = find_ttarchext()
    if not ttarchext:
        raise FileNotFoundError(
            "ไม่พบ ttarchext.exe!\n"
            "กรุณาวาง ttarchext.exe ไว้ในโฟลเดอร์เดียวกับสคริปต์นี้"
        )
    
    # ตั้งค่า output folder
    if not output_folder:
        base = os.path.splitext(input_file)[0]
        output_folder = base + "_extracted"
    
    os.makedirs(output_folder, exist_ok=True)
    
    # กำหนด game_id อัตโนมัติถ้าไม่ระบุ
    if game_id is None:
        fname = os.path.basename(input_file).lower()
        # ลองตรวจสอบจากชื่อไฟล์
        if "wdc_" in fname or "walkingdead3" in fname:
            game_id = 67  # Definitive Series
        elif "wds2" in fname or "walkingdead2" in fname:
            game_id = 55
        elif "wds1" in fname or "walkingdead" in fname:
            game_id = 52
        elif "twau" in fname or "wolf" in fname:
            game_id = 54
        elif "gtl" in fname or "thrones" in fname:
            game_id = 57
        elif "mc" in fname or "minecraft" in fname:
            game_id = 58
        elif "batman" in fname:
            game_id = 60
        else:
            game_id = 67  # Default to Definitive Series (newest)
    
    print(f"Extracting: {os.path.basename(input_file)}")
    print(f"Using Game ID: {game_id}")
    print(f"Output folder: {output_folder}")
    
    cmd = [ttarchext, str(game_id), input_file, output_folder]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0 and "Error" in result.stdout:
        print(f"Warning: {result.stdout}")
        # Try with -O flag (old mode) if failed
        print("Trying with -O flag...")
        cmd_old = [ttarchext, "-O", str(game_id), input_file, output_folder]
        result = subprocess.run(cmd_old, capture_output=True, text=True)
    
    print(result.stdout)
    
    # Count extracted files
    extracted = [f for f in os.listdir(output_folder) if os.path.isfile(os.path.join(output_folder, f))]
    print(f"\nExtracted {len(extracted)} files to: {output_folder}")
    
    # Find landb files specifically
    landb_files = [f for f in extracted if f.endswith('.landb')]
    if landb_files:
        print(f"\nFound {len(landb_files)} language file(s):")
        for lf in landb_files:
            print(f"  - {lf}")
    
    return output_folder


def unpack_multiple(folder, output_base=None, game_id=None):
    """
    แตกไฟล์ .ttarch2 ทั้งหมดในโฟลเดอร์
    """
    ttarch_files = [
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.endswith(('.ttarch', '.ttarch2'))
    ]
    
    if not ttarch_files:
        print(f"ไม่พบไฟล์ .ttarch2 ในโฟลเดอร์: {folder}")
        return []
    
    results = []
    for f in ttarch_files:
        try:
            out = unpack_ttarch(f, game_id=game_id)
            results.append(out)
        except Exception as e:
            print(f"Error extracting {f}: {e}")
    
    return results


if __name__ == '__main__':
    print("=== Telltale TTARCH2 Unpacker ===")
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  Unpack single file:   python Telltale_unpacker.py <file.ttarch2> [output_folder] [game_id]")
        print("  Unpack whole folder:  python Telltale_unpacker.py --folder <folder> [game_id]")
        print("\nGame IDs:")
        for name, gid in GAME_IDS.items():
            print(f"  {gid:2d}  {name}")
        sys.exit(1)
    
    if sys.argv[1] == '--folder':
        folder = sys.argv[2]
        game_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
        unpack_multiple(folder, game_id=game_id)
    else:
        input_file = sys.argv[1]
        output_folder = sys.argv[2] if len(sys.argv) > 2 else None
        game_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
        unpack_ttarch(input_file, output_folder, game_id)
