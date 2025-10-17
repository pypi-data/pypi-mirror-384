import cProfile
import os
import pstats
from contextlib import contextmanager
from pstats import SortKey
from time import time


__all__ = ["profile", "SortKey"]


@contextmanager
def profile(sortby: SortKey = SortKey.CUMULATIVE, directory="../pstats"):
    """
    sortby: SortKey.CUMULATIVE | SortKey.PCALLS | etc.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        pr = cProfile.Profile()
        pr.enable()
        yield
    finally:
        pr.disable()
        with open(os.path.join(directory, "%s-%d.py") % (__name__, int(time())), "w") as s:
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats()
