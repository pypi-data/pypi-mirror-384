import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
import os
import sys

console = Console()


def get_docs_path():
    """Get the path to the docs directory"""
    return os.path.join(os.path.dirname(__file__), 'docs')


def load_documentation(algorithm):
    """Load documentation for a specific algorithm"""
    docs_path = get_docs_path()
    doc_file = os.path.join(docs_path, f"{algorithm.lower()}.md")
    
    if not os.path.exists(doc_file):
        return None
    
    with open(doc_file, 'r', encoding='utf-8') as f:
        return f.read()


def display_documentation(algorithm):
    """Display documentation for an algorithm"""
    content = load_documentation(algorithm)
    
    if content is None:
        console.print(f"[red]Error:[/red] Documentation for '{algorithm}' not found.")
        console.print("\nUse [cyan]progan-h list[/cyan] to see available algorithms.")
        return
    
    # Display the documentation
    console.print(Panel(
        f"[bold cyan]Documentation for: {algorithm.upper()}[/bold cyan]",
        style="cyan"
    ))
    console.print()
    
    md = Markdown(content)
    console.print(md)


def list_algorithms():
    """List all available algorithms"""
    docs_path = get_docs_path()
    
    if not os.path.exists(docs_path):
        console.print("[red]Error:[/red] Documentation directory not found.")
        return
    
    # Get all .md files in docs directory
    algorithms = []
    for file in os.listdir(docs_path):
        if file.endswith('.md'):
            algorithms.append(file[:-3])  # Remove .md extension
    
    if not algorithms:
        console.print("[yellow]No documentation files found.[/yellow]")
        return
    
    # Create a nice table
    table = Table(title="Available Algorithms", show_header=True, header_style="bold cyan")
    table.add_column("Algorithm", style="green", width=20)
    table.add_column("Command", style="yellow", width=30)
    
    for algo in sorted(algorithms):
        table.add_row(algo.upper(), f"progan-h {algo}")
    
    console.print(table)


@click.command()
@click.argument('algorithm', required=False)
@click.option('--list', '-l', 'show_list', is_flag=True, help='List all available algorithms')
@click.version_option(version='0.1.0', prog_name='progan-h')
def main(algorithm, show_list):
    """
    Progan-H: Machine Learning Algorithm Documentation Tool
    
    Usage:
        progan-h knn        # Show KNN documentation
        progan-h --list     # List all available algorithms
    """
    if show_list or algorithm == 'list':
        list_algorithms()
    elif algorithm:
        display_documentation(algorithm)
    else:
        console.print(Panel(
            "[bold cyan]Progan-H[/bold cyan] - ML Algorithm Documentation Tool\n\n"
            "Usage:\n"
            "  [yellow]progan-h knn[/yellow]        Show KNN documentation\n"
            "  [yellow]progan-h --list[/yellow]     List all available algorithms\n"
            "  [yellow]progan-h --help[/yellow]     Show this help message",
            title="Welcome to Progan-H",
            style="cyan"
        ))


if __name__ == '__main__':
    main()
