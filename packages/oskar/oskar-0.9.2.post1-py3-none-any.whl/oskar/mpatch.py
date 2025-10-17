#!/usr/bin/env python
"""Monkeypatch pg.core stuff that might need migration or not."""

import sys
import os

import numpy as np
import pygimli as pg

from . op import OP


def _fixRHS_GradV_(E):
    """Apply E * Identity(v) for rhs grad(v)."""
    E.integrate()
    # print(E)
    # print(E.elastic(), E.entity().dim(), E.cols(), E.colIDs())

    if E.elastic() and E.nCoeff() == 2 and E.cols() == 3 and E.colIDs() == [0]*3:
        # E is from 2d grad(v) and elastic so we ignore d_ij
        E.cleanCols([2])
    elif E.elastic() and E.nCoeff() == 3 and E.cols() == 6 and E.colIDs() == [0]*6:
        # E is from 3d grad(v) and elastic so we ignore d_ij
        E.cleanCols([3, 4, 5])

    elif E.nCoeff() == 2 and E.cols() == 4 and E.colIDs() == [0]*4:
        E.cleanCols([1, 2])
        # E is from 2d grad(v) so we ignore d_ij
    elif E.nCoeff() == 3 and E.cols() == 9 and E.colIDs() == [0]*9:
        # E is 3d grad(v) so we ignore d_ij
        #pg._g(E)
        E.cleanCols([1, 2, 3, 5, 6, 7])
        #pg.critical('implement me')
        #pg._y(E)


__SparseMapMatrix__iadd__orig = pg.core.SparseMapMatrix.__iadd__

def __SparseMapMatrix_iadd__(self, E):
    if isinstance(E, pg.core.SparseMapMatrix):
        __SparseMapMatrix__iadd__orig(self, E)
        return self

    from .op import OP
    from .feaSpace import ConstantSpace
    from .elementMats import mulE

    if isinstance(E, OP):
        # pg._y('iadd OP:', E.a, E.op, E.b)
        # print('Expression:', E.a, E.op, E.b)
        if E.op == '+':
            self += E.a
            self += E.b
        if E.op == '-':
            self += E.a
            self -= E.b

    elif isinstance(E, pg.core.ElementMatrix):
        try:

            if pg.isScalar(E.mulR):
                #pg.info('add-1: ', E, 'mul:', E.mulR)
                _fixRHS_GradV_(E)
                self.add(E, scale=E.mulR)
            else:
                f = E.mulR
                E.mulR = 1.0
                # pg.info('add-2: ', E, 'mul:', E.mulR, 'f:', f)
                E_ = mulE(E, f=f)
                _fixRHS_GradV_(E_)
                self.add(E_)

        except Exception as e:
            pg.info('add: ', E)
            print(E.mat())
            print(E.rowIDs(), E.rows())
            print(E.colIDs(), E.cols())

            import traceback
            traceback.print_exc(file=sys.stdout)
            pg.critical(e)
    elif isinstance(E, ConstantSpace):
        # its handled in op.assemble .. maybe move it here
        pass
    else:
        pg.error("Don't to know hot to add: ", E)

    return self

__SparseMapMatrix__isub__orig = pg.core.SparseMapMatrix.__isub__


def __SparseMapMatrix_isub__(self, E):
    if isinstance(E, pg.core.SparseMapMatrix):
        __SparseMapMatrix__isub__orig(self, E)
        return self
    if isinstance(E, OP):
        #pg._y('isub OP', E.a, E.op, E.b)
        if E.op == '+':
            self -= E.a
            self -= E.b
        if E.op == '-':
            self -= E.a
            self += E.b

    if isinstance(E, pg.core.ElementMatrix):
        try:

            if pg.isScalar(E.mulR):
                _fixRHS_GradV_(E)
                self.add(E, scale=-E.mulR)
            else:
                f = E.mulR
                E.mulR = 1.0
                E_ = mulE(E, f=f, c=-1)
                _fixRHS_GradV_(E_)
                self.add(E_)
        except Exception as e:
            pg.info('sub: ', E)
            print(E.mat())
            print(E.rowIDs(), E.rows())
            print(E.colIDs(), E.cols())

            import traceback
            traceback.print_exc(file=sys.stdout)
            pg.critical(e)


    return self

pg.SparseMapMatrix.__iadd__ = __SparseMapMatrix_iadd__
pg.SparseMapMatrix.__isub__ = __SparseMapMatrix_isub__

