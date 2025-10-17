#!/usr/bin/env python3
"""
Color management system for dirmarks categories and tags.
Provides terminal-aware color mapping with graceful degradation.
"""

import os
import sys
import json
from typing import Dict, Optional, List
from colorama import init, Fore, Back, Style, just_fix_windows_console

# Initialize colorama for cross-platform support
just_fix_windows_console()
init(autoreset=True)


class ColorManager:
    """Manages color configuration and terminal capability detection for dirmarks."""
    
    # Default color mapping for categories
    DEFAULT_CATEGORY_COLORS = {
        'work': Fore.BLUE,
        'personal': Fore.GREEN,
        'projects': Fore.CYAN,
        'development': Fore.MAGENTA,
        'research': Fore.YELLOW,
        'archive': Fore.WHITE,
        'temp': Fore.LIGHTBLACK_EX,
        'important': Fore.RED,
        'docs': Fore.LIGHTBLUE_EX,
        'config': Fore.LIGHTYELLOW_EX,
    }
    
    # Default color mapping for tags
    DEFAULT_TAG_COLORS = {
        'urgent': Fore.RED + Style.BRIGHT,
        'priority': Fore.YELLOW + Style.BRIGHT,
        'review': Fore.CYAN + Style.BRIGHT,
        'testing': Fore.MAGENTA + Style.BRIGHT,
        'production': Fore.RED,
        'development': Fore.GREEN,
        'staging': Fore.YELLOW,
        'client': Fore.BLUE,
        'internal': Fore.WHITE,
        'deprecated': Fore.LIGHTBLACK_EX,
    }
    
    # Fallback colors for hierarchical categories
    HIERARCHY_COLORS = [
        Fore.BLUE, Fore.GREEN, Fore.CYAN, Fore.MAGENTA,
        Fore.YELLOW, Fore.RED, Fore.WHITE, Fore.LIGHTBLUE_EX
    ]
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize ColorManager with optional custom config file."""
        self.config_file = config_file or os.path.expanduser('~/.dirmarks_colors.json')
        self.colors_enabled = self._detect_color_support()
        self.category_colors = {}
        self.tag_colors = {}
        self.load_config()
    
    def _detect_color_support(self) -> bool:
        """Detect if terminal supports colors with graceful degradation."""
        # Check if colors are explicitly disabled
        if os.environ.get('NO_COLOR'):
            return False
        
        # Check if output is redirected (not a TTY)
        if not sys.stdout.isatty():
            return False
        
        # Check TERM environment variable
        term = os.environ.get('TERM', '').lower()
        if 'color' in term or term in ['xterm', 'xterm-256color', 'screen', 'tmux']:
            return True
        
        # Check for Windows terminal capabilities
        if sys.platform == 'win32':
            # Windows 10+ supports ANSI colors
            return True
        
        # Default to True for Unix-like systems
        return True
    
    def load_config(self):
        """Load color configuration from file or use defaults."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                # Convert color names back to colorama constants
                self.category_colors = self._resolve_color_config(
                    config.get('categories', {}), self.DEFAULT_CATEGORY_COLORS
                )
                self.tag_colors = self._resolve_color_config(
                    config.get('tags', {}), self.DEFAULT_TAG_COLORS
                )
            else:
                # Use defaults
                self.category_colors = self.DEFAULT_CATEGORY_COLORS.copy()
                self.tag_colors = self.DEFAULT_TAG_COLORS.copy()
                
        except (json.JSONDecodeError, IOError):
            # Fall back to defaults on error
            self.category_colors = self.DEFAULT_CATEGORY_COLORS.copy()
            self.tag_colors = self.DEFAULT_TAG_COLORS.copy()
    
    def _resolve_color_config(self, config: Dict[str, str], defaults: Dict[str, str]) -> Dict[str, str]:
        """Resolve color configuration from stored names to colorama constants."""
        resolved = defaults.copy()
        
        # Map color names to colorama constants
        color_map = {
            'RED': Fore.RED, 'GREEN': Fore.GREEN, 'BLUE': Fore.BLUE,
            'CYAN': Fore.CYAN, 'MAGENTA': Fore.MAGENTA, 'YELLOW': Fore.YELLOW,
            'WHITE': Fore.WHITE, 'BLACK': Fore.BLACK,
            'LIGHTRED_EX': Fore.LIGHTRED_EX, 'LIGHTGREEN_EX': Fore.LIGHTGREEN_EX,
            'LIGHTBLUE_EX': Fore.LIGHTBLUE_EX, 'LIGHTCYAN_EX': Fore.LIGHTCYAN_EX,
            'LIGHTMAGENTA_EX': Fore.LIGHTMAGENTA_EX, 'LIGHTYELLOW_EX': Fore.LIGHTYELLOW_EX,
            'LIGHTWHITE_EX': Fore.LIGHTWHITE_EX, 'LIGHTBLACK_EX': Fore.LIGHTBLACK_EX,
        }
        
        for key, color_name in config.items():
            if color_name in color_map:
                resolved[key] = color_map[color_name]
        
        return resolved
    
    def save_config(self):
        """Save current color configuration to file."""
        try:
            # Convert colorama constants to storable names
            config = {
                'categories': self._serialize_colors(self.category_colors),
                'tags': self._serialize_colors(self.tag_colors),
            }
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except IOError:
            # Silently fail if can't save config
            pass
    
    def _serialize_colors(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Convert colorama constants to storable color names."""
        reverse_map = {
            Fore.RED: 'RED', Fore.GREEN: 'GREEN', Fore.BLUE: 'BLUE',
            Fore.CYAN: 'CYAN', Fore.MAGENTA: 'MAGENTA', Fore.YELLOW: 'YELLOW',
            Fore.WHITE: 'WHITE', Fore.BLACK: 'BLACK',
            Fore.LIGHTRED_EX: 'LIGHTRED_EX', Fore.LIGHTGREEN_EX: 'LIGHTGREEN_EX',
            Fore.LIGHTBLUE_EX: 'LIGHTBLUE_EX', Fore.LIGHTCYAN_EX: 'LIGHTCYAN_EX',
            Fore.LIGHTMAGENTA_EX: 'LIGHTMAGENTA_EX', Fore.LIGHTYELLOW_EX: 'LIGHTYELLOW_EX',
            Fore.LIGHTWHITE_EX: 'LIGHTWHITE_EX', Fore.LIGHTBLACK_EX: 'LIGHTBLACK_EX',
        }
        
        serialized = {}
        for key, color_code in colors.items():
            # Handle composite colors (color + style)
            base_color = color_code.split(Style.BRIGHT)[0] if Style.BRIGHT in color_code else color_code
            if base_color in reverse_map:
                serialized[key] = reverse_map[base_color]
        
        return serialized
    
    def get_category_color(self, category: str) -> str:
        """Get color for a category with hierarchical support."""
        if not self.colors_enabled:
            return ''
        
        # Direct match first
        if category in self.category_colors:
            return self.category_colors[category]
        
        # Check hierarchical categories (e.g., 'work/web/frontend')
        parts = category.split('/')
        for i, part in enumerate(parts):
            # Try progressively more specific matches
            partial_category = '/'.join(parts[:i+1])
            if partial_category in self.category_colors:
                return self.category_colors[partial_category]
            
            # Try individual parts
            if part in self.category_colors:
                return self.category_colors[part]
        
        # Fall back to color based on hash for consistency
        color_index = hash(category) % len(self.HIERARCHY_COLORS)
        return self.HIERARCHY_COLORS[color_index]
    
    def get_tag_color(self, tag: str) -> str:
        """Get color for a tag."""
        if not self.colors_enabled:
            return ''
        
        if tag in self.tag_colors:
            return self.tag_colors[tag]
        
        # Fall back to category color system for unknown tags
        return self.get_category_color(tag)
    
    def colorize_category(self, category: str) -> str:
        """Apply color to category text."""
        if not self.colors_enabled or not category:
            return category
        
        color = self.get_category_color(category)
        return f"{color}{category}{Style.RESET_ALL}"
    
    def colorize_tag(self, tag: str) -> str:
        """Apply color to tag text."""
        if not self.colors_enabled or not tag:
            return tag
        
        color = self.get_tag_color(tag)
        return f"{color}{tag}{Style.RESET_ALL}"
    
    def colorize_tags(self, tags: List[str]) -> List[str]:
        """Apply colors to a list of tags."""
        if not self.colors_enabled:
            return tags
        
        return [self.colorize_tag(tag) for tag in tags]
    
    def set_category_color(self, category: str, color: str):
        """Set custom color for a category."""
        color_map = {
            'red': Fore.RED, 'green': Fore.GREEN, 'blue': Fore.BLUE,
            'cyan': Fore.CYAN, 'magenta': Fore.MAGENTA, 'yellow': Fore.YELLOW,
            'white': Fore.WHITE, 'black': Fore.BLACK,
        }
        
        if color.lower() in color_map:
            self.category_colors[category] = color_map[color.lower()]
            self.save_config()
    
    def set_tag_color(self, tag: str, color: str):
        """Set custom color for a tag."""
        color_map = {
            'red': Fore.RED, 'green': Fore.GREEN, 'blue': Fore.BLUE,
            'cyan': Fore.CYAN, 'magenta': Fore.MAGENTA, 'yellow': Fore.YELLOW,
            'white': Fore.WHITE, 'black': Fore.BLACK,
        }
        
        if color.lower() in color_map:
            self.tag_colors[tag] = color_map[color.lower()]
            self.save_config()
    
    def disable_colors(self):
        """Disable color output."""
        self.colors_enabled = False
    
    def enable_colors(self):
        """Enable color output if terminal supports it."""
        self.colors_enabled = self._detect_color_support()


# Global color manager instance
_color_manager = None

def get_color_manager() -> ColorManager:
    """Get or create the global color manager instance."""
    global _color_manager
    if _color_manager is None:
        _color_manager = ColorManager()
    return _color_manager