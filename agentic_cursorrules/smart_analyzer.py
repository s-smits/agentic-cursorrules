from pathlib import Path
import os
import yaml
from collections import Counter
import functools

# Cache the extensions to avoid repeated network requests
@functools.lru_cache(maxsize=1)
def get_code_extensions():
    """Get all programming language file extensions from a comprehensive local list."""
    extensions = {
        # Web development
        '.html', '.htm', '.xhtml', '.css', '.scss', '.sass', '.less',
        '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.php', '.asp', '.aspx',
        
        # Python
        '.py', '.pyx', '.pyd', '.pyi', '.pyw', '.rpy', '.cpy', '.gyp', '.ipynb',
        
        # Java ecosystem
        '.java', '.class', '.jar', '.jsp', '.jspx', '.properties', '.groovy', '.gradle', '.kt', '.kts',
        
        # C/C++/C#
        '.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.c++', '.hxx', '.h++',
        '.cs', '.csproj', '.fs', '.fsx', '.fsi',
        
        # Ruby
        '.rb', '.erb', '.gemspec', '.rake', '.ru',
        
        # Go
        '.go', '.mod',
        
        # Rust
        '.rs', '.rlib', '.toml',
        
        # Swift/Objective-C
        '.swift', '.m', '.mm',
        
        # Shell/Bash/PowerShell
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.psm1', '.psd1',
        
        # Perl/PHP
        '.pl', '.pm', '.t', '.php', '.phtml',
        
        # Lua/Tcl/Forth
        '.lua', '.tcl', '.tk', '.fth', '.4th',
        
        # Configuration files
        '.json', '.yaml', '.yml', '.xml', '.ini', '.cfg', '.conf', '.config',
        '.toml', '.properties', '.env', '.rc', '.editorconfig',
        
        # Documentation
        '.md', '.markdown', '.rst', '.adoc', '.asciidoc', '.txt', '.textile',
        
        # Functional languages
        '.hs', '.lhs', '.elm', '.ml', '.mli', '.fs', '.fsi', '.fsx', '.fsscript',
        '.clj', '.cljs', '.cljc', '.edn', '.ex', '.exs', '.erl', '.hrl',
        
        # Other languages
        '.dart', '.r', '.rmd', '.jl', '.v', '.ada', '.adb', '.ads', '.d',
        '.nim', '.nims', '.cr', '.io', '.sml', '.sig', '.fun', '.scm', '.rkt',
        '.lisp', '.cl', '.el', '.elc', '.awk', '.tcl', '.tk', '.vhd', '.vhdl',
        '.spin', '.plm', '.elua', '.xc', '.mps', '.purs', '.b4x', '.gdscript',
        '.as', '.asc', '.angelscript', '.hx', '.hxml', '.rebol', '.r3', '.st',
        '.scratch', '.logo', '.pl', '.pro', '.m', '.apl', '.vala', '.e',
        '.rex', '.rexx', '.ps', '.sml', '.sig', '.alice', '.io', '.e',
        
        # Mobile development
        '.swift', '.m', '.mm', '.java', '.kt', '.gradle',
        '.plist', '.pbxproj', '.storyboard', '.xib',
                
        # Data/Analytics
        '.sas', '.mat', '.sql', '.spss', '.dax', '.j',
        
        # Game development
        '.gd', '.cs', '.lua', '.js', '.ts', '.cpp', '.h', '.unity',
        '.unityproj', '.prefab', '.scene', '.mat', '.anim',
        
        # Common config/documentation extensions
        '.md', '.json', '.yaml', '.yml', '.toml', '.xml', '.ini', '.conf', '.config', 
        '.env', '.rst', '.txt', '.lock', '.dockerfile', '.ipynb'
    }
    
    return extensions

