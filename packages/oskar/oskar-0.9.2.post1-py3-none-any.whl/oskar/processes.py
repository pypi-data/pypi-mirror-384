#!/usr/bin/env python
"""Collection of pre build THM Processes solvers."""

import numpy as np
import pygimli as pg

from .op import (OP)
from .mathOp import (derive, dirac, div, grad, I, sym, tr, norm)

from .feaFunction import FEAFunction
from .feaSpace import (ScalarSpace, VectorSpace, TaylorHood, ConstantSpace)
from .feaSolution import FEASolution
from .linSolve import LinSolver, linSolve
from .solve import (DirichletManager, NeumannManager,
                    applyRHSBoundaryConditions, solve,
                    solveAlgebraicCrankNicolson, ensureInitialSolution)

from .elasticity import toLameCoeff, stressTo, notationToStress

# def linSolveFixNeumann(S, rhs, r, **kwargs):
#     pg.warn('Fixing neumann only condition.')
#     A = pg.BlockMatrix()
#     A.add(S, 0, 0)
#     A.add(r, 0, S.cols())
#     A.add(r, S.rows(), 0, transpose=True)

#     rhsc = pg.cat(rhs, [0.0])
#     uc = pg.solver.linSolve(A, rhsc, **kwargs)
#     return uc[0:len(rhs)]


class FEASolver(object):
    """Base class for process solver."""

    def __init__(self, mesh, bc=None, verbose=False, **kwargs):
        """Initialize FEASolver.

        Arguments
        ---------
        mesh: pg.Mesh
            Mandatory mesh for the modelling.
        bc: dict | None
            Boundary conditions. See. :ref:`userguide-fea-bc-dict`.
        """
        self.mesh = mesh

        if bc is None:
            bc = {}
        self.bc = bc # boundary condition

        self.verbose = verbose
        self.name = 'FEASolver'

        self.linSolver = LinSolver(solver=kwargs.pop('solver', 'scipy'))

        # default is useMats!

        self.core = kwargs.pop('core', None)
        if self.core is not None:
            # core is forced per arg
            self.assembleOptions = {'core': self.core}
        else:
            # default is useMats
            self.useMats = kwargs.pop('useMats', True)

            if self.useMats == True:
                self.assembleOptions = {'useMats': True}
            else:
                ## fallback for useMats forced to False
                self.assembleOptions = {'core': True}

        self.L = None # Left hand side expression (bilinear)
        self.M = None # Mass expression (bilinear)
        self.R = None # Right hand side expression (linear)

        self._mL = None # System matrix
        self._mM = None # Mass matrix
        self._vR = None # Right hand side vector

        self._vU = None # raw vector of the linsolver solution
        self.dirichlet = None # Dirichlet manager

        self.tictoc = pg.tictoc


    @property
    def mL(self):
        """
        """
        if self._mL is not None:
            # pg._g('mA (recover)', self)
            return self._mL

        # pg._g('mA (build)', self)
        with self.tictoc('assemble-L'):
            self._mL = self.L.assemble(**self.assembleOptions)

        return self._mL

    @property
    def mM(self):
        """
        """
        if self._mM is not None:
            # pg._y('mM (recover)', self)
            return self._mM

        # pg._y('mM (build)', self)
        with self.tictoc('assemble-M'):
            self._mM = self.M.assemble(**self.assembleOptions)

        return self._mM

    @property
    def vR(self):
        """
        """
        if self._vR is not None:
            # pg._r('vR (recover)', self)
            return self._vR

        # pg._r('vR (build)', self)
        with self.tictoc('assemble-R'):
            if self.R is not None:
                # pg._b(self.assembleOptions)
                # pg._b(self.R)
                self._vR = self.R.assemble(**self.assembleOptions)
            else:
                self._vR = pg.Vector(self.mL.cols())

        return self._vR


    @property
    def vU(self):
        """
        """
        self._vU = self._linSolve()
        return self._vU


    def showTimings(self, n=None):
        if n is not None:
            print(pg.timings(self.name +  '/' + n))
        else:
            print(pg.timings(self.name))


    def isPureNeumann(self, bc):
        """Check if the given boundary condition is pure Neumann.

        Check if the given boundary condition is pure Neumann, i.e., no
        Dirichlet condition given.
        """
        u = ScalarSpace(self.mesh)
        d = DirichletManager({u:bc})

        if len(d.idx) == 0:
            return True

    def _applyBC(self, bc={}):
        """ Private.  Only use for single step calculations.
        """

        # self.swatches['assemble-L'].start()
        # self.mL = self.L.assemble(**self.assembleOptions)
        # self.swatches['assemble-L'].store()

        # self.swatches['assemble-R'].start()
        # if self.R is not None:
        #     self.vR = self.R.assemble(**self.assembleOptions)
        # else:
        #     self.vR = pg.Vector(self.mL.cols())
        # self.swatches['assemble-R'].store()

        self.mL ## call once to ensure creation time is not count
        self.vR ## call once to ensure creation time is not count

        with self.tictoc('rhs'):
            applyRHSBoundaryConditions(bc, self.vR)

        # check how to cache!
        if self.dirichlet is None:
            self.dirichlet = DirichletManager(bc)

        with self.tictoc('dirichlet'):
            self.dirichlet.apply(self.mL, rhs=self.vR, swatches=self.tictoc)


    def _linSolve(self):
        """Private. Only use for single step calculations.

        TODO:
            check if mA has been changed:
            compare isChanged flag or time hashing
        """
        if not self.linSolver.isFactorized():
            with self.tictoc('solver/factorize'):
                self.linSolver.factorize(self.mL)

        with self.tictoc('solver/solve'):
            vU = self.linSolver.solve(self.vR)

        return vU

