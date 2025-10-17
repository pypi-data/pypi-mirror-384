#!/usr/bin/env python3
"""
Enhanced Marks class with category and tag support.
Extends the original Marks functionality with organizational features.
"""

import os
import re
import json
from typing import Dict, List, Optional, Any


class MarksEnhanced:
    """Enhanced bookmark manager with category and tag support."""
    
    def __init__(self):
        """Initialize the enhanced marks system."""
        self.marks = {}  # Simple key:path mapping for backward compatibility
        self.marks_metadata = {}  # Full metadata including categories and tags
        self.list = []
        self.rc = os.path.expanduser("~/.markrc")
        self.config_file = os.path.expanduser("~/.markrc.config")
        self.category_colors = {}
        self.load_config()
        self.read_marks("/etc/markrc", self.rc)
    
    def load_config(self):
        """Load configuration including category colors."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.category_colors = config.get('category_colors', {})
            except:
                self.category_colors = {}
    
    def save_config(self):
        """Save configuration to file."""
        config = {
            'category_colors': self.category_colors
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass
    
    def read_marks(self, *files):
        """Read marks from files, supporting both old and new formats."""
        for f in files:
            if os.path.isfile(f):
                with open(f) as file:
                    for line in file:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Try to parse new format with metadata
                        if '|' in line:
                            self._parse_new_format(line)
                        else:
                            # Old format: key:path
                            self._parse_old_format(line)
    
    def read_marks_with_metadata(self, *files):
        """Alias for read_marks that explicitly handles metadata."""
        return self.read_marks(*files)
    
    def _parse_old_format(self, line: str):
        """Parse old format bookmark (key:path)."""
        if ':' not in line:
            return
        
        parts = line.split(':', 1)
        if len(parts) != 2:
            return
            
        key, path = parts
        if key not in self.marks:
            self.list.append(line)
        
        self.marks[key] = path
        self.marks_metadata[key] = {
            'path': path,
            'category': None,
            'tags': []
        }
    
    def _parse_new_format(self, line: str):
        """Parse new format bookmark with metadata (key:path|category:cat|tags:tag1,tag2)."""
        parts = line.split('|')
        if not parts:
            return
        
        # First part is key:path
        if ':' not in parts[0]:
            return
            
        key_path = parts[0].split(':', 1)
        if len(key_path) != 2:
            return
            
        key, path = key_path
        
        # Initialize metadata
        metadata = {
            'path': path,
            'category': None,
            'tags': []
        }
        
        # Parse additional metadata
        for part in parts[1:]:
            if ':' in part:
                meta_key, meta_value = part.split(':', 1)
                if meta_key == 'category':
                    metadata['category'] = meta_value
                elif meta_key == 'tags':
                    metadata['tags'] = meta_value.split(',') if meta_value else []
        
        if key not in self.marks:
            self.list.append(f"{key}:{path}")
        
        self.marks[key] = path
        self.marks_metadata[key] = metadata
    
    def add_mark_with_category(self, key: str, path: str, category: str) -> bool:
        """Add a bookmark with a category."""
        if not self.is_valid_category(category):
            return False
        
        return self.add_mark_with_metadata(key, path, category=category)
    
    def add_mark_with_tags(self, key: str, path: str, tags: List[str]) -> bool:
        """Add a bookmark with tags."""
        return self.add_mark_with_metadata(key, path, tags=tags)
    
    def add_mark_with_metadata(self, key: str, path: str, category: Optional[str] = None, 
                               tags: Optional[List[str]] = None) -> bool:
        """Add a bookmark with metadata (category and/or tags)."""
        abs_path = os.path.abspath(path)
        if not os.path.isdir(abs_path):
            return False
        
        if self.get_mark(key):
            return False
        
        # Validate category if provided
        if category and not self.is_valid_category(category):
            return False
        
        # Store in memory
        self.marks[key] = abs_path
        self.marks_metadata[key] = {
            'path': abs_path,
            'category': category,
            'tags': tags or []
        }
        self.list.append(f"{key}:{abs_path}")
        
        # Write to file
        try:
            with open(self.rc, "a") as file:
                if category or tags:
                    # New format with metadata
                    line = f"{key}:{abs_path}"
                    if category:
                        line += f"|category:{category}"
                    if tags:
                        line += f"|tags:{','.join(tags)}"
                    file.write(f"{line}\n")
                else:
                    # Old format for backward compatibility
                    file.write(f"{key}:{abs_path}\n")
            return True
        except Exception:
            return False
    
    def get_mark(self, key: str) -> Optional[str]:
        """Get bookmark path by key (backward compatible)."""
        if key in self.marks:
            return self.marks[key]
        
        # Check by index
        if key.isdigit():
            idx = int(key)
            if 0 <= idx < len(self.list):
                line = self.list[idx]
                if ':' in line:
                    return line.split(':', 1)[1].split('|')[0]
        
        return None
    
    def get_mark_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get bookmark with all metadata."""
        if key in self.marks_metadata:
            return self.marks_metadata[key].copy()
        
        # Check by index
        if key.isdigit():
            idx = int(key)
            if 0 <= idx < len(self.list):
                line = self.list[idx]
                if ':' in line:
                    bookmark_key = line.split(':', 1)[0]
                    if bookmark_key in self.marks_metadata:
                        return self.marks_metadata[bookmark_key].copy()
        
        return None
    
    def is_valid_category(self, category: str) -> bool:
        """Validate category name (alphanumeric, hyphens, underscores, slashes for hierarchy)."""
        if not category:
            return False
        
        # Allow hierarchical categories with slashes
        parts = category.split('/')
        for part in parts:
            if not re.match(r'^[a-zA-Z0-9_-]+$', part):
                return False
        
        return True
    
    def parse_category_path(self, category_path: str) -> List[str]:
        """Parse hierarchical category path into components."""
        return category_path.split('/') if category_path else []
    
    def list_by_category(self, category: str) -> List[Dict[str, Any]]:
        """List all bookmarks in a specific category."""
        results = []
        for key, metadata in self.marks_metadata.items():
            if metadata.get('category') == category:
                results.append({
                    'name': key,
                    'path': metadata['path'],
                    'category': metadata.get('category'),
                    'tags': metadata.get('tags', [])
                })
        return results
    
    def list_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """List all bookmarks with a specific tag."""
        results = []
        for key, metadata in self.marks_metadata.items():
            if tag in metadata.get('tags', []):
                results.append({
                    'name': key,
                    'path': metadata['path'],
                    'category': metadata.get('category'),
                    'tags': metadata.get('tags', [])
                })
        return results
    
    def update_mark_category(self, key: str, new_category: str) -> bool:
        """Update the category of an existing bookmark."""
        if key not in self.marks_metadata:
            return False
        
        if not self.is_valid_category(new_category):
            return False
        
        self.marks_metadata[key]['category'] = new_category
        self._rewrite_marks_file()
        return True
    
    def update_mark_tags(self, key: str, new_tags: List[str]) -> bool:
        """Update the tags of an existing bookmark."""
        if key not in self.marks_metadata:
            return False
        
        self.marks_metadata[key]['tags'] = new_tags
        self._rewrite_marks_file()
        return True
    
    def _rewrite_marks_file(self):
        """Rewrite the marks file with current metadata."""
        try:
            with open(self.rc, 'w') as file:
                for key, metadata in self.marks_metadata.items():
                    path = metadata['path']
                    category = metadata.get('category')
                    tags = metadata.get('tags', [])
                    
                    if category or tags:
                        # New format with metadata
                        line = f"{key}:{path}"
                        if category:
                            line += f"|category:{category}"
                        if tags:
                            line += f"|tags:{','.join(tags)}"
                        file.write(f"{line}\n")
                    else:
                        # Old format for backward compatibility
                        file.write(f"{key}:{path}\n")
            return True
        except Exception:
            return False
    
    def set_category_color(self, category: str, color: str):
        """Set the color for a category."""
        self.category_colors[category] = color
        self.save_config()
    
    def get_category_color(self, category: str) -> str:
        """Get the color for a category."""
        return self.category_colors.get(category, 'default')
    
    def list_all_categories(self) -> List[str]:
        """List all unique categories in use."""
        categories = set()
        for metadata in self.marks_metadata.values():
            if metadata.get('category'):
                categories.add(metadata['category'])
        return sorted(list(categories))
    
    def list_all_tags(self) -> List[str]:
        """List all unique tags in use."""
        tags = set()
        for metadata in self.marks_metadata.values():
            for tag in metadata.get('tags', []):
                tags.add(tag)
        return sorted(list(tags))
    
    def get_category_stats(self) -> Dict[str, int]:
        """Get usage statistics for categories."""
        stats = {}
        for metadata in self.marks_metadata.values():
            category = metadata.get('category')
            if category:
                stats[category] = stats.get(category, 0) + 1
        return dict(sorted(stats.items()))
    
    def get_tag_stats(self) -> Dict[str, int]:
        """Get usage statistics for tags."""
        stats = {}
        for metadata in self.marks_metadata.values():
            for tag in metadata.get('tags', []):
                stats[tag] = stats.get(tag, 0) + 1
        return dict(sorted(stats.items()))
    
    def list_marks(self):
        """List all marks (backward compatible)."""
        for i, mark in enumerate(self.list):
            print(f"{i} => {mark}")
    
    def del_mark(self, key: str) -> bool:
        """Delete a bookmark (backward compatible)."""
        if key.isdigit():
            idx = int(key)
            if 0 <= idx < len(self.list):
                line = self.list[idx]
                if ':' in line:
                    key = line.split(':', 1)[0]
            else:
                return False
        
        if key not in self.marks:
            return False
        
        # Remove from all data structures
        del self.marks[key]
        if key in self.marks_metadata:
            del self.marks_metadata[key]
        
        # Remove from list
        self.list = [line for line in self.list if not line.startswith(f"{key}:")]
        
        # Rewrite file
        return self._rewrite_marks_file()
    
    def add_mark(self, key: str, path: str) -> bool:
        """Add a bookmark without metadata (backward compatible)."""
        return self.add_mark_with_metadata(key, path)
    
    def update_mark(self, key: str, path: str) -> bool:
        """Update a bookmark's path (backward compatible)."""
        if self.del_mark(key):
            return self.add_mark_with_metadata(key, path)
        return False


# Create a compatibility layer for the original Marks class
class Marks(MarksEnhanced):
    """Backward compatible Marks class with enhanced features."""
    pass