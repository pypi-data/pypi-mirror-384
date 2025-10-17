import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np

A = np.array([[ 1.0, 2, 3, 0], [-1, 1, 2, -1], [3, 1, 2, 4], [1, 1, 1, 1] ])

def test_lufact():
    L, U = FNC.lufact(A)
    assert isclose(L @ U, A).all()
    assert isclose(np.tril(L), L).all()
    assert isclose(np.triu(U), U).all()

def test_trisub():
    L = np.array([[1.0, 0, 0, 0], [-1, 1, 0, 0], [3, 1, 1, 0], [1, 1, 1, 1]])
    x = np.array([1, -2.5, 0, 2])
    result = FNC.forwardsub(L, L @ x)
    assert isclose(result, x).all()
    U = np.array([[1.0, 2, 3, 0], [0, 2, 2, -1], [0, 0, -1, 4], [0, 0, 0, 1]])
    result = FNC.backsub(U, U @ x)
    assert isclose(result, x).all()

def test_plufact():
    L, U, p = FNC.plufact(A)
    assert isclose(L @ U, A[p, :]).all()
    assert isclose(np.tril(L), L).all()
    assert isclose(np.triu(U), U).all()

