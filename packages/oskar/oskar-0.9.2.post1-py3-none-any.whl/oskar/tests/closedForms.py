#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Closed form solutions for verification.
"""
import numpy as np
import pygimli as pg
from oskar import parse


def fundamentalSolution(D:str='D', v:str='v', lam:str='lam', dim:int=1):
    r"""Return a fundamental solution.

    Create and return the fundamental solution (Green's function)
    for a partial differential equation with advection, diffusion and
    decay term.
    See :ref:`userguide-verification-mes-greens`.

    .. math::

        \partial_t c - D \Delta c + v \nabla c + \lambda c

    with

    .. math::

        G(x,t) = \frac{1}{(4\pi D t)^{\frac{\rm dim}{2}}}
            \operatorname{e}^{\left(-\frac{(x - v t)^2}{4 D t}\right)}
            \operatorname{e}^{-\lambda t}

    The solution is given in the form of a FEAFunction which can be evaluated
    with discrete values.

    Arguments
    ---------
    D: str='D'
        Variable name for the diffusion coefficient in m²/s.
    v: str='v'
        Variable name for Flow velocity in m/s.
    lam: str='lam'
        Variable name Decay rate in 1/s.
    dim: int=1
        Dimension of the problem (1, 2 or 3).

    Returns
    -------
    G: FEAFunction
        Function handle for the fundamental solution.

    """
    G = parse(G=f'1/(4*pi*{D}*t)**(dim/2)'
                f'*exp(-(x-{v}*t)²/(4*{D}*t))'
                f'*exp(-{lam}*t)',
              dim=dim)[0]
    return G


def terzaghi(z, t=None, tau=None, kappa=1e-6, alpha=1,
             betaF=4.41e-10, betaS=5e-11,
             lam=40e4, mu=40e4, phi=0.2, L=1, N=21):
    r"""Terzaghi's consolidation equation.

    Calculate the pore water pressure and displacement for the consolidation
    of an one dimensional soil column with unit surface load after
    :cite:`Terzaghi1925`:

    .. math::
        p =\:& p_0\frac{2}{L}\sum_n^\infty\frac{1}{\xi}
            \operatorname{e}^{-\xi^2 c t}
            \operatorname{sin}(\xi z)\\
        u =\:& u_0 + \alpha_{\rm B} c_M\,p_0 \left[(L-z)
            - \frac{2}{L}\sum_n^\infty\frac{1}{\xi²}
            \operatorname{e}^{-\xi^2 c t}
            \operatorname{cos}(\xi z)\right]\\[10pt]

    with

    .. math::
        \xi =\:& \frac{\pi(2 n + 1)}{2 L}\\[10pt]
        p_0 =\:& \frac{\alpha_{\rm B} M}{K_{\rm u} + \frac{4}{3}\mu}\\[10pt]
        u_0 =\:& \frac{L-z}{K_{\rm u} + \frac{4}{3}\mu} \\[10pt]

    and

    .. math::
        \text{Vertical consolidation coefficient:}~c=\:&
            \kappa\frac{1}{\frac{1}{M} + \alpha_{\rm B}^2 c_M}\\
        \text{Biot's modulus:}~M=\:&
              \frac{1}{\phi \beta_{\rm f}
            + (\alpha_{\rm B}-\phi)\beta_{\rm s}}\\[10pt]
        \text{Vertical uniaxial compressibility:}~c_M=\:&
            \frac{1}{\lambda + 2 \mu}\\[10pt]
        \text{Undrained bulk modulus:}~K_{\rm u}=\:&
            \lambda + \frac{2}{3}\mu + \alpha_{\rm B}^2 M

    Either a time :math:`t` in s or a dimensionless time :math:`\tau`
    needs to be given where:

    .. math::

        \tau = \frac{c\,t}{L^2}

    TODO
    ----
        * Converge slowly for small times :math:`\tau < 0.04`, implement
    :cite:`CarslawJaeger1980` p. 97 if needed.
        * Implement symbolic solution to explain the alpha in the displacement.

    Arguments
    ---------
    z: float| [float]
        Depth in m.
    t: float| [float]
        Time in s.
    tau: float| [float]
        Dimensionless time.
    kappa: float[1e-6]
        Permeability coefficient :math:`\kappa/\eta` in m/s,
        hydraulic permeability :math:`k` and dynamic viscosity :math:`\eta`
    alpha: float [1]
        Biot-Willis coefficient in [1].
    betaF: float [2e-10]
        Fluid compressibility in 1/Pa.
    betaS: float [5e-11]
        Solid compressibility in 1/Pa.
    lam: float [40e6]
        First Lamé-coefficient in Pa.
    mu: float [40e6]
        Second Lamé-coefficient in Pa.
    phi: float [0.2]
        Porosity in [1].
    L: float | [1.0]
        Soil column depth.
    N: int [21]
        Iteration order for the Fourier sine series representation.

    Returns
    -------
    p: float|[float]
        Pore water pressure :math:`p = p(z,t)`.
    u: float|[float]
        Displacement in :math:`z` direction :math:`u = u_z(z,t)`.

    Example
    -------
    >>> import numpy as np
    >>> import pygimli as pg
    >>> import oskar
    >>> from oskar.tests.closedForms import terzaghi
    >>> fig, axs = pg.plt.subplots(1, 2, figsize=(8,4))
    >>> L = 10
    >>> z = np.linspace(0, L, 51)
    >>> tau = [1, 0.4, 0.1, 0.04, 0.01]
    >>> p, u = terzaghi(z, tau=tau, L=L, N=21)
    >>> axs[0].plot(p.T, z/L) # doctest: +ELLIPSIS
    [...]
    >>> axs[1].plot(u.T, z/L) # doctest: +ELLIPSIS
    [...]
    >>> axs[0].set(xlabel='$p/p_0$ in Pa', ylabel='z/L') # doctest: +ELLIPSIS
    [...]
    >>> axs[1].set(xlabel='$u_z$ in m', ylabel='z/L') # doctest: +ELLIPSIS
    [...]
    >>> fig.suptitle('Terzaghi consolidation for dimensionless time τ')
    ... # doctest: +ELLIPSIS
    T...
    >>> for a in axs:
    ...     a.yaxis.set_inverted(True)
    ...     a.legend([r'$\tau='+ f'{t}$' for t in tau]) # doctest: +ELLIPSIS
    ...     a.grid()
    <...>
    """
    z = np.atleast_1d(z)

    c_M = 1/(lam + 2*mu)        # vertical uniaxial compressibility in 1/Pa
    M = 1/(phi*betaF + (alpha-phi)*betaS)   # Biot modulus in Pa

    c = kappa/(1/M + alpha**2*c_M)          # consolidation coefficient
    Ku = lam + 2/3 * mu + alpha**2 * M      # undrained bulk modulus in Pa

    p0 = alpha * M / (Ku + 4/3*mu)
    u0 = (L-z) / (Ku + 4/3*mu)

    if tau:
        t = np.atleast_1d(np.atleast_1d(tau)/c*L**2)
    else:
        t = np.atleast_1d(t)

    if t is None:
        pg.critical('No time given.')

    p = []
    u = []
    for ti in t:

        sumTermP = 0
        sumTermU = 0

        for m in range(N):
            xi = np.pi/(2*L) * (2*m + 1)
            ExXi = np.exp(-(xi**2*c*ti))
            sumTermP += 1/xi * ExXi * np.sin(xi * z)
            sumTermU += 1/xi**2 * ExXi * np.cos(xi * z)

        p.append(p0 * 2/L * sumTermP)
        # original
        # u.append(c_M * p0 * ((L-z) - 2/L * sumTermU) + u0)

        ### without the alpha the numeric tests for u fail.
        ### TODO: symbolic Terzaghi to explain
        u.append(alpha*c_M * p0 * ((L-z) - 2/L * sumTermU) + u0)

    return np.squeeze(p), np.squeeze(u)


def advectionDiffReactSun1998(x, t, k, D, v, R=1, c0=1):
    r"""Multiple species reactive transport.

    Calculate analytical solutions for multiple (:math:`n`) species reactive
    transport in multiple dimensions after :cite:`SunEtAl1999`.

    .. math::

        R\partial_t c_i
            - \nabla\cdot(D \nabla c_i)
            + \boldsymbol{v} \nabla c_i
            + k_i c_i
            = k_{i-i} c_{i-1} \quad\forall\quad i = 1\ldots n\\

    **Limitations**

        * Retardation factor :math:`R` constant
        * Dispersion :math:`D` constant
        * Velocity :math:`v` constant
        * Only 1D (x) at the moment. Flexibilise if needed.
        * Only impulse response at the origin. Flexibilise if needed.

    ====================== ================================================= ========================================
    Symbol                 Description                                       Dimension
    ====================== ================================================= ========================================
    :math:`t`              time                                              :math:`\mathsf{\Theta}`
    :math:`c_i`            concentration of :math:`i`-th species             :math:`\mathsf{M}\cdot\mathsf{L}^{-3}`
    :math:`\boldsymbol{v}` flow velocity                                     :math:`\mathsf{L}\cdot\mathsf{T}^{-1}`
    :math:`D`              dispersion coefficient                            :math:`\mathsf{L}^2\cdot\mathsf{T}^{-1}`
    :math:`k_i`            first order reaction rate of :math:`i`-th species :math:`\mathsf{T}^{-1}`
    :math:`R`              retardation factor                                :math:`\mathsf{1}`
    ====================== ================================================= ========================================

    Arguments
    ---------
    x: [float, ]
        Spatial coordinates in m.
    t: float
        Time in s.
    k: [float, ]
        List of first order reaction rates :math:`k_i` for each species.
    D: float
        Dispersion coefficient
    v: float
        Flow velocity
    R: float
        Retardation factor
    c0: [float, ]
        Initial concentration for all species at the origin.

    Returns
    -------
    c: [np.ndarray, ]
        List of concentrations for each species at time :math:`t` on profiles
        :math:`x`.

    Example
    -------
    >>> import numpy as np
    >>> import pygimli as pg
    >>> import oskar
    >>> from oskar.tests.closedForms import advectionDiffReactSun1998
    >>> R = 1
    >>> D = 0.18
    >>> v = 0.2 # cm/h
    >>> k = [0.05, 0.03, 0.02]
    >>> c0 = [1, 0.0, 0.0]
    >>> x = np.linspace(0, 40, 101)
    >>> c = advectionDiffReactSun1998(x, 400, k=k, D=D,
    ...                               v=v, R=R, c0=c0)
    >>> fig, ax = pg.plt.subplots()
    >>> ax.plot(x, c[0], lw=1, color='C0', label='C1') # doctest: +ELLIPSIS
    [...]
    >>> ax.plot(x, c[1], lw=1, color='C1', label='C2') # doctest: +ELLIPSIS
    [...]
    >>> ax.plot(x, c[2], lw=1, color='C2', label='C3') # doctest: +ELLIPSIS
    [...]
    >>> ax.set(xlabel='Distance in cm', ylabel='relative concentration') # doctest: +ELLIPSIS
    [...]
    >>> ax.legend() # doctest: +ELLIPSIS
    <matplotlib.legend.Legend object at ...>
    >>> ax.grid()
    >>> fig.suptitle(r'Sun et al. 1999 ($\approx$ Figure 1)') # doctest: +ELLIPSIS
    Text...
    >>> print(c[2][-1]) ## just for testing # doctest: +ELLIPSIS
    0.08958839...
    """
    def _aux(c, k, i=None):

        def prod(j, i, k, c):
            ret = 1.0
            for l in range(j, i):
                ret *= k[l] / (k[l] - k[i])

            return ret*c[j]

        if i is None:
            a = np.zeros_like(c)
            for i in range(1, len(c)):
                for j in range(i):
                    a[i] += prod(j, i, k, c)
        else:
            if i == 0:
                return 0
            a = np.zeros_like(c[i-1])
            for j in range(i):
                a += prod(j, i, k, c)

        return a

    c = parse(c='c0/2 * exp((v*x) / (2*D))*('
            '  exp(-beta * x)*erfc((x - sqrt((v² + 4*k*D))*t)/sqrt((4*D*t)))'
            '+ exp( beta * x)*erfc((x + sqrt((v² + 4*k*D))*t)/sqrt((4*D*t)))'
            ')',
            beta = 'sqrt((v²/(4*D²) + k/D))')[0]

    k = np.asarray(k)
    c0 = np.asarray(c0)

    if len(k) != len(c0):
        pg.critical('k and c0 need to have the same length.')

    a0 = c0 + _aux(c0, k/R)
    cA = []

    for i, ki in enumerate(k):
        ai = c(x, t=t, v=v/R, D=D/R, k=ki/R, c0=a0[i])
        cA.append(ai - _aux(cA, k/R, i=i))

    return np.asarray(cA)
