from pyschieber.player.treePlayer.strategy.mode.mode import Mode
from pyschieber.player.treePlayer.strategy.card_counter import CardCounter
from pyschieber.helpers.game_helper import split_card_values_by_suit, split_cards_by_suit
from pyschieber.trumpf import Trumpf
from pyschieber.suit import Suit
from pyschieber.card import from_string_to_card, Card
from typing import List, Tuple, Dict
from pyschieber.player.treePlayer.strategy.flags.flags import DoesntHaveCardFlag, PreviouslyHadStichFlag, FailedToServeSuitFlag, SuitAngezogenFlag, SuitVerworfenFlag, NumberOfTrumpfFlag
from pyschieber.player.treePlayer.helpers.state_dict_to_dataclass import Status
from pyschieber.player.treePlayer.helpers.helperfunctions import flatten_matrix, is_empty_or_none
from copy import deepcopy


class TrumpfColorMode(Mode):
    def __init__(self, suit: Suit, card_counter: CardCounter) -> None:
        self.suit = suit
        self.card_counter = card_counter


    def trumpf_name(self) -> Trumpf:
        """Returns the trumpf name for the current suit.

        This function provides the trumpf type corresponding to the suit selected for this mode.

        Returns:
            Trumpf: The trumpf type for the current suit.
        """
        return Trumpf[self.suit.name]


    def calculate_mode_score(self, cards: List[Card], geschoben: bool) -> int:
        """Calculates a score for the given hand to evaluate its suitability for this trumpf color.

        This function scores the hand by rewarding high-value trumpf cards and consecutive high cards in other suits, indicating how well the hand fits the trumpf color strategy.

        Args:
            cards (List[Card]): The hand cards to evaluate.
            geschoben (bool): Indicates if the game was pushed (affects scoring for certain cards).

        Returns:
            int: The calculated score for the hand.
        """
        score: int = 0

        cards_by_suit = split_card_values_by_suit(cards)

        for suit, suit_cards in cards_by_suit:
            if suit == self.suit:
                for card in suit_cards:
                    if card == 11:
                        score += 20 if geschoben else 30
                    elif card == 9:
                        score += 15
                    elif card == 14:
                        score += 12
                    else:
                        score += 10
            else:
                sorted_cards = sorted(suit_cards, reverse=True)
                best_remaining_rank = 14

                for card in sorted_cards:
                    if card != best_remaining_rank:
                        break
                    best_remaining_rank -= 1
                    score += 4
        return score
    

    def get_current_bock(self, suit: Suit) -> None | Card:
        """Returns the current strongest card ("bock") of the given suit.

        This function collects all remaining cards of the specified suit and returns the one with the highest rank according to the current trumpf.

        Args:
            suit (Suit): The suit for which to find the current bock.

        Returns:
            Card or None: The strongest card of the given suit, or None if no cards are available.
        """
        # Warning! Does not include Trumpf cards, if suit is not trumpf itself!
        # Check if a new function needs to be written to include this or if this function can be expanded. Where is this function used?
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

        This function identifies all cards of the same suit as the given card that are still in play and have a higher rank, considering trumpf rules if applicable.

        Args:
            card (Card): The card to compare against.

        Returns:
            List[Card]: A list of stronger cards of the same suit that are not dead.
        """
        stronger_cards: List[Card] = []

        if card.suit == self.suit:
            stronger_cards.extend(self.card_counter.filter_not_dead_cards_of_same_suit(card, lambda x: x.get_trumpf_rank() > card.get_trumpf_rank()))
        else:
            remaining_cards = self.card_counter.remaining_cards(self.card_counter.dead_cards())
            remaining_cards_by_suit: Dict[Suit, List[Card]] = dict(split_cards_by_suit(remaining_cards))
            suit_cards = remaining_cards_by_suit.get(self.suit)
            if suit_cards is not None:
                stronger_cards.extend(suit_cards)
            stronger_cards.extend(self.card_counter.filter_not_dead_cards_of_same_suit(card, lambda x: x.value > card.value))
        return stronger_cards


    def stronger_cards_unknown(self, card: Card) -> List[Card]:
        """Returns a list of stronger cards of the same suit that are still unknown.

        This function identifies all cards of the same suit as the given card that have a higher rank and are not yet revealed or played, considering trumpf rules if applicable.

        Args:
            card (Card): The card to compare against.

        Returns:
            List[Card]: A list of stronger cards of the same suit that are still unknown.
        """
        stronger_cards: List[Card] = []

        if card.suit == self.suit:
            stronger_cards.extend(self.card_counter.filter_cards_of_same_suit(card, lambda x: x.get_trumpf_rank() > card.get_trumpf_rank()))
        else:
            unknown_cards_by_suit: Dict[Suit, List[Card]] = dict(split_cards_by_suit(self.card_counter.unknown_cards()))
            suit_cards = unknown_cards_by_suit.get(self.suit)
            if suit_cards is not None:
                stronger_cards.extend(suit_cards)
            stronger_cards.extend(self.card_counter.filter_cards_of_same_suit(card, lambda x: x.value > card.value))
        return stronger_cards


    def is_non_trumpf_bock(self, card: Card) -> bool:
        """Checks if the given card is the highest remaining card of its suit, excluding trumpf.

        This function returns True if there are no stronger cards of the same suit left in play, and the card is not a trumpf.

        Args:
            card (Card): The card to check.

        Returns:
            bool: True if the card is the highest remaining non-trumpf card, False otherwise.
        """
        return len(self.card_counter.filter_not_dead_cards_of_same_suit(card, lambda x: x.value > card.value)) == 0


    def get_non_trumpf_bocks(self, available_cards: List[Card]) -> List[Card]:
        """Returns all non-trumpf cards in the hand that are currently bocks.

        This function filters the given cards to find those that are the highest remaining card of their suit while not belonging to the trumpf suit.

        Args:
            available_cards (List[Card]): The list of cards to evaluate.

        Returns:
            List[Card]: A list of non-trumpf bock cards from the given cards.
        """
        non_trumpf_bocks = []
        non_trumpf_bocks.extend(
            card
            for card in available_cards
            if self.is_non_trumpf_bock(card) and card.suit != self.suit
        )
        return non_trumpf_bocks


    def get_passing_card(self, cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> Card | None:
        """Selects a card to pass to the partner based on their likely strengths.

        This method attempts to pass a card in a suit where the partner is likely to have the strongest card (bock), or otherwise in their strongest suit.

        Args:
            cards_by_suit (List[Tuple[Suit, List[Card]]]): The player's hand grouped by suit.
            state (Status): The current game state.

        Returns:
            Card | None: The selected card to pass, or None if no suitable card is found.
        """
        for suit_cards in cards_by_suit:
            suit = suit_cards[0]
            cards = suit_cards[1]
            if not cards or suit == self.suit: # Added: we do not want to play trumpf suit as passing card.
                continue
            current_bock = self.get_current_bock(suit)
            if current_bock is None:
                continue
            partner_has_bock: bool = self.card_counter.has_card_likelihood(self.card_counter.partner_id, current_bock, state) == 1
            if partner_has_bock:
                return self.sort_by_rank(cards)[-1]

        partner_suits_by_strength = self.card_counter.get_suits_by_strength(self.card_counter.partner_id)
        for suit in partner_suits_by_strength:
            if cards := self.card_counter.filter_suit_cards_from_tuple(cards_by_suit, suit):
                return self.sort_by_rank(cards)[-1]
        return self.get_value_card(cards_by_suit, state) # Added, was None before.


    def can_make_all_stich(self, cards_by_suit: List[Tuple[Suit, List[Card]]], state) -> bool:
        """Checks whether all relevant cards in the player's hand behave like bocks (pseudo-bocks).

        This function evaluates the current round color, the player's hand, and the remaining cards to determine if, for every suit the player holds, their cards are as strong as the strongest remaining cards of that suit.
        This function does NOT check potential partner cards and if player and partner togeter have all bocks / pseudobocks.

        Args:
            cards_by_suit (List[Tuple[Suit, List[Card]]]): The player's cards grouped by suit.
            state (Status): The current game state.

        Returns:
            bool: True if all relevant cards in hand are pseudo-bocks, False otherwise.
        """
        # TODO: Check partner cards as well. Very complicated, as partner must be able to give us back control!
        # Or Opponents must be so bad they do not have any good cards left.
        # TODO: Implement the option to play trumpf and then see if our cards are NOW best cards.

        handcards = deepcopy(self.card_counter.get_hand())
        # check if we can win stich.
        cards_by_suit_dict = dict(cards_by_suit)
        round_color = self.card_counter.get_round_color(state)
        have_cards_of_round_color = bool(cards_by_suit_dict.get(round_color)) # checks if key is present and list of cards non-empty.

        # There are cards on the table and we do not have the round color -> cannot win stich.
        if round_color is not None and not have_cards_of_round_color:
            return False
        
        # There are cards on the table and we do have the round color -> check if we can win stich.
        if round_color is not None and have_cards_of_round_color:
            current_bock = self.get_current_bock(round_color)
            if current_bock not in dict(cards_by_suit).get(round_color):
                return False
            else:
                handcards.remove(current_bock)

        # get all remaining cards.
        remaining_cards = self.card_counter.remaining_cards(self.card_counter.cards_played())
        remaining_cards_by_suit = dict(split_cards_by_suit(remaining_cards))

        # filter cards such that only our suits remain (because only those will be relevant, as we can decide which suit is to be played.)
        opponent_1_no_trumpf = self.suit in self.card_counter.get_failed_to_serve_suits_flags(self.card_counter.opponent_1_id)
        opponent_2_no_trumpf = self.suit in self.card_counter.get_failed_to_serve_suits_flags(self.card_counter.opponent_2_id)
        opponents_no_trumpf = opponent_1_no_trumpf and opponent_2_no_trumpf
        handcards_by_suit = split_cards_by_suit(handcards)
        for suit, suit_cards in handcards_by_suit:
            if suit == self.suit and opponents_no_trumpf:
                continue
            sorted_cards = self.sort_by_rank(suit_cards)
            remaining = remaining_cards_by_suit.get(suit)
            remaining_sorted = self.sort_by_rank(remaining)
            for n, card in enumerate(sorted_cards):
                if n >= len(remaining_sorted):
                    continue
                if card != remaining_sorted[n]:
                    return False
        return True


    def should_win_stich_last_player(self, my_cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> bool:
        """Determines if the player should try to win the stich as the last player.

        This function checks if the player is last to play, no other players have cards of the round color, and the player has more than one card of the round color.

        Args:
            my_cards_by_suit (List[Tuple[Suit, List[Card]]]): The player's cards grouped by suit.
            state (Status): The current game state.

        Returns:
            bool: True if the player should try to win the stich as the last player, False otherwise.
        """
        are_last_player: bool = len(state.table) == 3
        round_color = self.card_counter.get_round_color(state)
        cards_of_suit_remaining: List[Card] = flatten_matrix([x[1] for x in split_cards_by_suit(self.card_counter.unknown_cards()) if x[0] == round_color])
        my_cards_of_suit = [x[1] for x in my_cards_by_suit if x[0] == round_color]
        return all([are_last_player, not cards_of_suit_remaining, len(my_cards_of_suit) > 1])


    def should_win_stich_not_last_player(self, my_cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> bool:
        """Determines if the player should try to win the stich when not the last player.

        This function checks if the player is not last to play, the last player has cards of the round color, only one card of the round color remains appart from own hand, and the player has more than one card of the round color.

        Args:
            my_cards_by_suit (List[Tuple[Suit, List[Card]]]): The player's cards grouped by suit.
            state (Status): The current game state.

        Returns:
            bool: True if the player should try to win the stich when not the last player, False otherwise.
        """
        are_last_player: bool = len(state.table) == 3
        round_color = self.card_counter.get_round_color(state)
        cards_of_suit_remaining: List[Card] = flatten_matrix([x[1] for x in split_cards_by_suit(self.card_counter.unknown_cards()) if x[0] == round_color])
        my_cards_of_suit = [x[1] for x in my_cards_by_suit if x[0] == round_color]
        last_player_has_cards_of_suit_remaining: bool = self.card_counter.has_suit_likelihood(self.card_counter.opponent_1_id, round_color, state) == 1
        return all([not are_last_player, last_player_has_cards_of_suit_remaining, len(cards_of_suit_remaining) == 1, len(my_cards_of_suit) > 1])


    def should_win_stich_partner_not_leader(self, state: Status) -> bool:
        """Determines if the player should try to win the stich when the partner is not the round leader.

        This function checks if the partner is not the round leader and if either the player is last to play or the opponent can beat the partner, indicating a situation where winning the stich may be necessary.

        Args:
            state (Status): The current game state.

        Returns:
            bool: True if the player should try to win the stich, False otherwise.
        """
        are_last_player: bool = len(state.table) == 3
        partner_is_roundleader = self.card_counter.is_round_leader(self.card_counter.partner_id, state)
        opponent_can_beat_partner = self.card_counter.has_cards_likelihood(self.card_counter.opponent_1_id, self.cards_beating_current_stich(self.card_counter.unknown_cards(), state), state) > 0
        condition = partner_is_roundleader and (are_last_player or not opponent_can_beat_partner)
        return not condition
    

    def want_stich(self, cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> bool:
        """Determines whether the player should attempt to win the current stich.

        This function evaluates the player's hand and the current game state to decide if winning the stich is advantageous, considering the player's position and the trumpf suit.

        Args:
            cards_by_suit (List[Tuple[Suit, List[Card]]]): The player's cards grouped by suit.
            state (Status): The current game state.

        Returns:
            bool: True if the player should attempt to win the stich, False otherwise.
        """
        if self.can_make_all_stich(cards_by_suit, state):
            return True

        color = from_string_to_card(state.table[0].card).suit
        if color != self.suit:
            if self.should_win_stich_last_player(cards_by_suit, state):
                return True
            if self.should_win_stich_not_last_player(cards_by_suit, state):
                return True
        return self.should_win_stich_partner_not_leader(state)


    def get_value_card(self, cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> None | Card:
        """Determines and returns the value card to play based on the current game state.

        This function evaluates all available cards and selects the one with the lowest probability of being beaten by opponents, or returns None if not applicable.

        Args:
            cards_by_suit (List[Tuple[Suit, List[Card]]]): The available cards grouped by suit.
            state (Status): The current game state.

        Returns:
            Card or None: The value card to play, or None if not applicable.
        """ # TODO: delete and instead use treesearch? Or good enough and resource efficient?
        if len(state.table) != 0:
            return None
        opponents_beating_card: Dict[Card, int] = {}
        for suit, suit_cards in cards_by_suit:
            for card in suit_cards:
                stronger = self.stronger_cards_remaining(card)
                if len(stronger) == 0:
                    opponents_beating_card[card] = 0
                else:
                    d1 = self.card_counter.has_card_likelihood(self.card_counter.opponent_1_id, card, state)
                    d2 = self.card_counter.has_card_likelihood(self.card_counter.opponent_2_id, card, state)
                    opponents_beating_card[card] = (d1+((1-d1)*d2))
        return min(opponents_beating_card, key=opponents_beating_card.get)


    def get_suit_to_toss(self, available_cards: List[Card], state: Status) -> Suit | None:
        """Determines which suit to toss based on the current hand and game state.

        This function selects a suit to discard, preferring suits already tossed, or otherwise the suit with the highest minimum bock distance.
        Never tosses Trumpf suit.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Suit or None: The suit to toss, or None if no suitable suit is found.
        """
        cards_by_suit = split_cards_by_suit(available_cards)

        # If we already tossed a suit, toss the same suit.
        tossed_suits = self.card_counter.get_tossed_suits_flags(self.card_counter.me.id)
        for suit, suit_cards in cards_by_suit:
            if suit not in tossed_suits:
                continue
            for card in suit_cards:
                if self.bock_distance(card, state) != 0:
                    return suit

        # TODO: Improve? Here, only checks bock distance. If we have only one card, card is clearly terrible if not bock.
        # maybe check if bock distance is larger than len(cards_of_suit)
        # Never toss suit with trumpf!
        bd_suits: List[Tuple[Suit, int]] = []
        for suit, suit_cards in cards_by_suit:
            if suit == self.suit:
                continue
            if suit not in tossed_suits:
                bock_distances: List[int] = []
                bock_distances.extend(self.bock_distance(card, state) for card in suit_cards)
                if bock_distances:
                    bd_suits.append((suit, min(bock_distances)))
                else:
                    bd_suits.append((suit, 0))

        return max(bd_suits,key=lambda item:item[1])[0] if bd_suits else None


    def get_stich_card(self, cards_by_suit: List[Tuple[Suit, List[int]]], state: Status) -> Card | None:
        """Determines the best card to play to win the current stich.

        This function evaluates the player's available cards and the current game state to select the strongest card that can win the stich, considering the player's position and the cards already played.

        Args:
            cards_by_suit (List[Tuple[Suit, List[int]]]): The player's cards grouped by suit.
            state (Status): The current game state.

        Returns:
            Card or None: The best card to play to win the stich, or None if no such card exists.
        """
        # Empty table: there is no stich card.
        table_is_empty: bool = len(state.table) == 0
        if table_is_empty:
            return None

        current_stich_color = from_string_to_card(state.table[0].card).suit
        current_color_and_trumpf_cards: List[Card] = flatten_matrix([x[1] for x in cards_by_suit if x[0] in [current_stich_color, self.suit]])
        cards = self.cards_beating_current_stich(current_color_and_trumpf_cards, state)
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
            (card for card in stich_cards if card.value == 10),
            stich_cards[0],
        )


    def sort_by_rank(self, cards: List[Card]) -> List[Card]:
        """Sorts the given cards in descending order based on their score for the current trumpf.

        This function ranks cards according to their value in the current trumpf mode, with the highest scoring card first.

        Args:
            cards (List[Card]): The list of cards to sort.

        Returns:
            List[Card]: The sorted list of cards, highest score first.
        """
        return sorted(cards, key=lambda card: card.get_score(self.trumpf_name()), reverse=True)


    def has_only_jack_of_trumpf(self, player_cards: List[Card]) -> bool:
        """Checks if the player holds only the jack of the trumpf suit.

        This function returns True if the player's hand contains only the jack in the trumpf suit, and no other trumpf cards.

        Args:
            player_cards (List[Card]): The player's current hand.

        Returns:
            bool: True if only the jack of trumpf is present, False otherwise.
        """
        cards_by_suit: dict[Suit, List[Card]] = dict(split_cards_by_suit(player_cards))
        cards_of_trumpf = cards_by_suit.get(self.suit)

        # Check if we have exactly one card of trumpf suit.
        if cards_of_trumpf is None or len(cards_of_trumpf) != 1:
            return False

        # Check if any of our trumpf cards is Jack.
        if any(card.value == 11 for card in cards_of_trumpf):
            return True
        return False


    def has_jack_and_one_trumpf(self, player_cards: List[Card]) -> bool:
        """Checks if the player holds exactly two trumpf cards, one of which is the jack.

        This function returns True if the player's hand contains exactly two cards of the trumpf suit, and one of them is the jack.

        Args:
            player_cards (List[Card]): The player's current hand.

        Returns:
            bool: True if the hand contains only the jack and one other trumpf card, False otherwise.
        """
        cards_by_suit: dict[Suit, List[Card]] = dict(split_cards_by_suit(player_cards))
        cards_of_trumpf = cards_by_suit.get(self.suit)

        # Check if we have exactly two cards of trumpf suit.
        if cards_of_trumpf is None or len(cards_of_trumpf) != 2:
            return False

        # Check if any of our trumpf cards is Jack.
        if any(card.value == 11 for card in cards_of_trumpf):
                return True
        return False


    def has_trumpfass_best_card(self, player_cards: List[Card]) -> bool:
        """Checks if the player holds the trumpf ace as their best trumpf card.

        This function returns True if the player's trumpf cards include the ace but do not include the jack or the nell.

        Args:
            player_cards (List[Card]): The player's current hand.

        Returns:
            bool: True if only the trumpf ace is present without the jack or nell, False otherwise.
        """
        cards_by_suit: dict[Suit, List[Card]] = dict(split_cards_by_suit(player_cards))
        cards_of_trumpf = cards_by_suit.get(self.suit)

        # Check if we have cards of trumpf suit.
        if cards_of_trumpf is None:
            return False

        # Check if the Ass is present, but the Nell and Jack are not.
        has_trumpf_ass = any(card.value == 14 for card in cards_of_trumpf)
        has_stronger_than_trumpf_ass = any(card.value in {9, 11} for card in cards_of_trumpf)

        if has_trumpf_ass and not has_stronger_than_trumpf_ass:
            return True
        return False


    def rate_suits_in_hand(self, player_cards: List[Card]) -> Dict[Suit, int]: # TODO: not yet revised.

        score_by_suit: Dict[Suit, int] = {}
        cards_by_suit = split_card_values_by_suit(player_cards)

        for suit, values in cards_by_suit:
            sorted_values_in_suit: List[int] = sorted(values, reverse=True)
            score = 0
            best_remaining_rank = 14

            for value in sorted_values_in_suit:
                if value == best_remaining_rank:
                    best_remaining_rank -= 1
                    score += 30
                elif value >= 10:
                    score += 10
                score += 10 if best_remaining_rank < 12 else 2

            score_by_suit[suit] = score
        return score_by_suit
    

    def toss_and_schmieren(self, available_cards: List[ Card], state: Status, round_color: Suit) -> Card | None:
        """Selects a card to toss and potentially score extra points if the partner is round leader.

        This function chooses a card to discard, prioritizing cards with value 10, when the partner is round leader and either the player is last or the stich is not beatable.

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
                if card.value == 10:
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

        This function determines the weakest suit and selects a card to toss, giving preference to cards with value 10 if the partner is round leader and the stich is not beatable.

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
                if card.value == 10:
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
        is_not_first_player: bool = len(state.table) > 0
        round_color_is_trumpf: bool = round_color == self.suit
        our_only_trumpf_is_jack: bool = self.has_only_jack_of_trumpf(available_cards)
        have_to_serve: bool = self.have_to_serve(eligible_suits, round_color)

        condition = all([is_not_first_player,
                         have_to_serve,
                         any([not round_color_is_trumpf, not our_only_trumpf_is_jack])])
        if condition:
            return self.serve_tossable_card_of_suit(available_cards, state, round_color)

        else:
            return self.serve_tossable_card_of_any_suit(available_cards, state)
        

    def opponents_out_of_turmpf(self, state: Status) -> bool:
        """Checks whether both opponents are out of trumpf cards.

        This function evaluates the suit likelihoods for each opponent to determine if neither is expected to hold any cards of the current trumpf suit.

        Args:
            state (Status): The current game state.

        Returns:
            bool: True if both opponents are out of trumpf, False otherwise.
        """
        opponent_1_no_trumpf: bool = self.card_counter.has_suit_likelihood(self.card_counter.opponent_1_id, self.suit, state) == 0
        opponent_2_no_trumpf: bool = self.card_counter.has_suit_likelihood(self.card_counter.opponent_2_id, self.suit, state) == 0
        return opponent_1_no_trumpf and opponent_2_no_trumpf


    def play_card_to_indicate_no_trumpf(self, available_cards: List[Card]) -> Card | None:
        """Selects a card that signals to the partner that the player has no trumpf cards.

        Geschoben and we have to open the game. We have no cards of the trumpf suit.
        To inform our partner that we have not a single trumpf, we play a high card (Under, Ober, Koenig) of our strongest possible suit.
        Even if we do not have any Under, Ober, or Koenig: We try not to play a Banner and definitely not an Ass, as this would bring our partner in a clinch.

        Args:
            available_cards (List[Card]): The list of cards available to the player.

        Returns:
            Card or None: The card to play to indicate no trumpf, or None if no suitable card is found.
        """
        suit_by_strength: Dict[Suit, int] = dict(sorted(self.rate_suits_in_hand(self.card_counter.get_hand()).items(),key=lambda x: x[1], reverse=True))
        cards_by_suit = dict(split_cards_by_suit(available_cards))
        backup_card: Card | None = None

        # Play Jack, Ober, or Koenig to indicate we have no trumpf.
        # Ideally from best suit, otherwise next best etc.
        for suit in suit_by_strength:
            # we cannot play card of suit we do not have
            cards = cards_by_suit.get(suit)
            if is_empty_or_none(cards):
                continue
            cards_by_rank = self.sort_by_rank(cards)
            if any(card.value in [11,12,13] for card in cards_by_rank):
                return list(filter(lambda card: card.value in [11, 12, 13], cards_by_rank))[-1]
            # Set backup card of a strongest possible suit in case we do not have any Jack, Ober, Koenig.
            for card in reversed(cards_by_rank):
                backup_card_not_yet_set: bool = backup_card is None
                is_banner = card.value == 10
                is_ass = card.value == 14
                condition = backup_card_not_yet_set and not any([is_banner, is_ass])
                if condition:
                    backup_card = card
        return backup_card


    def play_card_to_indicate_only_jack_of_trumpf(self, available_cards: List[Card]) -> Card | None:
        """Selects a card to indicate we have only the jack of trumpf suit.

        Geschoben and we have to open the game. We only have the jack of the trumpf suit.
        To inform our partner that we only have the jack of trumpf suit, we play a low card (6,7,8,9) of our strongest possible suit.
        Even if we do not have any 6,7,8,9: We try not to play a Banner and definitely not an Ass, as this would bring our partner in a clinch.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The card to toss, or None if no suitable card is found.
        """
        suit_by_strength: Dict[Suit, int] = dict(sorted(self.rate_suits_in_hand(self.card_counter.get_hand()).items(),key=lambda x: x[1], reverse=True))
        cards_by_suit = dict(split_cards_by_suit(available_cards))
        backup_card: Card | None = None

        # Play card below Banner to indicate we have only Jack of Trumpf
        # Ideally from best suit, otherwise next best etc.
        for suit in suit_by_strength:
            # only play non-trumpf card.
            if suit == self.suit:
                continue
            # we cannot play card of suit we do not have
            cards = cards_by_suit.get(suit)
            if is_empty_or_none(cards):
                continue
            cards_by_rank = self.sort_by_rank(cards)
            if cards_by_rank[-1].value in [6,7,8,9]:
                return cards_by_rank[-1]
            # Set backup card of a strongest possible suit in case we do not have any 6,7,8,9.
            for card in reversed(cards_by_rank):
                backup_card_not_yet_set: bool = backup_card is None
                is_banner = card.value == 10
                is_ass = card.value == 14
                condition = backup_card_not_yet_set and not any([is_banner, is_ass])
                if condition:
                    backup_card = card
        return backup_card
    

    def start_play_with_two_trumpf_geschoben(self, trumpf_cards: List[Card]) -> Card:
        """Selects the opening card when the player has exactly two trumpf cards after a geschoben.

        This function avoids leading with the trumpf jack in this situation and instead chooses the other trumpf card, or otherwise plays the strongest available trumpf.

        Args:
            trumpf_cards (List[Card]): The list of trumpf cards in the player's hand.

        Returns:
            Card: The selected trumpf card to open the game.
        """
        trumpf_cards = self.sort_by_rank(trumpf_cards)

        if self.has_jack_and_one_trumpf(trumpf_cards):
            # Geschoben, we have two trumpf cards, one of which is the jack.
            # Never play trumpf jack in this situation.
            # https://jassverzeichnis.ch/ausspielen-trumpf-bauer-zu-zweit/
            return list(filter(lambda card: card.value != 11, trumpf_cards))[0]
        
        # Do not start with banner, otherwise partner thinks we have only one or three trumpf cards.
        if trumpf_cards[0].value == 10:
            return self.sort_by_rank(trumpf_cards)[1]
        
        return self.sort_by_rank(trumpf_cards)[0]
    

    def start_play_with_three_trumpf_cards(self, trumpf_cards: List[Card]) -> Card:
        """Selects the opening trumpf card when the player holds exactly three trumpf cards.

        This function prioritizes leading with the strongest signaling trumpf (nell or jack), otherwise playing the banner, or falling back to the best remaining trumpf based on ace presence.

        Args:
            trumpf_cards (List[Card]): The three trumpf cards in the player's hand.

        Returns:
            Card: The selected trumpf card to open the game.
        """
        trumpf_cards = self.sort_by_rank(trumpf_cards)
        # With three trumpf cards, play nell or jack if in hand.
        if any(card.value in {9, 11} for card in trumpf_cards):
            return trumpf_cards[0]

        # otherwise, if we have three cards and one of which is Banner: Play banner.
        if any(card.value == 10 for card in trumpf_cards):
            return list(filter(lambda card: card.value == 10, trumpf_cards))[0]
        
        # otherwise, if we have three cards and the best is ace,
        # play the second strongest trumpf.
        # Source: https://jassverzeichnis.ch/jassen-trumpf-ass-ausspielen/
        if self.has_trumpfass_best_card(trumpf_cards):
            return trumpf_cards[1]
        
        # in any other case, play the best card of trumpf.
        return trumpf_cards[0]
    

    def get_card_to_play_first_player_partnerrole_first_round(self, available_cards: List[Card]) -> Card | None:
        """Determines the opening card to play in the first round when acting as partner.

        This function selects an appropriate trumpf or signaling card based on the exact number and composition of trumpf cards in hand, aiming to communicate trumpf strength or weakness to the partner.

        Args:
            sorted_trumpf_cards (List[Card]): The player's trumpf cards sorted by strength.

        Returns:
            Card or None: The selected opening card, or None if no suitable card can be determined.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        sorted_trumpf_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == self.suit][0])
        have_no_trumpf: bool = not sorted_trumpf_cards
        have_one_trumpf: bool = len(sorted_trumpf_cards) == 1
        have_two_trumpf: bool = len(sorted_trumpf_cards) == 2
        have_three_trumpf: bool = len(sorted_trumpf_cards) == 3
        jack_solo_trumpf: bool = self.has_only_jack_of_trumpf(sorted_trumpf_cards)

        if have_no_trumpf:
            return self.play_card_to_indicate_no_trumpf(available_cards)

        if jack_solo_trumpf:
            return self.play_card_to_indicate_only_jack_of_trumpf(available_cards)
        
        if have_one_trumpf and not jack_solo_trumpf:
            return sorted_trumpf_cards[0]
        
        if have_two_trumpf:
            return self.start_play_with_two_trumpf_geschoben(sorted_trumpf_cards)

        if have_three_trumpf:
            return self.start_play_with_three_trumpf_cards(sorted_trumpf_cards)
        
        # If we have four or more trumpf, or in any other case, we play the strongest trumpf.
        return sorted_trumpf_cards[0]
    

    def get_card_to_play_first_player_partnerrole_second_round(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the opening card to play in the second round when acting as partner.

        This function selects a trumpf or high-value non-trumpf card based on whether opponents still have trumpf cards, aiming to either continue drawing trumpf or secure points once opponents are out of trumpf.

        Args:
            available_cards (List[Card]): The list of cards available to the player.

        Returns:
            Card: The selected card to open the second round in partner role.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        sorted_trumpf_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == self.suit][0])
        non_trumpf_bocks = self.get_non_trumpf_bocks(available_cards)

        # Check if opponents do not have any trumpf cards remaining.
        opponents_out_of_trumpf = self.opponents_out_of_turmpf(state)

        if not opponents_out_of_trumpf and sorted_trumpf_cards:
            return sorted_trumpf_cards[0]
        if len(non_trumpf_bocks) != 0 and opponents_out_of_trumpf:
            return non_trumpf_bocks[0] # TODO: not yet tested
        return self.get_passing_card(cards_by_suit, state) # TODO: is this correct? Check! # TODO: not yet tested


    def get_card_to_play_first_player_partnerrole(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the opening card to play as the first player when acting in the partner role.

        This function chooses a trumpf or non-trumpf card based on the current round, remaining trumpf cards, and whether opponents are out of trumpf, aiming to support and coordinate with the partner.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to open the round in partner role, or None if no suitable card is found.
        """        
        cards_by_suit = split_cards_by_suit(available_cards)
        sorted_trumpf_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == self.suit][0])
        non_trumpf_bocks = self.get_non_trumpf_bocks(available_cards)
        current_round = self.card_counter.current_round()
        opponents_out_of_trumpf = self.opponents_out_of_turmpf(state)
        
        # Get Card to play in the first round.
        if current_round == 0:
            return self.get_card_to_play_first_player_partnerrole_first_round(available_cards)

        # Get Card to play in the second round
        if current_round == 1:
            return self.get_card_to_play_first_player_partnerrole_second_round(available_cards, state)

        # Get Card to play in any other round
        sorted_trumpf_cards = list(filter(lambda card: card.value != 11, sorted_trumpf_cards))
        if sorted_trumpf_cards and not opponents_out_of_trumpf:
            return sorted_trumpf_cards[0]
        elif opponents_out_of_trumpf and len(non_trumpf_bocks) != 0:
            return non_trumpf_bocks[0]
        
        partner_had_stich_previously = self.card_counter.had_stich_previously(self.card_counter.partner_id)
        if partner_had_stich_previously:
            return self.get_passing_card(cards_by_suit, state)
        else:
            return self.get_value_card(cards_by_suit, state)


    def get_card_to_play_first_player_trumpfrole_first_round(self, sorted_trumpf_cards: List[Card]) -> Card | None:
        """Determines the opening trumpf card to play in the first round when in the trumpf role.

        This function selects a trumpf card based on the number and strength of trumpf cards in hand, prioritizing key signaling cards such as jack, nell, and ace to communicate trumpf strength.

        Args:
            sorted_trumpf_cards (List[Card]): The player's trumpf cards sorted by strength.

        Returns:
            Card or None: The selected trumpf card to open the first round, or None if no suitable card is found.
        """
        trumpf_count = len(sorted_trumpf_cards)
        have_jack = any(card.value == 11 for card in sorted_trumpf_cards)
        have_nell = any(card.value == 9 for card in sorted_trumpf_cards)
        have_ace = any(card.value == 14 for card in sorted_trumpf_cards)

        # Jack, Nell and at least four trumpf cards -> play Nell
        if trumpf_count >= 4 and have_jack and have_nell:
            return list(filter(lambda card: card.value == 9, sorted_trumpf_cards))[0]
        
        # Jack, no Nell and at least four trumpf cards -> play Jack
        if trumpf_count >= 4 and have_jack and not have_nell:
            return list(filter(lambda card: card.value == 11, sorted_trumpf_cards))[0]
        
        # Nell and Ace with five cards -> play Nell. Partner has jack or opponent takes, giving us highest Trumpf again.
        if trumpf_count >= 5 and have_nell and have_ace and not have_jack:
            return list(filter(lambda card: card.value == 9, sorted_trumpf_cards))[0]
        
        return sorted_trumpf_cards[0]
    

    def get_card_to_play_first_player_trumpfrole_second_round(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the opening trumpf card to play in the second round when in the trumpf role.

        This function selects between continuing to pull trumpf or playing high-value non-trumpf cards, based on whether opponents still have trumpf and on the cards played in the first round.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to open the second round in trumpf role, or None if no suitable card is found.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        sorted_trumpf_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == self.suit][0])
        opponents_out_of_trumpf = self.opponents_out_of_turmpf(state)

        # first check opponent out of trumpf
        non_trumpf_bocks = self.get_non_trumpf_bocks(available_cards)
        if opponents_out_of_trumpf and non_trumpf_bocks:
            return non_trumpf_bocks[0]

        my_first_played_card: Card = self.card_counter.played_cards[self.card_counter.me.id][0]
        opponent_1_first_card: Card = self.card_counter.played_cards[self.card_counter.opponent_1_id][0]
        opponent_2_first_card: Card = self.card_counter.played_cards[self.card_counter.opponent_2_id][0]

        my_first_card_jack = my_first_played_card.suit == self.suit and my_first_played_card.value == 11
        opponent_1_first_card_nell = opponent_1_first_card.suit == self.suit and opponent_1_first_card.value == 9
        opponent_2_first_card_nell = opponent_2_first_card.suit == self.suit and opponent_2_first_card.value == 9

        if my_first_card_jack and any([opponent_1_first_card_nell, opponent_2_first_card_nell]):
            return sorted_trumpf_cards[0]
        
        have_ace = any(card.value == 14 for card in sorted_trumpf_cards)
        if my_first_card_jack and have_ace and len(sorted_trumpf_cards) >= 2:
            return sorted_trumpf_cards[1]
        
        return sorted_trumpf_cards[0]


    def get_card_to_play_first_player_trumpfrole(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the opening card to play as the first player when in the trumpf role.

        This function selects between various trumpf and non-trumpf options based on the round number, remaining trumpf distribution, and availability of high-value non-trumpf cards.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to open the round in trumpf role, or None if no suitable card is found.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        sorted_trumpf_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == self.suit][0])
        non_trumpf_bocks = self.get_non_trumpf_bocks(available_cards)
        current_round = self.card_counter.current_round()
        opponents_out_of_trumpf = self.opponents_out_of_turmpf(state)

        # Get Card to play in the first round.
        if current_round == 0:
            return self.get_card_to_play_first_player_trumpfrole_first_round(sorted_trumpf_cards)
        
        if current_round == 1:
            return self.get_card_to_play_first_player_trumpfrole_second_round(available_cards, state)

        # Pull opponents Trumpfs 
        pulling_trumpfs = len(sorted_trumpf_cards) > 0 and not opponents_out_of_trumpf
        if pulling_trumpfs:
            return sorted_trumpf_cards[0]
        
        # Opponents out of trumpf -> we play bocks.
        if opponents_out_of_trumpf and non_trumpf_bocks:
            return non_trumpf_bocks[0]
        
        if opponents_out_of_trumpf and not non_trumpf_bocks:
            return self.get_value_card(cards_by_suit, state)

        # TODO: Everything below was kept from strategy player. Improvement required.
        if not opponents_out_of_trumpf and len(sorted_trumpf_cards) == 0:
            return self.get_tossable_card(available_cards, state) # TODO: This is definitely wrong! Anziehen, NICHT verwerfen. But what do we play?

        # We still have trumpf, opponents no trumpf, we have no bock cards.
        if not self.card_counter.had_stich_previously(self.card_counter.partner_id):
            return self.get_passing_card(cards_by_suit, state)
        else:
            return self.get_value_card(cards_by_suit, state)


    def get_card_to_play_first_player_no_role(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the opening card to play as the first player when having no specific role.

        This function selects between pulling trumpf, playing high-value non-trumpf cards, or discarding weaker cards based on the current trumpf distribution and opponents' remaining trumpf cards.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to open the round with no specific role, or None if no suitable card is found.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        sorted_trumpf_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == self.suit][0])
        non_trumpf_bocks = self.get_non_trumpf_bocks(available_cards)
        opponents_out_of_trumpf = self.opponents_out_of_turmpf(state)

        # Pull Trumpfs if we have good Bock Cards.
        # TODO: Find a good definition for having good bock cards. here, just given if we have bock.
        pulling_trumpfs = len(sorted_trumpf_cards) > 0 and non_trumpf_bocks and not opponents_out_of_trumpf
        if pulling_trumpfs:
            return sorted_trumpf_cards[0]
        
        if opponents_out_of_trumpf and non_trumpf_bocks:
            return non_trumpf_bocks[0]

        # TODO: Everything below was kept from strategy player. Improvement required.
        if not opponents_out_of_trumpf and len(sorted_trumpf_cards) == 0:
            return self.get_tossable_card(available_cards, state) # TODO: This is definitely wrong! Anziehen, NICHT verwerfen. But what do we play?

        # We still have trumpf, opponents no trumpf, we have no bock cards.
        if not self.card_counter.had_stich_previously(self.card_counter.partner_id):
            return self.get_passing_card(cards_by_suit, state)
        else:
            return self.get_value_card(cards_by_suit, state)


    def get_card_to_play_first_player(self, available_cards: List[Card], state: Status, role: str) -> Card | None:
        """Determines the opening card to play based on the player's role.

        This function delegates the decision to specialized role-based strategies for trumpf, partner, or off roles, and validates that the provided role is supported.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.
            role (str): The role of the player, one of 'Trumpf', 'Partner', or 'Off'.

        Returns:
            Card or None: The selected card to open the round, or None if no suitable card is found.

        Raises:
            ValueError: If the provided role is not one of the supported values.
        """
        if role == 'Trumpf':
            return self.get_card_to_play_first_player_trumpfrole(available_cards, state)
        
        if role == 'Partner':
            return self.get_card_to_play_first_player_partnerrole(available_cards, state)

        if role == 'Off':
            return self.get_card_to_play_first_player_no_role(available_cards, state)
        
        raise ValueError(f'Role is expected to be Trumpf, Partner, or Off. However, {role=}.')


    def get_card_to_play_second_player(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the card to play when acting as the second player in a round.

        This function attempts to win the stich with an appropriate card if possible, otherwise it selects a suitable card to toss.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play as second player, or None if no suitable card can be found.
        """
        ueberzug_card = self.ueberzug(available_cards, state)
        if ueberzug_card is not None:
            return ueberzug_card
        cards_by_suit = split_cards_by_suit(available_cards)
        stich_card = self.get_stich_card(cards_by_suit, state)
        if stich_card is None:
            return self.get_tossable_card(available_cards, state)
        return stich_card
    

    def get_card_to_play_third_player_trumpfrole(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the card to play as the third player when in the trumpf role.

        This function decides whether to attempt winning the stich with a suitable trumpf or non-trumpf card, or instead discard a card when taking the stich is not desired or not possible.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play as third player in trumpf role, or None if no suitable card can be found.
        """
        ueberzug_card = self.ueberzug(available_cards, state)
        if ueberzug_card is not None:
            return ueberzug_card

        cards_by_suit = split_cards_by_suit(available_cards)
        # TODO: Everything below was kept from strategy player. Improvement required.
        if self.card_counter.had_stich_previously(self.card_counter.me.id):
            if self.want_stich(cards_by_suit, state):
                return self.get_stich_card(cards_by_suit, state)
            else:
                return self.get_tossable_card(available_cards, state)

        card = self.get_stich_card(cards_by_suit, state)
        if card is not None:
            return card
        else:
            return self.get_tossable_card(available_cards, state)          


    def get_card_to_play_third_player_partnerrole(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the card to play as the third player when acting in the partner role.

        This function balances preserving strong trumpf, supporting the partner's winning position, and using tactical overtrump or discard plays to optimize the team's overall stich outcome.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play as third player in partner role, or None if no suitable card can be found.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        sorted_trumpf_cards = self.sort_by_rank([x[1] for x in cards_by_suit if x[0] == self.suit][0])
        round_color = self.card_counter.get_round_color(state)

        current_round = self.card_counter.current_round()
        first_round: bool = current_round == 0
        partner_card = self.card_counter.current_stich[self.card_counter.partner_id]
        opponent_card = self.card_counter.current_stich[self.card_counter.opponent_2_id]
        opponent_card_trumpf_jack = opponent_card.suit == self.suit and opponent_card.value == 11
        have_nell = any(card.value == 9 for card in sorted_trumpf_cards)
        have_jack = any(card.value == 11 for card in sorted_trumpf_cards)

        # if two trumpfs and one is nell, do not play nell on partners trumpf jack.
        condition = all([round_color == self.suit,
                            partner_card.value == 11,
                            have_nell,
                            len(sorted_trumpf_cards) == 2
                            ])
        if condition:
            return sorted_trumpf_cards[1]
        
        # Does not follow the rules, but we do not waste strong trumpf on lost stich.
        if opponent_card_trumpf_jack and round_color == self.suit and sorted_trumpf_cards:
            return sorted_trumpf_cards[-1]

        # Partner has stich with nell. We do not waste Jack. Play second best trumpf instead.
        condition = all([first_round,
                         partner_card.value == 9,
                         have_jack,
                         len(sorted_trumpf_cards) > 1
                         ])
        if condition:
            return sorted_trumpf_cards[1]

        # Partner has stich with nell. We do not waste Jack. Toss suit instead.
        condition = all([first_round,
                         partner_card.value == 9,
                         have_jack,
                         len(sorted_trumpf_cards) == 1
                         ])
        if condition:
            return self.toss_and_schmieren(available_cards, state, self.suit)

        # Play strongest trumpf.
        elif round_color == self.suit and sorted_trumpf_cards:
            return sorted_trumpf_cards[0]

        # Check Ueberzug possible
        ueberzug_card = self.ueberzug(available_cards, state)
        if ueberzug_card is not None:
            return ueberzug_card

        # Check Unterzug possible
        unterzug_card = self.unterzug(state)
        if unterzug_card is not None:
            return unterzug_card

        # Check if we want the stich and act accordingly.
        if self.want_stich(cards_by_suit, state):
            stich_card = self.get_stich_card(cards_by_suit, state)
            if stich_card is not None:
                return stich_card

        # Toss away useless cards.
        return self.get_tossable_card(available_cards, state)


    def get_card_to_play_third_player_no_role(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the card to play as the third player when having no specific role.

        This function decides whether to attempt winning the stich or discard a less valuable card, based on the current table situation and the player's desire to take the stich.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play as third player with no specific role, or None if no suitable card can be found.
        """
        # Check Ueberzug possible
        ueberzug_card = self.ueberzug(available_cards, state)
        if ueberzug_card is not None:
            return ueberzug_card

        cards_by_suit = split_cards_by_suit(available_cards)
        if self.want_stich(cards_by_suit, state):
            stich_card = self.get_stich_card(cards_by_suit, state)
            if stich_card is not None:
                return stich_card
            return self.get_tossable_card(available_cards, state)


    def get_card_to_play_third_player(self, available_cards: List[Card], state: Status, role: str) -> Card | None:
        """Determines the card to play as the third player based on the current role.

        This function delegates the decision to the corresponding role-specific strategy for trumpf, partner, or off roles, and validates that the provided role is supported.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.
            role (str): The role of the player, one of 'Trumpf', 'Partner', or 'Off'.

        Returns:
            Card or None: The selected card to play as third player, or None if no suitable card can be found.

        Raises:
            ValueError: If the provided role is not one of the supported values.
        """
        if role == 'Trumpf':
            return self.get_card_to_play_third_player_trumpfrole(available_cards, state)

        elif role == 'Off':
            return self.get_card_to_play_third_player_no_role(available_cards, state)

        elif role == 'Partner':
            return self.get_card_to_play_third_player_partnerrole(available_cards, state)
        
        raise ValueError(f'Role is expected to be Trumpf, Partner, or Off. However, {role=}.')
 

    def get_card_to_play_fourth_player(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the card to play when acting as the fourth (last) player in a round.

        This function decides whether to secure the stich with a winning card or to discard a less valuable card when winning the stich is not desired or possible.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play as fourth player, or None if no suitable card can be found.
        """
        # Check Ueberzug possible
        ueberzug_card = self.ueberzug(available_cards, state)
        if ueberzug_card is not None:
            return ueberzug_card

        cards_by_suit = split_cards_by_suit(available_cards)
        if self.want_stich(cards_by_suit, state):
            stich_card = self.get_stich_card(cards_by_suit, state)
            if stich_card is not None:
                return stich_card
        return self.get_tossable_card(available_cards, state)


    def get_card_to_play(self, available_cards: List[Card], state: Status, role: str) -> Card | None:
        """Determines the card to play based on the player's table position and role.

        This function routes the decision to the appropriate position- and role-specific strategy method, ensuring that only valid table positions are accepted.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.
            role (str): The role of the player, one of 'Trumpf', 'Partner', or 'Off'.

        Returns:
            Card or None: The selected card to play for the current position and role, or None if no suitable card can be found.

        Raises:
            ValueError: If the inferred table position is not between 0 and 3.
        """
        current_position = len(state.table)

        # We start round
        if current_position == 0:
            return self.get_card_to_play_first_player(available_cards, state, role)

        # Opponent started round
        if current_position == 1:
            return self.get_card_to_play_second_player(available_cards, state)

        # Partner started round
        if current_position == 2:
            return self.get_card_to_play_third_player(available_cards, state, role)
            
        # We are the last player to play this round
        if current_position == 3:
            return self.get_card_to_play_fourth_player(available_cards, state)
        
        raise ValueError(f'Position is expected to be 0-3. However, {current_position=}.')


    def unterzug(self, state: Status):# TODO: Implement!
        return None
   

    def ueberzug(self, available_cards: List[Card], state: Status) -> Card | None: # TODO: Test
        """Determines whether a trumpf overtrump ('Ueberzug') play is possible and selects the card to use.

        This function checks positional, suit, and card-distribution constraints to decide if an overtrump maneuver is valid and returns an appropriate trumpf card when the conditions are met.

        Args:
            available_cards (List[Card]): The list of cards currently available to the player.
            state (Status): The current game state, including the current table and card history.

        Returns:
            Card or None: The selected trumpf card for the overtrump play, or None if no valid overtrump is possible.
        """
        # We cannot open a round with Ueberzug. There must be already cards on the table.
        current_position = len(state.table)
        if current_position == 0:
            return None

        # Round color must not be of trumpf suit.
        round_color = self.card_counter.get_round_color(state)
        if round_color == self.suit:
            return None
        
        # check if hand of self contains bock and 3rd bock of current suit.
        cards_by_suit = split_cards_by_suit(available_cards)
        cards_of_interest = self.card_counter.filter_suit_cards_from_tuple(cards_by_suit, round_color)
        cards_remaining = self.card_counter.remaining_cards(self.card_counter.cards_played())
        cards_remaining_in_suit = self.sort_by_rank([x for x in cards_remaining if x.suit == round_color])

        # Must have at least two cards.
        if len(cards_remaining_in_suit) < 2:
            return None
        
        # Must have Trumpf, no opponent has trumpf
        opponents_no_trumpf = self.opponents_out_of_turmpf(state)
        trumpf_cards = self.card_counter.filter_suit_cards_from_tuple(cards_by_suit, self.suit)
        have_trumpf = len(trumpf_cards) > 0
        if not (have_trumpf and opponents_no_trumpf):
            return None

        # check if hand of self contains bock and 3rd bock of current suit.
        have_strongest_card = cards_remaining_in_suit[0] in cards_of_interest # We must have strongest card.
        have_second_strongest_card = cards_remaining_in_suit[1] in cards_of_interest # We must not have second strongest card, because else Ueberzug does not make sense.
        if not have_strongest_card or have_second_strongest_card:
            return None

        return trumpf_cards[0]
        

    def partner_has_only_trumpf_bauer_flag(self) -> None:
        """Adds flags indicating the partner has only the trumpf Bauer card.

        This function updates flags to reflect that the partner holds only the trumpf Bauer, and other trumpf cards are held by opponents.

        Returns:
            None
        """
        trumpf_cards: List[Card] | None = None
        # Partner plays non-trumpf low card. Has only Trumpf Bauer.
        for suit_cards in split_cards_by_suit(self.card_counter.unknown_cards()):
            if suit_cards[0].name == self.trumpf_name().name:
                trumpf_cards = suit_cards[1]
        assert trumpf_cards is not None
        for trumpf_card in trumpf_cards:
            if trumpf_card.value != 11:
                self.add_flag(DoesntHaveCardFlag(trumpf_card), self.card_counter.partner_id)
            else:
                self.add_flag(DoesntHaveCardFlag(trumpf_card), self.card_counter.opponent_1_id)
                self.add_flag(DoesntHaveCardFlag(trumpf_card), self.card_counter.opponent_2_id)
        return None


    def partner_has_no_trumpf_cards_flag(self) -> None:
        """Adds flags indicating the partner has no trumpf cards.

        This function updates the partner's flags to reflect that they do not possess any trumpf cards, marking each trumpf card as not held and the trumpf suit as discarded.

        Returns:
            None
        """
        for suit_cards in split_cards_by_suit(self.card_counter.unknown_cards()):
            if suit_cards[0].name == self.trumpf_name().name:
                for trumpf_card in suit_cards[1]:
                    self.add_flag(DoesntHaveCardFlag(trumpf_card), self.card_counter.partner_id)
        self.add_flag(FailedToServeSuitFlag(self.suit), self.card_counter.partner_id)
        return None


    def partner_non_trumpf_opening(self, card: Card) -> None:
        """Updates flags when the partner opens with a non-trumpf card.

        This function determines whether the partner has only the trumpf Bauer or no trumpf cards at all, based on the value of the card played.

        Args:
            card (Card): The card played by the partner.

        Returns:
            None
        """
        if card.value < 10:
            self.partner_has_only_trumpf_bauer_flag()

        if card.value >= 10:
            self.partner_has_no_trumpf_cards_flag()
        return None


    def update_partner_vorhand_flag(self, card: Card) -> None:
        """Updates flags based on the partner's opening play when they made trumpf (vorhand).

        This function infers the partner's trumpf strength and likely holdings when they open with specific trumpf cards, and propagates flags to restrict which players can still hold key trumpf cards.

        Args:
            card (Card): The card played by the partner when opening the game as trumpf maker.

        Returns:
            None
        """      
        card_is_trumpf: bool = self.is_trumpfcard(card)
        nell: bool = card.value == 9
        jack: bool = card.value == 11
        remaining_trumpf = self.card_counter.remaining_by_suit(self.suit)

        if card_is_trumpf and nell:
            # Has either Jack + Nell with at least two more trumpf, or nell and Ace with at least three more trumpf.
            self.add_flag(NumberOfTrumpfFlag(max=len(remaining_trumpf), min=4), self.card_counter.partner_id)
            self.add_flag(DoesntHaveCardFlag(Card(self.suit, 11)), self.card_counter.opponent_1_id) # 99 Percent sure. Good enough.
            self.add_flag(DoesntHaveCardFlag(Card(self.suit, 11)), self.card_counter.opponent_2_id) # 99 Percent sure. Good enough.
        
        if card_is_trumpf and jack:
            # Partner would have opened with nell if he had jack and nell of trumpf.
            self.add_flag(NumberOfTrumpfFlag(max=len(remaining_trumpf), min=4), self.card_counter.partner_id)
            self.add_flag(DoesntHaveCardFlag(Card(self.suit, 9)),self.card_counter.partner_id)
        return None


    def update_partner_geschoben_flag(self, card: Card) -> None:
        """Updates flags based on the partner's opening play when the game was geschoben.

        This function infers the partner's trumpf count and possible trumpf holdings from specific opening cards, and updates flags when the partner instead opens with a non-trumpf card.

        Args:
            card (Card): The card played by the partner when opening after geschoben.
            state (Status): The current game state (currently unused but reserved for future logic).

        Returns:
            None
        """
        card_is_trumpf: bool = self.is_trumpfcard(card)

        # Geschoben, and partner opens with Trumpf Banner: 
        # Has either only Banner or exactly three trumpf cards.
        card_is_banner = card.value == 10
        if card_is_trumpf and card_is_banner:
            self.add_flag(NumberOfTrumpfFlag(max=3, min=1), self.card_counter.partner_id)
            return None
        
        # Geschoben, Partner opens with trumpf jack. Has three trumpf. (Technically more, but then he would have made trumpf himself.)
        card_is_jack = card.value == 11
        if card_is_trumpf and card_is_jack:
            remaining_trumpf = self.card_counter.remaining_by_suit(self.suit)
            self.add_flag(NumberOfTrumpfFlag(max=len(remaining_trumpf), min=3), self.card_counter.partner_id)
            return None
        
        if card_is_trumpf:
            for stronger_card in self.stronger_cards_remaining(card):
            #     Ass zu dritt: Zweithöchste Karte spielen!
            #     Ass zu viert: Ass spielen!
            #     https://jassverzeichnis.ch/jassen-trumpf-ass-ausspielen/
                if stronger_card.value not in [11, 14]:
                    self.add_flag(DoesntHaveCardFlag(stronger_card), self.card_counter.partner_id)
            return None

        # Partner opens with non-bock and non-trumpf card
        if not card_is_trumpf:
            self.partner_non_trumpf_opening(card)
        return None


    def update_partner_first_player_first_round_flag(self, card: Card, state: Status) -> None:
        """Updates partner-related flags for the first round when the partner opens the stich.

        This function evaluates whether the game was geschoben and which card the partner used to open, and delegates to the corresponding helper to infer the partner's trumpf strength and distribution.

        Args:
            card (Card): The card played by the partner as the opening card of the first round.
            state (Status): The current game state providing geschoben status and player order.

        Returns:
            None
        """
        if state.geschoben:
            self.update_partner_geschoben_flag(card)
        else:
            self.update_partner_vorhand_flag(card)

        return None


    def update_partner_first_player_flag(self, card: Card, state: Status) -> None:
        """Updates inference flags based on the partner's opening play in later rounds.

        This function distinguishes between the first round and subsequent rounds, delegating early-round logic and, in later rounds, inferring opponents' trumpf holdings when the partner opens with specific non-trumpf bock cards.

        Args:
            card (Card): The card played by the partner when opening the stich.
            state (Status): The current game state used to determine round number and leader.

        Returns:
            None
        """
        # First round
        is_first_round: bool = self.card_counter.current_round() == 0
        if is_first_round:
            self.update_partner_first_player_first_round_flag(card, state)
            return None
        
        # Everything below is NOT the first round.
        # Partner opens with non-trumpf bock. We expect opponents to have no Trumpf cards left.
        partner_is_leader: bool = self.card_counter.round_leader(state) == self.card_counter.partner_id
        card_is_trumpf: bool = self.is_trumpfcard(card)
        card_is_bock: bool = card == self.get_current_bock(card.suit)
        condition = all([partner_is_leader,
                         card_is_bock,
                         not card_is_trumpf
        ]) 
        if condition:
            cards_by_suit = split_cards_by_suit(self.card_counter.unknown_cards())
            suit_cards = flatten_matrix([x[1] for x in cards_by_suit if x[0].name == self.trumpf_name().name])
            for trumpf_card in suit_cards:
                self.add_flag(DoesntHaveCardFlag(trumpf_card), self.card_counter.opponent_1_id)
                self.add_flag(DoesntHaveCardFlag(trumpf_card), self.card_counter.opponent_2_id)
        return None
    

    def update_first_player_flags(self,player_id: int, card: Card, state: Status) -> None:

        # Add Suit "anziehen" Flag if a non-trumpf card is played.
        if not self.player_played_trumpf(player_id):
            self.add_flag(SuitAngezogenFlag(card.suit), player_id)

        # Partner is first player. Update his flags.
        if player_id == self.card_counter.partner_id:
            self.update_partner_first_player_flag(card, state)
        
        return None
    

    def check_banner_hint(self, state: Status) -> bool:
        """Checks whether the banner-based trumpf count hint condition is met.

        This function verifies if the game was geschoben and the partner opened the first stich with the trumpf banner, which implies the partner has either only the banner or exactly three trumpf cards.

        Args:
            state (Status): The current game state containing stiche and geschoben status.

        Returns:
            bool: True if the banner hint condition is fulfilled, otherwise False.
        """
        first_card = from_string_to_card(state.stiche[0].played_cards[0].card)
        partner_played_first_card = state.stiche[0].played_cards[0].player_id == self.card_counter.partner_id
        card_is_trumpf = first_card.suit == self.suit
        card_is_banner = first_card.value == 10
        is_geschoben = state.geschoben
        return all(
            [
                is_geschoben,
                card_is_trumpf,
                card_is_banner,
                partner_played_first_card,
            ]
        )


    def update_number_of_trumpf_flag(self, card: Card, state: Status) -> None:
        """Updates the inferred range of trumpf cards held by the partner.

        This function adjusts the partner's minimum and maximum possible trumpf count based on the current play, and sets flags when all remaining trumpf cards are localized to specific opponents.

        Args:
            card (Card): The card just played by the partner.
            state (Status): The current game state providing round color and history.

        Returns:
            None
        """
        # Get Flag
        number_of_trumpf = self.card_counter.get_number_of_trumpf_flag(self.card_counter.partner_id)
        if is_empty_or_none(number_of_trumpf):
            return None
        assert isinstance(number_of_trumpf, NumberOfTrumpfFlag)

        round_color = self.card_counter.get_round_color(state)

        # Update for banner
        # If second round was trumpf again and partner did not play trumpf: had only one trumpf.
        # If second round was trumpf again and partner did not play trumpf: has exactly three trumpf.
        if self.check_banner_hint(state):
            trumpf_round = round_color == self.suit
            card_is_trumpf = card.suit == self.suit
            if trumpf_round and not card_is_trumpf:
                number_of_trumpf.max = number_of_trumpf.min
            
            if trumpf_round and card_is_trumpf:
                number_of_trumpf.min = number_of_trumpf.max

        # update flag
        if card.suit == self.suit:
            number_of_trumpf.max = max(number_of_trumpf.max-1, 0)
            number_of_trumpf.min = max(number_of_trumpf.min-1, 0)
        
        if round_color == self.suit and card.suit != self.suit:
            number_of_trumpf.max = 0
            number_of_trumpf.min = 0

        return None
        

    def update_non_first_player_flags(self, player_id: int, card: Card, state: Status) -> None:
        """Updates inference flags for non-leading players based on the card they played.

        This function marks when a player both fails to follow the round color and does not play trumpf, and for the partner additionally updates the inferred trumpf count based on their play.

        Args:
            player_id (int): The ID of the player who played the card.
            card (Card): The card that was played by the player.
            state (Status): The current game state.

        Returns:
            None
        """
        did_not_play_trumpf: bool = card.suit != self.suit
        round_color = self.card_counter.get_round_color(state)
        did_not_serve_suit: bool = round_color != card.suit

        if round_color is None:
            raise ValueError # Round color should not be none, since there are already cards on the table!

        if did_not_play_trumpf and did_not_serve_suit:
            self.add_flag(FailedToServeSuitFlag(round_color), player_id)
            self.add_flag(SuitVerworfenFlag(card.suit), player_id)
        
        if player_id == self.card_counter.partner_id:
            self.update_number_of_trumpf_flag(card, state)

        return None
    

    def update_trumpf_distribution_estimation(self) -> None:
        """Refines the estimated distribution of remaining trumpf cards among opponents.

        This function uses the partner's inferred trumpf count and the remaining unseen trumpf cards to determine when all remaining trumpf must belong to the partner, and updates flags to reflect that opponents cannot hold those cards.

        Returns:
            None
        """
        partner_id = self.card_counter.partner_id
        opponent_1_id = self.card_counter.opponent_1_id
        opponent_2_id = self.card_counter.opponent_2_id

        partner_number_of_trumpfs_flag = self.card_counter.get_number_of_trumpf_flag(partner_id)
        if is_empty_or_none(partner_number_of_trumpfs_flag):
            return None
        
        remaining_trumpf = self.card_counter.remaining_by_suit(self.suit)
        if len(remaining_trumpf) == partner_number_of_trumpfs_flag.min:
            for trumpf_card in remaining_trumpf:
                self.add_flag(DoesntHaveCardFlag(trumpf_card), opponent_1_id)
                self.add_flag(DoesntHaveCardFlag(trumpf_card), opponent_2_id)
        return None


    def update_flags(self, player_id: int, card: Card, state: Status) -> None:
        """Updates player flags based on the card played and the current game state.

        This function analyzes the card played and the current stich to update flags such as failed to serve suit or suit discarded, reflecting the player's actions and possible hand composition.

        Args:
            player_id (int): The ID of the player who played the card.
            card (Card): The card that was played.
            state (Status): The current game state.

        Returns:
            None
        """
        current_stich_length = len(self.card_counter.current_stich)

        if current_stich_length == 1:
            self.update_first_player_flags(player_id, card, state)

        elif current_stich_length > 1:
            self.update_non_first_player_flags(player_id, card, state)

        if current_stich_length == 4:
            self.update_flags_end_of_round(player_id, state)
        
        self.update_trumpf_distribution_estimation()