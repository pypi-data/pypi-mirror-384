#!/usr/bin/env python
"""Functions for evaluations for finite element approximations."""
import sys
import numpy as np
import pygimli as pg

from .op import OP
from .feaOp import FEAOP
from .utils import (asLatex, asString, asPosListNP,
                    asVecField, isVecField,
                    dumpSP, call, getInstanceAssignmentName,
                    showVectorField, vectorizeEvalQPnts,
                    )
from .units import (toSymbol)


class FEAFunction(OP):
    """A function to represent a physical field.

    TODO
    ----
        * refactor with FEAOP or OP
    """

    def __init__(self, *args, **kwargs):
        """Create FEAFunction.

        Arguments
        ---------
        *args : list
            List of arguments.

        Keyword Args
        ------------
        name : str
            Name of the function.
        repr : Sympy.Expr
            Sympy representation.
        """
        #self._OP = FEAOP
        if 'name' in kwargs:
            self._name = kwargs.pop('name')
        else:
            self._name = getInstanceAssignmentName(self.__class__.__name__)

        # sympy expression .. if exists
        self._repr = kwargs.pop('repr', '')

        # temporary holding expression for any field if Function is kind of
        # expression like grad(field) with u = expression.
        # Need generic gradient operator
        self.field = kwargs.pop('field', None)

        self._func = None
        if len(args) > 0:
            self._func = args[0]

        ## Set a flag if the function eval is performed by a lambdified function
        ## so the call is normalized with (pnt, **kwargs) see toFeaFunc.
        if hasattr(self._func, '_f'):
            self.hasLambdified = True

        super().__init__(valueSize=kwargs.pop('valueSize', 1),
                         OP=kwargs.pop('OP', FEAOP))

        if hasattr(self._func, 'evalOrder'):
            self.evalOrder = self._func.evalOrder


    def _copyMembers_(self, f):
        """Copy members from another FEAFunction."""
        self._func = f._func
        self._name = f._name
        self._repr = f._repr
        self.field = f.field
        self.evalOrder = f.evalOrder


    def __eq__(self, b):
        """Compare if two functions are equal.

        Just compare if two functions have the same sympy expression.
        Mainly supposed for easy testing.
        """
        if self.hasSympy() and (hasattr(b, 'hasSympy') and b.hasSympy()):
            return str(self._sympy_()) == str(b._sympy_())
        return super().__eq__(b)


    def __str__(self):
        """Return short (general) name, e.g., print()."""
        #pg._y(f'__self__: {self._name}')

        if self._repr != '':
            if pg.isNotebook():
                # create Display object for latex renderer
                from IPython.display import display, Markdown
                display(Markdown(self._repr_html_()))
                return ''
            elif pg.isIPyTerminal():
                # This will be caught and rendered as HTML by sphinx-gallery
                return self._repr_html_()
            #return 'f3(pnt)'
            return str(self._repr)

            # fails tests!
            #return asString(self._repr, lhs=self._name)

        if self._name is None:
            return f'f{self.valueSize()}(pnt)'
        return f'{self._name}(pnt)'


    def _repr_html_(self):
        """Return html representation for jupyter notebooks."""
        #pg._y(f'_repr_html_: {self._name}')
        return asLatex(self._repr, lhs=self._name)


    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        """Handle communication with numpy."""
        if ufunc == np.multiply:
            ## for np.float * self
            return self.__rmul__(inputs[0])

        if self.hasSympy():
            if ufunc == np.sin:
                #TODO: Refactor FEAFunction(hasSympy) -> class SympyFunction
                import sympy as sp
                return toFEAFunc(sp.sin(self._sympy_()),
                              name=getInstanceAssignmentName(),
                              isVec=self._func._isVec)
            else:
                pg._r('ufunc:', ufunc)
                pg._r('method:', method)
                pg._r('input:', *inputs)
                pg._r('kwargs', kwargs)
                pg.critical('implement me.')

        return FEAOP(self, op=ufunc)


    def itex(self):
        """Return inline latex representation."""
        # pg._y(f'itex', self._name, self._repr)
        return asLatex(self._repr,
                       lhs=self._name).replace('$$', '$')


    def _repr_str_(self):
        """Return str representation for pprint.

        Maybe this will be moved to str itself after all tests.
        """
        #pg._y(f'_repr_str_: {self._name}')
        return asString(self._repr, lhs=self._name)


    def __repr__(self):
        """Return long (unique) name, e.g, display."""
        #pg._y(f'__repr__: {self._name}')
        # if self._repr != '':
        if pg.isNotebook():
            ## already covered be _repr_html_
            return ''
        return str(self)


    def hasSympy(self):
        """Check if sympy expression is available."""
        return self._sympy_() != ''


    def sympy(self):
        """Return sympy expression."""
        return self._repr


    def _sympy_(self):
        """Return sympy expression. (compatible with sympy)."""
        return self._repr


    @property
    def expr(self):
        """Return sympy expression."""
        return self._repr


    @property
    def name(self):
        """Return name of the function."""
        return self._name


    @property
    def simplify(self):
        """Simplify sympy expression of available.

        Shortcut to toFEAFunc(self.expr.simplify())
        if sympy expression is available.
        """
        if self.hasSympy():
            return toFEAFunc(self._repr.simplify())
        else:
            return self


    @property
    def lfCode(self):
        """Return lambdified code."""
        import inspect
        return inspect.getsource(self._func._f)


    def show(self, mesh=None, **kwargs):
        """Show the function as field.

        Draws the function using pg.show.
        If the function is a vector function, it draws the
        field as absolute values with some arrows or streamlines using
        :py:mod:`oskar.utils.showVectorField()`.

        Arguments
        ---------
        mesh: pg.Mesh [None]
            If no mesh is given, some Unity range definition is chosen.
            Default dimension is 1, but it tries to guess the correct
            dimension from the sympy expression, if available.

        Keyword Args
        ------------
        **kwargs
            Forwarded to :py:mod:`oskar.utils.showVectorField()`.

        Returns
        -------
        ax, cBar:
            Return axes instance and color bar instance from pg.show.

        Example
        -------
        >>> import pygimli as pg
        >>> from oskar import asFunction, grad
        >>> v = asFunction('sin(4*pi*x)')
        >>> v.show() # doctest: +ELLIPSIS
        (<Axes:...
        >>> v = asFunction('(-y, x)')
        >>> v.show() # doctest: +ELLIPSIS
        (<Axes:...
        >>> u = asFunction('-x*y')
        >>> ax = u.show()[0]
        >>> grad(u).show(ax=ax, noAbs=True) # doctest: +ELLIPSIS
        (<Axes:...
        """
        if mesh is None:
            dim = 1
            if self.hasSympy():
                #dumpSP(self.sympy())

                if hasattr(self.expr, '__len__'):
                    dim = len(self.expr)
                else:
                    dim = 0
                    for fs in self.sympy().free_symbols:
                        if 'C.' in fs.name:
                            dim += 1

            x = np.linspace(0, 1, 21)
            if dim == 2:
                mesh = pg.createGrid(x, x)
            elif dim == 3:
                mesh = pg.createGrid(x, x, x)
            else:
                x = np.linspace(0, 1, 101)
                mesh = pg.createGrid(x)
                if dim != 1:
                    pg.warn(f"Can't interpret dimension: {dim}, "
                            "falling back to default dim=1.")

        label = kwargs.pop('label', None)
        xLabel = kwargs.pop('xl', None)
        yLabel = kwargs.pop('yl', None)

        if label is None:
            if mesh.dim() == 1 and self.hasSympy():
                label = self.itex()
            else:
                label = self.name

        if self.valueSize() == 3:
            return showVectorField(self, mesh=mesh, label=label, **kwargs)
        else:
            return pg.show(mesh, self(mesh), label=label,
                           xl=xLabel or 'x',
                           yl=yLabel or self.name,
                           **kwargs)


    def round(self, decimals:int=0):
        """Return a new FEAFunction with rounded coefficients.

        Only work for sympy functions.
        Change float values to int if its appropriate.

        Arguments
        ---------
        decimals: int[0]
            Number of decimal places to round to.

        Example
        -------
        >>> from oskar import asFunction, pprint
        >>> a = asFunction('1.0*x + 2.0*y + 2.00000004')
        >>> pprint(a)
        a(x,y) = 1.0*x + 2.0*y + 2.00000004
        >>> pprint(a.round(7))
        a(x,y) = x + 2*y + 2
        """
        name = getInstanceAssignmentName()
        if name is None:
            name = self.name
        import sympy as sp

        se = self.expr
        a = se.atoms(sp.Float)

        for ai in a:
            ar = round(ai, decimals)
            # pg._g(ar, int(round(ar)), abs(int(round(ar)) - ar),
            #      abs(abs(int(round(ar)) - ar)-0.5))

            if abs(int(round(ar)) - ar) < 1e-12:
                se = se.xreplace({ai:int(round(ar))})
            elif abs(abs(int(round(ar)) - ar)-0.5) < 1e-12:
                ## 4.4999999999 -> 4.5
                se = se.xreplace({ai:round(ar,10)})
            else:
                se = se.xreplace({ai:ar})

        return toFEAFunc(se, name=name, isVec=self._func._isVec)


    def subst(self, **kwargs):
        """Return a new FEAFunction with substituted kwargs.

        Only work for sympy functions.
        """
        from . feaSolution import (FEASolution, FEASolutionOP, FEASolutionStore)
        from .solve import (asFunction)
        import sympy as sp

        verbose = kwargs.pop('verbose', False)

        name = kwargs.pop('name', getInstanceAssignmentName())

        if name is None:
            name = self.name
        # from sympy.vector import CoordSys3D
        # C = CoordSys3D('C')

        se = self.expr
        old = None
        for k, v in kwargs.items():
            # if k == 'x':
            #     old = C.x
            # elif k == 'y':
            #     old = C.y
            # elif k == 'z':
            #     old = C.z
            # else:
            #     old = toSymbol(k)
            old = k
            new = v
            if isinstance(k, str):
                old = asFunction(k).expr

            if isinstance(v, str):
                new = asFunction(v).expr

            if isinstance(new, FEASolution | FEASolutionOP):

                # class FEASolEvaluator(sp.Function):
                #     """Evaluate FEASolution for sympy lambda."""
                # C = sp.vector.CoordSys3D('C', variable_names=['x', 'y', 'z'])
                # new = FEASolEvaluator(C.x, C.y, C.z, solSym)

                new = sp.Symbol(FEASolutionStore().add(new))

            elif isinstance(new, FEAFunction):
                if new.hasSympy() and new._sympy_():
                    new = new._sympy_()
                else:
                    pg.critical('FEAFunction without sympy expression '
                                'can not be substituted.')

            if verbose:
                dumpSP(se)
                pg._g(old, type(old))
                pg._y(new, type(new))

            se = se.subs(old, new)

            if verbose:
                dumpSP(se)

        return toFEAFunc(se, name=name, isVec=self._func._isVec)


    def iSubst(self, **kwargs):
        """Inline substitute kwargs."""
        self._copyMembers_(self.subst(name=self._name, **kwargs))
        #return self


    def eval(self, *args, **kwargs):
        """Evaluate function.

        Function is defined in R1, R2 or R3 optional with time parameter.

        If self has sympy expression and no args but kwargs are given,
        self is subst with kwargs.

        Arguments
        ---------

        Example
        -------
        >>> from oskar import *
        >>> f = asFunction('x²')
        >>> print(f)
        C.x**2
        >>> print(f(2))
        4.0
        >>> # swap coordinates
        >>> g = f(x='y')
        >>> print(g)
        C.y**2
        >>> print(g([0, 4]))
        16.0
        >>> # change coordinate to auxiliary
        >>> g = f(x='k')
        >>> print(g)
        k**2
        >>> print(g(0, k=3))
        9
        """
        ### check first if there is a parsed symbolic function
        if hasattr(self, 'hasLambdified'):
            with pg.tictoc('eval.subst'):
                if len(args) == 0 and kwargs:
                    return self.subst(**kwargs)

            return self._func(*args, **kwargs)

        if len(args) == 1 and pg.isPos(args[0]):
            return call(self._func, args[0], **kwargs)

        #return self.scale *
        # pg._g(id(self), self, args, kwargs)

        if len(args) > 0 and isinstance(args[0], pg.core.stdVectorR3Vector):
            ## qpi = [[R3,],]
            qp = args[0]
            ret = pg.core.stdVectorRVector()

            elementMap = kwargs.pop('elementMap', None)

            for i, qpi in enumerate(qp):
                ## qpi = [R3,]
                # print(i, qpi)
                # print(self.eval(qpi))

                ####
                ### lambda functions should be able to use p[0]
                ### and p.x() (which only work for qpi.T ..
                ### checking for Transpose
                ### print(np.array(qpi).flags)
                ### print(np.array(qpi).T.flags)
                ###

                ## r = f([R3,])
                try:
                    with pg.tictoc('eval f: [(R3),]'):
                        ## r = [f(R3),]
                        r = np.array([self.eval(a, **kwargs)
                                        for a in np.array(qpi)])
                except BaseException:
                    try:
                        with pg.tictoc('eval f: ([R3,])'):
                            ## r = f([R3,])
                            r = self._func(qpi,
                                           elementMap.pMat(i).entity(),
                                           **kwargs)
                            # r = self._func(np.array(qpi).T,
                            #               elementMap.pMat(i).entity())
                    except BaseException:
                        r = [0]

                # pg._y(type(qpi))
                # pg._y(len(qpi), qpi)
                # pg._g(len(r), r)
                if pg.isScalar(r):
                    ### function returns constant value
                    #pg._r('add len(qpi) * scalar')
                    ret.append(pg.Vector(len(qpi),r))
                elif len(r) == len(qpi):
                    ### function returns arrays (uses pg.x(p))
                    #pg._r('add r')
                    ret.append(r)
                else:
                    ### function returns returns single values (uses p[0])
                    #pg._r('iterate new')
                    # pg._b(kwargs)
                    try:
                        with pg.tictoc('eval f: [(R3), ]_3'):
                            ret.append([call(self.eval, qpii,
                                             elementMap.pMat(i).entity(),
                                             **kwargs) for qpii in qpi])
                    except BaseException:
                        with pg.tictoc('eval f: [(R3), ]_4'):
                            try:
                                ret.append([self.eval(qpii, **kwargs)
                                                for qpii in qpi])
                            except BaseException:
                                ret.append([self.eval(qpii,
                                            elementMap.pMat(i).entity(),
                                            **kwargs) for qpii in qpi])
            return ret

        # try:
        #     with tictoc('eval f: (**)'):
        #         return call(self._func, *args, **kwargs)
        # except:

        if len(args) > 0 and pg.isPosList(args[0]):
            # pg._b(args[0])
            return np.array([self.eval(a, **kwargs) for a in args[0]])

        if len(args) == 1 and args[0] is None:
            return call(self._func, self.space.mesh, **kwargs)

        # pg._r(self._func, args, kwargs)
        return call(self._func, *args, **kwargs)


    def __neg__(self):
        """Create negative of FEAFunction.

        Example
        -------
        >>> from oskar import asFunction, pprint
        >>> a = asFunction('x')
        >>> c = -a
        >>> pprint(c)
        c(x) = -x
        """
        if self.hasSympy():
            return toFEAFunc(-self._sympy_(),
                              name=getInstanceAssignmentName(),
                              isVec=self._func._isVec)

        return FEANegFunction(self)


    def __add__(self, b):
        """Create FEAFunction by addition.

        Example
        -------
        >>> from oskar import asFunction, pprint
        >>> a = asFunction('x')
        >>> b = asFunction('x')
        >>> c = a + b
        >>> pprint(c)
        c(x) = 2*x
        """
        if self.hasSympy():
            if (hasattr(b, 'hasSympy') and b.hasSympy()):
                #pg._b()
                return toFEAFunc(self._sympy_() + b._sympy_(),
                                  name=getInstanceAssignmentName(),
                                  isVec=self._func._isVec)
            if pg.isScalar(b):
                return toFEAFunc(self._sympy_() + b,
                                  name=getInstanceAssignmentName(),
                                  isVec=self._func._isVec)
        return super().__add__(b)


    def __radd__(self, b):
        """Create FEAFunction by addition.

        Example
        -------
        >>> from oskar import asFunction, pprint
        >>> a = asFunction('x')
        >>> b = 1 + a
        >>> pprint(b)
        b(x) = x + 1
        >>> print(b(2))
        3.0
        """
        if self.hasSympy():
            return toFEAFunc(b + self._sympy_(),
                              name=getInstanceAssignmentName(),
                              isVec=self._func._isVec)

        return super().__radd__(b)


    def __sub__(self, b):
        """Create FEAFunction by subtraction.

        Example
        -------
        >>> from oskar import asFunction, pprint
        >>> a = asFunction('2*x')
        >>> b = asFunction('x')
        >>> c = a - b
        >>> pprint(c)
        c(x) = x
        """
        if self.hasSympy():
            if (hasattr(b, 'hasSympy') and b.hasSympy()):
                #pg._b()
                return toFEAFunc(self._sympy_() - b._sympy_(),
                                  name=getInstanceAssignmentName(),
                                  isVec=self._func._isVec)
            if pg.isScalar(b):
                return toFEAFunc(self._sympy_() - b,
                                  name=getInstanceAssignmentName(),
                                  isVec=self._func._isVec)

        return super().__sub__(b)


    def __rsub__(self, b):
        """Create FEAFunction by subtraction.

        Example
        -------
        >>> from oskar import asFunction, pprint
        >>> a = asFunction('2*x')
        >>> b = 1 - a
        >>> pprint(b)
        b(x) = 1 - 2*x
        >>> print(b(2))
        -3.0
        """
        if self.hasSympy():
            return toFEAFunc(b - self._sympy_(),
                              name=getInstanceAssignmentName(),
                              isVec=self._func._isVec)

        return super().__rsub__(b)


    def __mul__(self, b):
        """Create FEAFunction by multiplication.

        Multiplication is supposed to be context dependent, e.g.,
        dot product is preferred over per value multiplication, if possible.

        Example
        -------
        >>> from oskar import asFunction, pprint, grad
        >>> a = asFunction('x')
        >>> b = a * 2
        >>> pprint(b)
        b(x) = 2*x
        >>> print(b(2))
        4.0
        >>> u = asFunction('x*y')
        >>> pprint(grad(u) * [1.0, 1.0])
        1.0*x + 1.0*y
        """
        from .mathOp import I

        if isinstance(b, I):
            return b.__rmul__(self)

        if isinstance(b, type) and b.__name__ == 'I' :
            return I(self).__rmul__(self)

        if self.hasSympy():
            import sympy as sp
            # pg._b('MUL', self, b, type(b), isinstance(b, sp.Expr))

            if isinstance(b, str):
                from .solve import asFunction
                b = asFunction(b)

            if isinstance(b, sp.Expr):
                return toFEAFunc(self._sympy_() * b,
                                  name=getInstanceAssignmentName(),
                                  isVec=self._func._isVec)

            if (hasattr(b, 'hasSympy') and b.hasSympy()):
                try:
                    return toFEAFunc(self._sympy_() * b._sympy_(),
                                  name=getInstanceAssignmentName(),
                                  isVec=b._func._isVec != self._func._isVec)
                except sp.matrices.exceptions.ShapeError:
                    return toFEAFunc(self._sympy_().dot(b._sympy_()),
                                      name=getInstanceAssignmentName(),
                                      isVec=False)

            if isinstance(b, (list | tuple)):
                return toFEAFunc(self._sympy_().dot(b),
                                  name=getInstanceAssignmentName(),
                                  isVec=False)

            if pg.isScalar(b):
                return toFEAFunc(self._sympy_() * b,
                                  name=getInstanceAssignmentName(),
                                  isVec=self._func._isVec)

        if (hasattr(self, '_sympy_') and self._sympy_() != '') and \
           (hasattr(b, '_sympy_') and b._sympy_() != ''):
            ## refactor me!!
            pg.critical('in use?')
            from .solve import asFunction
            #pg._b('MUL sp*sp', self, b)
            return asFunction(dummyMul=self._sympy_() * b._sympy_())
            #return toFEAFunc(self._sympy_() * b._sympy_(), isVec=False,
            #                  name=f'{self}*{b}')

        return super().__mul__(b)


    def __rmul__(self, b):
        """Create FEAFunction by reverse multiplication.

        Reverse multiplication is supposed to be context dependent, e.g.,
        dot product is preferred over per value multiplication, if possible.

        Example
        -------
        >>> from oskar import asFunction, pprint, grad
        >>> a = asFunction('x')
        >>> b = 2*a
        >>> pprint(b)
        b(x) = 2*x
        >>> print(b(2))
        4.0
        >>> u = asFunction('x*y')
        >>> pprint([1.0, 1.0]*grad(u))
        1.0*x + 1.0*y
        """
        import sympy as sp
        # pg._b('RMUL', self, b, type(b), isinstance(b, sp.Expr))
        from .mathOp import I
        if isinstance(b, type) and b.__name__ == 'I' :
            return I(self).__mul__(self)

        if self.hasSympy():
            if isinstance(b, (list | tuple | pg.Pos)):
                return toFEAFunc(self._sympy_().dot(b[0:len(self._sympy_())]),
                                  name=getInstanceAssignmentName(),
                                  isVec=False)
            # pg._g(b)
            from . elasticity import (ElasticityMatrix, notationToStress,
                                      strainToNotation)
            if isinstance(b, ElasticityMatrix):
                ## C * strain
                #pg._b('RMUL ElasticityMatrix', self, b)
                return toFEAFunc(notationToStress(b * strainToNotation(self)),
                                 name=getInstanceAssignmentName(),
                                 isVec=True)

            return toFEAFunc(b * self._sympy_(),
                              name=getInstanceAssignmentName(),
                              isVec=self._func._isVec)
        return super().__rmul__(b)


    def __pow__(self, exponent:any):
        """Create FEAFunction from exponent.

        Arguments
        ---------
        exponent: any
            Return $self^exponent$.
            For symbolic function, the dot product is chosen
            if the exponent is two and the FEAFunction is a vector field.

        Example
        -------
        >>> from oskar import asFunction, pprint, grad
        >>> u = asFunction('x*y')
        >>> pprint(grad(u)**2)
        x² + y²
        """
        if self.hasSympy():
            if exponent == 2 and self._func._isVec:
                return toFEAFunc(self._sympy_().dot(self._sympy_()),
                                  name=getInstanceAssignmentName(),
                                  isVec=False)
            else:
                return toFEAFunc(self._sympy_()**exponent,
                                  name=getInstanceAssignmentName(),
                                  isVec=self._func._isVec)

        #pg._b(f'POW: {self}, exponent: {exponent}')

        return super().__pow__(exponent)


