import os

def print_directory_tree(path, indent=""):
    files = os.listdir(path)
    for i, file in enumerate(files):
        if i == len(files) - 1:
            print(indent + "└── " + file)
            new_indent = indent + "    "
        else:
            print(indent + "├── " + file)
            new_indent = indent + "│   "
        full_path = os.path.join(path, file)
        if os.path.isdir(full_path):
            print_directory_tree(full_path, new_indent)

# Replace '.' with the directory you want to start from
print_directory_tree(".")
