from __future__ import annotations
#########################################
##               LIBRARY               ##
#########################################

# Dependencies
from pyschieber.player.treePlayer.strategy.mode.mode import Mode
from pyschieber.helpers.game_helper import split_cards_by_suit
from pyschieber.trumpf import Trumpf
from pyschieber.player.treePlayer.strategy.flags.flags import DoesntHaveCardFlag, PreviouslyHadStichFlag, FailedToServeSuitFlag, SuitAngezogenFlag, SuitVerworfenFlag
from pyschieber.card import from_string_to_card
from pyschieber.player.treePlayer.helpers.helperfunctions import flatten_matrix
from copy import deepcopy

# Type Annotation
from typing import Dict, List, Tuple, TYPE_CHECKING
from pyschieber.card import Card
from pyschieber.suit import Suit
from pyschieber.player.treePlayer.helpers.state_dict_to_dataclass import Status
from pyschieber.player.treePlayer.strategy.card_counter import CardCounter


class UncoloredTrumpf(Mode):
    
    def __init__(self, card_counter: CardCounter) -> None:
        self.card_counter = card_counter


    def sort_by_rank(self, cards: List[Card]) -> List[Card]:
        raise NotImplementedError
    

    def get_stich_card(self, cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> Card | None:
        raise NotImplementedError

    
    def get_tossable_card(self, available_cards: List[Card], state: Status) -> Card | None:
        raise NotImplementedError


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



    def get_passing_card(self, cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> Card | None:
        """Selects a card to pass to the partner based on suit strength and known information.

        This function chooses a card to play that benefits the partner, preferring suits where the partner has the strongest card or opponents have none, otherwise selecting the best suit for the partner.

        Args:
            cards_by_suit (List[Tuple[Suit, List[Card]]]): The available cards grouped by suit.
            state (Status): The current game state.

        Returns:
            Card: The card to pass to the partner, or None if no suitable card is found.
            None: If no card was found.
        """
        # Get a suit where we know partner has bock or where we know opponent has no cards left.
        for suit_cards in cards_by_suit:
            suit = suit_cards[0]
            cards = suit_cards[1]
            if not cards:
                continue
            current_bock = self.get_current_bock(suit)
            if current_bock is None:
                continue
            partner_has_bock: bool = self.card_counter.has_card_likelihood(self.card_counter.partner_id, current_bock, state) == 1
            opponents_no_card_of_suit: bool = self.card_counter.has_suit_likelihood(self.card_counter.opponent_1_id, suit, state) == 0 and self.card_counter.has_suit_likelihood(self.card_counter.opponent_2_id, suit, state) == 0
            if partner_has_bock and opponents_no_card_of_suit:
                return self.sort_by_rank(cards)[-1]

        # Play best suit for partner
        partner_suits_by_strength = self.card_counter.get_suits_by_strength(self.card_counter.partner_id)
        for suit in partner_suits_by_strength:
            if cards := self.card_counter.filter_suit_cards_from_tuple(cards_by_suit, suit):
                return self.sort_by_rank(cards)[-1]
        return None


    def get_suit_to_toss(self, available_cards: List[Card], state: Status) -> Suit | None:
        """Determines which suit to toss based on the current hand and game state.

        This function selects a suit to discard, preferring suits already tossed, or otherwise the suit with the highest minimum bock distance.

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

        bd_suits: List[Tuple[Suit, int]] = []
        for suit, suit_cards in cards_by_suit:
            if suit not in tossed_suits:
                bock_distances: List[int] = []
                bock_distances.extend(self.bock_distance(card, state) for card in suit_cards)
                if bock_distances:
                    bd_suits.append((suit, min(bock_distances)))
                else:
                    bd_suits.append((suit, 0))

        return max(bd_suits,key=lambda item:item[1])[0] if bd_suits else None


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
        handcards_by_suit = split_cards_by_suit(handcards)
        for suit, suit_cards in handcards_by_suit:
            sorted_cards = self.sort_by_rank(suit_cards)
            remaining = remaining_cards_by_suit.get(suit)
            remaining_sorted = self.sort_by_rank(remaining)
            for n, card in enumerate(sorted_cards):
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


    def want_stich(self, my_cards_by_suit: List[Tuple[Suit, List[Card]]], state: Status) -> bool:
        """Determines whether the player should attempt to win the current stich.

        This function evaluates the player's hand, the game state, and the likelihood of opponents holding key cards to decide if going for the stich is advantageous.

        Args:
            my_cards_by_suit (List[Tuple[Suit, List[Card]]]): The player's cards grouped by suit.
            state (Status): The current game state.

        Returns:
            bool: True if the player should attempt to win the stich, False otherwise.
        """
        if self.can_make_all_stich(my_cards_by_suit, state):
            return True
        if self.should_win_stich_last_player(my_cards_by_suit, state):
            return True
        if self.should_win_stich_not_last_player(my_cards_by_suit, state):
            return True
        return self.should_win_stich_partner_not_leader(state)


    def unterzug(self, state: Status) -> Card | None:
        """Determines if an 'Unterzug' (special play) is possible and returns the card to play if so.

        This function checks a series of conditions related to the game state, partner's performance, and the player's hand to decide if an Unterzug can be performed, and returns the appropriate card if possible.

        Args:
            state (Status): The current game state.

        Returns:
            Card or None: The card to play for Unterzug, or None if Unterzug is not possible.
        """
        # Source: https://jassverzeichnis.ch/jassen-in-zahlen-richtiger-unterzug/
   
        round_color = self.card_counter.get_round_color(state)

        # check if Partner won at least four rounds and we can make Matsch. Also, we need at least 2 remaining rounds for a proper unterzug.
        if (
            self.card_counter.current_round() < 4
            or self.card_counter.current_round() > 8
        ):
            return None

        # Match must be possible. Only partner must have had a stich.
        opponent_1_had_stich = self.card_counter.get_had_stich_flags(self.card_counter.opponent_1_id)
        opponent_2_had_stich = self.card_counter.get_had_stich_flags(self.card_counter.opponent_2_id)
        i_had_stich = self.card_counter.get_had_stich_flags(self.card_counter.me.id)

        if opponent_1_had_stich or opponent_2_had_stich or i_had_stich:
            return None
        
        # check if opponent after us had Verworfen the suit on table.
        verworfen_flag = self.card_counter.get_tossed_suits_flags(self.card_counter.opponent_1_id)
        failed_to_serve_flag = self.card_counter.get_failed_to_serve_suits_flags(self.card_counter.opponent_1_id)
        if round_color not in verworfen_flag[:2] or round_color not in failed_to_serve_flag:
            return None

        # check if hand of self contains bock and 3rd bock of current suit.
        my_cards_by_suit = split_cards_by_suit(self.card_counter.get_hand())
        cards_of_interest = self.card_counter.filter_suit_cards_from_tuple(my_cards_by_suit, round_color)
        cards_remaining = self.card_counter.remaining_cards(self.card_counter.cards_played())
        cards_remaining_in_suit = self.sort_by_rank([x for x in cards_remaining if x.suit == round_color])

        # Must have at least two cards.
        if len(cards_remaining_in_suit) < 2:
            return None

        have_strongest_card = cards_remaining_in_suit[0] in cards_of_interest # We must have strongest card.
        have_second_strongest_card = cards_remaining_in_suit[1] in cards_of_interest # We must not have second strongest card, because else Unterzug does not make sense.
        if not have_strongest_card or have_second_strongest_card:
            return None

        if self.card_counter.current_round() < 7:
            remaining_rounds = max(3,9-self.card_counter.current_round())
            if remaining_rounds > len(cards_remaining_in_suit):
                return None
            for n in range(2,remaining_rounds): # Must have all remaining Bocks for Match.
                if cards_remaining_in_suit[n] not in cards_of_interest:
                    return None

        # return card to play
        return self.sort_by_rank([x[1] for x in my_cards_by_suit if x[0] == round_color][0])[1]


    def rate_initial_suit_strength(self, cards_of_same_suit: List[Card]) -> int:
        """Calculates the initial strength score for a suit based on the player's cards.

        This function evaluates the cards of a given suit and assigns a score based on their rank, rewarding consecutive high ranks and high cards.

        Args:
            cards_of_same_suit (List[Card]): The list of cards of the same suit.

        Returns:
            int: The calculated strength score for the suit.
        """
        raise NotImplementedError


    def are_missing_second_strongest_card(self, available_cards: List[Card]) -> Card | None:
        """Finds a suit where the player has the strongest and third strongest cards but is missing the second strongest.

        This function searches through the available cards to identify the strongest suit where the player holds the first and third strongest cards, but not the second, and returns the strongest card of that suit if found.

        Args:
            available_cards (List[Card]): The list of cards available to the player.

        Returns:
            Card or None: The strongest card of the identified suit, or None if no such suit is found.
        """
        candidates: dict[Card, int] = {}
        for suit, suit_cards in sorted(split_cards_by_suit(available_cards),key=len, reverse=True):
            suit_sorted = self.sort_by_rank(suit_cards)
            # Check if we have sufficient cards of suit. # TODO: tweak value. Min. number of cards required is chosen with educated guess.
            if len(suit_sorted) < 3:
                continue
            # Check if we have first and third strongest cards of suit in hand.
            is_bock = self.is_bock(suit_sorted[0])
            is_third_bock = self.is_nth_nut(2, suit_sorted[1])
            if is_bock and is_third_bock:
                candidates[suit_sorted[0]] = len(suit_sorted)

        return max(candidates, key=candidates.get) if candidates else None


    def evaluate_suit_strengths(self, available_cards) -> Dict[Suit, int]:
        """Evaluates and ranks the strength of each suit in the available cards.

        This function calculates a strength score for each suit based on the player's cards and returns a dictionary of suits sorted by strength in descending order.

        Args:
            available_cards (List[Card]): The list of cards available to the player.

        Returns:
            Dict[Suit, int]: A dictionary mapping each suit to its calculated strength score, sorted by strength descending.
        """
        # Get strongest card of each suit as a dictionary key and score this card by suit strength.
        strength_of_suits: Dict[Suit, int] = {}
        cards_by_suit = split_cards_by_suit(available_cards)
        for suit, suit_cards in cards_by_suit:
            strength_of_suits[suit] = self.rate_initial_suit_strength(suit_cards)

        # Sort the dictionary based on decreasing suit strength.
        return dict(sorted(strength_of_suits.items(), key=lambda item: item[1], reverse=True))



    def get_best_card_of_strongest_suit_to_play_first_player(self, available_cards: List[Card]) -> Card | None:
        """Selects the best card of the strongest suit to play as the first player.

        This function evaluates each suit in the available cards, scores them for strength, and returns the strongest card of the strongest suit, avoiding suits where only one card is held.

        Args:
            available_cards (List[Card]): The list of cards available to the player.

        Returns:
            Card or None: The best card of the strongest suit to play, or None if no suitable card is found.
        """
        cards_by_suit = dict(split_cards_by_suit(available_cards))
        strength_of_suits = self.evaluate_suit_strengths(available_cards)

        # Never start round with best card of suit if we only have one card of suit.
        # We risk to lose control of this suit otherwise if the opponent gets into the game.
        for suit in strength_of_suits:
            cards = self.sort_by_rank(cards_by_suit[suit])
            # Check if list is empty. Go to next if empty.
            if not cards:
                continue
            card = cards[0]
            is_blutt_bock: bool = len(cards_by_suit[suit]) < 2
            if self.is_bock(card) and not is_blutt_bock:
                return card
        return None
    

    def play_lowest_card_of_strongest_suit(self, available_cards: List[Card]) -> Card:
        """Plays the lowest card of the strongest suit from the available cards.

        This function determines the strongest suit based on suit strength evaluation and returns the lowest-ranked card from that suit.

        Args:
            available_cards (List[Card]): The list of cards available to the player.

        Returns:
            Card: The lowest card of the strongest suit.
        """
        cards_by_suit = dict(split_cards_by_suit(available_cards))
        suits_by_strength = self.evaluate_suit_strengths(available_cards)
        for suit in suits_by_strength:
            cards_of_strongest_suit = cards_by_suit[suit]
            # Check if list is empty. Go to next if empty.
            if not cards_of_strongest_suit:
                continue
            weakest_card = cards_of_strongest_suit[-1]
            # return weakest card, unless weakest card is banner. return second weakest instead
            # exception: second weakest card is Bock.
            if len(cards_of_strongest_suit) >= 2 and weakest_card.value == 10 and not self.is_bock(cards_of_strongest_suit[-2]):
                return cards_of_strongest_suit[-2]

        # We have no other option than to play banner.
        suit = next(iter(suits_by_strength))
        return cards_by_suit[suit][-1]



    def get_card_to_play_first_player_trumpfrole_first_round(self, available_cards: List[Card]) -> Card | None:
        """Determines the best card to play as the first player in the first round in trumpf role.

        This function selects a card to play based on suit length and card strength, prioritizing suits where the second strongest card is missing, then the strongest suit, and finally the lowest card of the strongest suit.

        Args:
            available_cards (List[Card]): The list of cards available to the player.

        Returns:
            Card or None: The selected card to play, or None if no suitable card is found.
        """
        # We have a long suit but are missing the second strongest card. Play bock to see if partner has said card. He must play it.
        card: Card | None = self.are_missing_second_strongest_card(available_cards)
        if card is not None:
            return card
        
        # Play strong suit where we have best and second best card.
        # Do not play blutt bock of a suit!
        # Do not play bock of suit where we do not have third best card and a lot of cards!
        card = self.get_best_card_of_strongest_suit_to_play_first_player(available_cards)
        if card is not None:
            return card
        
        # We made Vorhand trumpf. We must play our bocks.
        if bocks := list(filter(lambda x: self.is_bock(x), available_cards)):
            return bocks[0]

        # No bock: play lowest card of strongest suit
        return self.play_lowest_card_of_strongest_suit(available_cards)


    def signal_passing_card(self, bocks: List[Card], cards_by_suit: Dict[Suit, List[Card]], state: Status) -> Card | None:
        raise NotImplementedError


    def get_card_to_play_first_player_not_first_round(self, available_cards: List[Card], state: Status) -> Card | None:
        """Selects the optimal card to play as the first player in non-initial rounds.

        This function determines which card to play based on the current round, available bocks, suit flags, and the partner's status, aiming to maximize team advantage and signal intentions.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play, or None if no suitable card is found.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        suit_angezogen_flags = self.card_counter.get_angezogen_flags(self.card_counter.me.id)
        bocks = list(filter(lambda x: self.is_bock(x), available_cards))

        # We play our Wall of Cards but stop for a moment to signal our partner which card to hold.
        # We want to hand over to him after we played all our bocks.
        # Play a bock of another suit where we have at least one more non-bock card.
        if self.card_counter.current_round() == 3:
            card = self.signal_passing_card(bocks, dict(cards_by_suit), state)
            if card is not None:
                return card

        # Play bocks of same color first
        for bock in bocks:
            if bock.suit in suit_angezogen_flags:
                return bock
            
        # We played all bocks of angezogen flags. Play remaining bocks.
        if bocks:
            return bocks[0]

        # We played all our bocks. Hand over to partner.
        if not self.card_counter.had_stich_previously(self.card_counter.partner_id):
            return self.get_passing_card(cards_by_suit, state)
        
        # We cannot hand over to partner. Play best possible card in this situation.
        return self.get_value_card(cards_by_suit, state)


    def get_card_to_play_first_player_partnerrole(self, available_cards: List[Card]) -> Card | None:
        """Determines the best card to play as the first player in the partner role.

        This function selects a card to play based on suit length and card strength, prioritizing suits where the second strongest card is missing, then the strongest suit, and finally the lowest card of the strongest suit.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play, or None if no suitable card is found.
        """
        # We have a long suit but are missing the second strongest card. Play bock to see if partner has said card. He must play it.
        card: Card | None = self.are_missing_second_strongest_card(available_cards)
        if card is not None:
            return card
        
        # Play strong suit where we have best and second best card.
        # Do not play blutt bock of a suit!
        # Do not play bock of suit where we do not have third best card and a lot of cards!
        card = self.get_best_card_of_strongest_suit_to_play_first_player(available_cards)
        if card is not None:
            return card

        # No bock: play lowest card of strongest suit
        return self.play_lowest_card_of_strongest_suit(available_cards)


    def get_card_to_play_first_player(self, available_cards: List[Card], state: Status, role: str) -> Card | None:
        """Determines the best card to play as the first player based on the round and player role.

        This function selects the optimal card to play as the first player, considering whether it is the first round and the player's role (Trumpf or Partner), and delegates to the appropriate strategy.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.
            role (str): The role of the player ('Trumpf', 'Partner', etc.).

        Returns:
            Card or None: The selected card to play, or None if no suitable card is found.
        """
        is_first_round = not self.card_counter.current_round()

        if role == 'Trumpf' and is_first_round:
            return self.get_card_to_play_first_player_trumpfrole_first_round(available_cards)

        elif role == 'Partner' and is_first_round:
            return self.get_card_to_play_first_player_partnerrole(available_cards)

        
        elif role in {'Off', 'Trumpf', 'Partner'}:
            return self.get_card_to_play_first_player_not_first_round(available_cards, state)
        raise ValueError(f'Role is expected to be Trumpf, Partner, or Off. However, {role=}.')


    def get_stich_card_or_tossable(self, available_cards: List[Card], state: Status) -> Card | None:
        """Returns a stich card if available, otherwise returns a tossable card.

        This function attempts to select a card that can win the stich; if no such card is found, it returns a card that can be safely tossed.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The stich card if available, otherwise a tossable card, or None if neither is found.
        """
        cards_by_suit = split_cards_by_suit(available_cards)
        stich_card = self.get_stich_card(cards_by_suit, state)
        if stich_card is None:
            return self.get_tossable_card(available_cards, state)
        return stich_card


    def play_second_strongest_card_if_in_hand(self, available_cards: List[Card], state: Status) -> Card |None:
        """Checks if the partner is requesting the second strongest card of a suit.

        This function determines if the partner's play indicates a request for the second strongest card in the current suit, and returns it if available.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The second strongest card of the suit if requested and available, otherwise None.
        """
        suit = from_string_to_card(state.table[0].card).suit
        cards_of_suit = dict(split_cards_by_suit(available_cards))[suit]
        # If we do not have suit in hand, return None
        if cards_of_suit is None:
            return None
        
        # return second strongest card if in hand, else return None
        return next((card for card in cards_of_suit if self.is_nth_nut(1, card)), None)


    def partner_looks_for_second_strongest_card(self, available_cards: List[Card], state: Status) -> Card |None:
        """Checks if the partner is looking for the second strongest card in the first round.

        This function determines if it is the first round and the partner played a bock, and if so, returns the second strongest card if it is in hand.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The second strongest card if the partner is looking for it and it is available, otherwise None.
        """
        card: Card | None = None

        is_first_round: bool = self.card_counter.current_round() == 0
        partner_card: Card = from_string_to_card(state.table[0].card)
        partner_card_is_bock: bool = self.is_bock(partner_card)
        if is_first_round and partner_card_is_bock:
            card = self.play_second_strongest_card_if_in_hand(available_cards, state)
        return card


    def get_card_to_play_third_player_trumpf(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the best card to play as the third player in the trumpf role.

        This function selects a card based on whether it is the first round and the partner's play, or otherwise evaluates the player's stich history and desire to win the stich to choose between stich-winning or tossable cards.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play, or None if no suitable card is found.
        """
        # First round: check if partner played bock and is asking for the second strongest card so he can play his wall.
        card = self.partner_looks_for_second_strongest_card(available_cards, state)
        if card is not None:
            return card

        # Any other case
        cards_by_suit = split_cards_by_suit(available_cards)
        if not self.card_counter.had_stich_previously(self.card_counter.me.id):
            return self.get_stich_card_or_tossable(available_cards, state)
        if not self.want_stich(cards_by_suit, state):
            return self.get_tossable_card(available_cards, state)
        return self.get_stich_card_or_tossable(available_cards, state)
    

    def get_card_to_play_third_player_partner(self, available_cards: List[Card], state: Status) -> Card | None:
        """Determines the best card to play as the third player in the partner role.

        This function first checks if the partner is asking for the second strongest card, then if an Unterzug is possible, and otherwise decides between tossing a card or attempting to win the stich based on the game state.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.

        Returns:
            Card or None: The selected card to play, or None if no suitable card is found.
        """
        # First round: check if partner played bock and is asking for the second strongest card so he can play his wall.
        card = self.partner_looks_for_second_strongest_card(available_cards, state)
        if card is not None:
            return card

        # Check if Unterzug is possible
        unterzug_card = self.unterzug(state)
        if unterzug_card is not None:
            return unterzug_card

        # Any other case
        cards_by_suit = split_cards_by_suit(available_cards)
        if not self.want_stich(cards_by_suit, state):
            return self.get_tossable_card(available_cards, state)
        return self.get_stich_card_or_tossable(available_cards, state)
    

    def get_card_to_play_third_player(self, available_cards: List[Card], state: Status, role: str) -> None | Card:
        """Determines the best card to play as the third player based on the player's role.

        This function selects the optimal card to play as the third player, delegating to the appropriate strategy for the player's role (Trumpf, Partner, or Off), and considers whether to attempt to win the stich or toss a card.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.
            role (str): The role of the player ('Trumpf', 'Partner', or 'Off').

        Returns:
            Card or None: The selected card to play, or None if no suitable card is found.
        """
        if role not in {'Trumpf', 'Partner', 'Off'}:
            raise ValueError(f'Role is expected to be Trumpf, Partner, or Off. However, {role=}.')
        cards_by_suit = split_cards_by_suit(available_cards)
        if role == 'Trumpf':
            return self.get_card_to_play_third_player_trumpf(available_cards, state)

        elif role == 'Partner':
            return self.get_card_to_play_third_player_partner(available_cards, state)
        
        elif role == 'Off' and self.want_stich(cards_by_suit, state):
            return self.get_stich_card_or_tossable(available_cards, state)
        return self.get_tossable_card(available_cards, state)
        

    def get_card_to_play(self, available_cards: List[Card], state: Status, role: str) -> None | Card:
        """Determines the optimal card to play based on the player's position and role.

        This function selects the best card to play by evaluating the player's position in the round, the current game state, and the player's role, delegating to specialized strategies for each scenario.

        Args:
            available_cards (List[Card]): The list of cards available to the player.
            state (Status): The current game state.
            role (str): The role of the player ('Trumpf', 'Partner', etc.).

        Returns:
            Card or None: The selected card to play, or None if no suitable card is found.
        """
        current_position = len(state.table)
        cards_by_suit = split_cards_by_suit(available_cards)

        if current_position == 0:
            return self.get_card_to_play_first_player(available_cards, state, role)
            
        elif current_position == 1:
            return self.get_stich_card_or_tossable(available_cards, state)
        
        elif current_position == 2:
            return self.get_card_to_play_third_player(available_cards, state, role)

        elif current_position == 3 and self.want_stich(cards_by_suit, state):
            return self.get_stich_card_or_tossable(available_cards, state)
        
        return self.get_tossable_card(available_cards, state)
    

    def remove_all_bockcards_flagupdate(self, card: Card, player_id: int) -> None:
        """Updates flags to indicate that a player has no bock cards of any suit.

        This function checks if the played card is not a bock and, if so, marks all current bock cards as not held by the specified player.

        Args:
            card (Card): The card that was played by the player.
            player_id (int): The ID of the player whose bock card flags are updated.

        Returns:
            None
        """
        if self.is_bock(card):
            return None

        for suit in Suit:
            self.add_flag(DoesntHaveCardFlag(self.get_current_bock(suit)), player_id)
        return None


    def update_partner_first_player_flag_first_round(self, card: Card, state: Status) -> None:
        """Updates partner-related flags for the first round when the partner opens the stich.

        This function adjusts bock-related flags for the partner based on whether the game was geschoben and which card the partner played to open the first round.

        Args:
            card (Card): The card played by the partner as the opening card of the first round.
            state (Status): The current game state providing geschoben status and other context.

        Returns:
            None
        """
        if not state.geschoben:
            self.remove_all_bockcards_flagupdate(card, self.card_counter.partner_id)
        return None


    def update_partner_first_player_flag(self, card: Card, state: Status) -> None:
        """Updates partner-related inference flags when the partner leads a stich.

        This function adjusts the partner's bock-related flags based on whether it is the first round or a later round, and on the card the partner used to open the stich.

        Args:
            card (Card): The card played by the partner as the opening card.
            state (Status): The current game state.

        Returns:
            None
        """
        current_round: int = self.card_counter.current_round()

        if current_round == 0:
            self.update_partner_first_player_flag_first_round(card, state)

        # Partner opens with non-bock card
        else:
            self.remove_all_bockcards_flagupdate(card, self.card_counter.partner_id)
        return None


    def update_first_player_flags(self,player_id: int, card: Card, state: Status) -> None:
        """Updates inference flags after the leading player has played a card.

        This function records suit-strength information for the leader, updates partner or opponent-specific bock flags based on who led and the round number, and tracks whether the player has previously won a stich.

        Args:
            player_id (int): The ID of the player who led the stich.
            card (Card): The card that was played to open the stich.
            state (Status): The current game state.

        Returns:
            None
        """
        self.add_flag(SuitAngezogenFlag(card.suit), player_id)

        # Partner is first player. Update his flags.
        if player_id == self.card_counter.partner_id:
            self.update_partner_first_player_flag(card, state)
        
        # Opponent is first player. Update his flags.
        opponent_1_id = self.card_counter.opponent_1_id
        opponent_2_id = self.card_counter.opponent_2_id
        is_first_round: bool = self.card_counter.current_round() == 0
        if player_id in {opponent_1_id, opponent_2_id} and not is_first_round:
            self.remove_all_bockcards_flagupdate(card, player_id)

        # Add a flag because the player won the previous stich.
        player_has_won_stich_previously: bool = self.card_counter.had_stich_previously(player_id)
        is_geschoben: bool = state.geschoben
        suit_is_trumpf: bool = self.is_suit_trumpf()

        # TODO: Not sure why is_geschoben is here. Is also included in challenge player.
        condition = not (is_first_round and is_geschoben and suit_is_trumpf and player_has_won_stich_previously)

        if condition:
            self.add_flag(PreviouslyHadStichFlag(), player_id)
        return None
    

    def update_non_first_player_flags(self, player_id: int, card: Card, state: Status) -> None:
        """Updates inference flags for a non-leading player based on the card they played.

        This function records when a player fails to follow the round color, marking the led suit as failed to serve and the played suit as discarded for that player.

        Args:
            player_id (int): The ID of the player who played the card.
            card (Card): The card that was played by the player.
            state (Status): The current game state.

        Returns:
            None
        """
        round_color = self.card_counter.get_round_color(state)
        if round_color is None:
            raise ValueError
        if card.suit != round_color:
            self.add_flag(FailedToServeSuitFlag(round_color), player_id)
            self.add_flag(SuitVerworfenFlag(card.suit), player_id)
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