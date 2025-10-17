#!/usr/bin/env python
"""Test assembling of basic finite element expressions."""
import sys
import numpy as np
import pygimli as pg

import oskar
from oskar.elementMats import (uE, dotE, duE, mulE, copyE, identityE, setMat)
from oskar import (FEAFunction, FEAFunction3, FEASolution,
                   ScalarSpace, VectorSpace, ConstantSpace, TaylorHood,
                   asAnisotropyMatrix,
                   dirac, grad, div, norm, sym, tr, trace,
                   I, identity,
                   normL2, normSemiH1,
                   applyBoundaryConditions,
                   strain, stress,
                   solve, parse, asFunction,
                   DZ)

from oskar.op import OP
from oskar.feaFunction import FEAFunctionDotNorm
from oskar.tests import assertEqual, testCount, TestCollection
from oskar.feaOp import findForms, FEAOP, formToExpr

from oskar.tests.utils import _assemble, _testExp
from oskar.units import Parameters, ParameterDict
from oskar.utils import asPosListNP
from oskar.elasticity import createElasticityMatrix, asNoMapping, asVoigtMapping


def createTestMeshs():
    """Create some test meshes for linear shape functions."""
    m0 = pg.createGrid(x=np.linspace(0.0, 1.0, 3)) # in use?

    x = np.linspace(0.0, 1.0, 5) # #num < 5 lead to ambiguities. Fixme
    # 1D with 4 cells
    m1 = pg.createGrid(x=x)

    x = np.linspace(0.0, 1.0, 3)
    # 2D quad with 4 cells
    m2 = pg.createGrid(x=x, y=x)
    # 2D tri with 4 cells
    m3 = pg.meshtools.refineQuad2Tri(m2)

    # 3D hex with 8 cells
    m4 = pg.createGrid(x=x, y=x, z=x)
    # 3D tet with 8 cells
    m5 = pg.meshtools.refineHex2Tet(m4)
    return [m0, m1, m2, m3, m4, m5]


def deepDebug(L, var=0, exitEnd=True, useMats=True):
    """Test assembling of expression with more debugging infos.

    Calls exit after run as syntactic sugar to stop running the code.

    Args
    ----
    L:
        FEA Expression

    var: int [0]
        Give deep debug infos about the run variant.

        1. use python implementation

        2. use core implementation

        3. use implementation using matrices

    exitEnd: bool [True]
        Don't exit the run.

    useMats: bool [True]
        Compare if useMats mode.

    """
    pg._b('+'*60)

    pg.boxprint('apply(0) core=False')
    if var == 1:
        pg.core.setDeepDebug(-1)

    l1 = L.apply(0)
    pg.core.setDeepDebug(0)
    print(l1)

    pg.boxprint('apply(0) core=True')
    if var == 2:
        pg.core.setDeepDebug(-1)

    l2 = L.apply(0, core=True)
    pg.core.setDeepDebug(0)
    print(l2)

    assertEqual(l1, l2)

    L1 = L.assemble()
    L2 = L.assemble(core=True)

    assertEqual(L1, L2)

    if useMats is True:
        if var == 3:
            pg.core.setDeepDebug(-1)

        L3 = L.assemble(useMats=True)
        pg.core.setDeepDebug(0)

        print(L1)
        print(L2)
        print(L3)

        assertEqual(L2, L3)

        pg._b('-'*60)

    if exitEnd is True:
        sys.exit()


