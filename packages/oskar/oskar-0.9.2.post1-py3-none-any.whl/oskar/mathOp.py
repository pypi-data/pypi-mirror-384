#!/usr/bin/env python
r"""Expressions and mathematical operators for functions and FEASpaces."""
import numpy as np
import pygimli as pg

from . feaFunction import FEAFunction, FEAFunction3, toFEAFunc
from . feaSpace import FEASpace, VectorSpace, hasFEASpace
from . feaSolution import FEASolution, FEASolutionOP, FEASolutionStore
from . feaOp import FEAOP, Derive, Dirac, Sym

from . op import OP, findInstance
from . utils import asPosListNP, getInstanceAssignmentName, dumpSP
from . units import ParameterDict


def derive(func, var=1, **kwargs):
    r"""Derive function for variable.

    Derive can be used for symbolic function or numeric functions.

    TODO
    ----
        * more examples
        * better doc

    Arguments
    ---------
    func: FEAFunction, FEAOP, FEASpace, FEASolution

        Derive a callable function object.

        - FEAFunction:
            Derive symbolic via :term:`SymPy` or numerical
            via :term:`numdifftools` depending on the origin of the FEAFunction.

        - FEASolution:
            Derive numerical.

    var: int, str
        Variable to derive for. String for symbolic functions or integer for
        numeric functions.

    Keyword Args
    ------------
    simplify: bool[True]
        Simplify sympy expression if possible.

    Example
    -------
    >>> from oskar import asFunction, pprint
    >>> f = asFunction('x²')
    >>> df = derive(f, 'x')
    >>> pprint(df)
    df(x) = 2*x
    >>> print(df(2))
    4.0
    >>> df = derive(f, 1, numeric=True)
    >>> print(np.round(df(2), 12))
    4.0
    """
    if hasattr(func, 'hasSympy') and func.hasSympy() and \
        kwargs.pop('numeric', False) is not True:

        import sympy as sp
        from sympy.vector import CoordSys3D
        C = CoordSys3D('C')
        # pg._b(func, var)
        # dumpSP(func._sympy_())

        if isinstance(var, FEASolution):
            var = FEASolutionStore().name(var)
        #pg._r(var)

        if isinstance(var, str):
            if var == 'x':
                var = C.x
            elif var == 'y':
                var = C.y
            elif var == 'z':
                var = C.z
            else:
                for s in func.sympy().free_symbols:
                    if s.name == var:
                        #pg._y(s, var)
                        # s._assumptions['real'] = True
                        # s._assumptions['complex'] = False
                        # s._assumptions['imaginary'] = False
                        s._assumptions['extended_real'] = True
                        var = s
                        break


        # h,g = sp.symbols('h g', real=True)
        # pg._g(h._assumptions)
        # K = abs(h)**g
        # print(K)
        # print(sp.diff(K, h))

        # pg._b(var)
        # pg._y(var._assumptions)
        # pg._b(func.sympy())
        expr = sp.diff(func.sympy(), var)
        #pg._g(expr)

        return toFEAFunc(expr,
                          name=getInstanceAssignmentName(),
                          isVec=False,
                          simplify=kwargs.get('simplify', True))

    if isinstance(func, (FEASpace)):
        return Derive(func, var)

    if 1 and isinstance(func, FEASolutionOP):
        u = findInstance(func, FEASolution)
        dVar = 1e-6
        method = kwargs.pop('method', 'central')
        if method == 'forward':
            return (1/dVar) * (func.subst(u, u + dVar) - func)
        if method == 'backward':
            return (1/dVar) * (func - func.subst(u, u - dVar))
        if method == 'central':
            return (func.subst(u, u + dVar) - func.subst(u, u - dVar)) / (2*dVar)

    if (callable(func)
        and isinstance(var, FEASolution | pg.Vector | np.ndarray)) \
        or (hasattr(var, 'hasSympy') and var.hasSympy()):

        #pg._b()
        dVar = 1e-6
        method = kwargs.pop('method', 'central')
        if method == 'forward':
            return (1/dVar) * (func(var + dVar) - func(var))
        if method == 'backward':
            return (1/dVar) * (func(var) - func(var - dVar))
        if method == 'central':
            return (func(var + dVar) - func(var - dVar)) / (2*dVar)

    if isinstance(func, FEAFunction):
        import numdifftools as nd
        if var == 'x':
            var = 1
        elif var == 'y':
            pg.critical('in use?')
            var = 2 # wrong would mean secind derivative
        elif var == 'z':
            pg.critical('in use?')
            var = 3 # wrong would mean third derivative
        return FEAFunction(nd.Derivative(func, n=var),
                           #repr=f'derive({func}, {func._v})',
                           field=func)

    import sympy
    if isinstance(func, sympy.core.expr.Expr | sympy.core.symbol.Symbol):
        pass
        # will not work .. we need custom object of derive as placeholder
        # for symbolic sympy syntax until it reaches lambdify

        # class Derive:
        #     def __init__(self, e):
        #         self.e = e

        #     def _sympy_(self):
        #         return derive({self.e})

        # return Derive(s)
        # pg._b(s)

        # from sympy import parse_expr, lambdify, Matrix, diff
        # from sympy.vector import CoordSys3D, gradient, divergence

        # C = CoordSys3D('C')
        # loc = {}
        # loc.update({ 'x': C.x,
        #          'y': C.y,
        #          'z': C.z,
        #          'div': divergence,
        #          'grad': gradient,
        #          'derive': diff,
        #          })

        # l = lambdify([loc['x'], loc['y'], loc['z']], s)

        # import numdifftools as nd
        # return FEAFunction(nd.Derivative(l, n=n))
        # return toFEAFunc(s, isVec=False)

        # return toFEAFunc(s, isVec=False)

    pg._r(type(func), func)
    pg._r(type(var), var)
    pg.critical('implement me')


