import random
from typing import Generator
from pyschieber.trumpf import Trumpf
from pyschieber.player.base_player import BasePlayer
from pyschieber.player.treePlayer.strategy.jass_strategy import JassStrategy
from pyschieber.player.treePlayer.helpers.state_dict_to_dataclass import StatusDict, Status, translate_get_status_to_dataclass
from pyschieber.card import Card

''' Rule Sources
        https://www.watson.ch/schweiz/sport/293024792-jass-tipps-welche-karte-wuerdest-du-hier-spielen
        https://jassverzeichnis.ch/thema/jassen-in-zahlen/
        https://jassclub-wasserturm.ch/wp-content/uploads/2018/11/Die-10-heiligen-Jass-Gebote.pdf
'''

class RuleBasedPlayer(BasePlayer):
    

    def init_strategy(self) -> None:
        """Initializes the strategy for a new round if the hand contains 9 cards.

        This function checks the player's hand size and sets up a new JassStrategy if a new round has started.

        Returns:
            None
        """
        if len(self.cards) == 9:
            self.strategy = JassStrategy(self)


    def set_card(self, card: Card) -> None:
        """Adds a card to the player's hand and initializes strategy if needed.

        This function appends the given card to the player's hand and checks if a new round has started to initialize the strategy.

        Args:
            card (Card): The card to add to the player's hand.

        Returns:
            None
        """
        self.cards.append(card)
        self.init_strategy()


    def choose_trumpf(self, geschoben: bool) -> Generator[str | None, None, None]:
        """Yields possible trumpf choices until an allowed trumpf is selected.

        This generator produces trumpf options based on the player's hand and whether the partner has geschoben, continuing until an allowed trumpf is confirmed.

        Args:
            geschoben (bool): Indicates if the partner has geschoben.

        Returns:
            Generator[Trumpf | None]: Yields trumpf choices and None when an allowed trumpf is selected.
        """
        allowed: bool = False
        while not allowed:
            trumpf = self.strategy.chose_trumpf(self.cards, geschoben)
            allowed = yield trumpf
            if allowed:
                yield None


    def choose_card(self, state: StatusDict = None) -> Generator[Card | None, None, None]:
        """Yields possible card choices until an allowed card is selected.

        This generator produces card options based on the current game state and player's role, continuing until an allowed card is confirmed.

        Args:
            state (StatusDict, optional): The current game state.

        Returns:
            Generator[Card | None, None, None]: Yields card choices and None when an allowed card is selected.
        """
        # Which role do we play this round?
        status: Status = translate_get_status_to_dataclass(state)
        if self.role_setting_required(status):
            self.set_player_role_by_state(status)

        # Get the Handcards, that we are allowed to play.
        cards = self.allowed_cards(state=state)

        # Choose the best card to play.
        allowed = False
        while not allowed:
            card = self.strategy.choose_card(cards, state)
            # if not isinstance(card, Card):
            #     !!! Commented for now. Will be continued at a later state in the bot because of errors and policy improvements.
            #     tree = TreeSearch(self, state, depth = 4 * 4, time_s = 60)
            #     card = tree.root()
            if not isinstance(card, Card):
                card = random.choice(cards)
            allowed = yield card
            if allowed:
                yield None


    def move_made(self, player_id: int, card: Card, state: StatusDict) -> None:
        """Updates the strategy and player role after a move is made.

        This function processes a move by updating the player's role if needed and informing the strategy about the move.

        Args:
            player_id (int): The ID of the player who made the move.
            card (Card): The card that was played.
            state (StatusDict): The current game state.

        Returns:
            None
        """
        status: Status = translate_get_status_to_dataclass(state)
        if self.role_setting_required(status):
            self.set_player_role_by_id(player_id, status)
        self.strategy.move_made(player_id, card, status)


    def set_player_role_by_state(self, state: Status) -> None:
        """Sets the player's role based on the current game state.

        This function determines and assigns the player's role (Partner, Trumpf, or Off) according to the table and geschoben status.

        Args:
            state (Status): The current game state.

        Returns:
            None
        """
        # Wir spielen als erstes in einer neuen Runde aber haben geschoben. -> Partner
        if all([len(state.table) == 0, state.geschoben]):
            self.role = 'Partner'

        # Wir spielen als erstes in einer neuen Runde und haben nicht geschoben. -> Trumpf
        elif all([len(state.table) == 0, not state.geschoben]):
            self.role = 'Trumpf'

        # Wir spielen als drittes in einer neuen Runde (Teamkollege war erster) und unser Teamkollege hat nicht geschoben. -> Partner
        elif all([len(state.table) == 2, not state.geschoben]):
            self.role = 'Partner'

        # Wir spielen als drittes in einer neuen Runde (Teamkollege war erster) aber unser Teamkollege hat geschoben. -> Trumpf
        elif all([len(state.table) == 2, state.geschoben]):
            self.role = 'Trumpf'
        else:
            self.role = 'Off'


    def set_player_role_by_id(self, player_id: int, status: Status) -> None:

        if len(status.table) != 0:
            return None
        
        partner_id: int = (self.id + 2) % 4
        opponent_1_id: int = (self.id + 1) % 4
        opponent_2_id: int = (self.id + 3) % 4

        if player_id in {opponent_1_id, opponent_2_id}:
            self.role = 'Off'
        
        if player_id == self.id and status.geschoben:
            self.role = 'Partner'
        
        if player_id == self.id and not status.geschoben:
            self.role = 'Trumpf'

        if player_id == partner_id and status.geschoben:
            self.role = 'Trumpf'
        
        if player_id == partner_id and not status.geschoben:
            self.role = 'Partner'


    def role_setting_required(self, state: Status) -> bool:
        """Checks whether the player's role needs to be set for the current game state.

        This function determines if it is the first round and the player still holds a full hand, indicating that the role should be assigned.

        Args:
            state (Status): The current game state.

        Returns:
            bool: True if the role should be set based on the current state, otherwise False.
        """
        first_round: bool = len(state.stiche) == 0
        full_hand: bool = len(self.cards) == 9
        return first_round and full_hand


if __name__ == "__main__":
    print('This script cannot be executed by itself...')