class FEAFunctionDotNorm(FEAFunction):
    """FEAFunction for evaluate R3 * entity.norm().

    FEAFunction with special evaluator returns R1(p) = R3(p) * entity.norm().
    Norm is a size 3 vector so any to small FEAFunction3 evaluates will be
    filled with zeros.

    Example
    -------
    >>> from oskar import asFunction
    >>> from oskar.feaFunction import FEAFunctionDotNorm
    >>> mesh = pg.createGrid(2,2,2)
    >>> b = mesh.boundary(0)
    >>> v3 = asFunction('3*x, y, z')
    >>> print(v3(b.center()), b.norm())
    [3.  0.5 0.5] Pos: (1.0, 0.0, 0.0)
    >>> print(FEAFunctionDotNorm(v3)(b.center(), b))
    3.0
    >>> v2 = asFunction('3*x, y')
    >>> print(v2(b.center()))
    [3.  0.5]
    >>> print(FEAFunctionDotNorm(v2)(b.center(), b))
    3.0
    >>> v1 = asFunction('3*x')
    >>> print(v1(b.center()))
    3.0
    >>> print(FEAFunctionDotNorm(v1)(b.center(), b))
    3.0
    """

    def __init__(self, func, **kwargs):
        """Construct the Function.

        Arguments
        ---------
        func : FEAFunction3
            R3 input Function.

        Keyword Args
        ------------
        **kwargs: any
            Forwarded to `FEAFunction.__init__`.
        """
        super().__init__(func, **kwargs)


    def __str__(self):
        """Return string representation."""
        return f"<n,{self._func}>"


    def eval(self, p, entity, **kwargs):
        """Evaluate function at a position.

        Arguments
        ---------
        p: Pos, [Pos,]
            Evaluation points.
        entity: BoundaryElement
            Element entity provide a `R3 = norm()`

        Keyword Arguments
        ----------------
        **kwargs: any
            Forwarded to `eval(p, **kwargs)` of the input function.
        """
        #pg._b(p, entity, kwargs)
        with pg.tictoc('eval.<..,n>'):
            ## think about to guaranty FEAFunction3.eval always return R3
            ## TODO. check if p is [p,]
            v = super().eval(p, **kwargs)
            if pg.isScalar(v):
                return np.dot([v, 0, 0], entity.norm())
            try:
                return np.dot(v, entity.norm())
            except ValueError:
                return np.dot(np.resize(v, 3), entity.norm())


    def __mul__(self, f):
        """"""
        if self._func is None:
            self._func = f
        return self


