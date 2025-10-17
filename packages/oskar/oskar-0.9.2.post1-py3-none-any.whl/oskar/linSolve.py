#!/usr/bin/env python
"""Proxy class for linear solvers.

TODO
----
* Refactor lineSolve

"""
import sys
import numpy as np

import pygimli as pg


def cg(A, b, x, imax=50, eps=1e-6):
    """Conjugate Gradient reference solver.

    from petsc4py/demo/legacy/kspsolve/petsc-cg.py

    A, b, x  : matrix, rhs, solution
    imax     : maximum allowed iterations
    eps      : tolerance for convergence
    """
    # allocate work vectors
    r = b.duplicate()
    d = b.duplicate()
    q = b.duplicate()
    # initialization
    i = 0
    A.mult(x, r)
    r.aypx(-1, b)
    r.copy(d)
    delta_0 = r.dot(r)
    delta = delta_0
    # enter iteration loop
    while i < imax and \
          delta > delta_0 * eps**2:
        A.mult(d, q)
        alpha = delta / d.dot(q)
        x.axpy(+alpha, d)
        r.axpy(-alpha, q)
        delta_old = delta
        delta = r.dot(r)
        beta = delta / delta_old
        d.aypx(beta, r)
        i = i + 1
    return i, delta**0.5


def _splitMatrix(A, nA=0):
    """Split block matrix into four single blocks.
    """
    _A, _B, _C, _D = [None]*4

    if isinstance(A, list) and len(A) == 2:
        _A = A[0]
        _B = A[1]
        _C = _B.T
    elif isinstance(A, list) and len(A) == 3:
        _A = A[0]
        _B = A[1]
        _C = _B.T
        _D = A[2]
        pg.critical('implement me')
    elif isinstance(A, list) and len(A) == 4:
        _A = A[0]
        _B = A[1]
        _C = A[2]
        _D = A[3]
        pg.critical('implement me')
    elif isinstance(A, pg.core.RBlockMatrix):
        for e in A.entries():
            # print(e.rowStart, e.colStart, A.matRef(e.matrixID),
            #         e.scale, e.transpose )

            if e.scale != 1.0 or e.transpose is True:
                print(e.rowStart, e.colStart, A.matRef(e.matrixID),
                        e.scale, e.transpose )
                pg.critical('implement me')
                # print(type(self._A))
            if e.rowStart == 0 and e.colStart == 0:
                _A = pg.matrix.asCSR(A.matRef(e.matrixID))

            elif e.rowStart == 0 and e.colStart == _A.shape[1]:
                _B = pg.matrix.asCSR(A.matRef(e.matrixID))

            elif e.rowStart == _A.shape[0] and e.colStart == 0:
                _C = pg.matrix.asCSR(A.matRef(e.matrixID))
            elif e.rowStart == _A.shape[0] and e.colStart == _A.shape[1]:
                _D = pg.matrix.asCSR(A.matRef(e.matrixID))

            else:
                print(e.rowStart, e.colStart, A.matRef(e.matrixID))
                print(A)
                pg.critical('implement me')
    else:
        #print(self.nV, A)
        if nA > 0:
            _A = A[:nA, :nA]
            _B = A[:nA, nA:]
            _C = _B.T
        else:
            pg.critical("For schur type wrapper we need either list ",
                    "of matrices or block matrix")
    return _A, _B, _C, _D


class SolverWrapper(pg.core.SolverWrapper):
    """Abstract interface for linear solvers."""
    def __init__(self, A=None, **kwargs):

        self._iterCounter = 0
        self._b = None
        self._res = []
        self.rtol = float(kwargs.pop('rtol', kwargs.get('tol', 5e-8)))
        self.type = kwargs.pop('type', None)
        self.pc = kwargs.pop('pc', None)        ## PreConditioner type
        self.P = kwargs.pop('P', None)      ## PreConditioner Matrix
        self.verbose = kwargs.pop('verbose', False)
        self.tSolve = 0
        self.tSetup = 0
        self.kwargs = kwargs
        self._factorized = False
        self._testSetup = kwargs.pop('test', False)
        super().__init__()

        if A is not None:
            self(A, verbose=self.verbose, **kwargs)


    def __call__(self, A, verbose=False, **kwargs):
        """ Call the solver wrapper to setup a new matrix.
        """
        self.kwargs.update(kwargs)
        self.verbose = verbose
        self._AIn = A
        self.setup(**self.kwargs)
        return self


    def setup(self, **kwargs):
        """ Abstract interface to setup a linear solver.
        """
        pass


