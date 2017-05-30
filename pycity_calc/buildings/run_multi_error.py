#!/usr/bin/env python
# coding=utf-8
"""

"""

import logging
from multiprocessing import Pool

def f(args):
    d = {}
    d[0] # <-- raises KeyError

def f_mp(args):
    try:
        return f(args)
    except Exception:
        logging.exception("f(%r) failed" % (args,))

if __name__=="__main__":
    p = Pool()
    p.map(f_mp, [None])