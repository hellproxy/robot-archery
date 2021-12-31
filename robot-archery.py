from random import random
from math import sqrt
from functools import partial
from collections import deque
import mr4mp


def main():
    matches = 10000000
    n_players = 2

    wins = play_matches_parallel(n_players, matches, 8)
    total_wins = sum(wins.values())
    
    assert total_wins == matches, f"Total wins ({wins}) do not equal number of matches played ({matches})"

    for player in range(1, n_players + 1):
        print(f"P({player}): {wins[player]/matches}")


def combine(n_players, partial_wins_a, partial_wins_b):
    return { x: partial_wins_a[x] + partial_wins_b[x] for x in range(1, n_players + 1) }


def play_match_n(n_players, instance):
    return play_match(n_players)


def play_matches_parallel(n_players, matches, parallelism):
    combine_ = partial(combine, n_players)
    play_match_n_ = partial(play_match_n, n_players)
    return mr4mp.pool(parallelism).mapreduce(play_match_n_, combine_, range(matches))


def play_matches(matches, n_players):
    wins = { x: 0 for x in range(1, n_players + 1) }

    for _ in range(matches):
        winner = play_match(n_players)
        wins[winner] += 1

    return wins


def play_match(n_players):
    assert n_players > 1, "Need at least 2 players"

    # create linked list that starts with the 2nd player e.g. [2, 3, 4, 1]
    players = deque(range(2, n_players + 1))
    players.append(1)
    # 2nd player always has 50% chance to beat 1st shot
    p_hit = 0.5

    while len(players) > 1:
        current_player = players.popleft()
        r = random() 
        if r < p_hit:
            p_hit = r
            players.append(current_player)

    wins = { x: 0 for x in range(1, n_players + 1) }
    wins[players.pop()] += 1

    return wins


if __name__ == "__main__":
    main()