class SmartCodeAnalyzer:
    """Smart code analyzer for efficient directory structure detection."""
    
    def __init__(self, project_dir, config_dir):
        self.project_dir = Path(project_dir)
        self.config_dir = Path(config_dir)
        self.config_path = config_dir / 'config.yaml'
        self.code_files = []
        self.code_dirs = Counter()
        
        # Common patterns and excluded directories
        self.standard_dirs = ['src', 'app', 'components', 'lib', 'utils', 'api']
        self.exclude_dirs = {
            'node_modules', 'dist', 'build', '.git', '__pycache__',
            'venv', 'env', '.next', 'out', 'coverage', 'tmp', 'temp'
        }
        
        # Get all code file extensions
        self.extensions = get_code_extensions()
        
    def analyze(self):
        """Perform multi-phase analysis of the project structure."""
        print(f"\n🔍 Analyzing project structure: {self.project_dir}")
        
        # Phase 1: Check for standard src directory
        focus_dirs = self._check_src_directory()
        
        # If we didn't find src pattern, do a more thorough scan
        if not focus_dirs:
            print("No standard src directory found. Performing detailed scan...")
            focus_dirs = self._scan_for_code_directories()
        
        # If we still don't have directories, use fallback
        if not focus_dirs:
            print("No code directories found. Using fallback structure...")
            focus_dirs = self._fallback_structure()
        
        # Update the config file
        self._update_config(focus_dirs)
        return focus_dirs
    
    def _check_src_directory(self):
        """Check for standard src directory pattern."""
        focus_dirs = []
        
        # Check for src directory
        src_dir = self.project_dir / 'src'
        if src_dir.exists() and src_dir.is_dir():
            print("Found 'src' directory. Checking subdirectories...")
            focus_dirs.append('src')
            
            # Check important immediate subdirectories
            for item in src_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Add src subdirectories as focus directories
                    rel_path = f"src/{item.name}"
                    focus_dirs.append(rel_path)
                    print(f"  ✅ Added subdirectory: {rel_path}")
        
        # Check for other common top-level directories
        for dir_name in self.standard_dirs:
            if dir_name != 'src':  # Already checked src
                dir_path = self.project_dir / dir_name
                if dir_path.exists() and dir_path.is_dir():
                    focus_dirs.append(dir_name)
                    print(f"✅ Found standard directory: {dir_name}")
        
        return focus_dirs
    
    def _scan_for_code_directories(self):
        """Scan the project for directories with code files."""
        print("Scanning for code files...")
        
        # Walk through the directory tree
        for root, dirs, files in os.walk(str(self.project_dir)):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not d.startswith('.')]
            
            # Check each file
            for file in files:
                # Check if the file has a code extension
                if any(file.endswith(ext) for ext in self.extensions):
                    rel_path = os.path.relpath(os.path.join(root, file), str(self.project_dir))
                    self.code_files.append(rel_path)
                    
                    # Count files in each directory
                    dir_path = os.path.dirname(rel_path)
                    if dir_path:
                        self.code_dirs[dir_path] += 1
                        
                        # Also count parent directories
                        parent = dir_path
                        while '/' in parent:
                            parent = os.path.dirname(parent)
                            self.code_dirs[parent] += 1
        
        # Identify significant directories (with at least 3 code files)
        significant_dirs = {d: count for d, count in self.code_dirs.items() 
                           if count >= 3 and d}
        
        if not significant_dirs:
            return []
            
        # Select top directories
        focus_dirs = []
        
        # Level 1: Top-level directories first
        top_level = sorted([d for d in significant_dirs if '/' not in d], 
                         key=lambda d: -significant_dirs[d])
        focus_dirs.extend(top_level)
        
        # Level 2: Add important subdirectories
        if len(top_level) <= 3:  # Only add subdirs if we don't have too many top dirs
            for top_dir in top_level:
                # Find subdirectories of this top directory
                subdirs = [d for d in significant_dirs if d.startswith(f"{top_dir}/")]
                
                # Take up to 2 most significant subdirectories
                subdirs = sorted(subdirs, key=lambda d: -significant_dirs[d])[:2]
                focus_dirs.extend(subdirs)
        
        print(f"Found {len(focus_dirs)} directories with code:")
        for d in focus_dirs:
            print(f"  - {d} ({self.code_dirs[d]} files)")
            
        return focus_dirs
    
    def _fallback_structure(self):
        """Use fallback structure if no code directories found."""
        focus_dirs = []
        
        # Check for any directories at the top level
        for item in self.project_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in self.exclude_dirs:
                focus_dirs.append(item.name)
        
        return focus_dirs
    
    def _update_config(self, focus_dirs):
        """Update config.yaml with the identified focus directories."""
        # Load existing config if available
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            config = {}
        
        # Update with new values
        config['project_title'] = self.project_dir.name
        config['tree_focus'] = focus_dirs
        
        # Ensure exclude_dirs exists
        if 'exclude_dirs' not in config:
            config['exclude_dirs'] = list(self.exclude_dirs)
        
        # Ensure ordered structure (project_title first, tree_focus second)
        ordered_config = {}
        ordered_config['project_title'] = config.pop('project_title')
        ordered_config['tree_focus'] = config.pop('tree_focus')
        ordered_config.update(config)  # Add remaining sections
        
        # Write the updated config
        with open(self.config_path, 'w') as f:
            yaml.dump(ordered_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"\n✅ Updated config.yaml with {len(focus_dirs)} focus directories")
        print(f"File saved to: {self.config_path}")
        return focus_dirs