class FEAFunction3(FEAFunction):
    """Wrapper for functions that need to be the first in any expression.

    TODO
    ----
        * refactor with OP
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, valueSize=kwargs.pop('valueSize', 3), **kwargs)


    def eval(self, *args, **kwargs):
        """Evaluate the function.

        Returns
        -------
        field or another FEAFunction
        """
        if hasattr(self, 'hasLambdified'):
            if len(args) == 0 and kwargs:
                return self.subst(**kwargs)

            return self._func(*args, **kwargs)

        if len(args) > 0 and isinstance(args[0], pg.core.stdVectorR3Vector):
            #pg._b()

            qp = args[0]
            ret = pg.core.stdVectorR3Vector()
            ## expect value is PosList(nQuadratures) p
            ## !! vectorize me !!

            for i, qpi in enumerate(qp):
                if hasattr(self._func, '_f'):
                    ### toFunction auto generated functions
                    #print(qpi)
                    ri = self._func(qpi, **kwargs)
                    # print(ri)
                else:
                    #print(f'qpi {i}, {qpi}')
                    ri = self.eval(qpi)
                    #pg._g(i, ri)
                    if len(qpi) > 1:
                        ### fix possible [scalar, vector] results
                        for j, vj in enumerate(ri):
                            if pg.isScalar(vj):
                                ri[j] = np.zeros(len(qpi)) + vj
                    else:
                        # for single quad points (order=1)
                        ri = [ri]
                #print(i, ri)
                #ret.append(np.array(ri).T)
                ret.append(np.asarray(ri))

            return ret

        if len(args) > 0:
            pts = asPosListNP(args[0])

            if pts.shape[0] > 1:
                with pg.tictoc('eval F3: [(R3), ]'):
                    return np.array([self.eval(p, **kwargs) for p in pts])

            try:
                with pg.tictoc('eval F3(pts)'):
                    return self._func(np.squeeze(pts), **kwargs)
            except Exception as e:
                pg._r(e)

            # pg._b(pts, kwargs)
            # pg._b(pts[0], kwargs)
            return [self._func(p, **kwargs) for p in pts]

        return pg.critical(ValueError, 'No points for evaluation given.')


    def __getitem__(self, i:int):
        """Get the i-th component.

        Returns a copy of the i-th component for symbolic vector functions.

        Arguments
        ---------
        i : int
            Get the i-th component of this vector function.

        Example
        -------
        >>> from oskar import asFunction, pprint
        >>> a = asFunction('[x, y]')
        >>> pprint(a[0])
        x
        """
        if self.hasSympy():
            return toFEAFunc(self.sympy()[i])

        pg.critical(f'Function {self} has no sympy base.')


class FEANegFunction(FEAFunction):
    """Negative function operator."""

    def __init__(self, func, **kwargs):
        """Create operator to negative a function.

        Arguments
        ---------
        func : FEAFunction
            Function to be negated.

        Keyword Args
        ------------
        **kwargs: any
            Forwarded to `FEAFunction.__init__`.
        """
        super().__init__(func, **kwargs)

    def __str__(self):
        """Return string representation."""
        return f'-{self._func.__str__()}'

    def __repr__(self):
        """Return long string representation."""
        # pg._b(str(self))
        return f'-{self._func.__repr__()}'

    def eval(self, *args, **kwargs):
        """Evaluate function.

        See FEAFunction.eval for details.

        Arguments
        ---------
        args: any
            Forwarded to FEAFunction.eval.

        Keyword Args
        ------------
        **kwargs: dict
            Forwarded to FEAFunction.eval.

        Returns
        -------
        ret: any
            Return the negative of the evaluated function.
        """
        ret = self._func.eval(*args, **kwargs)
        return -ret

    def __neg__(self):
        """Create negative of FEANegFunction.

        The original function is returned.
        """
        return self._func


class FEAFunctionRegionDict(FEAFunction):
    """Functions that contain out of region dictionaries."""

    def __init__(self, d, **kwargs):
        """Construct the Function.

        Arguments
        ---------
        d : dict {region: FEAFunction|FEAFunction3|scalar}
            Dictionary with region markers as keys and FEAFunctions as values.
        """
        if isinstance(d, dict):
            self._dict = d
        else:
            pg.critical(f'{d} need to be of type dictionary but is: {type(d)}')

        super().__init__(**kwargs)


    def __hash__(self):
        """Return hash of the function."""
        from pygimli.utils.cache import valHash
        return valHash(self._dict)


    def eval(self, *args, **kwargs):
        """Evaluate function.

        See FEAFunction.eval for details.

        Arguments
        ---------
        args: any
            Forwarded to FEAFunction.eval.

        Keyword Args
        ------------
        **kwargs: dict
            Forwarded to FEAFunction.eval.
        """
        tictoc = pg.tictoc
        #pg._b(self, args, kwargs)

        if len(args) > 0 and isinstance(args[0], pg.core.stdVectorR3Vector):
            qp = args[0] # mapped quadrature points
            eMap = kwargs.pop('elementMap', None)

            if eMap is None:
                pg.critical('Need elementMap to evaluate for regions.')

            ret = pg.core.stdVectorRVector()

            with tictoc('eval f(dict): vectorize(qpi)'):
                for regionMarker, func in self._dict.items():
                    #pg._r(regionMarker)
                    vqp = pg.PosList() # vectorized quadrature points
                    # fill vqp from qp for regionMarker based on eMap
                    pg.core.vectorizePosVectorList(qp, vqp, regionMarker, eMap)
                    vqp = np.array(vqp)     #TODO Cache me!

                    if 'time' in kwargs:
                        try:
                            rf = func(vqp[:,0], vqp[:,1], vqp[:,2],
                                      kwargs['time'])
                        except BaseException:
                            rf = func(vqp, kwargs['time'])
                    else:
                        try:
                            rf = func(vqp[:,0], vqp[:,1], vqp[:,2])
                        except BaseException:
                            rf = func(vqp, kwargs['time'])

                    # backfill ret from rf like qp
                    pg.core.deVectorizeRVectorToPosVectorList(ret, rf, qp,
                                                            regionMarker, eMap)

                    #print(len(ret), eMap.size())
                return ret


def toFEAFunc(expr, name:str=None, isVec:bool=False, simplify:bool=False):
    """Convert sympy expression to FEAFunction.

    It might be easier to use `:py:mod:`oskar.solve.parse` since it ensures
    some convention to produce suitable functions from string.

    Arguments
    ---------
    simplify: bool[False]
        Simplify the given sympy expression. Use with care.
    """
    if simplify:
        import sympy as sp
        expr = sp.simplify(expr)

    class FunctionClosure:
        """Closure to hold the function."""

        def __init__(self, f, isVec=False, isMat=False, extraArgs=None):
            self._f = f
            self._isVec = isVec
            self._isMat = isMat
            self._needExtraArgs = extraArgs
            # pg._g(f'Create isMat: {id(self)} {self._isMat}')

        @property
        def coefficients(self):
            """Coefficients for the functions.

            Coefficients are not necessary component variables
            like $x$, $y$, $z$, but needed for evaluation.
            """
            return self._needExtraArgs

        def __call__(self, *args, **kwargs):
            """pg.x(args[0])."""

            if 0:
                import inspect
                pg._b('_'*40)
                pg._g(f'isMat: {id(self)} {self._isMat}')
                pg._y(self._f)
                pg._g(f'args {args}')
                pg._y(f'kwargs {kwargs}')
                pg._g(inspect.getsource(self._f))
                pg._b('_'*40)

            if isinstance(args[0], pg.core.stdVectorR3Vector):
                return vectorizeEvalQPnts(self.__call__, args[0], **kwargs)

                # qp = args[0]
                # ret = pg.core.stdVectorRVector()

                # with pg.tictoc('fun.eval: f(vqp)'):
                #     vqp = pg.PosList()
                #     with pg.tictoc('qp->p'):
                #         pg.core.vectorizePosVectorList(qp, vqp)
                #     with pg.tictoc('call'):
                #         rf = self.__call__(vqp, **kwargs)
                #     with pg.tictoc('r->vr'):
                #         pg.core.deVectorizeRVectorToPosVectorList(ret, rf, qp)
                #     return ret

            if 't' in kwargs:
                kwargs['time'] = kwargs.pop('t')

            if 'time' in kwargs and hasattr(kwargs['time'], '__iter__'):
                kwargs['time'] = np.asarray(kwargs.pop('time'))

                pgx = pg.x(args[0])
                ### if [x] and [t] -> iterate for ([x], t_) with t_ in [t]
                if hasattr(pgx, '__iter__') and len(pgx) > 1:
                    kwt = kwargs.pop('time')
                    #pg._b(pgx, kwt)
                    return np.array([self(*args, time=t_, **kwargs)
                                     for t_ in kwt])

            extraArgs = []

            if self._needExtraArgs is not None:
                for k, v in self._needExtraArgs.items():
                    if k in kwargs:
                        extraArgs.append(kwargs[k])
                    else:
                        try:
                            if 'FEASolution_' in k:
                                from . feaSolution import FEASolutionStore
                                extraArgs.append(FEASolutionStore().get(k))
                            if k == 't':
                                extraArgs.append(kwargs['time'])
                            else:
                                ## extra args k is not exactly in kwargs
                                ## check if and kwargs is a symbol abbr. of k.
                                for kw in list(kwargs.keys()):
                                    ks = toSymbol(kw)
                                    if hasattr(ks, 'name') and ks.name == k:
                                        extraArgs.append(kwargs[kw])

                        except BaseException as e:
                            pg._r(e)
                            pg._r(args, kwargs)
                            pg._y(k, v)
                            pg._y('extra keyword arguments:'
                                   f'{self._needExtraArgs}')
                            pg.critical(f'Extra keyword arguments: {k}'
                                ' expected for call auto generated function.'
                                ' Either add this argument or substitute it'
                                ' before calling.')

            if len(extraArgs) != len(self._needExtraArgs.keys()):
                pg._b('+'*80)
                pg._b(f'called kwargs: {kwargs}')
                pg._y(self._f)
                pg._y(f'isVec={self._isVec}, isMat={self._isMat}')
                pg._g(inspect.getsource(self._f))
                pg._b(f'self._needExtraArgs: {self._needExtraArgs}')
                pg._y(f'extraArgs: {extraArgs}')
                pg._b('-'*80)
                pg.critical('Need some more extra arguments.')

            pnts = asPosListNP(args[0])
            x = pnts[:,0]
            y = pnts[:,1]
            z = pnts[:,2]

            if self._isVec:
                ### Returning function values are in R3
                try:
                    ## for < 2D this might throws a exception like:
                    ## return array([[0.18*Dummy_65], [0], [0]])
                    ## ValueError: setting an array element with a sequence.
                    ## The requested array has an inhomogeneous shape after
                    ## 2 dimensions.
                    ## The detected shape was (3, 1) + inhomogeneous part.
                    # pg._b(x, y, z, * extraArgs)

                    if len(extraArgs) > 0 and (hasattr(extraArgs[0],'__iter__')\
                                                and len(extraArgs[0]) > 0) and \
                       (x.shape[0] == 1 and y.shape[0] == 1 and z.shape[0] ==1):
                        ### time is iterable but pnt is scalar
                        ### (x, y, z, [time])

                        #isScalar(x) and isScalar(y) and isScalar(z):
                        #pg._r(x, y, z, * extraArgs)
                        ### (x, y, z, [t])
                        try:
                            ## might fail : see
                            # test_FEASolution_Interpolation (p=1, time=[1,2,3])
                            with pg.tictoc('sp.f3(x,y,z,[t])'):
                                ret = self._f(np.squeeze(x), np.squeeze(y),
                                            np.squeeze(z), *extraArgs).T
                            #ret = self._f(x, y, z, *extraArgs)
                            #pg._g(ret)
                        except ValueError:
                            #ret = np.asarray([self._f(x, y, z, t).T
                            #                   for t in extraArgs[0]])
                            with pg.tictoc('[sp.f3(x,y,z,t_i)]'):
                                ret = np.asarray([self._f(np.squeeze(x),
                                                        np.squeeze(y),
                                                        np.squeeze(z), t).T
                                                    for t in extraArgs[0]])
                            #pg._y(ret)
                            ### shape is already correct?
                            return np.squeeze(ret)
                    else:
                        ### time is scalar or 0
                        ### ([x], [y], [z], time|0)
                        #pg._b('##################   ')
                        try:
                            if self._isMat and len(pnts) > 0:
                                # fix new field here
                                with pg.tictoc('[sp.f3(x_i,y_i,z_i,t),]'):
                                    ret = np.squeeze([self._f(p_[0],
                                                            p_[1],
                                                            p_[2], *extraArgs)
                                                        for p_ in pnts])

                                if 'time' in kwargs and \
                                        hasattr(kwargs['time'], '__iter__') and\
                                        len(kwargs['time']) > 1:
                                    ret = np.array([np.squeeze(ret)] *
                                                    len(kwargs['time']))

                                return ret

                            else:
                                with pg.tictoc('sp.f3(x,y,z,t)'):
                                    ret = self._f(x, y, z, *extraArgs)
                            # pg._b('########### 1 ############')
                            # pg._b(ret)
                            # pg._g('shape:', ret.shape)

                            if ret.shape == (3,1,3) or ret.shape == (2,1,2):
                                ret = ret.T

                            # pg._y(ret)

                        except ValueError:
                            # f, gf = toFunctions(f='(-y*x, x**2)',gf='grad(f)')
                            # pg._g(gf([1.0, 2.0]))
                            # setting an array element with a sequence.
                            # The requested array has an inhomogeneous shape
                            # after 2 dimensions.
                            # The detected shape was(2, 2) + inhomogeneous part.
                            #ret = self._f(x, y, z, *extraArgs)
                            try:
                                with pg.tictoc('sp.f3(x,y,z)'):
                                    ret = self._f(np.squeeze(x),
                                                np.squeeze(y),
                                                np.squeeze(z), *extraArgs)

                                # pg._b('########### 2 ############')
                                # pg._b(ret)
                                # pg._g(ret.shape)

                            except ValueError:
                                # pg._b(x, y, z, * extraArgs)

                                # for i in range(len(x)):
                                #     print(self._f(x[i], y[i], z[i],
                                #                    *extraArgs))
                                with pg.tictoc('[sp.f3([x_i,y_i,z_i],t)]'):
                                    if self._isMat:
                                        ret = np.asarray([self._f(x[i],
                                                                  y[i],
                                                                  z[i],
                                                                  *extraArgs)
                                                    for i in range(len(x))]).T
                                    else:
                                        ret = np.asarray([self._f(x[i],
                                                                  y[i],
                                                                  z[i],
                                                                  *extraArgs)
                                                    for i in range(len(x))])

                                # pg._b('########### 3 ############')
                                # pg._b(ret)
                                # pg._g(ret.shape)

                    if self._isMat:
                        # ensure resulting dim is input dim ..
                        # needed for very simple functions

                        # pg._b(ret, ret.shape)
                        ## shape(2,2,1) : ret is 2D matrix (grad(v))
                        # for one pnt and assumed to be correct aligned
                        if ret.ndim == 3 and not ret.shape == (2,2,1):
                            ### old field style [NPts, (mat)]
                            ret = np.squeeze(ret.T)
                        ret = np.squeeze(ret)

                        #print(ret)
                        if len(pnts) > 1 and \
                                (ret.shape[0] < len(pnts) or ret.ndim < 3):
                            #pg._g(ret.shape, ret.ndim, len(pnts))
                            #ret = np.tile(ret.T, len(pnts)).T
                            ret = np.array([np.squeeze(ret)] * len(pnts))
                            #print(ret)

                        if 'time' in kwargs and \
                                hasattr(kwargs['time'], '__iter__') and \
                                len(kwargs['time']) > 1:
                            ## time is array and not extra arg so function
                            # may not depend on time
                            ## repeat matrix to fit desired input dimensions
                            ret = np.array([np.squeeze(ret)] *
                                            len(kwargs['time']))

                        # pg._b(f'## MAT FINAL to pnts: {len(pnts)} #########')
                        # pg._b(ret)
                        # pg._y(ret.shape)

                        return ret

                    ## no self._isMat
                    #
                    # ensure resulting dim is input dim ..
                    # needed for very simple functions
                    if ret.ndim == 2 and ret.shape[1] != len(pnts):

                        # pg._b(f'## FIX to pnts: {len(pnts)} ############')
                        # pg._b(ret)
                        # pg._y(ret.shape)

                        ret = np.array([np.squeeze(ret)] * len(pnts))

                        # pg._g(ret.shape)
                        return ret

                    ret = np.squeeze(ret) # remove unneeded empty dims

                    # pg._b(f'## FINALE SQUEEZE pnts: {len(pnts)} ############')
                    # pg._b(ret)
                    # pg._y(ret.shape, ret.ndim)
                    if ret.ndim == 1:
                        return ret

                    if len(pnts) > 1:
                        if len(pnts) == ret.shape[1] and \
                            len(pnts) != ret.shape[0]:
                            # add new field check
                            return ret.T
                        if len(pnts) == ret.shape[0] and \
                            len(pnts) != ret.shape[1]:
                            # add new field check
                            return ret

                    ### special case for one pnt. refactor me
                    # after switch to newFieldOrder
                    if ret.shape != (3,3) and \
                       ret.shape != (3,2) and \
                       ret.shape != (2,2):
                        return asVecField(ret)

                    #pg._g(ret.shape)

                    return ret
                    # print(np.squeeze(ret).shape)
                    # #print(np.asarray(ret))
                    # return self._f(x, y, z, *extraArgs).T[0]
                except ValueError as e:
                    print(e)
                    pg._y(ret.shape, ret.ndim)

                    pg._b(x, y, z, * extraArgs)

                    ret = np.asarray([self._f(x[i], y[i], z[i],
                                              *extraArgs).T[0]
                                      for i in range(len(x))])
                    ret = np.squeeze(ret) # remove unneeded empty dims

                    #pg._y(ret.shape)

                    if self._isMat:
                        return ret.T
                    return ret
                except BaseException as e:
                    pg._r(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)

            ### Returning function values are in R1
            if pg.isArray(args[0]) and not pg.isPos(args[0]):
                # pg._b('sp.f(x,0,0,*e)')
                # pg._b(x)
                # pg._b(*extraArgs)
                ret = None
                with pg.tictoc('sp.f(x,0,0,*e)'):
                    try:
                        ret = self._f(x, 0, 0, *extraArgs)
                    except TypeError:
                        ## possible lambda fails for
                        ## f([x], 0, 0, *args) -> iterate for x
                        ret = np.array([self._f(x_, 0, 0, *extraArgs)
                                        for x_ in x])

                if pg.isScalar(ret):
                    return np.full(len(args[0]), ret)
                else:
                    return ret
            with pg.tictoc('sp.f(x,y,z,*e)'):
                # pg._g('sp.f(x,y,z,*e)')
                # pg._g(x, y, z)
                # pg._g(self._needExtraArgs)
                # pg._g(*extraArgs)
                ret = None
                try:
                    ret = self._f(np.squeeze(x), np.squeeze(y), np.squeeze(z),
                                  *extraArgs)

                except ValueError as e:
                    ## possible lambdified fails for
                    ## f(x, y, z, [times], *args) -> iterate for all times
                    # pg._b('sp.f(x,y,z,*e)')
                    # pg._b(x, y, z)
                    # pg._b(self._needExtraArgs)
                    # pg._b(*extraArgs)
                    if len(extraArgs) > 0:
                        try:
                            tID = list(self._needExtraArgs.keys()).index('t')
                            if hasattr(extraArgs[tID], '__iter__') \
                                and len(extraArgs[tID]) > 0:

                                if len(extraArgs) == 1:
                                    ret = np.array([self._f(np.squeeze(x),
                                                            np.squeeze(y),
                                                            np.squeeze(z), t_)
                                                    for t_ in extraArgs[tID]])
                                else:
                                    ## we need to keep order of extraArgs but
                                    # exchange [t] with ti
                                    ex_ = list(extraArgs)

                                    def _extra(t):
                                        ex_[tID] = t
                                        return ex_

                                    ret = np.array([self._f(np.squeeze(x),
                                                            np.squeeze(y),
                                                            np.squeeze(z),
                                                            *_extra(ti))
                                                    for ti in extraArgs[tID]])
                        except ValueError as err:
                            pg._r(err)
                            pg.critical('no fixme!')
                    else:
                        pg._y(err)
                        pg._y('sp.f(x,y,z,*e)')
                        pg._y(x, y, z)
                        pg._y(self._needExtraArgs)
                        pg._y(*extraArgs)
                        pg.critical('fixme!')
                except TypeError as e:
                    #"only length-1 arrays can be converted to Python scalars"
                    #sp.f() accept only scalar args
                    try:

                        ret = np.array([self._f(x[i], y[i], z[i], *extraArgs)
                                            for i in range(len(x))])
                    except BaseException:
                        import traceback
                        traceback.print_exc(file=sys.stdout)
                        pg.critical('fix me!')

                    return ret

                except BaseException as e:
                    pg._r(type(e))
                    pg._r(e)
                    pg._r('sp.f(x,y,z,*e)')
                    pg._r(x, y, z)
                    pg._r(self._needExtraArgs)
                    pg._r(*extraArgs)

                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    pg.critical('fixme!')

                #return ret
                #pg._b(ret)
                if pg.isScalar(ret) and not pg.isScalar(args[0]) and \
                    not pg.isPos(args[0]):
                    return np.full(len(x), ret)

                return ret

            pg.critical('fixme .. I should not be here')

    with pg.tictoc('toFEAFunc'):
        # if name is None:
        #     name = str(expr)
        #name = str(expr)

        import sympy as sp
        from sympy import lambdify, Symbol
        from sympy.vector import CoordSys3D

        C = CoordSys3D('C', variable_names=['x', 'y', 'z'])

        if hasattr(expr, 'components'):

            comp = []
            if 1 or expr.components.get(C.i, 0) != 0:
                comp.append(expr.components.get(C.i, 0))

            if 1 or expr.components.get(C.j, 0) != 0:
                comp.append(expr.components.get(C.j, 0))

            if 0 or expr.components.get(C.k, 0) != 0:
                comp.append(expr.components.get(C.k, 0))

            ### maybe better use all components to ensure if its always in R3?
            expr = sp.Matrix(comp)
            isVec = True

        #dumpSP(expr)

        isMat = False
        #if isinstance(expr, (sp.matrices.immutable.ImmutableDenseMatrix)):
            # check if matrix is 1D then skip
            #print(expr.shape)
        if isinstance(expr, sp.matrices.MatrixBase) \
            and len(expr.shape) > 1 and expr.shape[0] > 1 and expr.shape[1] > 1:
                isMat = True
        # pg._y('isMat:', isMat)

        #TODO check sympy dynamic symbols for transient variables!!

        extra = {}
        #pg._b(expr)
        exprForLam = expr
        try:
            for fs in list(expr.free_symbols):
            #for fs in expr.atoms(Symbol):
                if not 'C.' in fs.name:
                    extra[fs.name] = fs

                if 'FEASolution_' in fs.name:
                    class FEASolEvaluator(sp.Function):
                        """Evaluate FEASolution for sympy lambda."""

                    C = sp.vector.CoordSys3D('C', variable_names=['x', 'y', 'z'])
                    solReplace = FEASolEvaluator(C.x, C.y, C.z, fs.name)
                    exprForLam = expr.xreplace({fs: solReplace})

        except BaseException:
            pass

        args = [Symbol('x'), Symbol('y'), Symbol('z')]
        args += list(extra.values())

        #pg._g('lamb args:', *args)
        mapping = {C.x: args[0],
                   C.y: args[1],
                   C.z: args[2]}

        def expLimited(x):
            if pg.isScalar(x):
                return np.exp(x)
            return np.exp(x, where=x<np.log(1e99), out=np.ones_like(x)*1e99)

        def evalSolution(x, y, z, sol):
            """Evaluate the solution."""
            return sol.eval([x, y, z])

        F_ = lambdify(args, exprForLam.xreplace(mapping),
                      modules=[{'exp': expLimited,
                                'FEASolEvaluator':evalSolution,
                               },
                               'numpy', 'scipy']
                      )
        #pg._b(expr)
        # import inspect
        # pg._g(inspect.getsource(F_))

        ## think about subclass FEAFunction3Sym(FEAFunction3) Why?
        if isVec is True:
            return FEAFunction3(FunctionClosure(F_, isVec=isVec, isMat=isMat,
                                                extraArgs=extra),
                                name=name, repr=expr)
        else:
            return FEAFunction(FunctionClosure(F_, isVec=isVec,
                                               extraArgs=extra),
                                name=name, repr=expr)

# Check if really not needed
# class Sym(FEAFunction3):
#     """
#     """
#     def __init__(self, v, **kwargs):
#         # pg.critical('in use?')
#         super().__init__(self, **kwargs)
#         self._v = v
#         self.evalOrder = v.evalOrder

#     def eval(self, *args, **kwargs):
#         # pg._b(*args, **kwargs)
#         # pg._b(type(self._v), self._v)
#         # if hasattr(self._v, 'mesh'):
#         #     s = self._v.eval(*args, **kwargs)
#         #     #pg._g(s)
#         #     # move index mess from mesh dependency to the grad
#         #     if s.ndim == 3:
#         #         #return np.asarray([sym(_s) for _s in s])
#         #         return np.asarray([sym(_s[0:self._v.mesh.dim(),
#                                       0:self._v.mesh.dim()]) for _s in s])
#         #     else:
#         #         s = s[0:self._v.mesh.dim(),0:self._v.mesh.dim()]
#         # else:
#         #     s = self._v.eval(*args, **kwargs)
#         # pg._g(s)
#         # pg._y(sym(s))
#         s = self._v.eval(*args, **kwargs)
#         return sym(s)


# class Trace(FEAFunction):
#     def __init__(self, v, **kwargs):
#         # pg.critical('in use?')
#         super().__init__(self, **kwargs)
#         self._v = v

#     def eval(self, *args, **kwargs):
#         s = self._v.eval(*args, **kwargs)
#         return trace(s)
