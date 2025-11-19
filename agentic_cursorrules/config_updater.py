from pathlib import Path
import yaml
import re
import os

class ConfigUpdater:
    """Handles config.yaml generation and updates."""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_path = config_dir / 'config.yaml'
        
        # Default configuration sections
        self.defaults = {
            'important_dirs': [
                'components', 'pages', 'app', 'src', 'lib', 'utils', 'hooks', 
                'styles', 'public', 'assets', 'layouts', 'services', 'context', 'types'
            ],
            'exclude_dirs': [
                'node_modules', 'dist', 'build', '.next', 'out', '__pycache__', 
                'venv', 'env', '.git', 'coverage', 'tmp', 'temp'
            ],
            'include_extensions': [
                '.py', '.ts', '.tsx', '.js', '.jsx', '.json', '.css', '.scss', 
                '.html', '.md', '.vue', '.svelte'
            ]
        }
    
    def from_tree_text(self, tree_text, project_name="cursorrules-agentic"):
        """Generate config from tree text and save it."""
        print("\nUpdating config.yaml from tree text...")
        
        # Parse directories from tree text
        directories = self._parse_directories(tree_text)
        print(f"Found {len(directories)} directories in tree text")
        
        # Identify focus directories and exclude directories
        focus_dirs = self._identify_focus_dirs(directories)
        exclude_dirs = self._identify_exclude_dirs(directories)
        
        # Create or update config
        config = self._create_config(project_name, focus_dirs, exclude_dirs)
        
        # Save and verify
        return self._save_config(config)
    
    def _parse_directories(self, tree_text):
        """Extract directories from tree text."""
        directories = set()
        dir_pattern = re.compile(r'[│├└─\s]*([^/\n]+)/')
        
        for line in tree_text.split('\n'):
            if '/' in line:  # Directory lines end with /
                match = dir_pattern.search(line)
                if match:
                    dir_name = match.group(1).strip()
                    if dir_name and not dir_name.startswith('.'):
                        directories.add(dir_name)
        
        return directories
    
    def _identify_focus_dirs(self, directories):
        """Identify which directories should be in tree_focus."""
        focus_dirs = []
        
        # First add important directories
        important = set(self.defaults['important_dirs'])
        for dir_name in directories:
            if dir_name in important:
                focus_dirs.append(dir_name)
        
        # Then add common top-level directories
        common_top = ['api', 'app', 'src', 'backend', 'frontend', 'server', 'client']
        for dir_name in common_top:
            if dir_name in directories and dir_name not in focus_dirs:
                focus_dirs.append(dir_name)
        
        # If still empty, add remaining non-excluded directories
        if not focus_dirs:
            exclude_set = set(self.defaults['exclude_dirs'])
            focus_dirs = [d for d in directories if d not in exclude_set]
        
        return sorted(focus_dirs)
    
    def _identify_exclude_dirs(self, directories):
        """Identify which directories should be excluded."""
        exclude_dirs = []
        standard_excludes = set(self.defaults['exclude_dirs'])
        
        for dir_name in directories:
            if dir_name.lower() in [d.lower() for d in standard_excludes]:
                exclude_dirs.append(dir_name)
            # Also add binary/media directories
            elif dir_name.lower() in ['fonts', 'images', 'img', 'media', 'static']:
                exclude_dirs.append(dir_name)
        
        return sorted(exclude_dirs)
    
    def _create_config(self, project_name, focus_dirs, exclude_dirs):
        """Create properly structured config dictionary."""
        # Start with existing config if available
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            config = {}
        
        # Create ordered config with proper structure
        ordered_config = {}
        
        # Project title always first
        ordered_config['project_title'] = project_name
        
        # Tree focus always second
        ordered_config['tree_focus'] = focus_dirs
        
        # Add exclude dirs (with existing ones if present)
        if 'exclude_dirs' in config:
            exclude_set = set(config['exclude_dirs']).union(exclude_dirs)
            ordered_config['exclude_dirs'] = sorted(exclude_set)
        else:
            ordered_config['exclude_dirs'] = exclude_dirs
        
        # Add remaining sections from defaults if not present
        for section, values in self.defaults.items():
            if section != 'exclude_dirs' and section not in ordered_config:
                ordered_config[section] = config.get(section, values)
        
        return ordered_config
    
    def _save_config(self, config):
        """Save config to file and verify it was written."""
        try:
            # Save with consistent formatting
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            # Verify file was created
            if os.path.exists(self.config_path):
                file_size = os.path.getsize(self.config_path)
                print(f"✅ Config successfully written to {self.config_path} ({file_size} bytes)")
                print(f"  - Added {len(config['tree_focus'])} focus directories")
                print(f"  - Added {len(config['exclude_dirs'])} excluded directories")
                return True
            else:
                print(f"❌ Failed to create config file at {self.config_path}")
                return False
        except Exception as e:
            print(f"❌ Error saving config: {str(e)}")
            return False