def div(func, **kwargs):
    r"""Create divergence for vector function.

    Divergence for function `func` representing vector field
    :math:`\boldsymbol{u}=\{u_i\}\in\mathbb{R}^n, i = 1,\ldots,n` .

    .. math::
        \operatorname{div}(\boldsymbol{u})=
        \nabla\cdot \boldsymbol{u} =
        \sum_i^{\operatorname{n}} \frac{\partial u_i}{\partial x_i} \\

    TODO
    ----
        * Doc for tensor div
        * example

    Arguments
    ---------
    func: FEASpace, FEASolution, FEAFunction, FEAFunction3

        A callable function object.

        - FEAFunction:
            Create divergence symbolic via :term:`SymPy` or numerical
            via :term:`numdifftools` depending on the origin of the FEAFunction.

    Keyword Args
    ------------
    simplify: bool[True]
        Simplify sympy expression if possible.

    **kwargs
        Will be forwarded to func.eval().

    Returns
    -------
        Function object of base type OP that can be evaluated depending on func.

    Example
    -------
    >>> from oskar import asFunction, pprint
    """
    import sympy as sp

    u = None

    if isinstance(func, sp.MatrixBase):
        u = func

    if u is not None \
        or (isinstance(func, FEAFunction)
            and hasattr(func, 'hasSympy') and func.hasSympy()
            and kwargs.pop('numeric', False) is not True):

        simplify = kwargs.pop('simplify', True)

        from sympy.vector import CoordSys3D

        C = CoordSys3D('C')

        def _SPtensorDiv(u):
            """Return divergence for tensor of type 2.

                return [du_i_x/d_x + du_i_y/dy + du_i_z/dz] i = 1..dim
            """
            # pg._r('** Symbolic tensor div **')
            # pg._y(u)

            dim = u.shape[0]
            ret = sp.zeros(1, dim)
            x = [C.x, C.y, C.z]

            for i in range(dim):
                for j in range(dim):
                    ret[i] += sp.diff(u[i, j], x[j])

            return ret

        u = func.expr if u is None else u

        if hasattr(u, 'shape'):
            if len(u.shape) == 2 and u.shape[1] > 1:
                #s is tensor 2 matrix [], e.g. grad(VectorSpace)
                return toFEAFunc(sp.simplify(_SPtensorDiv(u)),
                                    name=getInstanceAssignmentName(),
                                    isVec=True, simplify=simplify)

            dim = u.shape[0]
            x = [C.x, C.y, C.z]

            ret = sp.diff(u[0], x[0])
            for i in range(1,dim):
                ret += sp.diff(u[i], x[i])

            return toFEAFunc(sp.simplify(ret),
                                name=getInstanceAssignmentName(),
                                isVec=False, simplify=simplify)

        ## assuming 1d here
        return toFEAFunc(sp.simplify(sp.diff(u)),
                            name=getInstanceAssignmentName(),
                            isVec=False, simplify=simplify)

    def _haveGrad(o):
        """Check if o have an own grad op."""
        # pg._y(f'{o.a} OP: {o.op}, {o.a}')

        try:
            if o.op == 'grad':
                return True
        except BaseException:
            return False

        #pg._r(f'{o.a} OP: {o.op}, {o.a}')
        return _haveGrad(o.a) or _haveGrad(o.b)

    if isinstance(func, FEAOP) and _haveGrad(func):
        #pg._r(type(func), func, _haveGrad(func))
        #from .solve import Div
        return Div(func)

    return func.div()


