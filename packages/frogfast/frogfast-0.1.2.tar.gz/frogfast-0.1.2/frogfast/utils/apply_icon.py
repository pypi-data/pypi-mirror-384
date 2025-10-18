import subprocess
import os

def apply_icon(exe_file, icon_file, rcedit_path=r"C:\rcedit\rcedit.exe"):
    # Make paths absolute
    exe_file = os.path.abspath(exe_file)
    icon_file = os.path.abspath(icon_file)
    rcedit_path = os.path.abspath(rcedit_path)
    
    # Run rcedit
    subprocess.run([rcedit_path, exe_file, "--set-icon", icon_file])
    print(f"✅ Icon applied to {exe_file}")