class PetscWrapper(SolverWrapper):
    """ Wrapper for PETSc linear solvers."""
    def __init__(self, A=None, **kwargs):
        super().__init__(A, **kwargs)


    def setup(self, **kwargs):
        """Setup the PETSc solver.
        """
        from mpi4py import MPI
        from petsc4py import PETSc

        self._ksp = PETSc.KSP().create(PETSc.COMM_WORLD)

        def _toPetsc(A):
            if A is not None:
                A = pg.matrix.asCSR(A)
                return PETSc.Mat().createAIJ(size=A.shape,
                                         csr=(A.indptr, A.indices,
                                              np.round(A.data, 14)))
            return A

        if self.type is None:
            self.type = 'preonly'

        self.verbose=True
        if self.verbose:
            pg.info(f'Petsc ksp type: {self.type}')

        self._ksp.setType(self.type)

        if isinstance(self.pc, list):
            # use fieldsplit
            #multiple PreConditioner .. so we want fieldsplit

            A, B, C, D = _splitMatrix(self._AIn)

            if self.verbose:
                pg.info(f"A ({type(A)}): {A.shape}")
                pg.info(f"B ({type(B)}): {B.shape}")
                pg.info(f"C ({type(C)}): {C.shape}")
            try:
                pg.info(f"D ({type(D)}): {D.shape}")
            except:
                pass
            A = _toPetsc(A)
            B = _toPetsc(B)
            C = _toPetsc(C)
            D = _toPetsc(D)

            self._A = PETSc.Mat().createNest([[A, B], [C, D]])

            if self.P is None:
                self.P = []*len(self.pc)

            if self._testSetup is True:
                return self.testSetup()

            if isinstance(self.P, list):
                self._ksp.getPC().setType("fieldsplit")

                P0 = _toPetsc(self.P[0])
                P1 = _toPetsc(self.P[1])

                if P0 is None:
                    P0 = A

                if self.verbose:
                    try:
                        pg.info(f"P[0,0] ({type(self.P[0])}): "
                                f" {self.P[0].shape}")
                    except:
                        pass
                    try:
                        pg.info(f"P[1,1] ({type(self.P[1])}): "
                                f"{self.P[1].shape}")
                    except:
                        pass

                self._P = PETSc.Mat().createNest([[P0, None], [None, P1]])

                nIS = self._P.getNestISs()
                self._ksp.getPC().setFieldSplitIS(("1", nIS[0][0]),
                                                  ("2", nIS[0][1]))

                ksp_ = self._ksp.getPC().getFieldSplitSubKSP()
                for i, pc in enumerate(self.pc):

                    def _set_pc_o(ksp, t):
                        pc = t.split('[')
                        ksp.setType(pc[0])

                        if len(pc) > 1:
                            vals = pc[1].split(']')[0].split(',')
                            for p in vals:
                                kv = p.split('=')
                                #setattr(ksp, kv[0], int(kv[1]))


                    typ = pc.split('|')
                    if len(typ) == 1:
                        if self.verbose:
                            pg.info(f'Petsc PreConditioner {i}: '
                                    f'preonly|{typ[0]}')

                        ksp_[i].setType("preonly")
                        ksp_[i].getPC().setType(typ[0])
                    elif len(typ) == 2:
                        if self.verbose:
                            pg.info(f'Petsc PreConditioner {i}: '
                                    f'{typ[0]}|{typ[1]}')

                        _set_pc_o(ksp_[i], typ[0])
                        # try:
                        #     ksp_[i].setType(typ[0])
                        #     ksp_[i].getPC().setType(typ[1])
                        # except:
                        #     ksp_[i].setType("richardson")
                        #     ksp_[i].max_it = 1
                        #     ksp_[i].getPC().setType("none")

                    else:
                        print(typ)
                        pg.critical('PreConditioner unknown')

                fieldsplit = kwargs.pop('fs', 'add')
                if self.verbose:
                    pg.info(f'Petsc PreConditioner fieldsplit type: '
                            f' {fieldsplit}')

                if fieldsplit == 'schur':
                    self._ksp.getPC().setFieldSplitType(
                                                PETSc.PC.CompositeType.SCHUR)
                    fact = kwargs.pop('fact', None)
                    if self.verbose:
                        pg.info(f'Petsc PreConditioner fieldsplit schur '
                                f'factorization type: {fact}')

                    if fact == 'diag':
                        self._ksp.getPC().setFieldSplitSchurFactType(
                                                PETSc.PC.SchurFactType.DIAG)
                    elif fact == 'upper':
                        self._P = PETSc.Mat().createNest([[P0, B], [None, P1]])
                        self._ksp.getPC().setFieldSplitSchurFactType(
                                                PETSc.PC.SchurFactType.UPPER)
                    else:
                        print(fact)
                        pg.critical('implement me')
                elif fieldsplit == 'mult':
                    self._ksp.getPC().setFieldSplitType(
                                        PETSc.PC.CompositeType.MULTIPLICATIVE)
                elif fieldsplit == 'add':
                    self._ksp.getPC().setFieldSplitType(
                                        PETSc.PC.CompositeType.ADDITIVE)
                else:
                    print(fieldsplit)
                    pg.critical('implement me')

                pg.tic(key='PetscWrapper.setup')

                self._ksp.setOperators(self._A, self._P)
                #self._ksp.setOperators(self._A, self._A)

            else:

                pg.tic(key='PetscWrapper.setup')
                self._ksp.setOperators(self._A)

        else:
            self._A = _toPetsc(self._AIn)

            pg.tic(key='PetscWrapper.setup')
            self._ksp.setOperators(self._A)


            if self.type == 'preonly' and self.pc is None:
                self._ksp.getPC().setType('lu')
            else:
                if self.pc is None or self.pc == '':
                    self._ksp.getPC().setType('none')
                else:
                    self._ksp.getPC().setType(self.pc)

        self.tSetup = pg.dur(key='PetscWrapper.setup')


    def testSetup(self):
        """Temporary test setup for the Schur complement solver.
        """
        # from amg cl cpp compare!
        from mpi4py import MPI
        from petsc4py import PETSc

        pg.tic(key='PetscWrapper.setup')

        ksp = self._ksp
        A_ = self._A
        ksp.setType("bcgsl")
        ksp.setTolerances(rtol=1e-12)

        #P_ = PETSc.Mat().createNest([[A, B], [None, P]])
        ksp.setOperators(A_, A_)

        nested_IS = A_.getNestISs()
        ksp.getPC().setType("fieldsplit")
        ksp.getPC().setFieldSplitIS(("0", nested_IS[0][0]),
                                    ("1", nested_IS[0][1]))

        ksp_ = ksp.getPC().getFieldSplitSubKSP()
        ksp_[0].setType("preonly")
        ksp_[0].getPC().setType("gamg")
        ksp_[0].rtol = 1e-12
        ksp_[1].setType("preonly")
        ksp_[1].getPC().setType("jacobi")
        ksp_[1].rtol = 1e-12

        ksp.getPC().setFieldSplitType(PETSc.PC.CompositeType.SCHUR)
        ksp.getPC().setFieldSplitSchurPreType(PETSc.PC.SchurPreType.SELFP)
        ksp.getPC().setFieldSplitSchurFactType(PETSc.PC.SchurFactType.LOWER)

        self.tSetup = pg.dur(key='PetscWrapper.setup')


    def solve(self, b):
        r""" Solve the factorized system
            :math:`\textbf{A}\textbf{x} = \textbf{b}` for :math:`x`.
        """
        self._b = b
        x_, b_ = self._A.createVecs()
        x_.set(0)
        b_.array[:] = b

        self._ksp.rtol = self.rtol
        self._ksp.atol = 0
        self._ksp.max_it = len(b)*100

        # set ksp from command line options to overwrite local settings
        self._ksp.setFromOptions()
        self._ksp.solve(b_, x_)

        self._iterCounter = self._ksp.its

        # bNorm = np.linalg.norm(b)
        # res = np.linalg.norm(self._A * x_ - b_)
        # pg._r(f"res={res} tol={self.rtol} res={res} b={bNorm}, rres={res/bNorm}")

        # its, norm = cg(self._A, b_, x_, 10000, self.rtol)
        # print("iterations: %d residual norm: %g" % (its, norm))

        return x_.array


