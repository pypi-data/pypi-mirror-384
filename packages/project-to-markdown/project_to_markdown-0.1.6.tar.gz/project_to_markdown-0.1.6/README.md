# project-to-markdown

A bidirectional tool to export Python projects to Markdown and recreate projects from Markdown files.

## Features

### Export (project-to-markdown)
- Recursively scans a project directory
- Includes code and markdown files (configurable)
- Outputs a single, well-structured Markdown file
- Supports file/directory exclusion and size limits
- Git-aware (respects .gitignore when requested)

### Import (markdown-to-project)
- Recreates project structure from exported Markdown files
- Preserves directory hierarchy and file contents
- Handles UTF-8 encoding properly
- Safe overwrite protection

## Installation

```sh
pip install project-to-markdown
```

Or, for local development:

```sh
pip install .
```

## Usage

### Export a Project to Markdown

```sh
project-to-markdown --root path/to/project --output export.md --include-exts .py,.md --exclude-dirs .venv,.git --title "My Project"
```

#### Export Options
- `--root`         Root directory of the project (default: current directory)
- `--output`       Output Markdown file (default: project_export.md)
- `--title`        Title for the Markdown document
- `--include-exts` Comma-separated list of file extensions to include (default: .py,.md)
- `--exclude-dirs` Comma-separated list of directory names to exclude
- `--exclude-files`Comma-separated list of file names to exclude
- `--use-gitignore`Respect .gitignore files in the export
- `--all-files`    Include all files, not just tracked files
- `--max-bytes`    Maximum size of files to include (default: 10,000,000)
- `--max-lines`    Maximum number of lines to include per file (0 = unlimited)
- `--tree-from-files` Build tree from included files (mirrors gitignore/filters)

### Recreate a Project from Markdown

```sh
python -m project_to_markdown.markdown_to_project -i exported_project.md -o recreated_project
```

#### Import Options
- `-i, --input`    Input markdown file containing the project source (required)
- `-o, --output`   Output directory to recreate the project in (default: 'recreated_project')
- `--overwrite`    Allow writing into an existing, non-empty output directory

## Examples

### Export Example
```sh
project-to-markdown --root my_project --output my_project.md --title "My Project"
```

### Import Example
```sh
markdown-to-project -i my_project.md -o recreated_project --overwrite
```

## Project Structure

```
codebase_to_markdown/
├── project_to_markdown/
│   ├── __init__.py
│   ├── project_to_markdown.py    # Export script - project to markdown
│   └── markdown_to_project.py    # Import script - markdown to project
├── pyproject.toml
├── README.md
├── MANIFEST.in
├── example.md
└── __init__.py
```

## License

MIT License

---

Created by Benaya Trabelsi. Contributions welcome!
benaya7@gmail.com
