#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Test for miscellaneous basic functionality.
"""
import numpy as np
import pygimli as pg

from oskar.tests.utils import (compSolve)
from oskar.tests import assertEqual, testCount, TestCollection

from oskar.tests.closedForms import terzaghi

from oskar import (DirichletManager,
                   LinSolver,
                   FEAFunction3,
                   PoroElasticitySolver,
                   solvePoroElasticity,
                   solveThermoPoroElasticity,
                   ScalarSpace, VectorSpace,
                   FEASolution,
                   asFunction,
                   applyBoundaryConditions,
                   comparingLabels,
                   div, grad, sym, tr, I,
                   dirac, solve,
                   solveAdvectionDiffusion,
                   derive, laplace, grad,
                   normL2, normSemiH1,
                   )

import scipy.integrate as integrate

_show_ = False


class TestTHM(TestCollection):
    """Tests for the AdvectionDiffusion process solver."""

    def testHMT_CMP_Var(self):
        r"""Test the poroelasticity solver."""
        """"""
        show = _show_
        pg.info('testThermoPoroElasticity (vars)')

        L = 5           # soil column length
        kappa = 1e-9    # permeability coefficient
        phi = 0.2       # porosity
        alphaB = 0.5    # Biot-Willis coefficient

        lam = 40        # First Lame parameter in MPa
        mu = 40         # Second Lame parameter in MPa
        betaF = 4.4e-4
        betaS = 4.4e-5
        Ss = phi*betaF + (alphaB-phi)*betaS # Storativity
        cv = 4000
        kappa=1e-3
        betaV=1e-4
        Ku=1e3

        z = np.linspace(0, L, 21)
        mesh = pg.meshtools.createGrid(z)

        c = kappa / (Ss + alphaB**2 * 1/(lam + 2*mu)) #vert. consolid. coeff

        t = np.asarray([0, *np.geomspace(1e-3*L**2/c,
                                         10*L**2/c, 51)])

        bcU = {'Dirichlet':{1:[None, 0.0],
                            2:[0.0, 0.0],
                            3:[None, 0.0],
                            4:[None, 0.0],
                        },
                'Neumann': {1:[0, 0.0]}
                }
        bcP = {'Dirichlet':{1:0}}
        bcT = {'Dirichlet':{1:10}}

        print()
        pg.info('ThermoPoroElasticitySolver (var=1)')

        th, ph, uh = solveThermoPoroElasticity(mesh, times=t, K=kappa,
                                                lam=lam, mu=mu,
                                                Ss=Ss, alphaB=alphaB,
                                                cv=cv, kappa=kappa,
                                                betaV=betaV, Ku=Ku,
                                                bcP=bcP, bcU=bcU, bcT=bcT,
                                         var=1)
        print()
        pg.info('ThermoPoroElasticitySolver (var=2)')
        thT, phT, uhT = solveThermoPoroElasticity(mesh, times=t, K=kappa,
                                                lam=lam, mu=mu,
                                                Ss=Ss, alphaB=alphaB,
                                                cv=cv, kappa=kappa,
                                                betaV=betaV, Ku=Ku,
                                                bcP=bcP, bcU=bcU, bcT=bcT,
                                                var=2)

        self.assertEqual(th, thT)
        self.assertEqual(ph, phT)
        self.assertEqual(uh, uhT)


    def testHM_Terzaghi(self):
        r"""Test the poroelasticity solver."""
        """"""
        show = _show_
        pg.info('testPoroElasticity: Terzaghi')

        def test_(mesh, L, p0, bcP, bcU):

            kappa = 1e-9    # permeability coefficient
            phi = 0.2       # porosity
            alphaB = 0.5    # Biot-Willis coefficient

            lam = 40        # First Lame parameter in MPa
            mu = 40         # Second Lame parameter in MPa
            betaF = 4.4e-4  # Fluid compressibility in 1/MPa
            betaS = 4.4e-5  # Solid grain compressibility in 1/MPa

            lam *= 1e6  #in Pa
            mu *= 1e6   #in Pa
            betaF /= 1e6 # in 1/Pa
            betaS /= 1e6 # in 1/Pa
            Ss = phi*betaF + (alphaB-phi)*betaS # Storativity

            # normalized times
            c = kappa / (Ss + alphaB**2 * 1/(lam + 2*mu)) #vert. consolid. coeff
            t = np.asarray([0, *np.geomspace(5e-4*L**2/c,
                                            2*L**2/c, 11)])

            pg.info('PoroElasticitySolver (var=1)')
            pg.tic()
            phR, uhR = solvePoroElasticity(mesh, times=t, K=kappa, lam=lam, mu=mu,
                                        Ss=Ss, alphaB=alphaB,
                                        bcP=bcP, bcU=bcU, var=1)
            pg.toc()
            print()
            pg.info('PoroElasticitySolver (var=2)')
            pg.tic()
            ph, uh = solvePoroElasticity(mesh, times=t, K=kappa, lam=lam, mu=mu,
                                        Ss=Ss, alphaB=alphaB,
                                        bcP=bcP, bcU=bcU, var=2)

            #pg._g(normL2(ph.values-phR.values)/phR.values)
            pg.toc()

            self.assertEqual(ph, phR, rtol=3e-9)
            self.assertEqual(uh, uhR, rtol=5e-12)

            print()
            pg.info('PoroElasticitySolver (core=True)')
            pg.tic()

            phT, uhT = solvePoroElasticity(mesh, times=t, K=kappa, lam=lam, mu=mu,
                                        Ss=Ss, alphaB=alphaB,
                                        bcP=bcP, bcU=bcU, var=2, core=True)
            pg.toc()
            self.assertEqual(ph, phT, rtol=2e-9)
            self.assertEqual(uh, uhT)

            print()
            pg.info('PoroElasticitySolver (core=False)')
            pg.tic()

            phT, uhT = solvePoroElasticity(mesh, times=t, K=kappa, lam=lam, mu=mu,
                                        Ss=Ss, alphaB=alphaB,
                                        bcP=bcP, bcU=bcU, var=2, core=False)
            pg.toc()
            self.assertEqual(ph, phT, rtol=1.1e-9)
            self.assertEqual(uh, uhT)

            # compare with Terzaghi
            t = np.asarray([0, *np.geomspace(5e-4*L**2/c,
                                             2*L**2/c, 101)])

            ph, uh = solvePoroElasticity(mesh, times=t, K=kappa, lam=lam, mu=mu,
                                         Ss=Ss, alphaB=alphaB,
                                         bcP=bcP, bcU=bcU, var=2)

            z = np.linspace(0, L, 41)
            p, u = terzaghi(z, tau=0.1, kappa=kappa, alpha=alphaB,
                            betaF=betaF, betaS=betaS,
                            lam=lam, mu=mu, phi=phi, L=L, N=21)

            self.assertEqual(ph(z, t=0.1*L**2/c)/p0, p, atol=0.041)
            self.assertEqual(uh(z, t=0.1*L**2/c)[:,0], u, atol=0.007)

            if _show_:

                fig, axs = pg.plt.subplots(1, 2, figsize=(12,4))

                tau = [0.001, 0.01, 0.1, 0.5, 1, 2]

                for i, ti in enumerate(tau):
                    p, u = terzaghi(z, tau=ti, kappa=kappa, alpha=alphaB,
                                    betaF=betaF, betaS=betaS,
                                    lam=lam, mu=mu, phi=phi, L=L, N=21)

                    lbl = dict(label=r'$\tau=$'+f'{ti}', c=f'C{i}')
                    axs[0].plot(p, z/L, **lbl, lw=1)
                    axs[0].plot(ph(z, t=ti*L**2/c)/p0, z/L, '.', **lbl)
                    #axs[0].plot(phR(z, t=ti*L**2/c)/p0, z/L, 'x', **lbl)

                    axs[1].plot(u*p0, z/L, **lbl, lw=1)
                    axs[1].plot(uh(z, t=ti*L**2/c)[:,0], z/L, '.', **lbl)
                    #axs[1].plot(uhR(z, t=ti*L**2/c)[:,0], z/L, 'x', **lbl)

                axs[0].legend(*comparingLabels(axs[0],['Terzahgi', 'Oskar']))
                axs[0].grid(True)
                axs[0].yaxis.set_inverted(True)
                axs[0].set(ylabel='$z/L$', xlabel='pore pressure $p$ in Pa')

                axs[1].legend(*comparingLabels(axs[0],['Terzahgi', 'Oskar']))
                axs[1].grid(True)
                axs[1].yaxis.set_inverted(True)
                axs[1].set(ylabel='$z/L$', xlabel='displacement $u_z$ in mm')
                fig.tight_layout()

        L = 2           # soil column length
        p0 = 1e6  # reference pressure
        z = np.linspace(0, L, 51)
        bcU = {'Dirichlet':{1:[None, 0.0, 0.0],
                            2:[0.0, 0.0, 0.0],
                            3:[None, 0.0, 0.0],
                            4:[None, 0.0, 0.0],
                        },
                'Neumann': {1:[-p0, 0.0, 0.0]}
                }
        bcP = {'Dirichlet':{1:0}}

        mesh = pg.meshtools.createGrid(z)
        test_(mesh, L, p0, bcP, bcU)
        mesh = pg.meshtools.createGrid(z, [-0.1, 0.1])
        test_(mesh, L, p0, bcP, bcU)
        mesh = pg.meshtools.createGrid(z, [-0.1, 0.1], [-0.1, 0.1])
        test_(mesh, L, p0, bcP, bcU)


if __name__ == '__main__':

    import sys
    if 'show' in sys.argv:
        sys.argv.remove('show')
        _show_ = True

    import unittest
    pg.tic()
    unittest.main(exit=True)

    print()
    pg.info(f'Absolut tests: {testCount()}, took {pg.dur()} s')
