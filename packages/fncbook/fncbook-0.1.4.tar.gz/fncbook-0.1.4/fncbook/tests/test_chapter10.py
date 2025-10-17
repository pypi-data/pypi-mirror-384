import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np

f = lambda x: np.exp(x**2 - 3*x)
df = lambda x: (2*x - 3) * f(x)
ddf = lambda x: ((2*x - 3)**2 + 2) * f(x)

def test_shoot():
    lamb = 0.6
    phi = lambda r, w, dwdr: lamb / w**2 - dwdr / r
    a, b = 1e-15, 1
    g1 = lambda u, du: du
    g2 = lambda u, du: u - 1
    r, w, dwdr = FNC.shoot(phi, a, b, g1, g2, [0.8, 0])
    assert isclose(w[0], 0.78776, rtol=1e-4)

def test_diffmat2():
    x, D, DD = FNC.diffmat2(400, (-0.5, 2))
    assert isclose(df(x), D @ f(x), rtol=1e-3).all()
    assert isclose(ddf(x), DD @ f(x), rtol=1e-3).all()

def test_diffcheb():
    t, D, DD = FNC.diffcheb(80, (-0.5, 2))
    assert isclose(df(t), D @ f(t), rtol=1e-7).all()
    assert isclose(ddf(t), DD @ f(t), rtol=1e-7).all()

def test_bvplin():
    exact = lambda x: np.exp(np.sin(x))
    p = lambda x: -np.cos(x)
    q = np.sin
    r = lambda x: np.zeros(x.shape)
    x, u = FNC.bvplin(p, q, r, [0, np.pi/2], 1, np.exp(1), 300)
    assert isclose(u, exact(x), rtol=1e-3).all()

def test_bvp():
    phi = lambda t, theta, omega: -0.05 * omega - np.sin(theta)
    g1 = lambda u, du: u - 2.5
    g2 = lambda u, du: u + 2
    init = np.linspace(2.5, -2, 101)
    t, theta = FNC.bvp(phi, [0, 5], g1, g2, init)
    assert isclose(theta[6], 2.421850016880724, rtol=1e-5)

def test_fem():
    c = lambda x: x**2
    q = lambda x: np.tile(4, x.shape)
    f = lambda x: np.sin(np.pi * x)
    x, u = FNC.fem(c, q, f, 0, 1, 100)
    assert isclose(u[32], 0.1641366907307196, rtol=1e-10)