def grad(func:any, **kwargs):
    r"""Create function that calculates the gradient of a function.

    .. math::
        \operatorname{grad}(u)=
        \nabla u =
        \sum_i^{\operatorname{dim}}
        \frac{\partial u}{\partial x_i}\boldsymbol{e}_i \\

    TODO
    ----
        * more examples
        * better doc

    Arguments
    ---------
    func: FEASpace, FEASolution, FEAFunction, FEAFunction3

        A callable function object.

        - FEAFunction:
            Create gradient symbolic via :term:`SymPy` or numerical
            via :term:`numdifftools` depending on the origin of the FEAFunction.

        - FEASolution:
            Create gradient numerical using the underlying FEASpace.
            Note, due to the nature of the finite element theory, the resulting
            gradients will be constant within each cell for 'p=1' base functions
            and have a linear behavior for 'p=2'.

    Keyword Args
    ------------
    simplify: bool[True]
        Simplify sympy expression if possible.

    **kwargs
        Will be forwarded to func.eval().

    Returns
    -------
        Function object of basetype OP that can be evaluated depending on func.

    Example
    -------
    >>> from oskar import asFunction, pprint
    >>> f = asFunction('x² + y² + z²')
    >>> df = grad(f)
    >>> pprint(df)
    df(x,y,z) = Matrix([[2*x], [2*y], [2*z]])
    >>> print(df([1, 2, 3]))
    [2 4 6]
    """
    if 1 and isinstance(func, FEASolutionOP):
        ## chain rule only works if func contains only one derivable
        ## TODO:
        ##   * count for multiple different FEAFunction and FEASolutions
        f = findInstance(func, FEAFunction)
        u = findInstance(func, FEASolution)
        if f is not None and u is not None:
            pass
        else:
            return derive(func, u)*grad(u)

    if hasattr(func, 'op') and func.op != None:
        if func.op == '-':
            return grad(func.a) - grad(func.b)
        if func.op == '+':
            return grad(func.a) + grad(func.b)
        if func.op == '*':
            # check value sizes -- only for a and b in R1
            pg.critical('in use?')
            return grad(func.a) * func.b + func.a * grad(func.b)
        pg._y(func)
        pg._y(func.op)
        pg.critical("Implement me")

    ## FEAOperator
    # if 0 and isinstance(func, (FEASolution, FEASolutionOP)):
    #     return SolutionGrad(func, **kwargs, name=f'grad({s})')

    def _spGrad(u, **kwargs):
        """Return sympy grad variant for u."""
        with pg.tictoc('grad.sp.grad'):
            keepDim = kwargs.pop('keepDim', False)

            import sympy as sp
            from sympy.vector import CoordSys3D, gradient
            #u = s.expr

            if hasattr(u, 'components') or hasattr(u, 'shape') \
                and u.shape[0] > 1:

                #pg._g(type(u), u)
                C = CoordSys3D('C')
                try:
                    uM = u.to_matrix(C)
                    dim = len(uM)
                    if u.components.get(C.k, 0) == 0:
                        dim = 2
                except:
                    uM = u
                    dim = len(uM)

                    #if keepDim is True:
                    #     if uM[2] == 0:
                    #         dim = 2

                expr = sp.Matrix([gradient(ui).to_matrix(C)[:dim]
                                        for ui in uM[:dim]])
            else:
                #pg._g(u)
                expr = gradient(u)
                #pg._y(expr)
            return expr

    # TODO: think of moving this to FEAFunction.grad()
    if isinstance(func, FEAFunction):

        if 1 and hasattr(func, 'hasSympy') and func.hasSympy() and \
            kwargs.pop('numeric', False) is not True:
            return toFEAFunc(_spGrad(func.sympy(), **kwargs),
                              name=getInstanceAssignmentName(),
                              isVec=True,
                              simplify=kwargs.get('simplify', True))

        ## FEAFunction with prior expression

        simple = kwargs.pop('simple', False)

        if simple is True:
            #pg._b('simple')
            ##// refactor with FEAFunction3
            class _SimpleGrad(object):
                def __init__(self, func, **kwargs):
                    self._funct = func
                    self._method = kwargs.pop('method', 'forward')

                def __call__(self, *args, **kwargs):

                    p = asPosListNP(args[0])
                    #print(p)
                    #duN = np.zeros_like(px)

                    dx = 1e-5

                    u = self._funct
                    if self._method == 'forward':

                        up = u(p)
                        #pg._g(up)
                        #pg._g(p+[dx, 0, 0])
                        upx = u(p + [dx, 0, 0])
                        #pg._y(upx)
                        upy = u(p + [0., dx, 0])
                        upz = u(p + [0., 0, dx])
                        return (np.array([upx, upy, upz]) - up)/dx

                    elif self._method == 'backward':
                        up = u(p)
                        upx = u(p - [dx,  0,  0])
                        upy = u(p - [0., dx,  0])
                        upz = u(p - [0.,  0, dx])

                        return (up - np.array([upx, upy, upz]))/dx

                    elif self._method == 'central':
                        upxF = u(p + [dx,  0,  0])
                        upyF = u(p + [0., dx,  0])
                        upzF = u(p + [0.,  0, dx])
                        upxB = u(p - [dx,  0,  0])
                        upyB = u(p - [0., dx,  0])
                        upzB = u(p - [0.,  0, dx])

                        return (np.array([upxF-upxB,
                                          upyF-upyB,
                                          upzF-upzB]))/(2*dx)

                    pg.critical("Don't know how to handle method: "
                                f"{self._method}")

            ##!! refactor into common GradientFunctor and/or derive
            ## to avoid holding s for symbolic calculations
            ##
            ##
            #pg._b('simple grad f')
            return FEAFunction3(_SimpleGrad(func, **kwargs),
                                repr=f'grad({func})', field=func)

        else:
            import numdifftools as nd
            #pg._b('numdifftools')
            return FEAFunction3(nd.Gradient(func, **kwargs),
                                repr=f'grad({func})', field=func)

    ### fallback for all OP
    if hasattr(func, 'grad'):
        # pg._b('func.grad()')
        return func.grad()

    try:
        ## used by parse for sympy gradient directly
        return _spGrad(func)
    except BaseException as e:
        print(e)
        print(type(func))
        print(func)
        pg.critical("Don't know how to build gradient.")


