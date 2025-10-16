"""Walking animation function for CLI Pets."""

from cli_pets.race import race


def walk(pet: str = "🐱", steps: int = 30, speed: float = 0.1) -> None:
    """Animate a pet walking across the terminal.

    Args:
        pet: Emoji character to display (default: cat)
        steps: Number of steps to take (default: 30)
        speed: Seconds between steps (default: 0.1)
    """
    race(distance=steps, racers=1, pets=[pet], speed=speed, show_winner=False)
