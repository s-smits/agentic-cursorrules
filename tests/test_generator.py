import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from agentic_cursorrules.project_tree_generator import ProjectTreeGenerator

def test_project_tree_generator(tmp_path):
    """Test that ProjectTreeGenerator correctly ignores files."""
    
    # Setup directory structure
    project_root = tmp_path
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Create config file
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
project_title: test-project
tree_focus:
  - src
exclude_dirs:
  - ignored_dir
include_extensions:
  - .py
  - .txt
""")
    
    # Create source files
    src_dir = project_root / "src"
    src_dir.mkdir()
    (src_dir / "main.py").touch()
    (src_dir / "readme.txt").touch()
    (src_dir / "ignored.log").touch()
    
    # Create ignored directory
    ignored_dir = project_root / "ignored_dir"
    ignored_dir.mkdir()
    (ignored_dir / "file.py").touch()
    
    # Initialize generator
    generator = ProjectTreeGenerator(project_root, config_dir)
    
    # Generate tree lines
    tree_lines = generator.generate_tree(src_dir)
    
    # Verify contents
    output = "\n".join(tree_lines)
    assert "main.py" in output
    assert "readme.txt" in output
    assert "ignored.log" not in output # Should be ignored based on extension
    
    # Verify exclude dirs
    # We can't easily test the excluded directory with generate_tree(src_dir) 
    # because it only walks the passed directory.
    # But we can verify attributes
    assert "ignored_dir" in generator.EXCLUDE_DIRS

def test_rich_tree_generation(tmp_path):
    """Test that rich tree generation runs without error."""
    project_root = tmp_path
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    config_file = config_dir / "config.yaml"
    config_file.write_text("tree_focus: []\n")
    
    generator = ProjectTreeGenerator(project_root, config_dir)
    tree = generator.generate_rich_tree(project_root)
    
    # Rich Tree label can be a string or Text object depending on how it was created
    # Our implementation uses a string with markup: f":open_file_folder: [bold blue]{directory.name}[/]"
    # So we check the string representation
    assert project_root.name in str(tree.label)
