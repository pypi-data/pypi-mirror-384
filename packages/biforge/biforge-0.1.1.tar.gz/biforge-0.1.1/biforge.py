"""
biforge - Scaffold Power BI projects instantly from templates.

A universal CLI tool to initialize Power BI projects from any .pbip template.
It handles intelligent renaming of files, folders, and updates JSON content to maintain path integrity.

[project]
requires-python = ">=3.10"
dependencies = [
  "typer>=0.12.0",
  "rich>=13.0.0",
]
"""

import typer
import shutil
import json
import re
from pathlib import Path
from datetime import datetime
from rich.console import Console
from typing import List, Any, Optional

# --- Setup ---
app = typer.Typer(
    add_completion=False,
    help="biforge - Scaffold Power BI projects instantly from templates.",
    # Removemos invoke_without_command del Typer principal
)
console = Console()
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "config.json"

# --- Helper Functions ---
def load_config() -> dict | None:
    try:
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    console.print(f"[green]✓ Configuration saved to {CONFIG_FILE}[/green]")


def is_valid_foldername(name: str) -> bool:
    if not name or Path(name).is_absolute():
        return False
    return not bool(re.search(r'[<>:"/\\|?*]', name))


def run_setup_wizard() -> dict:
    console.print("[bold yellow]🚀 Welcome! Let's configure your .pbip project template.[/bold yellow]")
    while True:
        template_path_str = console.input("[bold]Drag your template folder here and press Enter: [/bold]")
        cleaned_path_str = template_path_str.strip().strip('"')
        template_path = Path(cleaned_path_str).resolve()
        if template_path.is_dir():
            try:
                discover_template_base_name(template_path)
                config = {"template_path": str(template_path)}
                save_config(config)
                return config
            except ValueError as e:
                console.print(f"[bold red]Error: {e}[/bold red]")
        else:
            console.print(f"[bold red]Error: Path is not a valid directory. Try again.[/bold red]")

def update_json_file(file_path: Path, key_path: List[Any], new_value: Any):
    if not file_path.exists():
        console.print(f"[yellow]  - Warning: Could not update '{file_path.name}', file not found.[/yellow]")
        return
    try:
        with open(file_path, "r+", encoding='utf-8') as f:
            data = json.load(f)
            temp_data = data
            for key in key_path[:-1]:
                temp_data = temp_data[key]
            temp_data[key_path[-1]] = new_value
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        console.print(f"[green]  ✓ Updated '{file_path.name}'[/green]")
    except (KeyError, IndexError):
        console.print(f"[red]  - Error: Key path {key_path} not found in '{file_path.name}'.[/red]")
    except Exception as e:
        console.print(f"[red]  - Error: Failed to update '{file_path.name}'. Details: {e}[/red]")

def discover_template_base_name(template_path: Path) -> str:
    pbip_files = list(template_path.glob("*.pbip"))
    if not pbip_files:
        raise ValueError("Invalid template: No *.pbip file found in directory.")
    if len(pbip_files) > 1:
        raise ValueError("Invalid template: Multiple *.pbip files found, which is ambiguous.")
    base_name = pbip_files[0].stem
    console.print(f"Discovered template base name: [bold cyan]'{base_name}'[/bold cyan]")
    return base_name

def post_process_project(destination_dir: Path, project_name: str, template_base_name: str):
    console.print("[cyan]Starting Power BI structure post-processing...[/cyan]")
    old_pbip_path = destination_dir / f"{template_base_name}.pbip"
    old_report_dir = destination_dir / f"{template_base_name}.Report"
    old_model_dir = destination_dir / f"{template_base_name}.SemanticModel"
    new_pbip_path = destination_dir / f"{project_name}.pbip"
    new_report_dir = destination_dir / f"{project_name}.Report"
    new_model_dir = destination_dir / f"{project_name}.SemanticModel"
    pbir_file_path = new_report_dir / "definition.pbir"
    report_platform_file = new_report_dir / ".platform"
    model_platform_file = new_model_dir / ".platform"

    console.print("Renaming files and folders...")
    if old_pbip_path.exists(): old_pbip_path.rename(new_pbip_path)
    if old_report_dir.exists(): old_report_dir.rename(new_report_dir)
    if old_model_dir.exists(): old_model_dir.rename(new_model_dir)

    console.print("Updating internal project references...")
    update_json_file(new_pbip_path, ['artifacts', 0, 'report', 'path'], new_report_dir.name)
    update_json_file(pbir_file_path, ['datasetReference', 'byPath', 'path'], f"../{new_model_dir.name}")
    update_json_file(report_platform_file, ['metadata', 'displayName'], project_name)
    update_json_file(model_platform_file, ['metadata', 'displayName'], project_name)


