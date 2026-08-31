from copy import deepcopy

from pyschieber.card import Card
from pyschieber.player.rulebased_player.rulebased_player import RuleBasedPlayer
from pyschieber.player.rulebased_player.strategy.flags.flags import (
    FailedToServeSuitFlag,
)
from pyschieber.player.treePlayer.treesearch.helper import (
    flip_ones_and_zeros_in_list,
    list_of_cards_to_array,
)
from pyschieber.player.treePlayer.treesearch.ismcts.cpmpy_csp import (
    CardDistributionSolver,
)


class Informationset:
    def __init__(self, player: RuleBasedPlayer) -> None:
        self.player = deepcopy(player)

    def constrain_cards(
        self,
        possible_players_holding_card: list[list[int]],
        cards_constraint: list[int],
        player_id: int,
    ) -> list[list[int]]:
        """Restrict the possible holders of specific cards for a given player.

        This method updates the card distribution model so that, for each card,
        the given player is disallowed from holding that card whenever the
        corresponding constraint entry is 0.

        Args:
            possible_players_holding_card (list[list[int]]): A list of lists, where each inner list represents a card and the values represent whether a player can hold that card (1) or not (0).
            cards_constraint (list[int]): A list of flags for each card; 0 means the player must not hold that card, 1 leaves the current possibility unchanged.
            player_id (int): The ID of the player whose possible card holdings are being restricted.

        Returns:
            list[list[int]]: The updated matrix of possible players holding each card.
        """
        if len(possible_players_holding_card) != len(cards_constraint):
            raise ValueError(
                "cards_constraint length must match number of cards in possible_players_holding_card"
            )

        for card_index, constraint_flag in enumerate(cards_constraint):
            if constraint_flag == 0:
                possible_players_holding_card[card_index][player_id] = 0

        return possible_players_holding_card

    def restrict_cards_to_single_player(
        self,
        possible_players_holding_card: list[list[int]],
        cards: list[int],
        player_id: int,
    ) -> list[list[int]]:
        """Limit the possible holders of selected cards to a single specified player.

        This method constrains the card distribution model so that the given player
        is the only one who can hold the indicated cards, while all other players
        are explicitly excluded from holding those same cards.

        Args:
            possible_players_holding_card (list[list[int]]): A list of lists, where each inner list represents a card and the values represent whether a player can hold that card (1) or not (0).
            cards (list[int]): A list of flags for each card; 1 means the card must be held by the given player, 0 means the card must not be held by the given player.
            player_id (int): The ID of the player to whom the selected cards are restricted.

        Returns:
            list[list[int]]: The updated matrix of possible players holding each card, reflecting the single-player restriction for the specified cards.
        """

        possible_players_holding_card = self.constrain_cards(
            possible_players_holding_card, cards, player_id
        )

        cards = flip_ones_and_zeros_in_list(cards)
        for id in range(4):
            if id == player_id:
                continue
            possible_players_holding_card = self.constrain_cards(
                possible_players_holding_card, cards, id
            )

        return possible_players_holding_card

    def exclude_suits_by_player(self, player_id) -> list[Card]:
        """Collect remaining cards of suits a player has failed to serve.

        This method inspects the failure flags for the specified player and
        returns the cards of each suit that the player could not follow, so
        those cards can be excluded from that player's possible holdings.

        Args:
            player_id: The ID of the player whose failed-to-serve suits are being analysed.

        Returns:
            A list of cards belonging to suits that the given player has failed to serve
            and should therefore be excluded from that player's potential hand.
        """
        cards_of_suit: list[Card] = []
        for flag in self.player.strategy.card_counter.flags[player_id]:
            if isinstance(flag, FailedToServeSuitFlag):
                cards_of_suit.extend(
                    self.player.strategy.card_counter.remaining_by_suit(flag.color)
                )
        return cards_of_suit

    def _build_initial_possibility_matrix(self) -> list[list[int]]:
        """Create the initial matrix of possible players holding each card.

        This helper initializes a placeholder matrix where all players can hold
        all cards. The matrix is later refined based on the current game state
        and player knowledge.
        """
        return [[1, 1, 1, 1] for _ in range(36)]

    def _apply_known_player_cards(
        self, possible_players_holding_card: list[list[int]]
    ) -> list[list[int]]:
        """Apply constraints based on the cards currently held by the search player.

        This helper restricts the cards that the current player holds to only that
        player, and removes them from the possible holdings of other players.
        """
        self.restrict_cards_to_single_player(
            possible_players_holding_card,
            list_of_cards_to_array(self.player.cards),
            self.player.id,  # type: ignore
        )
        return possible_players_holding_card

    def _apply_played_cards_constraints(
        self, possible_players_holding_card: list[list[int]]
    ) -> list[list[int]]:
        """Apply constraints based on cards that have already been played.

        This helper removes all played cards from the possible holdings of all
        players in the possibility matrix.
        """
        played_cards = list_of_cards_to_array(
            self.player.strategy.card_counter.cards_played()
        )
        played_cards = flip_ones_and_zeros_in_list(played_cards)
        for id in range(4):
            possible_players_holding_card = self.constrain_cards(
                possible_players_holding_card, played_cards, id
            )
        return possible_players_holding_card

    def _apply_failed_suit_constraints(
        self, possible_players_holding_card: list[list[int]]
    ) -> list[list[int]]:
        """Apply constraints for players who failed to serve specific suits.

        This helper excludes cards of suits that players have failed to serve
        from those players' possible holdings.
        """
        for player_id in range(4):
            if cards_of_suit := self.exclude_suits_by_player(player_id):
                self.constrain_cards(
                    possible_players_holding_card,
                    flip_ones_and_zeros_in_list(list_of_cards_to_array(cards_of_suit)),
                    player_id,
                )
        return possible_players_holding_card

    def _compute_handcard_lengths(self) -> list[int]:
        """Compute the expected hand card lengths for each player.

        This helper derives hand sizes from the number of cards already played
        per player, assuming a total of nine cards per player.
        """
        handcard_lengths: list[int] = []
        handcard_lengths.extend(
            9 - len(self.player.strategy.card_counter.played_cards[id])
            for id in range(4)
        )
        return handcard_lengths


def initialize_card_distribution(player: RuleBasedPlayer) -> CardDistributionSolver:
    """Initialize the card distribution constraint satisfaction problem.

    This method builds the initial possibility matrix, applies all known
    constraints derived from the current game state and player knowledge,
    and constructs a CardDistributionSolver instance over the resulting
    card possibilities and hand sizes.

    Returns:
        CardDistributionSolver: The configured solver ready to sample
        feasible card distributions.
    """
    informationset = Informationset(player)
    possible_players_holding_card = informationset._build_initial_possibility_matrix()
    possible_players_holding_card = informationset._apply_known_player_cards(
        possible_players_holding_card
    )
    possible_players_holding_card = informationset._apply_played_cards_constraints(
        possible_players_holding_card
    )
    possible_players_holding_card = informationset._apply_failed_suit_constraints(
        possible_players_holding_card
    )
    handcard_lengths = informationset._compute_handcard_lengths()
    return CardDistributionSolver(handcard_lengths, possible_players_holding_card)
