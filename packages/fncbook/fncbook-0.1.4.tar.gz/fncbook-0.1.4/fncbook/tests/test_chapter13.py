import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np
from numpy.linalg import norm

def test_poissonfd():
    f = lambda x,y: -np.sin(3*x*y-4*y)*(9*y**2+(3*x-4)**2)
    g = lambda x,y: np.sin(3*x*y-4*y)
    xspan = [0,1]
    yspan = [0,2]
    U, X, Y = FNC.poissonfd(f,g,100,xspan,90,yspan)
    assert norm(g(X,Y) - U) / norm(U) < 1e-3

def test_elliptic():
    lamb = 1.5
    def pde(X,Y,U,Ux,Uxx,Uy,Uyy):
        return Uxx + Uyy - lamb/(U+1)**2   # residual
    g = lambda x,y: x + y     # boundary condition
    u = FNC.elliptic(pde, g, 30, [0,2.5], 24, [0,1])
    assert isclose(u(1.25, 0.5), 1.7236921361, rtol=1e-6)
    assert isclose(u(1, 0), 1, rtol=1e-6)
