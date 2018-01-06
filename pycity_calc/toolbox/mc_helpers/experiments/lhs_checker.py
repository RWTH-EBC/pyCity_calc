#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import pyDOE
import matplotlib.pylab as plt


design = pyDOE.lhs(n=4, samples=100)

plt.hist(design[:, 0])
plt.hist(design[:, 1])
plt.hist(design[:, 2])
plt.hist(design[:, 3])
plt.show()
plt.close()

plt.plot(design[:, 0])
plt.plot(design[:, 1])
plt.plot(design[:, 2])
plt.plot(design[:, 3])
plt.show()
plt.close()

design = pyDOE.lhs(n=4, samples=100, criterion='center')

plt.hist(design[:, 0])
plt.hist(design[:, 1])
plt.hist(design[:, 2])
plt.hist(design[:, 3])
plt.show()
plt.close()

plt.plot(design[:, 0])
plt.plot(design[:, 1])
plt.plot(design[:, 2])
plt.plot(design[:, 3])
plt.show()
plt.close()

design = pyDOE.lhs(n=4, samples=100, criterion='maximin')

plt.hist(design[:, 0])
plt.hist(design[:, 1])
plt.hist(design[:, 2])
plt.hist(design[:, 3])
plt.show()
plt.close()

plt.plot(design[:, 0])
plt.plot(design[:, 1])
plt.plot(design[:, 2])
plt.plot(design[:, 3])
plt.show()
plt.close()

design = pyDOE.lhs(n=4, samples=100, criterion='centermaximin')

plt.hist(design[:, 0])
plt.hist(design[:, 1])
plt.hist(design[:, 2])
plt.hist(design[:, 3])
plt.show()
plt.close()

plt.plot(design[:, 0])
plt.plot(design[:, 1])
plt.plot(design[:, 2])
plt.plot(design[:, 3])
plt.show()
plt.close()
