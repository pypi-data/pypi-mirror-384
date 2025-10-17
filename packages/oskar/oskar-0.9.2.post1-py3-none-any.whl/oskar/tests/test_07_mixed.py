#!/usr/bin/env python
"""Test finite element solution for basic equations.

Test consistency and convergence for all cell types using MMS.
"""
from bs4 import _s
import numpy as np
import pygimli as pg
from oskar import (div, grad, OP,
                   derive, parse, solve, norm, normL2, normSemiH1, asFunction,
                   ScalarSpace, VectorSpace, FEASolution, TaylorHood)

from oskar.tests.utils import (compSolve, parseTestArgs)
from oskar.tests import TestCollection, assertEqual, testCount
from oskar.utils import convergenceRate, drawConvergenceOrder

import logging
logging.getLogger('distributed').setLevel(30) # Warning

pg.setThreadCount(1)
__tests__ = {}

_show_ = False


class TestFEAMixedFormulation(TestCollection):

    def test_Stationary(self):
        """MMS for mixed formulation for stationary problem.

        TODO
        ----
            * Pure Neumann case
            * Gradient version
            * 1D, 3D
            * convergency test
            * patch test
            * strong form conversion
        """
        p = asFunction('cos(x*5)*cos(5*y)')
        vz = asFunction('-2, +2.')
        alpha = 42.0
        q = -alpha * (grad(p) + vz)

        x = np.linspace(0, 1, 10)
        mesh = pg.createGrid(x, x)

        f = div(q)

        #%% [markdown]
        s = ScalarSpace(mesh, p=1, order=3)
        v = VectorSpace(mesh, p=2, order=3, dofOffset=s.dofs.stop)

        L = v*alpha**-1.0*v - div(v)*s - s*div(v) == -v*vz - s*f  # ok
        bcV={'assemble': {'*': -v*p*norm(v)}}
        bcS={'fix': [[0.0, 0.0], p(0.0, 0.0)]}

        ph, qh = solve(L, bc={s:bcS, v:bcV}, solver='scipy')

        if _show_ is True:
            fig, ax  = pg.plt.subplots(2, 2, figsize=(10, 10))

            p.show(ax=ax[0, 0], mesh=mesh)
            q.show(ax=ax[0, 1], mesh=mesh)
            ph.show(ax=ax[1, 0])
            qh.show(ax=ax[1, 1])

        self.assertEqual(normL2(ph-p), 0.0, tol=8.3e-3)
        self.assertEqual(normL2(qh-q), 0.0, tol=8.4)

        bcV={'assemble': {'*': -v*p*norm(v)}}
        L = [v*alpha**-1.0*v - div(v)*s == -v*vz,
             - s*div(v) == -s*f]
        bcV={'assemble': {'*': -v*p*norm(v)}}
        compSolve(L, bc = {s:bcS, v:bcV}, solver='scipy',
                  ref=[ph, qh])

        L = [v*alpha**-1.0*v - div(v)*s == -v*vz, # ok
             s*div(v) == s*f]
        bcV={'assemble': {'*': -v*p*norm(v)}}
        compSolve(L, bc = {s:bcS, v:bcV}, solver='scipy',
                  ref=[ph, qh])

        L = v*v - div(v)*alpha*s - s*div(v) == -v*alpha*vz - s*f # ok but slower
        bcV={'assemble': {'*': -v*alpha*p*norm(v)}}
        compSolve(L, bc = {s:bcS, v:bcV}, solver='scipy',
                  ref=[ph, qh])

        ## Concatenated and half signs flipped
        L = v*v - div(v)*alpha*s + s*div(v) == -v*alpha*vz + s*f # ok but slower
        bcV={'assemble': {'*': -v*alpha*p*norm(v)}}
        compSolve(L, bc = {s:bcS, v:bcV}, solver='scipy',
                  ref=[ph, qh])

        ## List and all signs flipped
        L = [s*div(v) == s*f, -v*alpha**-1.0*v + div(v)*s == v*vz] #ok
        bcV={'Neumann': {'*': v*p}} # natural condition !pos. like div(v)*s!


if __name__ == '__main__':
    _show_ = parseTestArgs()

    import unittest
    pg.tic()
    unittest.main(exit=False)

    print()
    pg.info(f'Absolut tests: {testCount()}, took {pg.dur()} s')
