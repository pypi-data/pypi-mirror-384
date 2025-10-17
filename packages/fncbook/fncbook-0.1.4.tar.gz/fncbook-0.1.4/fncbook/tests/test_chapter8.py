import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np
from numpy.linalg import norm

V = np.random.randn(4,4)
D = np.diag([-2,0.4,-0.1,0.01])
A = V @ D @ np.linalg.inv(V)
b = np.ones(4)

def test_poweriter():
    beta,x = FNC.poweriter(A,30)
    assert isclose(beta[-1], -2, rtol=1e-10)
    d = np.dot(x,V[:,0])/(norm(V[:,0])*norm(x))
    assert isclose(np.abs(d), 1, rtol=1e-10)

def test_inviter():
    beta,x = FNC.inviter(A,0.37,15)
    assert isclose(beta[-1], 0.4, rtol=1e-10)
    d = np.dot(x,V[:, 1]) / (norm(V[:, 1])*norm(x))
    assert isclose(np.abs(d), 1, rtol=1e-10)

def test_arnoldi():
    Q,H = FNC.arnoldi(A, b, 4)
    assert isclose(A @ Q[:, :4], Q @ H, rtol=1e-10).all()

def test_gmres():
    x,res = FNC.gmres(A, b, 3)
    assert isclose(norm(b - A @ x), res[-1], rtol=1e-10)
    x,res = FNC.gmres(A, b, 4)
    assert isclose(A @ x, b, rtol=1e-10).all()
