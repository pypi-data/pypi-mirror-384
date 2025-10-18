import frogfast.pythonc.main as thing
import frogfast.c.main as thing2
import frogfast.cpp.main as thing3
import frogfast.utils.apply_icon as apply

def main():
    while True:
        code = 0
        command = input("frogfast> ").strip().split(" ")
        if not command == "90":
            code = thing.main(command)
        elif command == "90":
            code = 90
            print("""
🐸🐸🐸 POWER MODE 🐸🐸🐸
in power mode you can use frogfast's utils and experimental things just be sure not to explode you're computer
to exit power mode type "5"
""")
        if code == 45:
            break
        elif code == 9:
            thing2.main(command)
        elif code == 10:
            thing3.main(command)
        elif command == "5" and code == 90:
            code == 5
        elif code == 90:
            if command == "icon":
                apply.apply_icon()