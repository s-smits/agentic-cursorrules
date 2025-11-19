from pathlib import Path
from typing import List, Set
import yaml
from gitignore_parser import parse_gitignore
import os
from collections import defaultdict
from rich.tree import Tree
from rich.text import Text

class ProjectTreeGenerator:
    def __init__(self, project_root: Path, config_dir: Path):
        """
        Initializes the generator with gitignore-based exclusions and the project root.
        """
        self.project_root = project_root
        self.config_dir = config_dir
        
        # Load config from YAML in the config directory
        config_path = config_dir / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Set file extensions from config
        self.INCLUDE_EXTENSIONS: Set[str] = set(config.get('include_extensions', []))
        self.IMPORTANT_DIRS = set(config.get('important_dirs', []))
        self.EXCLUDE_DIRS = set(config.get('exclude_dirs', []))
        
        # Initialize gitignore matcher
        gitignore_path = project_root / '.gitignore'
        if gitignore_path.exists():
            self.matches = parse_gitignore(gitignore_path)
        else:
            # Create temporary gitignore with exclude_dirs from config
            temp_gitignore = project_root / '.temp_gitignore'
            with open(temp_gitignore, 'w') as f:
                f.write('\n'.join(f'{dir}/' for dir in self.EXCLUDE_DIRS))
            self.matches = parse_gitignore(temp_gitignore)
            temp_gitignore.unlink()

    def generate_tree(self, directory: Path, file_types: List[str] = None, max_depth: int = 3, skip_dirs: Set[str] = None, config_paths: Set[str] = None) -> List[str]:
        """
        Generates a visual tree representation of the directory structure using Rich.
        Returns a list of strings for file output.
        """
        # We need two versions: one for the file (ASCII) and one for display (Rich Tree)
        # For now, we'll keep the ASCII generation for the file content as agents might parse it better
        # but we could add a method to return a Rich Tree object for display if needed.
        
        tree_lines = []
        skip_dirs = skip_dirs or set()
        config_paths = config_paths or set()

        def _generate_tree(dir_path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return

            items = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_file(), x.name))
            for i, item in enumerate(items):
                rel_path = str(item.relative_to(self.project_root))
                
                if (item.name in self.EXCLUDE_DIRS or 
                    self.matches(str(item)) or 
                    rel_path in skip_dirs or
                    (item.is_dir() and any(cp.startswith(rel_path) for cp in config_paths))):
                    # print(f"Skipping {rel_path}")  # Debug print
                    continue

                is_last = i == len(items) - 1
                display_path = item.name

                if item.is_dir():
                    tree_lines.append(f"{prefix}{'└── ' if is_last else '├── '}{display_path}/")
                    _generate_tree(item, prefix + ('    ' if is_last else '│   '), depth + 1)
                elif item.is_file():
                    extensions_to_check = file_types if file_types else self.INCLUDE_EXTENSIONS
                    if any(item.name.endswith(ext) for ext in extensions_to_check):
                        tree_lines.append(f"{prefix}{'└── ' if is_last else '├── '}{display_path}")

            return tree_lines

        return _generate_tree(directory)

    def generate_rich_tree(self, directory: Path, file_types: List[str] = None, max_depth: int = 3, skip_dirs: Set[str] = None, config_paths: Set[str] = None) -> Tree:
        """
        Generates a Rich Tree object for console display.
        """
        skip_dirs = skip_dirs or set()
        config_paths = config_paths or set()
        
        root_tree = Tree(f":open_file_folder: [bold blue]{directory.name}[/]")

        def _build_tree(dir_path: Path, parent_tree: Tree, depth: int = 0):
            if depth > max_depth:
                return

            items = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_file(), x.name))
            for item in items:
                rel_path = str(item.relative_to(self.project_root))
                
                if (item.name in self.EXCLUDE_DIRS or 
                    self.matches(str(item)) or 
                    rel_path in skip_dirs or
                    (item.is_dir() and any(cp.startswith(rel_path) for cp in config_paths))):
                    continue

                if item.is_dir():
                    branch = parent_tree.add(f":file_folder: [bold blue]{item.name}[/]")
                    _build_tree(item, branch, depth + 1)
                elif item.is_file():
                    extensions_to_check = file_types if file_types else self.INCLUDE_EXTENSIONS
                    if any(item.name.endswith(ext) for ext in extensions_to_check):
                        parent_tree.add(f":page_facing_up: {item.name}")

        _build_tree(directory, root_tree)
        return root_tree

    def find_focus_dirs(self, directory: Path, focus_dirs: List[str]) -> List[Path]:
        """
        Finds directories matching the focus names, handling nested paths and special cases.
        """
        found_dirs = []
        print(f"\n🔍 Looking for focus directories in: {directory}")
        
        # First, normalize all focus dirs and preserve special paths
        normalized_focus_dirs = []
        for fd in focus_dirs:
            # Preserve paths with double underscores
            if '__' in fd:
                normalized_focus_dirs.append(Path(fd))
            # Convert single underscores to paths
            elif '_' in fd and '/' not in fd:
                normalized_focus_dirs.append(Path(fd.replace('_', '/')))
            else:
                normalized_focus_dirs.append(Path(fd))
        
        # Sort by path depth (shortest first) to handle parent folders first
        normalized_focus_dirs.sort(key=lambda p: len(p.parts))
        
        # Try exact directory matching first
        for focus_path in normalized_focus_dirs:
            try:
                # Check for exact path
                target_path = (directory / focus_path).resolve()
                if target_path.exists() and target_path.is_dir():
                    print(f"✅ Found exact path: {target_path}")
                    found_dirs.append(target_path)
                    continue
                
                # Check simple name at top level
                simple_path = (directory / focus_path.name).resolve()
                if simple_path.exists() and simple_path.is_dir():
                    print(f"✅ Found directory by name: {simple_path}")
                    found_dirs.append(simple_path)
                    continue
                
                # Look one level deeper for matching directory name
                for item in directory.iterdir():
                    if item.is_dir():
                        nested_path = (item / focus_path.name).resolve()
                        if nested_path.exists() and nested_path.is_dir():
                            print(f"✅ Found nested directory: {nested_path}")
                            found_dirs.append(nested_path)
                            break
                
                # Still not found - try searching by walking the tree
                if not any(focus_path.name in str(d) for d in found_dirs):
                    print(f"🔍 Searching for '{focus_path.name}' in directory tree...")
                    # Walk no more than 3 levels deep to find matching directory names
                    for root, dirs, _ in os.walk(str(directory)):
                        depth = root[len(str(directory)):].count(os.sep)
                        if depth > 3:  # Limit depth
                            continue
                        
                        for dir_name in dirs:
                            if dir_name == focus_path.name:
                                match_path = Path(os.path.join(root, dir_name))
                                print(f"✅ Found directory by walking tree: {match_path}")
                                found_dirs.append(match_path)
                                break
                        
                        # Break after finding first match to avoid too many results
                        if any(focus_path.name in str(d) for d in found_dirs):
                            break
                
            except Exception as e:
                print(f"⚠️ Error processing {focus_path}: {str(e)}")
        
        # If we found no directories, fall back to scanning for code directories
        if not found_dirs:
            print("\n⚠️ Exact matching failed. Falling back to code directory detection...")
            # Look for directories with most code files
            code_dirs = self._find_code_directories(directory)
            if code_dirs:
                found_dirs = code_dirs
        
        print(f"\n📂 Final directories found: {len(found_dirs)}")
        for d in found_dirs:
            print(f"  - {d}")
        
        return found_dirs

    def _find_code_directories(self, directory: Path, max_dirs=5) -> List[Path]:
        """
        Find directories containing the most code files by scanning the filesystem.
        Used as a fallback when directory names aren't found.
        """
        print(f"Scanning for code files in {directory}...")
        
        # Common file extensions to look for
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss',
            '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.php',
            '.vue', '.svelte', '.json', '.yaml', '.yml', '.md'
        }
        
        # Directories to exclude
        exclude_dirs = {
            'node_modules', 'dist', 'build', '.git', '__pycache__',
            'venv', 'env', '.next', 'out', 'coverage', 'tmp', 'temp'
        }
        
        # Count code files per directory
        dir_counts = defaultdict(int)
        
        try:
            # Walk through the directory tree
            for root, dirs, files in os.walk(str(directory)):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
                
                # Skip if we're too deep
                depth = root[len(str(directory)):].count(os.sep)
                if depth > 4:  # Limit depth to 4 levels
                    continue
                
                # Count code files in this directory
                code_file_count = sum(1 for f in files if any(f.endswith(ext) for ext in code_extensions))
                
                if code_file_count > 0:
                    rel_path = os.path.relpath(root, str(directory))
                    if rel_path == '.':
                        continue  # Skip root
                    
                    # Record directory and count
                    dir_counts[rel_path] += code_file_count
        
            # Get the top directories by file count
            top_dirs = sorted(dir_counts.items(), key=lambda x: -x[1])[:max_dirs]
            
            # Convert to Path objects
            result = []
            for rel_path, count in top_dirs:
                full_path = (directory / rel_path).resolve()
                if full_path.exists():
                    print(f"✅ Found code directory: {full_path} ({count} files)")
                    result.append(full_path)
            
            return result
        
        except Exception as e:
            print(f"⚠️ Error scanning for code directories: {str(e)}")
            return []
