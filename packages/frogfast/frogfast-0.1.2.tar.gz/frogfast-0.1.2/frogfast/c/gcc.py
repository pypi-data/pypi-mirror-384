import sys
import subprocess
from PIL import Image
import os

# Add MinGW bin to PATH for Python subprocess
os.environ["PATH"] = r"C:\msys64\mingw64\bin;" + os.environ["PATH"]

def png_to_ico(png_path):
    """Convert PNG to ICO and save in the same folder."""
    img = Image.open(png_path)
    dir_name = os.path.dirname(png_path)
    base_name = os.path.splitext(os.path.basename(png_path))[0]
    ico_path = os.path.join(dir_name, base_name + ".ico")
    img.save(ico_path, format='ICO', sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])
    print(f"Converted '{png_path}' to '{ico_path}'")
    return ico_path

def justdoit(options):
    """Build a Windows executable from source, embedding an icon."""
    exe_name, start, icon = options

    # Convert PNG to ICO
    ico_path = png_to_ico(icon)

    # Ensure build directory exists
    build_dir = os.path.join(os.getcwd(), "build")
    os.makedirs(build_dir, exist_ok=True)
    exe_path = os.path.join(build_dir, exe_name)

    # Prepare temporary RC and RES files
    rc_path = os.path.join(build_dir, r"temp_icon.rc").replace("\\", "/")
    res_file = os.path.join(build_dir, r"temp_icon.res").replace("\\", "/")

    # Create RC file for icon
    with open(rc_path, "w") as f:
        f.write(f'1 ICON "{ico_path.replace("\\", "/")}"\n')

    # Compile RC to RES
    try:
        subprocess.run(["windres", rc_path, "-O", "coff", "-o", res_file], check=True)
        print(f"Compiled icon resource: {res_file}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to compile icon resource: {e}")
        return

    # Build GCC command
    gcc_cmd = [
        "gcc",
        start,
        res_file,
        "-o",
        exe_path,
    ]

    # Run GCC
    try:
        subprocess.run(gcc_cmd, check=True)
        print(f"Build complete: {exe_path}")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return
    finally:
        # Cleanup temporary files
        for f in [rc_path, res_file]:
            if os.path.exists(f):
                os.remove(f)

# Example usage:
# justdoit(("myapp.exe", "main.c", "icon.png"))