class HeatConductionSolver(FEASolver):
    """Solver for heat equation."""

    def __init__(self, mesh, lam=None, cv=None, verbose=False, **kwargs):
        r"""Finite element approximation for heat conduction.

        Finite element approximation for heat conduction to solve for
        a temperature :math:`T` with:

        .. math::

            c_{\rm v} \partial_t T
            - \nabla\cdot(\lambda\nabla T) =\:& H_{\rm v} \quad~\text{in}\quad\Omega \\
            T(\boldsymbol{r}, 0) =\:& T_0 \quad\text{in}\quad\Omega \\
            T(\boldsymbol{r}, t) =\:& T_{\rm d} \quad\text{on}\quad\Gamma_{\rm Dir} \\
            \lambda\partial_{\boldsymbol{n}}T(\boldsymbol{r}, t) =\:& q \quad\text{on}\quad\Gamma_{\rm Neu}

        ====================== ================================== ========================================
        Symbol                 Description                        Dimension
        ====================== ================================== ========================================
        :math:`T`              temperature                        :math:`\mathsf{\Theta}`
        :math:`T_0`            initial temperature                :math:`\mathsf{\Theta}`
        :math:`\lambda`        thermal conductivity               :math:`\mathsf{M}\cdot\mathsf{L}\cdot\mathsf{\Theta}^{-1}\cdot\mathsf{T}^{-3}`
        :math:`c_{\rm v}`      volumetric heat capacity           :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{\Theta}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`H_{\rm v}`      volumetric heat source             :math:`mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-3}`
        ====================== ================================== ========================================

        The function for the boundary conditions :math:`T_{\rm d}(\boldsymbol{r}, t)` and
        :math:`q(\boldsymbol{r}, t)` are given with the `bc` argument.

        Load vector :math:`H_{\rm v}=H_{\rm v}(\boldsymbol{r}, t) \neq 0` and
        initial condition :math:`T_0\neq 0` for a time dependency is applied with
        :py:mod:`oskar.processes.HeatConductionSolver.solve` method.

        Arguments
        ---------
        mesh: pg.Mesh
            Mesh for :math:`\Omega` to solve for.

        lam: FEASolution | FEAFunction | iterable | float [0]
            Thermal conductivity.

        cv: FEASolution | FEAFunction | iterable | float [0]
            Volumetric heat capacity. :math:`c_{\rm v} = c_{\rm p}\rho`
            with :math:`c_{\rm p}` specific heat capacity and :math:`\rho` density.

        bc: dict
            Dictionary of boundary conditions.
            See :ref:`userguide-fea-bc-dict`.

        Keyword Args
        ------------
        solver: str or LinSolver
            Linear solver. **TODO** Link to solver options.

        theta: float
            Crank-Nicholson parameter for time discretization.
            See: :ref:`userguide-fea-timediscrete`.
        """
        super().__init__(mesh, verbose=verbose, **kwargs)
        self.name = 'Temperature'

        self.lam = lam
        """thermal conductivity"""
        self.cv = cv
        """volumetric heat capacity"""
        self.init()


    def init(self):
        """
        """
        self.u = u = ScalarSpace(self.mesh, name='T', order=2)

        if isinstance(self.lam, dict):
            self.lam = pg.solver.cellValues(self.u.mesh, self.lam)

        self.L = grad(u) * self.lam * grad(u)
        self.M = u * self.cv * u


    def solve(self, Hv=0.0, times=None, T0=0.0, **kwargs):
        """Solve heat conduction equation.

        Arguments
        ---------
        Hv: FEAFunction | float
            Volumetric heat flux for the right hand side.

        times: iterable [None]
            Time steps for time discretization. If times is None,
            the steady state solution is calculated.

        T0: FEAFunction | float [0]
            Initial temperature.

        Keyword Args
        ------------
        theta: float
            Crank-Nicholson parameter for time discretization.

        Returns
        -------
        T: FEASolution
            Temperature solution.
        """
        # self._applyBC(bc={self.u:self.bc})
        # u = self.u.split(self.vU)

        theta = kwargs.pop('theta', 1.0)

        f = kwargs.pop('Hv', None)
        if f is not None:
            self.R = self.u * f

        if times is None:
            ### stationary
            applyRHSBoundaryConditions(self.bc, self.vR)
            self.dirichlet.apply(self.vR, swatches=self.tictoc)

            T = (self.u).split(self.vU)
            T.solver = self
            return T
        else:
            pg.critical('implementme!')
            # Sought scalar field for the mesh with linear basis functions
            u = ScalarSpace(self.mesh, p=1)
            # Assemble system matrix regarding weak formulation
            S = (grad(u) * self.lam * grad(u)).assemble(core=True)
            # Assemble mass matrix needed for time integration
            M = (u * self.rc * u).assemble(core=True)
            # Assemble source term
            R = np.zeros(u.dof)
            # Set singular point source at origin
            if isinstance(f, OP):
                srcNodeID = self.u.mesh.findNearestNode(f.a.rs)

                R = np.zeros(self.u.dof)
                # Set singular point source at origin
                R[srcNodeID] = f.b
                #R[srcNodeID] = P


            dirichlet = DirichletManager({u:{'Dirichlet':{'*':0.0}}})

            T_fem = pg.solver.crankNicolson(times=times, S=S, I=M, f=R,
                                            dirichlet=dirichlet,
                                            theta=0.6,
                                            #progress=pg.utils.ProgressBar(len(times))
                                            )
            return T_fem


def solveHeatConduction(mesh, lam=None, Hv=0.0, **kwargs):
    """Shortcut to solve heat conduction equation.

    See :py:mod:`oskar.processes.HeatConductionSolver`.
    """
    ts = HeatConductionSolver(mesh, lam, **kwargs)
    T = ts.solve(Hv, times=kwargs.pop('times', None),
                 T0=kwargs.pop('T0', None))
    return T


class DarcySolver(FEASolver):
    """Solver for Darcy equation."""

    def __init__(self, mesh, K=1.0, bcP={}, bcV={}, var=1, verbose=False,
                 **kwargs):
        super().__init__(mesh, verbose=verbose, bc={}, **kwargs)
        self.name = 'Darcy'

        self.bcP = bcP # boundary condition (pressure)
        self.bcV = bcV # boundary condition (velocity)
        self.var = var

        self.K = K
        if pg.isScalar(self.K):
            self.K = np.diag(np.ones(mesh.dim()) * self.K)

        self.KI = np.linalg.inv(self.K)

        self.init()

    def init(self):
        """Initialize Darcy solver."""
        if self.var == 1:
            ### Scalar elements
            self.p = p = ScalarSpace(self.mesh)
            self.bc = {p:self.bcP}

            self.L = grad(p)*grad(p)
            self.M = p*p

        elif self.var == 2:
            ### Mixed elements. Achieve symmetry using grad
            # Neumann BC is natural means dp/dn=0 everywhere if not defined
            # else.
            # Dirichlet BC is essential, If no Dirichlet is given,
            # the Neumann Fix need to be applied.
            v, p = TaylorHood(self.mesh, order=3)
            self.v = v
            self.p = p
            self.bc = {p:self.bcP, v:self.bcV}

            self.L = v*self.KI*v + grad(p)*v + v*grad(p)
            self.M = v*v + p*p

        elif self.var == 3:
            ### Mixed elements. Achieve symmetry with div
            # Dirichlet is natural, means v*p=0 everywhere if not defined else;
            # Neumann is essential
            v, p = TaylorHood(self.mesh, order=3)
            self.v = v
            self.p = p

            if 'Dirichlet' in self.bcP and '*' in self.bcP['Dirichlet']:
                pDir = self.bcP['Dirichlet']['*']
            else:
                pg.info('Solve for p with pDirichlet (grad(p)*grad(p)) to fill '
                        'unknown p on outside boundaries.')
                ## pDir is natural condition here and needs to be
                # defined on all!!
                ## boundaries or its set to 0.0. If we don't have values
                # for all, find them here for test cases.
                _, pDir = solveDarcy(self.mesh, bcP=self.bcP, var=1)
                #pDir = solve(grad(u)*grad(u) == 0, bc=bcP)
                #pg.show(pDir)
                #pg.wait()

            # self.bcP.pop('Dirichlet', None)
            # bcP.pop('Neumann', None)

            bcVL = self.bcV.copy()
            bcVL['assemble'] = {'*':-pDir*(v*norm(v))}
            self.bc = {v:bcVL}

            self.L = v*self.KI*v - div(v)*p - p*div(v)
            self.M = v*v + p*p

        if self.isPureNeumann(self.bcP):
            pg.warn('Fixing neumann only condition.')
            self.c = c = ConstantSpace(dofOffset=self.p.dofs.stop)
            self.L += c*self.p + self.p*c

        self.dirichlet = DirichletManager(self.bc)

        ###  self.mL evaluated here!
        self.dirichlet.apply(self.mL, swatches=self.tictoc)


    def solve(self, fP=0.0, fV=None, bcP={}, bcV={}, times=None,
              v0=None, p0=None, **kwargs):
        """Solve Darcy equation.

        Arguments
        ---------
        fV:
            Note: need to be without K
        """
        with pg.tictoc(f'{self.name}/solve'):
            if self.var == 1:
                ### special handling for Darcy with non-mixed elements
                self.R = -self.p * fP
            else:
                self.R = self.p * fP

                if fV is not None:
                    #self.R += self.v * self.KI * fV
                    self.R += self.v * fV

            if len(bcP.keys()) > 0 or len(bcV.keys()) > 0:
                pg.critical('implement me')

            if self.isPureNeumann(self.bcP):
                self.R += self.c

            self._vR = None

            if times is None:
                applyRHSBoundaryConditions(self.bc, self.vR)
                self.dirichlet.apply(self.vR, swatches=self.tictoc)

                if self.var == 1:
                    p = (self.p).split(self.vU)
                    p.solver = self
                else:
                    v, p = (self.v*self.p).split(self.vU)
                    v.solver = self
                    p.solver = self
            else:
                # apply for steady and unsteady
                applyRHSBoundaryConditions(self.bc, self.vR)

                # pg._r('refactor me')
                theta = kwargs.pop('theta', 1.0)
                # self.mM = self.M.assemble(**self.assembleOptions)

                u0 = pg.Vector(self.vR.size(), 0.0)
                if v0 is not None:
                    print('v0', v0.shape, v0.vals.shape)
                    self.v.fill(u0, v0)
                if p0 is not None:
                    print('p0', p0.shape, p0.vals.shape)
                    self.p.fill(u0, p0)

                us = pg.solver.crankNicolson(times, self.mL, self.mM, f=self.vR,
                                            dirichlet=self.dirichlet,
                                            u0=u0,
                                            theta=theta,
                                            solver=self.linSolver)
                u = us[-1]

            # pg._r(min(u), max(u), np.mean(u), np.linalg.norm(u))
            ### special handling for darcy with non-mixed elements
            if self.var == 1:
                gradP = -pg.solver.grad(self.mesh, p)

                v = pg.meshtools.cellDataToNodeData(self.mesh,
                                            gradP[:,0:self.mesh.dim()] @ self.K)

                # if fV is not None:
                #     for c in self.mesh.cells():
                #         v[c.id(), 0] += fV(c.center(), c)[0]
                #         v[c.id(), 1] += fV(c.center(), c)[1]

                if fV is not None:
                    for n in self.mesh.nodes():
                        v[n.id(), 0] += fV(n.pos(), n)[0]
                        v[n.id(), 1] += fV(n.pos(), n)[1]

                # ax, _ = pg.show(self.mesh, pg.abs(v))
                # pg.show(self.mesh, v, ax=ax)
                # pg.wait()

                v = FEASolution(VectorSpace(self.p.mesh), values=v)


        return v, p


