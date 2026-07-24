import pytest

from pyschieber.player.treePlayer.treePlayer import TreePlayer
from pyschieber.player.random_player import RandomPlayer
from tests.example.statistical_helper import run_statistics


@pytest.mark.statistical
def test_treeplayer() -> None:
    players = [TreePlayer(name='Tree1'), RandomPlayer(name='Random1'), TreePlayer(name='Tree1'),
               RandomPlayer(name='Random2')]

    run_statistics(players=players)


def main() -> None:
    print('this file cannot be run by itself.')
    
if __name__ == '__main__':
    main()