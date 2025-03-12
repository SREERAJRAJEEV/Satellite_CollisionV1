import os

def print_tree(directory, prefix=""):
    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            print(f"{prefix}├── {item}/")
            print_tree(path, prefix + "│   ")
        else:
            print(f"{prefix}└── {item}")

if __name__ == "__main__":
    print_tree(".")