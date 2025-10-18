import os
from . import gpp

def main(command):
        script_dir = os.getcwd()

        dira = script_dir.replace("\\", "/")

        if command[0] == "build":
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
            build_tool = "g++"
            output_name = None
            start = None
            icon = None
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
                        start = os.path.join(dira, value).replace("\\", "/")
                    elif key == "icon":
                        icon = os.path.join(dira, value).replace("\\", "/")
                else:
                    print(f"Invalid line format: {line}")
            if build_tool == "g++":
                gpp.justdoit([output_name, start, icon])

        elif command[0] == "exit":
            print("Goodbye from FrogFast! ")
            return 45

        else:
            print("Unknown command. Try 'frogfast build [config.frogbulid]' or 'exit' or 'init'.")