class ScipyWrapper(SolverWrapper):
    """Wrapper for SciPy sparse linear solvers."""

    def __init__(self, A=None, **kwargs):
        self._ksp = None
        super().__init__(A, **kwargs)
        self._progress = None


    def setup(self, **kwargs):
        """Set up the SciPy solver."""
        import scipy.sparse
        from scipy.sparse.linalg import factorized

        if isinstance(self._AIn, scipy.sparse.linalg.LinearOperator):
            self._A = self._AIn
        else:
            self._A = pg.matrix.asCSC(self._AIn)

        pg.tic(key='ScipyWrapper.setup')
        # pg._y(self.type, ':' , self.pc)

        if self.type is None:
            self._direct = factorized(self._A)
        else:
            self._ksp = getattr(scipy.sparse.linalg, self.type)

            # pg._b(self._ksp, ':' , self.pc, ':', kwargs, ':', type(self.P))
            self._P = None

            if self.pc is not None and self.pc != '':

                P = kwargs.pop('P', None)
                if P is None:
                    ## local for global
                    P = self.P

                if P is None:
                    P = self._A

                # pg._g(self.pc, type(P), P.shape)

                if self.pc == 'cholmod':

                    cholmod = LinSolver(P)
                    self._P = LinearOperator(P.shape, cholmod.solve)

                elif self.pc == 'ilu':

                    ilu = scipy.sparse.linalg.spilu(pg.matrix.asCSC(P))
                    self._P = LinearOperator(P.shape, ilu.solve)

                elif self.pc == 'spsolve':

                    Mx = lambda x: scipy.sparse.linalg.spsolve(P, x)
                    self._P = scipy.sparse.linalg.LinearOperator(P.shape, Mx)

                else:
                    pg.critical(f'Preconditioning: "{self.pc}" '
                                 'not yet implemented')

        self.tSetup = pg.dur(key='ScipyWrapper.setup')
        #pg._b(self.tSetup)
        self._factorized = True


    def info(self, x):
        """Callback function for the solver.
        """
        self._iterCounter += 1
        if len(x) == self._A.shape[1]:
            res = np.linalg.norm(self._A*x - self._b) / self._bNorm
        else:
            res = x

        self._res.append(res)

        if self.verbose:
            tolRatio = np.log10(res)/np.log10(self.rtol) * 100
            #print('\r'+ f'{self._iterCounter}
            # {np.log10(b)}/{np.log10(self.rtol)} {int(tolRatio)}')
            if self._progress is None:
                self._progress = pg.utils.ProgressBar(100)
            self._progress(tolRatio-1,
                           f'iter: {self._iterCounter} tol: {pg.pf(res)}')


    def solve(self, b):
        """ Solve the factorized system
            :math:`\textbf{A}\textbf{x} = \textbf{b}` for :math:`x`.
        """
        self._b = b
        self._bNorm = np.linalg.norm(b)

        if self._ksp is not None:
            ## I want  res(a*x-b)/b == rtol

            # pg._b(self._P)
            if 'gmres' in str(self._ksp):
                x, err = self._ksp(self._A, b, tol=self.rtol, atol=0,
                                   M=self._P,
                                   callback=self.info, callback_type='x')


            elif 'cg' in str(self._ksp):
                x, err = self._ksp(self._A, b, tol=self.rtol, atol=0,
                                   M=self._P,
                                   callback=self.info)
            else:
                # minres
                bNorm = np.linalg.norm(b)
                x, err = self._ksp(self._A, b, tol=self.rtol*bNorm,
                                   M=self._P,
                                   callback=self.info)

            # bNorm = np.linalg.norm(b)
            # res = np.linalg.norm(self._A * x - b)
            # pg._r(f"tol={self.rtol} res={res} b={bNorm}, rRes={res/bNorm}")
            if self.verbose is True:
                print()
            return x

        if not isinstance(b, np.ndarray):
            b = np.array(b)
        x = self._direct(b)
        return x


