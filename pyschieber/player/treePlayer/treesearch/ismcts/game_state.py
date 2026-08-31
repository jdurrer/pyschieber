from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, NoReturn, Self

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from pyschieber.player.rulebased_player.helpers.state_dict_to_dataclass import (
        StatusDict,
    )
    from pyschieber.player.treePlayer.treePlayer import TreePlayer
    from pyschieber.player.treePlayer.treesearch.ismcts.informationset import (
        CardDistributionSolver,
    )


from pyschieber.card import Card, from_string_to_card
from pyschieber.game import Game
from pyschieber.player.base_player import BasePlayer
from pyschieber.player.rulebased_player.helpers.state_dict_to_dataclass import (
    Status,
)
from pyschieber.player.treePlayer.treesearch.helper import array_to_list_of_cards
from pyschieber.rules.stich_rules import stich_rules
from pyschieber.stich import PlayedCard
from pyschieber.team import Team
from pyschieber.trumpf import get_trumpf


class GameState(Game):
    def __init__(
        self,
        teams: list[Team],
        id: int,
        point_limit: float = 1500,
        use_counting_factor: bool = True,
    ) -> None:
        super().__init__(teams, point_limit, use_counting_factor)
        self.id = id

    def current_player(self) -> int:
        """
        Get the id of the player that is next to act.

        Returns:
            int: player id
        """
        assert self.cards_on_table is not None
        if self.cards_on_table:
            return (self.cards_on_table[-1].player.id + 1) % 4  # type: ignore
        return self.stiche[-1].player.id or self.id

    def information_state_string(self) -> int:
        """
        Get a hash of the game state. Acts as a key in a lookup table.

        Returns:
            int: hash key
        """
        history_string: str = ""
        if self.stiche:
            for stich in self.stiche:
                history_string += str(stich.player.id)
                history_string += list_of_cards_to_history_string(stich.played_cards)

        if self.cards_on_table:
            history_string += list_of_cards_to_history_string(self.cards_on_table)

        history_string += "-"  # * separator, after which the current player hand cards will be included.
        hand_current_player = self.players[self.current_player()].cards
        history_string += "".join(
            sorted(card_to_history_string(card) for card in hand_current_player)
        )

        if not history_string:
            history_string = str(self.id)

        return hash(history_string)

    def resample_from_infostate(self, informationset: CardDistributionSolver) -> Self:
        """
        Distribute a new set of plausible cards to each player.
        Args:
            informationset (CardDistributionSolver): CSP hand distribution solver.
        Returns:
            Self: Modified GameState with new card distribution.
        """
        card_distribution = informationset.solve_iter()
        for id in range(4):
            hand_cards: list[int] = [1 if x == id else 0 for x in card_distribution]
            self.players[id].cards = array_to_list_of_cards(hand_cards)
        return self

    def legal_actions(self) -> list[Card]:
        """
        Get all legal actions a player can take.
        Some players are able to already provide a smaller set than all legal actions based on their programmed heuristic.

        Returns:
            list[Card]: Actions a player is able to play.
        """
        # TODO: Implement choose_card_treesearch @ TreePlayer to return list[Card] if no optimal solution was found using rule based approach.
        return self.players[self.current_player()].choose_card_treesearch(
            self.get_status()
        )

    def is_terminal(self) -> bool:
        """Determine whether the current search state represents a finished game.

        This method checks whether the game has reached its natural end based on
        the number of rounds played and the completion of the final round.

        Returns:
            bool: True if exactly nine rounds have been played and the last round
            contains four played cards, otherwise False.
        """
        return len(self.stiche) == 9
        # Below probably wrong, because stiche is only len==9 if last stich completed. # TODO: Check!
        # # check if 9 rounds have been played.
        # if len(self.stiche) != 9:
        #     return False
        # # check if the last round has been completed (4 cards played)
        # return len(self.stiche[-1].played_cards) == 4

    def returns(self) -> NDArray[np.float64]:
        """
        Get the (estimated) value for a game state for each player.

        Returns:
            NDArray[np.float64]: The value of the game state as seen for each player. Ordered by player id.
        """
        own_team: int = self.id % 2
        score: int = self.teams[0].points - self.teams[1].points
        if own_team:
            score = -score
        modifier: list[int] = [1, -1, 1, -1]
        return np.asarray([x * score for x in modifier], dtype=np.float64)

    def is_chance_node(self) -> bool:
        """There are no random events for this game.

        Returns:
            bool: Returns False, indicating that the current state is not a chance node.
        """
        return False

    def chance_outcomes(
        self,
    ) -> list[tuple[Card, float]]:
        """
        There are no chance events. Nothing can be returned.

        Returns:
            list[tuple[Card, float]]: empty list of chance events and empty list of their probabilities.
        """
        raise NotImplementedError

    def apply_action(self, action: Card) -> None:
        """
        Act on the game using the provided card.

        Args:
            action (Card): Card to be played in the game.
        """
        self.move_made(self.current_player(), action)
        self.cards_on_table.append(
            PlayedCard(player=self.players[self.current_player()], card=action)
        )
        if len(self.cards_on_table) == 4:
            stich = stich_rules[self.trumpf](played_cards=self.cards_on_table)  # type: ignore
            self.stiche.append(stich)
            self.count_points(stich, last=(len(self.stiche) == 9))
            self.cards_on_table = []

    def clone(self) -> Self:
        """Create and return a copy of this search state instance.

        This method is intended to provide an independent duplicate that can be
        used for search without affecting the original state.

        Returns:
            SearchState: A new instance representing a copy of the current search state.
        """
        return deepcopy(self)