def laplace(s, **kwargs):
    r"""Create Laplace of s.

    This is just a shortcut for:

    .. math::

        \Delta s =\:& \nabla\cdot\nabla s\\[8pt]
        \:&\text{with} \\
        \Delta =\:& \nabla\cdot\nabla=
        \sum_1^{\text{dim}}\frac{\partial^2}{\partial x_i^2}

    Arguments
    ---------
    func: FEASpace, FEASolution, FEAFunction

        A callable function object.

    Keyword Args
    ------------
    simplify: bool[True]
        Simplify sympy expression if possible.

    Returns
    -------
        Operator for `div(grad(s))`.

    """
    return div(grad(s,**kwargs), **kwargs)


def norm(s=None):
    """Create a function for the norm for space s."""
    if isinstance(s, pg.Mesh):
        s = FEASpace(s)
        pg.critical('in use?')
        return s.norm()

    if isinstance(s, VectorSpace):
        ## check if necessary!
        return s.norm()

    ## better variant with special class
    from . feaFunction import FEAFunctionDotNorm
    return FEAFunctionDotNorm(None, name='_')


def sym(s, **kwargs):
    """Return symmetry of s."""
    ## FEAOperator
    #pg._b(s)

    if isinstance(s, FEAOP) \
        and (hasattr(s, '_solutionGrad') and s._solutionGrad is True):
        # TODO refactor with SolutionGrad
        return Sym(s)
        pg.critical('shouldNotBeHere')
        #return sym(eps(s))

    if hasattr(s, 'sym'):
        return s.sym()

    if isinstance(s, FEAFunction3):
        if 1 and hasattr(s, 'expr') and s.expr != '':
            return toFEAFunc(sym(s.expr, **kwargs),
                              name=getInstanceAssignmentName(),
                              isVec=True)
        return Sym(s, name=f'sym({s})')

    ## RMatrix and ndarray
    if hasattr(s, 'ndim') and s.ndim == 2 and s.shape[0] == s.shape[1]:
        return 0.5 * (s + s.T)

    if hasattr(s, 'ndim') and s.ndim == 3 and s.shape[1] == s.shape[2]:
        return np.asarray([sym(s_) for s_ in s])

    ## Default, e.g. sympy expression itself
    try:
        return 0.5 * (s + s.T)
    except BaseException as e:
        print(e)
        pg._r(type(s))
        pg.critical(f"Don't know how to symmetrize s: {s}")


def tr(x):
    """Create trace for x.

    Shortcut for :py:mod:`oskar.mathOP.trace`.
    """
    return trace(x)


def trace(x, **kwargs):
    """Create trace for x with tr = sum(diag(x)).

    Arguments
    ---------
    x: np.array, list, FEAOP
    """
    ### move to newFEA.py
    if isinstance(x, FEASolution):
        pg.critical('shouldNotBeHere')
        #return tr(eps(x))

    if isinstance(x, FEAFunction3):
        if 1 and hasattr(x, 'expr') and x.expr != '':
            return toFEAFunc(trace(x.expr, **kwargs), isVec=True)
        return Trace(x, name=f'trace({x})')

    if isinstance(x, FEAOP):
        return x.tr()

    ### quadratic matrix
    if isinstance(x, np.ndarray) and x.ndim == 2 and x.shape[0] == x.shape[1]:
        return np.trace(x)

    ### np.array | list of matrices
    if isinstance(x, (np.ndarray, list)) and x[0].ndim == 2:
        return np.squeeze(np.trace(x, axis1=1, axis2=2).reshape((len(x), 1)))

    # pg._b(x)
    # pg._b(type(x))
    if 'sympy.' in str(type(x)):
        import sympy as sp
        return sp.simplify(x.trace())

    ### flatten matrices or list|np.array of flatten matrices
    if len(x) == 3 and pg.isScalar(x[0]):
        ## 2D single flatten VoigtMapping
        # x = [xx, yy, xy]
        return x[0] + x[1]
    elif len(x) == 4 and pg.isScalar(x[0]):
        ## 2D single matrix flatten
        # x = [xx, xy, yx, yy]
        return x[0] + x[3]
    elif len(x) == 6 and pg.isScalar(x[0]):
        ## 3D single flatten VoigtMapping
        # x = [xx, yy, zz, xy, yz, xz]
        return x[0] + x[1] + x[2]
    elif len(x) == 9 and pg.isScalar(x[0]):
        ## 3D single matrix flatten
        # x = [xx, xy, yz, yx, yy, yz, zx, zy, zz]
        return x[0] + x[4] + x[8]
    elif len(x[0]) == 3 or len(x[0]) == 4:
        ## iterable of flatten matrices -> need (shape = [[],[]].T (N, 1))
        return np.array([[trace(e)] for e in x])

    pg._y(x)
    pg._g(x[0])
    pg._r('check whats this and comment type')
    pg.critical('implement me')


