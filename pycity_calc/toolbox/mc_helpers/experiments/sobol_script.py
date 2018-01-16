#!/usr/bin/env python
# coding=utf-8
"""
Script for sobol sampling

https://people.sc.fsu.edu/~jburkardt/py_src/sobol/sobol_lib.py
"""

import math
import numpy as np
import random as rd


def i4_uniform(a, b, seed):
    # *****************************************************************************80
    #
    ## I4_UNIFORM returns a scaled pseudorandom I4.
    #
    #  Discussion:
    #
    #    The pseudorandom number will be scaled to be uniformly distributed
    #    between A and B.
    #
    #  Licensing:
    #
    #    This code is distributed under the MIT license.
    #
    #  Modified:
    #
    #    22 February 2011
    #
    #  Author:
    #
    #    Original MATLAB version by John Burkardt.
    #    PYTHON version by Corrado Chisari
    #
    #  Reference:
    #
    #    Paul Bratley, Bennett Fox, Linus Schrage,
    #    A Guide to Simulation,
    #    Springer Verlag, pages 201-202, 1983.
    #
    #    Pierre L'Ecuyer,
    #    Random Number Generation,
    #    in Handbook of Simulation,
    #    edited by Jerry Banks,
    #    Wiley Interscience, page 95, 1998.
    #
    #    Bennett Fox,
    #    Algorithm 647:
    #    Implementation and Relative Efficiency of Quasirandom
    #    Sequence Generators,
    #    ACM Transactions on Mathematical Software,
    #    Volume 12, Number 4, pages 362-376, 1986.
    #
    #    Peter Lewis, Allen Goodman, James Miller
    #    A Pseudo-Random Number Generator for the System/360,
    #    IBM Systems Journal,
    #    Volume 8, pages 136-143, 1969.
    #
    #  Parameters:
    #
    #    Input, integer A, B, the minimum and maximum acceptable values.
    #
    #    Input, integer SEED, a seed for the random number generator.
    #
    #    Output, integer C, the randomly chosen integer.
    #
    #    Output, integer SEED, the updated seed.
    #
    assert seed !=0, 'I4_UNIFORM - Fatal error!'

    seed = math.floor(seed)

    a = round(a)
    b = round(b)

    seed = np.mod(seed, 2147483647)

    if (seed < 0):
        seed = seed + 2147483647

    k = math.floor(seed / 127773)

    seed = 16807 * (seed - k * 127773) - k * 2836

    if (seed < 0):
        seed = seed + 2147483647

    r = seed * 4.656612875E-10
    #
    #	Scale R to lie between A-0.5 and B+0.5.
    #
    r = (1.0 - r) * (min(a, b) - 0.5) + r * (max(a, b) + 0.5)
    #
    #	Use rounding to convert R to an integer between A and B.
    #
    value = round(r)

    value = max(value, min(a, b))
    value = min(value, max(a, b))

    c = value

    return [c, int(seed)]


def do_sobol_sampling(min_val, max_val, nb_samples, seed=1, do_print=False):
    """
    Do sobol sampling for range of min/max values with specific seed.
    Requires uniform distribution

    Parameters
    ----------
    min_val : float
        Minimal value
    max : float
        Maximal value
    nb_samples : int
        Number of samples for list_of_cs
    seed : int, optional
        Seed for random number generation (default: 1)
    do_print : bool, optional
        Defines, if list should be printed out (default: False)

    Returns
    -------
    list_of_cs : list (of floats)
        List with chosen values
    """

    #  Increase float input values. This is done to prevent generation of
    #  repeating int output values
    min_val *= 1000000
    max_val *= 1000000

    list_of_cs = []

    while len(list_of_cs) < nb_samples:
        [c, seed] = i4_uniform(a=min_val, b=max_val, seed=seed)
        if c not in list_of_cs:
            list_of_cs.append(c)
        if do_print:
            print(list_of_cs)

    #  Reconvert list values
    for i in range(len(list_of_cs)):
        val = list_of_cs[i]
        val /= 1000000
        list_of_cs[i] = round(val, 4)

        assert val >= min_val / 1000000, 'Sampling values is smaller than min.'
        assert val <= max_val / 1000000, 'Sampling values is larger than max.'

    return list_of_cs


if __name__ == '__main__':

    #  Nb. of samples
    nb_samples = 100

    min_val = 0.5
    max_val = 20.5

    # Do sobol sampling with uniform distribution
    list_of_cs = do_sobol_sampling(min_val=min_val, max_val=max_val,
                                   nb_samples=nb_samples, seed=1,
                                   do_print=False)

    print('Sampling list:')
    print(list_of_cs)


    def only_for_comparison_random_sampling(min_val, max_val, nb_samples):
        """
        Perform random sampling

        Parameters
        ----------
        min_val : float
            Minimal value
        max : float
            Maximal value
        nb_samples : int
            Number of samples for list_of_cs

        Returns
        -------
        list_rd : list
            List of floats (sample values)
        """

        list_rd = []

        #  Increase float input values. This is done to prevent generation of
        #  repeating int output values
        min_val *= 1000000
        max_val *= 1000000

        for i in range(nb_samples):
            val = rd.randint(min_val, max_val) / 1000000

            list_rd.append(val)

        return list_rd

    list_rnd = only_for_comparison_random_sampling(min_val=min_val,
                                                   max_val=max_val,
                                                   nb_samples=nb_samples)

    import matplotlib.pyplot as plt

    plt.hist(list_of_cs, bins=nb_samples * 5, label='Sobol')
    plt.title('Sobol')
    plt.show()
    plt.close()

    plt.hist(list_rnd, bins=nb_samples * 5, label='Random')
    plt.title('Random')
    plt.show()
    plt.close()

    plt.hist(list_of_cs, bins=nb_samples*5, label='Sobol')
    plt.hist(list_rnd, bins=nb_samples*5, label='Random')
    plt.legend()
    plt.show()
    plt.close()