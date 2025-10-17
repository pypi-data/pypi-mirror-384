# Dirmarks
Dirmarks is a directory bookmarking tool that allows you to easily manage, navigate, and switch between directories using bookmarks with **categories and tags**. This tool can save you time and make working with the command line more efficient by organizing your bookmarks with color-coded categories and searchable tags.

## ✨ Features

- 📁 **Directory Bookmarking**: Quick navigation to frequently used directories
- 🏷️ **Category Organization**: Group bookmarks by categories (work, personal, config, etc.)
- 🔖 **Tag System**: Add multiple tags to bookmarks for flexible filtering
- 🌈 **Color-Coded Display**: Categories and tags are displayed in distinctive colors
- 📊 **Smart Discovery**: Commands to explore categories, tags, and statistics
- 🔍 **Advanced Filtering**: Filter bookmarks by category or tag
- 📂 **Hierarchical Categories**: Support for nested categories (work/web/frontend)
- 🖥️ **Cross-Platform**: Works on Linux, macOS, and Windows
- 🔄 **Backward Compatible**: Works with existing bookmark files
- 🎨 **Terminal Detection**: Automatic color enable/disable based on terminal support

## Installation

### From PyPI (Recommended)
Install the dirmarks package using pip:

```bash
pip install dirmarks
```

### From Source (Development)
Clone the repository and install using Poetry:

```bash
# Clone the repository
git clone https://github.com/meirm/dirmarks.git
cd dirmarks

# Install with Poetry (recommended)
poetry install

# Or install with pip in development mode
pip install -e .
```

For development with all test dependencies:

```bash
# Install including development dependencies
poetry install --with dev

# Run tests to verify installation
python -m pytest
```

## Shell Function Setup
To enable the dir command for changing directories using bookmarks, add the following shell function to your .profile, .bashrc, or .zshrc file, depending on your shell:

```bash
#!/bin/bash
dir() {
if [ $# -eq 0 ]; then
    dirmarks --list
    return
fi
OPT=$1;
shift;
case $OPT in
        -l)
        # Enhanced list with optional category/tag filtering
        if [ "$1" = "--category" ] && [ -n "$2" ]; then
            dirmarks --list --category "$2"
        elif [ "$1" = "--tag" ] && [ -n "$2" ]; then
            dirmarks --list --tag "$2"
        else
            dirmarks --list "$@"
        fi
        ;;
        -h)
        dirmarks --help
        ;;
        -d)
        dirmarks --delete $1
        ;;
        -m)
        # Enhanced mark current directory with optional category/tags
        if [ "$2" = "--category" ] && [ -n "$3" ]; then
            if [ "$4" = "--tag" ] && [ -n "$5" ]; then
                dirmarks --add $1 "$PWD" --category "$3" --tag "$5"
            else
                dirmarks --add $1 "$PWD" --category "$3"
            fi
        elif [ "$2" = "--tag" ] && [ -n "$3" ]; then
            dirmarks --add $1 "$PWD" --tag "$3"
        else
            dirmarks --add $1 "$PWD"
        fi
        ;;
        -u)
        # Enhanced update with optional category/tags
        local name="$1"
        local path="$2"
        shift 2
        dirmarks --update "$name" "$path" "$@"
        ;;
        -a)
        # Enhanced add with optional category/tags
        local name="$1"
        local path="$2"
        shift 2
        dirmarks --add "$name" "$path" "$@"
        ;;
        -p)
        GO=$(dirmarks --get $1);
        if [ "X$GO" != "X" ]; then
                echo $GO;
        fi
        ;;
        -c)
        # List categories
        dirmarks --categories
        ;;
        -t)
        # List tags
        dirmarks --tags
        ;;
        -s)
        # Show statistics
        dirmarks --stats
        ;;
        --category)
        # List bookmarks by category
        if [ -n "$1" ]; then
            dirmarks --list --category "$1"
        else
            dirmarks --categories
        fi
        ;;
        --tag)
        # List bookmarks by tag
        if [ -n "$1" ]; then
            dirmarks --list --tag "$1"
        else
            dirmarks --tags
        fi
        ;;
        --stats)
        dirmarks --stats
        ;;
        *)
        GO=$(dirmarks --get $OPT);
        if [ "X$GO" != "X" ]; then
                cd "$GO";
        fi
        ;;
esac
}
```

Or add a file .functions in your home directory and source it in .bashrc

```
echo "source ~/.functions" >> ~/.bashrc
```
## Setup dirmarks for all users 

```bash
mkdir -p /etc/bash.functions 
cp dirmarks/data/dirmarks.function /etc/bash.functions/
```

### Append the following line in /etc/bash.bashrc

```
if [ -d /etc/bash.functions ]; then
        for i in /etc/bash.functions/*;do 
                source $i
        done
fi
```

## Usage:

### Basic Commands
```
dir -h   ------------------ prints this help
dir -l	------------------ list marks (with colors!)
dir <[0-9]+> -------------- dir to mark[x] where is x is the index
dir <name> ---------------- dir to mark where key=<shortname>
dir -a <name> <path> ------ add new mark
dir -d <name>|[0-9]+ ------ delete mark
dir -u <name> <path> ------ update mark
dir -m <name> ------------- add mark for PWD
dir -p <name> ------------- prints mark
```

### Category and Tag Commands
```
dir -c   ------------------ list all categories (with colors!)
dir -t   ------------------ list all tags (with colors!)
dir -s   ------------------ show bookmark statistics
dir -l --category <cat> --- list bookmarks in category
dir -l --tag <tag> -------- list bookmarks with tag
dir --category <cat> ------ list bookmarks in category
dir --tag <tag> ----------- list bookmarks with tag
```

