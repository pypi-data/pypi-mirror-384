#!/usr/bin/env python
"""Expression operators for finite element approximations."""
import numpy as np
import pygimli as pg

from . op import OP, Constant, findInstance, hasInstance, hasOP, splitOP
from . elementMats import dotE, createEMap, trE, symE
from . utils import asPosListNP, call
from . units import ParameterDict


class FEAOP(OP):
    """Operator for Expression with Finite Element Spaces.

    Special operator for expression with Finite Element Spaces.
    """

    def __init__(self, a=None, b=None, op=None, **kwargs):
        """FEAOP constructor.

        Arguments
        ---------
        a: OP|FEASpace|FEAOP
            Left side of the operator.
        b: OP|FEASpace|FEAOP
            Right side of the operator.
        op: str
            Operator symbol.

        Keyword Args
        ------------
        solutionGrad: bool
            Use solution gradient instead of the operator.
            Temporary until refactoring.
        **kwargs:
            Additional keyword arguments forwarded to OP.
        """
        #tmp hack until refactoring SolutionGrad.
        self._solutionGrad = kwargs.pop('solutionGrad', False)
        #tmp hack until refactoring SolutionGrad.

        super().__init__(a, b, op, OP=FEAOP, **kwargs)

        self._mesh = self.findMesh()
        self._lvl = 0 ## needed?

        #self._OP = FEAOP ## here or

        ## [dofOffset:FEASpace]
        self.feaSpaces = set()
        self.neg = False
        self._mulR = 1.0

        self.li = None
        self.bi = None


    def __call__(self, p=None, *args, **kwargs):
        """Forward for `eval(...)`."""
        return self.eval(p, *args, **kwargs)


    def __getitem__(self, idx):
        """Create new FEAOP with indicied values."""
        # don't use it for iteration .. it will run endless
        return OP(self, op='[]', idx=idx)


    def __hash__(self):
        """Hash for FEAOP."""
        from pygimli.utils.cache import valHash

        h = super().__hash__()
        for s in self.spaces:
            h = h ^ valHash(s)
        return h


    @property
    def dof(self):
        """Find degrees of freedom from active fea spaces."""
        dof = 0
        #self.feaSpaces = self.findFEASpaces()
        for space in self.spaces:
            #pg._b(self, space, type(space), id(space), space.forAssembling)
            if space.forAssembling is True:
                dof = max(dof, space.dof + space.dofOffset)
        return dof


    @property
    def reference(self):
        """Check if used reference implementation."""
        for space in self.feaSpaces:
            return not space.useCore


    @reference.setter
    def reference(self, ref):
        """Set to use reference implementation."""
        for space in self.feaSpaces:
            space.useCore = not ref


    @property
    def spaces(self):
        """Get all FEA spaces in this FEAOP."""
        return self.findFEASpaces()


    @property
    def mesh(self):
        """The mesh associated to this FEAOP."""
        return self._mesh

    @property
    def isZero(self):
        """Check if this FEAOP is zero."""
        if pg.isScalar(self.a, 0.0) or pg.isScalar(self.b, 0.0):
            return True

        return self.a is None and self.b is None


    def findMesh(self, op=None):
        """Recursive search this FEAOP for the associated mesh."""
        if op is None:
            op = self

        #pg.info(op)
        if hasattr(op.a, 'mesh') \
            and op.a.mesh is not None and op.a.mesh.nodeCount() > 0:

            return op.a.mesh

        if hasattr(op.b, 'mesh') \
            and op.b.mesh is not None and op.b.mesh.nodeCount() > 0:

            return op.b.mesh

        if isinstance(op.a, FEAOP):
            return op.a.findMesh()

        if isinstance(op.b, FEAOP):
            return op.b.findMesh()

        return None
        #pg.critical("Can't find mesh for this FEAOP", self)


    def findFEASpaces(self, op=None):
        """Recursive search this FEAOP for the associated FEASpaces."""
        from .feaSpace import FEASpace #circular .. fix me

        if op is None:
            op = self

        fea = self.feaSpaces

        if isinstance(op.a, FEASpace):
            # if op.a.dofOffset in fea and fea[op.a.dofOffset] != op.a:
            #     print('offset:', op.a.dofOffset, 'space', fea[op.a.dofOffset],
            #           'new space', op.a)
            #     pg.critical('Multiple FEA Spaces for the same dofOffset')
            #pg._g('### add-a', op.a, id(op.a))
            fea.add(op.a)
            #fea.update({op.a.dofOffset:op.a})

        if isinstance(op.b, FEASpace):
            # if op.b.dofOffset in fea and fea[op.b.dofOffset] != op.b:
            #     print('offset:', op.b.dofOffset, 'space', fea[op.b.dofOffset],
            #           'new space', op.b)
            #     pg.critical('Multiple FEA Spaces for the same dofOffset')

            # fea.update({op.b.dofOffset:op.b})
            #pg._g('### add-b', self, id(op.b))
            fea.add(op.b)

        if isinstance(op.a, OP):
            self.findFEASpaces(op.a)

        if isinstance(op.b, OP):
            self.findFEASpaces(op.b)

        return fea


    def eval(self, *args, **kwargs):
        """Evaluate FEAOP at p.

        Check possibility to use FEASolutionOP.eval directly

        Only works if FEAOP depends on FEASpaces with prior calculated
        FEASolution.

        Arguments
        ---------
        p: None | int | pos | [pos, ] [None]

            Evaluate for if p is of type:

            * None: for all cells
            * cell: for this cell
            * pg.Pos: for cell at position p
            * 1d-array: for list of 1D pg.Pos(x) along x-axis
            * int, float: x-coordinate for 1D
        """
        from . feaFunction import FEAFunction, FEAFunction3
        from . feaSolution import FEASolution, FEASolutionOP
        from . feaSpace import FEASpace
        from . mathOp import trace
        from . elasticity import ElasticityMatrix, strainToNotation

        with pg.tictoc('FEAop.eval'):
            #pg._b('FEAOP.eval', self, args, kwargs)
            p = args[0] if len(args) > 0 else None
            #pg.critical('fix me eval without arguments')

            if pg.core.deepDebug() == -1:
                pg._g('+'*80)
                pg._g(f'FEAop.eval {self} at\n', p, kwargs)
                pg._g('-'*80)
            spaces = list(self.findFEASpaces())
            #pg._y(type(self), spaces)

            if len(spaces) == 0:
                ## refactor me
                # pg._b('#######:', self, args,  kwargs)
                # if hasattr(self.a, 'mesh'): print(self.a.mesh)
                # if hasattr(self.b, 'mesh'): print(self.b.mesh)
                #print(self.b.mesh)
                return super().eval(*args, **kwargs)
                #return OP(self.a, self.b, self.op).eval(p, **kwargs)

            if len(spaces) != 1:
                if self.op == '*' and isinstance(p, pg.core.Boundary):
                    if self.b.op == 'norm':
                        pg._y()
                        return self.a.eval(p.center()) \
                            @ p.norm()[0:p.dim()+1]
                    if self.a.op == 'norm':
                        pg._g()
                        return p.norm()[0:p.dim()+1] \
                            @ self.b.eval(p.center())

                pg.warn('FEAOP', self)
                pg.warn('A', self.a)
                pg.warn('OP', self.op)
                pg.warn('B', self.b)
                pg.critical("Don't not how to interpret OP and cannot evaluate "
                            "for more than one space: ", spaces)
            # if len(spaces) == 0:
            #     return OP(self.a, self.b, self.op).eval(please)

            if 'time' in kwargs:
                kwt = kwargs.pop('time')
                if hasattr(kwt, '__iter__'):
                    return np.array([self.eval(*args, time=t, **kwargs)
                                        for t in kwt])
                kwargs['time'] = kwt

            space = spaces[0]
            if space.solution is None:
                pg.critical("Cannot evaluate without value.")

            #pg._g()
            uA = space.solution.eval(**kwargs)
            #pg._g(uA)
            def _evalMat(mE, u):
                scale = 1.0
                if mE.mulR:
                    scale = mE.mulR

                if __newFieldOrder__ is True:
                    ret = np.array(mE.mat()).T \
                        @ u.flatten()[mE.rowIDs()] / mE.entity().size() * scale
                else:
                    ret = np.array(mE.mat()).T \
                      @ u.T.flatten()[mE.rowIDs()] / mE.entity().size() * scale

                if pg.core.deepDebug() == -1:
                    print('mE:', mE)
                    print('scale:', scale)
                    print('u:', u[mE.rowIDs()])
                    print('Ret:', ret)

                if mE.nCoeff() == 1:
                    return ret

                dim = len(ret) // mE.nCoeff()
                ret.resize(mE.nCoeff(), dim)

                # if mE._nCoeff == 1:
                #     return ret

                # dim = len(ret) // mE._nCoeff
                # ret.resize(mE._nCoeff, dim)
                return ret

            def _evalForCell(c, u, p=None, op=None, **kwargs):
                """Evaluate for cell c at position p.

                TODO
                ----
                    * c can be cellSet if eval p is on a node, currently
                    only the mean of op[c] is chosen, maybe harmonic
                    or weighted mean can be useful .. test and check!
                """
                if op is None:
                    op = self

                if p is None:
                    p = c.center()

                if pg.core.deepDebug() == -1:
                    pg._y(f'#'*60)
                    pg._y(f'# Eval for cell {self}')
                    pg._y(f'#'*60)
                    pg._y(f'\tCell: {c}, p: {p}, op={op}, type={type(op)}')

                if pg.isScalar(op):
                    return op

                if pg.isPos(op):
                    return op

                if isinstance(op, ElasticityMatrix) or pg.isSquareMatrix(op):
                    return op

                if isinstance(op, list) \
                   and (isinstance(op[0], ElasticityMatrix) \
                     or pg.isSquareMatrix(op[0])) \
                   or (isinstance(op, np.ndarray) and pg.isSquareMatrix(op[0])):

                    if isinstance(c, pg.core.stdSetCells):
                        for _c in c:
                            return op[_c.id()]
                    return op[c.id()]

                # if pg.core.deepDebug() == -1:
                #     pg._g(isinstance(op, Constant))

                if isinstance(op, Constant):
                    if isinstance(c, pg.core.stdSetCells):
                        for _c in c:
                            return op(_c.dim())
                    return op(c.dim())

                if pg.isArray(op, space.mesh.cellCount()):

                    ## c is cellset so we take the mean value
                    if isinstance(c, pg.core.stdSetCells):
                        ## TODO need test!
                        m = 0
                        for i, _c in enumerate(c):
                            m += op[_c.id()]
                        return m/len(c)
                    else:
                        return op[c.id()]

                if isinstance(op, ParameterDict):
                    if isinstance(c, pg.core.stdSetCells):
                        ## TODO need test!
                        m = 0
                        for i, _c in enumerate(c):
                            m += op[_c.marker()]
                        return m/len(c)
                    else:
                        return op[c.marker()]

                if isinstance(op, FEASolution | FEASolutionOP | FEAFunction):
                    #if callable(op) and not isinstance(op, FEAOP):
                    #pg.error("checkme if FEASolution or FEAFunction", op)
                    #r = op(p, cell=c, **kwargs)
                    with pg.tictoc('OP(p, c)'):
                        return op(p, cell=c, **kwargs)

                if pg.core.deepDebug() == -1:
                    print(f'\t{op} := \n ' +\
                        f'\t\tA == {op.a}\n\t\t OP == {op.op}\n\t\t B  == {op.b}\n')

                if op.b is None:
                    if op.op == 'grad' and 1:
                        #pg._b()
                        # refactor with SolutionGrad!
                        ### could need performance op (check if necessary)
                        ## g = c.grad(p, u)
                        #pg._r(p, g[0:c.dim()])
                        #pg._g(u.shape)
                        ### think about forward to special
                        # FEAFunction3( grad_functor() )
                        #return np.asarray(c.grad(p, u, c.dim()))
                        #return np.asarray(c.grad(p, u))[0:c.dim(), 0:c.dim()]
                        #pg._b(kwargs)
                        if isinstance(c, pg.core.stdSetCells):
                            ### there are different interpolation results
                            ### if p is on node for different cells so we choose
                            ### for the mean
                            for i, _c in enumerate(c):
                                dim = kwargs.get('dim', _c.dim())
                                with pg.tictoc('grad(p)'):
                                    #pg._b(i, _c.grad(p, u, dim))

                                    if i == 0:
                                        a = np.asarray(
                                                    _c.grad(p, u, dim))[0:dim]
                                    else:
                                        a += np.asarray(
                                                    _c.grad(p, u, dim))[0:dim]

                            return a/len(c)

                        else:
                            dim = kwargs.pop('dim', c.dim())

                            # TODO: dim sp.grad differ mygrad FIXME
                            # my.dim = 1 this will mix up with func.sp.dim > 1
                            #dim = max(dim, 2)
                            #pg._g()
                            with pg.tictoc('grad(p)'):
                                return np.asarray(c.grad(p, u, dim))[0:dim]

                    elif op.op == 'div':
                        # TODO: Refactor with SolutionDiv
                        gr = _evalForCell(c, u, p=p,
                                          op=FEAOP(a=op.a, op='grad'), **kwargs)

                        if gr.ndim == 2:
                            return trace(gr)
                        else:
                            return sum(gr)
                    elif op.op == 'sym':
                        from . mathOp import sym
                        ret = _evalForCell(c, u, p=p, op=op.a, **kwargs)
                        #pg._b(op.a, type(ret), ret)
                        return sym(ret)
                    elif op.op == 'tr':
                        ret = _evalForCell(c, u, p=p, op=op.a, **kwargs)
                        #pg._b(op.a, type(ret), ret)
                        return trE(_evalForCell(c, u, p=p, op=op.a, **kwargs))
                    elif op.op == 'abs':
                        return abs(_evalForCell(c, u, p=p, op=op.a, **kwargs))
                    elif op.op == 'pow':
                        r = _evalForCell(c, u, p=p, op=op.a, **kwargs)
                        # pg._r(op.a)
                        #pg._r(r)
                        #r[1] = 0
                        if 0 and op.exponent == 2:
                            pg.critical('in use?')
                            if 1 and pg.isPos(r):
                                return (r*r).sum()

                        return pow(r, op.exponent)
                    elif op.op == 'identity':
                        # pg._g('identity', op.a)
                        if isinstance(op.a, FEAOP | FEASpace):
                            #pg._g('identity dim:', op.a.mesh.dim())
                            dim = kwargs.pop('dim', op.a.mesh.dim())
                            return np.diag(np.ones(dim))
                            # pg._g('identity dim:', 1)
                            # return 1.0
                    elif op.op == 'neg':
                        return -_evalForCell(c, u, p=p, op=op.a, **kwargs)

                else:
                    a = _evalForCell(c, u, p=p, op=op.a, **kwargs)
                    b = _evalForCell(c, u, p=p, op=op.b, **kwargs)

                    if pg.core.deepDebug() == -1:
                        pg._g(op)
                        print('A:', a)
                        print('B:', b)

                    cDim = None
                    if isinstance(c, pg.core.stdSetCells):
                        for _c in c:
                            cDim = _c.dim()
                            break
                    else:
                        cDim = c.dim()

                    if isinstance(a, ElasticityMatrix) or \
                    (pg.isSquareMatrix(a, 3) and pg.isSquareMatrix(b, 2)) or \
                    (pg.isSquareMatrix(a, 6) and pg.isSquareMatrix(b, 3)):

                        return a @ strainToNotation(b)

                    # handle unary operators
                    if op.op == '+':
                        # TODO: Refactor me
                        # for r = (grad(uF) + grad(uS))
                        # there will be dimension mix for 1D
                        # because:
                        # len.grad(uF) > 1 != len(grad(uS)) == c.dim()
                        # and resulting r has invalid values for r[>1]
                        if pg.isPos(a) and pg.isPos(b) and cDim == 1:
                            return a[0] + b[0]
                        return a + b
                    elif op.op == '-':
                        # TODO: Refactor me
                        # for r = (grad(uF) - grad(uS))
                        # there will be dimension mix for 1D
                        # because:
                        # len.grad(uF) > 1 != len(grad(uS)) == c.dim()
                        # and resulting r has invalid values for r[>1]
                        if pg.isPos(a) and pg.isPos(b) and cDim == 1:
                            return a[0] - b[0]
                        return a - b
                    elif op.op == '@':
                        return a @ b
                    elif op.op == '*':
                        return a * b
                    elif op.op == '/':
                        #elif op.op == '/' and not isinstance(op.b, OP):
                        return a / b

                #print('apply:', op)
                #pg.core.setDeepDebug(-1)
                # in use .. needed?
                with pg.tictoc('evalMat(p)'):
                    mE = self.apply(c.id(), op=op, debug=False,
                                    forEval=True, ent=c,
                                    core=not self.reference)
                    #pg._r(mE)
                    mE.integrate()
                    # print(mE)

                    return _evalMat(mE, u)

            # bad hack until refactoring .. convert FEAOP to OP for SolutionGrad
            if isinstance(p, pg.core.stdVectorR3Vector):
                def _toOP(t):
                    if isinstance(t, FEAOP):
                        if t.op == 'grad':
                            from .feaSolution import SolutionGrad
                            return SolutionGrad(t.a.solution)
                        elif t.op == 'div':
                            from .feaSolution import SolutionDiv
                            return SolutionDiv(t.a.solution)
                        a = _toOP(t.a)
                        b = _toOP(t.b)
                        return OP(a, b, op=t.op, **t._kwargs)
                    return t
                #in use?
                # pg._r('+'*80)
                # self.dump()
                # pg._r('-'*80)
                # pg._y('+'*80)
                # _toOP(self).dump()
                # pg._y('-'*80)
                with pg.tictoc('->OP.eval'):
                    return _toOP(self).eval(p, **kwargs)

            if isinstance(p, pg.core.MeshEntity):
                with pg.tictoc('eval.for_cell [ent]'):
                    return _evalForCell(p, uA, **kwargs)

            if p is None:
                p = self.mesh.cells()
                with pg.tictoc('eval.for_cell [c, ]'):
                    ret = np.array([_evalForCell(c, uA, **kwargs) for c in p])
            else:

                p = asPosListNP(p)

                if uA.ndim == 2:
                    ### convert field to core object to avoid per-pnt-conversion
                    uA = pg.core.R3Vector(uA)

                def _forPos(p):
                    n = self.mesh.node(self.mesh.findNearestNode(p))
                    ## check if p is on Node .. then create mean of interpolate
                    if n.pos().dist(p) < 1e-12:
                        c = n.cellSet()
                    else:
                        c = self.mesh.findCell(p)

                    if c is None:
                        pg.warn(f'{p} is outside the mesh for eval. '
                                'Returning 0.0.')
                        return 0.0

                    return _evalForCell(c, uA, p=p, **kwargs)

                with pg.tictoc('eval.forPos [p, ]'):
                    ret = np.array([_forPos(pi) for pi in p])

        return np.squeeze(ret)


    def multElementMatAndScale(self, a, f, **kwargs):
        """Multiply ElementMatrixMap a with f and return the result."""
        if pg.core.deepDebug()==-1:
            pg._g(a, f, kwargs)

        af = createEMap(name=f'{a}*{f}', space=a.space)

        rhs = a.createParametersForIntegration(f, **kwargs)
        a.mult(rhs, af)
        #halt
        return af


    def findElementMatAndScale(self, a, vLevel=0, **kwargs):
        """Find element matrix map and scale for operator a.

        The operator `a` needs to be a single linear or bilinear form.
        Return MapMatrix, scale(f), sign
        """
        order = kwargs.get('order')
        def _needsAssembling(a):
            ### refactor with similar below
            from . feaSpace import FEASpace
            if isinstance(a, FEASpace):
                return True
            if isinstance(a, FEAOP) and a.needsAssembling():
                return True

            A = False
            B = False
            if hasattr(a, 'a'):
                A = _needsAssembling(a.a)

            if hasattr(a, 'b'):
                B = _needsAssembling(a.b)

            return A or B

            # return isinstance(a, FEASpace) or \
            #        (isinstance(a, FEAOP) and a.needsAssembling())

        if pg.core.deepDebug() == -1:
            pg._y(f'{" "*8*vLevel}find for: {a}')

        if a is None:
            if pg.core.deepDebug() == -1:
                pg._g(f'{" "*8*vLevel}->ret({a}): {None, None, 1}')
            return None, None, 1

        if a is None or pg.isScalar(a) or pg.isArray(a) or \
            pg.isPosList(a) or pg.isMatrix(a):
            #check_in_use
            ## scalar field or vector field
            if pg.core.deepDebug() == -1:
                pg._g(f'{" "*8*vLevel}->ret({a}): {None, a, 1}')
            return None, a, 1

        if isinstance(a, list) and not pg.isPos(a) and not pg.isPosList(a):
            ## [f, a, b] .. decide the mul itself after know what to need
            #check_in_use
            if pg.core.deepDebug() == -1:
                pg._g(f'{" "*8*vLevel}->ret({a}): {None, a, 1}')
            return None, a, 1

        #pg._b(a, type(a))

        # and not kwargs.get('ignoreNeedsAssembleCheck', False):
        if not _needsAssembling(a):
            #pg._b('return no assembling')
            if pg.core.deepDebug() == -1:
                pg._g(f'{" "*8*vLevel}->ret({a}): {None, a, 1}')
            return None, a, 1
        else:
            pass
            #pg._b('needs assembling')

        from . feaSpace import FEASpace
        from . feaSolution import SolutionGrad, SolutionDiv

        if isinstance(a, FEASpace):
            if pg.core.deepDebug() == -1:
                pg._g(f'{" "*8*vLevel}->ret ({a}): '
                      f'{a.uMat(order=order), None, 1}')
            return a.uMat(order=order), None, 1

        if isinstance(a, FEAOP):
            if a.op == 'grad' and isinstance(a.a, FEASpace):
                # pg._b('a is FEAOP grad', type(a.a), isinstance(a.a, FEASpace),
                #                     isinstance(a.a, FEASolution),
                #                     a._solutionGrad,
                #         )
                if a._solutionGrad is True:
                    if pg.core.deepDebug() == -1:
                        pg._g(f'{" "*8*vLevel}->ret ({a}): '
                              f' {None,"SolutionGrad", 1}')
                    return None, SolutionGrad(a.a.solution), 1
                # ret pot matrix
                if pg.core.deepDebug() == -1:
                    pg._g(f'{" "*8*vLevel}->ret ({a}): '
                          f'{a.a.gradUMat(order=order), None, 1}')
                return a.a.gradUMat(order=order), None, 1

            elif a.op == 'div' and isinstance(a.a, FEASpace):
                # ret pot matrix

                if a._solutionGrad is True:
                    if pg.core.deepDebug() == -1:
                        pg._g(f'{" "*8*vLevel}->ret ({a}): '
                              f'{None, "SolutionDiv", 1}')
                    return None, SolutionDiv(a.a.solution), 1
                if pg.core.deepDebug() == -1:
                    pg._g(f'{" "*8*vLevel}->ret ({a}):'
                          f'{a.a.divUMat(order=order), None, 1}')
                return a.a.divUMat(order=order), None, 1

            elif a.op == 'identity' and isinstance(a.a, FEASpace):
                # ret pot matrix
                if pg.core.deepDebug() == -1:
                    pg._g(f'{" "*8*vLevel}->ret ({a}): {None, None, 1}')
                return None, None, 1
                #return a.a.identityMat, None, 1

            if pg.core.deepDebug() == -1:
                pg._r(f'{" "*8*vLevel}a.a: {a.a}')
                pg._r(f'{" "*8*vLevel}a.op: {a.op}')
                pg._r(f'{" "*8*vLevel}a.b: {a.b}')

            aa, fa, siga = self.findElementMatAndScale(a.a, vLevel=vLevel+1,
                                                       **kwargs)
            ab, fb, sigb = self.findElementMatAndScale(a.b, vLevel=vLevel+1,
                                                       **kwargs)

            # pg._b(aa.mats()[0])
            # pg._b(fa)
            # pg._b(siga)
            # pg._r(ab)
            # pg._r(fb)
            # pg._r(sigb)

            if a.op == 'neg':
                sigb = -1

            elif a.op == 'sym':
                # implement me with caching and/or without copying

                aas = createEMap(name=f'sym({aa})', space=aa.space)
                with pg.tictoc('create sym'):
                    pg.core.sym(aa, aas)
                aa = aas

            elif a.op == 'tr':
                aas = createEMap(name=f'tr({aa})', space=aa.space)
                with pg.tictoc('create tr'):
                    pg.core.trace(aa, aas)
                aa = aas

            if pg.core.deepDebug() == -1:
                pg._g(f'{" "*8*vLevel}aa: {aa} fa: {fa}')
                pg._g(f'{" "*8*vLevel}a.op: {a.op}')
                pg._g(f'{" "*8*vLevel}ab: {ab} fb: {fb}')
                pg._g(f'{" "*8*vLevel}siga {siga} | sigb {sigb}')

            sign = siga*sigb

            if aa and ab:

                if a.op == '+':
                    if fa is not None:
                        aa = self.multElementMatAndScale(aa, fa, **kwargs)
                    if fb is not None:
                        ab = self.multElementMatAndScale(ab, fb, **kwargs)

                    if pg.core.deepDebug() == -1:
                        pg._g(f'{" "*8*vLevel}->ret: ({a})'
                              f'{OP(aa, ab, "+"), None, sign}')
                    return [OP(aa, ab, '+'), None, sign]

                pg._r('in:', a)
                print('a', aa)
                print(a.op)
                print('b', ab)
                pg.critical('implement me')

            Ma = aa or ab
            #if Ma is None:
            #     # Fallback just in case.. e.g. with SolutionGrad()
            #     return None, a, 1
            #    pg._r(a)
            #     pg.critical('check me')

            f = None
            if fa is not None:
                f = fa
            if fb is not None:
                if f is not None:
                    ## fa * Ma * fb -> return mult(Ma, fb), fa
                    if Ma is None:
                        if pg.core.deepDebug() == -1:
                            pg._g(f'{" "*8*vLevel}->ret: ({a})'
                                  f'{None, a, 1}')
                        return None, a, 1

                    Ma = self.multElementMatAndScale(Ma, fb, **kwargs)

                    f = fa
                else:
                    f = fb

            if Ma is None and a.op == 'pow':
                ## TODO solutionGrad is FEAOP -> refactor
                ## FEAOP forced advanced parsing so the exp is neglected.

                if pg.core.deepDebug() == -1:
                    pg._g(f'{" "*8*vLevel}->ret ({a}): {Ma, a, sign}')
                return [Ma, a, sign]

            #pg._y([Ma, f, sign])
            if pg.core.deepDebug() == -1:
                pg._g(f'{" "*8*vLevel}->ret ({a}): {Ma, f, sign}')
            return [Ma, f, sign]

        if callable(a):
            if not isinstance(a, OP):

                pg.critical('shouldNotBeHere')

            return None, a, 1

        pg._r('a', a)
        pg.critical('implementme')
        return None, None, 1


    def assembleLinearForm(self, RHS, onBoundaries=False,
                           scale=1.0, **kwargs):
        """Search and assemble Linear form.

        Search and assemble Linear form with ElementMatrixMaps
        and Interpolators.
        """
        tictoc = pg.tictoc

        with tictoc('assemble linear form'):

            if scale is None:
                scale = 1.0

            # def _haveDirac_(a):
            #     if isinstance(a, Dirac):
            #         return a
            #     if hasattr(a, 'a') and hasattr(a, 'b'):
            #         return _haveDirac_(a.a) or _haveDirac_(a.b)
            #     if hasattr(a, 'a'):
            #         return _haveDirac_(a.a)
            #     return None

            ### special case for dirac impulse on Linear form
            d = findInstance(self, Dirac)
            if d is not None:
                with tictoc('assemble dirac'):
                    d.assemble(RHS, op=self, scale=scale, **kwargs)
                return

            from . feaSpace import ConstantSpace, ScalarSpace
            from . feaSolution import FEASolution
            from . elasticity import ElasticityMatrix

            if isinstance(self.a, ConstantSpace):
                if scale is not None and scale != 1.0:
                    pg.critical('implement me')
                if self.a.val is not None:
                    RHS[self.a.dofs] = self.a.val
            else:

                #pg._y(self)
                ## shortcut and cache for s*scale*sh
                if 1 and isinstance(self.a, ScalarSpace) and \
                    isinstance(self.b, FEASolution) and self.b.evalOrder == 2:

                    if self.a.order == self.b.space.order:
                        if not hasattr(self.a, '_M') or self.a._M is None:
                            self.a._M = pg.matrix.asSparseMatrix(
                                    (self.a * self.a).assemble(useMats=True))

                        #self.a._M = pg.matrix.asSparseMatrix(
                        #       (self.a * self.a).assemble(useMats=True))
                        # pg._r(type(RHS), type(self.a._M),
                        #       type(self.b), type(scale))
                        # pg._r(RHS, self.a._M, self.b, scale)
                        RHS += self.a._M * (self.b(**kwargs)*scale)
                        return

                with tictoc('get map'):
                    #pg._y(self, scale)
                    a, fa, sig = self.findElementMatAndScale(self,
                                                ignoreNeedsAssembleCheck=True,
                                                **kwargs)

                    if scale == 0.0 and fa is None:
                        return
                    # pg._g('a:', a, a.size())
                    # pg._g('fa:', fa)
                    # pg._g('scale:', scale)

                with tictoc('eval parameter'):
                    if fa is None and scale is not None:
                        fa = scale
                        scale = 1.

                    if pg.core.deepDebug() == -1:
                        pg._y(f'self:\t{self}')
                        pg._y(f'sig:\t{sig}')
                        pg._y(f'a:\t{a}')
                        pg._y(f'fa:\t{fa}')

                    with tictoc('a'):
                        #pg._b(fa)
                        f = a.createParametersForIntegration(fa, **kwargs)

                        if pg.core.deepDebug() == -1:
                            pg._y(f'f({type(f)}):\t{f}')
                            pg._y(f'scale.1:\t{scale}')

                    with tictoc('b'):
                        if isinstance(scale, OP):
                            scale = a.createParametersForIntegration(scale,
                                                                     **kwargs)

                    if pg.core.deepDebug() == -1:
                        pg._y(f'scale.2:\t{scale}')

                    if sig < 0:
                        scale *= -1.0

                    with tictoc('c'):
                        if isinstance(scale, pg.core.stdVectorRVector):
                            if isinstance(f, np.ndarray):
                                f = scale * f
                            else:
                                #fixme
                                f = scale * f
                                #f *= scale
                            scale = 1.0

                # pg._g('R:', R)
                # pg._g(f'scale: {scale}')
                # pg._g(f'f: {len(f)}:{f}')
                # for i, fi in enumerate(f):
                #     pg._g(i,':', fi)

                if isinstance(scale, int):
                    # integrate(.., .., alpha=scale)
                    # alpha can be float or RVector
                    # int(scale) -> wrongly converted to RVector(scale)
                    scale = float(scale)
                elif isinstance(scale, ParameterDict):
                    with tictoc('parMap'):
                        scale = [scale[m.entity().marker()] for m in a.mats()]

                # for i in range(a.size()):
                #     print(a.mats()[i])
                with tictoc('integrate'):
                    ### try to catch special cases first:
                    if isinstance(f, pg.core.stdVectorMatrixVector \
                                    | pg.core.stdVectorRDenseMatrixVector) and \
                        len(f) == a.size():
                        ### f is matrix per quadrature -- Refactor!

                        ### Check and fix first probably from wrong: s * grad(v)
                        if a.mats()[0].nCoeff() == 1 \
                            and a.mats()[0].cols() == 1:

                            if pg.core.deepDebug() == -1:
                                pg._b('integrate vrv')

                            with tictoc('integrate vrv'):
                                # s * [grad(v)] -> s*[div(v)]
                                # also possible
                                # s * [grad(v)] -> full sum (normL2(grad(v)))
                                vs = pg.core.stdVectorRVector()
                                #pg.core.trace(f, vs)
                                pg.core.sum(f, vs)
                                # print(R)
                                # print(a.size())
                                # print(len(vs))
                                # for ai in a.mats():
                                #     print(ai)

                                a.integrate(vrv=vs, R=RHS, alpha=scale)

                        else:

                            if pg.core.deepDebug() == -1:
                                pg._b('integrate vvmd')

                            with tictoc('integrate vvmd'):
                                a.integrate(vvmd=f, R=RHS, alpha=scale)
                        return

                    elif isinstance(f, ElasticityMatrix) \
                        or (pg.isMatrix(f) and f.shape[0] == f.shape[1]):
                        ### grad(v_elastic) * f(C) * I()

                        if pg.core.deepDebug() == -1:
                            print('assemble md')
                        with tictoc('assemble md'):
                            if hasattr(scale, '__len__') \
                                and len(scale) == a.size():

                                vmd = pg.core.stdVectorRDenseMatrix()
                                for i, si in enumerate(scale):
                                    vmd.append(f*si)
                                a.assemble(vmd=vmd, R=RHS, scale=1.0)
                            else:
                                a.assemble(md=f, R=RHS, scale=scale)
                        return

                    elif isinstance(f, pg.core.stdVectorRVector) and \
                        len(f) == a.size():
                        ### f is scalar per quadrature

                        if pg.core.deepDebug() == -1:
                            pg._b('integrate vrv')

                        with tictoc('integrate vrv'):
                            #pg._g(RHS, a, *f, scale)
                            a.integrate(vrv=f, R=RHS, alpha=scale)
                            #pg._y(RHS)

                    elif isinstance(f, pg.core.stdVectorR3Vector) and \
                        len(f) == a.size():

                        ### f is pos per quadrature
                        if pg.core.deepDebug() == -1:
                            pg._b('integrate vpv')

                        with tictoc('integrate vpv'):

                            if a.mats()[0].entity().dim() > 1 and \
                                a.mats()[0].nCoeff() == 1 and \
                                  a.mats()[0].cols() == 1:
                                ## for dim > 1
                                ## (ScalarSpace and not grad(u)) * R3(qp):
                                ## ->ScalarSpace *sum(R3(qp))
                                # e.g., normL2(v) = s*(v**2).assemble()
                                # pg._g(self)
                                # for i, v in enumerate(f):
                                #     print(i)
                                #     print(v)

                                vs = pg.core.stdVectorRVector()
                                pg.core.sum(f, vs)
                                # for i, v in enumerate(vs):
                                #     print(i)
                                #     print(v)
                                a.integrate(vrv=vs, R=RHS, alpha=scale)
                            else:
                                # VectorSpace * R3(qp)
                                # pg._b(f)
                                # pg._b(*f)
                                # pg._b(a.mats()[0])
                                a.integrate(vpv=f, R=RHS, alpha=scale)

                    elif hasattr(f, '__len__') and len(f) == a.size():
                        ## f is per cell
                        if pg.isPosList(f):
                            ### f is pos per cell
                            if pg.core.deepDebug() == -1:
                                print('integrate [p]_Cells')
                            with tictoc('integrate [p]_Cells'):
                                a.integrate(pv=f, R=RHS, alpha=scale)

                        elif isinstance(f[0], ElasticityMatrix) \
                            or pg.isMatrix(f[0]):
                            ### e.g., grad(v_elastic) * [f(C)]_Cells * I()
                            if pg.core.deepDebug() == -1:
                                print('assemble [md]_Cells')
                            with tictoc('assemble [md]_Cells'):
                                ## TODO create custom converter if needed
                                with tictoc('conv'):
                                    vmd = pg.core.stdVectorRDenseMatrix()

                                    if hasattr(scale, '__len__') \
                                        and len(scale) == a.size():
                                        for i, si in enumerate(scale):
                                            vmd.append(f[i]*si)
                                        scale = 1.0
                                    else:
                                        for i, fi in enumerate(f):
                                            vmd.append(fi)

                                a.assemble(vmd=vmd, R=RHS, scale=scale)
                            return

                        else:
                            ### f is scalar per cell
                            #pg._b(len(f), f[0], type(f[0]))
                            if pg.core.deepDebug() == -1:
                                print('integrate rv')
                            with tictoc('integrate rv'):
                                a.integrate(rv=f, R=RHS, alpha=scale)

                    elif hasattr(f, '__len__') and \
                        len(f) == a.space.dofPerCoeff:
                        #pg._g(a.space.mesh, a.space.dofPerCoeff, len(f))
                        if pg.core.deepDebug() == -1:
                            print('integrate n')
                        with tictoc('integrate n'):
                            a.integrate_n(f, R=RHS, alpha=scale)
                    #elif isinstance(f, ElasticityMatrix):

                    else:
                        ### generic fallback
                        if 0 or pg.core.deepDebug() == -1:
                            pg._b(f'a:{a}')
                            print(f'f:{f}')
                            print(f'alpha:{scale}')
                            print('integrate(default)')
                        with tictoc('integrate'):
                            a.integrate(f, RHS, alpha=scale)

                    #pg._r(R)


    def assembleBilinearForm(self, LHS=None, onBoundaries=False,
                             scale=1.0, **kwargs):
        """Search and assemble bilinear form.

        Search and assemble bilinear form with ElementMatrixMaps
        and Interpolators.

        FEAOP need to be: FEAOP|Space * FEAOP|Space or neg(FEAOP))

        """
        from . feaSolution import FEASolution

        tictoc = pg.tictoc

        with tictoc('assemble bilinear form'):
            if scale is None:
                scale = 1.0

            feaop = None
            sig = 1
            if self.op == 'neg':
                feaop = self.a
                sig = -1
            elif self.op == '*':
                feaop = self
            else:
                print(self)
                pg.critical('wrong operator for bilinear form ... need to be *')

            with tictoc('create maps'):
                a, fa, sig_a = self.findElementMatAndScale(feaop.a, **kwargs)
                b, fb, sig_b = self.findElementMatAndScale(feaop.b, **kwargs)

            sig *= sig_a * sig_b

            if pg.core.deepDebug() == -1:
                pg._y(f'Ma:\t{a} fa: {fa}')
                pg._y(f'a.op:\t{feaop.op}')
                pg._y(f'Mb:\t{b} fb: {fb}')
                pg._y(f'sig:\t{sig}')
                pg._y(f'scale:\t{scale}')

            if isinstance(a, OP):
                # for stuff like (a+b)*c
                with pg.tictoc('pre_eval a'):
                    a = a.eval(dim=b.pMat(0).cols())

            if isinstance(b, OP):
                # for stuff like c*(a+b)
                with pg.tictoc('pre_eval b'):
                    b = b.eval(dim=a.pMat(0).cols())

            fa2 = a.createParametersForIntegration(fa, **kwargs)
            fb2 = b.createParametersForIntegration(fb, **kwargs)

            # useMul = False

            # if isinstance(fa2, (pg.core.stdVectorR3Vector,
            #                    pg.core.stdVectorRVector)) or \
            #    isinstance(fb2, (pg.core.stdVectorR3Vector,
            #                    pg.core.stdVectorRVector)):
            #     useMul = True
            # if fa is not None and fb is not None:
            #     useMul = True

            # pg._g(useMul, fa, fb, type(fa2), type(fb2))

            useMul = True

            if fa is not None and pg.isScalar(fa) or pg.isMatrix(fa) and \
                not isinstance(fa, FEASolution):
                useMul = False
            if fb is not None and pg.isScalar(fb) or pg.isMatrix(fb) and \
                not isinstance(fb, FEASolution):
                useMul = False

            if fa is None and fb is None:
                useMul = False
            if fa is not None and fb is not None:
                useMul = True

            if pg.core.deepDebug() == -1:
                pg._g(f'useMul\t{useMul}')
                pg._g(f'fa2:\t{type(fa2), fa2}')
                pg._g(f'fa:\t{type(fa), fa}')
                pg._g(f'fb2:\t{type(fb2), fb2}')
                pg._g(f'fb:\t{type(fb), fb}')
                pg._g(f'scale:\t{type(scale), scale}')

            if sig < 0:
                scale *= -1.0

            if useMul is True:
                ### for fa or fb continuous
                # u * (v*grad(v))
                ###

                def _eMapImul(a, fa, fa2):
                    if not pg.isScalar(fa2, 1.0):
                        # hash might be better. but there is no hash for ndarray
                        #af = createEMap(name=f'{type(fa)}({hash(fa2)})*{a}',
                        #                space=a.space)
                        af = createEMap(name=f'{type(fa)}'
                                            f'({np.linalg.norm(fa2)})*{a}',
                                        space=a.space)
                        #af = pg.core.ElementMatrixMap()
                        if isinstance(fa, ParameterDict):
                            fa = fa.cellValues(a.space.mesh)

                        if isinstance(fa, np.ndarray | list) \
                            and pg.isMatrix(fa[0]):

                            with tictoc('map * p .1(vmd)'):
                                # TODO add custom rvalue conversion
                                vmd = pg.core.stdVectorRDenseMatrix()
                                for v in fa2:
                                    vmd.append(v)
                                #print('a', a, 'vmd:', vmd)
                                a.mult(vmd=vmd, ret=af)
                        else:
                            with tictoc('map * p .1'):
                                a.mult(fa2, af)
                    else:
                        af = a
                    return af

                af = _eMapImul(a, fa, fa2)
                bf = _eMapImul(b, fb, fb2)

                if pg.core.deepDebug() == -1:
                    pg._b('bilinear dot (useMul): '
                            f'{self} : {fa} : {fb} : {a} : {b}')

                # print('af:', af.dof(), af.dofB())
                # print('bf:', bf.dof(), bf.dofB())

                f = 1.0
                ### refactor with per cell part
                if pg.isArray(scale, a.space.mesh.cellCount()):
                    ###
                    # [perCell] * (BLForm(continuous))
                    ###
                    f *= scale
                    scale = 1.0
                elif pg.isArray(scale, a.space.mesh.nodeCount()):
                    ###
                    # [perCell] * (BLForm(continuous))
                    ###
                    f *= scale
                    scale = 1.0
                elif isinstance(scale, OP):
                    ###
                    # OP * (BLForm(continuous))
                    ###
                    if scale.evalOrder != 0:
                        pg.warn('f*(BL-form): Function f is marked for '
                                'eval order != 0 evaluation but only cell '
                    'center values allowed and used here. '
                    'If you want to apply it continuously you should '
                    'reformulate your equation, '
                    'e.g., move it inside the bilinear expression.')

                    f *= scale(a.space.mesh.cellCenters())
                    scale = 1.0

                if pg.core.deepDebug() == -1:
                    pg._b('eMap.integrate .1 ((af @ f * bf) * scale)\n'
                            f'{self}\n bf={bf}\n f={f}\n scale={scale}')

                    # print(af.mats()[0])
                    # print(bf.mats()[0])
                with tictoc('integrate .1'):
                    af.integrate(bf, f=f, A=LHS, scale=scale)
            else:
                ###
                # BLForm(perCell)
                ###
                with tictoc('integrate .2'):
                    f = 1.0

                    if not pg.isScalar(fa2, 1.0):
                        f = fa2

                    if not pg.isScalar(fb2, 1.0):
                        if not pg.isScalar(f, 1.0):
                            pg.critical('implement me', self)

                        f = fb2

                    #pg.info(f"bilinear dot:, {self}, {fa}, {fb}, {a}, {b}")
                    #pg.info('bilinear dot:', self)

                    if pg.isPosList(f) and len(f) > 3:
                        if pg.core.deepDebug() == -1:
                            pg.info('bilinear dot (vec): '
                                    f'{self}: {f} : {fa}: {fb} : {scale}')

                        a.integrate(b, v=f, A=LHS, scale=scale)
                    else:

                        if pg.isScalar(f) and 1: # always cache, TODO: check
                            ###
                            # scalar * BLForm(perCell)
                            ###
                            if pg.core.deepDebug() == -1:
                                pg.info('bilinear dot (cached): '
                                        f'{self} : {f} : {fa} : {fb} : {scale}')

                            if pg.isArray(scale, a.space.mesh.cellCount()):
                                ###
                                # [perCell] * (BLForm(perCell))
                                ###
                                f *= scale
                                scale = 1.0
                            elif isinstance(scale, OP):
                                ###
                                # OP * (BLForm(perCell))
                                ###
                                if scale.evalOrder != 0:

                                    pg.warn('f*(BL-form): Function f is '
                        'marked for evalOrder != 0 but only cell '
                        'center values allowed and used here. If you want to '
                        'apply it continuously you should reformulate '
                        'your equation, e.g., move it inside the '
                        'bilinear expression.')

                                f *= scale(a.space.mesh.cellCenters())
                                scale = 1.0

                            eMap = a.space.blMat(a, b,
                                            verbose=pg.core.deepDebug() == -1)

                            eMap.assemble(f, A=LHS, scale=scale)
                            #eMap.assemble(f=f, A=LHS, scale=scale)

                        else:
                            # not cached .. check if needed!!
                            if pg.core.deepDebug() == -1:
                                pg.info(f'bilinear dot:, {self}, {fa}, {fb}')

                            a.integrate(b, f=f, A=LHS, scale=scale)

    def findForms(self, cache=True):
        """Return cached version of findForms."""
        if cache is False:
            li, bi = findForms(self)
            return li, bi

        if self.li is None and self.bi is None:
            li, bi = findForms(self)
            self.li = li
            self.bi = bi

        return self.li, self.bi


    def assembleWithMats(self, onBoundaries=False, LHS=None, RHS=None,
                         **kwargs):
        """Assemble FEAOP with ElementMatrixMaps and interpolators."""
        with pg.tictoc(key='assemble.mats'):

            if pg.core.deepDebug() == -1:
                pg.info('assembleWithMats', self)
                pg._g('self.a:', self.a)
                pg._g('self.op:', self.op)
                pg._g('self.b:', self.b)

            # self.dump()
            li, bi = self.findForms(cache=False)

            #pg._y('li:', li)

            LHS = assembleBilinearForm(bi, A=LHS,
                                       onBoundaries=onBoundaries, **kwargs)

            RHS = assembleLinearForm(li, b=RHS, dof=self.dof,
                                     onBoundaries=onBoundaries, **kwargs)

            if len(bi) > 0 and len(li) > 0:
                return LHS, RHS

            if len(li) > 0:
                return RHS

            return LHS


    def assemble(self, onBoundaries=False, core=False, useMats=False, **kwargs):
        """Assemble FEAOP into a linear system of equations."""
        #### implement and clean
        #core = kwargs.pop('core', False)
        if useMats is True:
            return self.assembleWithMats(onBoundaries=onBoundaries,**kwargs)

        with pg.tictoc(key='assemble.cells.0'):
            ## REFACTOR!!
            ## Note: onBoundaries not yet ready for find form (norm(v) wrong)
            withForms = kwargs.pop('withForms', True)

            if 1 and withForms is True:# and onBoundaries is False:
                #refactor with assembleLinearFormWithCells()
                #refactor with assembleBilinearFormWithCells()


                lF, bF = self.findForms(cache=True)
                #pg._g(lF, bF)

                rhs = kwargs.pop('RHS', None)
                A = kwargs.pop('LHS', None)

                if len(lF) > 0:
                    #pg._g('LF', lF)
                    if rhs is None:
                        rhs = pg.Vector(self.dof, 0.0)
                    for lf in lF:
                        LF = formToExpr(lf)
                        if not pg.isScalar(LF, 0.0):
                            #pg._g(L)

                            d = findInstance(LF, Dirac)
                            if d is not None:
                                d.assemble(rhs, op=LF, scale=1.0, **kwargs)
                            else:
                                LF.assemble(onBoundaries=onBoundaries,core=core,
                                            RHS=rhs, withForms=False, **kwargs)

                if len(bF) > 0:
                    #pg._g('BF', bF)
                    #A = pg.SparseMapMatrix(self.dof, 1)
                    if A is None:
                        A = pg.SparseMapMatrix(1, 1)

                    for bf in bF:
                        BF = formToExpr(bf)

                        BF.assemble(onBoundaries=onBoundaries, core=core,
                                    LHS=A, withForms=False, **kwargs)

                #pg._b(type(A), type(rhs))
                if rhs is not None and A is not None:
                    return A, rhs
                if rhs is not None:
                    return rhs
                return A
            ## REFACTOR!!

            self.feaSpaces = self.findFEASpaces()

            oldReference = self.reference
            self.reference = not core

            if self.op == '==':
                #pg._y(self.a)
                if pg.isMatrix(self.a):
                    return self.a, self.b.assemble(onBoundaries=onBoundaries,
                                                core=core, **kwargs)

                elif pg.isArray(self.b):
                    return self.a.assemble(onBoundaries=onBoundaries,
                                        core=core, **kwargs), self.b

                elif pg.isScalar(self.b, 0.0):
                    A = self.a.assemble(onBoundaries=onBoundaries,
                                        core=core, **kwargs)
                    # pg.info(A.rows(), A.cols(), self.dof)
                    self.reference = oldReference
                    return A, np.zeros(self.dof)

                return (self.a.assemble(onBoundaries=onBoundaries,
                                        core=core, **kwargs),
                        self.b.assemble(onBoundaries=onBoundaries,
                                        core=core, **kwargs))

        with pg.tictoc(key='assemble.cells.1'):
            A = kwargs.pop('LHS', None)
            b = kwargs.pop('RHS', None)

            if onBoundaries is not False:
                #pg._b(self)
                with pg.tictoc(key='boundaries'):
                    if onBoundaries is True:
                        bIDS = [b.id() for b in self.mesh.boundaries()
                                if b.outside()]
                    else:
                        bIDS = onBoundaries

                    self.S = pg.SparseMapMatrix(self.dof, 1)
                    ret = np.zeros(self.dof)

                    for bID in bIDS:
                        if isinstance(bID, pg.core.Boundary):
                            bID = bID.id()
                        E = self.apply(bID, entity='boundary',
                                       core=core, **kwargs)
                        self.S += E

                #print(self.S)
            else: # assemble for all cells
                with pg.tictoc(key='cells'):
                    # A = kwargs.pop('L', None)
                    # b = kwargs.pop('R', None)
                    if self.mesh is not None:
                        #nCells = self.mesh.cellCount()
                        #ret = self.S = kwargs.pop('A',pg.SparseMapMatrix(1, 1))
                        self.S = pg.SparseMapMatrix(1, 1)
                        #ret = self.S = pg.SparseMapMatrix(self.dof, 1)

                        #pg._r(self)
                        for c in self.mesh.cells():
                            self.S += self.apply(c.id(), ent=c, core=core,
                                                 **kwargs)
                            #pg._g(self.S)

                    else:
                        #ret = self.S = kwargs.pop('A',
                        #                   pg.SparseMapMatrix(self.dof, 1))
                        self.S = pg.SparseMapMatrix(self.dof, 1)
                        for i in range(self.dof):
                            self.S.setVal(i, 0, 0.0)

                    # print('done:', self, self.S, self.S.rows(), self.S.cols())

            with pg.tictoc(key='post'):
                if self.S.cols() == 1:
                    ## Linear form
                    # if onBoundaries is not False:
                    #     # pg._r("S", self.S)
                    #     pg._r("S", self.S.rows(), self.S.cols())
                    #     pg._r("S.cols().", len(self.S.col(0)), self.dof)

                    if b is None:
                        ret = self.S.col(0)
                    else:
                        ret = b
                        ret += self.S.col(0)

                    ### Special case for Constant spaces ..fill RHS
                    ### with values if exist
                    for s in self.spaces:
                                # refactor me!!
                        from .feaSpace import ConstantSpace

                        if isinstance(s, ConstantSpace) and s.val is not None:
                            ret[s.dofs] = s.val

                elif self.S.cols() == 0:
                    # TODO: can happen on boundary assembling with ConstantSpace
                    # -> cleanMe
                    # e.g. equation:Darcy see: 04_Darcy, 05_Stokes
                    ret = self.S.row(0)

                elif self.S.shape == (0,0):
                    ## maybe some zero-ish
                    ret = pg.Vector(self.dof, 0.0)
                else:

                    if A is None:
                        ret = self.S
                    else:
                        ret = A
                        A += self.S

                self.reference = oldReference
            #pg._b(type(ret))
            return ret


    def needsAssembling(self):
        """Check is the operator needs assembling.

        Check if the operator contains FEASpace without a prior solution,
        then its assumed to be one for assembling.

        If all spaces are a solution then it needs eval(p).
        """
        # if not isinstance(op, FEAOP):
        #     return False
        if self._solutionGrad is True:
            return False

        return any(s.forAssembling is True for s in self.spaces)


    def apply(self, entID, op=None, entity='cell', debug=False, forEval=False,
              ent=None, core=False, **kwargs):
        """Create local element matrix the operator and the given entity.

        Arguments
        ---------

        forEval: bool
            Disable the 'forAssembling' check.

        TODO
        ----
        * Refactor with ent as first argument and optional with ent as int
        * ..

        """
        # refactor me!!
        from . feaSolution import FEASolution, FEASolutionOP
        from . feaFunction import FEAFunction
        from . feaSpace import FEASpace, ConstantSpace
        from . elasticity import ElasticityMatrix

        if op is None:
            # start assemble and reset temporaries
            op = self

        def opForAssembling(op):
            if isinstance(op, FEAOP):
                return op.needsAssembling()
            elif isinstance(op, FEASpace):
                return True
            return False

        if (debug or pg.core.deepDebug() == -1):
            pg._g('*'*60)
            pg._g(f'** apply() : {op}')
            pg._g(f'** isReference: {self.reference}, use core: {core}')
            pg._g(f'** A: {type(op.a)}: {op.a}')
            s = f'**\t assemble: {opForAssembling(op.a)}, eval:{forEval}'
            if hasattr(op.a, 'neg'):
                s += f', neg: {op.a.neg}'
            if hasattr(op.a, 'mulR'):
                s += f', mulR: {op.a.mulR}'
            pg._g(s)

            pg._g(f'** OP: {op.op}')

            pg._g(f'** B: {type(op.b)}: {op.b}')
            s = f'**\t assemble: {opForAssembling(op.b)}, eval:{forEval}'
            if hasattr(op.b, 'neg'):
                s += f', neg: {op.b.neg}'
            if hasattr(op.b, 'mulR'):
                s += f', mulR: {op.b.mulR}'
            pg._g(s)
            pg._g('*'*60)

        ## hack until cleanup
        ## assuming scalar * u == u * scalar
        ## assuming array * u == u * array

        if any([pg.isScalar(op.a),
                pg.isArray(op.a),
                pg.isMatrix(op.a),
                pg.isPosList(op.a),
                isinstance(op.a, ParameterDict),
                hasattr(op.a, '__iter__') \
                    and len(op.a) == self.mesh.cellCount(),
                ]) and op.b is not None:
            #pg._g(self)
            return self.apply(entID, self._OP(op.b, op.a, op.op),
                              entity=entity, ent=ent, core=core, **kwargs)

        if op.a is None:
            a = op.a
        elif opForAssembling(op.a) is False and forEval is False:
            a = op.a
        elif isinstance(op.a,
                    ConstantSpace | FEASolution | FEASolutionOP | FEAFunction):
            #pg.critical('in use?')
            #pg._g(type(op.a), forEval, opForAssembling(op.a), op.a, )
            a = op.a
            a.mulR = 1.0
        elif op.op == 'identity':
            #pg._r('general identity call **********', op.a)
            space = op.a
            if isinstance(op.a, FEAOP):
                spaces = list(op.a.spaces)

                if len(spaces) != 1:
                    pg.critical("Don't not how to find identity for "
                                "mixed spaces: ", spaces)

                space = spaces[0]

            entA = getattr(space, entity)(entID)
            #a = None
            #return 1.
            return space.identityE(entA)

        elif isinstance(op.a, FEASpace):

            entA = getattr(op.a, entity)(entID)
            ### space, grad(space), div(space)
            if op.op == 'grad':
                #print('return grad({0})'.format('a'))
                return op.a.gradE(entA, core=core)
            elif op.op == 'div':
                # print('return div({0})'.format('a'))
                return op.a.gradE(entA, core=core, isDivergence=True)
            elif op.op == 'norm':
                #pg._g('who use this return norm()')
                return entA.norm()
            elif op.op == 'neg':
                # print('return div({0})'.format('a'))
                #op.a.scale = -1
                # pg.warn('neg')
                return op.a.uE(entA, scale=-1, core=core)
            elif op.op == 'identity':
                pg.critical('FEASpace call, needed?')
                return op.a.identityE(entA, core=core)

            if isinstance(op.b, Dirac):
                return op.b.apply(getattr(op.a, entity)(entID), space=op.a,
                                  **kwargs)
            else:
                a = op.a.uE(entA, core=core)

            a.mulR = 1.0
        else:
            a = self.apply(entID, op.a, entity=entity, ent=ent, core=core,
                           **kwargs)

            if op.op == 'sym':
                # print('return sym({0})'.format('a'))
                return symE(a)

            elif op.op == 'neg':

                #self.neg = False
                a *= -1.0
                if hasattr(a, '_mat'):
                    a._mat *= -1.0
                #pg._b(a)
                return a

            elif op.op == 'tr':
                return trE(a)

        ### apply B ###########################################################

        def _applyParam(a, op, b):
            ## apply constant scale for the whole cell
            #pg._b("applyParam:", a, op, b)
            if op == '/':
                a.mulR = np.copy(a.mulR) / b
            elif op == '*':
                # if pg.isPos(a.mulR) and pg.isPos(b):
                #     pg._b('!!!')
                try:
                    a.mulR = np.copy(a.mulR) * b
                except BaseException:
                    #print(a.mulR, b)
                    if pg.isPos(b):
                        # could be a list
                        a.mulR = np.copy(a.mulR) * pg.Pos(b)
            else:
                pg.critical(f'implement me for op={op.op}')

            return a

        #pg._b(op.b)
        if op.b is None:
            return a
        elif pg.isScalar(op.b):
            ### A * float
            return _applyParam(a, op.op, op.b)
        elif isinstance(op.b, ConstantSpace):
            b = op.b

        elif 0 and hasattr(op.b, 'op' ) and op.b.op == 'identity':
            ## OP * I -> OP
            # if not (isinstance(op.a, ElasticityMatrix) or pg.isMatrix(op.a)):
            #     return op.a
            return op.a

        elif isinstance(op.b, FEASpace):
            if isinstance(op.a, Dirac):
                return op.a.apply(getattr(op.b, entity)(entID), space=op.b,
                                  **kwargs)

            entB = getattr(op.b, entity)(entID)
            b = op.b.uE(entB, core=core)
        elif (isinstance(op.b, OP) and opForAssembling(op.b) is False) and \
                forEval is False:

            # FEASpace free operator just need evaluation on p
            # (quadrature or cell center) mulE decides
            #pg._g(type(op.a), forEval, opForAssembling(op.a), op.a, )
            b = op.b

            # #### evaluate per cell
            # pg.warning('is needed?')
            # b = op.b.eval(entID)
            # return _applyParam(a, op.op, b)
        elif isinstance(op.b, ParameterDict):
            ## s * {} -> s* dict value for the cell
            # pg._r('apply param dict', op.b,
            #       op.b[getattr(self.mesh, entity)(entID).marker()])
            return _applyParam(a, op.op,
                               op.b[getattr(self.mesh, entity)(entID).marker()])
        elif isinstance(op.b, ElasticityMatrix) or pg.isMatrix(op.b):
            if pg.core.deepDebug() == -1:
                pg._b('op.b = C', op.b)
            a.mulR = op.b
            return a
        elif hasattr(op.b, '__len__'):
            ### A * [](len(cells)) | A * [](len(nodes)) | matrix


            if len(op.b) == self.mesh.cellCount() \
                and (isinstance(op.b[0], ElasticityMatrix) \
                     or pg.isMatrix(op.b[0])):
                if pg.core.deepDebug() == -1:
                    pg._b('op.b = [C]_CellID', op.b)
                a.mulR = op.b[getattr(self.mesh, entity)(entID).id()]
                return a

            elif len(op.b) == self.mesh.dim() or len(op.b) == 3:
                # decide if op.b is a vector field or a value
                # for each of 3 cells
                if np.all([pg.isScalar(bi) for bi in op.b]):
                    if len(op.b) == self.mesh.cellCount():
                        return _applyParam(a, op.op, op.b[entID])
                    # probably for each cell
                    return _applyParam(a, op.op, op.b)
                else:
                    # op.b can be [Field, 0, 0, ]
                    pass

            elif len(op.b) == self.mesh.cellCount():
                return _applyParam(a, op.op, op.b[entID])
            # elif len(op.b) == self.mesh.nodeCount():
            # does not work correctly .. fix me!!
            #     b = op.b[ent.ids()]
                #return _applyParam(a, op.op, op.b[ent.ids()])

            # pg._r(self.mesh, len(op.b))
            ## everything else .. could l(len(nodes)), or anisotropy matrix
            a.mulR = op.b
            return a

        elif callable(op.b) and not isinstance(op.b, OP):
            pg.critical('shouldNotBeHere')
            b = op.b
        elif isinstance(op.b, FEAFunction):
            b = op.b
        else:
            ### A * OP()
            # pg._y(self)
            # pg._y(op.b)

            b = self.apply(entID, op.b, entity=entity, ent=ent, core=core,
                            **kwargs)

        #
        ### apply a OP b where a and b only EMats or OP(EMats) ###############
        if a is None and b is not None:
            #pg._r(a, b)
            return b

        if pg.core.deepDebug() == -1:
            pg._b('apply op', self, 'op:', op.op)
            pg._b(a)
            pg._b(b)

        if op.op == '*':
            if self.neg is True:
                pg.warn('neg', self, self.neg)
                self.neg = False
                ret = dotE(a, b, c=-1.0, core=core, **kwargs)
                #ret.mulR = -1.0
                return ret
                #return dotE(a, b, c=-1.0*a.mulR*b.mulR, core=core)

            return dotE(a, b, core=core, **kwargs)
            # if isinstance(a, OP):
            #     return dotE(a, b, core=core)
            # return dotE(a, b, c=a.mulR, core=core)
        elif op.op == '+':
            if self.neg is True:
                pg.warn('unhandled neg  +', self.neg)
            # don't eval here .. kind of addition depends on rhs needs(v1 vs.v3)
            # pg._y(a)
            # pg._y(b)
            return a + b
        elif op.op == '-':
            if self.neg is True:
                pg.warn('unhandled neg  -', self.neg)
            # don't eval here .. kind of addition depends on rhs needs(v1 vs.v3)
            return a - b

        elif op.op == '==':
            if self.neg is True:
                pg.warn('unhandled neg  ==', self.neg)
            return a, b
        else:
            print('unhandled op', op)


    def split(self, u, skipHistory=False, time=None):
        """Split solution array and distribute it to available FEA spaces."""
        #print("self._feaSpaces 1", self, self.feaSpaces)
        ret = []

        if len(self.feaSpaces) == 0:
            self.feaSpaces = self.spaces

        d = {}
        for space in self.feaSpaces:
            if space.forAssembling is True:
                d[space.dofOffset] = space

        sortedSpaces = dict(sorted(d.items()))

        for space in sortedSpaces.values():
            ret.append(space.split(u,
                                   skipHistory=skipHistory, time=time))

        if len(ret) == 1:
            return ret[0]

        return ret


    def sym(self):
        """Create symmetry operator."""
        for s in self.spaces:
            ## elastic mapped spaces are automatically symmetric
            if s.elastic is True:
                #pg._b('symmetry for elastic space', s)
                return self
                #return FEAOP(self, op='sym')
        return FEAOP(self, op='sym')


    def tr(self):
        """Create trace operator."""
        return FEAOP(self, op='tr')


