"""Greeting function for CLI Pets."""

import random
from rich.console import Console
from cli_pets.constants import PETS

console = Console()


def greet() -> None:
    """Print a friendly greeting with a random pet.

    Displays a colorful welcome message accompanied by a randomly selected
    pet emoji from the available PETS collection.

    Returns:
        None: Prints directly to console using Rich formatting.

    Examples:
        >>> from cli_pets import greet
        >>> greet()
        Hello from CLI Pets! 🐱
    """
    pet = random.choice(PETS)
    console.print(f"[bold green]Hello from CLI Pets! {pet}[/bold green]")