### Enhanced Add/Update Commands
```
dir -a <name> <path> --category <cat> --tag <tag1,tag2>
dir -u <name> <path> --category <cat> --tag <tag1,tag2>
dir -m <name> --category <cat> --tag <tag1,tag2>
```

## Usage Examples

### Basic Usage
```bash
$ dir -l
0 => project1:/home/user/projects/webapp [category: work] [tags: urgent, frontend]
1 => docs:/home/user/documents [category: personal] [tags: important]
2 => config:/etc/nginx [category: config] [tags: production, critical]

$ dir 1
user@host:/home/user/documents$ 

$ dir project1
user@host:/home/user/projects/webapp$ 
```

### Category and Tag Organization
```bash
# Add bookmark with category and tags
$ dir -a myproject /home/user/work/project --category work --tag urgent,frontend

# List bookmarks by category (with colors!)
$ dir -l --category work
Bookmarks in category 'work':
  myproject => /home/user/work/project [tags: urgent, frontend]
  backend => /home/user/work/api [tags: production, backend]

# List bookmarks by tag
$ dir -l --tag urgent
Bookmarks with tag 'urgent':
  myproject => /home/user/work/project [category: work] [tags: frontend]
  hotfix => /home/user/urgent/fix [category: work] [tags: critical]

# Quick category/tag discovery
$ dir -c
Available categories:
  work
  personal
  config

$ dir -t  
Available tags:
  urgent
  frontend
  backend
  production
  critical

$ dir -s
Bookmark Statistics:
========================================

Categories (3):
  work: 5 bookmarks
  personal: 2 bookmarks
  config: 1 bookmark

Tags (5):
  urgent: 2 bookmarks
  frontend: 3 bookmarks
  backend: 2 bookmarks
  production: 4 bookmarks
  critical: 1 bookmark
```

### Hierarchical Categories
```bash
# Create hierarchical categories
$ dir -a webapp /var/www/html --category work/web/frontend --tag react,production
$ dir -a api /var/www/api --category work/web/backend --tag node,production

# List hierarchical categories
$ dir -l --category work/web/frontend
Bookmarks in category 'work/web/frontend':
  webapp => /var/www/html [tags: react, production]
```

### Advanced Features
```bash
# Mark current directory with metadata
$ cd /home/user/important-project
$ dir -m important --category personal --tag priority,backup

# Update existing bookmark with new category/tags
$ dir -u oldproject /new/path --category work --tag updated,refactored

# Color-coded output automatically adapts to your terminal
# Categories and tags are displayed in different colors for easy identification
```

## Configuration

### Color Customization
Dirmarks automatically assigns colors to categories and tags. You can customize these colors by editing `~/.dirmarks_colors.json`:

```json
{
  "categories": {
    "work": "BLUE",
    "personal": "GREEN",
    "projects": "CYAN",
    "important": "RED"
  },
  "tags": {
    "urgent": "RED",
    "production": "RED",
    "development": "GREEN",
    "testing": "MAGENTA"
  }
}
```

Available colors: `RED`, `GREEN`, `BLUE`, `CYAN`, `MAGENTA`, `YELLOW`, `WHITE`, `BLACK`, and their light variants (e.g., `LIGHTRED_EX`).

### Disabling Colors
To disable colors, set the `NO_COLOR` environment variable:

```bash
export NO_COLOR=1
dirmarks --list  # Will display without colors
```

### Category Naming Rules
Categories must follow these naming conventions:
- Alphanumeric characters, hyphens, and underscores only
- Forward slashes (/) for hierarchical categories
- Examples: `work`, `work-projects`, `work/web/frontend`

## Troubleshooting

### Common Issues

#### ValueError: too many values to unpack
**Problem**: This error occurs when using an old version of dirmarks with bookmarks created by the enhanced version.

**Solution**: Update to the latest version:
```bash
pip uninstall dirmarks
pip install -e /path/to/dirmarks/repo
```

#### Colors not displaying
**Problem**: Terminal doesn't support colors or colors are disabled.

**Check**:
- Ensure your terminal supports ANSI colors
- Check if `NO_COLOR` environment variable is set
- Verify terminal type: `echo $TERM`

#### Bookmarks not persisting
**Problem**: Bookmarks disappear after restart.

**Check**:
- Verify `~/.markrc` file exists and has proper permissions
- Check if HOME environment variable is set correctly
- Ensure write permissions in home directory

#### Shell function not working
**Problem**: `dir` command not recognized.

**Solution**: Source the shell function:
```bash
# Add to ~/.bashrc or ~/.zshrc
eval "$(dirmarks --shell)"
# Then reload
source ~/.bashrc  # or source ~/.zshrc
```

## Advanced Usage

### Python API
You can also use dirmarks programmatically:

```python
from dirmarks.marks_enhanced import Marks

# Create marks instance
marks = Marks()

# Add bookmark with metadata
marks.add_mark_with_metadata('myproject', '/path/to/project', 
                            category='work', tags=['urgent', 'frontend'])

# List by category
work_marks = marks.list_by_category('work')

# List by tag
urgent_marks = marks.list_by_tag('urgent')

# Get statistics
stats = marks.get_category_stats()
```

### File Format
Bookmarks are stored in `~/.markrc` with backward-compatible format:
```
# Old format (still supported)
bookmark_name:/path/to/directory

# New format with metadata
bookmark_name:/path/to/directory|category:work|tags:urgent,frontend
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For development setup, see the installation from source instructions above.

## License

MIT License - see LICENSE file for details.