class Derive(FEAOP):
    """Operator for derivative of a function. Not yet implemented."""

    def __init__(self, space, var):
        super().__init__(a=space, b=None, op='derive')
        self._v = var

    def __str__(self):
        """Return string representation of Derive operator."""
        return f"derive({self.a}, {self._v})"


class Dirac(FEAOP):
    """Finite element operator allowing Dirac operator."""

    def __init__(self, rs=None, t0=0.0, space=None, **kwargs):
        super().__init__(a=None, b=None, op='dirac')
        if rs is None:
            self._rs = pg.Pos(0.0, 0.0, 0.0)
        else:
            self._rs = rs

        self._cellScale = kwargs.pop('cellScale', False)

        self._scale = None

        self._t0 = t0
        self._space = space ## needed?


    def __str__(self):
        """Return string representation of Dirac operator."""
        if self._rs != pg.Pos(0.0, 0.0, 0.0):
            return f'dirac(r-{self._rs})'
        return 'dirac(r)'


    def __repr__(self):
        """Return string representation of Dirac operator."""
        # pg._b(str(self))
        return str(self)


    def _getScaleVal(self, scale=1, **kwargs):
        """Return scale value based on input scale and internal scale."""
        if callable(scale):
            scale = call(scale, self._rs, **kwargs)

        if isinstance(self._scale, int | float):
            return self._scale*scale

        if callable(self._scale):
            return call(self._scale, self._rs, **kwargs)

        return scale


    def _findScale(self, op, **kwargs):
        """Find scale value for the operator."""
        from . feaSpace import FEASpace
        if isinstance(op, Dirac | FEASpace):
            return 1.

        if isinstance(op, list):
            return np.array(op)

        from . feaFunction import FEAFunction
        if isinstance(op, FEAFunction):
            return op(self._rs, **kwargs)

        if hasattr(op, 'op'):
            a = self._findScale(op.a, **kwargs)
            b = self._findScale(op.b, **kwargs)
            if op.op == '*':
                return a * b
            elif op.op == '/':
                return a / b
            # else:
            #     pg._r(op)
            #     pg.critical('implement me!')

        return op


    def assemble(self, R, op, scale=1.0, **kwargs):
        """Assemble Dirac operator into the given sparse matrix R."""
        if pg.core.deepDebug() == -1:
            pg._g(f'Dirac.assemble: {op}, scale={scale}')

        from . feaSpace import FEASpace
        space = findInstance(op, FEASpace) or self._space
        if space is None:
            pg.critical('Need FEAspace to apply Dirac.')

        ## check if self._rs is on node
        # nId = space.mesh.findNearestNode(self._rs)
        # if space.mesh.node(nId).pos().dist(self._rs) < 1e-6:
        #     R.addVal(self._getScaleVal(scale=scale, **kwargs), nId)
        #     return

        if pg.core.deepDebug() == -1:
            pg._g(f'Dirac.assemble addScale: {self._findScale(op)}')

        scale = scale * self._findScale(op, **kwargs)

        cell = space.mesh.findCell(self._rs)
        scale = self._getScaleVal(scale=scale, entity=cell, **kwargs)

        if self._cellScale is True:
            scale /= cell.size()

        if cell is not None:
            cN = cell.N(cell.shape().rst(self._rs))

            if space.nCoeff > 1:
                if isinstance(scale, float | int):
                    if scale != 1:
                        pg.warn('vector space, '
                                'but only scalar scale for Dirac.')
                    scale = [scale]*space.nCoeff

                if len(scale) < space.nCoeff:
                    pg.critical(f'Dirac scale to short for dim: {space.nCoeff}')
                if len(scale) > space.nCoeff:
                    pg.warning(f'Dirac scale then dim: {space.nCoeff}')

                for i in range(space.nCoeff):
                    R.addVal(cN*scale[i], cell.ids()+i*space.dofPerCoeff)
            else:
                R.addVal(cN*scale, cell.ids())
        else:
            pg.warn(f'Dirac source position rs={self._rs} is outside the mesh.')


    # def apply(self, ent, **kwargs):
    #     """
    #     """
    #     space = kwargs.pop('space', self._space) or self._space
    #     if space is None:
    #         pg.critical('Need FEAspace to apply Dirac.')

    #     E = createE(space.nCoeff, space.dofPerCoeff, space.dofOffset,
    #                     matX=None, w=None, x=None, ent=ent, order=0)

    #     if (hasattr(self, '_diracCell') and self._diracCell == ent) or \
    #        (not hasattr(self, '_diracCell') and \
    #               ent.shape().isInside(self._rs)):

    #         ### store this cell to avoid double count
    #         self._diracCell = ent

    #         E.mulR = self._getScaleVal(scale=1.0, entity=ent, **kwargs)
    #         #E.mulR = self._getScaleVal(scale=1.0,
    #                                       entity=ent, **kwargs)/ent.size()
    #         if self._cellScale is True:
    #             E.mulR /= ent.size()

    #         E.pMat().setCol(0, ent.N(ent.shape().rst(self._rs)))
    #         E.integrated(True)

    #     #print(E)
    #     return E

    # def __mul__(self, b):
    #     """Add multiplication."""
    #     #pg._b('Dirac.mul:', self, type(self), ':',  b, type(b))
    #     #pg._b('mul:', self, ':',  b, type(b))
    #     if pg.isScalar(b, -1):
    #         return FEAOP(self, b, '*')

    #     from . feaSpace import FEASpace
    #     if isinstance(b, FEASpace):
    #         return FEAOP(self, b, '*')

    #     if self._scale is None:
    #         self._scale = b
    #     else:
    #         self._scale *= b
    #     return self


    # def __div__(self, b):
    #     """Add division."""
    #     #pg._b('Dirac.div:', self, type(self), ':',  b, type(b))
    #     #pg._b('div:', self, ':',  b, type(b))
    #     if pg.isScalar(b, -1):
    #         return FEAOP(self, b, '/')

    #     from . feaSpace import FEASpace
    #     if isinstance(b, FEASpace):
    #         return FEAOP(self, b, '/')

    #     if self._scale is None:
    #         self._scale = b
    #     else:
    #         self._scale /= b
    #     return self


    # def __rmul__(self, b):
    #     """Add reverse multiplication."""
    #     ### CLEAN
    #     #pg._b('Dirac.rmul:', self, type(self), ':',  b, type(b))
    #     if pg.isScalar(b, -1):
    #         return FEAOP(self, b, '*')

    #     from . feaSpace import FEASpace
    #     if isinstance(b, (FEASpace, FEAOP)):
    #         return FEAOP(self, b, '*')

    #     if self._scale is None:
    #         self._scale = b
    #     else:
    #         self._scale *= b
    #     return self