class CholmodWrapper(SolverWrapper):
    """Wrapper for CHOLMOD linear solvers.
    """
    def __init__(self, A, **kwargs):
        super().__init__(A, **kwargs)

    def setup(self, **kwargs):
        """Setup the CHOLMOD solver.
        """
        with pg.tictoc('CholmodWrapper.setup'):
            self._A = pg.matrix.asSparseMatrix(self._AIn)
            pg.tic(key='CholmodWrapper.setup')
            self._direct = pg.core.LinSolver(self._A, verbose=self.verbose)
            self.tSetup = pg.dur(key='CholmodWrapper.setup')
            self._factorized = True

    def solve(self, b):
        """ Solve the factorized system
            :math:`\textbf{A}\textbf{x} = \textbf{b}` for :math:`x`.
        """
        with pg.tictoc('CholmodWrapper.solve'):
            x = pg.Vector(len(b))
            pg.tic(key='CholmodWrapper.solve')
            if not isinstance(b, pg.core.Vector):
                b = pg.Vector(b)

            self._direct.solve(b, x)

        self.tSolve = pg.dur(key='CholmodWrapper.solve')
        return x

class UmfpackWrapper(SolverWrapper):
    """Wrapper for UMFPACK linear solvers.
    """
    def __init__(self, A, **kwargs):
        pg.critical(NotImplementedError)
        super().__init__(A, **kwargs)

    def setup(self, **kwargs):
        """
        """
        pg.critical(NotImplementedError)

    def solve(sef, rhs, x):
        """
        """
        pg.critical(NotImplementedError)
        pass


