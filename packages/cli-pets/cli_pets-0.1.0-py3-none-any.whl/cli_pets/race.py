"""Racing function for CLI Pets."""

import random
import time
from rich.console import Console
from rich.live import Live
from rich.text import Text
from cli_pets.constants import PETS

console = Console()


def race(
    distance: int = 50,
    racers: int = 3,
    pets: list[str] | None = None,
    speed: float = 0.1,
    show_winner: bool = True,
) -> None:
    """Race pets across the terminal.

    Args:
        distance: Length of the race track (default: 50)
        racers: Number of racing pets (default: 3)
        pets: Specific pets to race; if None, random pets are chosen (default: None)
        speed: Seconds between updates (default: 0.1)
        show_winner: Whether to announce the winner (default: True)
    """
    ### Setup ----
    if pets is None:
        pets = random.sample(PETS, min(racers, len(PETS)))
    else:
        pets = pets[:racers]  # Limit to number of racers

    positions = [0] * len(pets)

    ### Race Loop ----
    with Live(console=console, refresh_per_second=10) as live:
        while max(positions) < distance:
            # Update positions randomly
            for i in range(len(positions)):
                positions[i] += random.randint(0, 2)

            # Render race
            display = Text()
            for i, pet in enumerate(pets):
                pos = min(positions[i], distance)
                line = " " * pos + pet + "\n"
                display.append(line)

            live.update(display)
            time.sleep(speed)

    ### Declare Winner ----
    if show_winner and len(pets) > 1:
        winner_idx = positions.index(max(positions))
        console.print(f"\n[bold yellow]🏆 {pets[winner_idx]} wins![/bold yellow]")
