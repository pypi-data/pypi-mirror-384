import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np

A = np.array([[3.0, 4, 5], [-1, 0, 1], [4, 2, 0], [1, 1, 2], [3, -4, 1] ])
b = np.array([5.0, 4, 3, 2, 1])
x_true = np.linalg.lstsq(A, b)[0]

def test_lsnormal():
    x = FNC.lsnormal(A, b)
    assert isclose(x_true, x, rtol=1e-6).all()

def test_lsqrfact():
    x = FNC.lsqrfact(A, b)
    assert isclose(x_true, x).all()
    
def test_qrfact():
    Q, R = FNC.qrfact(A)
    assert isclose(Q @ R, A).all()
    assert isclose(Q.T @ Q, np.eye(Q.shape[0])).all()
    assert isclose(R, np.triu(R)).all()
    assert R.shape == (5, 3)
