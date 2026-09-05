from copy import deepcopy

from benchmark.helpers.statistical_helper import run_statistics
from pyschieber.player.base_player import BasePlayer
from pyschieber.player.challenge_player.challenge_player import ChallengePlayer
from pyschieber.player.greedy_player.greedy_player import GreedyPlayer
from pyschieber.player.random_player import RandomPlayer
from pyschieber.player.treePlayer.treePlayer import TreePlayer


def get_players() -> list[BasePlayer]:
    """Returns a list of available card player bots.

    Returns:
        list[BasePlayer]: A list of available card player bots.
    """
    return [
        RandomPlayer(name="RandomPlayer"),
        GreedyPlayer(name="GreedyPlayer"),
        ChallengePlayer(name="ChallengePlayer"),
        TreePlayer(name="TreePlayer"),
    ]


def select_player(objects: list[BasePlayer]) -> BasePlayer | None:
    """Show the list of bots and prompt for a selection.

    Args:
        objects: The available card player bots to choose from.

    Returns:
        The selected bot, or None if the input was invalid.
    """
    print("Available bots:")
    for i, obj in enumerate(objects, start=1):
        print(f"{i}. {obj}")

    try:
        choice = int(input("\nEnter a number: "))

        if 1 <= choice <= len(objects):
            return objects[choice - 1]
        print(f"Please enter a number between 1 and {len(objects)}.")
        return select_player(objects)
    except ValueError:
        print("That's not a valid number!")
        return select_player(objects)  # Retry on invalid input


def main() -> None:
    # Define the bots
    objects: list[BasePlayer] = get_players()

    # Create a list for selections and select the first bot
    selected: list[BasePlayer] = [select_player(objects)]  # type: ignore

    # Second prompt to add another bot
    selected.append(select_player(objects))  # type: ignore

    # Show the final list
    players = [
        deepcopy(selected[0]),
        deepcopy(selected[1]),
        deepcopy(selected[0]),
        deepcopy(selected[1]),
    ]

    run_statistics(players)


if __name__ == "__main__":
    main()