def card_to_history_string(card: Card) -> str:
    suit_value = str(card.suit.value)
    card_value = str(card.value - 5)
    return suit_value + card_value


def list_of_cards_to_history_string(
    cards: list[PlayedCard],
) -> str:
    string: str = ""
    for action in cards:
        card = action.card
        string += card_to_history_string(card)
    return string


class DummyTreePlayer(BasePlayer):
    def choose_trumpf(self, geschoben) -> NoReturn:  # noqa: ARG002
        raise ValueError("This player is not supposed to decide Trumpf!")

    def choose_card_treesearch(self, state: StatusDict) -> list[Card]:
        """
        Does not return a card but all allowed cards. Search tree algorithm chooses card based on its own policy.

        Args:
            state (Status, optional): _description_. Defaults to None.

        Returns:
            list[Card]: all allowed cards able to play in current state.
        """
        return self.allowed_cards(state)


# TODO: Maybe also simulate player handcards. could influence things.
def _replay_until_current_stich(game: GameState, state: Status) -> GameState:
    """
    Rebuild a game based on the provided game history (state).

    Args:
        game (Game): New game with boundary conditions.
        state (Status): History, based on which the game is rebuilt

    Returns:
        Game: rebuilt game
    """
    for stich in state.stiche:
        for card_string in stich.played_cards:
            card = from_string_to_card(card_string.card)
            current_player = game.players[card_string.player_id]  # type: ignore
            game.move_made(current_player.id, card)
            game.cards_on_table.append(PlayedCard(player=current_player, card=card))
        game.stiche.append(stich_rules[game.trumpf](played_cards=game.cards_on_table))  # type: ignore
        game.cards_on_table = []
    return game


def _replay_until_table_position(game: GameState, state: Status) -> GameState:
    """
    Rebuild the table cards based on the provided game state.

    Args:
        game (Game): The game for which the table shall be rebuilt.
        state (Status): The current gamestate. Provides a build plan for the table.

    Returns:
        Game: game with the rebuilt table.
    """
    for tablecard in state.table:
        card = from_string_to_card(tablecard.card)
        current_player = game.players[tablecard.player_id]  # type: ignore
        game.move_made(current_player.id, card)
        game.cards_on_table.append(PlayedCard(player=current_player, card=card))
    return game


def rebuild_game(player: TreePlayer, state: Status) -> GameState:
    """
    rebuild a game based on the provided history (state).

    Args:
        player (TreePlayer): The player which requested to rebuild the game.
        state (Status): The game history and current state.

    Returns:
        GameState: Rebuilt game
    """
    assert player.id is not None
    players: list[BasePlayer] = []
    for id in range(4):
        if id == player.id:
            bot = DummyTreePlayer(name=str(id))  # * replace with SearchPlayer later.
            # bot.strategy = player.strategy
            bot.cards = player.cards
            # bot.role = player.role
            players.append(bot)
            # TODO: If rulebased partner needs to be implemented, complete game has to be replayed because partner strategy needs to be built from ground up.
            # * This would mean that the partner needs to have already known cards. Strategy needs to be built for each possible hand. Not yet implemented.
            # * Another take: Rules Player uses policy and assumes a partner with same policy. For now, only use random players until partner can be fully integrated as well.
            # * In that case, this function likely must be called by GameState.resample_from_infostate()

        else:
            players.append(DummyTreePlayer(name=str(id)))
        players[id].id = id
    team_1: Team = Team(players=[players[0], players[2]])  # type: ignore
    team_2: Team = Team(players=[players[1], players[3]])  # type: ignore
    teams: list[Team] = [team_1, team_2]
    game = GameState(
        teams=teams,
        point_limit=state.point_limit,
        use_counting_factor=False,
        id=player.id,
    )
    game.teams[0].points = state.teams[0].points
    game.teams[1].points = state.teams[1].points
    game.geschoben = state.geschoben
    game.trumpf = get_trumpf(state.trumpf)
    game = _replay_until_current_stich(game, state)
    game = _replay_until_table_position(game, state)

    return game


def main() -> None:
    print(
        "This module is not intended to be run directly. It provides the RootState class for use in the ISMCTS tree search implementation."
    )


if __name__ == "__main__":
    main()
