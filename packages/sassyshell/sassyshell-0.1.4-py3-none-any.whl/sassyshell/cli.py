import os
import platform

os.environ["GRPC_VERBOSITY"] = "ERROR"

import typer
from rich.console import Console
from rich.syntax import Syntax
from typing_extensions import Annotated
from .classifier import find_most_similar_commands
from .storage import save_data, get_data
from .llm_client import get_results_from_llm
from .config import settings
from .setup import init_config

FILE_NAME = settings.data_file
console = Console()
app = typer.Typer(help="SassyShell CLI")

def get_shell_type() -> str:
    system = platform.system()
    if system == "Windows":
        parent = os.environ.get("PSModulePath")
        return "powershell" if parent else "cmd"
    elif system == "Darwin":
        return "bash/zsh (macOS)"
    else:
        return "bash/zsh (Linux)"

@app.command(name="ask")
def sassysh(
    query: Annotated[str, typer.Argument(help="The query to process")] = "",
):
    if not settings.llm_api_key:
        console.print("\n[bold yellow]⚠️  Welcome to SassyShell! API Key not found.[/bold yellow]")
        console.print("It looks like your configuration is incomplete.")
        console.print("\nPlease run the one-time setup wizard to get started:")
        console.print("\n  [cyan]sassysh setup[/cyan]\n")
        raise typer.Exit()
    user_input: dict[str, str] = {"user_query": query}
    load_data = get_data(FILE_NAME)
    
    similar_commands = find_most_similar_commands(query, load_data)
    user_input["shell_type"] = get_shell_type()
    context_summary = ""

    if similar_commands:
        context_summary += "Here are some previously asked queries by the user:\n\n"
        for cmd in similar_commands:
            context_summary += f"Generalized Command: {cmd.get('generalized_command', '')} \n User Queries: {', '.join(cmd.get('user_query', []))}\n\n"
            # print(cmd)
        
        user_input["context"] = context_summary


    response = get_results_from_llm(user_input)
    console.print(f"\n{response.message_to_user}\n")
    highlighted_command = Syntax(response.command, "bash", theme="monokai", line_numbers=False)
    console.print(highlighted_command)
        
    # Save data
    output = {
        "generalized_command": response.generalized_command,
        "user_query": [query],
        "statistics": {"times_called": 1}
    }
    save_data(output, FILE_NAME)


@app.command(name="setup")
def setup():
    init_config()

if __name__ == "__main__":
    app()
