#!/usr/bin/env python
"""Test for miscellaneous basic functionality."""
import sys
import traceback

import numpy as np
import pygimli as pg
import oskar as oc

from oskar import (ScalarSpace, VectorSpace, FEASolution,
                   asFunction, div, grad, laplace, solve)
from oskar.tests import testCount, TestCollection


class TestMisc(TestCollection):
    """Test miscellaneous stuff."""

    def test_Unsorted(self):
        """Test unsorted miscellaneous stuff that needs to be sorted anywhere."""
        print(oc.__version__)
        self.assertEqual(oc.__version__, oc.version())


    def test_AssignmentName(self):
        """Test oskar.utils.getInstanceAssignmentName."""
        # check for class instance
        class Foo:
            """Dummy class."""

            def __init__(self):
                self.name = oc.utils.getInstanceAssignmentName('foo')
        a = Foo()
        self.assertEqual(a.name, 'a')

        # take the first possible
        def foobar():
            return oc.utils.getInstanceAssignmentName()
        name = foobar()
        self.assertEqual(name, 'name')

        # productive test
        a = oc.asFunction('x')
        self.assertEqual(a.name, 'a')

        self.assertEqual(oc.asFunction('x').name, 'dummy_0')


    def test_assertEqual(self):
        """Test the tester."""
        self.assertEqual(None, None)
        self.assertRaises(AssertionError, self.assertEqual, 0, None)
        self.assertRaises(AssertionError, self.assertEqual, None, 0)

        M1 = pg.core.RMatrix(3,3)
        for i in range(3):
            M1.setVal(i, np.ones(3)*100)

        M2 = pg.core.RDenseMatrix(M1)
        M3 = pg.matrix.asSparseMatrix(M1)
        M4 = pg.matrix.asSparseMapMatrix(M1)

        for A in [M1, M2, M3, M4]:
            B = A + 1e-5
            self.assertEqual(A, A)
            self.assertRaises(AssertionError, self.assertEqual, A, B)
            self.assertRaises(AssertionError, self.assertEqual, A, B, atol=1e-5)
            self.assertEqual(A, B, atol=9.9e-4)

            C = A*(1 + 1e-8)
            self.assertRaises(AssertionError, self.assertEqual, A, C)
            self.assertRaises(AssertionError, self.assertEqual, A,C,rtol=9.9e-9)
            self.assertEqual(A, C, rtol=1e-8)


        mesh = pg.createGrid(5)
        s = ScalarSpace(mesh)
        u = asFunction('x')
        uh = FEASolution(s, u)

        for L in [s,
                  uh,
                  u,
                  1+u,
                  1+uh,
                  -div(uh),
                  div(u),
                  grad(uh),
                  grad(u),
                  ]:

            try:
                self.assertEqual(L, L)
            except AssertionError:
                pg._r(L)
                traceback.print_exc(file=sys.stdout)
                return


    def test_pickling(self):
        """Test manual pickling of some classes."""
        import pickle

        def _tst(a):
            """Generic pickle tester."""
            p = pickle.dumps(a)
            b = pickle.loads(p)
            self.assertEqual(a, b)
            return b

        mesh = pg.createGrid(5,5)
        s = ScalarSpace(mesh)
        u = asFunction('x')
        uh = FEASolution(s, u)

        uh = solve(laplace(s)==1, bc={'Dirichlet': {0:1}})
        # _tst(s)
        # _tst(u)
        _tst(uh)

        v = VectorSpace(mesh)
        u = asFunction('x, y')
        uh = FEASolution(v, u)

        uh = solve(laplace(v)==1, bc={'Dirichlet': {0:[1, 1]}})
        #print(uh.valueSize(), uh.valSize)
        b = _tst(uh)
        #print(b.valueSize(), b.valSize)
        self.assertEqual(uh.valSize, b.valSize)


    def test_quadratureRules(self):
        """Test integration for all available quadrature rules."""
        def testIntegrate(c, u, x, w, I, tol):
            Ih = 0
            for i, x in enumerate(x):
                Ih += u(x)*w[i]*c.size()

            try:
                print('.', end='', flush=True)
                self.assertEqual(I, Ih, tol=tol)

            except AssertionError:
                pg._g(c)
                pg._g(u)
                pg._g(I)
                pg._y(Ih)
                pg._r(I-Ih)
                pg.critical('quadrature rule test failed.')

        def testIntegrateEdge(c, u, x, w, tol):
            """Integrate a function on an unit Edge.

               ([0,0],[0,1]).
            """
            I = oc.integrate(u, d='x', limits=[0, 1])
            testIntegrate(c, u, x, w, I(0), tol)

        def testIntegrateTriangle(c, u, x, w, tol):
            """Integrate a function on an unit Triangle.

            ([0,0],[1.0],[0,1]).
            """
            I = oc.integrate(u, d=['x', 'y'], limits=[[0, '1-y'], [0, 1]])
            testIntegrate(c, u, x, w, I(0), tol)

        def testIntegrateTet(c, u, x, w, tol):
            """Integrate a function on an unit Tetrahedron.

            ([0,0,0],[1,0,0],[0,1,0],[0,0,1]).
            """
            I = oc.integrate(u, d=['x', 'y', 'z'],
                        limits=[[0, '1-y-z'], [0, '1-z'], [0, 1]])
            testIntegrate(c, u, x, w, I(0), tol)

        def testIntegrateQuad(c, u, x, w, tol):
            """Integrate a function on an unit Quadrangle.

            ([0,0],[1,0],[1,1],[0,1]).
            """
            I = oc.integrate(u, d=['x', 'y'], limits=[[0, 1], [0, 1]])
            testIntegrate(c, u, x, w, I(0), tol)

        def testIntegrateHex(c, u, x, w, tol):
            """Integrate a function on an unit Hexahedron.

            ([0,0,0],[1.0,0],[1,1,0],[0,1,0],[0,0,1],[1.0,1],[1,1,1],[0,1,1]).
            """
            I = oc.integrate(u, d=['x', 'y', 'z'],
                             limits=[[0, 1], [0, 1], [0, 1]])
            testIntegrate(c, u, x, w, I(0), tol)

        def testIntegrateTriPrism(c, u, x, w, tol):
            """Integrate a function on an unit Triangular Prism.

            ([0,0,0],[1.0,0],[0,1,0],[0,0,1],[1.0,1],[0,1,1]).
            """
            I = oc.integrate(u, d=['x', 'y', 'z'],
                             limits=[[0, ('1-y')], [0, 1], [0, 1]])
            testIntegrate(c, u, x, w, I(0), tol)

        for order in range(1, 10):
            x = pg.core.IntegrationRules.instance().gauAbscissa(order)
            w = pg.core.IntegrationRules.instance().gauWeights(order)

            nx, nw = np.polynomial.legendre.leggauss(order)

            for i, xi in enumerate(x):
                #print(x[i][0], nx[i], w[i], nw[i])
                self.assertEqual(xi[0], nx[i], tol=1.2e-16)
                self.assertEqual(nw[i], nw[i])

        edge = pg.createGrid(2)
        for order in range(1, 10):
            x, w = oc.quadratureRules(edge.cell(0).shape(), order, show=False)
            u = oc.asFunction(f'(x)^{order}')
            testIntegrateEdge(edge.cell(0), u, x, w, tol=6e-17)

        quad = pg.createGrid(2,2)
        for order in range(1, 10):
            u = oc.asFunction(f'(x + y)^{order}')
            x, w = oc.quadratureRules(quad.cell(0).shape(), order, show=False)
            testIntegrateQuad(quad.cell(0), u, x, w, tol=1.8e-15)

        tri = pg.meshtools.refineQuad2Tri(quad)
        for order in range(1, 6):
            u = oc.asFunction(f'(x + y)^{order}')
            x, w = oc.quadratureRules(tri.cell(0).shape(), order, show=False)
            testIntegrateTriangle(tri.cell(0), u, x, w, tol=1.4e-16)

        Hex = pg.createGrid(2,2,2)
        for order in range(1, 10):
            u = oc.asFunction(f'(x + y + z)^{order}')
            x, w = oc.quadratureRules(Hex.cell(0).shape(), order, show=False)
            testIntegrateHex(Hex.cell(0), u, x, w, tol=5.2e-13)

        tet = pg.meshtools.refineHex2Tet(Hex)
        for order in range(1, 6):
            u = oc.asFunction(f'(x + y + z)^{order}')
            x, w = oc.quadratureRules(tet.cell(0).shape(), order, show=False)
            testIntegrateTet(tet.cell(0), u, x, w, tol=6.0e-16)

        pri = pg.meshtools.extrude(tri, z=[0,1])
        for order in range(1, 6):
            u = oc.asFunction(f'(x + y + z)^{order}')
            x, w = oc.quadratureRules(pri.cell(0).shape(), order, show=False)
            testIntegrateTriPrism(pri.cell(0), u, x, w, tol=8.9e-16)

        print()


    def test_shapeFunctions(self):
        """Create and test shape functions."""
        # Lagrange bilinear quadrilateral
        oc.fitShapeFunctions('(a + b*x + c*y + d*x*y)' ,
                              dof=[[0.0, 0.0], [1.0, 0.0],
                                   [1.0, 1.0], [0.0, 1.0]])

        # # Lagrange biquadratic quadrilateral
        oc.fitShapeFunctions(    '            a '
                                  '+    b*x    +   c*y'
                                  '+ d*x²  + e*x*y  + f*y²'
                                  '+   g*x²*y  +   h*x*y²'
                                  '+        i*x²*y²',
                       dof=[[0.0, 0.0], [0.5, 0.0], [1.0, 0.0],
                            [0.0, 0.5], [0.5, 0.5], [1.0, 0.5],
                            [0.0, 1.0], [0.5, 1.0], [1.0, 1.0]])


    def test_FEASolutionOP_subst(self):
        """Test FEASolutionOP substitution."""
        s = oc.ScalarSpace(pg.createGrid(2, 2), p=2)
        u = oc.asFunction('x² + y')
        uh = oc.FEASolution(s, u)
        pnt = [0.5, 0.5]

        #### START DEBUG WORKSPACE ############################################

        # def F(x):
        #     return x**3
        # F1 = F(uh)
        # F2 = F(uh).subst(uh, uh + 42.42)
        # self.assertEqual(F1(pnt), F(u)(pnt), atol=3e-13)
        # self.assertEqual(F2(pnt), F(u + 42.42)(pnt), atol=3e-13)
        #### END DEBUG WORKSPACE ############################################

        for F in [
                    lambda x: x + 2,
                    lambda x: x + 2*x,
                    lambda x: x*x + 2*x,
                    lambda x: 1/x + 2*x,
                    lambda x: 1/(x + 2*x),
                    lambda x: x**3 + 2*x,
                    lambda x: 2.0 * (3.3/(4.4 + abs(x)**1.4)),
                    lambda x: 2.0 * (3.3 - 4.4) / (5.5 + abs(x)**0.4) + 6.6,
                    #lambda x: log(x + 2*x),
                ]:

            # test eval
            F1 = F(uh)
            F2 = F(uh).subst(uh, uh + 42.42)
            self.assertEqual(F1(pnt), F(u)(pnt), atol=3e-13)
            self.assertEqual(F2(pnt), F(u + 42.42)(pnt), atol=3e-13)



if __name__ == '__main__':
    import unittest
    pg.tic()
    unittest.main(exit=True)
    print()
    pg.info(f'Absolut tests: {testCount()}, took {pg.dur()} s')
