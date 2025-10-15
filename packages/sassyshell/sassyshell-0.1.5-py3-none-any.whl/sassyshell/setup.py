from rich.prompt import Prompt
from rich.console import Console
from pathlib import Path

console = Console()

def init_config():
    console.print("[bold]Welcome to SassyShell Setup![/bold]")
    console.print("Let's configure your LLM provider.")

    llm_model_provider = Prompt.ask("Enter LLM model provider", choices=["google_genai", "openai", "ollama", "anthropic", "groq"], default="google_genai")
    llm_model_name = Prompt.ask("Enter LLM model name", default="gemini-2.5-flash")
    llm_api_key = Prompt.ask("Enter LLM API key (input will be hidden)", password=True)

    config_dir = Path.home() / ".config" / "sassyshell"
    config_dir.mkdir(parents=True, exist_ok=True)
    env_file = config_dir / ".env"

    with open(env_file, "w") as f:
        f.write(f"llm_model_provider={llm_model_provider}\n")
        f.write(f"llm_model_name={llm_model_name}\n")
        f.write(f"llm_api_key={llm_api_key}\n")
    
    console.print("\n[bold green]Setup complete![/bold green]")
    console.print(f"Your settings have been saved to [cyan]{env_file}[/cyan].")
    console.print("The new configuration will be used the next time you run sassysh.")