class Sym(FEAOP):
    """Operator for symmetrizing gradient solutions."""

    def __init__(self, op):
        """Initialize Symmetrize operator."""
        super().__init__(a=op, b=None, op='sym')


    def __str__(self):
        """Return string representation of Symmetrize operator."""
        return f'sym({self.a})'


    def __repr__(self):
        """Return string representation of Symmetrize operator."""
        return str(self)


    def eval(self, *args, **kwargs):
        """Evaluate the symmetrized operator."""
        #pg._b('Sym.eval:', self, type(self), ':',  args, kwargs)
        a = self.a.eval(*args, **kwargs)

        if pg.isSquareMatrix(a):
            return 1/2 *(a + a.T)

        if pg.isSquareMatrix(a[0]):
            return np.asarray([1/2 *(a_ + a_.T) for a_ in a])

        print('Sym.eval:', self, type(self), ':',  args, kwargs)
        print(a)
        pg.critical("Don't know how symmetrize for evaluation")


def findForms(op, sign='+', parentOP=None, scale=None, vLevel=0):
    """Separate operator `op` in its linear and bilinear forms.

    Returns list of linear and bilinear expressions forms.

    * Linear form is: `[sign, space-function, scale-function]`
    * Bilinear form is: `[sign, space-function, scale-function]`

    Arguments
    ---------
    op: FEAOP
        Operator to be separated.
    sign: str
        Sign of the operator.
    parentOP: FEAOP
        Parent operator.
    scale: float
        Scale of the operator.
    vLevel: int
        Verbosity level.

    Returns
    -------
    li:
        List of linear forms.
    bi:
        List of bilinear forms.
    """
    with pg.tictoc(key='find forms'):
        from . feaSpace import FEASpace, hasFEASpace, ConstantSpace

        def _toggleSign(sign):
            if sign == '+':
                return '-'
            else:
                return '+'

        def _findForms(op, li, bi, sign='+', scale=None, vLevel=0):
            """Find forms (helper)."""
            #op.dump()
            def _countAssembling(a):
                """Count number of assembling in the operator."""
                N = 0
                if hasattr(a, 'op') and a.op == 'identity':
                    return 0

                if hasattr(a, 'a'):
                    N += _countAssembling(a.a)
                if hasattr(a, 'b'):
                    N += _countAssembling(a.b)

                if isinstance(a, FEASpace):
                    return 1

                return N

            #TODO reimplement with recursive search!!
            def _needsAssembling(a):
                """Check if the operator needs assembling."""
                # if hasattr(a, 'a') and hasattr(a.a, 'op') \
                # and a.a.op == 'identity':
                #     return False
                # if hasattr(a, 'b') and hasattr(a.b, 'op') \
                # and a.b.op == 'identity':
                #     return False

                if hasattr(a, 'op') and a.op == 'identity':
                    return False
                if hasattr(a, 'op') and a.op == 'norm':
                    return False

                # aN = False
                # bN = False
                # if hasattr(a, 'a'):
                #     aN = _needsAssembling(a.a)
                # if hasattr(a, 'b'):
                #     bN = _needsAssembling(a.b)

                return isinstance(a, FEASpace) or \
                    (isinstance(a, FEAOP) and a.needsAssembling())

            def _addScale(a, b):
                """Add scale to the operator."""
                if a is not None and not pg.isScalar(a, 1.0):
                    return a*b
                return b

            # if hasattr(a, 'op') and a.op == 'dirac':
            #     return True
            ## identity is shorted to 1.0
            if hasattr(scale, 'op') and scale.op == 'identity':
                pg._b('in use?')
                scale = 1.0

            if pg.core.deepDebug() == -1:
                pg._g('#'*60)
                pg._g(f'# {" "*8*vLevel} Find forms for op: {op}, '
                        f'scale: {scale}, sign: {sign}, '
                        f'asm: {_needsAssembling(op)}, '
                        f'asm_count {_countAssembling(op)}')

                if isinstance(op, OP):
                    print(f'{" "*8*vLevel} op.a:', op.a, 'asm:',
                            _needsAssembling(op.a))
                    print(f'{" "*8*vLevel} op.op:', op.op)
                    print(f'{" "*8*vLevel} op.b:', op.b, 'asm:',
                            _needsAssembling(op.b))

            if not isinstance(op, OP) and _needsAssembling(op):
                ## op is FEASpace -> FEAOP(op) that have assembleLinearForm
                li.append([sign, FEAOP(op), scale])
                return

            if _countAssembling(op) == 1:
                li.append([sign, op, scale])
                return

            if pg.isScalar(op, 0.0):
                # TODO why this should be needed? Check .. NeumannNorm test
                li.append([sign, 0.0, scale])
                return

            elif op.op is None and _needsAssembling(op):
                ## single u
                # pg._r('for doc write what happens here', op)
                li.append([sign, op, scale])

            elif op.op == 'neg':
                _findForms(op.a, li, bi, _toggleSign(sign), scale=scale)

            elif op.op == 'grad' or op.op == 'identity':
                #pg._b(op, scale)
                li.append([sign, op, scale])

            elif op.op == 'sym':
                symL = []
                symB = []
                _findForms(op.a, symL, symB)

                if len(symL) > 0:
                    li.append([sign, op, scale])
                if len(symB) > 0:
                    pg.warning('sym(BilinearForm) needs testing!')
                    bi.append([sign, op, scale])
                # pg._r('---')
                # print(sl)
                # print(sb)

                # sys.exit()

            elif op.op == 'tr':
                li.append([sign, op, scale])

            elif op.op in ['div']:
                if _needsAssembling(op.a) is True:
                    li.append([sign, op, scale])

            elif op.op == '==':
                pg.critical('should not be here')
                _findForms(op.a, li, bi, '+', vLevel=vLevel+1)
                _findForms(op.b, li, bi, '+', vLevel=vLevel+1)

            elif op.op == '+':
                pg.critical('should not be here')
                _findForms(op.a, li, bi, '+', vLevel=vLevel+1)
                _findForms(op.b, li, bi, '+', vLevel=vLevel+1)

            elif op.op == '-':
                pg.critical('should not be here')
                _findForms( op.a, li, bi, '+', vLevel=vLevel+1)
                _findForms(-op.b, li, bi, '+', vLevel=vLevel+1)

            elif op.op == '*':
                # pg._r(0)
                if _needsAssembling(op.a) is True and \
                    _needsAssembling(op.b) is True:

                    bi.append([sign, op, scale])
                elif 0 and isinstance(op.a, OP) and \
                    _needsAssembling(op.a) is True \
                        and not _needsAssembling(op.b):
                    # LF: u*Scale * B or Scale*u * B
                    _findForms(op.a, li, bi, sign, scale=_addScale(scale, op.b),
                                vLevel=vLevel+1)

                elif isinstance(op.a, OP) and _needsAssembling(op.a) is True \
                    and (pg.isScalar(op.b) or op.b is None
                            or not _needsAssembling(op.b)):
                    ## (u*u)|u * 1.0
                    # pg._y(op.a)
                    # pg._y(scale)
                    _findForms(op.a, li, bi, sign, scale=_addScale(scale, op.b),
                                vLevel=vLevel+1)

                    # li.append([sign, op])
                elif isinstance(op.b, OP) and _needsAssembling(op.b) is True \
                    and (pg.isScalar(op.a) or op.a is None
                            or not _needsAssembling(op.a)):
                    ## 1.0 * (u*u)|u
                    # pg._r(op.b)
                    # pg._r(f'scale: {scale}')
                    _findForms(op.b, li, bi, sign, scale=_addScale(scale, op.a),
                                vLevel=vLevel+1)

                    # l_ = []
                    # b_ = []

                elif _needsAssembling(op.a) is True or \
                    _needsAssembling(op.b) is True:
                    # LF: u * Scale  OR  scale * u
                    #pg._y(op)
                    li.append([sign, op, scale])
            else:
                print("can't find forms")
                print(op)
                pg.critical("can't find forms")


        if 0 or pg.core.deepDebug() == -1:
            pg.info('expand term:', op)

        terms = op.expand(forSpaces=True)

        if 0 or pg.core.deepDebug() == -1:
            pg.info('expanded terms:', terms)

        li = []
        bi = []
        for term in terms:
            _findForms(term, li, bi)

        if pg.core.deepDebug() == -1:
            # print('bilinear forms:', bi)
            pg._y('linear forms:', li)

        ## if LinForm and BinForm move LF form to the rhs
        if len(bi) > 0:
            for l in li:
                l[0] = _toggleSign(l[0])

        ## correct [-, neg(a), b] -> [+, a, b]
        ## correct [+, neg(a), b] -> [-, a, b]
        for l in li:
            if hasattr(l[1], 'op') and l[1].op == 'neg':
                l[1] = l[1].a
                l[0] = _toggleSign(l[0])

        ## remove I
        from .mathOp import I
        for i, l in enumerate(li):
            #pg._g(l)
            def _reduceI(l):
                #pg._y(l)
                if hasattr(l, 'op') and l.op == '*':
                    #pg._r(l)
                    if isinstance(l.a, I):
                        return l.b
                    if isinstance(l.b, I):
                        return l.a

                    return _reduceI(l.a) * _reduceI(l.b)
                return l

            li[i][1] = _reduceI(l[1])

            # return
            # if l[1].op == '*':
            #     _
            #     pg._b(l[1].a, l[1].b)

        ## LF should look like [sign, f(FEASpace)*any(not scalar), extra scalar scale]
        ## move wrong scales to the right side, and the rescale the FEASpace
        for i, l in enumerate(li):
            #l[1].dump()
            if not hasFEASpace(l[1]):
                ## TODO should this happen? check me
                continue

            ## skip LF with any norm inside -- >TODO: fix
            if hasOP(l[1], 'norm') or hasOP(l[2], 'norm'):
                continue

            ## skip LF with any sym inside -- >TODO: fix
            if hasOP(l[1], 'sym') or hasOP(l[2], 'sym'):
                continue

            ## skip LF with any identity inside -- >TODO: fix
            if 0 and hasOP(l[1], 'identity') or hasOP(l[2], 'identity'):
                continue

            ## skip LF with any Dirac inside -- >TODO: fix
            if hasInstance(l[1], Dirac) or hasOP(l[2], Dirac):
                continue

            ## skip LF with any ConstantSpace inside -- >TODO: fix
            if hasInstance(l[1], ConstantSpace) or hasOP(l[2], ConstantSpace):
                continue

            space = None
            coeff = None
            scale = None
            if 1:
                def _tokenize(e):
                    """Tokenize the expression."""
                    #pg._r(e, type(e))
                    if e is None:
                        return None, None, None

                    if pg.isScalar(e) \
                        or isinstance(e, (pg.core.RMatrix, ParameterDict)):
                        #pg._r(e)
                        return None, None, e

                    #print(hasattr(e, 'op'), e.op)

                    if hasattr(e, 'op') and e.op == '*':
                        #pg._g(e)
                        sa, ca, sca = _tokenize(e.a)
                        #pg._b(sa, ca, sca)
                        # pg._b('---', e.b)
                        sb, cb, scb = _tokenize(e.b)
                        #pg._b(sb, cb, scb)

                        #print([sa, sb], [ca, cb], [sca, scb])
                        #return [sa, sb], [ca, cb], [sca, scb]
                        if sa and sb:
                            pg.critical('implement me double space',
                                        sa, ':', sb)

                        if ca is None:
                            c = cb
                        elif cb is None:
                            c = ca
                        else:
                            c = ca*cb

                        if sca is None:
                            sc = scb
                        elif scb is None:
                            sc = sca
                        else:
                            sc = sca*scb

                        #print(sa or sb, c, sc)
                        return sa or sb, c, sc

                    elif hasFEASpace(e) and not hasOP(e, 'identity'):
                        #pg._g(e)
                        return e, None, None

                    elif isinstance(e,
                            OP | list | np.ndarray | pg.Vector | pg.Pos) \
                                or hasOP(e, 'identity'):
                        #pg._y(e)
                        #check solutionGrad=True
                        return None, e, None

                    else:
                        print(e)
                        pg.critical('implement me for', type(e), e)

                #pg._b(l)
                if l[2] is None:
                    space, coeff, scale = _tokenize(l[1])
                else:
                    space, coeff, scale = _tokenize(l[1]*l[2])

                #pg._b('s:', space, 'c:', coeff, 'sc:', scale)
                li[i][1] = space*coeff
                li[i][2] = scale
                #halt
            else:
                pg.critical('in use?')
                prod = None
                while (hasattr(l[1], 'op') and l[1].op == '*'):
                    if hasFEASpace(l[1].a):
                        break
                    scale = 1
                    noScale = None

                    #l[1].dump()
                    if hasOP(l[1].b, 'identity'):
                        break

                    if not hasFEASpace(l[1].a):
                        scale = l[1].a
                        noScale = l[1].b

                    elif not hasFEASpace(l[1].b):
                        noScale = l[1].a
                        scale = l[1].b

                    if not pg.isScalar(scale, 1):
                        li[i][1] = noScale
                        prod = scale if prod is None else prod * scale

                if prod is not None:
                    if li[i][2] is None:
                        li[i][2] = prod
                    else:
                        li[i][2] = prod*li[i][2]

            #pg._g(l)

        # remove NULL linear forms if they are are more than one li
        if len(li) > 1:
            li = [l for l in li if not (pg.isScalar(l[1], 0.0) or \
                                        pg.isScalar(l[2], 0.0))]

        if 0 or pg.core.deepDebug() == -1:
            print('bilinear forms:', bi)
            print('linear forms:', li)

        # pg._b(li)
        # pg._r('*'*80)

        return li, bi


