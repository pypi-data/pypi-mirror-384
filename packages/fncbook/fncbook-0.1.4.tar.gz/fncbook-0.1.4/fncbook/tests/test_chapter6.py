from scipy.integrate import solve_ivp
import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np

f = lambda t, u: u - 2*t**2
u_ex = np.exp(1.5) - 2*(-2 + 2*np.exp(1.5) - 2*1.5 - 1.5**2)
g = lambda t, u: np.array([t -6 - np.sin(u[1]), u[0]])
sol = solve_ivp(g, [1, 2], np.array([-1., 4]), rtol=1e-11, atol=1e-11)

def test_euler():
    t, u = FNC.euler(f, [0, 1.5], 1.0, 4000)
    assert isclose(u[0,-1], u_ex, rtol=0.005)

def test_ie2():
    t, u = FNC.ie2(f, [0, 1.5], 1.0, 4000)
    assert isclose(u[:, -1], u_ex, rtol=0.0001)

def test_am2():
    t, u = FNC.am2(f, [0, 1.5], 1.0, 4000)
    assert isclose(u[:, -1], u_ex, rtol=1e-4)

def test_eulersys():
    t, u = FNC.euler(g, [1, 2], [-1., 4], 4000)
    assert isclose(u[:, -1], sol.y[:, -1], rtol=0.004).all()

def test_ie2sys():
    t, u = FNC.ie2(g, [1, 2], [-1., 4], 4000)
    assert isclose(u[:, -1], sol.y[:, -1], rtol=1e-3).all()

def test_rk4():
    t, u = FNC.rk4(g, [1, 2], [-1., 4], 800)
    assert isclose(u[:, -1], sol.y[:,-1], rtol=1e-6).all()

def test_rk23():
    t, u = FNC.rk23(g, [1, 2], [-1., 4], 1e-5)
    assert isclose(u[:, -1], sol.y[:, -1], rtol=1e-4).all()

def test_ab4():
    t, u = FNC.ab4(g, [1, 2], [-1., 4], 800)
    assert isclose(u[:, -1], sol.y[:, -1], rtol=1e-4).all()

def test_am2sys():
    t, u = FNC.am2(g, [1, 2], [-1., 4], 2000)
    assert isclose(u[:, -1], sol.y[:, -1], rtol=1e-4).all()