def dirac(s=None, rs=None, t0=None, **kwargs):
    r"""Dirac operator.

    .. math::

        \delta(\mathbf{r}-\mathbf{r}_{\mathrm s}, t-t_0)

    TODO
    ----
        * Explain cellScale by example

    Keyword Args
    ------------
    s: FEASpace [optional]
        Give FEA space. Need check if really needed. Might be removed in
        the future.

    rs: [x,y,z]
        Source position :math:`r_{\mathrm s}`. If :math:`r_{\mathrm s}`
        is not given.
        Dirac becomes :math:`\delta(t-t_{\mathrm s})` and so
        independent of position.

    t0: float
        Time for dirac impulse. If :math:`t` is not not given. Dirac becomes
        steady :math:`\delta(\mathbf{r}-\mathbf{r}_{\mathrm s})`.

    cellScale: bool [False]
        Weight the resulting assembling by the size of the cell where the dirac
        impulse is located.
    """
    return Dirac(rs=rs, t0=t0, space=s, **kwargs)


class I(FEAFunction3):
    """Identity operator."""

    def __init__(self, dim=None, **kwargs):
        """Create identity matrix operator function.

        Arguments
        ---------
        dim: int, FEASolution, FEAFunction, FEASpace
            Scalar dimension will be evaluated from argument.

        """
        super().__init__(self, **kwargs)

        if isinstance(dim, FEASpace):
            #pg._b()
            self._space = dim

        ### identify dimension of I from argument
        if hasattr(dim, 'shape'):
            if dim.ndim == 2:
                #! not! __newFieldOrder__
                self._dim = dim.shape[1]
            else:
                self._dim = 3

        elif isinstance(dim, FEAFunction) and dim.hasSympy():
            import sympy as sp

            if isinstance(dim.expr, sp.MatrixBase):
                self._dim = dim.expr.shape[0]
            else:
                self._dim = 3
        else:
            self._dim = dim

        self._isNeg = False


    def __hash__(self):
        """Return hash of I."""
        from pygimli.utils.cache import valHash
        return valHash((self.__class__, self._dim, self._isNeg))


    def __str__(self):
        """Return string representation of I."""
        return f'I({self._dim})'


    def __mul__(self, b):
        """Multiplication of I with b."""
        # pg._b('I.mul:', type(b), b)
        return self.__rmul__(b)


    def __rmul__(self, b):
        """Right side multiplication of I with b."""
        # pg._b('I.rmul:', type(b), b)

        def _retNegCheck(obj):
            """Check if the operator is negative."""
            if self._isNeg:
                return -obj
            return obj

        ## Forward I * sol -> solutionOP
        if isinstance(b, FEASolution | FEASolutionOP):
            return _retNegCheck(FEASolutionOP(b, self, '*'))

        if isinstance(self._dim, FEASpace | FEAOP):
            return _retNegCheck(b * identity(self._dim))

        from .feaSolution import SolutionGrad
        if isinstance(b, SolutionGrad):
            return _retNegCheck(OP(b, self, '*'))

        if isinstance(b, FEAFunction) and b.hasSympy():
            if self._isNeg:
                pg.critical('implement me')

            I = identity(b.expr, dim=self._dim)
            import sympy as sp

            if isinstance(b.expr, (sp.matrices.MatrixBase)):
                ## Matrix * I is supposed to be element wise ..
                # else I would be ONE and meaningless
                return toFEAFunc(
                    sp.matrices.dense.matrix_multiply_elementwise(b.expr, I),
                    isVec=True)

            return toFEAFunc(b.expr*I, isVec=True)

        if isinstance(b, np.ndarray):
            return _retNegCheck(b * identity(self._dim))

        #pg._b(f'b * identity(b, dim={self._dim})')

        return _retNegCheck(b * identity(b, dim=self._dim))


    def eval(self, *args, **kwargs):
        """Evaluate identity operator."""
        if pg.core.deepDebug() == -1:
            pg._y('*'*60)
            pg._y('** Identity eval')
            pg._y('at:', args, kwargs)
            pg._y('*'*60)

        #return identity(self._dim)
        # pg._b(*args)
        # pg._b(**kwargs)
        pnts = []

        if len(args) > 0:
            pnts = asPosListNP(args[0])
        else:
            pg.critical('implement me')

        dim = kwargs.pop('dim', None)

        if dim is None:
            dim = self._dim

        #pg._r(dim)

        return np.asarray([identity(dim)]*len(pnts))


    def __neg__(self):
        """Negate the identity operator."""
        #refactor!!
        self._isNeg = True
        return self
        #return self._OP(self, op='neg')


