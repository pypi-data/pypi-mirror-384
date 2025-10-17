import os

def program(number):
    base_path = os.path.join(os.path.dirname(__file__), "codes")
    file_path = os.path.join(base_path, f"{number}.txt")

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            code = f.read()
            print(code)
            # Optional: execute it too
            # exec(code)
    else:
        print(f"No code found for number {number}")