def solveDarcy(mesh, K=1.0, fP=0.0, fV=None, g=None, bcP={}, bcV={}, var=1,
               **kwargs):
    """Shortcut to solve Darcy equation.

    See :py:mod:`oskar.processes.DarcySolver`.
    """
    darcy = DarcySolver(mesh, K, bcP, bcV, var=var, **kwargs)
    return darcy.solve(fP, fV)


class RichardsSolver(FEASolver):
    """Solver for Richards equation.
    """
    def __init__(self, mesh, vel=None,
                 D=1.0, b=0.0, c=1.0, bc={},
                 supg=True, assembleOnly=False, verbose=False,
                 **kwargs):
        """
        """
        pg.critical('implementme!')

    def solve(self):
        """Call RichardsSolver.
        """
        pg.critical('implementme!')


def solveRichards(mesh, **kwargs):
    """Shortcut to solve Richards equation.

    See :py:mod:`oskar.processes.RichardsSolver`.
    """
    sol = RichardsSolver(mesh, **kwargs)
    return sol.solve()


class AdvectionDiffusionSolver(FEASolver):
    r"""Solver for Advection-diffusion-sorption-decay equation.
    """
    def __init__(self, mesh, v=None, D=1.0, lam=0.0, R=1.0, bc=None,
                 **kwargs):
        r"""Finite element approximation
        for advection-diffusion-sorption-decay equation to solve for
        a concentration :math:`c(\boldsymbol{r}, t)` with:

        .. math::

            R \partial_t c
            - \nabla\cdot(D\nabla c)
            + \boldsymbol{v}\nabla c
            + \lambda c =\:&  f \quad~\text{in}\quad\Omega \\
            c(\boldsymbol{r}, 0) =\:& c_0 \quad\text{in}\quad\Omega \\
            c(\boldsymbol{r}, t) =\:& g \quad\text{on}\quad\Gamma_{\rm Dir} \\
            D\partial_{\boldsymbol{n}}c(\boldsymbol{r}, t) =\:& h \quad\text{on}\quad\Gamma_{\rm Neu}

        ====================== ================================== ========================================
        Symbol                 Description                        Dimension
        ====================== ================================== ========================================
        :math:`c`              concentration                      :math:`\mathsf{N}`
        :math:`c_0`            initial concentration              :math:`\mathsf{N}`
        :math:`\boldsymbol{v}` flow velocity                      :math:`\mathsf{L}\cdot\mathsf{T}^{-1}`
        :math:`D`              diffusivity                        :math:`\mathsf{L}^2\cdot\mathsf{T}^{-1}`
        :math:`\lambda`        decay rate                         :math:`\mathsf{T}^{-1}`
        :math:`R`              retardation factor due to sorption :math:`[1]`
        :math:`l`              load function                      :math:`\mathsf{N}\cdot\mathsf{T}^{-1}`
        ====================== ================================== ========================================

        The function for the boundary conditions :math:`g(\boldsymbol{r}, t)` and
        :math:`h(\boldsymbol{r}, t)` are given with the `bc` argument.

        Load vector :math:`f=f(\boldsymbol{r}, t) \neq 0` and
        initial condition :math:`c_0\neq 0` for a time dependency is applied with
        :py:mod:`oskar.processes.AdvectionDiffusionSolver.solve` method.

        Arguments
        ---------
        mesh: pg.Mesh
            Mesh for :math:`\Omega` to solve for.

        v: FEASolution | FEAFunction | iterable | [vector, ] | float [0]
            Flow Velocity.

        D: FEASolution | FEAFunction | iterable | [vector, ] | float [0]
            Diffusivity.

        lam: FEASolution | FEAFunction | iterable | float [0]
            Decay value.

        R: FEASolution | FEAFunction | iterable | float [0]
            Retardation factor.

        bc: dict
            Dictionary of boundary conditions.
            See :ref:`userguide-fea-bc-dict`.

        Keyword Args
        ------------
        solver: str or LinSolver
            Linear solver. **TODO** Link to solver options.

        supg: bool[False]
            Streamline upwind Petrov Galerkin stabilization.
            **TODO**. Merge with stabilization argument.

        stabilization: {}
            Dictionary of stabilization options.

        theta: float
            Crank-Nicholson parameter for time discretization.
            See: :ref:`userguide-fea-timediscrete`.

        Example
        -------
        >>> import pygimli as pg
        >>> from oskar import *
        >>>
        >>> x = np.linspace(-5, 5, 200)
        >>> t = np.linspace(0, 1, 101)
        >>> mesh = pg.createGrid(x)
        >>> v = 2.0
        >>> D = 0.2
        >>> lam = 0.0195
        >>>
        >>> # compare with impulse response of the fundamental solution
        >>> c = asFunction(c='1/(4*pi*D*t)**(1/2)*exp(-(x-v*t)²/'
        ...                  '(4*D*t))*exp(-lam*t)')
        >>> c = c(D=D, lam=lam, v=v)
        >>>
        >>> ad = AdvectionDiffusionSolver(mesh, v=v, D=D, lam=lam,
        ...                               bc={'Dirichlet':{'*':0}})
        ...
        >>> ch = ad.solve(ic=dirac(rs=[0.0, 0.0], cellScale=True), times=t)
        ... # doctest: +ELLIPSIS
        >>>
        >>> ax = pg.show()[0]
        >>> ax.plot([0,0], [0, 1], c='k', label='Impulse (t=0)')
        ... # doctest: +ELLIPSIS
        [...
        >>> ax.plot(x, c(x, t=t[-1]), label='Fundamental solution')
        ... # doctest: +ELLIPSIS
        [...
        >>> ax.plot(x[::5], ch(x[::5], t=t[-1]), lw=0.5, marker='.',
        ...         label='Oskar') # doctest: +ELLIPSIS
        [...
        >>> ax.set(xlabel='x', ylabel='Concentration $c$',
        ...        title='Concentration after 1s') # doctest: +ELLIPSIS
        [...
        >>> ax.grid() # doctest: +ELLIPSIS
        >>> ax.legend() # doctest: +ELLIPSIS
        <...
        >>>
        >>> print(np.round(normL2(c-ch), 14))
        0.00685004673915
        """
        ## change solver default to scipy
        self.linSolver = kwargs.pop('solver', 'scipy')
        super().__init__(mesh, bc=bc, **kwargs)

        self.name = 'Advection-diffusion'

        if kwargs.pop('p2', False) is True:
            pg.warning('p2 not recommended for advection with high'
                       'Peclet numbers until there is a better'
                       'stabilization available')
            self.u = ScalarSpace(mesh, p=2, name='s', order=3)
        else:
            self.u = ScalarSpace(mesh, p=1, name='s', order=2)

        self.vel = v
        self.c = R
        self.D = D
        self.b = lam
        self.stabilization = kwargs.pop('stabilization', None)
        self.supg = kwargs.pop('supg', False)
        self.theta = kwargs.pop('theta', 0.6)


    def solve(self, v=None, f=0, D=None, lam=None, R=None, times=None,
              ic=None, **kwargs):
        """Solve the advection-diffusion-sorption-decay problem.

        Solve the equation stationary if no times are given
        or time depending for given initial condition.

        Arguments
        ---------
        v: FEASolution | FEAFunction | iterable | [vector, ] | float [0]
            Flow velocity, overwrite defaults from class initializing.

        D: FEASolution | FEAFunction | iterable | [vector, ] | float [0]
            Diffusivity, overwrite defaults from class initializing.

        lam: FEASolution | FEAFunction | iterable | float [0]
            Decay value, overwrite defaults from class initializing.

        R: FEASolution | FEAFunction | iterable | float [0]
            Retardation factor, overwrite defaults from class initializing.

        ic: FEASolution | FEAFunction | iterable | float [0]
            Initial condition, i.e., values for the first time step.

        times: iterable of float
            Time discretization.

        Returns
        -------
        ch: FEASolution
            FEASolution instance of the sought concentration.
        """
        with pg.tictoc(f'{self.name}/solve'):
            if v is not None:
                self.vel = v
            if R is not None:
                self.c = R
            if D is not None:
                self.D = D
            if lam is not None:
                self.b = lam

            D = self.D          # diffusivity
            b = self.b          # decay
            u = self.u          # space
            vel = self.vel
            c = self.c          # R retardation

            ut = u

            if vel is None:
                vel = 0.0

            if self.stabilization is not None:

                if 'diffusion' in self.stabilization:
                    self.supg = False
                    beta = self.stabilization['diffusion']
                    h = self.mesh.h()
                    pg._g(beta)
                    D = D + beta*abs(vel)*h/2

                    #pg._y(D)

                if 'supg' in self.stabilization:
                    self.supg = self.stabilization['supg']

            if self.supg is True:
                with self.tictoc('supg'):
                    # pg = u + beta * h/2 * grad(u)
                    # pg = u + beta * h/2 * v/abs(v)*grad(u);
                    # 0 <= beta <= 1
                    # beta = 1 -> upwind approximation
                    # beta = acoth(Pe) - 1/Pe -> supg # for p=1 only
                    # beta = 0 -> no stabilization
                    # Streamline-Upwind Petrov-Galerkin stabilization
                    if isinstance(vel, OP):
                        ### TODO optimize with:
                        ### cv = self.mesh.h() / (2.0 * abs(vel).eval(self.mesh.cellCenters()))
                        ### Note! mesh.h() don't work for p > 1
                        @FEAFunction
                        def cv(p, entity):
                            #print('entity:', entity, p)
                            vAbs = pg.abs(vel(p))
                            if vAbs > 0:
                                ret = entity.shape().h()/(2.0*vAbs)
                                #sys.exit()
                                return ret
                            else:
                                return 0.0

                        class CV(FEAFunction):
                            def __init__(self, vel, *args, **kwargs):
                                super().__init__(*args, **kwargs)
                                self.vel = vel

                            def eval(self, pnts, **kwargs):
                                if isinstance(pnts, pg.core.stdVectorR3Vector):
                                    ret = pg.core.stdVectorRVector()
                                    pg.core.testEvalEmap(kwargs['elementMap'], self.vel(pnts), ret)
                                    return ret

                                #pg._b(pnts, kwargs)
                                if not 'entity' in kwargs:
                                    raise TypeError()

                                if pg.isPos(pnts):
                                    vAbs = pg.abs(self.vel(p))
                                    if vAbs > 0:
                                        ret = entity.shape().h()/(2.0*vAbs)
                                        return ret
                                    else:
                                        return 0.0

                        if 1 and 'useMats' in self.assembleOptions:
                            if self.assembleOptions['useMats'] == True:
                                cv = CV(vel)

                    else:
                        if vel != 0.0:
                            cv = self.mesh.h() / (2.0 * pg.abs(vel))
                            #cv = self.mesh.h() / (2.0 * pg.abs(vel))*10 # smooth on one side!, check!
                        else:
                            cv = 0

                    ut = u + cv*(vel*grad(u))

                    if 0:
                        if isinstance(vel, OP):
                            pg._y(vel,
                                vel.evalOrder, vel.continuous,
                                (vel/abs(vel)).evalOrder,
                                (vel/abs(vel)).continuous, type(vel))

                            pg._g()

                            h = self.mesh.h()
                            # vc = (vel/abs(vel))(self.mesh.cellCenters())
                            # ut = u + h/2*(vc*grad(u))
                            ut = u + (h/2) * ((vel/abs(vel))*grad(u))
                        else:
                            pg._r()
                            ut = u

            self.L = ut * (vel*grad(u)) + grad(u)*D*grad(u) + u*b*u
            self.M = ut * c*u
            #self.M = u * c*u # check theory!!!
            self.R = u*f

            # self.R = u * dirac(u, rs=[0.0, 0.0], cellScale=True)

            self._mL = None # check if necessary
            self._mM = None # check if necessary
            self._vR = None # check if necessary

            self.neumann = NeumannManager({u:self.bc})
            self.dirichlet = DirichletManager({u:self.bc})

            if times is None:
                ### steady
                with self.tictoc('bc'):
                    self._applyBC(bc={u:self.bc})

                u = u.split(self.vU)
                u.solver = self
                return u

            else:
                ### unsteady no SUPG
                ### apply neumann here,  if exists here
                # applyRHSBoundaryConditions({u:self.bc}, self.vR)
                # pg._r('refactorme')

                if not self.supg:
                    # ic = (u*ic).assemble(useMats=True)
                    # self.ic = ic
                    #T0 = dirac(u, rs=[0.0, 0.0], cellScale=True)       # dirac impulse
                    #ic = (u*T0).assemble(useMats=True)

                    ic = ensureInitialSolution(ic, space=u)

                    P = None
                    # if len(times) > 2:
                    #     P = pg.utils.ProgressBar(len(times))

                    # print(self.L)
                    # print(self.R)
                    # print(c)

                    uh = solveAlgebraicCrankNicolson(ic, self.L, self.R, c,
                                                      self.dirichlet,
                                                      self.neumann,
                                                      times,
                                                      theta=self.theta,
                                                      progress=P,
                                                      solver=self.linSolver,
                                                      **kwargs)
                    #pg._b()
                    return uh
                else:
                    # refactor me -- test elder
                    u0 = ic
                    if pg.isScalar(u0) and not pg.isScalar(u0, 0.0):
                        u0 = u.split(pg.Vector(u.dof, u0)).values

                    elif pg.isArray(u0, self.mesh.nodeCount()) and len(u0) != u.dof:
                        implementme_with_FEASolution_eval
                        #u0 = pg.interpolate(mesh, u0, u.mesh.positions())

                    elif pg.isArray(u0, u.dof):
                        u0 = u.split(u0).values

                    elif isinstance(u0, FEASolution):
                        u0 = u0.values

                    elif callable(u0):
                        u0 = u0(u.mesh.positions())

                    M = self.mM
                    A = self.mL
                    R = self.vR

                    with self.tictoc('CN'):
                        self._vU = pg.solver.crankNicolson(times,
                                                A, M, f=R,
                                                dirichlet=self.dirichlet,
                                                u0=u0, theta=self.theta,
                                                solver=self.linSolver,
                                                swatches=self.tictoc,
                                                progress=False
                                                        )
                    self.ic = u0

                    if len(times) == 2:
                        return u.split(self._vU[-1], time=times)
                    else:
                        return u.split(self._vU[-1])#, self._vU


