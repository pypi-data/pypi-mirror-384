import os
import shutil

def justdoit(templete):
    interpert(templete)

def temp_python():
    with open("config.frogfast", "w") as f:
        f.write("compiler=nuitka\n")
        f.write("entry=application/main.py\n")
        f.write("exe_name=application\n")
        f.write("icon=test.png\n")
        f.write("lang=python\n")
    os.mkdir("application")

    with open("application/main.py", "w") as f:
        f.write('if __name__ == "__main__":\n')
        f.write("   print('itz working by the froggggggggggggggggggggggggggggggs')\n")
    os.mkdir("Build")

def temp_c():
    with open("config.frogfast", "w") as f:
        f.write("compiler=gcc\n")
        f.write("entry=application/main.c\n")
        f.write("exe_name=application\n")
        f.write("icon=test.png\n")
        f.write("lang=c\n")
    os.mkdir("application")

    with open("application/main.c", "w") as f:
        f.write('#include <stdio.h>\n')
        f.write('int main(){printf("Hello, world!\n");}\n')
    os.mkdir("Build")

def temp_cpp():
    with open("config.frogfast", "w") as f:
        f.write("compiler=g++\n")
        f.write("entry=application/main.cpp\n")
        f.write("exe_name=application\n")
        f.write("icon=test.png\n")
        f.write("lang=c++\n")
    os.mkdir("application")

    with open("application/main.cpp", "w") as f:
        f.write('#include <iostream>\n')
        f.write('int main(){std::cout<<"Hello, World!";}\n')
    os.mkdir("Build")

def interpert(file):
    base_dir = f"C:\\frogfast_templetes\\{file}"
    dir_path = os.path.join(base_dir, f"{file}.txt")
    cwd = os.getcwd()

    with open(dir_path, "r") as f:
        data = f.readlines()

    for line in data:
        tokens = line.strip().split(" ")
        if not tokens:
            continue

        cmd, *args = tokens

        if cmd == "dir" and args:
            os.makedirs(os.path.join(cwd, args[0]), exist_ok=True)

        elif cmd == "add" and args:
            open(os.path.join(cwd, args[0]), "w").close()

        elif cmd == "delete" and args:
            target = os.path.join(cwd, args[0])
            if os.path.exists(target):
                os.remove(target)

        elif cmd == "edit" and len(args) == 2:
            src = os.path.join(base_dir, args[0])
            dst = os.path.join(cwd, args[1])
            if os.path.exists(src):
                with open(src, "r") as f_src:
                    content = f_src.read()
                with open(dst, "w") as f_dst:
                    f_dst.write(content)