class MumpsWrapper(SolverWrapper):
    """Wrapper for MUMPS linear solvers."""
    def __init__(self, A, **kwargs):
        self._ctx = None
        super().__init__(A, **kwargs)

    def __del__(self):
        if self._ctx is not None:
            self._ctx.destroy() # Cleanup


    def setup(self, **kwargs):
        """Setup the MUMPS solver.
        """
        self._A = pg.matrix.asCSR(self._AIn)

        from mumps import DMumpsContext
        self._ctx = DMumpsContext()

        if self.verbose == False:
            self._ctx.set_silent()

        if self._ctx.myid == 0:
            self._ctx.set_centralized_sparse(self._A)

            self._ctx.run(job=1) # Analysis
            self._ctx.run(job=2) # Factorization
            self._factorized = True

    def solve(self, b):
        """ Solve the factorized system
            :math:`\textbf{A}\textbf{x} = \textbf{b}` for :math:`x`.
        """
        x = b.copy()
        self._ctx.set_rhs(x) # Modified in place
        self._ctx.run(job=3) # Solve
        return x


class AMGCLWrapper(SolverWrapper):
    """Wrapper for AMGCL linear solvers."""
    def __init__(self, A=None, **kwargs):
        self._solver = None
        self._pre = None
        super().__init__(A, **kwargs)


    def __del__(self):
        pass

    def setup(self, **kwargs):
        """Setup the AMGCL solver.
        """
        self._A = pg.matrix.asCSR(self._AIn)

        import pyamgcl as amg

        pg._y('type:', self.type)
        pg._y('kwargs:', kwargs)
        pg._y('args:', self.kwargs)
        pg._y('pc:', self.pc)

        cls, typ = self.pc.split('|')
        PArgs=dict(type='iluk')
        PArgs['class'] = 'relaxation'

        SArgs=dict(type='idrs',
                   s=5,
                   maxiter=10000,
                   tol=1e-12,
                   replacement=True,
                   smoothing=True,
                   )

        PArgs=dict(type='iluk')
        PArgs['class'] = 'relaxation'

        # PArgs=dict(type=typ)
        # PArgs['class'] = cls

        ## some defaults
        SArgs=dict(type='idrs',
                   s=5,
                   maxiter=10000,
                   tol=1e-12,
                   replacement=True,
                   smoothing=True,
                   )

        # SArgs['type'] = self.type
        # SArgs.update(self.kwargs)

        with pg.tictoc('amgcl.setup'):
            self._solver = amg.solver(amg.amgcl(self._A, PArgs), SArgs)
            # self._pre = amg.amgcl(self._A, PArgs)
            # self._solver = amg.solver(self._pre, SArgs)

    def solve(self, b):
        """ Solve the factorized system
            :math:`\textbf{A}\textbf{x} = \textbf{b}` for :math:`x`.
        """
        with pg.tictoc('amgcl.solve'):
            x = self._solver(b)
        return x