def solveAdvectionDiffusion(mesh, D=1.0, f=0.0,
                            ic=0.0, bc={}, times=None,
                            **kwargs):
    """Shortcut to one-line the AdvectionDiffusionSolver.

    See :pymod:`oskar.processes.AdvectionDiffusionSolver` for arguments.
    """
    ads = AdvectionDiffusionSolver(mesh, D=D, bc=bc, **kwargs)
    return ads.solve(f=f, times=times, ic=ic)


class LinearElasticitySolver(FEASolver):
    """Solver for linear elasticity equation.

    Hooke's equation.

    """

    def __init__(self, mesh, lam=None, mu=None, E=None, nu=None,
                 var:int=1, verbose:bool=False, **kwargs):
        r"""
        Arguments
        ---------
        var: int[1]
            Variant of the linear elasticity equation to solve for.

            * `var=1`
                Means calculation anisotropic constitutive matrix with
                Voigt or Kelvin notation for strain and stress.
            * `var=2`
                Isotropic calculation with strain and stress formulation.

        Keyword Args
        ------------
        p: int[2]
            Polynomial order of the finite element space.
        order: int[3]
            Order of integration for assembling.
        """
        super().__init__(mesh, verbose=verbose, **kwargs)

        ## default quadratic
        self._p = kwargs.pop('p', 2)
        """ Polynomial order of the finite element space. """
        self._order = kwargs.pop('order', 3)
        """ Default integration order for the assembling. """

        if lam is None and mu is None:
            self.lam, self.mu = toLameCoeff(E=E, nu=nu, dim=mesh.dim())
        else:
            self.lam = lam
            self.mu = mu

        # set variation specific stuff
        self.var = var

        if self.var == 1:
            self.voigtNotation = kwargs.get('voigtNotation', True)

            if isinstance(self.lam, dict):
                self.C = {}

                for k in self.lam.keys():

                    self.C[k] = pg.solver.createConstitutiveMatrix(
                                            lam=self.lam[k],
                                            mu=self.mu[k],
                                            dim=self.mesh.dim(),
                                            voigtNotation=self.voigtNotation)

            else:
                self.C = pg.solver.createConstitutiveMatrix(lam=self.lam,
                                                       mu=self.mu,
                                                       dim=self.mesh.dim(),
                                            voigtNotation=self.voigtNotation)


    def strain(self, u, pnts=None):
        r"""Calculate the strain matrix for a displacement FEASolution.

        Attributes
        ----------

        u: FEASolution
            Solution from elastic calculation
        """
        if not hasattr(u, 'strainValues_'):
           u.strainValues_ = None

        if pnts is None:
            pnts = u.mesh

        # pg._b(pnts)

        if u.strainValues_ is None or len(pnts) != len(u.strainValues_):

            # if self.var == 1:
            #     from .elasticity import strain
            #     u.strainValues_ = strain(u)
            # else:
            u.strainValues_ = self.eps(u).eval(pnts)

        return u.strainValues_


    def stress(self, u, pnts=None, C=None, lam=None, mu=None, var='plain',
               **kwargs):
        r"""Calculate the stress matrix for a displacement FEASolution.

        Attributes
        ----------

        u: FEASolution | np.ndarray.
            Solution from elastic calculation.

        var: str, default='plain'
            Stress variant for each cell
            - 'mean': mean stress values
            - 'plain': complete stress tensor (see description)
            - 'mises': Von Mises stress

        """
        #pg._b(u)
        if isinstance(u, np.ndarray):
            if self.var == 1:
                # if self.C is None:
                #     pg.critical("We need at least C or lam/mu to calculate " \
                #                 "stress for given strain.")
                pg.critical("needed?")
                return self.sigma(u, C=self.C)(pnts)
            else:
                pg.tic()
                s = self.sigma(u, lam=lam, mu=mu)
                pg.toc('solver.stress')
                return s

        if not hasattr(u, '_stressValuesCache'):
           u._stressValuesCache = None

        if u._stressValuesCache is None:
            if pnts is None:
               pnts = u.mesh

            if self.var == 1:
                if C is None:
                    C = u.solver.C
                u._stressValuesCache = notationToStress(self.sigma(u, C=C)(pnts))
            else:
                if lam is None:
                    lam = u.solver.lam
                    mu = u.solver.mu

                if isinstance(lam, dict):
                    lam = np.array([lam[m] for m in self.mesh.cellMarkers()])
                    mu = np.array([mu[m] for m in self.mesh.cellMarkers()])

                u._stressValuesCache = self.sigma(u, lam=lam, mu=mu)(pnts)

        if var.lower() != 'plain':
            return stressTo(u._stressValuesCache, var=var)

        return u._stressValuesCache


    def eps(self, u):
        return sym(grad(u))


    def sigma(self, u, lam=None, mu=None, C=None):
        """Calculate the stress matrix for a strain FEASolution."""
        if self.var == 1:
            return C * self.eps(u)

        lam = lam or self.lam
        mu = mu or self.mu

        if isinstance(u, FEASolution | VectorSpace):
            e = self.eps(u)
        else:
            #assuming u is already strain
            pg.warn('in use?')
            e = u

        return lam*tr(e)*I(u) + 2.0*mu*e


    def solve(self, f=None, rho=0.0, **kwargs):
        r"""Solve the linear elasticity problem.

        .. math::
            f = \rho*\boldsymbol{g}

        Attributes
        ----------
        f: f in R3
            Force vector.

        rho: float
            Density in kg/m³. :math:`\boldsymbol{g}` is addeded with
            :math:`g_z=9.81` m/s².

        Keyword Arguments
        -----------------
        p: int[2]
            Polynomial order of the finite element space.
        order: int[3]
            Order of integration for assembling.
            Default is 3, but can be set to 2 for faster assembling.
        """
        g = 9.81
        self.space = None
        v = None
        order = kwargs.pop('order', self._order)
        p = kwargs.pop('p', self._p)

        if self.var == 1:  # with anisotropic constitutive matrix

            if isinstance(self.C, dict):
                C = [self.C[m] for m in self.mesh.cellMarkers()]
            else:
                C = self.C

            v = VectorSpace(self.mesh, p=p, order=order, name='u', elastic=True)

            v.voigt = self.voigtNotation

            # def _simga(v): ## test with such formulation, refactor!
            #     return C*eps(v)

            #self.L = grad(v) * C * self.eps(v) # should be!! TEST!!
            self.L = grad(v) * C * grad(v) # tests OK for isotropic cases

        elif self.var == 2: # isotropic formulation

            if isinstance(self.lam, dict):
                lam = np.array([self.lam[m] for m in self.mesh.cellMarkers()])
                mu = np.array([self.mu[m] for m in self.mesh.cellMarkers()])
            else:
                lam = self.lam
                mu = self.mu

            v = VectorSpace(self.mesh, p=p, order=order, name='u')
            self.space = v

            self.L = grad(v) * self.sigma(v, lam=lam, mu=mu)

        if self.mesh.dim() == 2:
            vRhoG = [0., -rho*g]

        elif self.mesh.dim() == 3:
            vRhoG = [0., 0.0, -rho*g]

        self.R = None
        # self.R = 0 -- then add += rest

        if rho != 0.0:
            self.R = v * vRhoG

        if f is not None:
            #self.R = grad(v) * f  ## for f is stress
            if self.R is None:
                self.R = v * f       ## for f is div(stress)
            else:
                self.R += v * f

        ##!!pg.warning('check order in LinearElasticSolver._assemble')
        self._applyBC(bc={v:self.bc})
        #needed?
        self.space = v
        u = v.split(self.vU)

        u.solver = self
        u.strain = lambda *args, **kwargs : u.solver.strain(u, *args, **kwargs)
        u.stress = lambda *args, **kwargs: u.solver.stress(u, *args, **kwargs)

        return u


