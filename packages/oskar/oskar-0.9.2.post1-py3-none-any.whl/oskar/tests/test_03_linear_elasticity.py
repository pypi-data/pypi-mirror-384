#!/usr/bin/env python
r"""Test for miscellaneous basic functionality."""
from matplotlib.style import use
import numpy as np
import pygimli as pg

import oskar
from oskar.feaOp import findForms
from oskar import (VectorSpace, solveLinearElasticity, solveThermoElasticity,
                   solve, tr, sym, I,
                   grad, div, asFunction, normL2, dirac, laplace, ScalarSpace)


from oskar.tests.utils import TestCollection, assertEqual, compSolve
from oskar.elasticity import (toLameCoeff, createElasticityMatrix, asNoNotation,
                              notationToStress, strainToNotation)


_show_ = False

def solveLinearElasticity_(*args, atol=4e-12, **kwargs):
    """Test for solve linear elasticity with different back-ends.(Internal)."""
    ref = kwargs.pop('ref', None)

    u1 = solveLinearElasticity(*args, **kwargs, core=False)
    print('.', end='', flush=True)
    if ref:
        assertEqual(u1, ref, atol=atol)

    u2 = solveLinearElasticity(*args, **kwargs, core=True)
    print('.', end='', flush=True)
    assertEqual(u1, u2, atol=atol)

    u3 = solveLinearElasticity(*args, **kwargs, useMats=True)
    print('.', end='', flush=True)
    assertEqual(u1, u3, atol=atol)

    return u3


class TestLinearElasticityMatrices(TestCollection):
    """Tests for the linear elasticity matrices."""

    def test_createNotations(self):
        """Test matrix notation conversion."""
        e = [1, 2, 3]
        eM = asNoNotation(e)
        assertEqual(eM, [[1, 3], [3, 2]])

        veM = np.asarray([eM, eM])
        assertEqual(asNoNotation(veM), asNoNotation([eM, eM]))


    def test_createElasticityMatrix3D(self):
        """Test createElasticityMatrix."""
        E = 42
        nu = 1/3

        lam, mu = toLameCoeff(E=E, nu=nu, dim=3)
        C0 = createElasticityMatrix(E=E, nu=nu, dim=3, voigtNotation=True)

        C = createElasticityMatrix(E=[E, E, E], nu=[nu, nu, nu], G=[mu, mu, mu],
                                   dim=3, voigtNotation=True,
                                   symmetry='orthotropic')
        self.assertEqual(C, C0)
        Ci = createElasticityMatrix(E=[E, E, E], nu=[nu, nu, nu],G=[mu, mu, mu],
                                   dim=3, voigtNotation=True,
                                   symmetry='orthotropic', inv=True)
        self.assertEqual(np.linalg.inv(Ci), C0)
        self.assertEqual(Ci, np.linalg.inv(C))

        Eo = [E*2, E*3, E*4]
        nuo = [nu*0.5, nu*0.3, nu*0.2]
        C = createElasticityMatrix(E=Eo, nu=nuo, G=[mu, mu, mu],
                                   dim=3, voigtNotation=True,
                                   symmetry='orthotropic')
        Ci = createElasticityMatrix(E=Eo, nu=nuo, G=[mu, mu, mu],
                                   dim=3, voigtNotation=True,
                                   symmetry='orthotropic', inv=True)
        self.assertEqual(C, np.linalg.inv(Ci))
        self.assertEqual(Ci, np.linalg.inv(C))

        Eo = [E*2, E*3]
        nuo = [nu*0.5, nu*0.3]
        C = createElasticityMatrix(E=Eo, nu=nuo, G=mu,
                                   dim=3, voigtNotation=True,
                                   symmetry='transverse isotropic')

        CI = createElasticityMatrix(E=Eo, nu=nuo, G=mu,
                                   dim=3, voigtNotation=True,
                                   symmetry='transverse isotropic', inv=True)

        self.assertEqual(C, np.linalg.inv(CI))
        self.assertEqual(CI, np.linalg.inv(C))


    def test_createElasticityMatrix2D(self):
        """Test createElasticityMatrix for 2D."""
        # check 2D -- plane state
        E = 42
        nu = 1/3
        lam, mu = toLameCoeff(E=E, nu=nu, dim=2)
        C = createElasticityMatrix(lam=lam, mu=mu, dim=2, voigtNotation=True)
        #print(C)

        C0 = createElasticityMatrix(E=E, nu=nu, dim=2,
                                    voigtNotation=True, inv=False)
        assertEqual(C, C0)

        CI = createElasticityMatrix(E=E, nu=nu, dim=2,
                                    voigtNotation=True, inv=True)
        self.assertEqual(np.linalg.inv(CI), C0)
        self.assertEqual(CI, np.linalg.inv(C0))

        C0 = createElasticityMatrix(E=E, nu=nu, dim=2,
                                    voigtNotation=True, inv=False,
                                    plain_strain=True)
        CI = createElasticityMatrix(E=E, nu=nu, dim=2,
                                    voigtNotation=True, inv=True,
                                    plain_strain=True)
        self.assertEqual(np.linalg.inv(CI), C0)
        self.assertEqual(CI, np.linalg.inv(C0))


        return
        # C0 = createElasticityMatrix(E=[E, E], nu=nu, G=mu,
        #                            dim=2, voigtNotation=True,
        #                            symmetry='orthotropic')
        # print(C0)
        # self.assertEqual(C0, C)

        # Ci = createElasticityMatrix(E=[E, E], nu=nu, G=mu,
        #                            dim=2, voigtNotation=True,
        #                            symmetry='orthotropic', inv=True)
        # self.assertEqual(np.linalg.inv(Ci), C0)
        # self.assertEqual(Ci, np.linalg.inv(C))

        # C0 = createElasticityMatrix(E=[E, E*2], nu=nu, G=mu,
        #                            dim=2, voigtNotation=True,
        #                            symmetry='orthotropic', inv=True)
        # Ci = createElasticityMatrix(E=[E, E*2], nu=nu, G=mu,
        #                            dim=2, voigtNotation=True,
        #                            symmetry='orthotropic', inv=True)
        # self.assertEqual(np.linalg.inv(Ci), C0)
        # self.assertEqual(Ci, np.linalg.inv(C))


        # check 3D