class TestFiniteElementBasics(TestCollection):
    """Test for some finite element basics."""

    def test_ElementMatrices(self):
        """Test element matrices against a different implementation from pg."""
        def _testU(c, orders):
            """Private to test linear form: integrate u."""
            uT = pg.core.ElementMatrix()
            uR = pg.core.ElementMatrix(nCoeff=1, dofPerCoeff=0, dofOffset=0)

            for o in orders:
                u = uE(c, order=o)
                uR.pot(c, o, sum=True)
                self.assertEqual(u, uR)

                uT = pg.core.ElementMatrix()
                uT.u(c)

                self.assertEqual(u.ids(), uT.ids())
                self.assertEqual(u.col(0), uT.mat().row(0), atol=1e-12)

        def _testU2(c, orders):
            """Private to test bilinear form: integrate <u, u>."""
            uR = pg.core.ElementMatrix(nCoeff=1, dofPerCoeff=0, dofOffset=0)
            #print(c)
            for o in orders:

                u = uE(c, order=o)
                uu = dotE(u, u, c=1e5)
                uR.pot(c, o, sum=True)
                uuR = pg.core.dot(uR, uR, c=1e5)

                self.assertEqual(uu, uuR)

                for K in [1e-14, 1.0, 1e14]:
                    uu = dotE(u, u, c=K)
                    uuR = pg.core.dot(uR, uR, c=K)
                    self.assertEqual(uu, uuR)

                uu = dotE(u, u, c=1.0)
                uT = pg.core.ElementMatrix()
                uT.u2(c)

                self.assertEqual(uu.ids(), uT.ids())
                self.assertEqual(uu.mat(), uT.mat(), atol=1e-12)

        def _testdUdU(c, orders):
            """Private to test bilinear form: integrate <grad u, grad u>."""
            du2 = pg.core.ElementMatrix(nCoeff=1, dofPerCoeff=0, dofOffset=0)

            for order in orders:
                du = duE(c, order=order)
                du2.grad(c, order, elastic=False, sum=True)
                self.assertEqual(du, du2)

                dudu = dotE(du, du)
                dudu2 = pg.core.dot(du2, du2, c=1.0)
                self.assertEqual(dudu, dudu2)

                uT = pg.core.ElementMatrix()
                uT.ux2uy2uz2(c)

                self.assertEqual(dudu.ids(), uT.ids())
                self.assertEqual(dudu.mat(), uT.mat(), atol=1e-12)

                ### test mult * f
                ## f == f(p) in v3
                @FEAFunction3
                def vel(p):
                    return [0.5 + pg.x(p), 0.5 + pg.y(p), 0.5 + pg.z(p)]

                vdU = mulE(du, vel)
                vdU2 = pg.core.mult(du2, b=vel)
                self.assertEqual(vdU, vdU2)

                u = uE(c, order=order)
                uvdu = dotE(u, vdU)
                du2.setValid(False)
                du2.pot(c, order, sum=True)
                uvdu2 = pg.core.dot(du2, vdU2, c=1.0)

                self.assertEqual(uvdu, uvdu2)
                uvdu = dotE(vdU, u)
                uvdu2 = pg.core.dot(vdU2, du2, c=1.0)
                self.assertEqual(uvdu, uvdu2)

                #### test for constitutive matrix ##############################
                if c.dim() == 2:
                    # IMPLEMENTME
                    return

                C = createElasticityMatrix(E=1, nu=0.1, dim=c.dim(),
                                           voigtNotation=True)
                ## create python reference solution
                dvR = duE(c, order=order, nCoeff=c.dim(),
                          dofPerCoeff=c.nodeCount(), dofOffset=0,
                          elastic=True)
                dvC = pg.core.ElementMatrix(nCoeff=c.dim(),
                                            dofPerCoeff=c.nodeCount(),
                                            dofOffset=0)
                dvC.grad(c, order, elastic=True, sum=True)

                self.assertEqual(dvR, dvC)

                ## compare with core version
                dvCdvR = dotE(dvR, dvR, c=C)
                #pg._g(dvCdvR)

                #pg._r('###########################')
                dvCdvC = pg.core.dot(dvC, dvC, C)
                #pg._y(dvCdvC)

                self.assertEqual(dvCdvR, dvCdvC)

                dvCC = pg.core.mult(dvC, C)

                # pg._y(dvCC)
                # pg._g(dvC)

                dvCdvC = pg.core.dot(dvCC, dvC)
                #exit()

                # pg._r(dvCdvC)
                self.assertEqual(dvCdvR, dvCdvC)

        x = np.linspace(0.0, 1.0, 2)
        quad = pg.createGrid(x=x, y=x)
        tri = pg.meshtools.refineQuad2Tri(quad)

        quad2 = quad.createP2()
        tri2 = tri.createP2()

        hexa = pg.createGrid(x=x, y=x, z=x)
        hexa2 = hexa.createP2()
        tet = pg.meshtools.refineHex2Tet(hexa)
        tet2 = tet.createP2()

        _testU(tri.cell(0), orders=[3, 4, 5])
        _testU(tri.cell(0), orders=[3, 4, 5])
        _testU2(tri.cell(0), orders=[2, 3, 4, 5])
        _testdUdU(tri.cell(0), orders=[1, 2, 3, 4, 5])

        _testU(tri2.cell(0), orders=[2, 3, 4, 5])
        _testU2(tri2.cell(0), orders=[4, 5])
        _testdUdU(tri2.cell(0), orders=[2, 3, 4, 5])

        _testU(quad.cell(0), orders=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        _testU2(quad.cell(0), orders=[2, 3, 4, 5, 6, 7, 8, 9])
        _testdUdU(quad.cell(0), orders=[2, 3, 4, 5, 6, 7, 8, 9])

        _testU(quad2.cell(0), orders=[2, 3, 4, 5, 6, 7, 8, 9])
        _testU2(quad2.cell(0), orders=[3, 4, 5, 6, 7, 8, 9])
        _testdUdU(quad2.cell(0), orders=[3, 4, 5, 6, 7, 8, 9])

        _testU(tet.cell(0), orders=[1, 2, 3, 4, 5])
        _testU2(tet.cell(0), orders=[2, 3, 4, 5])
        _testdUdU(tet.cell(0), orders=[1, 2, 3, 4, 5])

        _testU(tet2.cell(0), orders=[2, 3, 4, 5])
        _testU2(tet2.cell(0), orders=[4, 5])
        _testdUdU(tet2.cell(0), orders=[2, 3, 4, 5])

        _testU(hexa.cell(0), orders=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        _testU2(hexa.cell(0), orders=[2, 3, 4, 5, 6, 7, 8, 9])
        _testdUdU(hexa.cell(0), orders=[2, 3, 4, 5, 6, 7, 8, 9])

        _testU(hexa2.cell(0), orders=[2, 3, 4, 5, 6, 7, 8, 9])
        _testU2(hexa2.cell(0), orders=[3, 4, 5, 6, 7, 8, 9])
        _testdUdU(hexa2.cell(0), orders=[3, 4, 5, 6, 7, 8, 9])

        #assertEqual(1, 2)


    def test_FEA_VectorSpace_Elements(self):
        """Basic element matrix tests for vector spaces.
        """
        x = np.linspace(0.0, 1.0, 2)
        mesh = pg.createGrid(x=x, y=x)

        mesh = pg.meshtools.refineQuad2Tri(mesh)
        v = VectorSpace(mesh, p=1, order=1)
        u = ScalarSpace(mesh, p=1, order=1)
        c = v.mesh.cell(0)

        ### vector | load ######################################################
        # f = pg.Pos(1.0, 2.0)
        # v.useCore = False
        # vf = (v*f).apply(0)  # reference version
        # print(vf)
        # v1 = v.uE(c)
        # vf1 = mulE(v1, f)
        # print(vf1)

        # f = np.diag([f[0], f[1]])
        # vf1 = mulE(v1, f)
        # print(vf1)

        # exit()

        ### vector + mass ######################################################
        #
        vv1 = (v*v).apply(0)  # reference version
        v2 = v.createElementMatrix()
        v2.pot(c, v.order)
        vv2 = pg.core.dot(v2, v2, c=1.0)
        self.assertEqual(vv1, vv2)

        ### vector | mass | Matrix #############################################
        #
        # reference version
        f = np.array([[1.0, 2.0], [3.0, 4.0]])
        vR = v.uE(c)
        vfvR = dotE(vR, vR, c=f)
        # core version (dot)
        vC = v.createElementMatrix()
        vC.pot(c, v.order)

        vfvC = pg.core.dot(vC, vC, f) # A.T * (f*A)
        self.assertEqual(vfvR, vfvC)

        # core version (dot(mult))
        vfC = pg.core.mult(vC, f) # f*A

        vfvC = pg.core.dot(vC, vfC, c=1.0) # A.T * (f*A)
        self.assertEqual(vfvR, vfvC)

        vfvC = pg.core.dot(vfC, vC, c=1.0) # (f*A).T * A
        self.assertEqual(vfvR.T, vfvC)

        # KI = np.array([[1./1e-10, 0.],
        #                [0., 1./1e-10]])
        # vKv = pg.core.dot(v2, v2, KI)
        # print(vKv)
        # KI = 1/1e-10
        # vKv = pg.core.dot(v2, v2, KI)
        # print(vKv)

        # exit()

        ### vector + grad ######################################################
        dv = v.gradE(c)
        dvdv = dotE(dv,dv)

        m = np.zeros((dv.rows(), dv.rows()))

        mi = [[-1,  1, 0,  0,  0, 0], #dvx/dx
              [ 0, -1, 1,  0,  0, 0], #dvx/dy
              [ 0,  0, 0, -1,  1, 0], #dvy/dx
              [ 0,  0, 0,  0, -1, 1], #dvy/dy
              ]
        mi = np.array(mi)
        for i, w in enumerate(dv._w):
            m += mi.T @ mi * w * dv.entity().size()

        dvdv.setMat(m)
        self.assertEqual(np.array(dvdv.mat()),
                         np.array((grad(v)*grad(v)).apply(0).mat()))

        m *= 0
        dudu = (grad(u)*grad(u)).apply(0)
        m[0:3,0:3] = dudu.mat()
        m[3:6,3:6] = dudu.mat()
        self.assertEqual(np.array(dvdv.mat()), m)
        ###

        dv2 = (grad(v)).apply(0)  # reference version
        dv3 = v.createElementMatrix()
        dv3.grad(c, v.order, sum=True)  # core version

        self.assertEqual(dv2, dv3)

        dvdv2 = dotE(dv2, dv2)
        dvdv3 = pg.core.dot(dv3, dv3, c=1.0)
        self.assertEqual(dvdv2, dvdv3)

        ### vector + grad + Matrix #############################################
        #
        # IMPLEMENTME
        # dv2f = mulE(dv2, f)
        # print(dv2f)
        # v*KI*v
        # vdv2 = dotE(dv2, dv2, f)
        # print(vdv2)
        # exit()
        # dv3f = pg.core.mult(dv3, f)
        # dvdv3 = pg.core.dot(dv3f, dv3)
        # print(dvdv3)
        # self.assertEqual(dvdv2, dvdv3)

        ### Mixed + grad #######################################################
        v = VectorSpace(mesh, p=2, order=4)
        u = ScalarSpace(mesh, p=1, order=4)
        cu = u.mesh.cell(0)
        cv = v.mesh.cell(0)
        du1 = u.gradE(cu)
        v1 = v.uE(cv)
        duv1 = dotE(du1, v1)

        du2 = u.createElementMatrix()
        du2.grad(cu, u.order, sum=True)
        v2 = v.createElementMatrix()
        v2.pot(cv, u.order, sum=True)
        duv2 = pg.core.dot(du2, v2, c=1.0)
        self.assertEqual(duv1, duv2)

        duv1 = dotE(v1, du1)
        duv2 = pg.core.dot(v2, du2, c=1.0)
        self.assertEqual(duv1, duv2)

        ### Mixed + div ########################################################
        v = VectorSpace(mesh, p=1, order=1)
        u = ScalarSpace(mesh, p=1, order=1)
        D1 = (div(v)*u).apply(0)
        D2 = (u*div(v)).apply(0)
        # print(D1)
        self.assertEqual(np.array(D1.mat()), np.array(D2.mat()).T)

        ref = np.array([[-1/6, -1/6, -1/6],
                        [+1/6, +1/6, +1/6],
                        [   0,    0,    0],
                        [   0,    0,    0],
                        [-1/6, -1/6, -1/6],
                        [+1/6, +1/6, +1/6],
               ])
        self.assertEqual(np.array(D1.mat()), ref, atol=1e-15)

        u = ScalarSpace(mesh, p=1, order=4)
        v = VectorSpace(mesh, p=2, order=4, dofOffset=u.dof)

        u1 = u.uE(u.mesh.cell(0))
        v1 = v.uE(v.mesh.cell(0))
        dv1 = v.gradE(v.mesh.cell(0), isDivergence=True)

        u2 = u.createElementMatrix()
        v2 = v.createElementMatrix()
        dv2 = v.createElementMatrix()

        u2.pot(u.mesh.cell(0), u.order, sum=True)
        v2.pot(v.mesh.cell(0), v.order, sum=True)
        dv2.grad(v.mesh.cell(0), v.order, sum=True, div=True)

        self.assertEqual(u1, u2)
        self.assertEqual(v1, v2)
        self.assertEqual(dv1, dv2)

        self.assertEqual(dotE(u1, dv1), pg.core.dot(u2, dv2))
        self.assertEqual(dotE(dv1, u1), pg.core.dot(dv2, u2))

        ### Start testing for change of indexing order
        # v, p = TaylorHood(mesh)
        # bc = {v:{'assemble': {'*': -v*norm(v)}}}
        # v1, p1 = solve(v*v - div(v)*p - p*div(v) == p*f, bc=bc)

        # p = ScalarSpace(mesh, order=4, p=1)
        # v = VectorSpace(mesh, order=4, p=2, dofOffset=p.dof)
        # bc = {v:{'assemble': {'*': -v*norm(v)}}}
        # vt, pt = solve(v*v - div(v)*p - p*div(v) == p*f, bc=bc)

        # np.testing.assert_almost_equal(pt.eval(), p1.eval())
        # np.testing.assert_almost_equal(vt.eval(), v1.eval())


    def test_CreateLoadVector(self):
        """Basic element matrix tests for linear form.
        """
        x = np.linspace(0.0, 1.0, 2)
        mesh = pg.createGrid(x=x, y=x)
        mesh = pg.meshtools.refineQuad2Tri(mesh)

        p = ScalarSpace(mesh, p=2, order=3)
        f = FEAFunction(lambda p: -pg.x(p))
        #p = VectorSpace(mesh, p=1, order=None)

        #### START DEBUG WORKSPACE ############################################
        # L = -p*f
        # L = f*p
        # L = p*f
        # print(findForms(L))


        # _assemble(L)
        # return
        #### END DEBUG WORKSPACE ##############################################

        rhs = pg.Vector(p.dof)

        for c in p.mesh.cells():
            c = p.mesh.cell(c.id())
            cE = p.uE(c, f=f)
            rhs[cE.rowIDs()] += cE.col(0)

        ref = np.sort([1/120,  0.025, -0.025, -1/6, -1/15,
                       -1/30, -1/120, -1/7.5, -0.1])
        self.assertEqual(ref, np.sort(rhs))
        self.assertEqual(ref, np.sort((f*p).assemble()))
        self.assertEqual(ref, np.sort((p*f).assemble()))

        self.assertEqual(-ref[::-1], np.sort((-p*f).assemble(core=True)))
        self.assertEqual(-ref[::-1], np.sort((-f*p).assemble(core=True)))
        self.assertEqual(-ref[::-1], np.sort((p*-f).assemble(core=True)))
        self.assertEqual(-ref[::-1], np.sort((f*-p).assemble(core=True)))
        self.assertEqual(-ref[::-1], np.sort((-p*f).assemble(core=False)))
        self.assertEqual(-ref[::-1], np.sort((-f*p).assemble(core=False)))
        self.assertEqual(-ref[::-1], np.sort((p*-f).assemble(core=False)))
        self.assertEqual(-ref[::-1], np.sort((f*-p).assemble(core=False)))

        f = FEAFunction(lambda _p: pg.x(_p))
        fN = FEASolution(p, values=f(p.mesh.positions()))

        self.assertEqual((p*f).assemble(core=False),(p*fN).assemble(core=False))
        self.assertEqual((p*f).assemble(core=True), (p*fN).assemble(core=True))


    def test_CreateNeumann(self):
        """Basic element matrix tests for assembling on boundary elements.
        """
        x = np.linspace(0.0, 1.0, 2)
        mesh = pg.createGrid(x=x, y=x)
        mesh = pg.meshtools.refineQuad2Tri(mesh)

        p = ScalarSpace(mesh, p=2, order=3)
        #p = VectorSpace(mesh, p=1, order=None)

        @FEAFunction
        def pExact(p):
            return -(0.3/2*pg.x(p)*pg.y(p)**2 + pg.x(p) - 0.3/6*pg.x(p)**3)

        rhs = pg.Vector(p.dof)

        for b in p.mesh.boundaries():

            if b.outside():
                vE = p.uE(b, f=pExact)
                rhs[vE.rowIDs()] += vE.col(0)

        ref = np.sort(-1.0*np.array([0.00083333, 0.00083333, 0.36583333, 0.,
                    0.37666667, 0., 0.31583333, 0.66333333, 0.32666667]))
        self.assertEqual(ref, np.sort(rhs), atol=4e-9)

        ## more tests
        rhs = np.sort((p*pExact).assemble(onBoundaries=True))
        self.assertEqual(ref, rhs, atol=4e-9)

        rhs = np.sort((pExact*p).assemble(onBoundaries=True))
        self.assertEqual(ref, rhs, atol=4e-9)

        rhs = np.sort((-p*pExact).assemble(onBoundaries=True))
        self.assertEqual(-ref[::-1], rhs, atol=4e-9)

        rhs = np.sort((-pExact*p).assemble(onBoundaries=True))
        self.assertEqual(-ref[::-1], rhs, atol=4e-9)

        rhs = np.sort((-pExact*p).assemble(onBoundaries=True))
        self.assertEqual(-ref[::-1], rhs, atol=4e-9)

        rhs = np.sort((pExact*p).assemble(onBoundaries=True))
        self.assertEqual(ref, rhs, atol=4e-9)


        x = [-1.0, 0.0, 1.0, 2.]
        mesh = pg.createGrid(x=x, y=x)

        bID = [b.id() for b in mesh.boundaries(mesh.boundaryMarkers()==4)]

        ### few more tests for VectorSpace
        v = VectorSpace(mesh)
        #print(bID)

        R = v*[0, 1.0]
        #pg.core.setDeepDebug(-1)
        r1 = R.apply(bID[0], entity='boundary', core=False)
        r2 = R.apply(bID[0], entity='boundary', core=True)

        self.assertEqual(r1, r2)

        r1 = R.assemble(onBoundaries=bID, core=False)
        r2 = R.assemble(onBoundaries=bID, core=True)

        self.assertEqual(r1, r2, atol=1e-15)


    def test_CreateNeumannNorm_traced(self):
        """Basic element matrix tests for norm on boundary elements. (Traced)
        """
        mesh = createTestMeshs()[0]
        du = FEAFunction3(lambda x: [0.5, 0.5])
        s = ScalarSpace(mesh)

        ### start traced
        mesh = s.mesh
        rhs = np.zeros(mesh.nodeCount())
        bIDs = pg.solver.boundaryIdsFromDictKey(mesh, 1)

        neumN = FEAFunctionDotNorm(du)
        expr = (s*neumN)

        for boundIDs in bIDs.values():
            (expr).assemble(onBoundaries=boundIDs, RHS=rhs)
            #TODO trace further!!
            # for bID in boundIDs:
            #     ### self.apply(bID, entity='boundary')
            #     A = uE()
            #     mulE(A, f=B, c=c, core=core, **kwargs)

            # np.dot(NF.eval(p), entity.norm())
        #pg._g(rhs)
        ### end traced

        ### Combined, same like above.
        rhs2 = np.zeros(mesh.nodeCount())
        applyBoundaryConditions({'Neumann':{1:du}}, space=s, mat=None, rhs=rhs2)

        #pg._y(rhs2)
        assertEqual(rhs, rhs2)


    def test_CreateNeumannNorm(self):
        """Basic element matrix tests for norm on boundary elements.
        """
        x = np.linspace(0.0, 1.0, 2)
        mesh = pg.createGrid(x=x, y=x)
        mesh = pg.meshtools.refineQuad2Tri(mesh)

        v = VectorSpace(mesh, p=2, order=4)
        @FEAFunction
        def pExact(p):
            return -(0.3/2*pg.x(p)*pg.y(p)**2  + pg.x(p) - 0.3/6*pg.x(p)**3)

        #### START DEBUG WORKSPACE ############################################
        # L = v*v
        # A, rhs = (L == 0).assemble()

        # L = v*pExact*norm(v)

        # s = ScalarSpace(mesh)
        # a = 0.3
        # @FEAFunction3
        # def va(p):
        #     return np.array([0.5, 0.5, 0.5])
        # bID = [b.id() for b in mesh.boundaries(mesh.boundaryMarkers() == 1)]
        # boundSize = sum(mesh.boundarySizes()[bID])

        # R2 = np.zeros(mesh.nodeCount())
        # applyBoundaryConditions({'Neumann':{1:a*va}}, s, mat=None, rhs=R2)
        # self.assertEqual(sum(R2), -a*0.5*boundSize, atol=1e-16)


        # _testExp(L==0)
        # pg.core.setDeepDebug(-1)
        # ret = (L).assemble(onBoundaries=True)
        # pg.core.setDeepDebug(0)
        # print(ret)
        # # # print(rhs)
        # return
        #### END DEBUG WORKSPACE ##############################################

        L = v*v
        A, rhs = (L == 0).assemble()
        _testExp(L==0)

        for b in v.mesh.boundaries():
            if b.outside():

                n = b.norm()
                vE = v.uE(b, f=pExact)
                rhs[vE.rowIDs()]  += (vE.col(0)*n[0] + vE.col(1)*n[1])

        ref = np.sort(-1.0*np.array([0., 1/1200, 0.,-1/1200,  0.18083333,
                                    0.185, 0., 0., 0., 0.37666667, 0., 0.,
                                    0.15583333, -0.16, 0.66333333,  0., 0.,
                                    -0.32666667]))
        refM = np.sort(1.0*np.array([0., 1/1200, 0.,-1/1200,  0.18083333,
                                    0.185, 0., 0., 0., 0.37666667, 0., 0.,
                                    0.15583333, -0.16, 0.66333333,  0., 0.,
                                    -0.32666667]))

        self.assertEqual(ref, np.sort(rhs), atol=4e-9)

        ## more tests
        rhs = np.sort((v*pExact*norm(v)).assemble(onBoundaries=True))
        self.assertEqual(ref, rhs, atol=4e-9)

        rhs = np.sort((pExact*v*norm(v)).assemble(onBoundaries=True))
        self.assertEqual(ref, rhs, atol=4e-9)

        rhs = np.sort((-pExact*v*norm(v)).assemble(onBoundaries=True))
        self.assertEqual(refM, rhs, atol=4e-9)

        rhs = np.sort(((-pExact*v)*norm(v)).assemble(onBoundaries=True))
        self.assertEqual(refM, rhs, atol=4e-9)

        rhs = np.sort((pExact*(v*norm(v))).assemble(onBoundaries=True))
        self.assertEqual(ref, rhs, atol=4e-9)

        # FIXME .. this happens due to pre-form sorting in feaop.assemble()
        # rhs = np.sort((pExact*(-v*norm(v))).assemble(onBoundaries=True))
        # self.assertEqual(refM, rhs, atol=4e-9)
        #return

        rhs = np.sort((-pExact*(v*norm(v))).assemble(onBoundaries=True))
        self.assertEqual(refM, rhs, atol=4e-9)

        ### more generic test for (a v * norm(v))(ds)

        ms = createTestMeshs()

        for mesh in ms:

            v = VectorSpace(mesh)
            a = 0.3

            bID = [b.id() for b in mesh.boundaries(mesh.boundaryMarkers() == 1)]

            BC = a*-v*norm(v)
            R = BC.assemble(onBoundaries=bID)
            self.assertEqual(sum(R), a, atol=2e-16)

            bID = [b.id() for b in mesh.boundaries(mesh.boundaryMarkers() == 2)]
            BC = -a*-v*norm(v)
            R = BC.assemble(onBoundaries=bID)
            self.assertEqual(sum(R), a, atol=2e-16)

            s = ScalarSpace(mesh)
            bID = [b.id() for b in mesh.boundaries(mesh.boundaryMarkers() == 1)]
            #norm = [-1, 0] but will not seen by assemble
            BC = a*s
            R = BC.assemble(onBoundaries=bID)
            self.assertEqual(sum(R), a, atol=2e-16)

            @FEAFunction3
            def va(p):
                return np.array([0.5, 0.5, 0.5])

            boundSize = sum(mesh.boundarySizes()[bID])

            # Calculate Neumann value internally with norm(boundary)*va
            R2 = np.zeros(mesh.nodeCount())
            applyBoundaryConditions({'Neumann':{2:va}}, s, mat=None, rhs=R2)
            self.assertEqual(sum(R2), 0.5*boundSize, atol=1e-16)

            R2 = np.zeros(mesh.nodeCount())
            applyBoundaryConditions({'Neumann':{1:va}}, s, mat=None, rhs=R2)
            self.assertEqual(sum(R2), -0.5*boundSize, atol=1e-16)

            R2 = np.zeros(mesh.nodeCount())
            applyBoundaryConditions({'Neumann':{1:a*va}}, s, mat=None, rhs=R2)
            self.assertEqual(sum(R2), -a*0.5*boundSize, atol=1e-16)

            R2 = np.zeros(mesh.nodeCount())
            applyBoundaryConditions({'Neumann':{1:va*a}}, s, mat=None, rhs=R2)
            self.assertEqual(sum(R2), -a*0.5*boundSize, atol=1e-16)

            # Give Neumann value directly.
            R2 = np.zeros(mesh.nodeCount())
            applyBoundaryConditions({'Neumann':{1:-a*0.5}}, s, mat=None, rhs=R2)
            self.assertEqual(sum(R2), -a*0.5*boundSize, atol=1e-16)

            # Test some eval problems for missing dims of va
            R2 = np.zeros(mesh.nodeCount())
            u = asFunction('0.5*x + 0.5*y + 0.5*z')
            applyBoundaryConditions({'Neumann':{1:a*grad(u)}},s,mat=None,rhs=R2)
            self.assertEqual(sum(R2), -a*0.5*boundSize, atol=1e-16)

            if mesh.dim() == 1:
                R2 = np.zeros(mesh.nodeCount())
                u = asFunction('0.5*x')
                applyBoundaryConditions({'Neumann':{1:a*grad(u)}},s,
                                        mat=None,rhs=R2)
                self.assertEqual(sum(R2), -a*0.5*boundSize, atol=1e-16)
            elif mesh.dim() == 2:
                R2 = np.zeros(mesh.nodeCount())
                u = asFunction('0.5*x + 0.5*y')
                applyBoundaryConditions({'Neumann':{1:a*grad(u)}},s,
                                        mat=None,rhs=R2)
                self.assertEqual(sum(R2), -a*0.5*boundSize, atol=1e-16)


    def test_NeumannManager(self):
        """ Test Neumann Manager.
        """
        from oskar.solve import applyRHSBoundaryConditions, NeumannManager
        x = np.linspace(-1, 2, 5)
        mesh = pg.createGrid(x)

        s = ScalarSpace(mesh)
        u = asFunction('x^2')

        rhs1 = pg.Vector(mesh.nodeCount())
        N1 = -grad(u)(x[0])[0]
        N2 =  grad(u)(x[-1])[0]
        bc = {'Neumann':{1:N1, 2:N2}}
        applyRHSBoundaryConditions({s:bc}, rhs=rhs1)

        rhs_ = pg.Vector(mesh.nodeCount())
        neum = NeumannManager({s:bc})
        neum.apply(rhs_)
        self.assertEqual(rhs1, rhs_)

        rhs2 = pg.Vector(mesh.nodeCount())
        N1 = grad(u)
        bc = {'Neumann':{'*':N1}}
        applyRHSBoundaryConditions({s:bc}, rhs=rhs2)
        self.assertEqual(rhs1, rhs2)

        rhs_ = pg.Vector(mesh.nodeCount())
        neum = NeumannManager({s:bc})
        neum.apply(rhs_)
        self.assertEqual(rhs1, rhs_)

        rhs_ = np.zeros(mesh.nodeCount())
        neum = NeumannManager({s:bc})
        neum.apply(rhs_)
        self.assertEqual(rhs1, rhs_)


    def test_FEA_Integration(self):
        r"""Test per cell integration.

        \int_0^1 f(x) dx

        a) f(x) = sum_i^N i (-x)^i

        """
        def testIntegratePoly(gradP, order):
            x = np.linspace(-1.3, 1.2, 2)
            y = np.linspace(0, 1, 2)
            mesh = pg.createGrid(x=x, y=y, z=y)
            ms = createTestMeshs()

            #ms = [mesh]
            for mesh in ms:

                pg.info(f'dim: {mesh.dim()}: gradP ({gradP}) order={order}')
                fa = lambda x: sum([i * pg.x(-x)**i for i in range(1,gradP+1)])
                Fa = lambda x: sum([-i * (-x)**(i+1)/(i+1) for i in range(1,gradP+1)])
                Ifa = Fa(pg.x(mesh)[-1]) - Fa(pg.x(mesh)[0]) # ref result: int_x[0]^x[-1] fa dx
                uF = FEAFunction(fa)
                try:
                    self.assertEqual(uF.integrate(mesh, order=order), Ifa, atol=1e-12)
                except Exception as e:
                    print(e)
                    pg._r('uF.integrate fail', type(mesh.cell(0)))

                uFOP = 2.0 + uF - 2
                try:
                    self.assertEqual(uFOP.integrate(mesh, order=order), Ifa, atol=1e-12)
                except Exception as e:
                    print(e)
                    pg._r('uFOP.integrate fail', type(mesh.cell(0)))

                # Integration by assembling with function (interpolators)
                u = ScalarSpace(mesh, p=1, order=order)
                try:
                    self.assertEqual(sum((fa*u).assemble()), Ifa, atol=1e-12)
                except Exception as e:
                    print(e)
                    pg._r('fa*u (p1) fail', type(mesh.cell(0)))

                u = ScalarSpace(mesh, p=2, order=order)
                try:
                    self.assertEqual(sum((fa*u).assemble()), Ifa, atol=1e-12)
                except Exception as e:
                    print(e)
                    pg._r('fa*u (p2) fail', type(mesh.cell(0)))


        # exact numerical integration solutions
        # order = 1, evaluate at cell centers, exact for linear functions
        testIntegratePoly(gradP=1, order=1)
        testIntegratePoly(gradP=2, order=2)
        testIntegratePoly(gradP=3, order=2)
        # testIntegratePoly(gradP=4, order=3)
        # testIntegratePoly(gradP=5, order=3)
        # testIntegratePoly(gradP=6, order=4)
        # testIntegratePoly(gradP=7, order=4)
        # testIntegratePoly(gradP=8, order=5)
        # testIntegratePoly(gradP=9, order=5)
        # testIntegratePoly(gradP=10, order=6)
        # testIntegratePoly(gradP=11, order=6)
        # testIntegratePoly(gradP=12, order=7)
        # testIntegratePoly(gradP=13, order=7)
        # testIntegratePoly(gradP=14, order=8)
        # testIntegratePoly(gradP=15, order=8)
        # testIntegratePoly(gradP=16, order=9)
        # testIntegratePoly(gradP=17, order=9)


    def testTracedAssemblingLF(self):
        """ Test traced version of assembling.
        """
        #### START DEBUG WORKSPACE ####################################

        #halt
        #### END DEBUG WORKSPACE ######################################

        ### ScalarSpace * CellValue      #######################################
        for mesh in createTestMeshs():
            for p in [1, 2]:
                s = ScalarSpace(mesh, p=p, order=3)
                f = 2
                L = s * f
                RT = _testExp(L)
                try:
                    R = np.zeros_like(RT)
                    for c in s.mesh.cells():
                        A = s.uE(c)
                        R[A.rowIDs()] += np.sum(np.array(A.mat()*f), axis=1)

                    assertEqual(RT, R, atol=1e-15)

                except Exception as e:
                    pg._r('+'*80)
                    pg._g(f'mesh: {mesh} p:{p} order: {s.order}')
                    pg._y('L:', L)
                    pg._y(R)
                    pg._g(RT)
                    pg._r('-'*80)
                    print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()
        ### ScalarSpace * CellValue      #######################################

        ### ScalarSpace * f(quadrature)  #######################################
        for mesh in createTestMeshs():
            for p in [1, 2]:
                s = ScalarSpace(mesh, p=p, order=3)
                f = asFunction('x')
                L = s * f
                RT = _testExp(L)

                try:
                    R = np.zeros_like(RT)
                    for c in s.mesh.cells():
                        A = s.uE(c)
                        r = np.zeros_like(A._mat[0])
                        ## integrate over all quadrature points
                        for i, w in enumerate(A._w):
                            fi = f(c.shape().xyz(A._x[i]))
                            A._mat[i] *= fi
                            r += (A._mat[i] * w * c.size())
                        setMat(A, np.array(r.T))

                        R[A.rowIDs()]  += np.sum(np.array(A.mat()), axis=1)

                    assertEqual(RT, R, atol=1e-15)

                except Exception as e:
                    pg._r('+'*80)
                    pg._g(f'mesh: {mesh} order: {s.order}')
                    pg._y('L:', L)
                    pg._y(R)
                    pg._g(RT)
                    pg._r('-'*80)
                    print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()
        ### ScalarSpace * f(quadrature)  #######################################

        ### Grad(VectorSpace) * C * I #################################
        def _test(dim, full_Matrix_but_2d=False, elastic=True):
            pg.info(f'testTracedAssemblingLF: dim={dim}, '
                    f'full_Matrix_but_2d={full_Matrix_but_2d}, '
                    f'elastic={elastic}')

            x = np.linspace(-1.5, 1.5, 2)
            if dim == 2:
                mesh = pg.createGrid(x, x)
            else:
                mesh = createTestMeshs()[4]
                mesh = mesh.createMeshByCellIdx([0])
                #mesh = pg.createGrid(x, x, x)

            ### Grad(VectorSpace) * C * alpha * I #########################
            v1 = VectorSpace(mesh, order=3)
            vE = VectorSpace(mesh, order=3, elastic=True)

            alpha = 3.0
            lam = 2.0
            mu = 0.2
            lmu = mesh.dim()*lam + 2*mu
            C = createElasticityMatrix(lam=lam, mu=mu, dim=mesh.dim())

            full_Matrix_but_2d = False

            if full_Matrix_but_2d is True:
                ## full Matrix but 2d mesh
                C3 = createElasticityMatrix(lam=lam, mu=mu, dim=3)
                lmu = 3*lam + 2*mu
                C = C3

            L = grad(v1) * lmu * alpha * I(v1)
            RT = _testExp(L)

            # print(C)
            # print(lmu)
            R = np.zeros_like(RT)

            if elastic is True:
                s = vE  # elastic Matrix
            else:
                s = v1   # linear isotropic

            for c in s.mesh.cells():
                A = s.gradE(c)
                r = np.zeros_like(A._mat[0])
                #print(A)
                ## integrate over all quadrature points

                # for i, w in enumerate(A._w):
                #     # fi = f(c.shape().xyz(A._x[i]))

                #     # A._mat[i] *= fi
                #     r += (A._mat[i] * w * c.size())
                # setMat(A, np.array(r.T))
                #print(A)

                if s.elastic is True:
                    if C.shape == (6, 6) and c.dim() == 2:
                        # 3D elasticity Matrix for 2D problem
                        CDim = 3
                        AI = s.identityE(c, dim=CDim)
                        #print('AAI', AI)
                        CA = ((C*alpha) @ np.asarray(AI.mat()).T).T
                        #print('CA', CA)
                        CA = np.asarray(A.mat())*CA[:,[0,1,3]]
                        #print('CA', CA)
                    else:

                        AI = s.identityE(c)
                        #print('AAI', AI)
                        if c.dim() == 2:
                            CA = ((C*alpha) @ (np.asarray(AI.mat())[:,[0,1,3]]).T).T
                            #CA = np.asarray(AI.mat())[:,[0,1,3]]@(C*alpha)
                        else:
                            CA = ((C*alpha) @ np.asarray(AI.mat()).T).T
                        #print('CA', CA)

                        CA = np.asarray(A.mat())*CA
                        #print('CA', CA)

                    if s.mesh.dim() == 2:
                        colIds = (0,1)
                        #print(np.sum(CA[:,colIds], axis=1))
                    else:
                        colIds = (0,1,2)

                    R[A.rowIDs()] += np.sum(CA[:,colIds], axis=1)
                else:
                    if s.mesh.dim() == 2:
                        colIds = (0,3)
                    else:
                        colIds = (0,4,8)

                    R[A.rowIDs()] += np.sum(np.asarray(A.mat())[:,colIds]*lmu*alpha,
                                                axis=1)

            assertEqual(R, RT, atol=8e-15)
            #pg._g(R)

            ### useMats version
            aM = vE.gradUMat(order=vE.order)
            R = pg.Vector(len(R))
            aM.assemble(md=C*alpha, R=R)
            assertEqual(R, RT, atol=8e-15)
            ### useMats version

            L = grad(vE) * (C * alpha * I(vE))  #ok
            # R = L.assemble(core=False) #ok
            # pg._g(R)
            # R = L.assemble(core=True) #ok
            # pg._y(R)
            # R = L.assemble(useMats=True)
            # pg._r(R)
            #halt
            _testExp(L, ref=RT)

        _test(dim=2, full_Matrix_but_2d=False)
        _test(dim=2, full_Matrix_but_2d=True)
        _test(dim=3, full_Matrix_but_2d=True)
        _test(dim=2, full_Matrix_but_2d=False, elastic=False)
        _test(dim=2, full_Matrix_but_2d=True, elastic=False)
        _test(dim=3, full_Matrix_but_2d=True, elastic=False)

        ### Grad(VectorSpace) * C * I #################################


class TestFEAOperators(TestCollection):
    """Test for basic finite element operators."""

    def test_FEA_Dirac(self):
        r"""Linear form integration with special dirac operator.

        Test :math:`\int s* dirac()*f dx`
        """
        ms = createTestMeshs()
        f = FEAFunction(lambda p: 3)
        mesh = ms[2]
        s = ScalarSpace(mesh, p=2)

        #### START DEBUG WORKSPACE ############################################
        # L = s * dirac()*2 # ok
        # L = s * 2*dirac() # ok
        # L = s * dirac() * f # ok
        # L = s * dirac() * 2*f # ok
        # _assemble(L)
        # pg.core.setDeepDebug(-1)
        # pg._r(L.assemble(useMats=True))
        # pg.core.setDeepDebug(0)
        # _testExp(L)

        # pg._g(L.assemble(core=False))
        # pg._y(L.assemble(core=True))
        # return
        #### START DEBUG WORKSPACE ############################################

        from oskar.solve import ensureInitialSolution
        rhs = ensureInitialSolution(dirac(), s)
        self.assertEqual(sum(rhs.values), 1.0)
        self.assertEqual(ensureInitialSolution(dirac()*2.0, s), rhs*2.0)
        self.assertEqual(ensureInitialSolution(2*dirac(), s), rhs*2.0)
        self.assertEqual(ensureInitialSolution(dirac()/0.5, s), rhs*2.0)

        L = s * dirac(s, rs=[0.0, 0.0])
        _testExp(L)
        self.assertEqual(sum(L.assemble()), 1.0)

        L = s * dirac(s, rs=[0.1, 0.0])
        _testExp(L)
        self.assertEqual(sum(L.assemble()), 1.0)

        L = s * dirac(s, rs=[0.0, 0.0], cellScale=True)
        _testExp(L)
        self.assertEqual(sum(L.assemble()), 1/s.mesh.cell(0).size())

        L = s * dirac(s, rs=[1.0, 0.0], cellScale=True)
        _testExp(L)
        self.assertEqual(sum(L.assemble()), 1/s.mesh.cell(0).size())

        L = s * dirac(s, rs=[1.0, 0.0], cellScale=True) * 2
        _testExp(L)
        self.assertEqual(sum(L.assemble()),
                         1/s.mesh.cell(0).size()*2)

        L = s * dirac(s, rs=[1.0, 0.0], cellScale=True) * f
        _testExp(L)
        self.assertEqual(sum(L.assemble()),
                         1/s.mesh.cell(0).size()*f([1.0, 0.0]))

        L = s * dirac(s, rs=[1.0, 0.0], cellScale=True) * 2*f
        _testExp(L)
        self.assertEqual(sum(L.assemble()),
                         1/s.mesh.cell(0).size()*2*f([1.0, 0.0]))

        for i, mesh in enumerate(ms[0:]):

            for p in [1, 2]:

                dt = 0.1
                pg.info('mesh:', mesh, 'p:', p)
                s = ScalarSpace(mesh, p=p)

                Ls = [
                        s * dirac(),
                        s * (dirac()*f),
                        s * dirac() * 2.,
                        s * dirac()*f*2,
                        s * dirac()/2.,
                        s * dirac()*2*f,
                        s * f*2*dirac(),
                        s * f*dirac(),
                        s * 2.*dirac(),
                        s * 2*f*dirac(),
                        s * dirac(s, rs=[0.0, 0.0], t0=0.0),
                        s * dirac(s, rs=[0.0, 0.0], t0=0.0) * 2,
                        dt * (s * dirac(s, rs=[0.0, 0.0], t0=0.0) * 2),
                        s * (dirac(s, rs=[0.0, 0.0], t0=0.0) * 2),
                        s * 2 * dirac(s, rs=[0.0, 0.0], t0=0.0),
                        s * (2 * dirac(s, rs=[0.0, 0.0], t0=0.0)),
                     ]

                try:
                    for L in Ls:
                        print('.', end='', flush=True)
                        _testExp(L)

                except BaseException as e:
                    pg._r('+'*80)
                    pg._g(f'i={i} {s.mesh} p={p}')
                    pg._y('L:', L)
                    pg._r('-'*80)

                    # print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()
                print()


class TestFEAExpressions(TestCollection):
    """Test assembling of finite element expressions."""

    def test_FEA_Advection_Expressions(self):
        """Test Expressions with advection operator."""
        #### START DEBUG WORKSPACE ############################################
        # mesh = createTestMeshs()[2]
        # u = ScalarSpace(mesh, order=3)
        # v = VectorSpace(mesh, p=2, order=3)
        # vel2 = FEAFunction3(lambda p: [3.14, 3.14, 3.14])

        # vel = FEASolution(v, vel2)

        # @FEAFunction
        # def cv(p, entity, **kwargs):

        #     #print('entity:', entity, p)
        #     vAbs = pg.abs(vel(p))
        #     if vAbs > 0:
        #         ret = entity.shape().h()/(2.0*vAbs)
        #         #sys.exit()
        #         return ret
        #     else:
        #         return 0.0

        # class CV(FEAFunction):
        #     def __init__(self, vel, *args, **kwargs):
        #         super().__init__(*args, **kwargs)
        #         self.vel = vel

        #     def eval(self, pnts, **kwargs):
        #         if isinstance(pnts, pg.core.stdVectorR3Vector):
        #             ret = pg.core.stdVectorRVector()
        #             pg.core.testEvalEmap(kwargs['elementMap'],
        #                   self.vel(pnts), ret)
        #             return ret

        #         pg._b(pnts, kwargs)
        #         if not 'entity' in kwargs:
        #             raise TypeError()

        #         if pg.isPos(pnts):
        #             vAbs = pg.abs(self.vel(p))
        #             if vAbs > 0:
        #                 ret = entity.shape().h()/(2.0*vAbs)
        #                 return ret
        #             else:
        #                 return 0.0



        # cv = CV(vel)

        # ut = u + cv*(vel*grad(u))

        # L = ut * u

        # with pg.tictoc('A'):
        #     A3 = L.assemble(useMats=True)

        # print(pg.timings('A'))
        # pg._r(A3)

        # A1 = L.assemble(core=False)
        # pg._g(A1)
        # return
        # # A2 = L.assemble(core=True)
        # # pg._y(A2)
        # # pg._r(A3)

        # _testExp(L)

        # return
        #### END DEBUG WORKSPACE ##############################################

        for mesh in createTestMeshs()[2:]:
            pg.warning('1D TODO')
            u = ScalarSpace(mesh)
            v = VectorSpace(mesh)

            vel0 = 3.14
            vel1 = np.ones(mesh.dim()) * 3.14
            vel2 = FEAFunction3(lambda p: [3.14, 3.14, 3.14])
            vel3 = FEASolution(space=v, values=vel2)

            cv = FEAFunction(lambda p: 3.)
            c = 99.0

            L = (vel3/abs(vel3))*grad(u)

            #deepDebug(L)


            for vel in [vel0,
                        vel1,
                        vel2,
                        vel3,
                    ]:

                L1 = u
                L2 = vel*grad(u)
                L3 = c*u
                L4 = L1 + cv*L2

                self.assertEqual((vel0*grad(u)).apply(0),
                                 (vel*grad(u)).apply(0))
                self.assertEqual(((L1 + vel0*grad(u))*(c*u)).apply(0),
                                        ((L1 + vel*grad(u))*(c*u)).apply(0))

                self.assertEqual((L1*L2).apply(0), (L2*L1).apply(0).T)
                self.assertEqual(((L1+L2) * L1).apply(0),
                                 (L1 * (L1+L2)).apply(0).T)
                self.assertEqual(((L1+L2) * L2).apply(0),
                                 (L2 * (L1+L2)).apply(0).T)
                self.assertEqual(((L1 + L2)*(c*u)).apply(0),
                                 ((L1 + L2)*c*u).apply(0))
                self.assertEqual((L4*c*u).apply(0), (L4*(c*u)).apply(0))
                self.assertEqual(((-L1)*L2).apply(0), (-(L1*L2)).apply(0))
                self.assertEqual(((-L1)*L2).apply(0), (L2*(-L1)).apply(0).T)
                self.assertEqual(((L1+L2) * L2).apply(0),
                                 (L1*L2 + L2*L2).apply(0).eval())
                self.assertEqual((L1*L1 + L2*L1).apply(0).eval(),
                                 ((L1+L2) * L1).apply(0))
                self.assertEqual(((L1+L2) * L2).apply(0),
                                 ((L2+L1) * L2).apply(0))
                self.assertEqual(((L1+L2) * L1).apply(0),
                                 ((L2+L1) * L1).apply(0))
                self.assertEqual(((L1+L2) * L1).apply(0),
                                 (L1 * (L1+L2)).apply(0).T)
                self.assertEqual(((L1+L2) * L2).apply(0),
                                 (L2 * (L1+L2)).apply(0).T)

                try:
                    for L in [L1,               # u
                              L1*L1,            # u * u
                              L2,               # vGu
                              L1*L2,             # u * vGu
                              L2*L1,            # vGu * u == (u * vGu).T
                              L2*L2,            # vGu * vGu
                              -L1*L2,           # -u * vGu
                              (-L1)*L2,         # -u * vGu
                              (-L2)*L1,         # -vGu * u == (-u * vGu).T
                              L1*L2 + L2*L2,    # u*vGu + vGu*vGu
                              L1 + L2,            # u + vGu
                              L2 + L1,            # vGu + u
                            (L1+L1) * L2,     # (u+u) * vGu
                            (L1+L2) * L2,     # (u+vGu) * vGu
                            (L2+L1) * L2,     # (vGu+u) * vGu
                            (L1+L2) * L1,     # (u + vGu) * u
                            (L2+L1) * L1,     # (vGu + u) * u
                            L2 * (L1+L2),     # vGu*(u+vGu) == ((u+vGu) * vGu).T
                            L2 * (L2+L1),     # vGu*(u+vGu) == ((u+vGu) * vGu).T
                            L1 * (L1+L2),     # u*(u + vGu) == ((u + vGu)*u).T
                            L1 * (L2+L1),     # u*(u + vGu) == ((u + vGu)*u).T
                            L1*L1 + L2*L1,    # u*u + vGu*u
                            L1*L3 + L2*L3,    # u*cu + vGu*cu
                            (L1 + L2)*L3,     # (u + vGu)*cu
                            (L1 + L2)*(c*u),  # (u + vGu)*(c*u)
                            (L1 + L2)*c*u,    # ((u + vGu)*c)*u
                            L4*c*L1,
                            L4*(c*L1),
                            ]:

                        u.cache = False
                        v.cache = False

                        print('.', end='', flush=True)
                        _testExp(L)

                except BaseException:
                    pg._g('-'*80)
                    pg._g(u.mesh)
                    pg._y(vel)
                    pg._y(L)
                    pg._g('-'*80)
                    # print(e)
                    # import traceback
                    # traceback.print_exc(file=sys.stdout)
                    exit()
            print()


    def test_FEA_Combined_Expressions(self):
        """Test combined expressions.

        A, b = grad(v)(f(v) + g)
        A, b = s*a*(s + u0) ## @ boundaries Robin
        """
        #### START DEBUG WORKSPACE ############################################
        mesh = createTestMeshs()[2]
        mesh = pg.createGrid(2,2)
        s = ScalarSpace(mesh)
        v = VectorSpace(mesh)

        u0 = asFunction('x+y')
        beta = 42.
        #u0 = u + h/beta*alpha


        A = (s*beta*s).assemble()
        b = (s*beta*u0).assemble()

        A1, b1 = (s*beta*(s - u0)).assemble()

        assertEqual(A1, A)
        assertEqual(b1, b)

        #(s*beta*u0).assemble(onBoundaries=b2, RHS=rhs)
        #(s*beta*s).assemble(onBoundaries=b2, LHS=A)
        # pg._g('###################')
        # (s*beta*(s + u0)).assemble(onBoundaries=b2, LHS=A, RHS=rhs)

        return
        #### END DEBUG WORKSPACE ##############################################
        # mesh = pg.createGrid(2,2)

        # v = VectorSpace(mesh)

        # for L in [
        #            grad(v) * (grad(v) + I(v)),
        #            grad(v) * (grad(v) - I(v))
        #          ]:
        #     _testExp(L)


    def test_FEA_Combined_Expressions2(self):
        """Test combined expressions.

        Test expression resulting from time stepping.
        """
        #### START DEBUG WORKSPACE ############################################
        x = np.linspace(0.0, 1.0, 4)

        mesh = pg.createGrid(x=x)

        s = ScalarSpace(mesh)
        uh = FEASolution(s, values=pg.x(s.mesh))
        f = asFunction('x')
        a = asFunction('1+x')
        ft = asFunction('x*t')
        ti = 0.2
        dt = 0.1
        theta = 0.5

        # L = s*s - dt*grad(s)*grad(s) == s*uh + dt*s*f ok

        # L = theta*dt*(s*ft)             # ok
        # L = grad(s)*(((1-theta)*dt)*grad(uh)) # OK
        # L = (1-theta)*dt*grad(s)*grad(uh) # need OK

        # L = s*s + theta*dt*grad(s)*grad(s) == s*uh + theta*dt*s*ft \
        #       - (1-theta)*dt*grad(s)*grad(uh) + (1-theta)*dt*s*ft(t=ti)

        # L = (1-theta)*dt*grad(s)*grad(uh) + (1-theta)*dt*s*ft(t=ti)

        # L = (1-theta)*dt*s*ft(t=ti)     # ok
        # L = s*ft                        # ok

        kwargs = dict(time=ti)


        #L = grad(s)*(((1-theta)*dt*a)*grad(uh))
        L = (1-theta)*dt*grad(s)*a*grad(uh) # fixme

        #L = grad(s)*a*grad(uh)              # fixme

        # ref = (grad(s)*a*grad(s)).assemble(useMats=True)*uh.values
        # pg._g(ref)
        # LF, BF = findForms(L)
        # print(LF)

        # # pg.core.setDeepDebug(-1)
        # # E = L.apply(0)
        # # pg.core.setDeepDebug(0)
        # R1 = L.assemble(core=False, **kwargs)
        # pg._g(R1)
        # R2 = L.assemble(core=True, **kwargs)
        # pg._y(R2)
        # R3 = L.assemble(useMats=True, **kwargs)
        # pg._r(R3)

        # _testExp(L, **kwargs)
        #return
        #### END DEBUG WORKSPACE ##############################################

        _testExp(s*(((1-theta)*dt)*ft(t=ti)), (1-theta)*dt*s*ft(t=ti))

        for L in [
                    s*s - dt*grad(s)*grad(s) == s*uh + dt*s*f,
                    s*s - np.float64(dt)*grad(s)*grad(s) == s*uh + np.float64(dt)*s*f,
                    grad(s)*a*grad(uh),
                    (1-theta)*dt*grad(s)*a*grad(uh),
                 ]:

            try:
                _testExp(L)
            except BaseException as e:
                pg._r('+'*80)
                pg._g(L)
                pg._r('-'*80)

                print(e)
                import traceback
                traceback.print_exc(file=sys.stdout)
                exit()



    def test_FEA_Const_Expressions(self):
        """Test for constant space expressions."""
        x = np.linspace(0.0, 1.0, 2)
        mesh = pg.createGrid(x=x, y=x)
        #u = VectorSpace(mesh, p=1)
        # c = ConstantSpace(value=[1.0, 2.0],
        #                   dofOffset=v.dofs.stop, nCoeff=mesh.dim())
        u = ScalarSpace(mesh, p=1)
        c = ConstantSpace(val=1.0, dofOffset=u.dofs.stop, nCoeff=1)

        #### START DEBUG WORKSPACE ############################################
        L = c
        # _testExp(L)
        # exit()
        #### END DEBUG WORKSPACE ##############################################

        for mesh in createTestMeshs()[1:]:
            for p in [1, 2]:

                u = ScalarSpace(mesh, p=p)

                ## test in combination with Vector space
                c = ConstantSpace(dofOffset=u.dofs.stop)

                A3 = (c*u).assemble(useMats=True)
                self.assertEqual(sum(A3.row(A3.rows()-1)), 1.0, atol=5e-13)

                A3 = (u*c).assemble(useMats=True)
                self.assertEqual(sum(A3.col(A3.cols()-1)), 1.0, atol=5e-13)

                for L in [c,
                          c*u,
                          u*c,
                          u*c + c*u,
                          u + c,
                          c + u,
                          grad(u)*1.0*grad(u) + u*1.0*u + u*c + c*u]:

                    try:
                        print('.', end='', flush=True)
                        _testExp(L)
                    except BaseException as e:
                        pg._y(L)
                        pg._g('-'*80)

                        print(e)
                        import traceback
                        traceback.print_exc(file=sys.stdout)
                        exit()

                ## test in combination with Vector space
                v = VectorSpace(mesh, p=p)

                c = ConstantSpace(val=[1.0]*mesh.dim(),
                                  dofOffset=v.dofs.stop, nCoeff=mesh.dim())

                R1 = c.assemble(useMats=True)
                self.assertEqual(R1.size(), (c*v).dof)
                self.assertEqual(sum(R1), 1*mesh.dim(), atol=1e-15)

                for L in [c,
                          c*v,
                          v*c,
                          v*c + c*v,
                          v + c,
                          c + v,
                          grad(v)*1.0*grad(v) + v*1.0*v + v*c + c*v,
                          ]:

                    try:
                        print('.', end='', flush=True)
                        _testExp(L)
                    except BaseException as e:
                        pg._y(L)
                        pg._g('-'*80)

                        print(e)
                        import traceback
                        traceback.print_exc(file=sys.stdout)
                        exit()
        print()


    def test_FEA_Div_Expressions(self):
        """Test expression with div operator."""
        x = np.linspace(0.0, 1.0, 5)
        mesh = pg.createGrid(x)
        s = ScalarSpace(mesh)
        v1 = VectorSpace(mesh)
        v2 = ScalarSpace(mesh)

        v1h = FEASolution(v1, values=pg.x(v1.mesh))
        v2h = FEASolution(v2, values=pg.x(v2.mesh))

        #### START DEBUG WORKSPACE ############################################
        # Lp = p*alphaP*(p-ph) + grad(p)*dt*(kappa*grad(p)) + p*alpha*div(u) \
        #     == p*alpha*div(uh)

        # Lp = s*div(v1h)
        # _assemble(Lp)
        # _testExp(Lp)

        # Lp = s*div(v2h)
        # R1 = Lp.assemble(core=False)
        # pg._g(R1)
        # R2 = Lp.assemble(core=True)
        # pg._y(R2)
        # pg.core.setDeepDebug(-1)
        # R3 = Lp.assemble(useMats=True)
        # pg.core.setDeepDebug(0)
        # pg._r(R3)

        # _testExp(Lp)

        #### END DEBUG WORKSPACE ##############################################

        ## compare 1D ScalarSpace with VectorSpace
        _testExp(s*div(v2h), s*grad(v1h))
        _testExp(s*div(v2h), s*div(v1h))


    def test_FEA_Elastic_Expressions(self):
        """Test for Vector space expression for elastic properties.
        """

        def eps(v):
            return sym(grad(v))

        def sigma(v):
            return lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        # def sigmaE(e):
        #     return lam*identity(e)*tr(e) + 2.0*mu*e

        def sigmaE(e):
            return lam*tr(e)*identity(e) + 2.0*mu*e

        def sigmaT(e, T):
            return lam*tr(e)*I + 2.0*mu*e - alpha*(3*lam + 2*mu)*T


        #### START DEBUG WORKSPACE ############################################
        mesh = createTestMeshs()[2]
        print(mesh)
        print(mesh.cell(0).shape())
        #mesh = mesh.createMeshByCellIdx([0])
        s = ScalarSpace(mesh)

        T = FEASolution(s, values=pg.x(s.mesh), name='T')
        v = VectorSpace(mesh, order=3, p=2)
        E0 = np.array([[2.0, 0.5], [0.5, 2.0]])

        lam = 3.14
        mu = 0.2
        alpha = 0.3

        # L = grad(v)*sigmaT(eps(v), T)

        # RT = L.assemble(core=False)
        # pg._g(RT)

        # lam = ParameterDict({0:lam})
        # mu = ParameterDict({0:mu})
        # alpha = ParameterDict({0:alpha})

        # lam = lam.cellValues(mesh)
        # mu = mu.cellValues(mesh)
        # alpha = alpha.cellValues(mesh)

        # L = grad(v)*sigmaT(eps(v), T)


        # R1 = L.assemble(core=False)
        # pg._g(R1); print(R1==RT)
        # R2 = L.assemble(core=True)
        # pg._y(R2); print(R2==RT)
        # R3 = L.assemble(useMats=True)
        # pg._r(R3); print(R3==RT)
        # #halt
        # _testExp(L)
        #### END DEBUG WORKSPACE ##############################################

        #### START a few tests for cell or parameter based values
        lam = 3.14
        mu = 0.2
        alpha = 0.3
        L = grad(v)*sigmaT(eps(v), T)
        RT = _testExp(L)

        lam = ParameterDict({0:lam})
        mu = ParameterDict({0:mu})
        alpha = ParameterDict({0:alpha})
        L = grad(v)*sigmaT(eps(v), T)
        _testExp(L, ref=RT)

        lam = lam.cellValues(mesh)
        mu = mu.cellValues(mesh)
        alpha = alpha.cellValues(mesh)
        L = grad(v)*sigmaT(eps(v), T)
        _testExp(L, ref=RT)
        #### END a few tests for cell or parameter based values


        ms = createTestMeshs()
        for mesh in ms[0:]:
            lam = 3.14
            mu = 0.2
            alpha = 0.3

            for p in [1, 2]:

                pg.info('mesh:', mesh, 'p:', p)
                v = VectorSpace(mesh, p=p)
                s = ScalarSpace(mesh)
                T = FEASolution(s, name='T')
                vF = asFunction(u='(a - y + x)², (b + x +y )², (c + x +z )²',
                                a=1.1, b=2.2, c=3.3)[0]

                Ls = [
                        grad(v),
                        eps(v),
                        grad(v)*eps(v),
                        grad(v)*sigma(v),
                        grad(v)*sigmaT(eps(v), T),
                        sigma(v)*eps(v),
                        sigma(v),
                        lam*tr(eps(v))*I(v),
                        lam*identity(v)*tr(eps(v)),
                        v*div(sigma(vF)),
                        ]

                Ls_ = []
                if mesh.dim() == 2:

                    E0 = np.array([[2.0, 0.5], [0.5, 2.0]])
                    ## E0 as array can be ambiguous to stdVectorRVector and
                    ## fails mult(A, rv) for A.cols() == A.ncoeffs()
                    ## for useCore =True and useMats .. thing about
                    ## !!reimplement with RMatrix!! ..

                    Ls_.append(grad(v)*sigmaE(E0).flatten())
                    Ls_.append(sigmaE(E0).flatten()*grad(v))
                    Ls_.append(sigmaE(E0)*grad(v))
                    Ls_.append(grad(v)*sigmaE(E0))

                try:
                    for L in Ls:
                        print('.', end='', flush=True)
                        _testExp(L)
                    for L in Ls_:
                        print('.', end='', flush=True)
                        pg.warn('apply useMats')
                        _testExp(L, useMats=False)

                except BaseException as e:
                    pg._r('+'*80)
                    pg._g(v.mesh)
                    pg._y('L:', L)
                    pg._r('-'*80)

                    print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()
                print()


    def test_FEA_Elastic_Expressions_Mapping(self):
        """Test Vector space expressions for elastic properties with mapping."""
        def eps(v):
            return sym(grad(v))

        def sigma(v):
            return lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        def sigmaT(v, T, scale):
            return sigma(v) - scale * T * I(v)

        #### START DEBUG WORKSPACE ############################################
        #mesh = createTestMeshs()[2]

        x = np.linspace(0.0, 1.0, 3)
        #mesh = pg.createGrid(x=x, y=x, z=x)
        #mesh = pg.meshtools.refineHex2Tet(mesh)
        mesh = pg.createGrid(x=x, y=x)
        mesh = createTestMeshs()[3]
        mesh = mesh.createMeshByCellIdx([0,1])
        print(mesh)

        v = VectorSpace(mesh, p=2)
        vE = VectorSpace(mesh, p=2)
        vE.elastic = True
        vE.voigt = True

        lam = 3.14
        mu = 0.2
        alpha = 0.3

        C0 = createElasticityMatrix(lam=lam, mu=mu, dim=mesh.dim(),
                                    voigtNotation=True)
        C03 = createElasticityMatrix(lam=lam, mu=mu, dim=3,
                                     voigtNotation=True)

        cC = np.asarray([C0] * mesh.cellCount())
        s = ScalarSpace(mesh, p=2)
        T = FEASolution(s, values=pg.x(s.mesh), name='T')

        C = cC
        C = C0
        C = np.asarray([C03] * vE.mesh.cellCount())
        C = C03

        #########################################
        ### LHS + RHS const per cell

        # LR = grad(v) * sigmaT(v, 1, (3*lam + 2*mu)* alpha)
        # #L = grad(vE) * (C*eps(vE) - C*alpha*I(vE))
        # L = grad(vE) * C*(eps(vE) - alpha*I(vE))


        # #halt
        # RT = _testExp(LR)
        # pg._g(RT); print()

        # R = L.assemble(core=False)
        # pg._g(R); print(R==RT)
        # #pg.core.setDeepDebug(-1)
        # R = L.assemble(core=True)
        # pg.core.setDeepDebug(0)
        # pg._y(R); print(R==RT)
        # R = L.assemble(useMats=True)
        # pg._r(R); print(R==RT)

        #halt
        #_testExp(L, LR)
        #halt

        #return
        #### END DEBUG WORKSPACE ##############################################

        for i, mesh in enumerate(createTestMeshs()[2:]):

            v = VectorSpace(mesh, p=2)
            vE = VectorSpace(mesh, p=2)
            vE.elastic = True
            vE.voigt = True

            lam = 3.14
            mu = 0.2
            alpha = 0.3

            C0 = createElasticityMatrix(lam=lam, mu=mu, dim=v.mesh.dim(),
                                         voigtNotation=True)
            cC = np.asarray([C0] * v.mesh.cellCount())

            C03 = createElasticityMatrix(lam=lam, mu=mu, dim=3,
                                         voigtNotation=True)
            cC03 = np.asarray([C03] * vE.mesh.cellCount())

            s = ScalarSpace(mesh, p=2)
            T = FEASolution(s, values=pg.x(s.mesh), name='T')

            try:
                ## test basics for mapped vector space
                for L in [
                            lambda v: grad(v) * I(v),
                            lambda v: grad(v) * alpha*T*I(v),
                            lambda v: grad(v) * (alpha*T*I(v)),
                            lambda v: grad(v) * (alpha*T)*I(v),
                          ]:

                    _testExp(L(v))
                    _testExp(L(vE), L(v))

                ## test more complex expressions with elasticity Matrix
                for C in [C0,
                          cC
                          ]:

                    LR = grad(v) * (mesh.dim()*lam + 2*mu)* alpha * I(v)
                    for L in [
                                grad(vE) * C*alpha*I(vE),
                                grad(vE) * (C*alpha*I(vE)),
                                grad(vE) * alpha*C*I(vE),
                                grad(vE) * alpha*(C*I(vE)),
                            ]:
                        pass
                        _testExp(L, LR)

                    LR = grad(v) * sigma(v)
                    _testExp(LR)
                    _testExp(grad(vE) * C*eps(vE), LR)
                    _testExp(grad(vE) * C*grad(vE), LR)

                    LR = grad(v) * (alpha*(2*mu + mesh.dim()*lam))*I(v)
                    _testExp(LR)
                    _testExp(grad(vE) * (C*alpha*I(vE)), LR)

                    LR = grad(v) * sigmaT(v, 1, alpha)
                    _testExp(LR)
                    _testExp(grad(vE) * (C*eps(vE) - alpha*1*I(vE)), LR)

                    LR = grad(v) * sigmaT(v, 1, (2*mu + mesh.dim()*lam)* alpha)
                    _testExp(LR)
                    L = grad(vE) * (C*eps(vE) - C*alpha*I(vE)); _testExp(L, LR)
                    L = grad(vE) * C*(eps(vE) - alpha*I(vE));  _testExp(L, LR)

                    LR = grad(v) * (alpha*(2*mu + mesh.dim()*lam)*T*I(v))
                    _testExp(LR)
                    _testExp(grad(vE) * (C*alpha*T*I(vE)), LR)

                    LR = grad(v) * sigmaT(v, T, alpha)
                    _testExp(LR)
                    _testExp(grad(vE) * (C*eps(vE) - alpha*T*I(vE)), LR)

                    LR = grad(v) * sigmaT(v, T, (2*mu + mesh.dim()*lam)*alpha)
                    _testExp(LR)
                    _testExp(grad(vE) * (C*eps(vE) - C*alpha*T*I(vE)), LR)
                    _testExp(grad(vE) * C*(eps(vE) - alpha*T*I(vE)), LR)
                    print('.', end='', flush=True)

                ## 2D but 3D elasticity Matrix
                if mesh.dim() == 2:
                    for C in [C03,
                             cC03,
                            ]:
                        ### RHS const per cell
                        LR = grad(v) * (alpha*(3*lam + 2*mu))*I(v)
                        _testExp(LR)
                        L = grad(vE) * (C*alpha*I(vE))
                        _testExp(L, LR)

                        ### LHS + RHS const per cell
                        LR = grad(v) * sigmaT(v, 1, (3*lam + 2*mu)* alpha)
                        _testExp(LR)
                        L = grad(vE) * (C*eps(vE) - C*alpha*I(vE))
                        _testExp(L, LR)
                        L = grad(vE) * C*(eps(vE) - alpha*I(vE))
                        _testExp(L, LR)

                        ### LHS const per cell
                        LR = grad(v) * sigma(v)
                        _testExp(LR)
                        L = grad(vE) * (C*eps(vE))
                        _testExp(L, LR)

                        ### RHS per quadrature
                        LR = grad(v) * (alpha*(3*lam + 2*mu))*T*I(v)
                        _testExp(LR)
                        L = grad(vE) * (C*alpha*T*I(vE))
                        _testExp(L, LR)

                        ### LHS + RHS per quadrature
                        LR = grad(v) * sigmaT(v, T, (3*lam + 2*mu)* alpha)
                        _testExp(LR)
                        L = grad(vE) * (C*eps(vE) - C*alpha*T*I(vE))
                        _testExp(L, LR)
                        L = grad(vE) * C*(eps(vE) - alpha*T*I(vE))
                        _testExp(L, LR)

                        print('.', end='', flush=True)
            except BaseException as e:
                pg._r('+'*80)
                pg._g(f'mesh {i}, {v.mesh}', v.mesh.dim())
                pg._y(f'C: {C}')
                pg._y('L:', L)
                pg._r('-'*80)

                print(e)
                import traceback
                traceback.print_exc(file=sys.stdout)
                exit()


    def test_FEA_Identity_Expressions(self):
        r"""Test Expressions with \int identity * x.

        Only meaningful for nCoeff > 1
        For dim == 1 its the same like 1.

        For linear form and dim > 1 it ensures only main diagonal elements
        dFx/dx, dFy/dy but no dFx/dy and so on.
        For bilinear form keep side elements

        grad(v) * I(v);  (shortcut grad(v))     -> L-form (remove d_ij and d_ji)
        grad(v) * b*I(v); (shortcut x*grad(v))  -> L-form (remove d_ij and d_ji)
        grad(v) * (tr(e(v))*I(v))               -> BL-form

        I == I(dim) | I(v)

        I * x == x * I with x FEASpace|FEAOP

        TODO
        ----
            * grad(v) * (tr(e(v)) * I + b * I)-> BL-form () + L-form (grad(v)*b)
            * grad(v) * (tr(e(v) + a) * I   -> BL-form () + L-form(grad(v) * aI)

            * think of removing I completely

            * I(v) * grad(v) (LF) -> grad(v) (LF) explicit remove all d_ij
              instead of sum over all columns

            * need check who uses grad(v) LF and needs sum [d_ii + d_ij, d_jj + d_ji]
                grad(v) + tr(e)*I != grad(v) + tr(e) -> ambiguity

        """
        def eps(v):
            return sym(grad(v))

        def sigma(v):
            # shortcut version, fails for evaluation!!
            return lam*tr(eps(v)) + 2.0*mu*eps(v)

        def sigmaI1(v):
            # "save" version same like sigma
            return lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        def sigmaI2(v):
            # preferred version same like sigma -- only 3D
            return lam*tr(eps(v))*I + 2.0*mu*eps(v)

        ms = createTestMeshs()

        #### START DEBUG WORKSPACE ############################################
        mesh = pg.createGrid(2, 2)
        mesh = ms[2]
        v = VectorSpace(mesh, p=1)
        s = ScalarSpace(mesh, p=1)

        f = asFunction('x²')
        fS = FEASolution(s, values=f)

        #L = -grad(v) * I(v)
        # print(L.dump())
        # _assemble(L)
        # _testExp(L)

        #L = grad(v) * f
        #L = grad(v) * fS
        #L = grad(v) * I(v)*f
        #L = grad(v) * f*I(v)
        #L = grad(v) * fS*I(v)
        #L = grad(v) * I(v)*fS
        #L = grad(v) * I(2)*fS
        L = grad(v) * I(2)

        _testExp(grad(v))

        RR = grad(v).assemble(core=False)
        pg._g(RR)

        #pg.core.setDeepDebug(-1)
        RT = L.assemble(core=False)
        pg._y(RT)
        #_assemble(L)
        #RT = L.assemble(core=True)
        #R[A.rowIDs()] += r[0].T ## dxx ## without I mult
        #R[A.rowIDs()] += r[3].T ## dyy ## without I mult

        #R[A.rowIDs()] += r[1].T ## dxy ## without I mult    # # print(R2)
        # # print(R1)
        #_assemble(L)
        #_testExp(L, grad(v))

        #return
        #### END TRACED VERSION   #############################################

        #### START complex expr. + eval
        lam = 2
        mu = 0.3
        u = parse(u='x² + x*y + y², y² - x*y - x²')
        p = parse(p='x²')

        mesh = pg.createGrid(3, 3)
        v = VectorSpace(mesh, p=2)
        uS = FEASolution(v, values=u)
        s = ScalarSpace(mesh, p=2)
        pS = FEASolution(s, values=p)

        def sigma(u):
            return lam*tr(eps(u))*I(u) + 2.0*mu*eps(u)

        for EQ in [
            lambda u, p: sigma(u) - p*I(u),
            lambda u, p: sigma(u) - I(u)*p,
            lambda u, p: sigma(u) - p*I(2),
            lambda u, p: sigma(u) - I(2)*p,
            #lambda u, p: sigma(u) - p*I,  # fail expression (shapes).. needed?
            #lambda u, p: sigma(u) - I*p,  # fail expression (shapes).. needed?
            ]:

            _testExp(grad(v)*EQ(v, pS))                  ## assembling
            self.assertEqual(EQ(u, p)(1), EQ(uS, pS)(1)) ## evaluation
        #### END complex expr. + eval

        for i, mesh in enumerate(ms[0:]):
            lam = 3.14
            mu = 0.2

            for p in [1, 2]:

                pg.info('mesh:', mesh, 'p:', p)
                v = VectorSpace(mesh, p=p)
                dv = grad(v)

                Ls = [
                        dv,
                        [I(v)*dv, dv],
                        [I*dv, dv],
                        [dv*I(v), dv],
                        [dv*-I(v), -dv],
                        [-dv*I(v), -dv],
                        [dv*I, dv],
                        lam*tr(dv) * dv,
                        [lam*dv*I(v), lam*dv],
                        [lam*dv*I, lam*dv],
                        [lam*tr(dv)*I * dv, lam*tr(dv) * dv],
                        [lam*I(v)*tr(dv) * dv, lam*tr(dv) * dv],
                        [I(v)*lam*tr(dv) * dv, lam*tr(dv) * dv],
                        [lam*I(v)*tr(dv) * dv, lam*tr(dv) * dv],
                        [lam*tr(dv)*I(v) * dv, lam*tr(dv) * dv],
                        [dv * (lam*tr(dv)*I), lam*tr(dv) * dv],
                        [dv * (lam*tr(dv)*I(v)), dv * (lam*tr(dv))],
                        dv*(lam*tr(dv) + 2*mu*dv),
                        dv*(lam*tr(dv)*I + 2*mu*dv),
                        dv * sigma(v),
                        dv * sigmaI1(v),
                        dv * sigmaI2(v),
                     ]

                try:
                    for L in Ls:
                        print('.', end='', flush=True)
                        _testExp(L)

                except BaseException as e:
                    pg._r('+'*80)
                    pg._g(f'({i}) {v.mesh} p:{p}')
                    pg._y('L:', L)
                    pg._r('-'*80)

                    print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()
                print()


    def test_FEA_Misc_Expressions(self):
        """
        Test for more complex expressions which results in scaled useMult.

        like:
        L = dt * (grad(u) * a * grad(u))
        R = dt * (a * u)

        L = dt/c() * (grad(u) * a * grad(u))
        L = c()/dt * (grad(u) * a * grad(u))
        Ensure c(x|t) only evaluated on cell center.
        """
        x = np.linspace(0, 1, num=4) # don't use num<5 (ambiguity warning!)
        mesh = pg.createGrid(x)
        u = ScalarSpace(mesh, p=1)

        @FEAFunction
        def f(x, **kwargs):
            t = kwargs['time']
            #print(t)
            return (4.*np.pi**2)*np.exp(-t)*np.cos(2*np.pi*pg.x(x))

        def f0(x, **kwargs):
            t = 0.3
            return (4.*np.pi**2)*np.exp(-t)*np.cos(2*np.pi*pg.x(x))

        s = FEASolution(space=u, values=f0(mesh.positions()))

        aC = f0(mesh.cellCenters())

        cF2 = FEAFunction(lambda p: pg.x(p)**2)
        cF2.evalOnCells = True
        qF2 = FEAFunction(lambda p: pg.x(p)**2)
        qF2.evalOnQuads = True
        cF = FEAFunction(lambda p: 2)
        cF.evalOnCells = True

        dt = 0.1

        #### START DEBUG WORKSPACE ############################################
        # f = 2.0
        # L1 = 1/cF*(grad(u) * f * grad(u))
        # L2 = 1/2.0*(grad(u) * f * grad(u))

        # print(L1.expand())
        # print(L2.expand())

        # _assemble(L1)
        # _assemble(L2)

        #_testExp(L1, L2)
        #return
        #### END DEBUG WORKSPACE ##############################################

        for mesh in createTestMeshs()[1:]:
            for p in [1, 2]:

                pg.info('mesh:', mesh, 'p:', p)
                aC = f0(mesh.cellCenters())
                u = ScalarSpace(mesh, p=p)
                f = FEAFunction(lambda _x: pg.utils.dist([_x]))
                sv = FEASolution(space=u, values=f(u.mesh.positions()))
                s = FEASolution(space=u, values=abs(f(u.mesh.positions())))

                cF = FEAFunction(lambda p: 2)
                cF.evalOnCells = True
                cC = cF(mesh.cellCenters())

                for i, f in enumerate([2.0, aC, s, sv]):
                    for j, L in enumerate([
                        2.0 * (f * grad(u) * grad(u)),
                        2.0 * (grad(u) * f * grad(u)),
                        2.0 * (f * u),
                        (f * u) * 2.0,
                        [cF*(u * u), (u * cF * u)],
                        [cF2*(u * u), (u * cF2 * u)],
                        [1/cC*(grad(u) * f * grad(u)),
                         1/2.0*(grad(u) * f * grad(u))],
                        [1/cF*(grad(u) * f * grad(u)),
                         1/2.0*(grad(u) * f * grad(u))],
                        [(1/cF)*(grad(u) * f * grad(u)),
                         1/2.0*(grad(u) * f * grad(u))],
                        [cC/0.5*(grad(u) * f * grad(u)),
                         4.0*(grad(u) * f * grad(u))],
                        [cF/0.5*(grad(u) * f * grad(u)),
                         4.0*(grad(u) * f * grad(u))],
                        [(cF/0.5)*(grad(u) * f * grad(u)),
                         4.0*(grad(u) * f * grad(u))],
                        [-cF/0.5*(grad(u) * f * grad(u)),
                         -4.0*(grad(u) * f * grad(u))],
                        [-(cF/0.5)*(grad(u) * f * grad(u)),
                         -4.0*(grad(u) * f * grad(u))],
                        [u*u + dt*(grad(u)*grad(u)),
                         u*u - dt*-(grad(u)*grad(u))],
                        ]):

                        try:
                            print('.', end='', flush=True)
                            _testExp(L)
                        except BaseException:
                            pg._r('+'*60)
                            pg._r(mesh, 'dim:', mesh.dim())
                            pg._y(f'L:{i},{j}: {L}')
                            pg._r('-'*60)
                            sys.exit()
                print()


    def test_FEA_Mixed_Expressions(self):
        """Test Mixed Elements (Taylor Hood)(vector(p2) + scalar(p1))
           expressions.
        """
        #### START DEBUG WORKSPACE ############################################
        # _testExp(L)
        # mesh = createTestMeshs()[1]
        # v, u = TaylorHood(mesh)
        # fu = pg.x
        # fv = lambda p: [pg.x(p)**2, pg.y(p)**2, pg.z(p)**2]
        # #L = div(v)*u
        # L = u*fu

        # _assemble(L)
        #return

        #### END DEBUG WORKSPACE ##############################################

        for mesh in createTestMeshs()[0:]:

            pg.info('mesh:', mesh)

            v, u = TaylorHood(mesh)

            fu = pg.x
            fv = lambda p: [pg.x(p)**2, pg.y(p)**2, pg.z(p)**2]

            K = np.diag(np.ones(mesh.dim()))
            KI = np.linalg.inv(K)

            c = ConstantSpace(dofOffset=u.dofs.stop)

            try:
                for L in [u*fu, ### to check for correct indexing
                          fu*u, ### to check for correct indexing
                          v*fv, ### to check for correct indexing
                          fv*v, ### to check for correct indexing
                          u*fu + v*fv,
                          div(v),
                          div(v)*u,
                          u*div(v),
                          v,
                          v*KI*v,
                          c*u + u*c,
                          v*KI*v - div(v)*u - u*div(v) + c*u + u*c,
                          v*KI*v + grad(u)*v + v*grad(u) + c*u + u*c,
                        ]:
                    print('.', end='', flush=True)
                    _testExp(L)

            except BaseException:
                pg._g(u.mesh)
                pg._y(L)
                pg._g('-'*80)

                exit()
            print()


    def test_FEA_Region_Expressions(self):
        """Test for expression with region maps as arguments."""
        pr = Parameters(showDim=False, regions={2:'region-2', 1:'region-1'})

        a  = pr(a=[2, 1])       # need to be in same order like in constructor
        b  = pr(b={1:3, 2:6})

        mesh = createTestMeshs()[2]
        mesh.setCellMarkers([1,1,2,2])

        v = VectorSpace(mesh, p=1)
        s = ScalarSpace(mesh, p=1)

        aC = a.cellValues(mesh)
        bC = b.cellValues(mesh)
        self.assertEqual(aC, mesh.cellMarkers())
        self.assertEqual(bC, mesh.cellMarkers()*3)
        #### START DEBUG WORKSPACE ############################################
        #L = v*b
        # pg._g(L)
        #A1 = L.assemble(core=False); pg._g(A1)
        #A2 = L.assemble(core=True); pg._y(A2)
        # pg.core.setDeepDebug(-1)
        # pg.core.setDeepDebug(0)
        #A3 = L.assemble(useMats=True); pg._r(A3)
        # #pg._g(L)
        #_testExp(L)
        #return
        #### END DEBUG WORKSPACE ############################################

        _testExp(s*a*s, s*aC*s)
        _testExp(s*b*s, s*bC*s)
        _testExp(v*b, v*bC)
        _testExp(grad(v)*b, grad(v)*bC)


    def test_FEA_Scalar_Expressions(self):
        """Test for scalar space expressions."""
        #### START DEBUG WORKSPACE ############################################
        # mesh = createTestMeshs()[1]
        # print(mesh)
        # p = 1
        # s = ScalarSpace(mesh, p=p, order=3)
        # v = VectorSpace(mesh, p=p+1, order=3)
        # vF = asFunction("x²+y²")
        # vS = FEASolution(v, grad(vF))

        # L = s*div(vS)    # OK
        # # L = s*(2*div(vS))  # OK
        # # L = s*2*div(vS)  # OK
        # # L = s*(div(vS)*2)  # OK
        # # L = s*div(vS)*2  # OK
        # #L = s*div(vS)/2    # Wannehave
        # #L = s*div(vS)*1/2  # Wannehave

        # R1 = L.assemble(core=False)
        # pg._g(R1)
        # R2 = L.assemble(core=True)
        # pg._y(R2)
        # R3 = L.assemble(useMats=True)
        # pg.core.setDeepDebug(-1)
        # pg.core.setDeepDebug(0)
        # pg._r(R3)


        # _testExp(L)

        #return

        #### END DEBUG WORKSPACE ##############################################

        ### START eval(s div(v))
        for i, mesh in enumerate(createTestMeshs()[0:]):
            p = 1
            s = ScalarSpace(mesh, p=p)
            v = VectorSpace(mesh, p=p+1)
            vF = asFunction("x²+y²")
            vS = FEASolution(v, grad(vF))

            for L in [s*div(vS),
                    s*(2*div(vS)),
                    s*(div(vS)*2),
                    s*2.*div(vS),
                    s*div(vS)*2.,
                    s*2*div(vS),
                    s*div(vS)*2,

                    ]:
                try:
                    _testExp(L)
                    print('.', end='', flush=True)
                except BaseException:
                        pg._r('+'*80)
                        pg._y(f'--- Scalar Expression: {L}')
                        pg._y(f'--- mesh({i}) = {mesh}')
                        pg._y(f'--- p={p}')
                        pg._r('-'*80)
                        exit()

        ### END eval(s div(v))
        #return

        for i, mesh in enumerate(createTestMeshs()[1:]):
            for p in [1, 2]:

                pg.info(f'{i}: mesh: {mesh} p: {p}')
                u = ScalarSpace(mesh, p=p)

                if p == 1:
                    uL = lambda p: pg.x(p) + pg.y(p) + pg.z(p)
                else:
                    uL = lambda p: pg.x(p)**2

                uF = FEAFunction(uL)
                uN = uF(mesh.positions())
                uS = FEASolution(space=u, values=uF(u.mesh))

                # R = u * uF
                # R = u * uS
                # R = u * uN   #defunct
                # R = u * uN * u ## needs work .. transpose problem
                #deepDebug(R, 3)

                ### special cases
                # _testExp(u*u)

                _testExp(u)
                _testExp(-u)
                _testExp(u+u, 2*u)
                _testExp(u-u, 0*u)
                _testExp(u*uF, u*uS) # special case to test interpolation of

                self.assertEqual((u*uS).assemble(),  (u*u).assemble()*uS.values)

                _testExp(u*u + u*u, 2*u*u)
                _testExp(u*u - u*u, 0*u*u)

                #exit()

                for f in [None,
                    0.0,
                    #uF+uF,  # FEAFunction forms FEAOP -> sort to OP
                    2,
                    3.14,
                    pg.Vector(mesh.cellCount(), 3.14),
                    np.full(mesh.cellCount(), 3.14),
                    [3.14]*mesh.cellCount(),
                    lambda p: p[0],
                    # pg.Vector(mesh.nodeCount(), 3.14),
                    # np.full(mesh.nodeCount(), 3.14),
                    # [3.14]*mesh.nodeCount(),
                    # uN, ## need default decision about handling
                    # -uN, ## need default decision about handling
                    uF,
                    -uF,
                    uS,
                    -uS,
                    uS*uS,
                    1.0*uS,
                    uS*2.0,
                    -2*uS*0.5,
                    uS+uS,
                    1.0 + uS,
                    uF + 1.0,
                    1/2*(uS+uS),
                      ]:
                    try:
                        for L in [u*f,
                                    [f*u, u*f],
                                   -u*f,
                                   [f*-u, -u*f],
                                   f*u*u,
                                   u*f*u,
                                   u*(f*u),
                                   # f*(grad(u)*grad(u)), ambig. for f != scalar
                                   f*grad(u)*grad(u),
                                   grad(u)*f*grad(u),
                                   grad(u)*(f*grad(u)),
                                  ]:
                            print('.', end='', flush=True)
                            _testExp(L)

                        ## anisotropy
                        if mesh.dim() == 2:
                            A = pg.solver.createAnisotropyMatrix(1.0, 10.0,
                                                        45./360 * (2*np.pi))
                            L = grad(u) * A * grad(u)
                            _testExp(L)

                    except BaseException:
                        pg._r('-'*80)
                        pg._y(f'--- Scalar Expression: {L}')
                        pg._y(f'--- mesh={mesh}')
                        pg._y(f'--- p={p}')
                        pg._y(f'--- f{type(f)}: {f}')
                        pg._y(f)
                        pg._g(u.mesh)
                        pg._r('+'*80)
                        exit()
                print()

    def test_FEA_Scalar_Expressions_anisotropy(self):
        """Test for scalar space expressions with anisotropy."""
        #### START DEBUG WORKSPACE ############################################
        mesh = createTestMeshs()[2]

        p = 1
        s = ScalarSpace(mesh, p=p, order=3)
        C1 = asAnisotropyMatrix(*[2.2] * mesh.dim())
        C2 = [C1]*mesh.cellCount()

        L = grad(s)* C2*grad(s)
        L = grad(s)* (C2*grad(s))

        # R1 = L.assemble(core=False)
        # pg._g(R1)
        # R2 = L.assemble(core=True)
        # pg._y(R2)
        # R3 = L.assemble(useMats=True)
        # pg._r(R3)
        #_testExp(L)
        #return
        #### END DEBUG WORKSPACE ##############################################

        for i, mesh in enumerate(createTestMeshs()[2:]):
            for p in [1, 2]:
                s = ScalarSpace(mesh, p=p)
                C1 = asAnisotropyMatrix(*[2.2] * mesh.dim())
                C2 = [C1]*mesh.cellCount()

                for L in [grad(s)* C1*grad(s),
                          grad(s)* C2*grad(s),
                          grad(s)* (C2*grad(s)),
                        ]:
                    try:
                        _testExp(L)
                        print('.', end='', flush=True)
                    except BaseException:
                            pg._r('+'*80)
                            pg._y(f'--- mesh({i}) = {mesh}')
                            pg._y(f'p={p}')
                            pg._y(f'Scalar Expression: {L}')
                            pg._r('-'*80)
                            exit()
        print()


    def test_FEA_Vector_Expressions(self):
        """Test for vector space expressions."""
        #### START DEBUG WORKSPACE ############################################
        # mesh = createTestMeshs()[2]
        # s = ScalarSpace(mesh, p=p, order=3)
        # vF = grad(asFunction("x²+y²"))
        # vS = FEASolution(v, vF)

        # L = s*grad(vF)
        # L = s*grad(vS)

        # L = s*div(vF)
        # L = s*div(vS)

        # L = s*div(vF)

        #halt        # L = v * vF2
        # L = v * vF

        # R3 = L.assemble(useMats=True)
        # pg._g(R3)
        # R1 = L.assemble(core=False)
        # pg._g(R1)

        # _assemble(L)
        # # E = L.apply(0)
        # R1 = L.assemble(core=False)
        # #return
        # R2 = L.assemble(core=True)
        # pg._y(R2)
        # # pg.core.setDeepDebug(-1)
        # # pg.core.setDeepDebug(0)
        #pg._y(R3)

        #_testExp(L)

        #return

        #### END DEBUG WORKSPACE ##############################################

        ms = createTestMeshs()

        for mi, mesh in enumerate(ms[0:]):
            for p in [1, 2]:
                pg.info(f'{mi}, mesh: {mesh} p: {p}')

                u = ScalarSpace(mesh, p=p)
                v = VectorSpace(mesh, p=p, order=3)

                if p == 1:
                    vF = lambda p: [pg.x(p), pg.y(p), pg.z(p)]
                    uF = lambda p: pg.x(p) + pg.y(p) + pg.z(p)
                else:
                    vF = lambda p: [pg.x(p)**2, pg.y(p)**2, pg.z(p)**2]
                    uF = lambda p: pg.x(p)**2

                vSol = FEASolution(space=v, values=np.array(vF(v.mesh)).T)

                vF2 = FEAFunction3(lambda p: [uF(p), 1.0, 1.0])

                uF  = FEAFunction(uF) ## to test for the same like vF2
                uF.evalOnQuads = True

                uF_NC = FEAFunction(uF)
                uF_NC.evalOnCells = True

                vSol2 = FEASolution(space=v,
                    values=np.asarray([vF2(p) for p in v.mesh.positions()]))

                uSol = FEASolution(space=u, values=np.array(uF(u.mesh)).T)

                K = np.diag(np.ones(mesh.dim()))
                KI = np.linalg.inv(K)

                ### TODO .. interesting Test!!
                L =  v * (vF2*0. + 1) ## new Test!!
                ### TODO .. interesting Test!!
                vF3 = parse(u='(a - y + x)², (b + x +y )², (c + x - z)²',
                            a=1.1, b=2.2, c=3.3)[0]

                #L =  v * vSol
                # print(mesh)
                #deepDebug(L, 1)
                i = 0
                try:
                    for i, f in enumerate([None,
                            0.0,
                            3.14,
                            # heterogenous Pos fails for m1 with 3-cells,
                            # due to ambiguity cellCount() vs. R3)
                            pg.Pos([3.14, 3.14, 3.14]),
                            [3.14]*3,
                            vF,
                            vF2,
                            vF3,
                            vSol,
                            vSol2,
                            [uSol, 1.0, 1.0],
                            [-uSol, 0.0, 0.0],
                            [0.0, uSol, 0.0],
                            [uF, 0, 0],
                            [-uF, 0, 0],
                            [0, uF, 0],
                            [0, uF_NC, 0],
                            ]):

                        for L in [v*f,
                                  f*v,
                                  #f*grad(v), # needs implementation
                                  #grad(v)*f, # needs implementation
                                  ]:
                            print('.', end='', flush=True)
                            _testExp(L)

                    for f in [None,
                            0.0,
                            3.14,
                            ]:
                        #pg.Pos([3.14, 3.14, 3.14]), // don't work but
                        # unsure if this even make sense, probably an
                        # anisotropy matrix is needed instead

                        for L in [v*f*v,
                                v*(f*v),
                                grad(v)*f*grad(v),
                                ]:
                            print('.', end='', flush=True)
                            _testExp(L)

                    ###################################################
                    ### anisotropy
                    K = np.diag(np.ones(mesh.dim()))
                    KI = np.linalg.inv(K)

                    L = v * KI * v
                    _testExp(L)

                    ###################################################
                    ### constitutive matrix for elastic problems

                    if mesh.dim() > 1:
                        C = createElasticityMatrix(E=1,
                                                   nu=0.1,
                                                   dim=mesh.dim(),
                                                   voigtNotation=True)
                        v.elastic = True
                        v.voigt = True
                        L = grad(v) * C * grad(v)
                        _testExp(L)

                except BaseException as e:
                    pg._r('+'*80)
                    pg._g(u.mesh)
                    pg._y(f'p: {p}')
                    pg._y(f'L: {L}')
                    pg._g(f'f(#{i}): {f}')
                    pg._r('-'*80)

                    print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()

                print()


class TestFEAEval(TestCollection):
    """Test evaluation of finite element expressions."""
    def test_FEA_Identity_Eval(self):
        """Test evaluation of expression with Identity operator."""
        ms = createTestMeshs()

        ## Evaluation with I
        mesh = ms[2]
        # print(mesh)
        # print(mesh.dim())

        s = ScalarSpace(mesh, p=2)
        v = VectorSpace(mesh, p=2)
        T = FEAFunction(lambda p: pg.x(p))

        vF2 = parse(v='(x² + x*y + y², x² - x*y + y²)')
        vF3 = parse(v='(x² + x*y + y², x² - x*y + y², 0)')

        vS2 = FEASolution(v, values=vF2(v.mesh))
        uS = FEASolution(s, values=T(s.mesh))

        cV = [1.0] * s.mesh.cellCount()


        eps = lambda v: sym(grad(v))
        lam = 2.0
        mu = 0.5
        #### START DEBUG WORKSPACE ############################################
        # L = (cV * uS) * I(v)
        # #_testExp(L)
        # # pg.core.setDeepDebug(-1)
        # # print(L(vS2)(1, dim=3))
        # pnts = 1.0
        # print(L(pnts))
        # # pg.core.setDeepDebug(0)
        # return
        #### END DEBUG WORKSPACE ##############################################

        L = lambda v: grad(v) * I
        self.assertEqual(L(vS2)(1), L(vF2)(1))
        self.assertEqual(L(vS2)(1, dim=3), L(vF3)(1))

        sig3 = lambda v: lam*tr(eps(v))*I + 2.0*mu*eps(v) ## allways 3D
        sig2 = lambda v: lam*tr(eps(v))*I(2) + 2.0*mu*eps(v) ## allways 2D
        ## depending dim of v (preffered)
        sig1 = lambda v: lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)
        ## allways 2D .. evaluation will fail!
        sig0 = lambda v: lam*tr(eps(v)) + 2.0*mu*eps(v)

        p = 1.0
        self.assertEqual(sig3(vF3)(p), sig3(vS2)(p, dim=3), atol=1e-14)
        self.assertEqual(sig2(vF2)(p), sig2(vS2)(p), atol=1e-14)

        self.assertEqual(sig1(vF2)(p), sig1(vS2)(p), atol=1e-14)
        self.assertEqual(sig1(vF3)(p), sig1(vS2)(p, dim=3), atol=1e-14)

        # print(sig0(vS2)(p)) # need to be wrong result scalar + matrix instead of scalar*I + matrix!!
        # print(sig1(vS2)(p))
        # print(sig2(vS2)(p))
        # print(sig3(vS2)(p))
        self.assertEqual(sig1(vS2)(p), sig2(vS2)(p), atol=1e-14)
        self.assertEqual(sig1(vS2)(p), sig3(vS2)(p), atol=1e-14)

        # print(sig0(vS2)(p)) # need to be wrong result scalar + matrix instead of scalar*I + matrix!!
        # self.assertEqual(sig2(vF2)(p), sig0(vS2)(p), atol=1e-14)
        # self.assertEqual(sig3(vF2)(p), sig0(vS2)(p), atol=1e-14)


    def test_FEASolution_Eval(self):
        """Test evaluation of FEA solutions."""
        x = [-2, -1.0, 0.0, 1.0, 2.]
        mesh = pg.createGrid(x=x, y=x)

        ## linear field u = x, p=1 exact constant gradient = (1, 0)
        u = ScalarSpace(mesh, p=1)
        p1 = FEASolution(u, values=pg.x(u.mesh))
        p2 = FEASolution(u, values=pg.x(u.mesh))
        p = p1
        ## test simple operations on FEASolutions, e.g., for normL2
        f = FEAFunction(lambda p: 1 + pg.x(p))

        #self.assertEqual((f - p), -(p - f)) # expr test is with str -> fail
        self.assertEqual((f - p).values, -(p - f).values)
        #self.assertEqual((p1 - p2), -(p2 - p1)) # expr test is with str -> fail

        np.testing.assert_equal(normL2(p1-p2), 0.0)

        gp1 = grad(p).eval()
        gp2 = pg.solver.grad(mesh, p.values)
        self.assertEqual(grad(p).eval(0), [1.0, 0.0], atol=1e-16)
        self.assertEqual(grad(p).eval(pg.Pos([0.0, 0.0])), [1.0, 0.0], atol=1e-16)
        self.assertEqual(grad(p).eval([0.0, 0.0]), [1.0, 0.0], atol=1e-16)
        self.assertEqual(pg.utils.dist(grad(p)(mesh.cellCenters())),
                   pg.utils.dist(gp2), atol=1e-16)

        ## linear field u = x, p=2, exact constant gradient = (1, 0)
        u = ScalarSpace(mesh, p=2)
        p = FEASolution(u, values=pg.x(u.mesh))

        gp1 = grad(p).eval()
        gp2 = pg.solver.grad(mesh, p.values)
        self.assertEqual(grad(p).eval([0.0, 0.0]), [1.0, 0.0], atol=1e-16)

        ## quadratic solution u = x^2, p=2, exact gradient = 2x(x, y)
        ## check with 1D case first
        mesh = pg.createGrid(x=[-2, -1.0, 0.0, 1.0, 2.])

        u = asFunction('x²')
        s = ScalarSpace(mesh, p=2)
        p = FEASolution(s, values=u(s.mesh))

        xt = np.linspace(-2, 2, 21)
        pts = s.mesh.cellCenters()
        self.assertEqual(u(xt), p(xt), atol=1e-15)
        ### grad exact for cell center

        self.assertEqual(grad(u)(pts)[:,0], grad(p)(pts), atol=1e-16)

        ### eval for more complex expressions
        a = lambda x: 2.
        L = a * grad(p)

        self.assertEqual(2*grad(u)(pts)[:,0], L.eval(pts), atol=1e-16)

        L = -(a * grad(p))
        self.assertEqual(-2*grad(u)(pts)[:,0], L.eval(pts), atol=1e-16)

        L = -grad(p)*a
        self.assertEqual(-2*grad(u)(pts)[:,0], L.eval(pts), atol=1e-16)

        c = FEAFunction(lambda x: -0.5)
        L = 1/c*grad(p)
        self.assertEqual(-2*grad(u)(pts)[:,0], L.eval(pts), atol=1e-16)

        L = grad(p)*1/c
        self.assertEqual(-2*grad(u)(pts)[:,0], L.eval(pts), atol=1e-16)

        #Kn2_.append((K_s * (A/(A + abs(h))**gamma))(n.pos()))
        ### interpolate prior to evaluate

        u = ScalarSpace(mesh, p=1)
        uS = FEASolution(u, values=-53.0 + pg.x(u.mesh)/2)
        mC = u.mesh.cellCenters()
        mN = u.mesh.positions()
        uIn = pg.interpolate(mesh, uS.values, mN)
        uIc = pg.interpolate(mesh, uS.values, mC)

        L = lambda v: abs(v)
        self.assertEqual(L(uIc), L(uS).eval(mC), atol=1e-16)
        self.assertEqual(L(uIn), L(uS).eval(mN), atol=1e-16)

        L = lambda v: 3.3 + abs(v)
        self.assertEqual(L(uIc), L(uS).eval(mC), atol=1e-16)
        self.assertEqual(L(uIn), L(uS).eval(mN), atol=1e-16)

        L = lambda v: 2.2/3.3 + abs(v)
        self.assertEqual(L(uIc), L(uS).eval(mC), atol=1e-16)
        self.assertEqual(L(uIn), L(uS).eval(mN), atol=1e-16)

        L = lambda v: 1.1 * (2.2/(3.3 + abs(v))**4.4)
        self.assertEqual(L(uIc), L(uS).eval(mC), atol=1e-16)
        self.assertEqual(L(uIn), L(uS).eval(mN), atol=1e-16)

        K_s = 0.00944; A = 1.175e6; gamma = 4.74
        L = lambda u: K_s * (A/(A + abs(u)**gamma))
        K = L(uS)

        K.interpolationOrder = 2 ## interpolate->evaluate
        self.assertEqual(L(uIc), K.eval(mC), atol=1e-16)
        self.assertEqual(L(uIn), K.eval(mN), atol=1e-16)

        K.interpolationOrder = 1 ## evaluate->interpolate
        self.assertEqual(pg.interpolate(mesh, L(uS(mN)), mN),
                         K.eval(mN), atol=1e-16)
        self.assertEqual(pg.interpolate(mesh, L(uS(mN)), mC),
                         K.eval(mC), atol=1e-16)

        ## TODO
        ### test grad on whole domain .. should be exact but eval
        ### from scalarfield does not work yet .. implement/check or fix
        ### FEAOP/Space eval only work for cell centers now . compare with
        ### FEASolution eval .. create Test!!!
        ### wannehave
        ### pg.show(grad(p), showMesh=1, ax=ax)
        ### pg.show(-grad(p), showMesh=1, ax=ax)
        ### pg.show(abs(v), showMesh=1, ax=ax)
        ### v = grad(p)
        ### v = -grad(p)
        ### v = -grad(p) @ K
        ### pg.abs(v) == abs(v).eval()
        ###
        ### FEAOP like (u-np.array(u.values)).eval()
        ### implement iterator for FEASolution and OP with FEASolutions
        return

        # pg.core.setDeepDebug(-1)
        print(grad(p).eval([ 0.0, 0.0]))
        #self.assertEqual(0, grad(p).eval([ 0.0, 0.0])[0])
        # pg.core.setDeepDebug(0)

        dg = [grad(p).eval([xi, 0.]) for xi in xt]

        print(dg)
        print(grad(p).eval(xt))


        exit()

        pg.plt.plot(pg.x(u.mesh.cellCenters()), grad(p).eval(), '-x')
        pg.plt.plot(xt, dg, '-o')

        #pg.plt.plot(xt, grad(p).eval([[xi, 0.] for xi in xt])[:,0])

        v = VectorSpace(mesh, p=2)
        dg = np.array([grad(p).eval([xi, 0.]) for xi in pg.x(v.mesh)])
        p = FEASolution(v, values=dg)

        pg.plt.plot(xt, p.eval(xt), '-o')

        ##### END some simple tests


    def test_FEASolution_Eval2(self):
        """Test more evaluation of FEA solutions.

        Interface test: FEASolution.eval(p, times)
        """
        ## compare p1 <-> p2 interpolation, check if p2 works correctly
        fu = lambda p: p**2.

        x = np.linspace(0.0, 1.0, 11)
        m = pg.createGrid(x=x)

        u1 = ScalarSpace(m, p=1)
        up1 = FEASolution(space=u1, values=fu(pg.x(u1.mesh)))
        u2 = ScalarSpace(m, p=2)
        up2 = FEASolution(space=u2, values=fu(pg.x(u2.mesh)))

        tx = np.linspace(0, 1, 101)
        self.assertEqual(np.linalg.norm(up1(tx)-fu(tx)), 0.018256505689753576)
        self.assertEqual(up2(tx), fu(tx), atol=1e-12)

        if 0:
            pg.plt.plot(tx, fu(tx))
            pg.plt.plot(tx, up1(tx), label='p1', lw=0.5)
            pg.plt.plot(tx, up2(tx), label='p2', lw=0.5)

        #### START DEBUG WORKSPACE ############################################
        # x = np.linspace(0, 2, 5)
        # m = pg.createGrid(x, x)
        # tMin = 0
        # tMax = 10
        # times = np.linspace(tMin, tMax, 5)
        # p = 1
        # uF, duF, p = parse(uF='x^p*t', duF='grad(uF)', p=p)

        # u = ScalarSpace(m, p=p)
        # ### create temporal scalar field u(p,t) = x*t
        # for t in times:
        #     uS = u.split(uF(u.mesh, t=t), time=t)

        # qPnts = u.uMat().quadraturePoints()

        # ## test interpolation for error norms

        # pnt = qPnts
        # t = [1, 2]
        # t = 1

        #pg._g(grad(uS)(pnt, time=t))
        # pg._g(grad(uS)(pnt, t=t))
        # pg._y(duF(pnt, t=t))

        # uF = asFunction('x² + y²')
        # u = ScalarSpace(m, p=2)
        # uS = FEASolution(space=u, values=uF(u.mesh))
        # qPnts = u.uMat().quadraturePoints()

        # guF = grad(uF)
        # guS = grad(uS)
        # for i, iqp in enumerate(qPnts):
        #     pg._g(guF(qPnts, time=t)[i])
        #     pg._y(guS(qPnts, time=t)[i])
        # pg._g(grad(uS)(pnt, t=t))
        # pg._y(duF(pnt, t=t))

        # pg.core.setDeepDebug(-1)
        # print((guF-guS)(qPnts))
        # pg.core.setDeepDebug(0)
        #self.assertEqual((guF-guS)(qPnts), grad(uF-uS)(qPnts))

        # self.assertEqual(((guF-guS)*(guF-guS))(qPnts), ((guF-guS)**2)(qPnts))
        # print(pg.timings())
        #exit()
        #### END DEBUG WORKSPACE ##############################################

        tMin = 0
        tMax = 10
        times = np.linspace(tMin, tMax, 5)
        x = np.linspace(0.0, 1.0, 5)
        m = pg.createGrid(x=x, y=x)

        uF = asFunction('x² + y²')
        u = ScalarSpace(m, p=2)
        uS = FEASolution(space=u, values=uF(u.mesh))
        qPnts = u.uMat().quadraturePoints()

        guF = grad(uF)
        guS = grad(uS)

        self.assertEqual((guF-guS)(qPnts), grad(uF-uS)(qPnts))
        self.assertEqual(((guF-guS)*(guF-guS))(qPnts), ((guF-guS)**2)(qPnts))

        for p in [1, 2]:
            uF, duF, p = parse(uF='x^p*t', duF='grad(uF)', p=p)

            ### create temporal scalar field u(p,t) = x*t
            u = ScalarSpace(m, p=p)
            for t in times:
                uS = u.split(uF(u.mesh, t=t), time=t)

            ## test time integration
            for pnt in [0.5, # match node
                        0.3, # no node
                        [0.1, 0.2, 0.3, 0.4],
                        [[0.1, 0.0, 0.0]]*2,
                        [[0.1, 0.0, 0.0]]*3,
                        [[0.1, 0.0, 0.0]]*4,
                        u.mesh,
                        u.mesh.positions(),
                        u.mesh.cellCenters(),
                        u.uMat().quadraturePoints(),
                    ]:

                try:
                    self.assertEqual(uS(pnt, time=tMin-1), uF(pnt, t=tMin),
                                     atol=1e-14)
                    self.assertEqual(uS(pnt, time=tMax+1), uF(pnt, t=tMax),
                                     atol=1e-14)

                    self.assertEqual(uS(pnt), uF(pnt, t=tMax), atol=1e-14)
                    self.assertEqual(grad(uS)(pnt), duF(pnt, t=tMax),
                                     atol=1e-14)

                    for t in [tMin,
                            1.56, # arbitrary time
                            tMax,
                            (tMax+tMin)/2,
                            np.array([1, 2]),
                            #np.array([1, 2, 3]),  to ambigues ?
                            np.array([1, 2, 3, 4]),
                            times]:

                        print('.', end='', flush=True)
                        self.assertEqual(uS(pnt, time=t), uF(pnt, t=t),
                                         atol=1e-14)
                        self.assertEqual(grad(uS)(pnt, time=t), duF(pnt, t=t),
                                         atol=5e-14)

                except BaseException:
                    pg._r('#'*50)
                    pg._r(f'p={p}')
                    pg._r(f'pnt={pnt}')
                    pg._y(f'time={t}')
                    pg._y(f'uS={uS(pnt, time=t)}')
                    pg._g(f'uF={uF(pnt, t=t)}')
                    pg._y(f'grad(uS)={grad(uS)(pnt, time=t)}')
                    pg._g(f'duF={duF(pnt, t=t)}')
                    exit()
            print()


    def test_FEA_Eval_Vectorize(self):
        """Test if and when evaluation is vectorized."""
        #### START DEBUG WORKSPACE ############################################
        x = np.linspace(0, 2, 3)
        mesh = pg.createGrid(x, x)

        uF = asFunction('sin(x)*cos(y)')
        u = ScalarSpace(mesh)
        uS = FEASolution(space=u, values=uF(u.mesh))

        qPnts = u.uMat().quadraturePoints()

        ## test interpolation for error norms
        # f = grad(uF-uS)
        # f = grad(uF)-grad(uS)

        # f = grad(uS)

        # f0 = f(qPnts[0])
        # print(np.sum(f0*f0, axis=1))

        # ref = [np.sum(f(p)*f(p), axis=1) for p in qPnts]

        # pg._g(len(ref), ref[0].shape)
        # pg._g(ref[0])

        # t = (f*f)(qPnts, dim=2)
        # pg._y(len(t), t[0].shape)
        # pg._y(t[0])

            # with pg.tictoc('test_FEASolution_Eval2_t1'):
        #     t1 = (f*f)(qPnts)
        # #print(pg.timings('test_FEASolution_Eval2_t1'))
        # pg._g()
        # with pg.tictoc('test_FEASolution_Eval2_t2'):
        #     ref = [f(p)*f(p) for p in qPnts]

        # print(pg.timings())
        #return
        #### END DEBUG WORKSPACE ##############################################

        ### Start test vectorized solution eval for quadrature points
        x = np.linspace(0.0, 1.0, 15)
        m = pg.createGrid(x=x, y=x)

        uF = asFunction('sin(x)*cos(y)')
        u = ScalarSpace(m)
        uS = FEASolution(space=u, values=uF(u.mesh))

        qPnts = u.uMat().quadraturePoints()

        f = uS*uS
        self.assertEqual(f.eval(qPnts)[0], f.eval(qPnts[0])) # ??

        ## test interpolation for error norms
        f = uF-uS
        with pg.tictoc('test_FEASolution_Eval2_t1'):
            ref = [f(p)*f(p) for p in qPnts]
        #print(pg.timings('test_FEASolution_Eval2_t1'))

        ## Half vectorized .. evaluate fun 2 times for each cell
        self.assertEqual(len(pg.SWatches()[
                        '/test_FEASolution_Eval2_t1/sp.f(x,y,z,*e)'].stored()),
                         2*u.mesh.cellCount())
        ## Half vectorized .. evaluate sol 2 times for each cell
        self.assertEqual(len(pg.SWatches()[
                        '/test_FEASolution_Eval2_t1/sol.eval: I*vr3'].stored()),
                         2*u.mesh.cellCount())

        with pg.tictoc('test_FEASolution_Eval2_t2'):
            ref = [f(p)**2 for p in qPnts]

        ## Half vectorized .. evaluate fun for each cell
        self.assertEqual(len(pg.SWatches()[
                        '/test_FEASolution_Eval2_t2/sp.f(x,y,z,*e)'].stored()),
                         u.mesh.cellCount())
        ## Half vectorized .. evaluate sol for each cell
        self.assertEqual(len(pg.SWatches()[
                        '/test_FEASolution_Eval2_t2/sol.eval: I*vr3'].stored()),
                         u.mesh.cellCount())

        with pg.tictoc('test_FEASolution_Eval2_t3'):
            t2 = (f*f)(qPnts)
        #print(pg.timings('test_FEASolution_Eval2_t3'))

        ## Full vectorized .. evaluate fun 2 times
        self.assertEqual(len(pg.SWatches()['/test_FEASolution_Eval2_t3/'
                                           'eval.vec: f(vqp)/call/'
                                           'sp.f(x,y,z,*e)'].stored()),
                         2)
        ## Full vectorized .. evaluate sol 2 times
        self.assertEqual(len(pg.SWatches()[
                       '/test_FEASolution_Eval2_t3/sol.eval: I*vvr3'].stored()),
                         2)

        with pg.tictoc('test_FEASolution_Eval2_t4'):
            t1 = (f**2)(qPnts)

        ## Full vectorized .. evaluate fun 1 time
        self.assertEqual(len(pg.SWatches()['/test_FEASolution_Eval2_t4/'
                                           'eval.vec: f(vqp)/call/'
                                           'sp.f(x,y,z,*e)'].stored()),
                         1)

        ## Full vectorized .. evaluate sol 1 time
        self.assertEqual(len(pg.SWatches()[
                       '/test_FEASolution_Eval2_t4/sol.eval: I*vvr3'].stored()),
                         1)

        self.assertEqual(t2, ref)
        self.assertEqual(t1, ref)

        f = grad(uF)-grad(uS)
        with pg.tictoc('test_FEASolution_Eval2_t5'):
            ref = [f(p)*f(p) for p in qPnts]
        #print(pg.timings('test_FEASolution_Eval2_t5'))

        self.assertEqual(len(pg.SWatches()['/test_FEASolution_Eval2_t5/'
                            'FEAop.eval/eval.forPos [p, ]/OP(p, c)/'
                            'sp.f3(x,y,z,t)'].stored()),
                        2*u.mesh.cellCount()*len(qPnts[0]))

        f = grad(uF)-grad(uS)
        with pg.tictoc('test_FEASolution_Eval2_t6'):
            t = (f*f)(qPnts)
        #print(pg.timings('test_FEASolution_Eval2_t6'))

        self.assertEqual(len(pg.SWatches()['/test_FEASolution_Eval2_t6/'
                            'FEAop.eval/->OP.eval/eval.vec: f(vqp)/'
                            'call/sp.f3(x,y,z,t)'].stored()),
                            2)

        ### END test vectorized solution eval for quadrature points


    def test_FEA_Expression_Eval(self):
        """Test for more complex expressions with FEASolution used for rhs.

        scalar * (complex_Expression)

        like:

        L = dt * (grad(u) * a * grad(s))
        R = dt * (a * u)
        R = dt/c() * (s * u)
        R = dt * (s * c() * u)
        """
        x = np.linspace(0, 1, 3)
        mesh = pg.createGrid(x, x)
        s = ScalarSpace(mesh, p=1)
        uS = FEASolution(space=s, values=pg.x(mesh)**2 + pg.y(mesh)**2)

        #### ----------------------------------------------------------------------
        # Reference
        ####
        R0 = (grad(s)*grad(s)).assemble() * uS.values

        ####
        # For Reference (core = False)
        ####
        R = np.zeros_like(R0)
        for c in mesh.cells():
            ### Unshorten for: (grad(u)*grad(s)).apply(c.id())

            A = grad(s).apply(c.id())
            E = copyE(A)
            r = np.zeros_like(E._mat[0])

            # TODO ## test with per cell value vs. per node vs. per quad,
            # TODO ## compare p1, p2
            for i, w in enumerate(E._w):
                fi = grad(uS).eval(E.entity().shape().xyz(E._x[i]))
                E._mat[i] *= (np.array([fi[0:A.cols()]]).T)
                r += (E._mat[i] * w * E.entity().size())

            for i in range(c.dim()):
                R[E.rowIDs()] += r[i].T

            # print(R)
        # pg._g(R)
        np.testing.assert_allclose(R0, R)
        ### the same like the loop above
        RT = (grad(uS)*grad(s)).assemble(core=False)
        np.testing.assert_allclose(R0, RT)

        # ----------------------------------------------------------------------
        ### For Reference
        R = np.zeros_like(R0)
        for c in mesh.cells():
            # TODO ## test with per cell value vs. per node vs. per quad,
            # TODO ## compare p1, p2

            E = pg.core.ElementMatrix(nCoeff=1,
                                      dofPerCoeff=s.dof,
                                      dofOffset=0)

            E.grad(c, s.order, elastic=False, sum=True, div=False)
            f = grad(uS).eval(c, dim=E.cols())

            E = pg.core.mult(E, f)
            #print('E*f', pg.core.mult(E, f))

            for i in range(c.dim()):
                R[E.rowIDs()] += E.mat().T[i]

        np.testing.assert_allclose(R0, R)

        ##(core = True): the same like the loop above
        L = grad(uS)*grad(s)
        _testExp(L)
        RT = L.assemble(core=True)
        np.testing.assert_allclose(R0, RT)

        #     print(R)

        # ----------------------------------------------------------------------
        ### For Reference
        R = pg.Vector(len(R0))
        duM = pg.core.ElementMatrixMap()
        pg.core.createdUMap(s.mesh, s.order, duM,
                            elastic=False, div=False,
                            kelvin=False, nCoeff=1, dofOffset=0)

        f = grad(uS).eval(dim=duM.mats()[0].cols())
        duM.integrate(f, R, alpha=1.0)
        np.testing.assert_allclose(R0, R)

        ## (useMats = True): This does the same like above
        #pg._b('##############################')
        uS.evalOrder = 0 ##
        RT = (grad(uS)*grad(s)).assemble(useMats=True)
        np.testing.assert_allclose(R0, RT)
        #exit()
        # ----------------------------------------------------------------------

        _testExp(grad(uS)*grad(s))
        _testExp(-0.1*(grad(uS)*grad(s)))
        _testExp(-0.1*(uS*s))

        c = FEAFunction(lambda x: 2) #ok
        #c = FEAFunction(lambda x: x) # wrong format .. need to fail
        c = FEAFunction(lambda x: pg.x(x)) #ok

        # ## start DEBUG
        # c.evalOrder = 2
        # uS.evalOrder = 2
        # R = s*(c*uS) #ok
        # R = (s*c)*uS #ok
        # R = (grad(s)*grad(uS))
        # # s is space
        # # u is solution
        # # c is function
        #R = uS*c*s

        # # R = -0.1*(u*c*s)
        # # R = -0.1*c*(s*u)
        # pg._g(R.assemble(core=False))
        # pg._y(R.assemble(core=True))
        # # pg.core.setDeepDebug(-1)
        # pg._r(R.assemble(useMats=True))
        # # pg.core.setDeepDebug(0)
        # # #exit()
        # _testExp(R)
        # return
        # ## end DEBUG

        #deepDebug(R, 3)

        uS.evalOrder = 2
        self.assertEqual((s*uS).assemble(), (s*s).assemble()*uS.values)
        self.assertEqual((grad(s)*grad(uS)).assemble(),
                  (grad(s)*grad(s)).assemble()*uS.values)

        u = uS
        for _c in [2, 0]:
            for _u in [2, 0]:
                c.evalOrder = _c
                u.evalOrder = _u

                for L in [
                            s*u,
                            u*s,
                            s*c,
                            s*(c*u),
                            (s*c)*u,
                            s*c*u,
                            u*c*s,
                            [s*c*u, s*(c*u)],
                            [s*c*u, (s*c)*u],
                            -0.1*(s*c*u),
                            [-0.1*(u*c*s), -0.1*c*(s*u)],
                            (grad(s)*grad(u)),
                            #(grad(s)*c*grad(u)), c*(grad(s)*grad(u)) #check and fix
                            #-0.1/c*(grad(s)*grad(u)), #check and fix
                        ]:
                    try:
                        print('.', end='', flush=True)
                        _testExp(L)
                    except BaseException:
                        pg._r('+'*60)
                        pg._y(f'c.evalOrder: {_c} u.evalOrder: {_u}')
                        pg._y(f'L: {L}')
                        pg._r('-'*60)
                        exit()
            print()


    def test_FEA_Expression_Eval2(self):
        """Test more complex expression evaluation."""
        #### START DEBUG WORKSPACE ############################################
        fu = lambda x: x**2.
        du = lambda x: 2.*x

        x = np.linspace(0, 1, 11)
        mesh = pg.createGrid(x)
        s = ScalarSpace(mesh, p=1)
        uS = FEASolution(space=s, values=fu(pg.x(s.mesh)))

        xt = np.linspace(0, 1, 8)
        pxt = [pg.Pos([x]) for x in xt]

        #print(xt)
        # ## only works if xt is not on node, or need mean of all cell centers.
        la = np.array([2.0*du(s.mesh.findCell([x]).center()[0]) for x in xt])
        #pg._g(la)

        # test cell values * f(solution)
        L = np.full(s.mesh.cellCount(), 2.0) * grad(uS)
        #pg._y(L.eval(pxt))

        np.testing.assert_allclose(L.eval(pxt), la)

        #exit()
        #### END DEBUG WORKSPACE ############################################

        ### exact tests for p=1
        ### u(x) == x² #
        ### du/dx = 2x #
        f, df = parse(f='x²', df='grad(f)')

        fu = lambda x: x**2.
        du = lambda x: 2.*x**1

        x = np.linspace(0, 1, 11)
        mesh = pg.createGrid(x)

        s = ScalarSpace(mesh, p=1)
        u = FEASolution(space=s, values=fu(pg.x(s.mesh)))
        L = grad(u)

        ## evaluate for every cell center
        gU = L.eval(mesh.cellCenters())
        np.testing.assert_allclose(gU, du(pg.x(mesh.cellCenters())))
        np.testing.assert_allclose(gU, df(pg.x(mesh.cellCenters()))[:,0])

        ## for p=1, gradient is constant for each cell
        gU = L.eval(mesh.positions())
        ## gradient at nodes depends on which cell (left or right) is asked,
        ## the test need to fail
        # np.testing.assert_allclose(gU, [du(p[0]) for p in mesh.positions()])

        ## For better values we would need to sum weighted over all neighbours,
        ## however the boundary values would stay wrong.
        ## Maybe compare harmonic vs. geometric mean.
        for n in mesh.nodes():
            w = 0.0
            gu = 0.0
            skipp = False
            for b in n.boundSet():
                if b.outside():
                    # don't check nodes on boundaries
                    skipp = True
            if skipp:
                continue

            for c in n.cellSet():
                dist = c.center().dist(n.pos())
                w += dist
                gu += L.eval(c.center()) * dist
            gu /= w
            np.testing.assert_allclose(gu, du(n.pos()[0]))

        ##### evaluate at arbitrary points
        ## P1 const for every cell center
        xt = np.linspace(0, 1, 30) ## no xt should be on x

        pxt = [pg.Pos([x]) for x in xt]

        s = ScalarSpace(mesh, p=1)
        uS = FEASolution(space=s, values=fu(pg.x(s.mesh)))
        uC = np.full(mesh.cellCount(), 2.0)

        L = uS
        la = fu(xt)
        # quadratic u can't fitted with p1 (projection vs. interpolation)
        self.assertEqual(np.linalg.norm(L.eval(pxt)-la), 0.009831913851993954)

        L = grad(uS)
        la = np.array([du(s.mesh.findCell([x]).center()[0]) for x in xt])
        np.testing.assert_allclose(L.eval(pxt), la)

        L = 2.0 * grad(uS)
        la = 2.0 * np.array([du(s.mesh.findCell([x]).center()[0]) for x in xt])
        np.testing.assert_allclose(L.eval(pxt), la)

        L = np.full(mesh.cellCount(), 2.0) * grad(uS)
        la = np.array([2.0*du(s.mesh.findCell([x]).center()[0]) for x in xt])
        np.testing.assert_allclose(L.eval(pxt), la)

        # Note quadratic u cannot fit to p1 (projection vs. interpolation)

        #### P1 #######
        f = uC  ## per cell
        # f evaluated at specific cell
        ###########
        L = f * grad(uS)
        la = np.array([f[s.mesh.findCell([x]).id()] * \
                        du(s.mesh.findCell([x]).center()[0]) for x in xt])
        self.assertEqual(L.eval(pxt), la, atol=1e-12)

        L = f * grad(uS) + DZ
        la = np.array([-1.0 + f[s.mesh.findCell([x]).id()] * \
                        du(s.mesh.findCell([x]).center()[0]) for x in xt])
        self.assertEqual(L.eval(pxt), la, atol=1e-12)

        L = f * grad(uS) + f * DZ
        la = np.array([f[s.mesh.findCell([x]).id()] * \
                       (-1. + du(s.mesh.findCell([x]).center()[0])) for x in xt])
        self.assertEqual(L.eval(pxt), la, atol=1e-12)

        L = f * (grad(uS) + DZ)
        la = np.array([f[s.mesh.findCell([x]).id()] * \
                       (-1. + du(s.mesh.findCell([x]).center()[0])) for x in xt])
        self.assertEqual(L.eval(pxt), la, atol=1e-12)

        #### P1 #######
        f = uS ## FEASolution
        # quadratic u cannot fit to p1 (projection vs. interpolation)
        # f evaluated at specific point (interpolation)
        ###########
        L = f * grad(uS)
        l1 = L.eval(pxt)
        la = np.array([fu(x)*du(s.mesh.findCell([x]).center()[0]) for x in xt])
        self.assertEqual(np.linalg.norm(l1-la), 0.01133871619235311)

        L = f * grad(uS) + DZ
        l1 = L.eval(pxt)
        la = np.array([-1.+ fu(x)*du(s.mesh.findCell([x]).center()[0]) for x in xt])
        self.assertEqual(np.linalg.norm(l1-la), 0.01133871619235311, atol=1e-12)

        L = f * grad(uS) + f * DZ
        l1 = L.eval(pxt)[:,0]
        la1 = np.array([-fu(x) + fu(x)*du(s.mesh.findCell([x]).center()[0]) for x in xt])

        self.assertEqual(np.linalg.norm(l1-la1), 0.005648004505814392, atol=1e-12)

        L = f * (grad(uS) + DZ)
        l1 = L.eval(pxt)
        la1 = np.array([-fu(x) + fu(x)*du(s.mesh.findCell([x]).center()[0]) for x in xt])
        self.assertEqual(np.linalg.norm(l1-la1), 0.005648004505814392, atol=1e-12)

        #### P1 #######
        f = uS ## FEASolution
        # quadratic u cannot fit to p1 (projection vs. interpolation)
        # f evaluated at specific cell (center, nearest neighbour, harmonic mean, mean)
        # Need Decission!!  f.continuous = False, f.evaluate = 'method'
        # TODO!!
        ###########

        #### P2 #######
        ## P2 linear behave for every cell center -> exact for quadratic functions
        s = ScalarSpace(mesh, p=2)
        uS = FEASolution(space=s, values=fu(pg.x(s.mesh)))
        L = uS
        la2 = fu(xt)
        np.testing.assert_allclose(L.eval(pxt), la2)

        L = grad(uS)
        la2 = du(xt)
        np.testing.assert_allclose(L.eval(pxt), la2)

        #### P2 #######
        f = uS ## FEASolution
        # quadratic u cannot fit to p1 (projection vs. interpolation)
        # f evaluated at specific point (interpolation)
        ###########
        L = f * grad(uS)
        l2 = L.eval(pxt)
        la2 = np.array(fu(xt)*(du(xt)))
        self.assertEqual(np.linalg.norm(l2-la2), 0.0, atol=1e-12)

        L = f * grad(uS) + DZ
        l2 = L.eval(pxt)
        la2 = np.array(-1. + fu(xt)*(du(xt)))
        self.assertEqual(np.linalg.norm(l2-la2), 0.0, atol=1e-12)

        L = f * grad(uS) + f * DZ
        l2 = L.eval(pxt)[:,0]
        la2 = np.array(fu(xt)*(-1. + du(xt)))
        self.assertEqual(np.linalg.norm(l2-la2), 0.0, atol=1e-12)

        if 0:
            pg.plt.plot(xt, la1, label='exact (p1)')
            pg.plt.plot(xt, la2, label='exact (p2)')
            pg.plt.plot(xt, l1, 'x', label='eval p1')
            pg.plt.plot(xt, l2, 'x', label='eval p2')
            pg.plt.legend()


    def test_FEA_Expression_EvalOrder(self):
        """Test for basic forms with different evaluation orders"""
        ms = createTestMeshs()
        mesh = ms[3]; p=1

        s = ScalarSpace(mesh, p=p)
        v = VectorSpace(mesh, p=p)

        @FEAFunction
        def f1C(p):
            return 1.0

        @FEAFunction
        def f1(p):
            return pg.x(p)

        @FEAFunction3
        def f3C(p):
            return [1.0, 0, 0]

        @FEAFunction3
        def f3(p):
            return [pg.x(p), 0, 0]

        u1 = FEASolution(space=s, values=f1(s.mesh.positions()))

        eO = 2
        aN = f1(s.mesh.positions())
        aC = f1(s.mesh.cellCenters())
        f1C.evalOrder = eO
        f1.evalOrder = eO
        u1.evalOrder = eO
        #### START DEBUG WORKSPACE ############################################
        # mesh = ms[0]; p=2
        # s = ScalarSpace(mesh, p=2)

        # aN = f1(s.mesh.positions())
        # u1.evalOrder = 0
        # L = s*aN

        # pg._g(L.assemble(core=False))
        # pg._y(L.assemble(core=True))
        # pg.core.setDeepDebug(-1)
        # pg.core.setDeepDebug(0)
        # pg._r(L.assemble(useMats=True))

        # _testExp(L)
        #return
        #### END DEBUG WORKSPACE ############################################

        for mesh in ms[0:]:

            for p in [1, 2]:
                pg.info('mesh:', mesh, 'p:', p)
                v = VectorSpace(mesh, p=p)
                s = ScalarSpace(mesh, p=p)
                aN = f1(s.mesh.positions())
                aC = f1(s.mesh.cellCenters())
                u1 = FEASolution(space=s, values=f1(s.mesh.positions()))

                for evalOrder in [0, 1, 2]:
                    f1C.evalOrder = evalOrder
                    f3C.evalOrder = evalOrder
                    f1.evalOrder = evalOrder
                    f3.evalOrder = evalOrder
                    u1.evalOrder = evalOrder

                    Ls = [
                            s*f1C,
                            s*aN,
                            s*aC,
                            s*f1,
                            s*u1,
                            v*f1C,
                            v*aN,
                            v*aC,
                            v*f1,
                            v*u1,
                            grad(v)*f1C,
                            grad(v)*f1,
                            grad(v)*u1,
                            grad(v)*aN,
                            grad(v)*aC,
                         ]

                    try:
                        for i, L in enumerate(Ls):
                            print('.', end='', flush=True)
                            _testExp(L)

                    except BaseException as e:
                        pg._r('+'*80)
                        pg._g(v.mesh)
                        pg._y(f'L({i}): {L} p={p} evalOrder={evalOrder}')
                        pg._r('-'*80)

                        pg._g(L.assemble(core=False))
                        pg._y(L.assemble(core=True))
                        pg._r(L.assemble(useMats=True))

                        print(e)
                        import traceback
                        traceback.print_exc(file=sys.stdout)
                        exit()
                print()


    def test_FEA_Elastic_Expression_Eval(self):
        """Test evaluation of elastic expressions."""
        def eps(v):
            return sym(grad(v))

        def sigma(v):
            return lam*identity(v)*tr(eps(v)) + 2.0*mu*eps(v)

        def dev2(x):
            """For list of matrices"""
            #inner frobenius norm a:b = tr(a.T@b)

            if isinstance(x, FEAOP):
                return trace(dev(x).T @ dev(x))

            d = dev(x)
            return np.array([np.sum(np.dot(e.flatten(), e.flatten()))
                            for e in d])

        def positive(x):
            return 0.5 * (x + abs(x))

        x = [-1.0, 0.0, 1.0, 2.]
        mesh = pg.createGrid(x=x, y=x)
        # print(mesh)

        lam = 1
        mu = 0.5
        n0 = mesh.findNearestNode([0.0, 0.0]) # origin node
        nT = mesh.findNearestNode([0.0, 1.0]) # top center

        v = VectorSpace(mesh, order=3, p=1)

        bc={'Node': [[n0, [0.0, 0.0]],  # origin: no movement
                     [nT, [0.0, None]], # top-center: free-slip only y-movement
                    ],
            'Neumann':{'*':lambda _b: [0.0, 1.0]},
            #'Neumann':{'*':lambda _b: _b.norm() * 1.0},
            }


        #pg.core.setDeepDebug(-1)
        u = solve((grad(v) * sigma(v)) == 0, bc=bc, solver='scipy')
        #pg.core.setDeepDebug(0)

        ### single flatten [[xx, xy, yx, yy], [...]]
        epF = strain(u)

        self.assertEqual(epF[0].flatten(),
                         eps(u).eval(u.mesh.cell(0)).flatten(), atol=1e-14)
        self.assertEqual(np.array(epF).flatten(),
                    eps(u).eval(mesh.cellCenters(), keepDim=False).flatten(),
                    atol=1e-14)

        ### single flatten [[xx, xy, yx, yy], [...]]
        siF = stress(u, lam=lam, mu=mu)

        # print(siF[0])
        # pg.core.setDeepDebug(-1)
        # print(sigma(u).eval(0))
        # pg.core.setDeepDebug(0)
        # print(ep[0])
        # print(eps(u).eval(0))

        self.assertEqual(siF[0].flatten(),
                         sigma(u).eval(u.mesh.cell(0)).flatten(), atol=1e-14)
        self.assertEqual(siF.flatten(),
                         sigma(u).eval().flatten(), atol=1e-14)

        for func in [
                    lambda ep: trace(ep),
                    lambda ep: trace(ep) + abs(trace(ep)),
                    lambda ep: positive(trace(ep)),
                    #lambda ep: positive(trace(ep))**2,
                    #lambda ep: 0.5 * (lam+mu) * positive(trace(ep))**2,
                    lambda ep: ep,
                    #lambda ep: identity(ep),
                    #lambda ep: identity(v),
                    #lambda ep: ep - identity(ep),
                    #lambda ep: identity(v)*trace(ep),
                    #lambda ep: identity(ep)*trace(ep),
                    #lambda ep: lam*identity(ep)*trace(ep) + 2.0*mu*ep,
                    #lambda ep: dev(ep),
                    #lambda ep: dev(ep)*dev(ep),
                    #lambda ep: dev2(ep),
                ]:
            tF = func(epF)          ## ready made strain
            t  = func(eps(u))       ## function for strain

            try:
                self.assertEqual(tF[0].flatten(),
                                 t.eval(u.mesh.cell(0)).flatten(), atol=1e-14)
                self.assertEqual(tF.flatten(),
                                 t.eval(u.mesh.cellCenters()).flatten(),
                                 atol=1e-14)

            except BaseException as e:
                pg._r('#'*50)
                pg._r(f'func=func')

                pg._g(f'tF', tF)
                pg._y(f't', t.eval(u.mesh.cellCenters()))

                print(e)
                import traceback
                traceback.print_exc(file=sys.stdout)
                exit()


    def test_FEA_Elastic_Expression_Eval2(self):
        """Ensure correct interpolation of FEASolution for strain and
        stress values (p1, p2) for non-mapped spaces
        """
        #### START 1D test case
        uF, p = parse(u='(x^p + 0.1) * (y^p + 0.1)', p=2)
        guF = grad(uF)
        guFN = grad(uF, numeric=True)

        x = np.linspace(-2, 2, 11)
        m = pg.createGrid(x)
        s = ScalarSpace(m, p=2)
        uS = FEASolution(s, values=uF(s.mesh))

        guS = grad(uS)
        x = np.linspace(-2, 2, 51)
        np.testing.assert_allclose(uF(x), uS(x))## exact for p2
        np.testing.assert_allclose(guF(x)[:,0], guS(x)) ## exact for p2
        np.testing.assert_allclose(guF(x)[:,0], guS(x))## exact for p2
        np.testing.assert_allclose(guF(x)[:,0], guFN(x)[:,0])## exact for p2

        if 0: # show
            fig, axs = pg.plt.subplots(2, 2, figsize=(10,10))

            for i, p in enumerate([1, 2]):
                s = ScalarSpace(m, p=p)
                uS = FEASolution(s, values=uF(s.mesh))
                guS = grad(uS)

                x = np.linspace(-2, 2, 51)
                axs[i][0].plot(x, uF(x), label=f'uS p={p}')
                axs[i][0].plot(x, uS(x), label=f'uS p={p}')
                axs[i][0].set(xlabel='coordinate x in m', ylabel='u')
                axs[i][0].legend()

                axs[i][1].plot(x, guF(x)[:,0], label=f'grad(uF) p={p}')
                axs[i][1].plot(x, guS(x)[:,0], label=f'grad(uS) p={p}')
                axs[i][1].set(xlabel='coordinate x in m', ylabel='grad(u)')
                axs[i][1].legend()

                for xi in x:
                    pg._g(guS(xi))
                    c = guS.mesh.findCell([xi, 0])
                    pg._y(c.grad([xi, 0], uS.values))
                    pg._y(c)
                    break

        ### END 1D test case

        lam = 2.0
        mu = 0.3
        alpha = 0.5
        p0 = 0.1
        def eps(u):
            return sym(grad(u))

        def sigMu(v):
            return 2.0*mu*eps(v)

        def sigLam(v):
            return lam*tr(eps(v))*I(v)

        def sigP(v, p):
            return p*I(v)

        def sigP2(v, p):
            return alpha*(p-p0)*I(v)

        def sigma(v):
            return 2.0*mu*eps(v) + lam*tr(eps(v))*I(v)

        def sigmaP(v, p):
            return 2.0*mu*eps(v) + lam*tr(eps(v))*I(v) - sigP(v, p)

        def sigmaP2(v, p):
            return 2.0*mu*eps(v) + lam*tr(eps(v))*I(v) - sigP2(v, p)

        def sigma3(v, p):
            return 2.0*mu*eps(v) + (lam*tr(eps(v)) - alpha*(p-p0))*I(v)
            #return 2.0*mu*eps(v) + lam*tr(eps(v))*I(v) - alpha*(p-p0)*I(v)

        ### START 1D eval
        x = np.linspace(-2, 2, 5)
        m = pg.createGrid(x)

        s = ScalarSpace(m, p=1)
        v = VectorSpace(m, p=2)

        vF = asFunction('(1+x², 1+y², 1+z²)')
        sF = asFunction('x')
        vS = FEASolution(v, vF(v.mesh)[:,0])
        sS = FEASolution(s, sF)

        t1 = (2.0*mu*eps(vS))(0.3)
        t2 = (lam*tr(eps(vS))*I(vS))(0.3)
        t3 = (sS*I(vS))(0.3)

        assertEqual(t1, 2.0*mu*2*0.3, tol=1e-16)
        assertEqual(t2, lam*2*0.3, tol=1e-16)
        assertEqual(t3, 0.3, tol=1e-16)
        assertEqual(sigmaP(vS, sS)(0.3), t1+t2-t3)
        ### END 1D eval

        ### START 2D test evaluation: p * I
        x = np.linspace(-2, 2, 6)
        #print('x:', x)
        m = pg.createGrid(x, x, x)

        vF = asFunction('(1+x)², (1+y)², (1+z)²')
        v = VectorSpace(m, p=2)
        vS = FEASolution(v, vF(v.mesh))

        sF = asFunction('x')
        s = ScalarSpace(m, p=1)
        sS = FEASolution(s, sF)

        #### START DEBUG WORKSPACE ############################################

        # p = 0.3
        p = 2
        #p = [1, 1]
        #p = [1, 1, 1, 1] #ok
        #p = [[1.0, 1.0], [1.1, 1.1]]
        p = [[1.0, 1.0], [1.1, 1.1], [1.2, 1.2]]
        #p = [[1.0, 1.0], [1.1, 1.1], [1.2, 1.2], [1.3, 1.3]] #ok
        #p = [[1.0, 1.0], [1.1, 1.1], [1.2, 1.2], [1.3, 1.3], [1.4, 1.4]] #ok

        #p = [[0.1, 0.0, 0.0]]*3

        t = 1.
        #t = [1.]
        # t = [1, 2]
        # # t = [1., 2., 3., 4.]
        # t = np.linspace(0, 10, 5)
        #t = [1., 2., 3.]
        dim = 3
        #print('*'*40, 'pnts:', asPosListNP(p))
        #print('*'*40, 't:', t)

        #print('*** grad')

        #pg._g('+'*60)
        #pg.core.setDeepDebug(-1)
        #pg.core.setDeepDebug(0)
        #pg._g('-'*60)

        # print((2.0*mu*eps(uh))(0))
        # print((lam*tr(eps(uh))*I(uh))(0))


        # lam = np.asarray([2.0] * v.mesh.cellCount())
        # mu = np.asarray([0.3] * v.mesh.cellCount())
        # alpha = np.asarray([0.5] * v.mesh.cellCount())
        alpha = np.asarray([0.5] * v.mesh.cellCount())

        alpha = ParameterDict({0:0.5})
        lam = ParameterDict({0:2.0})
        mu = ParameterDict({0:0.3})


        L1 = 0.5*sS
        L2 = alpha*sS
        self.assertEqual(L1(p, t=t, dim=dim),
                         L2(p, t=t, dim=dim))

        self.assertEqual(L1(p, t=t, dim=dim),
                         L2(p, t=t, dim=dim))
        self.assertEqual(L1(p, t=t, dim=2),
                         np.asarray([L2(p_, t=t, dim=2)
                            for p_ in asPosListNP(p)]))

        self.assertEqual(sigma(vS)(p, t=t, dim=dim),
                                            sigMu(vS)(p, t=t, dim=dim) \
                                            + sigLam(vS)(p, t=t, dim=dim))

        self.assertEqual(sigmaP(vS, sS)(p, t=t, dim=dim),
                                        sigMu(vS)(p, t=t, dim=dim) \
                                        + sigLam(vS)(p, t=t, dim=dim) \
                                        - sigP(vS, sS)(p, t=t, dim=dim))

        self.assertEqual(sigmaP2(vS, sS)(p, t=t, dim=dim),
                                        sigMu(vS)(p, t=t, dim=dim) \
                                        + sigLam(vS)(p, t=t, dim=dim) \
                                        - sigP2(vS, sS)(p, t=t, dim=dim))

        self.assertEqual(sigma3(vS, sS)(p, t=t, dim=dim),
                                            sigMu(vS)(p, t=t, dim=dim) \
                                            + sigLam(vS)(p, t=t, dim=dim) \
                                            - sigP2(vS, sS)(p, t=t, dim=dim))
        ## fixme if sS is Scalar
        # self.assertEqual(sigma3(vS, 1)(p, t=t, dim=dim),
        #                                     sigMu(vS)(p, t=t, dim=dim) \
        #                                     + sigLam(vS)(p, t=t, dim=dim) \
        #                                     - sigP2(vS, 1)(p, t=t, dim=dim))

        #### START DEBUG WORKSPACE ############################################
        m = pg.createGrid(x, x, x)
        for t in [ 1.,
                  [1.],
                  [1, 2],
                  [1., 2., 3., 4.],
                  [np.linspace(0, 10, 5)],
                 ]:

            for p in [[1, 1],
                    [1, 1, 1, 1],
                    [[1.1,1.1], [1.2,1.2]],
                    [[1.1,1.1], [1.2,1.2], [1.3,1.3]],
                    [[1.1,1.1], [1.2,1.2], [1.3,1.3], [1.4,1.4]],
                    [[0.1, 0.0, 0.0]]*3,
                    ]:

                for dim in 2, 3:
                    try:
                        for lam, mu, alpha in [[2.0, 0.3, 0.5],
                                    [np.asarray([2.0] * v.mesh.cellCount()),
                                     np.asarray([0.3] * v.mesh.cellCount()),
                                     np.asarray([0.5] * v.mesh.cellCount())],
                                     [ParameterDict({0:2.0}),
                                      ParameterDict({0:0.3}),
                                      ParameterDict({0:0.5})]
                                            ]:

                            L1 = 0.5*sS
                            L2 = alpha*sS
                            self.assertEqual(L1(p, t=t, dim=dim),
                                            L2(p, t=t, dim=dim))
                            self.assertEqual(L1(p, t=t, dim=2),
                                            np.asarray([L2(p_, t=t, dim=2)
                                                     for p_ in asPosListNP(p)]))

                            self.assertEqual(sigma(vS)(p, t=t, dim=dim),
                                            sigMu(vS)(p, t=t, dim=dim) \
                                            + sigLam(vS)(p, t=t, dim=dim))

                            self.assertEqual(sigmaP(vS, sS)(p, t=t, dim=dim),
                                        sigMu(vS)(p, t=t, dim=dim) \
                                        + sigLam(vS)(p, t=t, dim=dim) \
                                        - sigP(vS, sS)(p, t=t, dim=dim))

                            self.assertEqual(sigmaP2(vS, sS)(p, t=t, dim=dim),
                                        sigMu(vS)(p, t=t, dim=dim) \
                                        + sigLam(vS)(p, t=t, dim=dim) \
                                        - sigP2(vS, sS)(p, t=t, dim=dim))

                            self.assertEqual(sigma3(vS, sS)(p, t=t, dim=dim),
                                            sigMu(vS)(p, t=t, dim=dim) \
                                            + sigLam(vS)(p, t=t, dim=dim) \
                                            - sigP2(vS, sS)(p, t=t, dim=dim))

                        print('.', end='', flush=True)

                    except BaseException as e:
                        pg._r('+'*60)
                        pg._g(f'p: {p} t: {t} dim: {dim}')
                        pg._y(f'sigma(vS)(p, t=t, dim=dim): '
                              f'{sigma(vS)(p, t=t, dim=dim)}')
                        pg._y(f'sigMu(vS)(p, t=t, dim=dim): '
                              f'{sigMu(vS)(p, t=t, dim=dim)}')
                        pg._y(f'sigLam(vS)(p, t=t, dim=dim): '
                              f'{sigLam(vS)(p, t=t, dim=dim)}')
                        pg._y(f'sigP(vS, sS)(p, t=t, dim=dim): '
                              f'{sigP(vS, sS)(p, t=t, dim=dim)}')
                        print(e)
                        import traceback
                        traceback.print_exc(file=sys.stdout)
                        exit()
        print()

        ### START test p * I
        lam = 2.0
        mu = 0.3
        alpha = 0.5
        vF = asFunction('(1+x)², (1+y)², (1+z)²')
        sF = parse(p='x')

        v = VectorSpace(m, p=2)
        vS = FEASolution(v, values=vF)

        s = ScalarSpace(m, p=1)
        sS = FEASolution(s, values=sF)

        for f in [
                    lambda p: p*I(2),
                    lambda p: p*I(3),
                    lambda p: I(2)*p,
                    lambda p: I(3)*p,
                    lambda p: p*I(sS),
                    lambda p: I(sS)*p,
                    lambda p: p*I(vF),
                    lambda p: I(vF)*p,
                    lambda p: p*I,
                    lambda p: I*p,

            ]:
            # pg._g(f(p)(2))
            # pg._r(f(pS)(2))
            assertEqual(f(sF)(2), f(sS)(2))
        ### END test p * I

        ### START test evaluation: sigma(u) - p*I, for function and solutions
        # no cell values for function eval
        for f in [
                    lambda u, p: sigma(u) - p*I(3),
                    lambda u, p: sigma(u) - p*I(u),
                    lambda u, p: sigma(u) - 3.3*p*I(u),
            ]:
            assertEqual(f(vF, sF)(2), f(vS, sS)(2))
            assertEqual(f(vS, sF)(2), f(vF, sS)(2))

        ### END test sigma(u) - p*I

        ### some random tests
        m = pg.createGrid(x, x)
        lam = 2
        mu = 0.5
        pnt = 2
        uF2 = parse(u='(x² + x*y + y², x² - x*y - y²)')
        uF3 = parse(u='(x² + x*y + y², x² - x*y - y², 0)')
        v = VectorSpace(m, p=2)
        s = ScalarSpace(m, p=1)
        uS2 = FEASolution(v, values=uF2)

        self.assertEqual(eps(uF3)(pnt), eps(uS2)(pnt, dim=3), atol=1e-14)

        sig3 = lambda v: lam*tr(eps(v))*I(3) + 2.0*mu*eps(v)
        sigV = lambda v: lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        # test 2D mesh with plain strain but 3D sigma
        self.assertEqual(sig3(uF3)(pnt), [[8.0, 3.0, 0.0],
                                          [3.0, 2.0, 0.0],
                                          [0.0, 0.0, 4.0]])
        self.assertEqual(sig3(uS2)(pnt, dim=3), [[8.0, 3.0, 0.0],
                                                [3.0, 2.0, 0.0],
                                                [0.0, 0.0, 4.0]])

        self.assertEqual(sigV(uF3)(pnt), [[8.0, 3.0, 0.0],
                                          [3.0, 2.0, 0.0],
                                          [0.0, 0.0, 4.0]])
        self.assertEqual(sigV(uS2)(pnt, dim=3), [[8.0, 3.0, 0.0],
                                                [3.0, 2.0, 0.0],
                                                [0.0, 0.0, 4.0]])
        self.assertEqual(sigV(uS2)(pnt), [[8., 3],
                                         [3, 2]])

        self.assertEqual(sig3(uF3)(pnt), sig3(uS2)(pnt, dim=3), atol=1e-14)
        self.assertEqual(sigV(uF2)(pnt), sigV(uS2)(pnt), atol=1e-14)

        for uF in [
                    #toFunctions(u='(x² + x*y + y², x² - x*y - y², 0)'),
                    parse(u='(x² + x*y + y², x² - x*y - y²)'),
                    parse(u='(x² + x*y + y², x² + x*y - y²)'),
                    ]:
            for pnts in [  1,           # p
                          [1,1],        # p
                          [1,1,1],      # p
                          [1,1,1,1],    # [p]*4
                          [[1.1,1.1], [1.2,1.2]],                        # [p]*2
                          [[1.1,1.1], [1.2,1.2], [1.3,1.3]],             # [p]*3
                          [[1.1,1.1], [1.2,1.2], [1.3,1.3], [1.4,1.4]],  # [p]*4
                          [[1.1,1.1,1.1], [1.2,1.2,1.2]],                # [p]*2
                          [[1.1,1.1,1.1], [1.2,1.2,1.2], [1.3,1.3,1.3]], # [p]*3
                          [[1,1,1]]*4,  # [p]*4
                    ]:

                v = VectorSpace(m, p=2)
                uS = FEASolution(v, values=uF)

                try:
                    print('.', end='', flush=True)
                    self.assertEqual(uS(pnts),
                                     uF(pnts), atol=3e-14)
                    self.assertEqual(grad(uS)(pnts),
                                     grad(uF)(pnts), atol=3e-14)
                    self.assertEqual(sym(grad(uS))(pnts),
                                     sym(grad(uF))(pnts), atol=3e-14)
                    self.assertEqual(eps(uS)(pnts),
                                     eps(uF)(pnts), atol=3e-14)
                    self.assertEqual((2*mu*eps(uS))(pnts),
                                     (2*mu*eps(uF))(pnts), atol=3e-14)
                    self.assertEqual((lam*tr(eps(uS)))(pnts),
                                     (lam*tr(eps(uF)))(pnts), atol=5e-14)
                    self.assertEqual((lam*tr(eps(uS))*I(2))(pnts),
                                     (lam*tr(eps(uF))*I(2))(pnts), atol=5e-14)
                    self.assertEqual(sigma(uS)(pnts),
                                     sigma(uF)(pnts), atol=7e-14)

                except BaseException as e:
                    pg._r('#'*50)
                    pg._r(f'f={uF.expr}')
                    pg._r(f'pnts={pnts}')

                    print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()
            print()


    def test_FEA_Elastic_Expression_Eval3(self):
        """Test evaluation of elastic expressions with mapped spaces."""
        def eps(v):
            return sym(grad(v))

        def sigma(v):
            return lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        def sigmaT(v, T, scale):
            return sigma(v) - scale*T*I(v)

        def sigma3(v, T, scale):
            return 2.0*mu*eps(v) + (lam*tr(eps(v)) - scale*T)*I(v)
            #return 2.0*mu*eps(v) + lam*tr(eps(v))*I(v) - scale*T*I(v)

        def sigmaM(v):
            return C*eps(v)

        def sigmaMT(v, T, scale):
            return C*(eps(v) - scale*T*I(v))

        #### START DEBUG WORKSPACE ############################################
        x = np.linspace(-2, 2, 3)
        m = pg.createGrid(x, x, x )
        print(m)
        vF = asFunction('(1+x)², (1+y)², (1+z)²')
        v = VectorSpace(m, p=2)
        vS = FEASolution(v, vF(v.mesh))

        vM = VectorSpace(m, p=2, elastic=True)
        vSM = FEASolution(vM, vF(vM.mesh))

        lam = 2.2
        mu = 0.3

        pt = 0.3
        #pt = 2
        pt = [1, 1]
        #pt = [1, 1, 1, 1] #ok
        #pt = [[1.0, 1.0]]
        pt = [[.5, .5]]
        #pt = [[1.0, 1.0], [1.1, 1.1]]
        #pt = [[1.0, 1.0], [1.1, 1.1], [1.2, 1.2]]
        #pt = [[1.0, 1.0], [1.1, 1.1], [1.2, 1.2], [1.3, 1.3]] #ok
        #pt = [[1.0, 1.0], [1.1, 1.1], [1.2, 1.2], [1.3, 1.3], [1.4, 1.4]] #ok
        #pt = [[0.1, 0.0, 0.0]]*3

        alpha = 0.5
        T = 1
        dim = 3
        C0 = createElasticityMatrix(lam=lam, mu=mu, dim=dim,
                                    voigtNotation=True)
        Cc = [C0]*m.cellCount()
        Ca = np.asarray(Cc)

        C = ParameterDict({0:C0})
        #C = C0
        #C = Cc
        C = Ca

        #L2 = sigmaMT(vSM, 1, alpha)
        L1 = sigma(vS)
        pg._g(asVoigtMapping(L1(pt, dim=dim)))

        L2 = sigmaM(vSM)

        #print('C:', C)
        pg._b('#################')
        C = Cc
        pg._y(sigmaM(vSM)(pt, dim=dim))
        C = Ca
        pg._r(sigmaM(vSM)(pt, dim=dim))

        #halt
        pg._y(L2(pt, dim=dim))

        self.assertEqual(L1(pt, dim=dim),
                         asNoMapping(L2(pt, dim=dim)))

        self.assertEqual(asVoigtMapping(L1(pt, dim=dim)),
                         L2(pt, dim=dim), atol=5e-12)

        #return
        #### START DEBUG WORKSPACE ############################################

        for i, m in enumerate(createTestMeshs()[2:]):
            vF = asFunction('(1+x)², (1+y)², (1+z)²')
            v = VectorSpace(m, p=2)
            vS = FEASolution(v, vF(v.mesh))

            vM = VectorSpace(m, p=2, elastic=True)
            vSM = FEASolution(vM, vF(vM.mesh))

            lam = 2.2
            mu = 0.3

            dim = 3
            C0 = createElasticityMatrix(lam=lam, mu=mu, dim=dim,
                                        voigtNotation=True)
            Cc = [C0]*m.cellCount()
            Ca = np.asarray(Cc)
            Cd = ParameterDict({0:C0})

            for pt in [
                        [[.5, .5]],
                        [[.5, .5], [0.6, 0.6]],
                        [[.5, .5], [0.6, 0.6], [0.7, 0.7]],
                        [[.5, .5], [0.6, 0.6], [0.7, 0.7], [0.8, 0.8]],
                        ]:

                try:
                    for C in [C0, Cc, Cd, Ca]:
                        L1 = sigma(vS)
                        L2 = sigmaM(vSM)

                        self.assertEqual(L1(pt, dim=dim),
                                         asNoMapping(L2(pt, dim=dim)),
                                         atol=5e-12)
                        self.assertEqual(asVoigtMapping(L1(pt, dim=dim)),
                                         L2(pt, dim=dim),
                                         atol=5e-12)
                    print('.', end='', flush=True)
                except BaseException as e:
                    pg._r('#'*50)
                    pg._y(f'mesh ({i}) {m}')
                    pg._y(f'pt={pt}')
                    pg._y(f'C={C}')
                    pg._g(f'sigma(vS)(pt, dim=dim): {sigma(vS)(pt, dim=dim)}')
                    pg._y(f'sigma1(vSM)(pt, dim=dim): {sigma1(vSM)(pt, dim=dim)}')

                    print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()



    def test_FEA_perQuadrature(self):
        """Tests for interpolation with different eval orders.

        Little redundant but kept because they don't hurt.
        """
        ## Start -- Interpolate Gradients per Quadrature
        # test for pg.core.interpolateGradients( grad grad )

        mesh = pg.createGrid(3, 2)
        s = ScalarSpace(mesh); eMat = s.uMat()
        qPnts = eMat.quadraturePoints()

        u = asFunction('x²*y + y²*x')
        du = grad(u)
        ddu = grad(du)
        v = VectorSpace(mesh, p=2)
        duh = FEASolution(v, values=du(v.mesh)) # exact p2, grad(du) -> exact p1
        dduh = grad(duh)

        assertEqual(duh(qPnts), du(qPnts))
        assertEqual(dduh(qPnts), ddu(qPnts))

        assertEqual((dduh-ddu)(qPnts), (ddu-dduh)(qPnts))

        #return
        ## End -- Interpolate Gradients per Quadrature

        x = np.linspace(0.0, 1.0, 3)
        mesh = pg.createGrid(x=x, y=x)
        f1 = lambda p: p[0]

        u = ScalarSpace(mesh)
        uF1 = FEAFunction(f1)
        uS1 = FEASolution(u, values=uF1(mesh.positions()))

        ### basic tests
        ### test with OP-function of FEASolution
        m = 2
        #uk = FEASolution(u, values=pg.x(u.mesh))
        uk = FEASolution(u)
        def p(x, ent):
            return (1 + uk(x))**m
        L = grad(u)*p*grad(u)
        A = _testExp(L)

        def p1(x, ent):
            return (1 + pg.x(x))**m

        def p2(u):
            return (1 + u)**m

        uk = FEASolution(u, values=pg.x(u.mesh))

        self.assertEqual(p1((0.1, 0.0, 0.0), None),
                         p2(uk)((0.1, 0.0, 0.0), None))

        L1 = grad(u)*p1*grad(u)
        L2 = grad(u)*p2(uk)*grad(u)

        A1 = L1.apply(0)
        A2 = L2.apply(0)
        self.assertEqual(A1, A2)

        A1 = _testExp(L1)
        A2 = _testExp(L2)
        self.assertEqual(A1, A2)


        ### Test integration of f on quadrature points
        F1Q = _testExp(uF1*u)
        F = _testExp(uS1*u)
        self.assertEqual(F1Q, F)

        ## Manual reference solution for cell center
        f1C = [uF1.eval(c.center()) for c in mesh.cells()]
        F1C = _testExp(f1C*u)

        uF1.evalOnCells = True
        uS1.evalOnCells = True

        F = _testExp(u*uF1)
        self.assertEqual(F, F1C)

        F = _testExp(u*uF1(mesh.cellCenters())) # same like above
        self.assertEqual(F, F1C)

        F = _testExp(u*uS1(mesh.cellCenters()))
        self.assertEqual(F, F1C)

        F = _testExp(u*uS1) # same like above
        self.assertEqual(F, F1C)

        ### Test same like above but with adv. OP
        uF1.evalOnQuads = True
        uS1.evalOnQuads = True

        f2 = lambda p: p[0] + 1.0
        uF2 = FEAFunction(f2) # 1 + x

        F2Q = _testExp(f2*u)
        F = _testExp((uS1 + 1)*u)
        self.assertEqual(F2Q, F)

        LC = _testExp((uF1 + 1.0)*u)
        self.assertEqual(F2Q, LC)

        LC = _testExp((1.0 + uF1)*u)
        self.assertEqual(F2Q, LC)

        LC = _testExp((uS1 + 1.0)*u)
        self.assertEqual(F2Q, LC)

        LC = _testExp((1.0 + uS1)*u)
        self.assertEqual(F2Q, LC)

        ### Test integration of f2 on cell centers
        F2C = _testExp(uF2(mesh.cellCenters())*u) # F2 for center vals

        uF1.evalOnCells = True
        uS1.evalOnCells = True

        LC = _testExp((uF1 + 1.0)*u)
        self.assertEqual(F2C, LC)

        LC = _testExp((1.0 + uF1)*u)
        self.assertEqual(F2C, LC)

        LC = _testExp((uS1 + 1.0)*u)
        self.assertEqual(F2C, LC)

        LC = _testExp((1.0 + uS1)*u)
        self.assertEqual(F2C, LC)


    def test_FEAFunction_call(self):
        """Test function evaluation used for expression assembling.
        """
        N = 4
        x = np.linspace(0.0, 1.0, N)
        m = pg.createGrid(x=x)

        m.setCellMarkers(np.full(m.cellCount(), 2.0))

        s = ScalarSpace(m)
        LRef = 2.*s

        def f0(x):
            return 2.0
        #_testExp(f0*s, LRef)

        def f1(pos, entity):
            return entity.marker()

        # L = s*f1
        # pg._b('_'*80)
        # R = L.assemble(core=False)
        # pg._g(R)
        # # R = L.assemble(core=True)
        # # pg._y(R)
        # # R = L.assemble(useMats=True)
        # # pg._r(R)

        # _assemble(L)
        _testExp(f1*s)
        # this fails .. with val init on utils.calc -> check and fix
        _testExp(f1*s, LRef)

        #halt

        def f2(pos, **kwargs):
            #pg._r(kwargs)
            return kwargs['extra']
        _testExp(f2*s, LRef, extra=2)

        # Is wanted?? ??should work??
        # def f3(x, **kwargs):
        #     return x*0+2.
        # _testExp(f3*u, LRef, extra=2)

        def u(x):
            return x

        uh = FEASolution(s, values=1+pg.x(m))

        self.assertEqual((uh-u(pg.x(uh.mesh))).values, [1]*N)
        self.assertEqual((u(pg.x(uh.mesh))-uh).values, [-1]*N)
        self.assertEqual((u-uh).values, [-1]*N)
        self.assertEqual((uh-u).values, [1]*N)

        def c0(p):
            return 0.1 + p[0]**2
        def c1(p):
            return 0.1 + pg.x(p)**2

        c0 = FEAFunction(c0)
        c1 = FEAFunction(c1)

        def ca(p, **kw):
            return c0(p)
        def cb(p, **kw):
            return c1(p)

        x = np.linspace(0, 1, 5)
        mesh = pg.createGrid(x)
        s = ScalarSpace(mesh, p=1, order=3)

        _testExp((c0*s))
        _testExp((c1*s))
        _testExp((ca*s))
        _testExp((cb*s))


class TestFEAMisc(TestCollection):
    """Test for some finite element miscelleneous function.
    """
    def test_ErrorNorm(self):
        """ Test implementation of norms
        """
        def _normL2(space, ua, ub):
            """Manual norm for debugging.

            Note. Order=2 with grad(uh) is ambiguous for q points on edges
            due to H1 non-smoothness
            """
            mesh = space.mesh

            l2N = np.zeros(mesh.nodeCount())

            l2 = 0
            for cell in mesh.cells():
                U = uE(cell, order=space.order + 1)
                r = np.zeros_like(U._mat[0])
                q = U.x()                           # quadrature points
                w = U.w()                           # quadrature weights

                for i, x in enumerate(q):
                    xq = cell.shape().xyz(x)

                    uaq = ua(xq)
                    ubq = ub(xq)

                    duq = uaq - ubq
                    #print(xq, uaq, ubq, duq, duq*duq, np.sum(duq*duq))

                    ### dot for R3 and Frobenious inner product for RM
                    U._mat[i] *= np.sum(duq*duq)
                    r += (U._mat[i] * w[i] * cell.size())

                    ## only for Lagrange elements
                    ## for triangles |J|/2, Tet: |J|/6 etc.
                    #drds = cell.shape().jacobianDeterminant()
                    drds = cell.size()

                    l2 += np.sum(duq*duq)*w[i] * drds

                l2N[U.rowIDs()] += sum(r)

            #pg._g(l2N)
            #return np.sqrt(sum(l2N))
            return np.sqrt(l2)


        #### START DEBUG WORKSPACE ############################################
        # x = np.linspace(0, 2, 3)
        # mesh = pg.createGrid(x, x)
        mesh = createTestMeshs()[2]
        print(mesh)
        p = 1
        #Note. Order=2 with grad(uh) is ambiguous for q points on edges
        #    due to H1 non-smoothness
        u = asFunction('sin(x)*cos(y)*t')
        du = grad(u)
        s = ScalarSpace(mesh, p=p, order=p+2)
        uh = FEASolution(s, values=u)
        duh = grad(uh)

        uh = FEASolution(s, values=u)

        uh = s.split(np.zeros(mesh.nodeCount()), time=1)
        uh = s.split(u(mesh, time=2), time=2)
        uh = s.split(np.zeros(mesh.nodeCount()), time=3)

        pg._g(normL2(uh-u, time=1))
        pg._g(normL2(uh-u, time=2))
        pg._y(normL2(u-uh))



        #u = grad(asFunction('sin(x)+cos(x) + sin(y)+cos(y)'))
        # u = asFunction('sin(x)*cos(y)')
        # uh = grad(FEASolution(s, values=u))
        # u = grad(u)
        #uh = FEASolution(v, values=u)

        # a = grad(du)            # VectorGrad
        # b = grad(duh_v)         # VectorGrad

        # ut = a-b
        # L = s*(ut*ut)
        # L = s*(ut**2)

        # pg._g(L.assemble(core=False))
        # pg._y(L.assemble(core=True))

        # pg.core.setDeepDebug(-1)
        # pg._r(L.assemble(useMats=True))
        # pg.core.setDeepDebug(0)
        # ref = _testExp(L, atol=4e-12)
        return

        # L3 = s*(ut*ut)

        # print(u)
        # print(uh)

        # print('L2       :', normL2(ut))
        # print('L2(order):', normL2(ut, order=2))
        # print('Man(1)   :', np.sqrt(sum(L3.assemble(useMats=True, order=1))))
        # print('Man(2)   :', np.sqrt(sum(L3.assemble(useMats=True, order=2))))
        # print('_L2      :', _normL2(s, u, uh))

        #return
        # self.assertEqual(normL2(ut),
        #                  np.sqrt(sum(L3.assemble(useMats=True, order=3))),
        #                  atol=3e-17)

        # self.assertEqual(normL2(ut), _normL2(s, u, uh), atol=3e-17)

        #return
        #### END DEBUG WORKSPACE ##############################################

        ### START Short test for vectorspaces
        x = np.linspace(0, 2, 3)
        mesh = pg.createGrid(x, x)

        v = VectorSpace(mesh, p=1)
        s = ScalarSpace(mesh, p=1)
        u = grad(asFunction('sin(x)+cos(x) + sin(y)+cos(y)'))
        uh = FEASolution(v, values=u)

        ut = u-uh
        L1 = v*(ut*ut)
        L2 = v*(ut**2)
        L3 = s*(ut*ut)
        L4 = s*(ut**2)

        _testExp(L1)
        _testExp(L2)
        _testExp(L2, ref=L1)
        _testExp(L3)
        _testExp(L4)
        _testExp(L3, ref=L4)

        ## sum(s*v²) need to be sum(v*v²)
        self.assertEqual(sum(L1.assemble(core=False)),
                         sum(L3.assemble(core=False)), atol=7e-18)
        self.assertEqual(sum(L1.assemble(core=True)),
                         sum(L3.assemble(core=True)), atol=7e-18)
        self.assertEqual(sum(L1.assemble(useMats=True)),
                         sum(L3.assemble(useMats=True)), atol=7e-18)

        ## VecSpace(<ut, ut>) should be the same like ScalarSpace(<ut, ut>)

        self.assertEqual(normL2(ut),
                         np.sqrt(sum(L3.assemble(useMats=True, order=s.order+1))),
                         atol=5e-17)
        self.assertEqual(normL2(ut), _normL2(s, u, uh), atol=1e-16)

        ### END Short test for vectorspaces

        ### START Newest version, test all variants vs. _normL2
        for i, mesh in enumerate(createTestMeshs()):
            if mesh.dim() == 2:
                u = asFunction('sin(x)*cos(y)')
            else:
                continue

            du = grad(u)

            for p in [1, 2]:
                s = ScalarSpace(mesh, p=p, order=p+2)
                uh = FEASolution(s, values=u)
                duh = grad(uh)

                v = VectorSpace(mesh, p=p, order=p+2)
                duh_v = FEASolution(v, values=du)

                for j, (a, b) in enumerate([
                             [u, uh],                   # ScalarSpace
                             [du, duh],                 # grad(ScalarSpace)
                             [du, duh_v],               # VectorSpace
                             [grad(du), grad(duh_v)],   # grad(VectorSpace)
                        ]):

                    ut = a-b
                    L1 = s*(ut*ut)
                    L2 = s*(ut**2)

                    try:
                        _testExp(L1, L2)
                        assertEqual(normL2(a-b), _normL2(s, a, b), atol=2e-16)

                    except BaseException:
                            pg._r(f'+ TEST FAIL {j}' + '+'*68)
                            pg._g(f'mesh({i}): {mesh}')
                            pg._g(f'p:  {p}')
                            pg._g(f'a:  {a}')
                            pg._g(f'b:  {b}')
                            pg._r('-'*80)
                            exit()

        ### END Newest version, test all variants vs. _normL2


        for i, mesh in enumerate(createTestMeshs()):

            ###!! tests cannot work for mixed dimensions between u and mesh
            if mesh.dim() == 1:
                u = asFunction('sin(x)+cos(x)')
                u1 = asFunction('1 + x')
                u2 = u1 + asFunction('2.2*x²')
            elif mesh.dim() == 2:
                u = asFunction('sin(x)+cos(x) + sin(y)+cos(y)')
                u1 = asFunction('1 + 2.2*x + 3.3*y')
                u2 = u1 + asFunction('2.2*x² + 3.3*y²')
            elif mesh.dim() == 3:
                u = asFunction('sin(x)+cos(x) + sin(y)+cos(y) + sin(z)+cos(z)')
                u1 = asFunction('1 + 2.2*x + 3.3*y + 4.4*z')
                u2 = u1 + asFunction('2.2*x² + 3.3*y² + 4.4*z²')

                #TODO: see why this test fails .. supposed to?
                #u2 = u1 + asFunction('2.2*x² + 3.3*y² + 4.4*z² + x*y')
            pg.info(mesh)

            us = [u1, u2]
            for p in [1, 2]:
                ## order=2(p=1) for grad(uh) leads to ambiguity due to q n edges
                s = ScalarSpace(mesh, p=p, order=p+2)
                uh = FEASolution(s, values=u)

                s0 = ScalarSpace(mesh, p=p, order=p+2)
                u0 = FEASolution(s0, values=us[p-1])

                try:
                    for ut in [ u-uh,
                                uh-u,
                                uh-uh,
                                ]:

                        ## L2-norm
                        ## test for equal u*u and u**2
                        ref = _testExp(s*(ut*ut))
                        _testExp(s*ut**2, ref=ref)

                        ## test for assemble vs- integrate
                        self.assertEqual(normL2(ut),
                             np.sqrt((ut**2).integrate(s.mesh,
                                                       order=s.order+1)),
                             atol=4e-12)

                        ## H1-seminorm
                        ## test for equal grad(u)*grad(u) and grad(u)**2
                        ref = _testExp(s*(grad(ut)*grad(ut)), atol=4e-12)
                        _testExp(s*(grad(ut)**2), ref=ref, atol=4e-12)

                        ## test for assemble vs- integrate
                        self.assertEqual(normSemiH1(ut, order=p+3),
                        np.sqrt((grad(ut)**2).integrate(s.mesh,
                                                        order=s.order+1)),
                            atol=3e-11)

                        # _testExp(L)
                        self.assertEqual(normL2(us[p-1]-u0), 0.0, atol=1e-5)
                        self.assertEqual(normSemiH1(us[p-1]-u0), 0.0, atol=1e-5)
                        print('.', end='', flush=True)

                except BaseException:
                    pg._r('+ TEST FAIL ' + '+'*68)
                    pg._g(f'mesh({i}): mesh')
                    pg._g(f'p:  {p}')
                    pg._g(f'ut: {ut}')
                    pg._g(f'u0: {us[p-1]}')
                    pg._r('-'*80)
                    exit()
            print()


if __name__ == '__main__':
    import unittest
    pg.tic()
    unittest.main(exit=True)
    print()

    pg.info(f'Absolut tests: {testCount()}, took {pg.dur()} s')
