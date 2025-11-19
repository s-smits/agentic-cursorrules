from pathlib import Path
from typing import List
import os

def generate_agent_files(focus_dirs: List[str], config_dir: Path, project_dir: Path, output_dir: Path):
    """
    Generates agent-specific markdown files for each focus directory.
    """
    created_files = set()
    print(f"\n📝 Generating agent files in project directory: {project_dir}")

    # Create a reference to the tree_files directory
    tree_files_dir = config_dir / 'tree_files'

    for dir_path in focus_dirs:
        try:
            # Ensure dir_path is a Path object
            if isinstance(dir_path, str):
                dir_path = Path(dir_path)
            
            # Make sure we have a full resolved path
            if not dir_path.is_absolute():
                dir_path = (project_dir / dir_path).resolve()
            
            # Check if the directory exists
            if not dir_path.exists() or not dir_path.is_dir():
                print(f"⚠️ Skipping non-existent directory: {dir_path}")
                continue
                
            # Get directory name and parent for agent file naming
            dir_name = dir_path.name
            
            # Calculate relative path to project dir for naming
            try:
                rel_path = dir_path.relative_to(project_dir)
                parent_path = rel_path.parent if rel_path.parent != Path('.') else None
                parent_name = parent_path.name if parent_path else None
            except ValueError:
                # Handle case where dir_path is not relative to project_dir
                rel_path = dir_path.name
                parent_name = dir_path.parent.name
            
            # Generate the agent file name based on the path structure
            if str(rel_path).count('/') > 0 or str(rel_path).count('\\') > 0:
                # Handle paths with depth
                parts = str(rel_path).replace('\\', '/').split('/')
                agent_name = f"agent_{parts[0]}_{parts[-1]}.md"
            elif parent_name and parent_name != project_dir.name and not dir_name.startswith('__'):
                agent_name = f"agent_{parent_name}_{dir_name}.md"
            else:
                agent_name = f"agent_{dir_name}.md"
            
            if agent_name in created_files:
                print(f"⚠️ Skipping duplicate agent file: {agent_name}")
                continue
                
            # Use the last part of the path for the tree file name
            # Look in tree_files directory instead of config_dir directly
            tree_file = tree_files_dir / f'tree_{dir_name}.txt'
            tree_content = ""
            if tree_file.exists():
                with open(tree_file, 'r', encoding='utf-8') as f:
                    tree_content = f.read()
            else:
                print(f"⚠️ No tree file found at {tree_file}")
            
            # Generate appropriate directory description
            if parent_name and parent_name != project_dir.name:
                dir_description = f"the {dir_name} directory within {parent_name}"
            else:
                dir_description = f"the {dir_name} portion"
            
            agent_content = f"""You are an agent that specializes in {dir_description} of this project. Your expertise and responses should focus specifically on the code and files within this directory structure:

{tree_content}

When providing assistance, only reference and modify files within this directory structure. If you need to work with files outside this structure, list the required files and ask the user for permission first."""
            
            # Save to project directory
            output_path = project_dir / agent_name
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(agent_content)
            print(f"✅ Created {output_path}")
            
            created_files.add(agent_name)
            
        except Exception as e:
            print(f"❌ Error processing directory '{dir_path}': {str(e)}")
            import traceback
            traceback.print_exc()