class TestLinearElasticity(TestCollection):
    """Tests for the linear elastics solver."""

    def test_MMS(self):
        """Test linear elastics with method of manufactured solutions."""
        x = np.linspace(0, 0.75, 3)
        mesh = pg.createGrid(x, x)

        E = 42      # Young's Modulus
        nu = 1/3    # Poisson's ratio

        lam, mu = toLameCoeff(E=E, nu=nu, dim=2)

        u = asFunction(u='(a - y + x)², (b + x +y )²')
        # u = asFunction(u='(a * sin(n * pi * x) * cos(n * pi * y),'
        #                  ' b * sin(n * pi * x) * cos(n * pi * y))')
        u = u(a=0.01, b=0.03, n=2)

        C = createElasticityMatrix(E=E, nu=nu, dim=mesh.dim(),
                                   voigtNotation=True)

        def eps(v):
            return sym(grad(v))

        def sigma1(v):
            return lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        def sigmaM(v):
            """Voigt's notation to return stress."""
            return C * eps(v)

        strain = eps(u)(mesh.cellCenters())
        stress = sigma1(u)(mesh.cellCenters())
        stressT = sigmaM(u)(mesh.cellCenters())
        assertEqual(stress, stressT)

        lam, mu = toLameCoeff(E=E, nu=nu, dim=mesh.dim())

        PDE1 = lambda u: -div(sigma1(u))
        PDEM = lambda u: -div(sigmaM(u))
        #PDEMSP = lambda u: -div(sigmaMSP(u))

        # print('PDE1:', PDE1(u))
        # print('PDEM:', PDEM(u))

        bc = {'Dirichlet':{'*':u}}

        v1 = VectorSpace(mesh, p=2, order=3)
        u1 = solve(PDE1(v1) == PDE1(u), bc=bc, useMats=True)
        assertEqual(normL2(u-u1), 0.0, atol=1e-12)

        eps1 = eps(u1)(mesh.cellCenters())
        assertEqual(eps1, strain)
        sig1 = sigma1(u1)(mesh.cellCenters())
        assertEqual(sig1, stress)

        vM = VectorSpace(mesh, p=2, order=3, elastic=True)
        uM = solve(PDEM(vM) == PDEM(u), bc=bc, useMats=True)
        assertEqual(normL2(u-uM), 0.0, atol=1e-12)

        epsM = eps(uM)(mesh.cellCenters())
        assertEqual(epsM, strain)
        sigM = sigmaM(uM)(mesh.cellCenters())
        assertEqual(notationToStress(sigM), stress)

        # pg.toc()
        uE = solveLinearElasticity_(mesh, E=E, nu=nu, var=1, bc=bc, f=PDE1(u),
                                    order=3, ref=u1)
        assertEqual(uE.strain(mesh.cellCenters()), strain)
        assertEqual(uE.stress(mesh.cellCenters()), stress)

        uE = solveLinearElasticity_(mesh, E=E, nu=nu, var=2, bc=bc, f=PDEM(u),
                                    order=3, ref=u1)
        assertEqual(uE.strain(mesh.cellCenters()), strain)
        assertEqual(uE.stress(mesh.cellCenters()), stress)

        ## orthotropic material
        mesh = pg.createGrid(x, x, x)
        mesh = pg.meshtools.refineHex2Tet(mesh, style=1) ##!Check style 2

        ## should this be exact solvable?
        # u = asFunction(u='a+(x + z)², b+ (x + y)², c + (y + z)²')
        u = asFunction(u='a+x², b+y², c+z²')

        u = u(a=0.1, b=0.3, c=0.4)

        bc={'Dirichlet': {'*': u}}

        Eo = [E*2, E*3, E*4]
        nuo = [nu*0.5, nu*0.3, nu*0.2]
        Go = [mu, mu, mu]

        C = createElasticityMatrix(E=Eo, nu=nuo, G=Go,
                                   dim=3, voigtNotation=True,
                                   symmetry='orthotropic')

        # print(PDEM(u))
        strain = eps(u)(mesh.cellCenters())
        stress = sigmaM(u)(mesh.cellCenters())

        vM = VectorSpace(mesh, p=2, order=4, elastic=True)
        uM = solve(PDEM(vM) == PDEM(u), bc=bc,
                   useMats=True)
        assertEqual(normL2(u-uM), 0.0, atol=1e-12)
        assertEqual(eps(uM)(mesh.cellCenters()), strain)
        assertEqual(notationToStress(sigmaM(uM)(mesh.cellCenters())), stress)


        if _show_:
            m = mesh
            with pg.tictoc('init'):
                fig, axs = pg.plt.subplots(3,4, figsize=(10,10))

            with pg.tictoc('parse'):
                um = u1(m)
                epm = eps(u1)(m)
                sim = notationToStress(sigmaM(uM)(m))

            with pg.tictoc('s1'):
                with pg.tictoc('s1.1'):
                    pg.show(m, abs(u), ax=axs[0][0], label=r'$\boldsymbol{u}$')
                with pg.tictoc('s1.2'):
                    pg.show(m, u, ax=axs[0][0])
                with pg.tictoc('s1.3'):
                    pg.show(m, um.T[0], ax=axs[0][1], label=r'$\boldsymbol{u}_{x}$')
                with pg.tictoc('s1.4'):
                    pg.show(m, um.T[1], ax=axs[0][2], label=r'$\boldsymbol{u}_{y}$')

            with pg.tictoc('s2'):
                with pg.tictoc('s2.1'):
                    pg.show(m, epm[:,0,0], ax=axs[1,0], label=r'$\epsilon_{xx}$')
                with pg.tictoc('s2.2'):
                    pg.show(m, epm[:,0,1], ax=axs[1,1], label=r'$\epsilon_{xy}$')
                with pg.tictoc('s2.3'):
                    pg.show(m, epm[:,1,0], ax=axs[1,2], label=r'$\epsilon_{yx}$')
                with pg.tictoc('s2.4'):
                    pg.show(m, epm[:,1,1], ax=axs[1,3], label=r'$\epsilon_{yy}$')

            with pg.tictoc('s3'):
                pg.show(m, sim[:,0,0], ax=axs[2,0], label=r'$\sigma_{xx}$')
                pg.show(m, sim[:,0,1], ax=axs[2,1], label=r'$\sigma_{xy}$')
                pg.show(m, sim[:,1,0], ax=axs[2,2], label=r'$\sigma_{yx}$')
                pg.show(m, sim[:,1,1], ax=axs[2,3], label=r'$\sigma_{yy}$')

            fig.tight_layout()


    def test_BernoulliBeam(self):
        """Test linear elastics with Euler-Bernoulli beam theory."""
        L = 25.
        H = 2.33
        W = 0.66
        E = 1e5
        nu = 0.3
        rho = 1e-3
        g = 9.81

        def createMesh(dim=2):
            Nx = 11
            Ny = 2
            if dim == 2:
                mesh = pg.createGrid(x=np.linspace(0, L, Nx+1),
                                        y=np.linspace(0, H, Ny+1))

                mesh = pg.meshtools.refineQuad2Tri(mesh, style=1)
            elif dim == 3:
                mesh = pg.createGrid(x=np.linspace(0, L, Nx+1),
                                        y=np.linspace(0, W, Ny+1),
                                        z=np.linspace(0, H, Ny+1))

                mesh = pg.meshtools.refineHex2Tet(mesh, style=1)
            return mesh

        def _testBodyLoad(dim=2):

            mesh = createMesh(dim)

            f = None
            if dim == 2:
                f = [0., -rho*g]
            elif dim == 3:
                f = [0., 0., -rho*g]

            C = createElasticityMatrix(E=E, nu=nu, dim=mesh.dim(),
                                                   voigtNotation=True)

            v = VectorSpace(mesh, p=2, order=3, elastic=True)

            bc = {'Dirichlet': {1: [0.0, 0.0, 0.0]}}
            u = solve(grad(v) * C * grad(v) == v*f, bc=bc,
                      solver='scipy', verbose=_show_, core=True)

            # generic formulation with Voigt or Kelvin notation
            ue1 = solveLinearElasticity_(mesh, E=E, nu=nu, rho=rho, var=1, bc=bc,
                                         order=3, ref=u, atol=9e-12)
            # isotropic formulation with small linear strain stress
            ue2 = solveLinearElasticity_(mesh, E=E, nu=nu, rho=rho, var=2, bc=bc,
                                   order=3, ref=u)

            assertEqual(ue1.strain(), ue2.strain(), atol=2e-11)
            assertEqual(ue1.stress(), ue2.stress(), atol=3e-9)

            #(https://en.wikipedia.org/wiki/Euler%E2%80%93Bernoulli_beam_theory)
            w = asFunction('q*x²*(6*L² - 4*L*x + x²)/(24*EI)')

            self.assertEqual(normL2(u-w(L=L, q=-rho*g*W, EI=E*W*H**2/12)),
                            0, atol=0.06)

            if _show_:
                ax = u.show(deform=u*300)[0]
                x = np.linspace(0, L, 21)
                wx = w(x, L=L, q=-rho*g*W, EI=E*W*H**2/12)
                if dim == 2:
                    ax.plot(x, H/2+300*wx, c='r')
                ax = pg.show()[0]
                ax.plot(x, 1000*wx, lw=1, label='Euler-Bernoulli Body-load')
                ax.plot(x, 1000*u(x)[:,dim-1], marker='.', lw=0.5,
                        label=f'Oskar dim:{dim}')
                ax.set(xlabel='$x$-coordinate in m',
                       ylabel='displacement $u_z$ in mm')
                ax.grid(True)
                ax.legend()

        def _testPointLoad(dim=2):
            mesh = createMesh(dim)

            P = 0.25*rho*g*L*(W*H)
            if dim == 2:
                f = dirac(rs=[L, W])*[0, -P]
            else:
                f = dirac(rs=[L, W])*[0, 0, -P*H]

            C = createElasticityMatrix(E=E, nu=nu, dim=mesh.dim(),
                                       voigtNotation=True)

            v = VectorSpace(mesh, p=2, order=3, elastic=True)

            #bc = {'Dirichlet': {1: [0.0, 0.0, 0.0]}}
            bc = {'Fixed': 1} # same like above
            u = solve(grad(v) * C * grad(v) == v*f, bc=bc,
                      solver='scipy', verbose=_show_, core=True)

            # generic formulation with Voigt's or Kelvin notation
            ue1 = solveLinearElasticity_(mesh, E=E, nu=nu, f=f, var=1, bc=bc,
                                   order=3, atol=2e-11, ref=u)
            # isotropic formulation with small linear strain stress
            ue2 = solveLinearElasticity_(mesh, E=E, nu=nu, f=f, var=2, bc=bc,
                                   order=3, atol=2e-11, ref=u)

            assertEqual(ue1.strain(), ue2.strain(), atol=2e-11)
            assertEqual(ue1.stress(), ue2.stress(), atol=4e-9)

            #(https://en.wikipedia.org/wiki/Euler%E2%80%93Bernoulli_beam_theory)
            w = asFunction('P*x²*(3*L - x)/(6*EI)')

            if dim == 2:
                EI = E * H**3/12
            else:
                EI = E * W*H**2/12
            self.assertEqual(normL2(u-w(L=L, P=-P, EI=EI)),
                             0, atol=0.075)

            if _show_:
                x = np.linspace(0, L, 21)
                ax = u.show(deform=u*300)[0]
                wx = w(x, L=L, P=-P, EI=EI)
                if dim == 2:
                    ax.plot(x, H/2+300*wx, c='r')
                #print(normL2(wx-u(x)[:,dim-1]))
                ax = pg.show()[0]
                ax.plot(x, 1000*wx, lw=1, label='Euler-Bernoulli Point-load')
                ax.plot(x, 1000*u(x)[:,dim-1], marker='.', lw=0.5,
                        label=f'Oskar dim:{dim}')
                ax.set(xlabel='$x$-coordinate in m',
                       ylabel='displacement $u_z$ in mm')
                ax.grid(True)
                ax.legend()

        _testBodyLoad(dim=2)
        _testBodyLoad(dim=3)
        _testPointLoad(dim=2)
        _testPointLoad(dim=3)