def identity(s, **kwargs):
    """Create identity for s.

    TODO
    ----
        * example and sort args

    Arguments
    ---------
    s: np.array, list, FEAOP, FEASolution, int

        Create identity representation for:

        - np.array
            I for 2D constitutive matrix for `len(s) == 3`
            `len(s) == 4` 2d matrix
        - list
            list of np.ndarray
        - FEAOP
            Create expression of `s` to create identity matrix.
        - int
            Create simple identity matrix of dim `s`
    """
    #pg._b('identity', s, kwargs)
    if isinstance(s, (FEAOP)):
        if len(list(s.spaces)) != 1:
            print(list(s.spaces))
            pg.critical("should not be here, implement me!")

        #pg._b(list(s.spaces)[0].identity(), type(list(s.spaces)[0].identity()))
        return list(s.spaces)[0].identity()

    # if hasattr(s, 'space'):
    #     pg._b(s.space.identity(), type(s.space.identity()))
    #     return s.space.identity()

    if isinstance(s, (FEASpace)):
        return s.identity()

    from .feaSolution import SolutionGrad

    if isinstance(s, SolutionGrad):
        dim = kwargs.pop('dim', None)
        pg._b(dim, s.mesh.dim())
        if dim is None:
            dim = s.mesh.dim()
        pg._b(dim, s.mesh.dim())
        return np.diag(np.ones(dim))

    if isinstance(s, FEAFunction3):
        # if 1 and hasattr(s, 'expr') and s.expr != '':
        #     return toFEAFunc(s.expr*I(s.expr), **kwargs),
        #                       name=f'tr({s})', isVec=True)
        pg.critical('implement me')
        #return Trace(s, name=f'trace({s})')

    ### find identity for symbolic expressions
    if 'sympy.' in str(type(s)):
        import sympy as sp

        dim = kwargs.pop('dim', None)

        if isinstance(dim, FEAFunction3) and dim.hasSympy():
            if isinstance(dim.sympy(), sp.MatrixBase):
                dim = dim.sympy().shape[0]
            else:
                pg._b(type(s))
                pg._b(s)
                pg.critical('implement me')

        elif isinstance(dim, FEASolution):
            #! not! __newFieldOrder__
            pg.critical('in use?')
            dim = dim.shape[1]

        if dim is None:
            if isinstance(s, sp.MatrixBase):
                dim = s.shape[0]
            else:
                dim = 3
                # pg._b(type(s))
                # pg._b(s)
                # pg.critical('implement me')

        return sp.eye(dim)

    # any in use?
    # print('__ identity')
    # print(s)
    # print(pg.isArray(s), isinstance(s, list), type(s))
    if isinstance(s, int):
        return np.diag(np.ones(s))

    if (not hasattr(s, '__iter__') or isinstance(s, ParameterDict)) \
        and 'dim' in kwargs:

        return identity(kwargs['dim'])

    #pg._b(type(s),  s)
    if not isinstance(s, list) and s.ndim == 1:
        if len(s) == 3:
            # assume s is [xx, yy, xy]
            return np.array([1.0, 1.0, 0.0])
        if len(s) == 4:
            # assume s is [xx, xy, yx, yy]
            return np.array([1.0, 0.0, 0.0, 1.0])

    if not isinstance(s, list) and s.ndim == 2:
        if s.shape == (2,2):
            ## assume s is [[[xx, xy],[yy, yx]]],
            return np.diag(np.ones(2))
        elif s.shape == (3,3):
            ## assume s is [[[xx, xy, xz],[yx, yy, yx], [zx, zy, zz]]],
            return np.diag(np.ones(3))

    if isinstance(s, np.ndarray) and not isinstance(s, FEASolution):
        if s[0].ndim == 2:
            return np.array([identity(si) for si in s])

        if len(s[0]) == 3 or len(s[0]) == 4 or s[0].ndim == 2:
            return np.array([identity(si) for si in s])
            return np.diag(np.ones(2))
            #return np.diag(np.ones(2))

        pg._r('############')
        print(s)
        pg.critical('implement me')

    if isinstance(s, list):
        return np.array([identity(si) for si in s])

    # pg._r("Identity for ", type(s))
    return s.identity()


def dev(x):
    """Create deviatoric part of constitutive matrix.

    TODO
    ----
        1D, 3D

    Arguments
    ---------
    s: np.array, list, FEAOP, FEASolution
        * FEAOP: Return function to be evaluated
        * ndarray: Return calculated matrices
    """
    if isinstance(x, FEAOP):
        return x - identity(x) * trace(x)/2

    ret = []
    tr = trace(x)

    for i, e in enumerate(x):
        if len(e) == 3:
        # deviatoric  only for list of 2d constitutive matrices
        # return should be flatten
            ret.append([e[0]-tr[i][0]/2, e[2],
                        e[2], e[1]-tr[i][0]/2])
        elif len(e) == 4:
        # 2d full eps matrix
        # return should be flatten
            ret.append([e[0]-tr[i][0]/2, e[1],
                        e[2], e[3]-tr[i][0]/2])

        else:
            print(x)
            print(x[0])
            pg.critical('implement me')

    return np.array(ret)


