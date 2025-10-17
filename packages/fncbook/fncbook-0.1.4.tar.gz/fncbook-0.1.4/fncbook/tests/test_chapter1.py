import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np

def test_horner():
    result = FNC.horner([1,-3,3,-1], 1.6)
    assert isclose(result, 0.6**3)
