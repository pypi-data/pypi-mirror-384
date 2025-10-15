# cli/ui/console_manager.py
from textwrap import dedent

from ...core.utils.console import KaguraConsole
from ...core.config import ConfigBase


class ConsoleManager:
    def __init__(self):
        self.console = KaguraConsole()

    async def display_welcome_message(self):
        model = ConfigBase.get("llm").get("model")
        language = ConfigBase.get("system").get("language")
        welcome_text = dedent(
            f"""
            [bold green]🤖 Hi, I'm Kagura AI!!! [/bold green]
            [bold cyan]   To execute: Type `Enter` Twice[/bold cyan]
            [bold cyan]   Special commands: Type /help for more information[/bold cyan]
            [bold cyan]   To exit: Ctrl+C[/bold cyan]

            [bold cyan]   System Configuration[/bold cyan]
            [bold cyan]   Language: {language}[/bold cyan]
            [bold cyan]   LLM Model: {model}[/bold cyan]
        """
        )
        self.console.panel(
            welcome_text,
            title="[bold blue]Welcome to Kagura AI[/bold blue]",
            border_style="blue",
        )

    async def display_message(self, message: str):
        # タイピングエフェクトで表示
        await self.console.display_typing(message)

    async def display_help(self):
        help_text = dedent(
            """
            [bold cyan]Available Commands:[/bold cyan]

            [bold green]/create agent[/bold green]
                Create a new agent interactively
                Usage: /create agent

            [bold green]/help[/bold green]
                Show this help message
                Usage: /help

            [bold green]/history[/bold green]
                Display message history
                Usage: /history

            [bold green]/clear[/bold green]
                Clear message history
                Usage: /clear

            [bold green]/exit[/bold green]
                Exit Kagura AI
                Usage: /exit
        """
        )
        self.console.panel(help_text, title="[bold blue]Kagura AI Help[/bold blue]")

    async def display_error(self, error: Exception):
        self.console.panel(f"[red]Error: {str(error)}[/red]", border_style="red")
