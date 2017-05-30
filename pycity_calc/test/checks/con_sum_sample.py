# coding=utf-8
import random


def constrained_sum_sample_pos(n, total):
    """
    Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur.
    """

    dividers = sorted(random.sample(range(1, total), n - 1))
    # print(dividers)
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def test_constrainted_sum_sample():

    n = 1
    total = 3
    #  Initial run
    result_list = constrained_sum_sample_pos(n, total)
    print(result_list)

    while all(i <= 5 for i in result_list) is not True:
        result_list = constrained_sum_sample_pos(n, total)
        print(result_list)


test_constrainted_sum_sample()