class SchurWrapper(SolverWrapper):
    """Wrapper for Schur complement linear solvers."""
    def __init__(self, A=None, outer=None, inner=None, **kwargs):
        self._outer = outer
        self._inner = inner
        self.nV = kwargs.pop('vLength', 0)
        self._A = 0
        self._B = 0 #
        self._C = 0 # usually B.T
        self._D = 0 # 0
        super().__init__(A, **kwargs)

    def setup(self, **kwargs):
        """Setup the Schur complement solver.
        """
        pg.tic(key='SchurWrapper.setup')
        self._A, self._B, self._C, self._D = _splitMatrix(self._AIn)

        if self.verbose:
            pg.info(f"A ({type(self._A)}): {self._A.shape}")
            pg.info(f"B ({type(self._B)}): {self._B.shape}")
            pg.info(f"C ({type(self._C)}): {self._C.shape}")
            try:
                pg.info(f"D ({type(self._D)}): {self._D.shape}")
            except:
                pass

        if self._D is not None:
            pg.critical('D is != 0', NotImplementedError)

        PInner=None
        POuter=None
        if self.P is not None:
            if isinstance(self.P, list) and len(self.P) == 2:
                PInner = self.P[0]
                POuter = self.P[1]
            else:
                pg.critical('Cannot interpret PreConditioner')

        self._innerSolver = self._inner(self._A, P=PInner,
                                        verbose=self.verbose)

        vMul = lambda v: self._C.dot(self.innerSolve(self._B.dot(v)))
        self._M = LinearOperator((self._B.shape[1], self._B.shape[1]),
                                  matvec=vMul)

        self._kspSolver = self._outer(A=self._M, P=POuter,
                                      verbose=self.verbose)

        if self.verbose:
            pg.info(f"inner solver: {self._innerSolver}")
            pg.info(f"outer solver: {self._kspSolver}")

        self.tSetup = pg.dur(key='SchurWrapper.setup')
        self._factorized = True


    def innerSolve(self, rhs):
        """
        """
        return self._innerSolver.solve(rhs)


    def solve(self, b, x=None):
        """ Solve the factorized system
            :math:`\textbf{A}\textbf{x} = \textbf{b}` for :math:`x`.
        """
        if self.verbose:
            pg.info(f"Solve {self._kspSolver} (tol: {self._kspSolver.rtol})")

        if isinstance(b, np.ma.core.MaskedArray):
            self.b = np.array(b.data[~b.mask])
        else:
            self.b = b

        f = self.b[:self._A.shape[0]]
        g = self.b[self._A.shape[0]:]

        vr = self._C.dot(self.innerSolve(f)) - g
        p = self._kspSolver.solve(vr)
        v = self.innerSolve(f - self._B.dot(p))

        self._res = self._kspSolver._res
        self._iterCounter = self._kspSolver._iterCounter

        if isinstance(b, np.ma.core.MaskedArray):
            if x is None:
                xUnmask = np.array(b.data)
                xUnmask[~b.mask] = np.append(v, p)
                return xUnmask
            else:
                pg.critical('implement me')
        else:
            if x is None:
                return np.append(v, p)
            else:
                x[:self._A.shape[0]] = v
                x[self._A.shape[0]:] = p