def solveLinearElasticity(mesh, lam=None, mu=None, E=None, nu=None,
                          bc={}, rho=0.0, f=None, var=1, verbose=False, **kwargs):
    r"""One-liner to solve the linear elastic problem.

    See :pymod:`oskar.processes.LinearElasticSolver`
    """
    solver = LinearElasticitySolver(mesh, lam=lam, mu=mu, E=E, nu=nu,
                                    bc=bc, var=var, verbose=verbose, **kwargs)
    ret = solver.solve(rho=rho, f=f)

    return ret


class ThermoElasticitySolver(FEASolver):
    r"""Solver for coupled thermoelasticity problems."""

    def __init__(self, mesh, lam, mu, alpha, K, c, rho, T0=0.0, **kwargs):
        r"""Finite element approximation of thermoelastic coupled problems.

        Solves for temperature :math:`T`, and displacement
        :math:`\boldsymbol{u}`:

        .. math::

            \rho c \partial_t T
            - \nabla\cdot(K\nabla T - \alpha T \nabla\cdot\boldsymbol{u})
            =\:& 0 \quad~\text{in}\quad\Omega \\[10pt]
            -\nabla\cdot\left(\lambda\operatorname{tr}(\boldsymbol{\epsilon})\,\mathbf{I} + 2\mu\boldsymbol{\epsilon}
                          - \alpha T\,\mathbf{I}\right)
            =\:& 0 \quad~\text{in}\quad\Omega

        with the small linear elastic strain tensor:

        .. math::

            \boldsymbol{\epsilon} = \frac{1}{2}(\nabla\boldsymbol{u} + (\nabla\boldsymbol{u})^{\rm T})

        =============================== ================================== ========================================
        Symbol                          Description                        Dimension
        =============================== ================================== ========================================
        :math:`T`                       temperature                        :math:`\mathsf{T}`
        :math:`\rho`                    density                            :math:`\mathsf{M}\cdot\mathsf{L}^{-3}`
        :math:`c`                       specific heat capacity             :math:`\mathsf{M}\cdot\mathsf{L}^{-2}\cdot\mathsf{T}^{-1}`
        :math:`K`                       thermal conductivity               :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-3}\cdot\mathsf{\Theta}^{-1}`
        :math:`\alpha`                  thermal expansion coefficient      :math:`\mathsf{\Theta}^{-1}`
        :math:`\lambda`                 Lamé's first parameter             :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`
        :math:`\mu`                     Lamé's second parameter            :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`\boldsymbol{\epsilon}`   strain tensor                      :math:`\mathsf{1}`
        :math:`\mathbf{I}`              identity tensor                    :math:`\mathsf{1}`
        =============================== ================================== ========================================
        """
        super().__init__(mesh, **kwargs)

        self.name = 'ThermoElasticity'

        self.lam = lam
        """Lamé's first parameter"""

        self.mu = mu
        """Lamé's second parameter"""

        self.alpha = alpha
        """thermal expansion coefficient"""

        self.K = K
        """thermal conductivity"""

        self.c = c
        """specific heat capacity"""

        self.rho = rho
        """density"""

        self.T0 = T0
        """Initial temperature"""

        self.u = VectorSpace(mesh, p=1, name='u')
        """Finite element space for displacement."""

        self.T = ScalarSpace(mesh, p=1, name='T')
        """Finite element space for temperature."""

        self.dirichlet = DirichletManager({self.u: self.bc, self.T: self.bc})


    def solve(self, times, **kwargs):
        """Solve the coupled thermoelasticity problem for
        given time steps.

        Arguments
        ---------
        times: iterable of float
            Time steps to solve for.

        Returns
        -------
        T, u: FEASolution, FEASolution
            Temperature and displacement solutions.
        """
        with self.tictoc('ThermoElasticity/solve'):
            pass
            NotImplemented