def formToExpr(f):
    """Convert linear form to expression."""
    if hasOP(f[1], 'identity') and f[2] is not None:
        a, b = splitOP(f[1], 'identity')
        f[1] = (a*f[2]) * b
        f[2] = None

    if f[0] == '-':
        if f[2] is not None:
            return -(f[1]*f[2])
        else:
            return -f[1]
    else:
        if f[2] is not None:
            return f[1]*f[2]
        else:
            return f[1]


def assembleLinearForm(lForm, onBoundaries=False, b=None, dof=None, **kwargs):
    """Assemble linear form into system vector.

    Arguments
    ---------
    lForm: [sign, OP, scale] | [[sign, OP, scale],]
        Linear form to be assembled. As result from `findForms()`.

    onBoundaries: [pg.Boundary,]
        List of boundary elements where the linear form should be assembled.

    b: np.ndarray()=None
        Right-hand side vector to which the linear form is added.

    dof: int=None
        Degrees of freedom for the linear form.
        Need to be given if `RHS` is None.

    Keyword Arguments
    -----------------
    **kwargs: dict
        Additional keyword arguments for the assembly process.

    Returns
    -------
    R: pg.Vector
        Assembled linear form system vector.
    """
    from . feaSpace import FEASpace

    if b is None:
        if dof is None:
            pg.critical('Need dof to create RHS vector.')
        b = pg.Vector(dof, 0.0) ## for linear parts

    for sign, op, scale in lForm:
        if pg.core.deepDebug() == -1:
            pg._g(sign, op)

        if pg.isScalar(op, 0.0):
            continue

        if sign == '-':
            (-op).assembleLinearForm(b, onBoundaries=onBoundaries,
                                     scale=scale, **kwargs)
        else:
            if isinstance(op, FEASpace):
                ## happens to LF scale shift
                op = op*scale
                scale = 1

            op.assembleLinearForm(b, onBoundaries=onBoundaries,
                                  scale=scale, **kwargs)

    return b