class LinSolver(object):
    """Proxy class for the solution of linear systems of equations."""
    def __init__(self, A=None, solver=None, verbose=False, **kwargs):
        r"""Init the solver class with Matrix and starts factorization.

        Arguments
        ---------
        A: Matrix
            Matrix :math:`\textbf{A}` for the linear system o be solved.
        solver: str
            If solver is none decide form Matrix type
        """
        self.A = A
        self.b = None
        self.x = None
        self.solverStr = solver
        if isinstance(A, pg.BlockMatrix):
            pg.matrix.asCSR(A)

        self.verbose = verbose
        self._wrapper = LinSolver.wrapper(solver, verbose=self.verbose,
                                          **kwargs)(A, verbose=self.verbose)

    @property
    def iters(self):
        """Number of iterations. If there any."""
        return self._wrapper._iterCounter


    @property
    def residuals(self):
        """Residuals of the last results."""
        return self._wrapper._res


    @property
    def res(self):
        """Residual of last run"""
        if len(self.residuals) > 0:
            res = self.residuals[-1]
        else:
            bN = np.linalg.norm(self.b)
            if bN > 0:
                res = np.linalg.norm(self.A.dot(self.x) - self.b)/bN
            else:
                res = np.linalg.norm(self.A.dot(self.x) - self.b)
        return res

    @property
    def rtol(self):
        """Relative tolerance for the solver."""
        return self._wrapper.rtol

    @property
    def tSetup(self):
        """Time for setup of the solver."""
        return self._wrapper.tSetup

    @property
    def tSolve(self):
        """Time for the solve of the solver."""
        return self.solverTime

    @staticmethod
    def wrapper(solver=None, verbose=False, **kwargs):
        """ Return wrapper instance from solver string.

            solverSyntax: `vendor:type:[pc]:**kwargs`
        """
        if solver is None:
            return CholmodWrapper
        else:
            solver = solver.lstrip()

        if solver.lower() == 'petsc':
            return PetscWrapper(type='preonly', pc='lu', verbose=verbose)
        elif solver.lower() == 'scipy':
            return ScipyWrapper
        elif solver.lower() == 'cholmod':
            return CholmodWrapper
        elif solver.lower() == 'umfpack':
            return UmfpackWrapper
        elif solver.lower() == 'mumps':
            return MumpsWrapper
        elif solver.lower() == 'amgcl':
            return AMGCLWrapper

        # pg._b(solver)

        if 'schur(' in solver:
             # pg._y(solver)
            vals = solver.split('schur(')[1].split(',')
        #     # pg._r(vals)
        #     # pg._b(kwargs)

            outer = LinSolver.wrapper(solver=vals[0], verbose=verbose)
            inner = LinSolver.wrapper(solver=vals[1].split(')')[0],
                                      verbose=verbose)
            wrapper = SchurWrapper(outer=outer, inner=inner,
                                   verbose=verbose, **kwargs)
            return wrapper

        vendor = solver.split(':')[0]
        opts = solver.split(':')[1:]

        try:
            wrapper = getattr(sys.modules[__name__],
                              vendor.lower().capitalize() + "Wrapper")
        except AttributeError:
            wrapper = LinSolver().wrapper(vendor)

        pg._g(wrapper)
        pg._g(opts)

        pc = None
        ### type:pc:kwargs
        ### first opt is type
        if len(opts) > 0:
            type = opts[0]

        # search PC
        ## PC = pc0[pc0 kwargs]|pc for pc0,pc1[pc0 kwargs]|pc for pc0
        if len(opts) > 1:
            if '=' in opts[1] and not '[' in opts[1]:
                # ups .. this opts is apparently kwargs
                pass
            else:
                pc = opts[1].split(',')
                if len(pc) == 1:
                    pc = pc[0]

        # kwargs only in last opts
        if '=' in opts[-1] and not '[' in opts[-1]:
            kw = dict([kw.split('=')  for kw in opts[-1].split(',')])
        else:
            kw = {}

        # pg._b('vendor:', vendor)
        # pg._b('type:', type)
        # pg._b('pc:', pc)
        # pg._b(kw)

        kw.update(kwargs)
        # pg._g(vendor, type, pc, kw, verbose)
        wrapper = wrapper(type=type, pc=pc, verbose=verbose, **kw)

        return wrapper


    def isFactorized(self):
        """Check if the solver is factorized."""
        return self._wrapper._factorized


    def factorize(self, A):
        """Factorize the matrix A."""
        self.A = A
        return self._wrapper(A)


    def solve(self, b, check=False, **kwargs):
        """ Solve the linear system for rhs b.

        Attributes
        ----------
        b: iterable
            Right hand side vector for the system.
            B can be masked array to fit a reduced matrix.
            For convenience reasons, the returning solution vector
            matches the original b size.
        check: bool
            Perform residual check.

        Keyword Args
        ------------
        space: FEASpace|FEAOP
            Return FEASolution for the result that is associated to
            the FEASpace space, i.e., split the array.
        time: float | None
            Split the array and set time info.
        """
        with pg.tictoc('Wrapper.solve'):

            if isinstance(b, np.ma.core.MaskedArray):
                self.b = np.array(b.data[~b.mask])
            else:
                self.b = b

            self.x = self._wrapper.solve(self.b)

            if self.verbose:
                pg.info('linSolver.solve residual: ', self.res)

            if check is True:
                with pg.tictoc('tol check'):
                    res = self.res
                    if res > self._wrapper.rtol:
                        pg.warning(f"Solution residual seems to large(rtol): "
                                 f"{res} > {self._wrapper.rtol}")

            if isinstance(b, np.ma.core.MaskedArray):
                xUnmask = np.array(b.data)
                xUnmask[~b.mask] = self.x
                return xUnmask

        if 'space' in kwargs:
            return kwargs['space'].split(self.x,
                                         time=kwargs.get('time', None))

        return self.x


    def __call__(self, b):
        """short cut to self.solve(b)"""
        return self.solve(b)



