import pytest

from pyschieber.player.rulebased_player.rulebased_player import RuleBasedPlayer
from pyschieber.player.random_player import RandomPlayer
from tests.example.statistical_helper import run_statistics


@pytest.mark.statistical
def test_rulebasedplayer() -> None:
    players = [RuleBasedPlayer(name='RuleBased1'), RandomPlayer(name='Random1'), RuleBasedPlayer(name='RuleBased2'),
               RandomPlayer(name='Random2')]

    run_statistics(players=players)


def main() -> None:
    print('this file cannot be run by itself.')
    
if __name__ == '__main__':
    main()