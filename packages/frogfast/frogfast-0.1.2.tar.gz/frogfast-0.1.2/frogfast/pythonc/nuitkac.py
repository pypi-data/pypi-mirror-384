import sys
import subprocess
from PIL import Image
import os

def png_to_ico(png_path):
    # Open the PNG file
    img = Image.open(png_path)
    
    # Get directory and base filename without extension
    dir_name = os.path.dirname(png_path)
    base_name = os.path.splitext(os.path.basename(png_path))[0]
    
    # Build the ICO path
    # temp path for ico file
    # THE ICO WILL LIVE IN TEMP FOLDER
    ico_path = os.path.join(dir_name, base_name + ".ico")
    
    # Save as ICO with common icon sizes
    img.save(ico_path, format='ICO', sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])
    
    print(f"Converted '{png_path}' to '{ico_path}'")
    return ico_path

def justdoit(settings: list):
    print(settings)
    # first is the output file path and the second is the input file path
    if len(settings) < 2:
        print("Usage: python script.py <output.ico> <input.png>")
        sys.exit(1)
    
    output_path = settings[0]
    input_path = settings[1]
    img = settings[2]
    # Check if the input file exists

    if not os.path.exists(input_path):
        print(f"Error: The file {input_path} does not exist.")
        sys.exit(1)
    
    # Convert PNG to ICO
    ico_path = png_to_ico(img)

    # now use subprocess to get the input and output file paths
    subprocess.run([
        sys.executable, "-m", "nuitka",
        "--output-dir=build",
        "--windows-icon-from-ico=" + ico_path,
        "--output-filename=" + output_path,
        input_path
    ], check=True)