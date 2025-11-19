from pathlib import Path
import argparse
import sys
import shutil
import time
import yaml
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from agentic_cursorrules import (
    ConfigUpdater, 
    ProjectTreeGenerator, 
    generate_agent_files, 
    SmartCodeAnalyzer
)

console = Console()

def add_arguments(parser):
    """Add command-line arguments to the parser."""
    parser.add_argument('--recurring', action='store_true', 
                        help='Run the script every minute')
    parser.add_argument('--project-path', type=str, 
                        help='Path to the target project directory')
    parser.add_argument('--tree-input', action='store_true',
                        help='Provide a tree structure to generate config')
    parser.add_argument('--auto-config', action='store_true',
                        help='Automatically generate config from filesystem')
    parser.add_argument('--init', action='store_true',
                        help='Interactively create a new configuration')
    parser.add_argument('--verify-config', action='store_true',
                        help='Print the current config.yaml content')
    parser.add_argument('--project-title', type=str, default="cursorrules-agentic",
                        help='Project title for generated config')
    parser.add_argument('--use-detected', action='store_true',
                        help='Use detected_config.yaml if available')
    parser.add_argument('--local-agents', action='store_true',
                        help='Store agent files in script directory instead of project directory')

def main():
    try:
        parser = argparse.ArgumentParser(description="Generate domain-specific cursorrules for your project")
        add_arguments(parser)
        args = parser.parse_args()

        # Get the config directory (where the script is located)
        config_dir = Path(__file__).parent

        # Set project directory from argument or use parent of config dir
        # If running as a package entry point, we might be running from anywhere
        # So default to CWD if project-path not specified
        if args.project_path:
            project_dir = Path(args.project_path).resolve()
        else:
            project_dir = Path.cwd()
            
        console.print(Panel.fit(f"[bold blue]Agentic Cursorrules[/]\nProject: {project_dir}", border_style="blue"))
        
        # Determine which config file to use
        if args.auto_config:
            config_path = config_dir / 'config_auto.yaml'
            console.print(f"[dim]Using auto-generated config: {config_path.name}[/]")
        elif args.use_detected and (config_dir / 'detected_config.yaml').exists():
            config_path = config_dir / 'detected_config.yaml' 
            console.print(f"[dim]Using detected config: {config_path.name}[/]")
        else:
            config_path = config_dir / 'config_manual.yaml'
            # Fallback to config.yaml if manual doesn't exist
            if not config_path.exists() and (config_dir / 'config.yaml').exists():
                config_path = config_dir / 'config.yaml'
            console.print(f"[dim]Using config: {config_path.name}[/]")

        # Verify config if requested
        if args.verify_config:
            if config_path.exists():
                console.print(f"\n[bold]Current config content at {config_path}:[/]")
                with open(config_path, 'r') as f:
                    console.print(f.read(), style="cyan")
            else:
                console.print(f"\n[bold red]❌ No config found at {config_path}[/]")
            sys.exit(0)

        # Handle --init flag
        if args.init:
            console.print("[bold green]Initializing new configuration...[/]")
            project_title = Prompt.ask("Enter project title", default=project_dir.name)
            
            analyzer = SmartCodeAnalyzer(project_dir, config_dir)
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("Analyzing project structure...", total=None)
                focus_dirs = analyzer.analyze()
                progress.update(task, completed=True)
            
            console.print(f"[green]Found {len(focus_dirs)} potential domains.[/]")
            
            # Create default config
            default_config = {
                'project_title': project_title,
                'tree_focus': focus_dirs,
                'exclude_dirs': list(analyzer.exclude_dirs),
                'important_dirs': analyzer.standard_dirs,
                'include_extensions': list(analyzer.extensions)
            }
            
            # Write config
            target_config_path = config_dir / 'config.yaml'
            with open(target_config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
            
            console.print(f"[bold green]✅ Created configuration at {target_config_path}[/]")
            
            if not Confirm.ask("Generate agent files now?"):
                sys.exit(0)
                
            # Use the newly created config
            config_path = target_config_path

        # If tree input mode is enabled, handle that first
        elif args.tree_input:
            console.print("Please paste your file tree below (Ctrl+D or Ctrl+Z+Enter when done):")
            tree_text = ""
            try:
                while True:
                    line = input()
                    tree_text += line + "\n"
            except (EOFError, KeyboardInterrupt):
                pass
            
            if tree_text.strip():
                # Use the ConfigUpdater to process the tree
                updater = ConfigUpdater(config_dir)
                success = updater.from_tree_text(tree_text, args.project_title)
                
                if not success:
                    console.print("[bold red]❌ Failed to update config from tree text[/]")
                    sys.exit(1)
                
                # If we're just updating config, exit
                if not Confirm.ask("Continue with agent generation?"):
                    sys.exit(0)
            else:
                console.print("[bold red]❌ No tree text provided.[/]")
                sys.exit(1)
        
        # Auto-config from filesystem
        elif args.auto_config:
            analyzer = SmartCodeAnalyzer(project_dir, config_dir)
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("Analyzing project structure...", total=None)
                focus_dirs = analyzer.analyze()
                progress.update(task, completed=True)
                
            console.print(f"[bold green]Smart structure analysis complete![/]")
            
            # Verify the config was updated
            if config_path.exists():
                console.print("\n[bold]Verifying config contents:[/]")
                with open(config_path, 'r') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if i < 15:  # First 15 lines
                            console.print(f"  {line.rstrip()}", style="cyan")
                        else:
                            console.print("  ...", style="cyan")
                            break
            
            # If we're just updating config, exit
            if not Confirm.ask("\nContinue with agent generation?"):
                sys.exit(0)

        # Create default config file if it doesn't exist
        if not config_path.exists() and not args.init:
            # If detected_config exists and we want to use it, copy it
            if args.use_detected and (config_dir / 'detected_config.yaml').exists():
                shutil.copy2(config_dir / 'detected_config.yaml', config_path)
                console.print(f"[green]Copied detected_config.yaml to {config_path}[/]")
            else:
                console.print("[yellow]No config found. Run with --init or --auto-config to generate one.[/]")
                # Create minimal default config
                default_config = {
                    'project_title': args.project_title,
                    'tree_focus': ['src', 'app'] # Minimal default
                }
                # Only write if explicitly needed, but better to warn user
                # with open(config_path, 'w') as f:
                #    yaml.dump(default_config, f, default_flow_style=False)
                
                if not Confirm.ask("Create default config now?"):
                    sys.exit(1)
                    
                with open(config_path, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False)
                console.print(f"Created default config at {config_path}")

        # Ensure project directory exists
        if not project_dir.exists():
            console.print(f"[bold red]Error: Project directory {project_dir} does not exist[/]")
            sys.exit(1)

        # Copy .cursorrules to project directory if it doesn't exist
        cursorrules_example = config_dir / '.cursorrules.example'
        project_cursorrules = project_dir / '.cursorrules'
        if not project_cursorrules.exists() and cursorrules_example.exists():
            shutil.copy2(cursorrules_example, project_cursorrules)
            console.print(f"[green]Copied .cursorrules to {project_cursorrules}[/]")
        
        while True:  # Add while loop for recurring execution
            # Load config with error handling
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if not isinstance(config, dict) or 'tree_focus' not in config:
                        # Try to load other configs if primary is invalid
                        raise ValueError("Invalid config format: 'tree_focus' list is required")
                    focus_dirs = config.get('tree_focus', [])
                    if not isinstance(focus_dirs, list):
                        raise ValueError("'tree_focus' must be a list of directories")
            except Exception as e:
                console.print(f"[red]Error loading config.yaml: {str(e)}[/]")
                console.print("[yellow]Using default configuration...[/]")
                focus_dirs = ['src', 'app']
            
            generator = ProjectTreeGenerator(project_dir, config_dir)
            
            # Generate tree for each focus directory
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("Scanning directories...", total=None)
                found_dirs = generator.find_focus_dirs(project_dir, focus_dirs)
                progress.update(task, completed=True)
            
            # Keep track of processed directories
            processed_dirs = set()
            
            # Create a set of all configured paths for exclusion checking
            config_paths = {str(Path(fd)) for fd in focus_dirs}
            
            console.print(f"\n[bold]Generating trees for {len(found_dirs)} domains...[/]")
            
            for focus_dir in found_dirs:
                # Calculate relative path from project root
                rel_path = focus_dir.relative_to(project_dir)
                
                # Skip if this directory is already included in a parent tree
                if any(str(rel_path).startswith(str(pd)) for pd in processed_dirs 
                       if not any(part.startswith('__') for part in rel_path.parts)):
                    continue
                
                console.print(f"[blue]Processing: {focus_dir.name}[/]")
                # print("=" * (len(focus_dir.name) + 9))
                
                # Generate skip_dirs for subdirectories that will be processed separately
                skip_dirs = {str(d.relative_to(project_dir)) for d in found_dirs 
                            if str(d.relative_to(project_dir)).startswith(str(rel_path)) 
                            and d != focus_dir 
                            and any(part.startswith('__') for part in d.relative_to(project_dir).parts)}
                
                # Pass the config_paths to generate_tree
                # Get ASCII tree for file
                tree_content = generator.generate_tree(
                    focus_dir, 
                    skip_dirs=skip_dirs,
                    config_paths=config_paths
                )
                
                # Get Rich tree for display
                rich_tree = generator.generate_rich_tree(
                    focus_dir, 
                    skip_dirs=skip_dirs,
                    config_paths=config_paths
                )
                console.print(rich_tree)
                console.print("") # Spacer
                
                # Create tree_files directory if it doesn't exist
                tree_files_dir = config_dir / 'tree_files'
                tree_files_dir.mkdir(exist_ok=True)
                
                # Save tree files in tree_files directory
                with open(tree_files_dir / f'tree_{focus_dir.name}.txt', 'w', encoding='utf-8') as f:
                    f.write('\n'.join(tree_content))
                
                processed_dirs.add(rel_path)
            
            # Generate agent files in project directory
            output_dir = config_dir if args.local_agents else project_dir
            generate_agent_files([str(d.relative_to(project_dir)) for d in found_dirs], config_dir, project_dir, output_dir)

            if not args.recurring:
                break
                
            console.print(f"[dim]Waiting 60 seconds...[/]")
            time.sleep(60)  # Wait for 1 minute before next iteration
            
    except Exception as e:
        console.print(f"[bold red]Fatal error: {str(e)}[/]")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
