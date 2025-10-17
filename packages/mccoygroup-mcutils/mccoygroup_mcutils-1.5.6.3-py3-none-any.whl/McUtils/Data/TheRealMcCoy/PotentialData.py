import scipy.special as funcs, numpy as np

data = {}

def harmonic(r, *, re=1, freq=1, mass=1, deriv_order=None):
    r = np.asanyarray(r)
    c = r - re
    k = (mass*(freq**2))
    vals = k/2 * c**2
    if deriv_order is not None:
        vals = [vals]
        for n in range(1, deriv_order+1):
            if n == 1:
                vals.append(k*c)
            elif n == 2:
                if not isinstance(k, np.ndarray):
                    k = np.full(r.shape, k)
                vals.append(k)
            else:
                vals.append(np.zeros(r.shape))
    return vals
data['HarmonicPotential'] = {
        "Name":"HarmonicPotential",
        "Parameters":{
            "re":"Equilibrium bond length",
            "freq":"Frequency of the oscillator",
            "mass":"Mass of the oscillator"
        },
        "Defaults":{
            "re":1,
            "freq":1,
            "mass":1
        },
        "Function": harmonic
    }

def morse(r, *, re=1, De=1, alpha=1, deriv_order=None):
    r = np.asanyarray(r)
    c = alpha * (r - re)
    vals = De * (1 - np.exp(-c)) ** 2
    if deriv_order is not None:
        vals = [vals]
        for n in range(1, deriv_order+1):
            d = (-1) **(n + 1) *( 2 * De * alpha**n) * np.exp(-2 * c) * (np.exp(c) - (2**(n - 1)))
            vals.append(d)
    return vals
data["MorsePotential"] = {
        "Name":"MorsePotential",
        "Parameters":{
            "re":"Equilibrium bond length",
            "De":"Dissociation energy",
            "alpha":"Width of the well"
        },
        "Defaults":{
            "re":1,
            "De":1,
            "alpha":1
        },
        "Function": morse
    }