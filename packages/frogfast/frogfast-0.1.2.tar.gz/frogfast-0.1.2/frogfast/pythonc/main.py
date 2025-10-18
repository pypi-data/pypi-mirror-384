# frogfast is a bulid tool for python and use pyinstaller, cx_Freeze, or py2exe or nuitka to build python applications. fast because frog is fast.\
# ok it will read a file called *.frogbulid to determine the build tool to use the final executable's name etc.
# wait does nuitka have this in-built? yes it does, but we will use it anyway.
# ok lets get started
#bruhbut i am a frog rabbit rabbit rabbit rabbit rabbit rabbit rabbit rabbit rabbit rabbit rabbit
# ok lets get started
import shutil
import os
import subprocess
from . import nuitkac  # my nuitka build helper
from . import initer

def main(command):
        script_dir = os.getcwd()

        dira = script_dir

        if command[0] == "clean":
            shutil.rmtree(os.path.join(dira, "dist"))
            shutil.rmtree(os.path.join(dira, "__pycache__"))

        elif command[0] == "build":
            print("Building your application...")
            # Get config file path, default if none given
            file_path = command[1]
            print(f"Using build configuration from: {os.path.join(dira, file_path)}")
            file_path = os.path.join(dira, file_path)
            try:
                with open(file_path, 'r') as f:
                    build_config = f.read()
                    print(f"Build configuration:\n{build_config}")
            except FileNotFoundError:
                print(f"Error: The file {file_path} does not exist.")
            # now we need to murder the config file lines by line
            # trust me i am not a phyco
            # Variables to hold config values
            build_tool = "nuitka"
            output_name = None
            start = None
            icon = None
            lang = None
            # Parse config lines
            lines = build_config.splitlines()
            for line in lines:
                parts = line.split("=")
                if len(parts) == 2:
                    key, value = parts
                    key = key.strip()
                    value = value.strip()
                    print(f"Key: {key}, Value: {value}")
                    if key == "compiler":
                        build_tool = value
                    elif key == "exe_name":
                        output_name = f"{value.replace(' ', '_')}.exe"
                    elif key == "entry":
                        start = os.path.join(dira, value)
                    elif key == "icon":
                        icon = os.path.join(dira, value)
                    elif key == "lang":
                        lang = value
                else:
                    print(f"Invalid line format: {line}")
            if lang == "python":
                print(f"Using build tool: {build_tool}")
                print(f"Output executable name: {output_name}")
                # Now run the build tool
                if build_tool == "nuitka":
                    if not all([output_name, start, icon]):
                        print("Error: Missing one or more required config values: exe_name, entry, or icon.")
                    print("Starting build with Nuitka...")
                    try:
                        nuitkac.justdoit([output_name, start, icon])
                        print("Build complete!")
                    except Exception as e:
                        print(output_name)
                        print(start)
                        print(icon)
                        print(f"Build failed with error: {e}")
                else:
                    print(f"Build tool '{build_tool}' not supported yet.")
            if lang == "c":
                return 9
            if lang == "c++":
                return 10
            else:
                return 90

        elif command[0] == "init":
            templete = command[1]
            initer.justdoit(templete)
        
        elif command[0] == "run":
            subprocess.run([f".\\{command[1]}"])

        elif command[0] == "exit":
            print("Goodbye from FrogFast! ")
            return 45

        else:
            print("Unknown command. Try 'frogfast build [config.frogbulid]' or 'exit' or 'init'.")