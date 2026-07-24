from typing import Tuple, List
from pyschieber.card import Card
from pyschieber.player.treePlayer.strategy.card_counter import CardCounter
from pyschieber.player.treePlayer.strategy.flags.flags import DoesntHaveCardFlag, PreviouslyHadStichFlag, FailedToServeSuitFlag, SuitAngezogenFlag, SuitVerworfenFlag, Flag
from pyschieber.suit import Suit
from pyschieber.player.treePlayer.helpers.state_dict_to_dataclass import Status
from pyschieber.helpers.game_helper import split_cards_by_suit
from pyschieber.player.treePlayer.helpers.helperfunctions import flatten_matrix
from pyschieber.card import from_string_to_card
from pyschieber.trumpf import get_trumpf, Trumpf


class Mode:

    def __init__(self, card_counter: CardCounter) -> None:
        self.card_counter = card_counter


    def is_suit_trumpf(self) -> bool:
        """Checks if the current trumpf is a suit-based trumpf.

        This function returns True if the current trumpf is a colored suit.
        Otherwise (i.e. une-ufe or obe-abe) returns false

        Returns:
            bool: True if the trumpf is suit-based, False otherwise.
        """
        return self.trumpf_name().name in [x.name for x in Suit]
    

    def is_trumpfcard(self, card: Card) -> bool:
        """Checks if the given card is a trumpf card in the current mode.

        This function returns True if the card's suit matches the current trumpf suit.

        Args:
            card (Card): The card to check.

        Returns:
            bool: True if the card is a trumpf card, False otherwise.
        """
        return card.suit.name == self.trumpf_name().name


    def get_card_to_play(self, available_cards: List[Card], state: Status, role: str) -> None | Card:
        """Selects the card to play according to the current mode's strategy.

        This function should be implemented by subclasses to determine which card to play based on the mode's logic.

        Returns:
            Card: The card chosen to play.
        """
        raise NotImplementedError


    def trumpf_name(self) -> Trumpf:
        """Returns the current trumpf (trump suit) for the mode.

        This function should be implemented by subclasses to provide the current trumpf.

        Returns:
            Trumpf: The current trumpf suit.
        """
        raise NotImplementedError

    def sort_by_rank(self, cards: List[Card]) -> List[Card]:
        """Returns a sorted list of Cards based on their strength in the current mode.

        This function should be implemented by subclasses to provide the sorted List.

        Returns:
            List[Card]: A sorted List of Cards.
        """
        raise NotImplementedError


    def is_bock(self, card: Card) -> bool:
        """Checks if the given card is the strongest ("bock") remaining.

        This function returns True if there are no stronger cards remaining than the given card.
        This function ignores cards of trumpf color, unless the provided card itself is of trumpf color.

        Args:
            card (Card): The card to check.

        Returns:
            bool: True if the card is the strongest remaining, False otherwise.
        """
        return len(self.stronger_cards_remaining(card)) == 0


    def get_current_bock(self, suit: Suit) -> None | Card:
        raise NotImplementedError


    def cards_beating_current_stich(self, available_cards: List[Card], state: Status) -> List[Card]:
        """Returns all available cards that can beat the current strongest card on the table.

        This function identifies which cards from the player's available cards are stronger than the current stich winner, or returns all available cards if the table is empty.

        Args:
            available_cards (List[Card]): The list of cards the player can play.
            state (Status): The current game state.

        Returns:
            List[Card]: A sorted list of cards that can beat the current stich winner, or all available cards if the table is empty.
        """
        current_position: int = len(state.table)
        if current_position != 0:
            for card_played in state.table:
                if card_played.player_id == self.card_counter.round_leader(state):
                    current_stich_winner: Card = from_string_to_card(card_played.card)
                    break
            cards_beating_winner: List[Card] = self.stronger_cards_remaining(current_stich_winner)
            beating_cards: List[Card] = []
            for card in available_cards:
                if card in cards_beating_winner:
                    beating_cards.append(card)
        else:
            beating_cards = available_cards
        return sorted(beating_cards, key=lambda card: card.get_score(get_trumpf(state.trumpf)))


    def bock_distance(self, card: Card, state: Status) -> int:
        """Calculates the number of stronger cards of the same suit that are not in hand or on the table.

        This function returns how many cards of the same suit are stronger than the given card, excluding those in the player's hand or already played on the table.

        Args:
            card (Card): The card to compare against.
            state (Status): The current game state.

        Returns:
            int: The number of stronger cards of the same suit not in hand or on the table.
        """
        stronger: List[Card] = self.card_counter.filter_not_dead_cards_of_same_suit(card, lambda x: x.value > card.value)
        stronger = [x for x in stronger if x not in self.card_counter.get_hand()]
        table_cards: List[Card] = [from_string_to_card(x.card) for x in state.table]
        stronger = [x for x in stronger if x not in table_cards]
        return len(stronger)


    def create_rank_comparator(self, card1: Card, card2: Card):
        """Creates a comparator for ranking two cards according to the current mode.

        This function should be implemented by subclasses to compare the rank of two cards based on the mode's rules.

        Args:
            card1 (Card): The first card to compare.
            card2 (Card): The second card to compare.

        Returns:
            Callable: A comparator function for ranking cards.
        """
        raise NotImplementedError


    def stronger_cards_remaining(self, card: Card) -> List[Card]:
        raise NotImplementedError


    def available_suits(self, available_cards: List[Card]) -> List[Suit]:
        """Returns a list of suits present in the available cards.

        This function identifies which suits are represented in the player's available cards.

        Args:
            available_cards (List[Card]): The list of cards to check.

        Returns:
            List[Suit]: A list of suits found in the available cards.
        """
        cards_per_suit: List[Tuple[int, List[Card]]] = split_cards_by_suit(available_cards)
        return [x[0] for x in cards_per_suit if len(x[1]) > 0]


    def is_nth_nut(self, number_of_stronger_cards: int, card: Card) -> bool:
        """Checks if exactly n cards are stronger than given card.

        This function returns True if there are exactly n stronger cards remaining than the given card.

        Args:
            n (int): The position to check (nth strongest).
            card (Card): The card to check.

        Returns:
            bool: True if the card is the nth strongest remaining, False otherwise.
        """
        return len(self.stronger_cards_remaining(card)) == number_of_stronger_cards


    def have_to_serve(self, available_suits: List[Suit], round_color: Suit | None) -> bool:
        """Determines if the player must serve the round color.

        This function checks if the round color is present in the player's available suits and is not None.

        Args:
            available_suits (List[Suit]): The suits available to the player.
            round_color (Suit | None): The color that must be served.

        Returns:
            bool: True if the player must serve the round color, False otherwise.
        """
        return round_color is not None and round_color in available_suits
    

    def add_flag(self, flag: Flag, player_id: int) -> None:
        """Adds a flag to the specified player's flag list if not already present.

        This function appends the given flag to the player's flags, unless it is already present, except for PreviouslyHadStichFlag which is always added.

        Args:
            flag (Flag): The flag to add.
            player_id (int): The ID of the player to update.

        Returns:
            None
        """
        if flag not in self.card_counter.flags[player_id] or isinstance(flag, PreviouslyHadStichFlag):
            self.card_counter.flags[player_id].append(flag)
        return None
    

    def update_player_lost_round_flags(self, player_id: int, state: Status) -> None:
        """Updates flags for the player when their team lost a round and this player was last to play.

        This function adds flags for all stronger cards not matching the trumpf suit, indicating the partner does not have those cards.

        Args:
            player_id (int): The ID of the partner player.
            state (Status): The current game state.

        Returns:
            None
        """
        for stronger_card in self.stronger_cards_remaining(self.card_counter.current_stich[self.card_counter.round_leader(state)]):
            if not self.is_trumpfcard(stronger_card):
                self.add_flag(DoesntHaveCardFlag(stronger_card), player_id)
        return None


    def player_played_trumpf(self, player_id: int) -> bool:
        """Checks if the specified player played a trumpf card in the current stich.

        This function returns True if the player's card matches the current trumpf suit.

        Args:
            player_id (int): The ID of the player to check.

        Returns:
            bool: True if the player played a trumpf card, False otherwise.
        """
        return self.is_trumpfcard(self.card_counter.current_stich[player_id])


    def update_partner_first_player_flag(self, card: Card, state: Status) -> None:
        raise NotImplementedError


    def update_first_player_flags(self,player_id: int, card: Card, state: Status) -> None:
        raise NotImplementedError


    def update_non_first_player_flags(self, player_id: int, card: Card, state: Status) -> None:
        raise NotImplementedError


    def update_flags_end_of_round(self, player_id: int, state: Status) -> None:
        """Updates flags at the end of a round based on which team lost the stich.

        This function determines if the partner or opponents lost the round and updates flags accordingly for the player who played last.

        Args:
            player_id (int): The ID of the player who played last in the round.
            state (Status): The current game state.

        Returns:
            None
        """
        # Me and Partner lose this Stich. Partner was last to play. -> Remove all non-Trumpf cards from partners hand, that could have won the round.
        player_is_partner: bool = player_id == self.card_counter.partner_id
        partner_lost_round: bool = player_is_partner and not self.card_counter.own_team_round_leader(state)
        
        # Both opponents lose this Stich. One opponent played the last card. -> Remove all non-Trumpf cards from the opponents hand, that could have won the round.
        player_is_opponent: bool = player_id in [self.card_counter.opponent_1_id, self.card_counter.opponent_2_id]
        opponent_lost_round: bool = player_is_opponent and self.card_counter.own_team_round_leader(state)
        
        condition: bool = partner_lost_round or opponent_lost_round
        if condition:
            self.update_player_lost_round_flags(player_id, state)
        return None


    def update_flags(self, player_id: int, card: Card, state: Status) -> None:
        raise NotImplementedError


    def card_played(self, player_id: int, card: Card, state: Status) -> None:
        """Registers a played card and updates internal game state and flags.

        This function records the card in the play history, tracks the current stich, and triggers flag updates, resetting the current stich at the end of each round.

        Args:
            player_id (int): The ID of the player who played the card.
            card (Card): The card that was played.
            state (Status): The current game state.

        Returns:
            None
        """
        self.card_counter.played_cards[player_id].append(card)
        self.card_counter.played_count += 1
        self.card_counter.current_stich[player_id] = card
        self.update_flags(player_id, card, state)
        if self.card_counter.played_count % 4 == 0:
            self.card_counter.current_stich = {}