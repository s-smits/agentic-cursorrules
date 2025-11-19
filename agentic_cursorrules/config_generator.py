from pathlib import Path
import yaml
import re
import os
from collections import defaultdict
import sys

class ConfigGenerator:
    """Dynamic config.yaml generator from file tree or filesystem."""
    
    def __init__(self, project_dir=None, config_dir=None):
        """Initialize with project and config directories."""
        self.project_dir = project_dir or Path.cwd().parent
        self.config_dir = config_dir or Path(__file__).parent
        self.config_path = self.config_dir / 'config.yaml'
        
        # Default configuration sections
        self.defaults = {
            'important_dirs': [
                'components', 'pages', 'app', 'src', 'lib', 'utils', 'hooks', 
                'styles', 'public', 'assets', 'layouts', 'services', 'context', 'types'
            ],
            'exclude_dirs': [
                'node_modules', 'dist', 'build', '.next', 'out', '__pycache__', 
                'venv', 'env', '.git', 'coverage', 'tmp', 'temp', 'fonts', 'images', 'img'
            ],
            'include_extensions': [
                '.py', '.ts', '.tsx', '.js', '.jsx', '.json', '.css', '.scss', 
                '.html', '.md', '.vue', '.svelte'
            ]
        }
        
        print(f"ConfigGenerator initialized with:")
        print(f"  - Project directory: {self.project_dir}")
        print(f"  - Config path: {self.config_path}")
    
    def load_existing_config(self):
        """Load existing config.yaml if it exists."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
                print(f"Loaded existing config with {len(config.get('tree_focus', []))} focus directories")
                return config
        except FileNotFoundError:
            print(f"No existing config found at {self.config_path}, creating new one")
            return {}
    
    def save_config(self, config):
        """Save config to config.yaml."""
        try:
            print(f"Saving config to {self.config_path}")
            print(f"Config contains:")
            print(f"  - {len(config.get('tree_focus', []))} focus directories")
            print(f"  - {len(config.get('exclude_dirs', []))} excluded directories")
            
            # Ensure proper YAML formatting
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            # Verify file was written
            if os.path.exists(self.config_path):
                file_size = os.path.getsize(self.config_path)
                print(f"✅ Config successfully written ({file_size} bytes)")
                with open(self.config_path, 'r') as f:
                    # Print the first few lines to verify structure
                    print("\nConfig preview:")
                    for i, line in enumerate(f):
                        if i < 10:  # Print first 10 lines
                            print(f"  {line.rstrip()}")
                        else:
                            print("  ...")
                            break
            else:
                print(f"❌ Failed to write config file - file doesn't exist after save")
                
            return config
        except Exception as e:
            print(f"❌ Error saving config: {str(e)}")
            raise
    
    def merge_with_defaults(self, config):
        """Merge config with default values for missing sections."""
        result = config.copy()
        
        # Set project title if not present
        if 'project_title' not in result:
            result['project_title'] = self.project_dir.name
            print(f"Added project_title: {result['project_title']}")
            
        # Add default sections if missing
        for section, default_values in self.defaults.items():
            if section not in result:
                result[section] = default_values
                print(f"Added default {section} ({len(default_values)} items)")
                
        return result
    
    def generate_from_tree_text(self, tree_text):
        """Generate config from a tree text representation."""
        print("\nGenerating config from tree text...")
        
        # Parse the tree structure
        directories = self._parse_directories_from_tree(tree_text)
        print(f"Parsed {len(directories)} directories from tree text")
        
        # Generate focus dirs from the tree
        focus_dirs = self._identify_focus_dirs(directories)
        print(f"Identified {len(focus_dirs)} focus directories: {', '.join(focus_dirs)}")
        
        # Extract excluded dirs
        exclude_dirs = self._identify_exclude_dirs(directories)
        print(f"Identified {len(exclude_dirs)} exclude directories: {', '.join(exclude_dirs)}")
        
        # Load existing config
        config = self.load_existing_config()
        
        # Update with new values
        config['tree_focus'] = focus_dirs
        
        # Add excluded dirs without duplicates
        if 'exclude_dirs' in config:
            # Combine existing excludes with newly detected ones
            config['exclude_dirs'] = sorted(set(config['exclude_dirs']).union(exclude_dirs))
        else:
            config['exclude_dirs'] = exclude_dirs
        
        # Merge with defaults and save
        config = self.merge_with_defaults(config)
        
        # Ensure tree_focus is at the top after project_title
        ordered_config = {}
        ordered_config['project_title'] = config.pop('project_title')
        ordered_config['tree_focus'] = config.pop('tree_focus')
        ordered_config.update(config)  # Add remaining sections
        
        return self.save_config(ordered_config)
    
    def generate_from_filesystem(self):
        """Generate config by directly scanning the filesystem."""
        print("\nGenerating config from filesystem...")
        focus_dirs = []
        exclude_dirs = set(self.defaults['exclude_dirs'])
        
        # Scan first level directories
        for item in self.project_dir.iterdir():
            if not item.is_dir():
                continue
                
            # Skip common excluded directories
            if item.name in exclude_dirs or item.name.startswith('.'):
                continue
                
            # Check if this is a significant directory (contains code files)
            if self._is_significant_directory(item):
                focus_dirs.append(item.name)
                print(f"Found significant directory: {item.name}")
        
        print(f"Identified {len(focus_dirs)} focus directories: {', '.join(focus_dirs)}")
        
        # Load existing config
        config = self.load_existing_config()
        
        # Update with new values
        config['tree_focus'] = sorted(focus_dirs)
        config['exclude_dirs'] = sorted(exclude_dirs)
        
        # Merge with defaults and save
        config = self.merge_with_defaults(config)
        
        # Ensure tree_focus is at the top after project_title
        ordered_config = {}
        ordered_config['project_title'] = config.pop('project_title')
        ordered_config['tree_focus'] = config.pop('tree_focus')
        ordered_config.update(config)  # Add remaining sections
        
        return self.save_config(ordered_config)
    
    def _is_significant_directory(self, directory):
        """Check if directory contains code files or important subdirectories."""
        # Count code files
        code_files = 0
        for ext in self.defaults['include_extensions']:
            code_files += len(list(directory.glob(f"**/*{ext}")))
            if code_files > 2:  # If we find more than 2 code files, it's significant
                return True
                
        # Check for important subdirectories
        for subdir in directory.iterdir():
            if subdir.is_dir() and subdir.name in self.defaults['important_dirs']:
                return True
                
        return False
    
    def _parse_directories_from_tree(self, tree_text):
        """Extract directory structure from tree text."""
        directories = set()
        dir_pattern = re.compile(r'[│├└─\s]*([^/\n]+)/')
        
        for line in tree_text.split('\n'):
            # Match directory lines (ending with /)
            if '/' in line:
                match = dir_pattern.match(line)
                if match:
                    dir_name = match.group(1).strip()
                    if dir_name:
                        directories.add(dir_name)
        
        return directories
    
    def _identify_focus_dirs(self, directories):
        """Identify key directories for tree_focus."""
        # Prioritize important directories first
        focus_dirs = [d for d in directories if d in self.defaults['important_dirs']]
        
        # Add other potentially important directories
        common_focus_dirs = ['api', 'app', 'src', 'server', 'client', 'web', 'mobile', 'backend', 'frontend']
        for dir_name in common_focus_dirs:
            if dir_name in directories and dir_name not in focus_dirs:
                focus_dirs.append(dir_name)
        
        # If we still don't have focus dirs, add all non-excluded directories
        if not focus_dirs:
            focus_dirs = [d for d in directories if d not in self.defaults['exclude_dirs']]
        
        return sorted(focus_dirs)
    
    def _identify_exclude_dirs(self, directories):
        """Identify directories that should be excluded."""
        # Common directories to exclude 
        exclude_dirs = set()
        
        for dir_name in directories:
            if dir_name.lower() in [d.lower() for d in self.defaults['exclude_dirs']]:
                exclude_dirs.add(dir_name)
            # Binary/media content directories
            elif dir_name.lower() in ['fonts', 'images', 'img', 'media', 'static', 'assets']:
                exclude_dirs.add(dir_name)
        
        return sorted(list(exclude_dirs))