def solveThermoElasticity(mesh, times, **kwargs):
    """ Shortcut to solve the coupled thermoelasticity problem.

    See :pymod:`oskar.processes.ThermoElasticitySolver`
    """
    solver = ThermoElasticitySolver(mesh, **kwargs)
    return solver.solve(times)


class PoroElasticitySolver(FEASolver):
    r"""Solver for coupled PoroElasticity problems.
    """
    def __init__(self, mesh, K, lam, mu, Ss=0, alphaB=1.0, **kwargs):
        r"""
        Finite element approximation of poroelastic coupled
        problems.
        Solves for pore water pressure :math:`p`, and displacement
        :math:`\boldsymbol{u}`:

        .. math::

            S_{\rm s} \partial_t p
                + \nabla\cdot(- K \nabla p + \alpha_{\rm B}\partial_t\boldsymbol{u})
                =\:& 0 \quad~\text{in}\quad\Omega \\[10pt]
            -\nabla\cdot\left(\lambda\operatorname{tr}(\boldsymbol{\epsilon})\,\mathbf{I} + 2\mu\boldsymbol{\epsilon}
                          - \alpha_{\rm B}p\,\mathbf{I}\right)
                =\:& 0 \quad~\text{in}\quad\Omega \\[10pt]

        with the small linear elastic strain tensor:

        .. math::

            \boldsymbol{\epsilon} = \frac{1}{2}(\nabla\boldsymbol{u} + (\nabla\boldsymbol{u})^{\rm T})


        =============================== ================================== ========================================
        Symbol                          Description                        Dimension
        =============================== ================================== ========================================
        :math:`p`                       pore water pressure                :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`S_{\rm s}`               specific storage coefficient       :math:`\mathsf{L}^{-1}`
        :math:`K`                       hydraulic conductivity             :math:`\mathsf{L}\cdot\mathsf{T}^{-1}`
        :math:`\boldsymbol{u}`          displacement                       :math:`\mathsf{L}`
        :math:`\alpha_{\rm B}`          Biot-Willis coefficient            :math:`\mathsf{1}`
        :math:`\lambda`                 Lamé's first parameter             :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`\mu`                     Lamé's second parameter            :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`\boldsymbol{\epsilon}`   strain tensor                      :math:`\mathsf{1}`
        :math:`\mathbf{I}`              identity tensor                    :math:`\mathsf{1}`
        =============================== ================================== ========================================

        Arguments
        ---------
        mesh: pg.Mesh
            Mesh for the domain :math:`\Omega`.
        K: FEAFunction | float
            Hydraulic conductivity.
        alpha_B: float(1)
            Biot-Willis coefficient.
        S_s: float(0)
            Specific storage coefficient.
        lam: FEAFunction | float
            Lamé's first parameter.
        mu: FEAFunction | float
            Lamé's second parameter.

        Keyword Args
        ------------
        p: int[1]
            Polynomial degree of the solution space.
        bcP: dict
            Boundary conditions for pressure.
            See :ref:`userguide-fea-bc-dict`.
        bcU: dict
            Boundary conditions for displacement.
            See :ref:`userguide-fea-bc-dict`.
        var: int[2]
            Variant of the solver implementation.
            1: solve with expression (for debugging, better readable)
            2: solve algebraic with matrices (faster)
        """
        super().__init__(mesh, **kwargs)
        self.name = 'PoroElasticity'

        self.useTHM = False
        if self.useTHM:
            self._thm = ThermoPoroElasticitySolver(mesh,
                                                cv=0, kappa=0, K=K,
                                                lam=lam, mu=mu, betaV=0, Ku=0,
                                                Ss=Ss, alphaB=alphaB, **kwargs)
            self._thm.name = self.name
            return

        self._p = kwargs.pop('p', 1)
        """Polynomial degree of the solution space."""

        self.K = K
        """hydraulic conductivity"""

        self.lam = lam
        """Lamé's first parameter"""

        self.mu = mu
        """Lamé's second parameter"""

        self.Ss = Ss
        """specific storage coefficient"""

        self.alphaB = alphaB
        """Biot-Willis coefficient"""

        self.bcP = kwargs.pop('bcP', {})
        """Boundary conditions for pressure."""

        self.bcU = kwargs.pop('bcU', {})
        """Boundary conditions for displacement."""

        self.p = ScalarSpace(mesh, p=self._p, order=3, name='p')
        """Finite element space for pore water pressure."""

        self.u = VectorSpace(mesh, p=self._p, order=3,
                             name='u', dofOffset=self.p.dof)
        """Finite element space for displacement."""

        self.var = kwargs.pop('var', 2)
        """Variant of the solver implementation."""

        self.p.solver = self
        self.u.solver = self

        self.bc = {self.p: self.bcP,
                   self.u: self.bcU}
        self.dirichlet = DirichletManager(self.bc)


    def solve(self, times, **kwargs):
        """Solve the coupled poroelasticity problem for
        given time steps.

        Arguments
        ---------
        times: iterable of float
            Time steps to solve for.

        Returns
        -------
        p, u: FEASolution
            FEASolution instances of the sought pressure and displacement.
        """

        if self.useTHM:
            th, ph, uh = self._thm.solve(times, **kwargs)
            return ph, uh

        ## TODO : remove me or use this HM part in THM
        t = times

        p = self.p
        u = self.u

        icP = kwargs.pop('icP', 0.0)
        icU = kwargs.pop('icU', 0.0)

        ph = ensureInitialSolution(icP, space=p)
        uh = ensureInitialSolution(icU, space=u)

        # ph = FEASolution(p, values=0)
        # uh = FEASolution(u, values=0)

        P = pg.utils.ProgressBar(len(t)-1)

        def eps(u):
            return sym(grad(u))

        asKW = self.assembleOptions

        with pg.tictoc(f'{self.name}/solve'):

            for i, ti in enumerate(t[1:]):
                asKW['time'] = ti
                P(i)
                dt = t[i+1] - t[i]

                if self.var == 1:

                    Lp = p*self.Ss*(p-ph) \
                        + grad(p)*dt*(self.K*grad(p)) \
                        + p*self.alphaB*div(u) \
                        == p*self.alphaB*div(uh)

                    Lu = -grad(u)*(self.lam*tr(eps(u))*I(u) + 2.0*self.mu*eps(u)) \
                        + div(u)*self.alphaB*p == 0

                    ph, uh = solve([Lp, Lu],
                                    bc={p:self.bcP, u:self.bcU},
                                    **asKW, solver='scipy')

                else:

                    ## matrix version
                    if i == 0:
                        with pg.tictoc('iter 0'):

                            AP = (grad(p)*(self.K * grad(p))).assemble(**asKW)

                            if self.Ss != 0.0:
                                MPP = (p*self.Ss*p).assemble(**asKW)

                            MPU = (p*self.alphaB*div(u)).assemble(**asKW)

                            AU = (-grad(u)*(2*self.mu*eps(u) + self.lam*tr(eps(u))*I(u))).assemble(**asKW)
                            MUP = (div(u)*self.alphaB*p).assemble(**asKW)

                    with pg.tictoc('assemble rhs'):

                        if self.Ss != 0.0:
                            RP = (p*self.Ss*(ph)).assemble(**asKW)

                        RPU = (p*self.alphaB*div(uh)).assemble(**asKW)

                    with pg.tictoc('sum lhs'):
                        if self.Ss != 0.0:
                            # SP = AP*dt + MPP + MPU
                            SP = pg.matrix.concatenateAsCOO([AP*dt + MPP, MPU])
                        else:
                            # SP = AP*dt + MPU
                            SP = pg.matrix.concatenateAsCOO([AP*dt, MPU])

                        SU = pg.matrix.concatenateAsCOO([AU, MUP])
                        #SU = AU + MUP
                        S = pg.matrix.concatenateAsCOO([SP, SU])
                        #S = ST + SP - SU
                        S = pg.matrix.asSparseMatrix(S)

                    with pg.tictoc('sum b'):
                        b = pg.Vector(S.shape[0], 0.0)

                        if self.Ss != 0.0:
                            b += RP

                        b += RPU

                    with pg.tictoc('bc'):
                        applyRHSBoundaryConditions(self.bc, b)
                        self.dirichlet.apply(S, b)

                    with pg.tictoc('linSolve'):
                        x = linSolve(S, b, solver='scipy')

                    ph,uh = (p*u).split(x, time=ti)

        return ph, uh


