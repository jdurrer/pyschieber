# ----------------------------
# Libraries
# ----------------------------

import logging
from typing import List, Dict, Tuple, Generator, TypedDict, Literal  # Required for Python < 3.9
from pyschieber.helpers.typed_dict import TypedDictPlayer

import random
import numpy as np

from pyschieber.team import Team
from pyschieber.card import Card
from pyschieber.dealer import Dealer
from pyschieber.rules.stich_rules import stich_rules, card_allowed
from pyschieber.rules.trumpf_rules import trumpf_allowed
from pyschieber.rules.count_rules import count_stich, counting_factor
from pyschieber.stich import stich_dict, played_cards_dict, Stich, PlayedCard, StichDict, PlayedCardsDict
from pyschieber.trumpf import Trumpf


logger = logging.getLogger(__name__)


# ----------------------------
# Helper TypeDicts
# ----------------------------


class StatusDict(TypedDict):
    stiche: tuple[List[StichDict]]
    trumpf: Literal['ROSE', 'BELL', 'ACORN', 'SHIELD', 'OBE_ABE', 'UNDE_UFE', 'SCHIEBEN']
    geschoben: tuple[bool]
    point_limit: tuple[float]
    table: tuple[list[PlayedCardsDict]]
    teams: List[Dict[str, int]]


# ----------------------------
# Main Class
# ----------------------------


