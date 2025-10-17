#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import unittest

import pygimli as pg
import numpy as np

from oskar import (ScalarSpace, PDE,
                   grad, div, laplace, solve, asAnisotropyMatrix,
                   )
from oskar.tests.utils import TestCollection, assertEqual, compSolve


_show_ = False

class TestAnisotropy(unittest.TestCase):

    def test_compare_simple(self, show=False):
        """Simple test with single anisotropy matrix."""
        pg.tic()

        grid = pg.createGrid(x=np.linspace(0.0, 2*np.pi, 11),
                             y=np.linspace(0.0, 2*np.pi, 11))

        #grid = pg.meshtools.refineQuad2Tri(grid)

        if _show_ is True:
            fig, axs = pg.plt.subplots(nrows=2, ncols=2,
                                       figsize=(10,10), squeeze=True)
            axs = axs.flatten()

        for i, th in enumerate([None, 0, 45, 90]):

            if th is None:
                C = 1.0
            else:
                C = asAnisotropyMatrix(1.0, 10.0, theta=th/360 * (2*np.pi))

            bc = {'Dirichlet':{'*':0}}
            f = 1.0
            #### p1
            u = ScalarSpace(grid, p=1)
            uh = compSolve(grad(u) * C*grad(u) == u*f, bc=bc, atol=2e-12)

            #### p2
            u = ScalarSpace(grid, p=2, order=4)
            uh = compSolve(grad(u) * C*grad(u) == u*f, bc=bc,atol=6e-12)

            if _show_ is True:
                if th is not None:
                    label = r'u (c: Long/Trans = 10, $\theta={0}$'.format(th)
                else:
                    label = 'u (c: isotrope)'
                pg.show(uh, label=label, ax=axs[i])


    def test_cell_list(self):
        """Test per cell anisotropy matrix."""
        x = np.linspace(0.0, 1.0, 5)
        mesh = pg.createGrid(x, x)

        bc = {'Dirichlet':{'*':0}}
        f = 1.0
        C = 2.0
            #### p1
        s = ScalarSpace(mesh, p=1)
        uR = solve(C*laplace(s) == f, bc=bc)

        C = asAnisotropyMatrix(2.0, 2.0)
        compSolve(-grad(s)*C*grad(s) == s*f, bc=bc, atol=6e-12, ref=uR) #ok
        compSolve(div(C*grad(s)) == f, bc=bc, atol=6e-12, ref=uR) #ok
        # fails but unsure if this even makes sense
        # compSolve(C*laplace(s) == f, bc=bc, atol=2e-12, ref=uR)

        C = [asAnisotropyMatrix(2.0, 2.0)] * mesh.cellCount()
        compSolve(-grad(s)*(C*grad(s)) == s*f, bc=bc, atol=6e-12, ref=uR)
        compSolve(div(C*grad(s)) == f, bc=bc, atol=6e-12, ref=uR) #todo
        # fails but unsure if this even makes sense
        # compSolve(C*laplace(s) == f, bc=bc, atol=2e-12, ref=uR)


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

    # test = TestAnisotropy()
    # test.test_compare_simple(show=True)
    # #unittest.main()
