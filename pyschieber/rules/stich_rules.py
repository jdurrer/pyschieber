from functools import partial
from typing import List
from pyschieber.card import Card
from pyschieber.stich import Stich, PlayedCard
from pyschieber.trumpf import Trumpf

UNDER: int = 11
NAELL: int = 9


def stich_obe_unde(played_cards: List[PlayedCard], operation, trumpf: Trumpf) -> Stich:
    """
    Determines the winner of a trick for Obe-Abe or Unde-Ufe trumpf types.

    Selects the player who played the highest or lowest card of the leading suit, depending on the operation.

    Args:
        played_cards (List[GivenCard]): The cards played in the trick.
        operation: The function to determine the winning card (max for Obe-Abe, min for Unde-Ufe).
        trumpf (Trumpf): The current trumpf for the round.

    Returns:
        Stich: A Stich namedtuple with the winning player, played cards, and trumpf.
    """
    suit = played_cards[0].card.suit
    (_, index) = operation(
        [(played_card.card.value, i) for i, played_card in enumerate(played_cards) if played_card.card.suit == suit])
    return Stich(player=played_cards[index].player, played_cards=played_cards, trumpf=trumpf)


def stich_trumpf(played_cards: List[PlayedCard], trumpf: Trumpf) -> Stich:
    """
    Determines the winner of a trick when a trumpf suit is played.

    Selects the player who played the highest trumpf card, or falls back to Obe-Abe rules if no trumpf cards are played.

    Args:
        played_cards (List[GivenCard]): The cards played in the trick.
        trumpf (Trumpf): The current trumpf for the round.

    Returns:
        Stich: A Stich namedtuple with the winning player, played cards, and trumpf.
    """
    trumpfs: list[tuple[int, int]] = [(played_card.card.value, i) for i, played_card in enumerate(played_cards) if
               played_card.card.suit.name == trumpf.name]
    if trumpfs:
        index = _stich_trumpf_cards(trumpfs=trumpfs)
        return Stich(player=played_cards[index].player, played_cards=played_cards, trumpf=trumpf)
    else:
        return stich_obe_unde(played_cards=played_cards, operation=max, trumpf=trumpf)


def _stich_trumpf_cards(trumpfs: list[tuple[int, int]]) -> int:
    """
    Determines the index of the winning trumpf card in a trick.

    Returns the index of the Under card if present, otherwise the Naell card, or the highest value trumpf card.

    Args:
        trumpfs (list[tuple[int, int]]): List of tuples containing card values and their indices.

    Returns:
        int: The index of the winning trumpf card.
    """
    values = [trumpf[0] for trumpf in trumpfs]
    if UNDER in values:  # Under
        return trumpfs[values.index(UNDER)][1]
    return trumpfs[values.index(NAELL)][1] if NAELL in values else max(trumpfs)[1]


# ----------------------------
# Loose Code. Will be executed as soon as file is imported.
# ----------------------------


stich_rules: dict[Trumpf, partial[Stich]] = {
    Trumpf.OBE_ABE: partial(stich_obe_unde, operation=max, trumpf=Trumpf.OBE_ABE),
    Trumpf.UNDE_UFE: partial(stich_obe_unde, operation=min, trumpf=Trumpf.UNDE_UFE),
}

for trumpf in filter(lambda x: x not in [Trumpf.OBE_ABE, Trumpf.UNDE_UFE, Trumpf.SCHIEBEN], Trumpf):
    stich_rules[trumpf] = partial(stich_trumpf, trumpf=trumpf)


