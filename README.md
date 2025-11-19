# agentic-cursorrules

**Give your AI agents a sense of place.**

Partition large codebases into domain-specific contexts for multi-agent workflows. This tool generates isolated markdown rule files that prevent agent conflicts by giving them explicit file-tree boundaries.

## Why this exists

We've all been there: you give an AI agent access to your whole repository, and suddenly it's "refactoring" a utility file that breaks five other modules you didn't even mention.

Traditional workflows drown agents in context they don't need. **Agentic-cursorrules** solves this by keeping each agent inside a clearly defined slice of the tree. Conversations stay focused, diffs stay local, and coordination overhead drops because your agents aren't trying to understand the entire universe at once.

## How it works

At its core, this tool is a boundary manager. It reads a configuration (which it can auto-detect for you!) mapping directory patterns to named domains.

When you run it, it resolves these domains, respects your `.gitignore` rules, and writes per-domain markdown files (like `@agent_backend_api.md`). These files describe the boundaries, relevant paths, and guardrails for that specific domain. You reference these in your IDE (Cursor, Windsurf, etc.) so your AI helper knows exactly where its lane is—and stays in it.

## Getting started

You'll need Python 3.10+ and [uv](https://github.com/astral-sh/uv) (because life is too short for slow installs).

```bash
# 1. Clone the repo
git clone https://github.com/s-smits/agentic-cursorrules.git .agentic-cursorrules
cd .agentic-cursorrules

# 2. Install dependencies
uv sync

# 3. Run the setup wizard
uv run agentic-cursorrules --init
```

The `--init` command is the friendliest way to start. It scans your project, guesses the logical domains, and builds a `config.yaml` for you interactively.

## Using the tool

### Auto-pilot mode

Just want to see what it finds?
```bash
uv run agentic-cursorrules --auto-config
```
This scans your repo and saves a `config_auto.yaml` without overwriting your main config. Great for checking if your folder structure makes sense to a machine.

### Taking control

For production use, you'll likely want to define your boundaries manually in `config.yaml`:

```yaml
project_title: "super-app"
tree_focus:
  - "backend/api"       # The API team's domain
  - "frontend/dashboard" # The dashboard team's domain
  - "shared/utils"      # Everyone's favorite dumping ground
```

Then generate the files:
```bash
uv run agentic-cursorrules
```

### Handy options

- `--init`: The friendly setup wizard.
- `--verify-config`: dry-run that shows you what config is loaded.
- `--tree-input`: Paste a text-based file tree if you want to generate config from a diagram.
- `--local-agents`: Keep the generated markdown files in the script directory (useful for testing without cluttering your actual project).
- `--recurring`: Run continuously every minute (good for active development sessions).

## What you get

For each domain, you get a markdown file like `@agent_backend_api.md`.

Reference this file when you start a chat with your AI. It contains a visual tree of *only* the files that matter to that domain, along with instructions to "only reference and modify files within this structure." It's like putting blinders on a racehorse—it keeps them moving forward, fast.

## Repository layout

Just so you know where things are:

```
.agentic-cursorrules/
├── agentic_cursorrules/          # The brains of the operation
│   ├── agent_generator.py        # Writes the markdown files
│   ├── config_updater.py         # Manages the yaml configs
│   ├── project_tree_generator.py # Draws those pretty trees
│   └── smart_analyzer.py         # Sherlock Holmes for your folder structure
├── main.py                       # The entry point
├── config.yaml                   # Your settings
└── pyproject.toml                # Dependencies
```