def assembleBilinearForm(bForm, onBoundaries=False, A=None, **kwargs):
    """Assemble bilinear form into system matrix.

    Arguments
    ---------
    bForm: [sign, OP, scale] | [[sign, OP, scale],]
        Bilinear form to be assembled. As result from `findForms()`.

    onBoundaries: [pg.Boundary,]
        List of boundary elements where the bilinear form should be assembled.

    A: pg.SparseMatrix=None
        System matrix to which the bilinear form is added.
        If None, a new `pg.SparseMatrix` is created.

    Keyword Arguments
    -----------------
    **kwargs: dict
        Additional keyword arguments for the assembly process.

    Returns
    -------
    A: pg.SparseMatrix
        Assembled bilinear form system matrix.
    """
    if A is None:
        A = pg.SparseMapMatrix(1, 1)

    #TODO assembling on SparseMatrix !
    A = pg.matrix.asSparseMapMatrix(A)

    for sign, op, scale in bForm:
        if pg.core.deepDebug() == -1:
            pg._g(sign, op)
        if sign == '-':
            (-op).assembleBilinearForm(A, onBoundaries=onBoundaries,
                                       scale=scale, **kwargs)
        else:
            op.assembleBilinearForm(A, onBoundaries=onBoundaries,
                                    scale=scale, **kwargs)

    return A
    #return pg.matrix.asSparseMatrix(A)