def card_allowed(table_cards: List[Card], chosen_card: Card, hand_cards: List[Card], trumpf: Trumpf) -> bool:
    """
    Determines if a chosen card can legally be played given the current table, hand, and trumpf.

    Checks suit-following and trumpf rules to validate the play according to game logic.

    Args:
        table_cards (List[Card]): The cards currently on the table.
        chosen_card (Card): The card the player wishes to play.
        hand_cards (List[Card]): The cards in the player's hand.
        trumpf (Trumpf): The current trumpf for the round.

    Returns:
        bool: True if the card is allowed to be played, False otherwise.
    """
    chosen_suit = chosen_card.suit

    if chosen_card not in hand_cards:
        return False

    if not table_cards or len(hand_cards) == 1:
        return True

    first_card = table_cards[0]
    first_suit = first_card.suit

    if first_suit == chosen_suit:
        return True
    
    if trumpf in [Trumpf.OBE_ABE, Trumpf.UNDE_UFE]:
        hand_suits = set([hand_card.suit for hand_card in hand_cards])
    else:
        if chosen_suit.name == trumpf.name:
            return not does_under_trumpf(table_cards=table_cards, chosen_card=chosen_card, hand_cards=hand_cards,
                                         trumpf=trumpf)
        hand_suits = set([card.suit for card in hand_cards if not is_trumpf_under(trumpf=trumpf, card=card)])
    return not (first_suit in hand_suits)


def is_trumpf_under(trumpf: Trumpf, card: Card) -> bool:
    """
    Checks if a given card is the Under card of the current trumpf suit.

    Returns True if the card matches the trumpf suit and has the value for Under.

    Args:
        trumpf (Trumpf): The current trumpf for the round.
        card (Card): The card to check.

    Returns:
        bool: True if the card is the Under of the trumpf suit, False otherwise.
    """
    return card.suit.name == trumpf.name and card.value == UNDER


def does_under_trumpf(table_cards: List[Card], chosen_card: Card, hand_cards: List[Card], trumpf: Trumpf) -> bool:
    """
    Determines if the player is required to play the Under card of the trumpf suit.

    Checks if the chosen card is the best trumpf, if the player holds non-trumpf cards, or if another trumpf card is the best.

    Args:
        table_cards (List[Card]): The cards currently on the table.
        chosen_card (Card): The card the player wishes to play.
        hand_cards (List[Card]): The cards in the player's hand.
        trumpf (Trumpf): The current trumpf for the round.

    Returns:
        bool: True if the player must play the Under trumpf card, False otherwise.
    """
    if is_chosen_card_best_trumpf(table_cards=table_cards, chosen_card=chosen_card, trumpf=trumpf):
        return False
    
    trumpf_cards_on_hand = [card for card in hand_cards if card.suit.name == trumpf.name]

    if len(trumpf_cards_on_hand) < len(hand_cards):
        return True

    for trumpf_card in trumpf_cards_on_hand:
        if is_chosen_card_best_trumpf(table_cards=table_cards, chosen_card=trumpf_card, trumpf=trumpf):
            return True
    return False


def is_chosen_card_best_trumpf(table_cards: List[Card], chosen_card: Card, trumpf: Trumpf) -> bool:
    """
    Checks if the chosen card is the best trumpf card among those played on the table.

    Compares the chosen card to all trumpf cards on the table and determines if it would win the trick.

    Args:
        table_cards (List[Card]): The cards currently on the table.
        chosen_card (Card): The card the player wishes to play.
        trumpf (Trumpf): The current trumpf for the round.

    Returns:
        bool: True if the chosen card is the best trumpf card, False otherwise.
    """
    trumpfs = [(card.value, i) for i, card in enumerate(table_cards) if card.suit.name == trumpf.name]
    chosen_card_index = len(table_cards)
    trumpfs.append((chosen_card.value, chosen_card_index))
    winner_index = _stich_trumpf_cards(trumpfs=trumpfs)
    return winner_index == chosen_card_index


def allowed_cards(hand_cards: List[Card] , table_cards: List[Card], trumpf: Trumpf) -> List[Card]:
    """
    Returns a list of cards from the player's hand that are allowed to be played.

    Checks each card in the hand against the current table and trumpf rules to determine legal plays.

    Args:
        hand_cards (List[Card]): The cards in the player's hand.
        table_cards (List[Card]): The cards currently on the table.
        trumpf (Trumpf): The current trumpf for the round.

    Returns:
        List[Card]: A list of cards that can legally be played.
    """
    cards = []
    if len(table_cards) > 0 or len(hand_cards) > 1:
        for card in hand_cards:
            if card_allowed(table_cards, card, hand_cards, trumpf):
                cards.append(card)
    else:
        cards += hand_cards
    return cards