def solvePoroElasticity(mesh, times, K, lam, mu, **kwargs):
    """ Shortcut to solve the coupled poroelasticity problem.

    See :pymod:`oskar.processes.PoroElasticitySolver`
    """
    solver = PoroElasticitySolver(mesh, K, lam, mu, **kwargs)
    return solver.solve(times, **kwargs)


class ThermoPoroElasticitySolver(FEASolver):
    r"""Solver for coupled Thermo-Hydro-Mechanical problems.
    """
    def __init__(self, mesh, cv, kappa, K, lam, mu, betaV, Ku,
                 Ss=0, alphaB=1.0, **kwargs):
        r"""
        Finite element approximation of thermo-hydro-mechanical coupled
        problems.
        Solves for temperature :math:`T`, pressure :math:`p`, and displacement
        :math:`\boldsymbol{u}`:

        .. math::

            c_{\rm v} \partial_t T
                - \nabla\cdot(\kappa \nabla T)
                =\:& H_{\rm v} \quad~\text{in}\quad\Omega \\[10pt]
            S_{\rm s} \partial_t p
                - \beta_{\rm v} \partial_t T
                + \nabla\cdot(- K \nabla p + \alpha_{\rm B}\partial_t\boldsymbol{u})
                =\:& 0 \quad~\text{in}\quad\Omega \\[10pt]
            -\nabla\cdot\left(\lambda\operatorname{tr}(\boldsymbol{\epsilon})\,\mathbf{I} + 2\mu\boldsymbol{\epsilon}
                          - K_u \beta_{\rm v} T\,\mathbf{I}
                          - \alpha_{\rm B}p\,\mathbf{I}\right)
                =\:& 0 \quad~\text{in}\quad\Omega \\[10pt]

        with the small linear elastic strain tensor:

        .. math::

            \boldsymbol{\epsilon} = \frac{1}{2}(\nabla\boldsymbol{u} + (\nabla\boldsymbol{u})^{\rm T})


        =============================== ================================== ========================================
        Symbol                          Description                        Dimension
        =============================== ================================== ========================================
        :math:`T`                       temperature                        :math:`\mathsf{\Theta}`
        :math:`\rho`                    mass density                       :math:`\mathsf{M}\cdot\mathsf{L}^{-3}`
        :math:`c_{\rm v}`               volumetric heat capacity           :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{\Theta}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`\kappa`                  thermal conductivity               :math:`\mathsf{M}\cdot\mathsf{L}\cdot\mathsf{\Theta}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`H_{\rm v}`               volumetric heat source             :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-3}`
        :math:`p`                       pore water pressure                :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`S_{\rm s}`               specific storage coefficient       :math:`\mathsf{L}^{-1}`
        :math:`K`                       hydraulic conductivity             :math:`\mathsf{L}\cdot\mathsf{T}^{-1}`
        :math:`\beta_{\rm v}`           volumetric thermal expansion       :math:`\mathsf{\Theta}^{-1}`
        :math:`\alpha_{\rm B}`          Biot-Willis coefficient            :math:`\mathsf{1}`
        :math:`\boldsymbol{u}`          displacement                       :math:`\mathsf{L}`
        :math:`\lambda`                 Lamé's first parameter             :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`\mu`                     Lamé's second parameter            :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`K_u`                     bulk modulus                       :math:`\mathsf{M}\cdot\mathsf{L}^{-1}\cdot\mathsf{T}^{-2}`
        :math:`\boldsymbol{\epsilon}`   strain tensor                      :math:`\mathsf{1}`
        :math:`\mathbf{I}`              identity tensor                    :math:`\mathsf{1}`
        =============================== ================================== ========================================

        Solves with T-PU scheme, i.e., solves temperature at first single step
        and then solves the pressure-displacement combined.

        TODO
        ----
            * Add advection term for energy balance equation. Needs a test case.

        Arguments
        ---------
        mesh: pg.Mesh
            Mesh for :math:`\Omega` to solve for.
        cv: FEAFunction | float
            Volumetric heat capacity.
        kappa: FEAFunction | float
            Thermal conductivity.
        K: FEAFunction | float
            Hydraulic conductivity.
        alphaB: float(1)
            Biot-Willis coefficient.
        Ss: float(0)
            Specific storage coefficient.
        lam: FEAFunction | float
            Lamé's first parameter.
        mu: FEAFunction | float
            Lamé's second parameter.
        betaV: FEAFunction | float
            Volumetric thermal expansion.
        Ku: FEAFunction | float
            Bulk modulus.

        Keyword Args
        ------------
        p: int[1]
            Polynomial degree of the solution space.
        bcT: dict
            Boundary conditions for temperature.
            See :ref:`userguide-fea-bc-dict`.
        bcP: dict
            Boundary conditions for pressure.
            See :ref:`userguide-fea-bc-dict`.
        bcU: dict
            Boundary conditions for displacement.
            See :ref:`userguide-fea-bc-dict`.
        var: int[2]
            Variant of the solver implementation.
            1: solve with expression (for debugging, better readable)
            2: solve algebraic with matrices (faster)
        """
        super().__init__(mesh, **kwargs)
        self.name = 'ThermoPoroElasticity'

        self._p = kwargs.pop('p', 1)
        """Polynomial degree of the solution space."""

        self.cv = cv
        """Volumetric heat capacity."""

        self.kappa = kappa
        """Thermal conductivity."""

        self.K = K
        """Hydraulic conductivity."""

        self.Ss = Ss
        """Specific storage coefficient."""

        self.alphaB = alphaB
        """Biot-Willis coefficient."""

        self.lam = lam
        """Lamé's first parameter."""

        self.mu = mu
        """Lamé's second parameter."""

        self.betaV = betaV
        """Volumetric thermal expansion."""

        self.Ku = Ku
        """Bulk modulus."""

        self.bcT = kwargs.pop('bcT', {})
        """Boundary conditions for temperature."""

        self.bcP = kwargs.pop('bcP', {})
        """Boundary conditions for pressure."""

        self.bcU = kwargs.pop('bcU', {})
        """Boundary conditions for displacement."""

        self.var = kwargs.pop('var', 2)
        """Variant of the solver implementation."""

        self.T = ScalarSpace(self.mesh, p=self._p, order=3)
        """Temperature FEASpace."""

        self.p = ScalarSpace(self.mesh, p=self._p, order=3)
        """Pressure FEASpace."""
        self.u = VectorSpace(self.mesh, p=self._p, order=3,
                             dofOffset=self.p.dofs.stop)
        """Displacement FEASpace."""

        self.T.solver = self
        self.p.solver = self
        self.u.solver = self

        self.dirichlet = DirichletManager({self.p: self.bcP,
                                           self.u: self.bcU})
        """Dirichlet boundary conditions manager."""


    def solve(self, times, Hv=0, **kwargs):
        """Solve the coupled thermo-hydro-mechanical problem for
        given time steps.

        Arguments
        ---------
        times: iterable of float
            Time steps to solve for.
        Hv: FEAFunction | FEAOperator
            Volumetric heat source.

        Keyword Args
        ------------
        icT: FEAFunction | FEAOperator | float[0]
            Initial condition for temperature.
        icP: FEAFunction | FEAOperator | float[0]
            Initial condition for pressure.
        icU: FEAFunction | FEAOperator | float[0]
            Initial condition for displacement.

        Returns
        -------
        T, p, u: FEASolution
            FEASolution instances of the sought temperature, pressure,
            and displacement.
        """
        t = times

        T = self.T
        p = self.p
        u = self.u

        icT = kwargs.pop('icT', 0)
        icP = kwargs.pop('icP', 0)
        icU = kwargs.pop('icU', 0)
        th = ensureInitialSolution(icT, space=T)
        ph = ensureInitialSolution(icP, space=p)
        uh = ensureInitialSolution(icU, space=u)

        P = pg.utils.ProgressBar(len(t)-1)

        def eps(u):
            return sym(grad(u))

        asKW = dict(self.assembleOptions)

        with pg.tictoc(f'{self.name}/solve'):

            for i, ti in enumerate(t[1:]):
                asKW['time'] = ti

                P(i)
                dt = t[i+1] - t[i]

                if i == 0:
                    if self.kappa != 0:
                        th = solve(  self.cv*derive(T, 't') \
                                    - div(self.kappa* grad(T)) == Hv,
                                    bc=self.bcT, ic=th, times=t,
                                    **self.assembleOptions, solver='scipy')

                if self.kappa != 0:
                    dT = ScalarSpace(T.mesh, p=T.p, order=3)
                    dth = FEASolution(dT, values=th(p.mesh, t=ti)\
                                    - th(p.mesh, t=ti-dt))

                if self.var == 1:

                    Lp = p * self.Ss*(p-ph) \
                       + grad(p) * dt*(self.K*grad(p)) \
                       + p * self.alphaB*div(u) \
                       == p * self.alphaB*div(uh)

                    Lu = -grad(u)*(2*self.mu*eps(u) + self.lam*tr(eps(u))*I(u))\
                        + div(u)*self.alphaB*p \
                        == 0

                    if self.kappa != 0:
                        # add them on the left side
                        Lp -= p * self.betaV*dth
                        Lu -= -grad(u)*self.Ku*th

                    ph, uh = solve([Lp, Lu], bc={p:self.bcP, u:self.bcU},
                                   **asKW, solver='scipy')

                else:

                    ## matrix version
                    if i == 0:
                        with pg.tictoc('iter 0'):

                            AP = (grad(p)*(self.K * grad(p))).assemble(**asKW)

                            if self.Ss != 0.0:
                                MPP = (p*self.Ss*p).assemble(**asKW)

                            MPU = (p*self.alphaB*div(u)).assemble(**asKW)

                            AU = (-grad(u)*(2*self.mu*eps(u) + self.lam*tr(eps(u))*I(u))).assemble(**asKW)
                            MUP = (div(u)*self.alphaB*p).assemble(**asKW)

                    with pg.tictoc('assemble rhs'):

                        if self.Ss != 0.0:
                            RP = (p*self.Ss*(ph)).assemble(**asKW)

                        RPU = (p*self.alphaB*div(uh)).assemble(**asKW)

                        if self.kappa != 0.0:
                            RPT = (p*self.betaV*dth).assemble(**asKW)
                            RUT = (grad(u)*self.Ku*th).assemble(**asKW)

                    with pg.tictoc('sum lhs'):
                        #SP = AP + MPP/dt - MPT/dt + MPU/dt
                        if self.Ss != 0.0:
                            # SP = AP*dt + MPP + MPU
                            SP = pg.matrix.concatenateAsCOO([AP*dt + MPP, MPU])
                        else:
                            # SP = AP*dt + MPU
                            SP = pg.matrix.concatenateAsCOO([AP*dt, MPU])

                        SU = pg.matrix.concatenateAsCOO([AU, MUP])
                        #SU = AU + MUP
                        S = pg.matrix.concatenateAsCOO([SP, SU])
                        S = pg.matrix.asSparseMatrix(S)

                    with pg.tictoc('sum b'):
                        b = pg.Vector(S.shape[0], 0.0)

                        b += RPU

                        if self.Ss != 0.0:
                            b += RP

                        if self.kappa != 0.0:
                            b += RPT
                            b -= RUT

                    with pg.tictoc('bc'):
                        applyRHSBoundaryConditions({p:self.bcP, u:self.bcU}, b)
                        self.dirichlet.apply(S, b)

                    with pg.tictoc('linSolve'):
                        x = linSolve(S, b, solver='scipy')

                    ph,uh = (p*u).split(x, time=ti)

        return th, ph, uh


def solveThermoPoroElasticity(mesh, times, Hv=0, **kwargs):
    """ Shortcut to solve coupled thermo-hydro-mechanical problems."

    See :pymod:`oskar.processes.ThermoPoroElasticitySolver`
    """
    solver = ThermoPoroElasticitySolver(mesh, **kwargs)
    return solver.solve(times, Hv=Hv, **kwargs)