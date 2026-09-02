from timeit import default_timer as timer

from pyschieber.tournament import Tournament


def run_statistics(players):
    point_limit = 100
    number_of_tournaments = 100

    tournament = Tournament(point_limit=point_limit)
    [tournament.register_player(player=player) for player in players]

    team_1_won = 0
    team_2_won = 0

    start = timer()

    for _ in range(number_of_tournaments):
        tournament.play()
        if tournament.teams[0].won(point_limit=point_limit):
            team_1_won += 1
        else:
            team_2_won += 1

    end = timer()
    print(
        f"\nTo run {number_of_tournaments} tournaments it took {end - start:.2f} seconds."
    )

    difference = abs(team_1_won - team_2_won)
    print("Difference: ", difference)
    print("Team 1: ", team_1_won)
    print("Team 2: ", team_2_won)
    assert team_1_won > team_2_won
