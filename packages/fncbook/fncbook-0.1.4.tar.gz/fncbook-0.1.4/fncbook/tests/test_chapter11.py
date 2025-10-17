import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np

def test_diffper():
    s = lambda x: np.sin(np.pi*(x-0.2))
    c = lambda x: np.cos(np.pi*(x-0.2))
    f = lambda x: 1 + s(x)**2
    df = lambda x: 2*np.pi*s(x)*c(x)
    ddf = lambda x: 2*np.pi**2*(c(x)**2 - s(x)**2)
    t,D,DD = FNC.diffper(400,(0,2))
    assert isclose(df(t), D @ f(t), rtol=1e-3).all()
    assert isclose(ddf(t), DD @ f(t), rtol=1e-3).all()

def test_parabolic():
    phi = lambda t,x,u,ux,uxx: uxx + t*u
    g1 = lambda u,ux: ux
    g2 = lambda u,ux: u-1
    init = lambda x: x**2
    x,u = FNC.parabolic(phi,(0,1),40,g1,g2,(0,2),init)
    assert isclose(u(0.5)[20], 0.845404, rtol=1e-3)
    assert isclose(u(1)[-1], 1, rtol=1e-4)
    assert isclose(u(2)[0], 2.45692, rtol=1e-3)