# --- The Engine ---
def run_project_creation_logic(project_name: str):
    """The core engine for creating a project. Called by CLI commands."""
    if not project_name:
        console.print("[bold red]Error:[/bold red] Project name is required.")
        console.print("Usage: [cyan]biforge create \"My Report\"[/cyan]")
        console.print("Or shortcut: [cyan]biforge \"My Report\"[/cyan]")
        raise typer.Exit(code=1)

    config = load_config()
    if not config:
        config = run_setup_wizard()

    template_path = Path(config["template_path"])
    try:
        template_base_name = discover_template_base_name(template_path)
    except ValueError as e:
        console.print(f"[bold red]Template Error: {e}[/bold red]")
        raise typer.Exit(code=1)

    if not is_valid_foldername(project_name):
        console.print(f"[bold red]Error: Invalid project name '{project_name}'. Avoid characters like /\\:*?\"<>|[/bold red]")
        raise typer.Exit(code=1)

    current_date = datetime.now().strftime("%Y%m")
    new_project_folder_name = f"{current_date} - {project_name}"
    destination_dir = Path.cwd() / new_project_folder_name

    if destination_dir.exists():
        console.print(f"[bold red]Error: Directory '{destination_dir.name}' already exists.[/bold red]")
        raise typer.Exit(code=1)

    try:
        with console.status("[bold cyan]Copying template files...[/bold cyan]", spinner="dots") as status:
            shutil.copytree(template_path, destination_dir)
            status.update("[bold cyan]Post-processing PBI project...[/bold cyan]")
            post_process_project(destination_dir, project_name, template_base_name)

        console.print(f"[bold green]✓ Success! Project created and configured at:[/bold green] \n[underline]{destination_dir}[/underline]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f'  [cyan]1. cd "{new_project_folder_name}"[/cyan]')
        console.print("  [cyan]2. Open the .pbip file to start working.[/cyan]")

    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        if destination_dir.exists():
            console.print("[yellow]Project was partially created. Consider deleting the folder and retrying.[/yellow]")
        raise typer.Exit(code=1)

# --- Typer CLI Commands ---

@app.command(name="setup", help="Run the wizard to (re)configure your template path.")
def setup_command():
    """Configure or reconfigure the template path."""
    run_setup_wizard()


@app.command(name="create", help="Create a new Power BI project from your template.")
def create_command(
    project_name: str = typer.Argument(..., help="The name for the new project.")
):
    """Create a new project (main command)."""
    run_project_creation_logic(project_name)


@app.command(name="new", help="Create a new Power BI project (alias for 'create').")
def new_command(
    project_name: str = typer.Argument(..., help="The name for the new project.")
):
    """Create a new project (alias for create)."""
    run_project_creation_logic(project_name)


# --- Default behavior (shortcut) ---
@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """
    biforge - Scaffold Power BI projects instantly.
    Quick usage: biforge "Project Name"
    """
    # Si Typer encontró y va a ejecutar un subcomando explícito (como 'setup' o 'create'),
    # ctx.invoked_subcommand tendrá un valor. En ese caso, detenemos esta función
    # y dejamos que Typer se encargue del enrutamiento. Esta es la clave.
    if ctx.invoked_subcommand is not None:
        return

    # Si llegamos aquí, no se encontró ningún subcomando.
    # El usuario intentó usar el atajo `biforge "Mi Proyecto"` o simplemente `biforge`.

    # Los argumentos crudos (sin procesar) están en ctx.args.
    if not ctx.args:
        # CASO: El usuario ejecutó `biforge` sin argumentos. Mostramos la ayuda rápida.
        console.print("[bold]biforge[/bold] - Scaffold Power BI projects instantly")
        console.print("\nQuick start:")
        console.print("  [cyan]biforge \"My Project\"[/cyan]        - Create a project (shortcut)")
        console.print("  [cyan]biforge create \"My Project\"[/cyan] - Create a project (explicit)")
        console.print("  [cyan]biforge setup[/cyan]                - Configure template path")
        console.print("\nFor full help: [cyan]biforge --help[/cyan]")
        raise typer.Exit()

    # CASO: `biforge "algun nombre de proyecto"`
    # Asumimos que los argumentos componen el nombre del proyecto.
    # El shell gestiona las comillas, por lo que `biforge "Q4 Sales"` -> ctx.args == ['Q4 Sales'].
    # `biforge Q4 Sales` -> ctx.args == ['Q4', 'Sales']. Unirlos es más robusto.
    project_name = " ".join(ctx.args)

    # Salvaguarda final: ¿El usuario escribió un comando válido pero no se detectó?
    # Esto evita crear un proyecto llamado "setup".
    if project_name in ctx.command.commands:
        console.print(f"[bold red]Error:[/bold red] '{project_name}' is a command. If you want to create a project with this name, use the 'create' command explicitly:")
        console.print(f"  [cyan]biforge create \"{project_name}\"[/cyan]")
        raise typer.Exit(1)
        
    run_project_creation_logic(project_name)
    

if __name__ == "__main__":
    app()