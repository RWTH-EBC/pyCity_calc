#!/usr/bin/env python
# coding=utf-8
"""
air exchange rate (Corrado,
2003). According to this, we chose a Nakagami distribution
with shape parameter 1.5 and scale parameter
0.3.
"""

import numpy as np
from scipy.stats import nakagami
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 1)


nu = 0.6
r = nakagami.rvs(nu, scale=0.4, size=10000)
ax.hist(r, bins=50)
plt.show()

print('mean value: ', np.mean(r))

x = [0, 1, 2, 3, 4]

f = nakagami.pdf(x, nu=nu, scale=1)

print(f)
