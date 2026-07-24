from pyschieber.player.treePlayer.strategy.mode.uncolored_trumpf import UncoloredTrumpf
from pyschieber.player.treePlayer.strategy.card_counter import CardCounter
from pyschieber.helpers.game_helper import split_card_values_by_suit, split_cards_by_suit
from pyschieber.trumpf import Trumpf
from pyschieber.card import Card
from pyschieber.suit import Suit
from pyschieber.card import from_string_to_card
from typing import Literal, List, Dict, Tuple
from pyschieber.player.treePlayer.helpers.state_dict_to_dataclass import Status


class TopDownMode(UncoloredTrumpf):

    def __init__(self, card_counter: CardCounter) -> None:
        self.card_counter = card_counter


    def trumpf_name(self) -> Literal[Trumpf.OBE_ABE]:
        """Returns the name of the trumpf for this mode.

        This function provides the specific trumpf name associated with the TopDownMode strategy.

        Returns:
            Literal[Trumpf.OBE_ABE]: The name of the trumpf for this mode.
        """
        return Trumpf.OBE_ABE


    def calculate_mode_score(self, cards: List[Card], geschoben: bool) -> int:
        """Calculates a score for the given hand to evaluate its suitability for this trumpf.

        This function scores the hand by rewarding consecutive high cards and high-value cards in each suit, indicating how well the hand fits the trumpf strategy.

        Args:
            cards (List[Card]): The hand cards to evaluate.
            geschoben (bool): Not used.

        Returns:
            int: The calculated score for the hand.
        """
        score: int = 0
        cards_by_suit = split_card_values_by_suit(cards)

        for suit, suit_cards in cards_by_suit:
            sorted_cards = self.sort_by_rank(suit_cards)
            best_remaining_rank = 14

            for card in sorted_cards:
                if card == best_remaining_rank:
                    best_remaining_rank -= 1
                    score += 13
                elif best_remaining_rank < 12:
                    score += 10

        return score


    def get_current_bock(self, suit: Suit) -> None | Card:
        """Returns the current strongest card ("bock") of the given suit.

        This function collects all remaining cards of the specified suit and returns the one with the highest rank according to the current trumpf.

        Args:
            suit (Suit): The suit for which to find the current bock.

        Returns:
            Card or None: The strongest card of the given suit, or None if no cards are available.
        """
        # Info: This function was incorrect in challenge player. the sorted() function missed the reverse=True statement.
        # This function was moved here from mode.py.
        remaining: List[Card] = []
        remaining.extend(self.card_counter.remaining_by_suit(suit))
        for suit_cards in split_cards_by_suit(self.card_counter.get_hand()):
            if suit_cards[0] == suit:
                remaining.extend(suit_cards[1])
        remaining.extend(self.card_counter.current_stich.values())

        if not remaining:
            return None

        trumpf = self.trumpf_name()
        remaining_sorted = sorted(remaining, key=lambda card: card.get_score(trumpf), reverse=True)
        return remaining_sorted[0]


    def stronger_cards_remaining(self, card: Card) -> List[Card]:
        """Returns a list of stronger cards of the same suit that are not yet dead.

        This function filters and returns all cards of the same suit as the given card that have a higher value and are still in play.

        Args:
            card (Card): The card to compare against.

        Returns:
            List[Card]: A list of stronger cards of the same suit that are not dead.
        """
        return self.card_counter.filter_not_dead_cards_of_same_suit(card, lambda x: x.value > card.value)


    def get_stich_card(self, cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> Card | None:
        """Selects a card that can win the current stich, if possible.

        This function evaluates the cards of the current stich color and determines which, if any, can win the stich based on the current table and the likelihood of opponents holding stronger cards.

        Args:
            cards_by_suit (List[Tuple[Suit, List[int]]]): The player's cards grouped by suit.
            state (Status): The current game state.

        Returns:
            Card or None: A card that can win the stich, or None if no such card is found.
        """
        # Empty table: there is no stich card.
        table_is_empty: bool = len(state.table) == 0
        if table_is_empty:
            return None

        current_stich_color = from_string_to_card(state.table[0].card).suit
        current_color_cards = [x[1] for x in cards_by_suit if x[0] == current_stich_color][0]
        cards = self.cards_beating_current_stich(current_color_cards, state)
        stich_cards = []

        # We are the last player this stich. Add all our cards beating current stich to the candidates.
        if len(state.table) == 3:
            stich_cards.extend(cards)

        # We have cards in current suit and are second or third player to play this round.
        if len(cards) > 0 and len(state.table) < 3:
            for card in cards:
                stronger = self.stronger_cards_unknown(card)
                if not stronger:
                    stich_cards.append(card)
                opponent_1_cannot_beat_card = bool(self.card_counter.has_cards_likelihood(self.card_counter.opponent_1_id, stronger, state))
                if opponent_1_cannot_beat_card: # Opponent 2 has already played. We are first player (then there is no suit on table), or the played before us.
                    stich_cards.append(card)

        # We have no cards that beat current stich
        if not stich_cards:
            return None

        # Return strongest card that beats current stich.
        stich_cards = self.sort_by_rank(stich_cards)
        return next(
            (card for card in stich_cards if card.value in [8, 10]),
            stich_cards[0],
        )


    def stronger_cards_unknown(self, card: Card) -> List[Card]:
        """Returns a list of stronger cards of the same suit that are still unknown.

        This function filters and returns all cards of the same suit as the given card that have a higher value and are not yet revealed or played.

        Args:
            card (Card): The card to compare against.

        Returns:
            List[Card]: A list of stronger cards of the same suit that are still unknown.
        """
        return self.card_counter.filter_cards_of_same_suit(card, lambda x: x.value > card.value)


    def sort_by_rank(self, cards: List[Card]) -> List[Card]:
        """Sorts a list of cards by their rank in descending order.

        This function returns a new list of cards sorted by their rank, with the highest-ranked cards first.

        Args:
            cards (List[Card]): The list of cards to sort.

        Returns:
            List[Card]: The sorted list of cards.
        """
        return sorted(cards, reverse=True)


    def signal_passing_card(self, bocks: List[Card], cards_by_suit: Dict[Suit, List[Card]], state: Status) -> Card | None:
        """Selects a bock card to signal to the partner which suit to hold.

        This function evaluates the available bocks and suit information to choose a bock card that best signals the partner, considering suit strength, partner's hand, and game state.

        Args:
            bocks (List[Card]): The list of bock cards available to the player.
            cards_by_suit (Dict[Suit, List[Card]]): The available cards grouped by suit.
            state (Status): The current game state.

        Returns:
            Card or None: The selected bock card to signal, or None if no suitable card is found.
        """
        suit_candidates: Dict[Suit, List[Card]] = {}

        suit_angezogen_flags = self.card_counter.get_angezogen_flags(self.card_counter.me.id)
        partner_suit_verworfen_flags = self.card_counter.get_tossed_suits_flags(self.card_counter.partner_id)
        partner_does_not_have_suit_flags = self.card_counter.get_failed_to_serve_suits_flags(self.card_counter.partner_id)
        bocks_by_suit = dict(split_cards_by_suit(bocks))

        for suit in Suit:
            has_bock_of_suit = bocks_by_suit.get(suit) is not None
            suit_not_angezogen = suit not in suit_angezogen_flags
            partner_has_suit = suit not in partner_does_not_have_suit_flags
            partner_is_strong_in_suit = suit not in partner_suit_verworfen_flags
            has_sufficient_cards_of_suit = 2 <= len(cards_by_suit[suit]) <= 3
            has_at_least_one_non_bock_card_of_suit = False
            for card in dict(cards_by_suit)[suit]:
                if not self.bock_distance(card, state):
                    has_at_least_one_non_bock_card_of_suit = True

            condition = all([
                partner_has_suit,
                partner_is_strong_in_suit,
                has_bock_of_suit,
                suit_not_angezogen,
                has_sufficient_cards_of_suit,
                has_at_least_one_non_bock_card_of_suit
            ])
            if condition:
                suit_candidates[suit] = cards_by_suit[suit]

        candidate_suit: Suit | None = None
        candidate_val: int = 20
        for suit, cards in suit_candidates.items():
            value = self.sort_by_rank(cards)[-1].value
            if value < candidate_val:
                candidate_val = value
                candidate_suit = suit
        
        if candidate_suit is None:
            return None
        
        passing_cards: List[Card] = bocks_by_suit.get(candidate_suit)
        return self.sort_by_rank(passing_cards)[0]
    

    def toss_and_schmieren(self, available_cards: List[ Card], state: Status, round_color: Suit) -> Card | None:
        """Selects a card to toss and potentially score extra points if the partner is round leader.

        This function chooses a card to discard, prioritizing cards with value 8 or 10, when the partner is round leader and either the player is last or the stich is not beatable.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.
            round_color (Suit): The suit from which to select the tossable card.

        Returns:
            Card or None: The card to toss and schmieren, or None if no suitable card is found.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        weak_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == round_color][0])
        cards_beating_stich = self.cards_beating_current_stich(self.card_counter.unknown_cards(), state)
        beatable = bool(self.card_counter.has_cards_likelihood(self.card_counter.opponent_1_id, cards_beating_stich, state))
        partner_is_roundleader: bool = self.card_counter.is_round_leader(self.card_counter.partner_id, state)
        we_are_last_player: bool = len(state.table) == 3
        if partner_is_roundleader and (we_are_last_player or not beatable):
            for card in weak_cards:
                if card.value in [8, 10]:
                    return card
        return None


    def serve_tossable_card_of_suit(self, available_cards: List[ Card], state: Status, round_color: Suit) -> Card:
        """Selects a card to toss from a specific suit, prioritizing cards that can score extra points.

        This function attempts to select a card to toss and schmieren if possible; otherwise, it returns the weakest card of the specified suit.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.
            round_color (Suit): The suit from which to select the tossable card.

        Returns:
            Card: The card to toss from the specified suit.
        """
        candidate_card = self.toss_and_schmieren(available_cards, state, round_color)
        if candidate_card is not None:
            return candidate_card

        cards_by_suit = split_cards_by_suit(available_cards)
        weak_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == round_color][0])
        return weak_cards[-1]
    

    def get_weak_suit(self, available_cards: List[Card], state: Status) -> List[Card] | None:
        """Finds and returns the weakest suit from the available cards.

        This function determines the weakest suit to play or discard from, based on the current hand, the suits to toss, and the number of unknown cards in each suit.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            List[Card] or None: The list of cards in the weakest suit, or None if no such suit is found.
        """
        cards_by_suit_dict = dict(split_cards_by_suit(available_cards))
        suit_to_toss = self.get_suit_to_toss(available_cards, state)
        weak_suit = None

        weak_suit = cards_by_suit_dict.get(suit_to_toss)
        if weak_suit is not None:
            return weak_suit

        # Throw away cards of suits that were played the most.
        unknown_by_suit = split_cards_by_suit(self.card_counter.unknown_cards())

        count = 10

        for suit, suit_cards in unknown_by_suit:
            is_lower_amount_of_cards: bool = len(suit_cards) < count
            is_suit_in_hand: bool = cards_by_suit_dict.get(suit) is not None
            if is_lower_amount_of_cards and is_suit_in_hand:
                count = len(suit_cards)
                weak_suit = cards_by_suit_dict.get(suit)

        return weak_suit
    
    
    def serve_tossable_card_of_any_suit(self, available_cards: List[Card], state: Status) -> Card | None:
        """Selects a card to toss from any suit, prioritizing cards that can score extra points.

        This function determines the weakest suit and selects a card to toss, giving preference to cards with value 8 or 10 if the partner is round leader and the stich is not beatable.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The card to toss from any suit, or None if no suitable card is found.
        """
        weak_suit = self.get_weak_suit(available_cards, state)

        weak_cards = self.sort_by_rank(weak_suit)
        # check if weak_cards is None or empty list.
        if not bool(weak_cards):
            return None

        cards_beating_current_stich = self.cards_beating_current_stich(self.card_counter.unknown_cards(), state)
        beatable_by_opponent: bool = self.card_counter.has_cards_likelihood(self.card_counter.opponent_1_id, cards_beating_current_stich, state) != 0
        partner_is_round_leader = self.card_counter.is_round_leader(self.card_counter.partner_id, state)
        we_are_final_player = len(state.table) == 3
        if partner_is_round_leader and (we_are_final_player or not beatable_by_opponent):
            for card in weak_cards:
                if card.value in [8, 10]:
                    return card
        return weak_cards[-1]


    def get_tossable_card(self, available_cards: List[Card], state: Status) -> Card | None:
        """Selects a card to toss based on the current hand and game state.

        This function determines which card to discard, considering whether the player must serve the round color, the weakest suit, and the likelihood of the card being beaten by opponents.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The card to toss, or None if no suitable card is found.
        """
        eligible_suits = self.available_suits(available_cards)
        round_color = self.card_counter.get_round_color(state)

        # Player is not the first player of this round and has the table suit on hand -> anhalten and verwerfen
        if self.have_to_serve(eligible_suits, round_color):
            return self.serve_tossable_card_of_suit(available_cards, state, round_color)

        else:
            return self.serve_tossable_card_of_any_suit(available_cards, state)


    def rate_initial_suit_strength(self, cards_of_same_suit: List[Card]) -> int:
        """Calculates the initial strength score for a suit based on the player's cards.

        This function evaluates the cards of a given suit and assigns a score based on their rank, rewarding consecutive high ranks and high cards.

        Args:
            cards_of_same_suit (List[Card]): The list of cards of the same suit.

        Returns:
            int: The calculated strength score for the suit.
        """
        score: int = len(cards_of_same_suit)
        best_remaining_rank = 14
        cards_of_same_suit = self.sort_by_rank(cards_of_same_suit)

        for card in cards_of_same_suit:
            if card.value == best_remaining_rank:
                best_remaining_rank -= 1
                score += 13
            elif best_remaining_rank < 12:
                score += 10
        return score