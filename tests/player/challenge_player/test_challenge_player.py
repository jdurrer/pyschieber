import pytest

from pyschieber.player.challenge_player.challenge_player import ChallengePlayer
from pyschieber.player.greedy_player.greedy_player import GreedyPlayer
from tests.example.statistical_helper import run_statistics


@pytest.mark.statistical
def test_challenge():
    players = [
        ChallengePlayer(name="Trick1"),
        GreedyPlayer(name="Greedy1"),
        ChallengePlayer(name="Trick2"),
        GreedyPlayer(name="Greedy2"),
    ]

    run_statistics(players=players)


def main() -> None:
    print("this file cannot be run by itself.")


if __name__ == "__main__":
    main()
