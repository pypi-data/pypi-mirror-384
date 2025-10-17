#!/usr/bin/env python3
from dirmarks import DATA_PATH
from dirmarks.marks_enhanced import Marks
from dirmarks.colors import get_color_manager
import os
import sys
import fileinput
import subprocess


# The Marks class is now imported from marks_enhanced.py
# which provides both backward compatibility and new category features


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




def parse_optional_args(args, start_index):
    """Parse optional category and tag arguments from command line."""
    category = None
    tags = []
    
    i = start_index
    while i < len(args):
        if args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tags = args[i + 1].split(',')
            i += 2
        else:
            i += 1
    
    return category, tags


def enhanced_list_marks(marks, category_filter=None, tag_filter=None):
    """Enhanced list function with category/tag display and filtering with colors."""
    color_manager = get_color_manager()
    
    if category_filter:
        filtered_marks = marks.list_by_category(category_filter)
        colored_category = color_manager.colorize_category(category_filter)
        print(f"Bookmarks in category '{colored_category}':")
        for mark in filtered_marks:
            if mark.get('tags'):
                colored_tags = color_manager.colorize_tags(mark['tags'])
                tags_str = f" [tags: {', '.join(colored_tags)}]"
            else:
                tags_str = ""
            print(f"  {mark['name']} => {mark['path']}{tags_str}")
    elif tag_filter:
        filtered_marks = marks.list_by_tag(tag_filter)
        colored_tag = color_manager.colorize_tag(tag_filter)
        print(f"Bookmarks with tag '{colored_tag}':")
        for mark in filtered_marks:
            category_str = f" [category: {color_manager.colorize_category(mark['category'])}]" if mark.get('category') else ""
            other_tags = [t for t in mark.get('tags', []) if t != tag_filter]
            if other_tags:
                colored_other_tags = color_manager.colorize_tags(other_tags)
                tags_str = f" [tags: {', '.join(colored_other_tags)}]"
            else:
                tags_str = ""
            print(f"  {mark['name']} => {mark['path']}{category_str}{tags_str}")
    else:
        # Enhanced default listing with categories and tags
        for i, mark in enumerate(marks.list):
            mark_name = mark.split(':')[0]
            mark_data = marks.get_mark_with_metadata(mark_name)
            
            if mark_data:
                category_str = f" [category: {color_manager.colorize_category(mark_data['category'])}]" if mark_data.get('category') else ""
                if mark_data.get('tags'):
                    colored_tags = color_manager.colorize_tags(mark_data['tags'])
                    tags_str = f" [tags: {', '.join(colored_tags)}]"
                else:
                    tags_str = ""
                print(f"{i} => {mark}{category_str}{tags_str}")
            else:
                print(f"{i} => {mark}")