class TestThermoElasticity(TestCollection):
    """Tests for the ThermoElasticitySolver."""

    def test_thermalExpansion(self):
        """Test linear elastics with thermal expansion."""
        L = 1 #m
        H = 0.1
        mesh = pg.meshtools.createGrid(np.linspace(0, L, 11),
                                                [0, H/2, H],
                                                [0, H/2, H])

        mesh = pg.meshtools.refineHex2Tet(mesh)
        T0 = 0 # C
        T1 = 1 # C
        bcT = {'Dirichlet':{1:T0, 2:T1}}
        s = ScalarSpace(mesh, name='T')
        Th = solve(laplace(s) == 0, bc=bcT)

        T = asFunction('T_0 + (T_1-T_0) * x/L')(T_0=T0, T_1=T1, L=L)
        assertEqual(normL2(T-Th), 0, tol=2.5e-13)

        E = 1e5
        nu = 0.3
        beta = 1e-5
        lam, mu = toLameCoeff(E=E, G=None, nu=nu, dim=mesh.dim())

        def eps(v):
            return sym(grad(v))

        def sigma(v):
            return lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        def sigmaEff(v, T):
            return sigma(v) - (beta*(3*lam + 2*mu)*T*I(v))

        def sigmaEffM(v, T):
            return C*(eps(v) - beta*T*I(v))


        bcU = {'Dirichlet':{2:[0, 0, 0],                     # fixed right side
                            '3,4':[None, 0, 0],               # only slide in x
                            '5,6':[None, 0, 0],               # only slide in x
                            }}


        v = VectorSpace(mesh, p=2)
        uh = compSolve(-div(sigmaEff(v, Th)) == 0, bc=bcU)
        ut = compSolve(grad(v)*sigmaEff(v, Th) == 0, bc=bcU)
        assertEqual(uh, ut, tol=1e-12)

        # uh = solve(-div(sigmaEff(v, Th)) == 0, bc=bcU, keepHistory=False)
        # v = VectorSpace(mesh, p=2)
        # ut = solve(grad(v)*sigmaEff(v, Th) == 0, bc=bcU)
        # assertEqual(uh, ut, tol=1e-12)

        eps1 = eps(uh)(mesh.cellCenters())
        sig1 = sigmaEff(uh, Th)(mesh.cellCenters())

        vM = VectorSpace(mesh, p=2, elastic=True)
        C = createElasticityMatrix(E=E, nu=nu, dim=mesh.dim(),
                                   voigtNotation=True)

        ut = solve(-div(sigmaEffM(vM, Th)) == 0, bc=bcU)
        assertEqual(ut, uh, tol=1e-12)

        eps2 = eps(uh)(mesh.cellCenters())
        assertEqual(eps2, eps1)
        sig2 = sigmaEffM(uh, Th)(mesh.cellCenters())
        assertEqual(notationToStress(sig2), sig1)


        # ut = solveThermoElasticity(mesh,
        #                            E=E, nu=nu, beta=beta,
        #                            bcT=bcT, bcU=bcU, var=1)
        # assertEqual(uh, ut, tol=1e-12)

        # ut = solveThermoElasticity(mesh, E=E, nu=nu, beta=beta,
        #                            bcT=bcT, bcU=bcU, var=2)

        # E = anisotropyMatrix
        # ut = solveThermoElasticity(mesh, E=E, nu=nu, beta=beta,
        #                            bcT=bcT, bcU=bcU, var=2)

        #assertEqual(uh, ut, tol=1e-12)

        u = asFunction('beta*(1+nu)/(1-nu)*(theta)/(2*L)*(x²-L²), 0, 0')
        p = dict(beta=beta, nu=nu, theta=T1-T0, L=L)
        e = eps(u)
        assertEqual(eps1, e(mesh.cellCenters(), **p))
        s = sigmaEff(u, T)
        assertEqual(sig1, s(mesh.cellCenters(), **p), tol=2e-9)

        assertEqual(normL2(u(**p)-uh), 0, tol=2.6e-15)
        x = np.linspace(0, 1, 20)
        assertEqual(normL2(e(x, **p)[:,0,0]-eps(uh)(x)[:,0,0]), 0, tol=4e-14)
        assertEqual(normL2(s(x, **p)[:,1,1]-sigmaEff(uh, T)(x)[:,1,1]),
                    0, tol=2e-9)


    def test_bimetal(self):
        """Test bimetal strip example."""
        L = 1.0
        H = 0.05
        W = 0.1

        def createMesh(dim=2, refine=False):
            Nx = 11 * 1
            Ny = 2 * 2
            Nz = 2 * 2

            if dim == 2:
                mesh = pg.meshtools.createGrid(x=np.linspace(0, L, Nx+1),
                                               y=np.linspace(-H/2, H/2, Ny+1))
            else:
                mesh = pg.meshtools.createGrid(x=np.linspace(0, L, Nx+1),
                                               y=np.linspace(-H/2, H/2, Nz+1),
                                               z=np.linspace(-W/2, W/2, Ny+1),
                                               )

            if refine is True:
                if mesh.dim() == 3:
                    mesh = pg.meshtools.refineHex2Tet(mesh, style=1)
                else:
                    mesh = pg.meshtools.refineQuad2Tri(mesh, style=1)

            for c in mesh.cells():
                if c.center()[1] < 0:
                    c.setMarker(2)
                else:
                    c.setMarker(1)
            return mesh

        def eps(v):
            return sym(grad(v))

        def sigma(v):
            return lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        def sigmaEff(v, T):
            return sigma(v) - (alpha*(3*lam + 2*mu)*T*I(v))

        # def sigmaEff(v, T):
        #     return sigma(v) - (3*lam + 2*mu)*alpha * T * I(v)

        def sigmaEffM(v, T):
            return C*(eps(v) - alpha*T*I(v))

        Ea = 210 # GPa
        Eb = 210 # GPa
        nu = 0.0
        for dim in [2, 3]:
            mesh = createMesh(dim=dim, refine=False)
            # mesh.show(markers=True, showMesh=True)
            lam, mu = toLameCoeff(E=Ea, nu=nu, dim=mesh.dim())
            C = createElasticityMatrix(E=Ea, nu=nu, dim=mesh.dim(),
                                        voigtNotation=True)
            dT = 200.
            alpha = oskar.units.ParameterDict()
            alpha[1] = 1.3e-5
            alpha[2] = 2.4e-5
            bc={'fixed':1}

            v = VectorSpace(mesh, p=2)
            uh = compSolve(grad(v)*sigmaEff(v, dT) == 0, bc=bc, atol=4e-10,
                            solver='scipy')

            v = VectorSpace(mesh, p=2)
            ut = compSolve(-div(sigmaEff(v, dT)) == 0, bc=bc, atol=4e-10,
                            solver='scipy')
            assertEqual(uh, ut, tol=1e-12)

            v = VectorSpace(mesh, p=2, elastic=True)
            ut = compSolve(grad(v)*sigmaEffM(v, dT) == 0, bc=bc, atol=4e-10,
                            solver='scipy')
            assertEqual(uh, ut, tol=1e-12)

            v = VectorSpace(mesh, p=2, elastic=True)
            ut = compSolve(-div(sigmaEffM(v, dT)) == 0, bc=bc, atol=4e-10,
                            solver='scipy')
            assertEqual(uh, ut, tol=1e-12)

            # uh.show(deform=uh)
            maxDefl = -max(pg.y(uh.values))
            #print('Max deflection:', maxDefl)
            k = lambda d: 2*np.sin(np.atan(d/L)) / np.sqrt(L**2 + d**2)

            R_num = 1/k(maxDefl)

            #https://en.wikipedia.org/wiki/Bimetallic_strip
            ha = H/2
            hb = H/2
            a = 1 + (Ea*ha**2 - Eb*hb**2)**2 / (4 * Ea*ha * Eb*hb * H**2)
            R_ana = 1 / (3/2/a * (alpha[1] - alpha[2])*dT/H)
            self.assertEqual(R_num, R_ana, rtol=4e-3)


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