class Game:
    def __init__(self, teams: List[Team], point_limit: float = 1500, use_counting_factor: bool = True) -> None:
        """
        Initializes a new game with the given teams, point limit, and counting factor option.

        Sets up the players, dealer, and game state for a new round of play.
        
        Args:
            teams (List[Team]): The teams participating in the game.
            point_limit (float, optional): The score required to win the game. Defaults to 1500.
            use_counting_factor (bool, optional): Whether to use the counting factor for scoring. Defaults to True.
        """
        self.teams = teams
        self.point_limit = point_limit
        self.players: List[TypedDictPlayer] = [teams[0].players[0], teams[1].players[0], teams[0].players[1], teams[1].players[1]]
        self.dealer: Dealer = Dealer(players=self.players)
        self.geschoben: bool = False
        self.trumpf: Trumpf | None = None
        self.stiche: List[Stich] = []
        self.cards_on_table: List[PlayedCard] = []
        self.use_counting_factor = use_counting_factor
    

    def prepare_deck(self, benchmark_enabled, benchmark_seed, start_player_index) -> None:
        """
        Prepares and shuffles the deck for the game, optionally using benchmarking mode for reproducibility.

        Shuffles and deals cards to players, with an option to rotate the deal based on the starting player and benchmarking settings.

        Args:
            benchmark_enabled (bool): If True, enables benchmarking mode for reproducible shuffling.
            benchmark_seed (float): Seed value for benchmarking mode.
            start_player_index (int): The index of the player to start dealing from.

        Returns:
            None
        """
        if not benchmark_enabled:
            self.dealer.shuffle_cards()
            self.dealer.deal_cards()
        elif not (start_player_index % 2):
            random.seed(benchmark_seed)
            self.dealer.shuffle_cards()
            self.dealer.deal_cards()
            # self.dealer.show_deck()
        else:
            random.seed(benchmark_seed)
            self.dealer.shuffle_cards()
            self.dealer.deal_cards_rotated()
            # self.dealer.show_deck()
    

    def is_winner(self, whole_rounds: bool) -> bool:
        """Überprüft, ob ein Team die benötigte Siegpunktzahl erreicht.

        Args:
            whole_rounds (bool): Falls eine fixe Anzahl runden gespielt werden, wird kein Gewinner gekührt.

        Returns:
            bool: True = es gibt einen Gewinner.
        """
        return bool(
            (
            self.teams[0].won(self.point_limit)
            or self.teams[1].won(self.point_limit)
            )
            and not whole_rounds
        )
    

    def check_for_matsch(self, matsch_counter) -> None:
        """
        Checks if a team has won all tricks in a round and awards bonus points accordingly.

        Awards bonus points to the team that wins all nine tricks, factoring in the current trumpf and counting factor.

        Args:
            matsch_counter: A numpy array tracking the number of tricks won by each team.

        Returns:
            None

        Raises:
            ValueError: If self.trumpf is None.
        """
        if self.trumpf is None:
            raise ValueError("trumpf must not be None.")
        if matsch_counter[0,0] == 9:
            self.teams[0].points += 100 * counting_factor[self.trumpf] if self.use_counting_factor else 100
        
        elif matsch_counter[0,1] == 9:
            self.teams[1].points += 100 * counting_factor[self.trumpf] if self.use_counting_factor else 100


    def define_trumpf(self, start_player_index: int) -> None:
        """
        Determines and sets the trumpf for the current round, handling the 'schieben' (push) rule if selected.

        Prompts the appropriate player(s) to choose the trumpf and updates the game state accordingly.

        Args:
            start_player_index (int): The index of the player who starts the trumpf selection.

        Returns:
            None
        """
        is_allowed_trumpf: bool = False
        generator: Generator[Trumpf] = self.players[start_player_index].choose_trumpf(geschoben=self.geschoben)
        chosen_trumpf: Trumpf = next(generator)
        if chosen_trumpf == Trumpf.SCHIEBEN:
            self.geschoben = True
            generator = self.players[(start_player_index + 2) % 4].choose_trumpf(geschoben=self.geschoben)
            chosen_trumpf = next(generator)
            while not is_allowed_trumpf:
                is_allowed_trumpf = trumpf_allowed(chosen_trumpf=chosen_trumpf, geschoben=self.geschoben)
                trumpf = generator.send(is_allowed_trumpf)
                chosen_trumpf = chosen_trumpf if trumpf is None else trumpf
        self.trumpf = chosen_trumpf


    def get_status(self) -> StatusDict:
        """
        Returns the current status of the game as a dictionary.

        The status includes the list of stiches, the current trumpf, whether 'geschoben' is active, the point limit, the cards on the table, and the points for each team. Raises a ValueError if the trumpf is not set.

        Returns:
            StatusDict: A dictionary containing the current game status.

        Raises:
            ValueError: If self.trumpf is None.
        """
        if self.trumpf is None:
            raise ValueError("trumpf must not be None.")
        return dict(stiche=[stich_dict(stich) for stich in self.stiche], trumpf=self.trumpf.name,
                    geschoben=self.geschoben, point_limit=self.point_limit,
                    table=[played_cards_dict(played_card) for played_card in self.cards_on_table],
                    teams=[dict(points=team.points) for team in self.teams])
    

    def play_card(self, table_cards: List[PlayedCard], player: TypedDictPlayer) -> Card:
        """
        Handles the process of a player choosing and playing a card for the current trick.

        Interacts with the player's card selection logic, validates the chosen card, and updates the player's hand.

        Args:
            table_cards (List[PlayedCard]): The cards currently on the table for the trick.
            player (TypedDictPlayer): The player who is making the move.

        Returns:
            Card: The card that was played by the player.
        """
        cards: List[Card] = [played_card.card for played_card in table_cards]
        is_allowed_card: bool = False
        generator: Generator[Card] = player.choose_card(state=self.get_status())
        chosen_card: Card = next(generator)
        while not is_allowed_card:
            is_allowed_card = card_allowed(table_cards=cards, chosen_card=chosen_card, hand_cards=player.cards,
                                           trumpf=self.trumpf)
            card = generator.send(is_allowed_card)
            chosen_card = chosen_card if card is None else card
        else:
            logger.info('Table: {0}:{1}'.format(player, chosen_card))
            player.cards.remove(chosen_card)

        return chosen_card


    def play_stich(self, start_player_index: int) -> Stich:
        """
        Plays a complete trick (stich) starting from the specified player index.

        Each player in turn plays a card, the moves are recorded, and the winner of the trick is determined and returned.

        Args:
            start_player_index (int): The index of the player who starts the trick.

        Returns:
            Stich: The completed trick with all played cards and the winner.
        """
        self.cards_on_table = []
        first_card: Card = self.play_card(table_cards=self.cards_on_table, player=self.players[start_player_index])
        self.move_made(self.players[start_player_index].id, first_card)
        self.cards_on_table = [PlayedCard(player=self.players[start_player_index], card=first_card)]
        for i in get_player_index(start_index=start_player_index):
            current_player: TypedDictPlayer = self.players[i]
            card = self.play_card(table_cards=self.cards_on_table, player=current_player)
            self.move_made(current_player.id, card)
            self.cards_on_table.append(PlayedCard(player=current_player, card=card))
        assert self.trumpf is not None
        stich: Stich = stich_rules[self.trumpf](played_cards=self.cards_on_table)
        return stich


    def move_made(self, player_id: int | None, card: Card) -> None:
        """
        Generates the indices of the next three players in turn order starting from a given index.

        Yields the player indices in the correct sequence for a four-player game.

        Args:
            start_index (int): The index of the player to start from.

        Returns:
            Generator[int, None, None]: A generator yielding the next three player indices.
        """
        if player_id is None:
            raise ValueError("player_id must not be None.")
        for player in self.players:
            player.move_made(player_id, card, self.get_status())


    def stich_over_information(self) -> None:
        """
        Notifies all players that the current trick (stich) is over.

        Calls the stich_over method on each player, passing the current game status as state.
        """
        [player.stich_over(state=self.get_status()) for player in self.players]


    def count_points(self, stich, last) -> None:
        """
        Calculates and adds points to the appropriate team for a completed trick.

        Determines the team based on the player who won the trick, extracts the played cards, and updates the team's score.

        Args:
            stich: The completed trick, containing the winning player and played cards.
            last: A boolean indicating if this is the last trick of the round.

        Returns:
            None
        """
        stich_player_index: int = self.players.index(stich.player)
        cards: List[Card] = [played_card.card for played_card in stich.played_cards]
        self.add_points(team_index=(stich_player_index % 2), cards=cards, last=last)


    def add_points(self, team_index: int, cards: List[Card], last: bool) -> None:
        """
        Adds points to the specified team based on the cards played in a trick.

        Calculates the points for the trick, applies the counting factor if enabled, and updates the team's score.

        Args:
            team_index (int): The index of the team to add points to.
            cards (List[Card]): The cards played in the trick.
            last (bool): Whether this is the last trick of the round.

        Returns:
            None
        """
        points = count_stich(cards, self.trumpf, last=last)
        points = points * counting_factor[self.trumpf] if self.use_counting_factor else points
        self.teams[team_index].points += points
 

    def reset_point(self) -> None:
        """
        Resets the points for all teams in the game.

        Calls the reset_points method on each team to set their points back to zero.
        """
        [team.reset_points() for team in self.teams]


    def play(self, start_player_index: int = 0, whole_rounds: bool = False, allow_weis: bool = True, benchmark_enabled: bool = False, benchmark_seed: float = 0) -> bool:
        """
        Plays a full round of the game, handling deck preparation, trump selection, and stich rounds.

        Manages the flow of the game from shuffling and dealing cards to determining the winner and updating points.

        Args:
            start_player_index (int, optional): Index of the player to start the round. Defaults to 0.
            whole_rounds (bool, optional): If True, plays a fixed number of rounds without declaring a winner. Defaults to False.
            allow_weis (bool, optional): If True, allows 'Weis' declarations. Defaults to True.
            benchmark_enabled (bool, optional): If True, enables benchmarking mode for reproducible results. Defaults to False.
            benchmark_seed (float, optional): Seed value for benchmarking mode. Defaults to 0.

        Returns:
            bool: True if a team wins during the round, False otherwise.
        """
        # Deck mischen und Karten verteilen
        self.prepare_deck(benchmark_enabled, benchmark_seed, start_player_index)

        # Spieler auffordern, Trumpf zu bestimmen.
        self.define_trumpf(start_player_index=start_player_index)
        logger.info('Chosen Trumpf: {0} \n'.format(self.trumpf.name))
        
        # Matsch zurücksetzen
        matsch_counter = np.zeros((1,2))

        # Spielrunde durchführen
        for i in range(9):
            stich: Stich = self.play_stich(start_player_index)
            self.count_points(stich, last=(i == 8))
            logger.info('\nStich: {0} \n'.format(stich.player))
            logger.info(f"{'-' * 180}{self.trumpf}\n")
            start_player_index = self.players.index(stich.player)
            self.stiche.append(stich)
            self.stich_over_information()
            matsch_counter[0,stich.player.id % 2] += 1
            if self.is_winner(whole_rounds):
                return True
        
        # Auf Matsch prüfen
        self.check_for_matsch(matsch_counter)
        return bool(self.is_winner(whole_rounds))
    

def get_player_index(start_index: int) -> Generator[int, None, None]:
    """
    Generates the indices of the next three players in turn order starting from a given index.

    Yields the player indices in the correct sequence for a four-player game.

    Args:
        start_index (int): The index of the player to start from.

    Returns:
        Generator[int, None, None]: A generator yielding the next three player indices.
    """
    for i in range(1, 4):
        yield (i + start_index) % 4


def main() -> None:
    print('This file cannot be run by itself.')
   

if __name__ == '__main__':
    main()