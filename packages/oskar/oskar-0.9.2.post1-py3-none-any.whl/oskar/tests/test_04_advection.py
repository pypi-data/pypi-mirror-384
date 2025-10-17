#!/usr/bin/env python
r"""Test for miscellaneous basic functionality."""
import numpy as np
import pygimli as pg

from oskar.tests.utils import (compSolve, parseTestArgs)
from oskar.tests import assertEqual, testCount, TestCollection

from oskar.tests.closedForms import fundamentalSolution

from oskar import (FEAFunction3,
                   AdvectionDiffusionSolver,
                   ScalarSpace,
                   asFunction,
                   comparingLabels,
                   dirac, solve,
                   solveAdvectionDiffusion,
                   derive, laplace, grad,
                   normL2, normSemiH1,
                   )

import scipy.integrate as integrate

_show_ = False


def _solveAdvectionDiffusion(*args, ref=None, **kwargs):
    """call ADV process solver for core/useMats."""
    pg._g('solveAdvectionDiffusion', args, kwargs)
    pg.tic()
    u1 = solveAdvectionDiffusion(*args, **kwargs, core=False)
    pg.toc('core=False')
    if ref is not None:
        assertEqual(u1, ref)

    pg.tic()
    u2 = solveAdvectionDiffusion(*args, **kwargs, core=True)
    pg.toc('core=True')
    assertEqual(u1, u2)

    pg.tic()
    u3 = solveAdvectionDiffusion(*args, **kwargs, useMats=True)
    pg.toc('useMats=True')
    assertEqual(u1, u3)

    return u1


