#!/usr/bin/env python3
from dirmarks import DATA_PATH
import os
import sys
import fileinput
import subprocess


class Marks:
    def __init__(self):
        self.marks = {}
        self.list = []
        self.rc = os.path.expanduser("~/.markrc")
        self.read_marks("/etc/markrc", self.rc)

    def read_marks(self, *files):
        for f in files:
            if os.path.isfile(f):
                with open(f) as file:
                    for line in file:
                        key, value = line.strip().split(":")
                        if key not in self.marks:
                            self.list.append(line.strip())
                        self.marks[key] = value

    def add_mark(self, key, path):
        abs_path = os.path.abspath(path)
        if not os.path.isdir(abs_path):
            return
        if self.get_mark(key):
            return
        try:
            with open(self.rc, "a") as file:
                file.write(f"{key}:{abs_path}\n")
        except Exception as e:
            pass  # Optionally, handle or log the error if needed

    def del_mark(self, key):
        path = None
        found = False
        if key.isdigit():
            if int(key) >= len(self.list) or int(key) < 0:
                sys.stderr.write("key outside bundaries\n")
                return False
                
            path = (self.list[int(key)]).split(":")[1]
            if not path:
                return False
            key = (self.list[int(key)]).split(":")[0]
        else:
            path = self.get_mark(key)
        pmarks = []
        if path:
            with open(self.rc) as file:
                for line in file:
                    if f"{key}:{path}\n" in line:
                        found = True
                        continue
                    pmarks.append(line.strip())
            if not found:
                return False
            with open(self.rc, "w") as file:
                for mark in pmarks:
                    file.write(f"{mark}\n")
            return True

    def save_marks(self):
        with open(self.rc, "w") as file:
            for mark in self.marks:
                file.write(f"{mark}\n")
        return True

    def list_marks(self):
        for i, mark in enumerate(self.list):
            print(f"{i} => {mark}")

    def get_mark(self, key):
        path = key
        key = key.split("/")[0]
        if not key.isdigit():
            for k,line in enumerate(self.list):
                if line.startswith(f"{key}:"):
                    key = f"{k}"
                    break
        if not key.isdigit():
            return False
        key = int(key) 
        if key >= len(self.list) or key < 0:
                sys.stderr.write("Key {key} outside bundaries\n")
                return False
        if "/" in path:
            key = self.list[key]
            path = "/".join(path.split("/")[1:])
            return os.path.abspath(os.path.join(f"{key}/{path}"))
        else:
            return self.list[key].split(":")[1]

    def update_mark(self,key, path):
        if self.del_mark(key):
            self.add_mark(key,path)


def get_current_shell():
    shell = os.environ.get('SHELL', '')
    if 'bash' in shell:
        return 'Bash'
    elif 'zsh' in shell:
        return 'Zsh'
    else:
        return 'Unknown'
    
def check_dir_function_exists():
    try:
        # Try to get the definition of the 'dir' function
        shell = get_current_shell()
        if shell == 'Bash':
            result = subprocess.run(['bash', '-lc', 'type dir'], capture_output=True, text=True)
        elif shell == 'Zsh':
            result = subprocess.run(['zsh', '-ic', 'type dir'], capture_output=True, text=True)
        else:
            sys.stderr.write("Unknown shell. Please add the 'dir' function manually.\n")
            return False
        if result.stdout.startswith("dir is a function") or result.stdout.startswith("dir is a shell function"):
            sys.stderr.write("The 'dir' function exists in your environment.\n")
            return True
        else:
            sys.stderr.write("The 'dir' function does not exist. Follow these steps to add it:\n")
            print_function_definition()
            return False
    except subprocess.CalledProcessError as e:
        sys.stderr.write("An error occurred while checking for the 'dir' function.\n")
        sys.stderr.write("Error:", e)
        sys.stderr.write("\n")
        return False

def print_instructions():
    sys.stderr.write("1. Open your bash profile file in a text editor. This file could be ~/.bashrc or ~/.bash_profile.\n")
    sys.stderr.write("2. Add the following function definition to the file:\n")
    print_function_definition()
    sys.stderr.write("\n3. Save the file and run 'source ~/.bashrc' or 'source ~/.bash_profile' to update your current shell environment.\n")

def print_function_definition():
    sys.stderr.write("""dir() {
if [ $# -eq 0 ]; then
    dirmarks --list
    return
fi
OPT=$1;
shift;
case $OPT in
        -l)
        dirmarks --list
        ;;
        -h)
        dirmarks --help
        ;;
        -d)
        dirmarks --delete $1
        ;;
        -m)
        dirmarks --add $1 $PWD
        ;;
        -u)
        dirmarks --update $1 $2
        ;;
        -a)
        dirmarks --add $1 $2
        ;;
        -p)
        GO=$(dirmarks --get $1);
        if [ "X$GO" != "X" ]; then
                echo $GO;
        fi
        ;;
        *)
        GO=$(dirmarks --get $OPT);
        if [ "X$GO" != "X" ]; then
                cd $GO;
        fi
        ;;
esac
}
""")




def main():
    if len(sys.argv) == 1:
        # Call the function to check
        if check_dir_function_exists():
            sys.stderr.write("Usage: python marks.py [list|mark|add|delete|update|get] [arguments]\n")
        return

    command = sys.argv[1]

    if command == "--list":
        Marks().list_marks()
    elif command == "--help":
        sys.stderr.write("""Usage:
Run dirmarks --shell to print the shell function to be imported.
For more information: https://www.github.com/meirm/dirmarks
dir -h   ------------------ prints this help
dir -l	------------------ list marks
dir <[0-9]+> -------------- gm to mark[x] where is x is the index
dir <name> ---------------- gm to mark where key=<shortname>
dir -a <name> <path> ------ add new mark
dir -d <name>|[0-9]+ ------ delete mark
dir -u <name> <path> ------ update mark
dir -m <name> ------------- add mark for PWD
dir -p <name> ------------- prints mark
""")
    elif command == "--shell":
        with open(os.path.join(f"{DATA_PATH}","dirmarks.function"), "r") as fb:
            for line in fb.readlines():
                print(line, end='')
    elif command == "--mark":
        shortname, path = sys.argv[2], os.path.abspath(".")
        Marks().add_mark(shortname, path)
    elif command == "--add":
        shortname, path = sys.argv[2], sys.argv[3]
        Marks().add_mark(shortname, path)
    elif command == "--delete":
        shortname = sys.argv[2]
        Marks().del_mark(shortname)
    elif command == "--update":
        shortname, path = sys.argv[2], sys.argv[3]
        Marks().update_mark(shortname, path)
    elif command == "--get":
        shortname = sys.argv[2]
        bookmark = Marks().get_mark(shortname)
        if bookmark:
            print(bookmark)
        else:
            sys.stderr.write("Bookmark not found.\n")
    else:
        shortname = sys.argv[1]
        bookmark = Marks().get_mark(shortname)
        if bookmark:
            print(bookmark)
        else:
            sys.stderr.write("Bookmark not found.\n")



if __name__ == "__main__":
    main()

