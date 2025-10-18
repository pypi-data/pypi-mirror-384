# devforge/cli.py
from __future__ import annotations
import logging
from pathlib import Path
import subprocess
import typer
from typing import Optional

from devforge.core.custom_generator import create_structure

app = typer.Typer(help="DevForge — generate project scaffolding quickly")

# basic templates (MVP) — يمكنك لاحقًا نقلها لملف templates/
TEMPLATES = {
    "fullstack": "sellwrite-ai/\n├── backend/\n│   ├── main.py\n│   ├── routes/\n│   └── models/\n├── frontend/\n│   ├── src/\n│   └── App.jsx\n└── README.md\n",
    "backend": "backend-app/\n├── app/\n│   ├── main.py\n│   └── models/\n└── README.md\n",
    "frontend": "frontend-app/\n├── src/\n│   └── App.jsx\n└── README.md\n",
}

def configure_logging(debug: bool = False, quiet: bool = False):
    level = logging.DEBUG if debug else (logging.ERROR if quiet else logging.INFO)
    fmt = "[%(levelname)s] %(message)s"
    logging.basicConfig(level=level, format=fmt)

@app.command()
def list_templates():
    """List built-in templates"""
    for name in sorted(TEMPLATES.keys()):
        typer.echo(f"- {name}")

@app.command()
def new(
    project_name: str = typer.Argument(..., help="Project directory name to create"),
    template: str = typer.Option("fullstack", help="Which template to use"),
    path: str = typer.Option(".", help="Parent path where the project folder will be created"),
    git: bool = typer.Option(False, "--git", help="Run git init after generation"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
    quiet: bool = typer.Option(False, "--quiet", help="Only show errors"),
):
    """Create a new project from a built-in template"""
    configure_logging(debug, quiet)
    logger = logging.getLogger(__name__)
    template = template.lower()
    if template not in TEMPLATES:
        logger.error("Template '%s' not found. Use 'devforge list-templates'.", template)
        raise typer.Exit(code=1)

    parent = Path(path).expanduser().resolve()
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
            logger.debug("Created parent path: %s", parent)
        except Exception as e:
            logger.error("Cannot create parent path '%s': %s", parent, e)
            raise typer.Exit(code=1)

    tree = TEMPLATES[template]
    # replace top folder name with project_name (remap)
    entries = tree.splitlines()
    # simple replace of top name:
    # find first non-empty line and replace leading name
    for i, ln in enumerate(entries):
        if ln.strip():
            top = ln.strip().split()[0]
            entries[i] = ln.replace(top, project_name, 1)
            break
    tree_text = "\n".join(entries)

    try:
        project_root = create_structure(str(parent), tree_text)
        if not project_root:
            raise RuntimeError("create_structure returned None")
        typer.secho(f"✅ Project created at: {project_root}", fg=typer.colors.GREEN)
    except Exception as e:
        logger.exception("Failed to create project: %s", e)
        raise typer.Exit(code=1)

    # extras: .gitignore and docker-compose if not exist
    try:
        gi = project_root.joinpath(".gitignore")
        if not gi.exists():
            gi.write_text("__pycache__/\nnode_modules/\n.env\n", encoding="utf-8")
        dc = project_root.joinpath("docker-compose.yml")
        if not dc.exists():
            dc.write_text("version: '3.8'\n", encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to write extras: %s", e)

    if git:
        try:
            subprocess.run(["git", "init", str(project_root)], check=True)
            typer.secho("git repository initialized", fg=typer.colors.GREEN)
        except Exception as e:
            logger.warning("git init failed: %s", e)

@app.command()
def custom(
    path: str = typer.Option(".", help="Parent path where the project will be created"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to text file containing ascii tree"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
    quiet: bool = typer.Option(False, "--quiet", help="Only show errors"),
):
    """Create a project from a custom ASCII tree file or interactive input"""
    configure_logging(debug, quiet)
    logger = logging.getLogger(__name__)
    parent = Path(path).expanduser().resolve()
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Cannot create parent path '%s': %s", parent, e)
            raise typer.Exit(code=1)

    if file:
        if not file.exists():
            logger.error("File %s not found", file)
            raise typer.Exit(code=1)
        tree_text = file.read_text(encoding="utf-8")
    else:
        base_path = typer.prompt("Enter base directory path", default=str(parent))
        typer.echo("Paste your directory structure below (end with an empty line):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                break
            lines.append(line)
        tree_text = "\n".join(lines)
        # use base_path
        parent = Path(base_path).expanduser().resolve()

    try:
        project_root = create_structure(str(parent), tree_text)
        if not project_root:
            raise RuntimeError("create_structure returned None")
        typer.secho(f"✅ Custom project created at: {project_root}", fg=typer.colors.GREEN)
    except Exception as e:
        logger.exception("Failed to create custom project: %s", e)
        raise typer.Exit(code=1)

@app.command()
def parse(tree_file: Path = typer.Argument(..., exists=True, readable=True, help="Path to ascii tree file to parse")):
    """Debug: parse and show entries"""
    txt = tree_file.read_text(encoding="utf-8")
    typer.echo("=== Structure preview ===\n")
    typer.echo(txt)
if __name__ == "__main__":
    app()
