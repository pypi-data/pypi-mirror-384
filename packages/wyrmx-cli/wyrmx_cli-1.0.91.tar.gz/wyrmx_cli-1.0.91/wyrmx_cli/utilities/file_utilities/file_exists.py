from pathlib import Path
import typer

def fileExists(file: Path, filename: str, fileType: str):
    if file.exists():
        typer.secho(f"❌ {fileType} '{filename}' already exists.", fg=typer.colors.RED)
        raise typer.Exit(1)
    