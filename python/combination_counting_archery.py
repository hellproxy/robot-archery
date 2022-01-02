from collections import deque
from itertools import count
from math import factorial
from itertools import islice
import numpy as np


def main():
    test_find_winner()
    test_generate_missed_shots()
    test_create_win_distribution()

    print_converging_probability_distribution(4, 20)


def print_converging_probability_distribution(n_robots, iterations):
    padding = " " * 2

    # print header
    print(f"{'s':12}", end="")
    for robot in range(n_robots):
        p_robot = f"P({robot})"
        print(f"{padding}{p_robot:12}{padding}", end="")
    print()

    # print probabilities
    for p_distribution, sequence_size in islice(generate_probability_distribution(n_robots), iterations):
        print(f"{str(sequence_size):12}", end="")
        for robot in range(n_robots):
            print(f"{padding}{p_distribution[robot]:.10f}{padding}", end="")
        print()


def find_winner(n_robots, winning_sequence):
    final_shot = winning_sequence[-1]
    losing_shots = deque(winning_sequence)
    robots_still_in = deque(range(n_robots))

    for shot in range(final_shot):
        # use popleft() and append() to cycle through the robots
        current_robot = robots_still_in.popleft()
        
        # if this robot shot the losing shot, it gets removed from the match
        if shot == losing_shots[0]:
            losing_shots.popleft()
        else:
            robots_still_in.append(current_robot)

    # there should now be only 1 robot remaining, the winner
    return robots_still_in.pop()


def generate_missed_shots(needed, sequence):
    if needed == 0:
        yield sequence
    else:
        # e.g. (6) -> (1, 6), (2, 6), (3, 6), (4, 6), (5, 6)
        for i in range(1, sequence[0]):
            new_sequence = (i, ) + sequence
            yield from generate_missed_shots(needed - 1, new_sequence)


def create_win_distribution(n_robots, final_shot):
    distribution = {robot: 0 for robot in range(n_robots)}

    missed_shots_needed = n_robots - 2
    sequence = (final_shot, )

    for winning_sequence in generate_missed_shots(missed_shots_needed, sequence):
        winner = find_winner(n_robots, winning_sequence)
        combinations = np.prod(winning_sequence)

        distribution[winner] += combinations

    return distribution


def generate_probability_distribution(n_robots):
    p_distribution = {robot: 0.0 for robot in range(n_robots)}

    for final_shot in count(start=1):
        distribution = create_win_distribution(n_robots, final_shot)
        total_combinations = factorial(final_shot + 1)

        # update each robot's probability with probability of winning on this shot
        for robot, combinations in distribution.items():
            p_distribution[robot] += combinations / total_combinations

        yield p_distribution, final_shot


def test_find_winner():
    assert find_winner(3, [1, 5]) == 2
    assert find_winner(3, [2, 5]) == 1
    assert find_winner(3, [3, 5]) == 1
    assert find_winner(3, [4, 5]) == 0
    assert find_winner(3, [1, 6]) == 0
    assert find_winner(3, [2, 6]) == 0
    assert find_winner(3, [3, 6]) == 2
    assert find_winner(3, [4, 6]) == 2
    assert find_winner(3, [5, 6]) == 1


def test_generate_missed_shots():
    assert set(generate_missed_shots(1, (5, ))) == {(1, 5), (2, 5), (3, 5), (4, 5)}
    assert set(generate_missed_shots(1, (6, ))) == {(1, 6), (2, 6), (3, 6), (4, 6), (5, 6)}
    assert set(generate_missed_shots(2, (6, ))) == {
        (1, 2, 6), (1, 3, 6), (1, 4, 6), (1, 5, 6), (2, 3, 6),
        (2, 4, 6), (2, 5, 6), (3, 4, 6), (3, 5, 6), (4, 5, 6)
    }


def test_create_win_distribution():
    assert create_win_distribution(2, 0) == {0: 0, 1: 0}
    assert create_win_distribution(2, 1) == {0: 1, 1: 0}
    assert create_win_distribution(3, 2) == {0: 2, 1: 0, 2: 0}
    assert create_win_distribution(3, 5) == {0: 20, 1: 25, 2: 5}
    assert create_win_distribution(3, 6) == {0: 18, 1: 30, 2: 42}


if __name__ == "__main__":
    main()