def integrate(func, d:str=None, limits=None, **kwargs):
    """Integrate function.

    Create a function of the integration of `func` regarding `var` with
    symbolic or numeric integration depending on function `func`.

    Arguments
    ---------
    func: str|FEAFunction|FEASolution
        Function to integrate.
        `func` is of type str is converted to FEAFunction.

    d: str, list(str)
        Differential `d` to integrate for.
        If `d` is a list, integrate is called for each.

    limits: [a, b], [[a,b],]
        With `a` and `b` integration limits, or list of for multiple integrals
        and can be scalar or strings.

    Keyword Args
    ------------
    simplify: bool[True]
        Simplify sympy expression if possible. Use with care.
    symbolic: bool[True]
        Apply symbolic integration on default, or use
        scipy.quad if set to False.

    Returns
    -------
    FEAFunction

    """
    if isinstance(func, str):
        from .solve import asFunction
        func = asFunction(func)

    if isinstance(d, list):
        if limits:
            if len(d) != len(limits):
                pg._r(d)
                pg._r(limits)
                pg.critical('Please provide limits for each differential.')
        else:
            limits = [None]*len(d)

        I = integrate(func, d=d[0], limits=limits[0])
        for i, di in enumerate(d[1:]):
            I = integrate(I, d=di, limits=limits[i+1])
        return I

    if isinstance(func, FEAFunction) and func.hasLambdified:
        import sympy as sp
        if d:
            from .solve import asFunction
            d = asFunction(d)
            if limits:
                if isinstance(limits[0], str):
                    a = asFunction(limits[0])
                else:
                    a = limits[0]
                if isinstance(limits[1], str):
                    b = asFunction(limits[1])
                else:
                    b = limits[1]

                intFunc = sp.Integral(func.expr, (d, a, b))
            else:
                intFunc = sp.Integral(func.expr, (d, None, None))
        else:
            intFunc = sp.Integral(func.expr)

        symbolic = kwargs.pop('symbolic', True)

        doit_flags = kwargs
        # {
        #             'deep': False,
        #             'INT TYPE':
        #             'manual': None
        #             }

        if symbolic:
            intFunc = intFunc.doit(**doit_flags)
            # TODO. simplify=False as default but
            # plot_20_mes_heat_equation.py:'Nonhomogeneous heat equation –
            # Continuous injection at singular source' fails with simplify=False
            #
            simplify = True
        else:
            simplify = False

        return toFEAFunc(intFunc,
                          name=getInstanceAssignmentName(),
                          simplify=kwargs.pop('simplify', simplify)
                          )

    else:
        pg._r(func, isinstance(func, FEAFunction), func.hasLambdified)
        pg.critical('implement me')


def isStrongFormPDE(L):
    """Check if a expression is a PDE in strong form."""
    terms = OP.expandTerm(L)

    if hasattr(L, 'op') and L.op == '==' \
        and (isinstance(L.a, PDE) or isinstance(L.b, PDE)):

        return True

    for t in terms:
        if not pg.isScalar(t, 0):

            if isinstance(t, PDE):
                return True

            if not hasFEASpace(t):
                # no space terms so probably not a weak form
                return True

    # if hasattr(L, 'op') and L.op == '*':
    #     if hasSpace(L.a) and hasSpace(L.b):
    #         return False
    ## count spaces

    return False