def linSolve(A, b, solver=None, verbose=False, **kwargs):
    r"""Solve linear system of equations.

    Syntactic sugar to solve the linear system of equations:

    .. math::
        \textbf{A}\textbf{x} = \textbf{b}

    for :math:`\textbf{x}` using :py:mod:`oskar.linSolve.LinSolver`.

    Matrix :math:`\textbf{A}` should be sparse and positive-definite.

    Arguments
    ---------

    A : scipy.sparse.matrix, pygimli.RSparseMatrix | pygimli.RSparseMapMatrix
        System matrix. Should be sparse and positive-definite.

    b : iterable [float]
        Right hand side of the equation.

    solver : str [None]
        Select the solver backend.

        Defaults for `str=None`:

        * :term:`Cholmod`
            Matrix :math:`\textbf{A}` is sparse,
            **symmetric** and positive definite

        * :term:`Umfpack`
            Matrix :math:`\textbf{A}` is sparse,
            **non-symmetric** positive definite

        `solver = scipy` to choose the default linear solver from :term:`SciPy`

        More complete solver syntax for more advanced backends to come.

    verbose : bool [False]
        Be verbose.

    Keyword Args
    ------------
    **kwargs:
        Forwarded to the chosen :py:mod:`oskar.linSolve.LinSolver`.

    Returns
    -------
    x : pygimli.RVector
        Solution of the linear system of equations.
    """
    with pg.tictoc('linSolve'):
        solver = LinSolver(A, solver=solver, verbose=verbose, **kwargs)
        x = solver.solve(b, check=kwargs.pop('check', True), **kwargs)
    return x

