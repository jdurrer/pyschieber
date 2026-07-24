# ----------------------------
# Libraries
# ----------------------------

from typing import List  # Required for Python < 3.9
from pyschieber.helpers.typed_dict import TypedDictPlayer


# ----------------------------
# Class
# ----------------------------


class Team:

    def __init__(self, players: List[TypedDictPlayer]): # removed  "players = None" as standard init
        self.points: int = 0
        self.players: List[TypedDictPlayer] = players


    def player_by_number(self, number: int) -> TypedDictPlayer | None:
        """
        Returns the player with the specified number from the team.

        Searches through the team's players and returns the player whose id matches the given number.
        
        Args:
            number (int): The id number of the player to find.

        Returns:
            TypedDictPlayer | None: The player with the matching id, or None if not found.
        """
        for player in self.players:
            if player.id == number:
                return player
        return None


    def won(self, point_limit: float) -> bool:
        """Checks if a team has won. Returns true if the point limit was reached.

        Args:
            point_limit (float): The given point limit to be reached for a team to win.

        Returns:
            bool: True if point limit reached, false otherwise. 
        """
        return self.points >= point_limit
    

    def reset_points(self) -> None:
        """
        Resets the team's points to zero.

        This method is used to clear the team's score, typically at the start of a new game or round.
        """
        self.points = 0