def main():
    if len(sys.argv) == 1:
        # Call the function to check
        if check_dir_function_exists():
            sys.stderr.write("Usage: python marks.py [list|mark|add|delete|update|get] [arguments]\n")
        return

    command = sys.argv[1]

    if command == "--list":
        # Parse optional category and tag filters
        category_filter = None
        tag_filter = None
        
        if "--category" in sys.argv:
            idx = sys.argv.index("--category")
            if idx + 1 < len(sys.argv):
                category_filter = sys.argv[idx + 1]
        
        if "--tag" in sys.argv:
            idx = sys.argv.index("--tag")
            if idx + 1 < len(sys.argv):
                tag_filter = sys.argv[idx + 1]
        
        marks = Marks()
        enhanced_list_marks(marks, category_filter, tag_filter)
        
    elif command == "--help":
        sys.stderr.write("""Usage:
Run dirmarks --shell to print the shell function to be imported.
For more information: https://www.github.com/meirm/dirmarks

=== BASIC COMMANDS ===
dir -h   ------------------ prints this help
dir -l	------------------ list marks (with colors!)
dir <[0-9]+> -------------- go to mark[x] where is x is the index
dir <name> ---------------- go to mark where key=<shortname>
dir -a <name> <path> ------ add new mark
dir -d <name>|[0-9]+ ------ delete mark
dir -u <name> <path> ------ update mark
dir -m <name> ------------- add mark for PWD
dir -p <name> ------------- prints mark

=== CATEGORY & TAG COMMANDS ===
dir -c   ------------------ list all categories (with colors!)
dir -t   ------------------ list all tags (with colors!)
dir -s   ------------------ show bookmark statistics
dir -l --category <cat> --- list bookmarks in category
dir -l --tag <tag> -------- list bookmarks with tag
dir --category <cat> ------ list bookmarks in category (shortcut)
dir --tag <tag> ----------- list bookmarks with tag (shortcut)

=== ENHANCED ADD/UPDATE ===
dir -a <name> <path> --category <cat> --tag <tag1,tag2>  -- add with metadata
dir -u <name> <path> --category <cat> --tag <tag1,tag2>  -- update with metadata
dir -m <name> --category <cat> --tag <tag1,tag2> ------- mark PWD with metadata

=== DIRECT COMMANDS (bypass shell function) ===
dirmarks --categories ----------------------------------- list all categories
dirmarks --tags ----------------------------------------- list all tags
dirmarks --stats ---------------------------------------- show category/tag statistics
dirmarks --list --category <cat> ----------------------- list by category
dirmarks --list --tag <tag> ----------------------------- list by tag

=== FEATURES ===
• Color-coded categories and tags (auto-detects terminal support)
• Hierarchical categories (work/web/frontend)
• Multiple tags per bookmark (urgent,production,frontend)
• Backward compatible with existing bookmarks
• Cross-platform support (Linux, macOS, Windows)
""")
    elif command == "--shell":
        with open(os.path.join(f"{DATA_PATH}","dirmarks.function"), "r") as fb:
            for line in fb.readlines():
                print(line, end='')
    elif command == "--mark":
        if len(sys.argv) < 3:
            sys.stderr.write("Usage: dirmarks --mark <name> [--category <category>] [--tag <tags>]\n")
            return
            
        shortname = sys.argv[2]
        path = os.path.abspath(".")
        category, tags = parse_optional_args(sys.argv, 3)
        
        marks = Marks()
        if category and not marks.is_valid_category(category):
            sys.stderr.write(f"Invalid category name: {category}\n")
            return
            
        if category or tags:
            success = marks.add_mark_with_metadata(shortname, path, category=category, tags=tags)
            if not success:
                sys.stderr.write("Failed to add bookmark\n")
        else:
            marks.add_mark(shortname, path)
            
    elif command == "--add":
        if len(sys.argv) < 4:
            sys.stderr.write("Usage: dirmarks --add <name> <path> [--category <category>] [--tag <tags>]\n")
            return
            
        shortname, path = sys.argv[2], sys.argv[3]
        category, tags = parse_optional_args(sys.argv, 4)
        
        marks = Marks()
        if category and not marks.is_valid_category(category):
            sys.stderr.write(f"Invalid category name: {category}\n")
            return
            
        if category or tags:
            success = marks.add_mark_with_metadata(shortname, path, category=category, tags=tags)
            if not success:
                sys.stderr.write("Failed to add bookmark\n")
        else:
            marks.add_mark(shortname, path)
            
    elif command == "--delete":
        shortname = sys.argv[2]
        Marks().del_mark(shortname)
        
    elif command == "--update":
        if len(sys.argv) < 4:
            sys.stderr.write("Usage: dirmarks --update <name> <path> [--category <category>] [--tag <tags>]\n")
            return
            
        shortname, path = sys.argv[2], sys.argv[3]
        category, tags = parse_optional_args(sys.argv, 4)
        
        marks = Marks()
        if category and not marks.is_valid_category(category):
            sys.stderr.write(f"Invalid category name: {category}\n")
            return
        
        # For update, we first delete then re-add with new metadata
        if marks.del_mark(shortname):
            if category or tags:
                success = marks.add_mark_with_metadata(shortname, path, category=category, tags=tags)
                if not success:
                    sys.stderr.write("Failed to update bookmark\n")
            else:
                marks.add_mark(shortname, path)
        else:
            sys.stderr.write("Bookmark not found\n")
            
    elif command == "--get":
        shortname = sys.argv[2]
        bookmark = Marks().get_mark(shortname)
        if bookmark:
            print(bookmark)
        else:
            sys.stderr.write("Bookmark not found.\n")
    
    elif command == "--categories":
        marks = Marks()
        color_manager = get_color_manager()
        categories = marks.list_all_categories()
        if categories:
            print("Available categories:")
            for category in categories:
                colored_category = color_manager.colorize_category(category)
                print(f"  {colored_category}")
        else:
            print("No categories found.")
    
    elif command == "--tags":
        marks = Marks()
        color_manager = get_color_manager()
        tags = marks.list_all_tags()
        if tags:
            print("Available tags:")
            for tag in tags:
                colored_tag = color_manager.colorize_tag(tag)
                print(f"  {colored_tag}")
        else:
            print("No tags found.")
    
    elif command == "--stats":
        marks = Marks()
        color_manager = get_color_manager()
        
        category_stats = marks.get_category_stats()
        tag_stats = marks.get_tag_stats()
        
        print("Bookmark Statistics:")
        print("=" * 40)
        
        if category_stats:
            print(f"\nCategories ({len(category_stats)}):")
            for category, count in category_stats.items():
                colored_category = color_manager.colorize_category(category)
                print(f"  {colored_category}: {count} bookmark{'s' if count != 1 else ''}")
        else:
            print("\nNo categories found.")
        
        if tag_stats:
            print(f"\nTags ({len(tag_stats)}):")
            for tag, count in tag_stats.items():
                colored_tag = color_manager.colorize_tag(tag)
                print(f"  {colored_tag}: {count} bookmark{'s' if count != 1 else ''}")
        else:
            print("\nNo tags found.")
        
        total_bookmarks = len(marks.list)
        categorized = len([m for m in marks.marks_metadata.values() if m.get('category')])
        tagged = len([m for m in marks.marks_metadata.values() if m.get('tags')])
        
        print(f"\nSummary:")
        print(f"  Total bookmarks: {total_bookmarks}")
        print(f"  With categories: {categorized}")
        print(f"  With tags: {tagged}")
            
    else:
        shortname = sys.argv[1]
        bookmark = Marks().get_mark(shortname)
        if bookmark:
            print(bookmark)
        else:
            sys.stderr.write("Bookmark not found.\n")



if __name__ == "__main__":
    main()