class PDE(OP):
    """Class for PDE expressions.

    This class is used to create PDE expressions in the weak form.
    """

    def __init__(self, a=None, b=None, op=None):

        if isinstance(a, OP) and b is None and op is None:
            # print(a, b, op)
            # a.dump()
            op = a.op
            b = a.b
            a = a.a

        self._space = None

        if isinstance(a, FEASpace):
            self._space = a
        elif hasattr(a, '_space'):
            self._space = a._space
        elif hasattr(a, 'spaces'):
            if len(a.spaces) == 1:
                self._space = list(a.spaces)[0]
            else:
                if hasattr(b, '_space'):
                    self._space = b._space
                else:
                    print(a.spaces)
                    pg.critical('implement me')

        self.neg = False
        self.testFunc = None

        super().__init__(a=a, b=b, op=op, OP=PDE)

        #pg._y('create:', self)
        if (hasattr(a, 'testFunc')):
            self.testFunc = self.a.testFunc
        elif (hasattr(b, 'testFunc')):
            self.testFunc = self.b.testFunc

        # if not isinstance(space, FEASpace):
        #     print(space)
        #     pg.critical('space need to be of type FEASpace')
        # self.space = space


    def __hash__(self):
        """Hash for FEAOP."""
        return super().__hash__() ^ hash(self.space)


    @property
    def space(self):
        """Return associated FEASpace."""
        return self.findSpace(self)


    def findSpace(self, pde=None):
        """Recursive search for associated FEASpaces."""
        #pg._b(pde, type(pde))
        if pde is None:
            return None

        identity = findInstance(pde, I)
        if identity is not None:
            #pg._b('I found')
            return identity._space

        if isinstance(pde, FEAFunction | FEASolution | FEASolutionOP):
            return None

        if hasattr(pde, "_space") and pde._space is not None:
            return pde._space

        if hasattr(pde, "needsAssembling") and not pde.needsAssembling():
            return None

        if isinstance(pde, FEASpace):
            return pde

        if hasattr(pde, "a"):
            a = self.findSpace(pde.a)
            if a is not None:
                pde._space = a
                #pde._space = a._space
                return a

        if hasattr(pde, "b"):
            #pg.critical('in use?')
            b = self.findSpace(pde.b)
            if b is not None:
                pde._space = b
                #pde._space = b._space
                return b

        return None


    def createWeakForm(self, indent=0, **kwargs):
        """Create finite element formulation of the weak formulation."""
        #pg._b(self)

        def _toWeak(t):
            # pg._r(t, type(t),
            #       ' neg:', hasattr(t, 'neg') and t.neg is True,
            #       'hasOP:', hasattr(t, 'op'),
            #       )
            if hasattr(t, 'weak'):
                #pg._g(t.weak())
                return t.weak()

            if hasattr(t, 'neg') and t.neg is True:
                # remove negs
                pg._g(-t)
                pg._r('i use?')
                return -_toWeak(-t)

            if hasattr(t, 'op') and t.op == 'neg':
                ## neg(FEASolution) -> -FEASolution
                ret = _toWeak(t.a)
                if ret is not None:
                    return -ret
                return None

            if hasattr(t, 'op') and t.op == 'div':
                ## special case for div( a*I(v) )-> grad(v)*a*I
                identity = findInstance(t.a, I)
                # t.a.dump()
                # pg._y(identity)

                if identity is not None:
                    #pg._b('I found')
                   return -grad(identity._space)*(t.a)
                else:
                    # can happen if t contains FEAOP('identity') instead of I
                    # TODO refactor
                    return -grad(list(t.spaces)[0])*(t.a)

            if hasattr(t, 'op') and (t.op == '*' or t.op == '/'):
                a = _toWeak(t.a)
                b = _toWeak(t.b)

                if a is None and b is not None:
                    if t.op == '*':
                        return t.a * _toWeak(t.b)
                    if t.op == '/':
                        print(t)
                        pg.critical('formula needs '
                                    'restructure or implement me')

                if b is None and a is not None:
                    if t.op == '*':
                        return _toWeak(t.a) * t.b

                    if t.op == '/':
                        return _toWeak(t.a) / t.b

            return None

        testFunction = self.space

        if testFunction is None:
            pg.critical('No space defined for this pde expression.')

        if hasattr(self, 'weak'):
            #pg._g(self.weak())
            return self.weak()

        forSpaces = kwargs.pop('forSpaces', False)
        splitSolOP = kwargs.pop('splitSolutionOPWithFuncs', False)

        terms = self.expand(removeDiv=True, forSpaces=forSpaces,
                            splitSolutionOPWithFuncs=splitSolOP)

        # for i, t in enumerate(terms):
        #     pg._g(f'term {i}:{type(t)}{t}\n '
        #           f'weak:{_toWeak(t)}, '
        #           f'space:{self.findSpace(t)}, \n\n'
        #             )

        feaLHS = None
        feaRHS = None

        for t in terms:
            # pg._g(f'term:{type(t)}{t}\n '
            #       f'weak:{_toWeak(t)}, '
            #       f'space:{self.findSpace(t)}, \n\n'
            #         )

            tWeak = _toWeak(t)

            #pg._b(tWeak, self.neg)
            if tWeak is not None:
                tWeak = OP.bubbleUpNeg(tWeak)

                #tWeak = fixOPSign(tWeak)

                if feaLHS is None:
                    feaLHS = tWeak
                else:
                    if hasattr(tWeak, 'neg') \
                        or (tWeak.op == '*' and tWeak.op < 0):
                        feaLHS -= -tWeak
                        #feaLHS += tWeak
                    else:
                        feaLHS += tWeak

            elif not self.findSpace(t):
                if feaRHS is None:
                    feaRHS = testFunction * -t
                else:
                    feaRHS += testFunction * -t

            else:
                if feaLHS is None:
                    feaLHS = testFunction * t
                else:
                    feaLHS += testFunction * t

        if feaRHS is None:
            if self.op == '==':
                return feaLHS == 0
            else:
                return feaLHS

        return feaLHS == feaRHS


    @property
    def weakForm(self):
        """Return weak form of PDE."""
        return self.createWeakForm()


    def __str__(self):
        """Return string representation of PDE."""
        if self.neg:
            return '-!' + super().__str__()
        else:
            return super().__str__()


    def __neg__(self):
        """Switch sign."""
        # self.neg = not self.neg
        # return self
        if self.op == '*' or self.op == '/':
            return PDE(-self.a, self.b, self.op)
        if self.op == '+' or self.op == '-':
            return PDE(-self.a, -self.b, self.op)

        pg.error('in use?')
        pg._b(self)
        ret = PDE(self.a, self.b, self.op)
        ret.neg = not self.neg
        return ret


class Div(PDE):
    """Divergence operator."""

    def __init__(self, pde):
        super().__init__(a=pde, b=None, op='div')


    def __str__(self):
        """Return string representation of div."""
        if self.neg is True:
            return f'-div({self.a})'
        return f'div({self.a})'


    def __repr__(self):
        """Return string representation of div."""
        return str(self)


    def weak(self):
        """Return FEA formulation."""
        # pg._r(self, self.space, self.a, self.space.forAssembling)

        # use the original space instead of the FEASolution
        if not self.space.forAssembling:
            self._space = self.space._origSpace

        if self.neg is True:
            return grad(self.space) * self.a
        return -(grad(self.space) * self.a)


    def __neg__(self):
        """Return copy of self with negative sign."""
        ### don't work see tests:
        ### python test_10_pde_expr.py TestPDEExpressions.test_Div
        # self.neg = not self.neg
        # return self
        ret = Div(self.a)
        ret.neg = not self.neg
        return ret


class Laplace(Div):
    """Laplace operator.

    May be removed.
    """

    def __init__(self, space):
        if isinstance(space, (FEASpace, FEAOP)):
            super().__init__(grad(space))
        else:
            super().__init__(space)


    def __str__(self):
        if self.space is not None:
            if self.neg is True:
                return f'-Laplace({self.space})'
            return f'Laplace({self.space})'
        else:
            if self.neg is True:
                return f'-Laplace({self.a})'
            return f'Laplace({self.a})'


    def __repr__(self):
        return str(self)