__SparseMatrixEqualOrig__ = pg.core.RSparseMatrix.__eq__

def __SparseMatrixEqual__(self, T):
    from .feaOp import FEAOP
    from .feaSpace import FEASpace
    if isinstance(T, (FEAOP, FEASpace)):
        return FEAOP(self, T, '==')
    return __SparseMatrixEqualOrig__(self, T)

pg.core.RSparseMatrix.__eq__ = __SparseMatrixEqual__
pg.core.RSparseMapMatrix.__eq__ = __SparseMatrixEqual__


def __ElementMatrix_add__(self, E, scale=None):
    """Add ElementMatrix E to self."""
    return OP(self, E, '+')


def __ElementMatrix_sub__(self, E):
    """Subtract ElementMatrix E from self."""
    return OP(self, E, '-')


def __ElementMatrix_mul__(self, E):
    """Multiply ElementMatrix E with self."""
    if isinstance(E, pg.core.ElementMatrix):

        return dotE(self, E)
    else:
        pg.error('Implement me')


def __ElementMatrixEqual__(self, T):
    """Compare two ElementMatrices."""
    self.integrate()
    T.integrate()
    from .elementMats import _applyMulR
    A = _applyMulR(self)
    B = _applyMulR(T)
    # for i, m in enumerate(self.matX()):

    #     if not np.allclose(self.matX()[i], T.matX()[i]):
    #         print(f'i:{i}', self.matX()[i], T.matX()[i])
    #         return False

    if A.rowIDs() != B.rowIDs():
        return False
    if A.colIDs() != B.colIDs():
        return False

    # if self.w() != T.w():
    #     return False

    # if self.w() != T.w():
    #     return False

    # if self.x() != T.x():
    #     return False
    # print(self.mat())
    # print(T.mat())

    sA = np.array(A.mat()).flatten()
    tA = np.array(B.mat()).flatten()

    meanA = np.mean(abs(sA))

    if pg.core.deepDebug() == -1:
       print('meanA:', meanA, np.linalg.norm(sA-tA),
            np.linalg.norm(sA-tA)< 1e-12,
            np.linalg.norm(sA-tA)/meanA, np.linalg.norm(sA-tA)/meanA < 1e-13)

    if meanA > 1e-10:
        return np.linalg.norm(sA-tA)/meanA < 1e-13
    else:
        return np.linalg.norm(sA-tA) < 1e-12

    return False

pg.core.ElementMatrix.__eq__ = __ElementMatrixEqual__
pg.core.ElementMatrix.__add__ = __ElementMatrix_add__
pg.core.ElementMatrix.__sub__ = __ElementMatrix_sub__
pg.core.ElementMatrix.__mul__ = __ElementMatrix_mul__
pg.core.ElementMatrix.mulR = 1.0


def __ElementMatrixTranspose__(self):
    """Return transposed ElementMatrix."""
    from . elementMats import copyE
    return copyE(self, transpose=True)
pg.core.ElementMatrix.T = property(__ElementMatrixTranspose__)


def __ElementMatrixShape__(self):
    """Return shape of ElementMatrix."""
    return self.rows(), self.cols()
pg.core.ElementMatrix.shape = property(__ElementMatrixShape__)


pg.core.ElementMatrix.eval = lambda a: a


def __stdVectorRMatrixShape__(self):
    """Return shape of stdVectorRMatrix."""
    return len(self), self[0].rows(), self[0].cols()
pg.core.stdVectorRMatrix.shape = property(__stdVectorRMatrixShape__)


def __IndexArrayEqual__(self, T):
    """Compare two IndexArray."""
    return np.allclose(self, T)
def __IndexArrayNEqual__(self, T):
    """Compare two IndexArray."""
    return not self.__eq__(T)

pg.core.IndexArray.__eq__ = __IndexArrayEqual__
pg.core.IndexArray.__ne__ = __IndexArrayNEqual__

def __MatrixArrayEqual__(self, T):
    """Compare two IndexArray."""
    return np.allclose(self, T)
def __MatrixArrayNEqual__(self, T):
    """Compare two IndexArray."""
    return not self.__eq__(T)

pg.core.RMatrix.__eq__ = __MatrixArrayEqual__
pg.core.RMatrix.__ne__ = __MatrixArrayNEqual__


