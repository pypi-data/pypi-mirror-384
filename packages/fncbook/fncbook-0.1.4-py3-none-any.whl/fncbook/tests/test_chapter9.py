import fncbook as FNC  # The code to test
from numpy import isclose
import numpy as np

def test_polyinterp():
    f = lambda x: np.exp(np.sin(x)+x**2)
    t = np.array([-np.cos(k*np.pi/40) for k in range(41)])
    p = FNC.polyinterp(t,f(t))
    assert isclose(p(-0.12345), f(-0.12345))

def test_triginterp():
    f = lambda x: np.exp(np.sin(np.pi*x))
    n = 30
    t = np.array([ 2*k/(2*n+1) for k in range(-n,n+1) ])
    p = FNC.triginterp(t,f(t))
    assert isclose(p(-0.12345), f(-0.12345))
    t = np.array([ k/n for k in range(-n,n) ])
    p = FNC.triginterp(t,f(t))
    assert isclose(p(-0.12345), f(-0.12345))

def test_ccint():
    F = lambda x: np.tan(x/2-0.2)
    f = lambda x: 0.5/np.cos(x/2-0.2)**2
    assert isclose(FNC.ccint(f,40)[0], F(1)-F(-1))

def test_glint():
    F = lambda x: np.tan(x/2-0.2)
    f = lambda x: 0.5/np.cos(x/2-0.2)**2
    assert isclose(FNC.glint(f,40)[0], F(1)-F(-1))

def test_intinf():
    f = lambda x: 1/(32+2*x**4)
    assert isclose(FNC.intinf(f,1e-9)[0], np.sqrt(2)*np.pi/32, rtol=1e-5)

def test_intsing():
    f = lambda x: (1-x)/( np.sin(x)**0.5 )
    assert isclose(FNC.intsing(f,1e-8)[0], 1.34312, rtol=1e-5)
