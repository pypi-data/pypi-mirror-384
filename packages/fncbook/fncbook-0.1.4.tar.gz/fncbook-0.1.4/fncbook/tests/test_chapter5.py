import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np
from scipy.interpolate import interp1d

f = lambda t: np.cos(5*t)
t = np.array([-2,-0.5,0,1,1.5,3.5,4]) / 10

def test_intadapt():
    Q, t = FNC.intadapt(f, -1, 3, 1e-8)
    assert isclose(Q, (np.sin(15) + np.sin(5)) / 5, rtol=1e-5)

def test_trapezoid():
    T, _, _ = FNC.trapezoid(f, -1, 3, 820)
    assert isclose(T, (np.sin(15) + np.sin(5)) / 5, rtol=1e-4)

def test_fdweights():
    w = FNC.fdweights(t - 0.12, 2)
    g = lambda t: np.cos(3*t)
    val = np.dot(w, g(t))
    assert isclose(val, -9*np.cos(0.36), rtol=1e-3)

def test_hatfun():
    H = FNC.hatfun(t, 5)
    P = interp1d(t, [0,0,0,0,0,1,0], kind='linear')
    x = np.array([0.22, 0.38, 0.06, t[5], t[6], t[0]])
    assert isclose(H(x), P(x)).all()

def test_plinterp():
    p = FNC.plinterp(t, f(t))
    P = interp1d(t, f(t), kind='linear')
    x = [-0.2, 0, 0.22, 0.38]
    assert isclose(p(x), P(x)).all()

def test_spinterp():
    S = FNC.spinterp(t, np.exp(t))
    x = np.array([-.17, -0.01, 0.33, .38])
    assert isclose(S(x), np.exp(x), rtol=1e-5).all()
    assert isclose(S(t), np.exp(t), rtol=1e-11).all()