def __ElementMatrixMap_Find_F(self, b, a=None, **kwargs):
    """Find values to evaluate b for ElementMatrixMap."""
    from . op import OP
    from . feaOp import FEAOP
    from . feaFunction import FEAFunction, FEAFunction3
    from . feaSolution import FEASolution, FEASolutionOP

    tictoc = pg.tictoc
    if b is None:
        return 1.0

    elif isinstance(b, int | float):
        return float(b)

    elif isinstance(b, dict):
        ## fallback or error here?
        with tictoc('params: eval(dict)'):
            return np.array([b[m.entity().marker()] for m in self.mats()])

    elif isinstance(b, pg.core.stdVectorR3Vector | pg.core.stdVectorRVector):
        rhs = b

    elif callable(b) and isinstance(b, OP):
        if hasattr(b, 'op') and b.op == '*' and \
            (isinstance(b.a, dict) or isinstance(b.b, dict)):
            ## dict * toEval(p) || toEval(p) * dict

            _a = self.createParametersForIntegration(b.a, **kwargs)
            _b = self.createParametersForIntegration(b.b, **kwargs)
            return _a * _b

        if hasattr(b, 'op') and b.op == '*' and \
            hasattr(b.a, 'evalOrder') and hasattr(b.b, 'evalOrder'):

            ## this can happen for u(FEASolution.continuous) * FeaFunction(forced per Cell)
            ## better move this somewhere inside eval!
            ## test in
            ## 00_test_assembling.py TestFiniteElementBasics.test_FEA_Expression_Eval
            ## c.continuous = False
            ## _testExp(s*c*u, u*c*s)
            # try:
            #     if b.a.continuous != b.b.continuous:
            #         #b.continuous = True
            _a = self.createParametersForIntegration(b.a, **kwargs)
            _b = self.createParametersForIntegration(b.b, **kwargs)

            # pg._g('*************', type(_a))
            # pg._g('*************', type(_b))

            if pg.isPosList(_a) and pg.isPosList(_b):
                # TODO refactor of OP.eval!!
                return np.sum(_a*_b, axis=2)

            if 0 and isinstance(_a, pg.core.stdVectorR3Vector) and \
                isinstance(_b, pg.core.stdVectorR3Vector):
                # TODO refactor of OP.eval!!
                # pg._b()
                ## will fail for VectorSpace*R3
                ## integrate will do it itself.

                ret = pg.core.stdVectorRVector()
                pg.core.dot(_a, _b, ret)
                return ret

            if isinstance(_a, pg.core.stdVectorMatrixVector):
                ## will fail for VectorSpace*R3 but this is ambiguous?
                ret = pg.core.stdVectorRVector()
                pg.core.dot(_a, _b, ret)
                return ret

            if isinstance(_a, pg.core.stdVectorRVector) and \
                isinstance(_b, pg.core.stdVectorR3Vector):

                return _b * _a

            return _a * _b

        #pg._b(b.evalOrder, b, kwargs)
        if b.evalOrder == 0:
            # pg._y('#######')
            # pg._r(self.entityCenters())
            # pg._r(b)
            # pg._r(b(self.entityCenters()[0]))
            # pg._b('+'*50)
            #pg._r('eval(center)', type(b), b,  kwargs)
            with tictoc('eval(centers)'):
                rhs = b(self.entityCenters(), elementMap=self, **kwargs)
            #pg._b('+'*50)
            #pg._r(rhs)
        elif b.evalOrder == 1:
            #pg._r('eval(nodes)', type(b), b,  kwargs)
            with tictoc('eval(nodes)'):
                rhs = b(self.space.mesh.positions(), elementMap=self, **kwargs)
        elif b.evalOrder == 2:
            #pg._r('eval(quads)', type(b), b,  kwargs)
            rhs = None
            with tictoc('eval(quads)'):
                with tictoc('get qp'):
                    qp = self.quadraturePoints()
                with tictoc('b(qp)'):
                    #pg._b(b)
                    rhs = b(qp, elementMap=self, **kwargs)
            #pg._b(rhs)

            with tictoc('params: eval(quads).2'):

                #pg._b(type(rhs), len(rhs), rhs[0])
                if isinstance(rhs, pg.core.stdVectorMatrixVector):
                    pg.error('remove me')

                if not isinstance(rhs,
                    pg.core.stdVectorRVector \
                    | pg.core.stdVectorR3Vector \
                    | pg.core.stdVectorMatrixVector \
                    | pg.core.stdVectorRDenseMatrixVector):

                    #print(rhs.ndim, rhs.shape)
                    if rhs.ndim == 4:
                        ## refactor with asStdVectorMatrixVector
                        rhs_ = pg.core.stdVectorRDenseMatrixVector()

                        for r in rhs:
                            #print(r.shape, r.ndim)
                            rv = pg.core.stdVectorRDenseMatrix()
                            for ri in r:
                                rv.append(ri)
                            rhs_.append(rv)

                    else:
                        rhs_ = pg.core.stdVectorRVector()
                        #pg._g(rhs)
                        for r in rhs:
                            rhs_.append(r)

                    return rhs_
            # for r in rhs:
            #     pg._r(r)
    elif isinstance(b, list) and any(isinstance(bi, FEAFunction) for bi in b):
        ### only supported so far:
        ### [func, scalar, scalar], one function at arbitrary position
        if len(b) == 2:

            if pg.isScalar(b[0]):
                f = FEAFunction3(lambda *a, **kw: [b[0], b[1](*a, kw)])
                f.evalOrder = b[1].evalOrder
            elif pg.isScalar(b[1]):
                f = FEAFunction3(lambda *a, **kw: [b[0](*a, kw), b[1]])
                f.evalOrder = b[0].evalOrder
            else :
                f = FEAFunction3(lambda *a, **kw: [b[0](*a, kw), b[1](*a, kw)])
                pg.critical('implement me')
                f.evalOrder = b[0].evalOrder or b[1].evalOrder

            return self.createParametersForIntegration(f, a=a, **kwargs)

        elif len(b) == 3:

            if isinstance(b[0], FEAFunction):
                f = FEAFunction3(lambda *a, **kw: [b[0](*a, kw), b[1], b[2]])
                f.evalOrder = b[0].evalOrder
            elif  isinstance(b[1], FEAFunction):
                f = FEAFunction3(lambda *a, **kw: [b[0], b[1](*a, kw), b[2]])
                f.evalOrder = b[1].evalOrder
            elif  isinstance(b[2], FEAFunction):
                f = FEAFunction3(lambda *a, **kw: [b[0], b[1], b[2](*a, kw)])
                f.evalOrder = b[2].evalOrder

            return self.createParametersForIntegration(f, a=a, **kwargs)

        pg.critical('implement me')

    elif isinstance(b, list) and any(callable(bi) for bi in b):
        ### only supported so far:
        ### [solution, scalar, scalar], one solution at arbitrary position

        scale = []
        sol = None
        for i, bi in enumerate(b):

            if isinstance(bi, FEASolution | FEASolutionOP) and sol is None:
                sol = bi
                scale.append(1.0)
            elif pg.isScalar(bi):
                scale.append(bi)
            else:
                pg._y(b)
                pg._y(type(bi))
                pg._y(bi)
                pg.critical('implement me')

        r = np.ndarray((len(sol.values), len(b)))
        evalOrder = 2

        for i, bi in enumerate(b):
            if isinstance(bi, FEASolution | FEASolutionOP):
                evalOrder = bi.evalOrder
                r[:,i] = bi.values
            else:
                r[:,i] = bi

        if evalOrder != 2:
            print(evalOrder)
            pg.critical('implement me')
        else:
            with pg.tictoc('params: Iq*r'):
                rhs = sol.qpInterpolationMatrix(self.quadraturePoints()) * r
        # print(type(sol*scale))
        # print(sol*scale)
        # rhs = (sol*scale).eval(self.quadraturePoints())
    else:
        if isinstance(b, int):
            pg.critical('Am I here?', b)
            rhs = float(b)
        else:
            rhs = b

    return rhs

pg.core.ElementMatrixMap.createParametersForIntegration = __ElementMatrixMap_Find_F


def __ElementMatrixMap_Mul__(self, b):
    if pg.core.deepDebug() == -1:
        pg.info('ElementMapMul', b)

    f = self.createParametersForIntegration(b)
    try:
        ret = pg.Vector(self.dofs.stop)
        self.integrate(f, ret)
    except BaseException as e:
        pg._g(type(b))
        pg._y(b)

        import traceback
        traceback.print_exc(file=sys.stdout)
        pg.critical(e)

    return ret
pg.core.ElementMatrixMap.__mul__ = __ElementMatrixMap_Mul__

