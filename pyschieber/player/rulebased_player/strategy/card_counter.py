from __future__ import annotations
from typing import TYPE_CHECKING

## Libraries

# Type Hinting
from typing import List, Dict, Callable, Tuple
from pyschieber.player.base_player import BasePlayer
from pyschieber.card import Card
from pyschieber.player.treePlayer.helpers.state_dict_to_dataclass import Status


# Code
from pyschieber.player.treePlayer.strategy.flags.flags import DoesntHaveCardFlag, PreviouslyHadStichFlag, FailedToServeSuitFlag, SuitAngezogenFlag, SuitVerworfenFlag, NumberOfTrumpfFlag, Flag
from pyschieber.deck import Deck
from pyschieber.card import from_string_to_card
from pyschieber.rules.stich_rules import stich_rules
from pyschieber.trumpf import get_trumpf
from pyschieber.stich import PlayedCard
from pyschieber.suit import Suit
from math import floor


class CardCounter:

    def __init__(self, player: BasePlayer) -> None:
        """
        played_cards:   keeps track on which player played which card.
        flags:          keeps track on flags for each player.
        played_count:   keeps track on how many cards have been played in total.
        current_stich:  keeps track on what cards are currently on the table. index is ID of respective player.

        """
        self.played_cards: List[List[Card]] = [[],[],[],[]]
        self.flags: List[List[Flag]] = [[],[],[],[]]
        self.played_count: int = 0
        self.current_stich: Dict[int, Card] = {}
        self.me = player
        self.partner_id: int = (self.me.id + 2) % 4
        self.opponent_1_id: int = (self.me.id + 1) % 4
        self.opponent_2_id: int = (self.me.id + 3) % 4


    def current_round(self) -> int:
        """Gives back how many rounds have been played (max 9)

        Returns:
            int: round number
        """
        return floor(self.played_count/4)


    def own_team_round_leader(self, state: Status) -> bool:
        """Returns True if our team won this round.

        Args:
            state (Dict): GameState

        Returns:
            bool: True if our team won.
        """
        return self.round_leader(state) in [self.me.id, self.partner_id]


    def round_leader(self, state: Status) -> None | int:
        """Gets player_id which currently controls the strongest card on the table.

        Args:
            state (dict): Gamestate

        Returns:
            int: player_id (Yes, this is correct. Has been tested.)
        """
        if len(self.get_table_cards()) == 0:
            return None
        return stich_rules[get_trumpf(state.trumpf)](played_cards=self.get_table_cards()).player
    

    def is_round_leader(self, player_id: int, state: Status) -> bool:
        round_leader = self.round_leader(state)
        return round_leader == player_id



    def get_hand(self) -> List[Card]:
        """Returns handcards of player

        Returns:
            list(Card): Handcards
        """
        return self.me.cards


    def get_table_cards(self) -> List[Tuple[int, Card]]:
        """Returns all cards on the table and who played which.

        Returns:
            list(Cards,player_id): tablecards and player_id.
        """
        cards_on_table = []
        for player_id in self.current_stich:
            cards_on_table.append(PlayedCard(player=player_id, card=self.current_stich[player_id]))
        return cards_on_table


    def cards_played(self) -> List[Card]:
        """Gets every card that has been played up until now by all players.

        Returns:
            list: All Cards that have been played.
        """
        played: List[Card] = []
        for x in range(4):
            played.extend(self.played_cards[x])
        return played


    def seen_cards(self) -> List[Card]:
        """Gets all cards that were either played or are on self's Hand.

        Returns:
            list: Cards
        """
        seen: List[Card] = []
        seen.extend(self.cards_played())
        seen.extend(self.me.cards)
        return seen


    def remaining_cards(self, gone: List[Card]) -> List[Card]:
        """Gets all cards that are not in "gone".

        Args:
            gone (List, Cards): A List of Cards that are "gone".

        Returns:
            list, Cards: All cards except the ones declared in "gone".
        """
        d = Deck()
        return [x for x in d.cards if x not in gone]


    def remaining_by_suit(self, suit: Suit) -> List[Card]:
        """Gets remaining Cards on other players hands of declared suit.

        Args:
            suit (Suit): One of four Card Suits

        Returns:
            list: Remaining Cards of said suit.
        """
        return [x for x in self.unknown_cards() if x.suit == suit]


    def unknown_cards(self) -> List[Card]:
        """Gets all cards that were not yet played and are not on self's hand.

        Returns:
            list, Cards: remaining Cards on other players hands.
        """
        return self.remaining_cards(self.seen_cards())


    def dead_cards(self) -> List[Card]:
        """Gets all Cards that were played with and including the previous round. (No cards on table).

        Returns:
            list, Cards: List of Cards
        """
        dead: List[Card] = []
        current_round = int(self.played_count/4)
        for player_id in range(4):
            dead.extend(self.played_cards[player_id][:current_round])
        return dead


    def filter_cards_of_same_suit(self, card: Card, predicate: Callable) -> List[Card]:
        """_summary_

        Args:
            card (Card): _description_
            predicate (function): _description_

        Returns:
            List[Card]: _description_
        """
        unknown_of_same_suit: List[Card] = list(filter(lambda x: x.suit == card.suit, self.unknown_cards()))
        return list(filter(predicate, unknown_of_same_suit))
    

    def filter_suit_cards_from_tuple(self, cards: List[Tuple[Suit, List[Card]]], suit: Suit) -> List[Card]:
        """Returns the list of cards for a given suit from a list of (Suit, List[Card]) tuples.

        This function searches the provided list of tuples and returns the list of cards corresponding to the specified suit.

        Args:
            cards (List[Tuple[Suit, List[Card]]]): The list of (Suit, List[Card]) tuples.
            suit (Suit): The suit to search for.

        Returns:
            List[Card]: The list of cards for the specified suit.
        """
        return [x[1] for x in cards if x[0] == suit][0]


    def filter_not_dead_cards_of_same_suit(self, card: Card, predicate: Callable) -> List[Card]:
        """Takes all cards that were played up until and including last round.
         Filters them to only get the ones with the same suit as given "card".
         Filters this by given "predicate".

        Args:
            card (Card): Card for which's suit we want to filter
            predicate (Callable): List of Cards we want to filter for

        Returns:
            list, cards: List of filtered cards
        """
        remaining_cards = self.remaining_cards(self.dead_cards())
        remaining_of_same_suit = list(filter(lambda x: (x.suit == card.suit), remaining_cards))
        return list(filter(predicate, remaining_of_same_suit))


    def had_stich_previously(self, player_id: int) -> bool:
        """This function returns False if a player did not win a stich yet.

        Args:
            player_id (int): player we are interested in.

        Returns:
            bool: If player_id PreviouslyHadStichFlag.
        """
        return any(
            isinstance(flag, PreviouslyHadStichFlag)
            for flag in self.flags[player_id]
        )


    def has_suit_likelihood(self, player_id: int, suit: Suit, state: Status) -> float:
        """Calculates the probabilty for given "player_id" to have "suit" on his hand.

        Args:
            player_id (int): player we are interested in
            suit (suit): suit we are interested in
            state (dict): gamestate

        Returns:
            float: probability
        """
        return self.has_cards_likelihood(player_id, self.remaining_by_suit(suit), state)


    def has_cards_likelihood(self, player_id: int, cards: List[Card], state: Status) -> float:
        """Calculates the probability, that given "player_id" has "cards" on his hand.

        Args:
            player_id (int): player we are interested in.
            cards (list, Card): cards we are interested in.
            state (dict): Gamestate

        Returns:
            float: probability
        """
        likelihood = 1
        for card in cards:
            likelihood = likelihood * (1 - self.has_card_likelihood(player_id, card, state))
        return 1 - likelihood


    def has_card_likelihood(self, player_id: int, card: Card, state: Status) -> float:
        """Calculates the probability that the specified player holds the given card.

        This function checks if the card is already played or held, evaluates flags indicating the player cannot have the card, and computes the likelihood based on other players' flags.

        Args:
            player_id (int): The ID of the player to check.
            card (Card): The card to check for.
            state (Status): The current game state.

        Returns:
            float: The probability that the player holds the card.
        """
        # check if card was already played or we have it on hand.
        if card in self.get_hand() or card in [x for y in self.played_cards for x in y]:
            return 0

        # Check if player does not have card or failed to serve the cards suit.
        for flag in self.flags[player_id]:
            failed_to_serve_suit: bool = isinstance(flag, FailedToServeSuitFlag) and card.suit == flag.color
            does_not_have_card: bool = isinstance(flag, DoesntHaveCardFlag) and flag.card == card
            if failed_to_serve_suit or does_not_have_card:
                return 0

        # Calculate probability
        potential_holders = 3
        for p_id in range(4):
            if p_id in [self.me.id, player_id]:
                continue
            for flag in self.flags[p_id]:
                failed_to_serve_suit: bool = isinstance(flag, FailedToServeSuitFlag) and card.suit == flag.color
                does_not_have_card: bool = isinstance(flag, DoesntHaveCardFlag) and flag.card == card
                if failed_to_serve_suit or does_not_have_card:
                    potential_holders -= 1
                    break

        return 1 / potential_holders if potential_holders > 0 else 0


    def get_suits_by_strength(self, player_id: int) -> List[Suit]:
        """Returns a sorted list for given "player_id". 
        The list sorted all suits by player strength, beginning with the strongest suit of player_id. 

        Note: Do not remove the for loops. They are needed in that order.

        Args:
            player_id (int): player we are interested in.

        Returns:
            list, Suits: player_id's suits ordered by strength.
        """
        # TODO: The way doesnthavecardflag is used here to guess a weak suit is better than nothing, but a bit primitive. Can be improved?
        strong: List[Suit] = []
        weak: List[Suit] = []

        failed_to_serve_suit_flag = self.get_failed_to_serve_suits_flags(player_id)
        suit_angezogen_flag = self.get_angezogen_flags(player_id)
        suit_verworfen_flag = self.get_tossed_suits_flags(player_id)
        does_not_have_card_flag = self.get_doesnt_have_card_flags(player_id)
        # TODO: also consider opponent flags (like failed to serve or tossed suits.)

        for suit in failed_to_serve_suit_flag:
            if suit not in weak:
                    weak.append(suit)

        for suit in suit_angezogen_flag:
            if suit not in weak and suit not in strong:
                    strong.append(suit)

        for suit in suit_verworfen_flag:
            if suit not in weak and suit not in strong:
                    weak.append(suit)

        for card in does_not_have_card_flag:
            if card.suit not in weak:
                    weak.append(card.suit)

        for suit in Suit:
            if suit not in weak and suit not in strong:
                weak.append(suit)

        preference = weak + list(reversed(strong))
        return list(reversed(preference))
    

    def get_angezogen_flags(self, player_id: int) -> List[Suit]:
        """Gets all "angezogen" suits for given "player_id".

        Args:
            player_id (int): ID of player we are interested in.

        Returns:
            List: suits that a given player is good in.
        """
        return list(map(lambda y: y.color, filter(lambda x: isinstance(x, SuitAngezogenFlag), self.flags[player_id])))
    

    def get_doesnt_have_card_flags(self, player_id: int) -> List[Card]:
        """Gets all "angezogen" suits for given "player_id".

        Args:
            player_id (int): ID of player we are interested in.

        Returns:
            List: suits that a given player is good in.
        """
        return list(map(lambda y: y.card, filter(lambda x: isinstance(x, DoesntHaveCardFlag), self.flags[player_id])))
    

    def get_failed_to_serve_suits_flags(self, player_id: int) -> List[Suit]:
        """Returns all suits that the given player failed to serve.

        This function collects and returns a list of suits for which the player has a FailedToServeSuitFlag.

        Args:
            player_id (int): The ID of the player to check.

        Returns:
            List[Suit]: A list of suits the player failed to serve.
        """
        return list(map(lambda y: y.color, filter(lambda x: isinstance(x, FailedToServeSuitFlag), self.flags[player_id])))


    def get_had_stich_flags(self, player_id: int) -> List[PreviouslyHadStichFlag]:
        """Returns all suits that the given player failed to serve.

        This function collects and returns a list of suits for which the player has a FailedToServeSuitFlag.

        Args:
            player_id (int): The ID of the player to check.

        Returns:
            List[Suit]: A list of suits the player failed to serve.
        """
        return list(map(lambda y: y, filter(lambda x: isinstance(x, PreviouslyHadStichFlag), self.flags[player_id])))


    def get_tossed_suits_flags(self, player_id: int) -> List[Suit]:
        """Gets all "verworfen" suits for given "player_id".

        Args:
            player_id (int): player we are interested in

        Returns:
            List, suit: suits that given player is bad in.
        """
        return list(map(lambda y: y.color, filter(lambda x: isinstance(x, SuitVerworfenFlag), self.flags[player_id])))


    def get_number_of_trumpf_flag(self, player_id: int) -> NumberOfTrumpfFlag | None:
        """Retrieves the NumberOfTrumpfFlag for the specified player if it exists.

        This function searches the player's flags and returns the first NumberOfTrumpfFlag found, or None if no such flag is present.

        Args:
            player_id (int): The ID of the player whose trumpf count flag is requested.

        Returns:
            NumberOfTrumpfFlag or None: The player's NumberOfTrumpfFlag, or None if no flag is set.
        """
        flag_list = list(map(lambda y: y, filter(lambda x: isinstance(x, NumberOfTrumpfFlag), self.flags[player_id])))
        return flag_list[0] if flag_list else None
    

    def get_round_color(self, state: Status) -> Suit | None:
        """Returns the color (suit) of the current round based on the first card on the table.

        This function determines the round color by inspecting the first card played in the current stich, or returns None if the table is empty.

        Args:
            state (Status): The current game state.

        Returns:
            Suit or None: The suit of the first card on the table, or None if no cards have been played.
        """
        return (
            from_string_to_card(state.table[0].card).suit
            if len(state.table) > 0
            else None
        )
    

if __name__ == "__main__":
    print('This script cannot be run by itself...')