class TestAdvection(TestCollection):
    """Tests for the AdvectionDiffusion process solver."""

    def test_01_ImpulseResponse(self):
        """Test AdvectionDiffusionSolver with impulse response."""
        show = _show_
        pg.info('testImpulseResponse')
        x = np.linspace(-5, 5, 200)
        t = np.linspace(0, 1, 101)
        mesh = pg.createGrid(x)
        v = 2.0
        D = 0.2
        lam = 0.2

        # compare with impulse response of the fundamental solution
        c = fundamentalSolution()(D=D, lam=lam, v=v)
        ic = dirac(rs=[0.0, 0.0], cellScale=True)

        chR = _solveAdvectionDiffusion(mesh, v=v, D=D, lam=lam,
                                      bc={'Dirichlet':{'*':0}},
                                      ic=ic, times=t)

        ad = AdvectionDiffusionSolver(mesh, v=v, D=D, lam=lam,
                                      bc={'Dirichlet':{'*':0}})
        ch = ad.solve(ic=ic, times=t)

        assertEqual(chR, ch)

        if show:
            ax = pg.show()[0]
            ax.arrow(0, 0, 0., 1, width=0.05, head_width=0.1, lw=0, color='k')
            ax.plot(x, c(x, t=t[-1]), label='Fundamental solution')
            ax.plot(x[::5], ch(x[::5], t=t[-1]), lw=0.5, marker='.',
                    label='Oskar')
            ax.set(xlabel='x', ylabel='Concentration $c$',
                title='Concentration after 1s')
            ax.grid()
            ax.legend()

        assertEqual(normL2(c-ch), 0.005777207485583308, atol=1e-12)


    def test_02_SmithHutton(self):
        r""" The Smith-Hutton problem.

        R. M. Smith and A. G. Hutton.
        The numerical treatment of advection:
        a performance comparison of current methods.
        Numerical Heat Transfer, 5:439–461, 1982. DOI: 10.1080/10407798208546996

        TODO
        ----
            * add benchmark notebook
        """
        show = _show_
        pg.info('testSmithHutton')

        x = np.linspace(-1.0, 1.0, 41)
        y = np.linspace( 0.0, 1.0, 15)

        mesh = pg.createGrid(x=x, y=y)

        for b in mesh.boundaries(mesh.boundaryMarkers() == 3):
            if b.center()[0] > 0:
                b.setMarker(5)

        vel = asFunction('2*y * (1-x²), -2*x * (1-y²)')

        x = np.linspace(0., 1.0, 21)

        if show is True:
            fig, axs = pg.plt.subplots(1, 2, figsize=(8,4))
            axs[1].plot([0, 0.5, 0.5, 1.0], [2.0, 2.0, 0.0, 0.0], ':',
                        label='exact')

        alpha = 1000.
        Peclet = 100.0 # vel/diffus
        Gamma = 1./Peclet # nearly no Diffusion

        bc = {'Dirichlet' :{'1,2,4': lambda p: 1. - np.tanh(alpha),
                            3: lambda p: 1. + np.tanh(alpha * (2 * p[0] + 1.))},
            }

        u = _solveAdvectionDiffusion(mesh, v=vel, D=Gamma, bc=bc,
                                     supg=False, times=None)

        if show is True:
            axs[1].plot(x, u(x), '-o', label='FEA')

        assertEqual(integrate.quad(u, 0.0, 0.5)[0], 1.0, atol=0.183)
        assertEqual(integrate.quad(u, 0.5, 1.0)[0], 0.0, atol=0.115)

        u = _solveAdvectionDiffusion(mesh, v=vel, D=Gamma, bc=bc,
                                     supg=True, times=None)

        if show is True:
            axs[1].plot(x, u(x), '-o', label='FEA-supg')
            u.show(ax=axs[0], label='u')

        assertEqual(integrate.quad(u, 0.0, 0.5, epsabs=1e-5)[0], 1.0, atol=0.25)
        assertEqual(integrate.quad(u, 0.5, 1.0)[0], 0.0, atol=0.143)


        ### Finite Volume Reference
        bc = {'Dirichlet' :{'1,2,4': lambda b_: 1. - np.tanh(alpha),
              3: lambda b_: 1. + np.tanh(alpha * (2 * b_.center()[0] + 1.))},
            'Neumann' : {5:0}
                }

        v = np.array(list(map(vel, mesh.cellCenters())))
        schemes=['UDS', 'HS', 'PS']
        for scheme in schemes:
            u = pg.solver.solveFiniteVolume(mesh, a=Gamma,
                                            vel=v, bc=bc,
                                            scheme=scheme)
            if show is True:
                axs[1].plot(x, pg.interpolate(mesh, u, x=x), '-o', label='FV-'+scheme)

        if show is True:
            axs[1].legend()
            axs[1].grid(True)

            pg.show(mesh, v, ax=axs[0])


    def test_03_DoneaHuerta(self):
        """See steady_convection DoneaHuerta chapter 2.2.2 benchmark
        """
        pg.info('testDoneaHuerta')
        show = _show_

        u = asFunction(u='1/a * (x - (1-exp(g * x))/(1-exp(g)))',
                       g='a/nu')[0]

        coth = lambda x: 1/np.tanh(x)
        cosh = lambda x: np.cosh(x)

        for var in [1, 2, 3, 4]:
            if show == True:
                fig, ax = pg.plt.subplots(1,1)

            xS = np.linspace(0, 1, 101)

            for nX, p in [[11, 1], [6, 2]]:

                x = np.linspace(0, 1, nX)
                mesh = pg.createGrid(x)

                r = 1 # sourceTerm

                ### Note. Reusing s for different Pe might lead to eratic
                ### caching problems .. fix me! with better testing and caching.
                s = ScalarSpace(mesh, p=p)

                bc = {'Dirichlet':{'*':0}}

                for i, Pe in enumerate([0.25, 0.9, 5.0]):
                    a = 5
                    h = min(pg.utils.diff(pg.sort(pg.x(s.mesh))))
                    nu = a/Pe * h/2

                    L = None
                    if var == 1:
                        ### Simple  Galerkin
                        L = s*a*grad(s) + grad(s)*nu*grad(s) == s*r

                        nL2H1 =[[
                        [0.000916895, 0.045386843], # var:1 Pe:0.25 p:1
                        [0.006273472, 0.271128810], # var:1 Pe:0.9 p:1
                        [0.040626229, 1.241083868], # var:1 Pe:5.0 p:1
                        ],[
                        [0.000290347, 0.011172247], # var:1 Pe:0.25 p:2
                        [0.004601184, 0.164408854], # var:1 Pe:0.9 p:2
                        [0.039035163, 1.218954133], # var:1 Pe:5.0 p:2
                        ]]

                    elif var == 2:
                        #### 2.3.1 Galerkin upwind approximation
                        L = s*a*grad(s) + grad(s)*(nu + (a*h/2))*grad(s) == s*r

                        ### [[L2,H1]_p1, [L2,H1]_p2]
                        nL2H1 = [[0.00, 0.0],
                                 [0.00, 0.0]]
                        nL2H1 =[[
                        [0.009383388, 0.060852835], # var:2 Pe:0.25 p:1
                        [0.018223403, 0.290761161], # var:2 Pe:0.9 p:1
                        [0.033407225, 0.429653129], # var:2 Pe:5.0 p:1
                        ],[
                        [0.009128053, 0.046050263], # var:2 Pe:0.25 p:2
                        [0.017205772, 0.239619204], # var:2 Pe:0.9 p:2
                        [0.031395111, 0.286700073], # var:2 Pe:5.0 p:2
                        ]]

                    elif var == 3:
                        #### 2.3.2 Petrov-Galerkin with upwind
                        beta = 1.0   # same line var == 2
                        L = (s + (beta*(h/2))*grad(s))*a*grad(s) + grad(s) * nu*grad(s) == s*r
                        nL2H1 =[[
                        [0.009383388, 0.060852835], # var:3 Pe:0.25 p:1
                        [0.018223403, 0.290761161], # var:3 Pe:0.9 p:1
                        [0.033407225, 0.429653129], # var:3 Pe:5.0 p:1
                        ],[
                        [0.009128053, 0.046050263], # var:3 Pe:0.25 p:2
                        [0.017205772, 0.239619204], # var:3 Pe:0.9 p:2
                        [0.031395111, 0.286700073], # var:3 Pe:5.0 p:2
                        ]]

                    elif var == 4:
                        #### 2.3.2 Petrov-Galerkin with upwind
                        beta = coth(Pe) - 1/Pe  # Streamline upwind approximation (SUPG)

                        if p == 2:
                            beta = np.zeros(s.mesh.nodeCount())
                            beta0 = coth(Pe) - 1/Pe
                            betaCorner = (beta0 - cosh(Pe)**2 * (coth(2*Pe) - 1/(2*Pe)))/ \
                                            (1-cosh(Pe)**2/2)

                            for c in s.mesh.cells():

                                beta[c.node(0).id()] = betaCorner
                                beta[c.node(1).id()] = betaCorner
                                beta[c.node(2).id()] = beta0

                        L = (s + (beta*(h/2))*grad(s)) *a*grad(s) + grad(s) * nu*grad(s) == s*r
                        nL2H1 =[[
                        [0.001309945, 0.045168849], # var:4 Pe:0.25 p:1
                        [0.007798760, 0.254982364], # var:4 Pe:0.9 p:1
                        [0.031321715, 0.455165721], # var:4 Pe:5.0 p:1
                        ],[
                        [0.000289615, 0.011087862], # var:4 Pe:0.25 p:2
                        [0.004481294, 0.151609205], # var:4 Pe:0.9 p:2
                        [0.027758461, 0.341618133], # var:4 Pe:5.0 p:2
                        ]]

                    # test for assemblation variants
                    try:
                        print(L)
                        # deactivated until reworked stabilizations
                        uh = solve(L == 0, bc=bc, solver='scipy', useMats=True)
                        #uh = solve(L == 0, bc=bc, solver='scipy', core=True)
                        #uh = compSolve(L, bc=bc, solver='scipy')
                        #continue

                    except BaseException as e:
                        print(e)
                        pg._r(f'var={var}, Pe={Pe}, p={p}')
                        pg._r('L:', L)
                        pg._r('bc:', bc)


                    # uh = solveAdvectionDiffusion(....)
                    # assertEqual(uh, uh_)

                    # to create references
                    if show:
                        print('[{0:.9f}, {1:.9f}], '
                              '# var:{2} Pe:{3} p:{4}'.format(
                            normL2(u(a=a, nu=nu) - uh),
                            normSemiH1(u(a=a, nu=nu) - uh), var, Pe, p))

                    try:
                        assertEqual(normL2(u(a=a, nu=nu) - uh),
                                    nL2H1[p-1][i][0], atol=1e-5)
                        assertEqual(normSemiH1(u(a=a, nu=nu) - uh),
                                    nL2H1[p-1][i][1], atol=1e-5)
                    except BaseException as e:
                        print(e)
                        pg._r(f'var={var}, Pe={Pe}, p={p}')
                        print(nL2H1[p-1][i])
                        normL2(u(a=a, nu=nu) - uh)
                        normSemiH1(u(a=a, nu=nu) - uh)
                        #return

                    # TODO test about known working versions
                    # np.testing.assert_allclose(normL2(u - uh), errL2[p-1][i], atol=1e-14)
                    # np.testing.assert_allclose(normH2(u - uh), errH2[p-1][i], atol=1e-14)

                    if show is True:
                        ax.plot(xS, u(a=a, nu=nu)(xS), ':',
                                    color='k', lw=1, alpha=0.5,
                                    #label=f'exact Pe={Pe}'
                                    )
                        ax.plot(pg.x(s.mesh), uh(pg.x(s.mesh)), 'o',
                                    color=f'C{i}',
                                    label=f'Galerkin Pe={Pe}, '
                                          r'$u_{\rm h}$'+f'var={var}, p={p}')
                        ax.plot(xS, uh(xS), '-', color=f'C{i}')

                        ax.legend()
                        ax.grid(True)

    def test_04_OgataBanks(self):
        """Unsteady test"""
        show = _show_
        pg.info('testOgataBanks')

        c = asFunction('cD/2*(erfc((x-v*t)/sqrt(4*D*t)) + '
                       'exp(x*v/D)*erfc((x+v*t)/sqrt(4*D*t)))')
        cD = 10
        D = 0.02
        v = 0.07
        xMax = 50
        x = np.linspace(0, xMax, 51)
        mesh = pg.createGrid(x)
        tMax = 500
        #t = np.linspace(0, tMax, 1000)  # new times
        t = [0, *np.geomspace(1, tMax, 100)]   # new times

        L = lambda u: derive(u, 't') - D * laplace(u) + v*grad(u)
        s = ScalarSpace(mesh, order=2)
        bc = {'Dirichlet':{1:cD}}
        pg.tic()
        ch = solve(L(s) == 0, ic=0, bc=bc, times=t,
                   theta=0.5, solver='scipy')

        ch = solveAdvectionDiffusion(mesh, v=v, D=D, supg=False, bc=bc,
                                     times=t, theta=0.5, ref=ch)

        pg.toc('solve')

        if show:
            fig, axs = pg.plt.subplots(1,1)
            for i, ti in enumerate([t[1], 0.2*tMax, 0.5*tMax, 0.8*tMax, t[-1]]):
                axs.plot(x/xMax, c(x, t=ti, D=D, cD=cD, v=v)/cD,
                         label=f't={ti/tMax}', c=f'C{i}')
                axs.plot(x/xMax, ch(x, t=ti)/cD, '-', marker='.', lw=0.5, c=f'C{i}',
                         label=f't={ti/tMax}')
            axs.set(xlabel=r'$x/x_{\rm max}$', ylabel=r'$c/c_{\rm D}$')
            axs.legend(*comparingLabels(axs, ['OgataBanks', 'Oskar']))
        # pg.tic()
        # Th = solveAdvectionDiffusion(mesh, D=alpha, v=v, times=t, supg=False,
        #                      bc=bc, theta=0.5)
        # pg.toc('adv')



if __name__ == '__main__':

    _show_ = parseTestArgs()

    import unittest

    pg.tic()
    unittest.main(exit=True)

    print()
    pg.info(f'Absolut tests: {testCount()}, took {pg.dur()} s')
