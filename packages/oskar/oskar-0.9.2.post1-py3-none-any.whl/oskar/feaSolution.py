#!/usr/bin/env python
"""Classes to hold and manage finite element solutions."""
import copy

import numpy as np
import pygimli as pg

from . op import OP, Direction, Constant
from . utils import (getInstanceAssignmentName, __newFieldOrder__,
                     vectorizeEvalQPnts, asPosListNP, asPosListPG,
                     isVecField, asVecField, showVectorField)
from . feaOp import FEAOP
from . units import ParameterDict
from oskar import op


def _showSolution(u, mesh=None, **kwargs):
    """Show solutions.

    Arguments
    ---------
    u: FEASolution
        Finite element solution.
    mesh: Mesh
        Mesh to show the solution on. If not set, the mesh of the
        solution is used.

    Keyword Args
    ------------

    noAbs: bool [False]
        If set, draw only arrows or streamlines for vector functions.

    ref: Function
        Reference solution to compare with. 1D only.

    animate: bool
        Create an animation if its a time depending function.
    """
    animate = kwargs.pop('animate', False)
    refSolution = kwargs.pop('ref', None)

    if mesh is None:
        mesh = u.mesh

    label = kwargs.pop('label', u.name.replace('$$', '$'))
    v_ = u(mesh)

    deform = kwargs.pop('deform', None)

    if deform:
        ax, cBar = pg.show(mesh, alpha=0.1, colorBar=False,
                           ax=kwargs.pop('ax', None), hold=True)

        kwargs['ax'] = ax

        if mesh.dim() == 2:
            ax.text(1., 1.02, 'deformed:' \
                            + str(deform).replace('*', '·').replace('**', '^'),
                    fontsize=8,
                    horizontalalignment='right',
                    verticalalignment='bottom', transform=ax.transAxes)

        mesh = pg.Mesh(mesh)
        mesh.deform(deform)

    if isVecField(v_):
        return showVectorField(v_, mesh=mesh, label=label, u=u, **kwargs)

    if animate:
        return pg.show(u.mesh, u.history, label=label, **kwargs)

    kw = {}
    ax = kwargs.pop('ax', None)

    if refSolution:
        try:
            refSolution = refSolution(t=u.times[-1])
        except IndexError:
            pass

        ax = pg.show(u.mesh, refSolution,
                     label='reference',
                     c='k', lw=1, ax=ax)[0]
        kw = dict(marker='.', lw=0.5, c='C0')

    kwargs.update(kw)

    return pg.show(u, label=label, ax=ax, **kwargs)


@pg.singleton
class FEASolutionStore:
    """Store for finite element solutions."""

    def __init__(self):
        self.solutions = {}

    def name(self, sol):
        """Return the key name of the solution."""
        if isinstance(sol, FEASolution):
            return f'FEASolution_{sol.name}_{id(sol)}'
        else:
            pg.critical(f'Unknown solution type {type(sol)}.')
            return None

    def add(self, sol):
        """Add a solution to the store.

        Returns
        -------
        str:
            The name of store key for the solution.
        """
        name = self.name(sol)
        self.solutions[name] = sol
        return name

    def get(self, name):
        """Get a solution from the store."""
        sol = self.solutions.get(name)
        #pg._b(name, f'self {id(self)}', id(sol))
        return self.solutions.get(name)

    def remove(self, name):
        """Remove a solution from the store."""
        if name in self.solutions:
            del self.solutions[name]

    def clear(self):
        """Clear the store."""
        self.solutions.clear()


class FEASolution(OP):
    """Finite element solution.

    Represents the solution of a finite element approximation.
    """

    def __init__(self, space=None, values=None, name=None, time=None,
                 skipHistory=False):
        r"""Initialize the finite element solution.

        The approximated FE solution consists of discrete coefficient values
        for a finite element space (FESpace).
        The coefficients stored in the `values` attribute, the FESpace in
        the `space` attribute.
        The solution is a subclass of `OP` and can be accessed
        using the `eval` method.
        Values outside the dof of the FEASpace are interpolated using the
        base function from the FEASpace.
        The solution can be visualized using the
        `show` method.

        Arguments
        ---------
        space: FESpace [None]
            Finite element space.
            The solution holds a copy of the
            space so there can be multiple solutions for the same space but
            the space can only one solution at a time.
            `Space` can be None for default pickle but need to be set later
            if used manually.
        values: FEAFunction | float [None]
            Coefficient values for the finite element space.
        name: string [None]
            Name of the solution. If not set, a name is generated
            automatically from script variable name.
        time: float[None]
            If set to a value, the solution is assumed time dependent for
            this time step.
        skipHistory: bool [False]
            If set to True, the solution will not stored in the FEASpace.
        """
        if name is None:
            self._name = getInstanceAssignmentName(self.__class__.__name__)
        else:
            self._name = name

        super().__init__(OP=FEASolutionOP)

        if space is not None:
            if skipHistory is False:
                #pg._b(skipHistory)
                space._solution = self
            ### keep reference to original base space,
            ### used for e.g. grad(u)*grad(u.base)
            self.base = space

            self.space = copy.copy(space)

            # keep a ref to the original which is used for caching,
            # used by PDE.weak
            self.space._origSpace = space

            ### we need a deep copy of this to avoid double adds,
            ### mesh and other content should use references.
            self.space._valuesHistory = [] # list for fast append.
            self.space.forAssembling = False
            self.space._name = self.name

            if values is not None:
                if hasattr(values, 'eval'):
                    try:
                        values = values(space.mesh, t=0)
                    except BaseException:
                        values = values(space.mesh)
                elif pg.isScalar(values):
                    values = np.full(space.mesh.nodeCount()*space.nCoeff,
                                     values)
                self.values = values

            if self.values.ndim > 1:
                # check if needed!
                self._x = None
                self._y = None
                self._z = None
                self.setValueSize(3)
            else:
                # check if needed!
                self._x = None
                self.setValueSize(1)

        # Interpolation matrix for quadrature points
        self._qpInterpolationMatrixCache = {}

        # store times for transient problems
        self.times = []
        if time is not None:
            self.times.append(time)


    @property
    def name(self):
        """Return name of the function."""
        return self._name


    @property
    def valSize(self):
        """Return the size of the values.

        Return 3 for vector values and 1 for scalar values.
        """
        # attribute to use so it can be pickled, the core attribute
        # ValueSize is not picklable
        if self.values.ndim > 1:
            self.setValueSize(3)
            return 3
        self.setValueSize(1)
        return 1


    def __str__(self):
        """Return short (general) name, e.g., print()."""
        return self._name


    def __repr__(self):
        """Return long (unique) name."""
        # pg._b(str(self))
        return str(self)


    def __getitem__(self, idx):
        """Return the solution for the given time step."""
        return self.history[idx]


    def __hash__(self):
        """Return hash value based on the mesh and values."""
        return self.space.mesh.hash() ^ pg.utils.valHash(self.values)


    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        """Communicate with numpy."""
        if 0:
            pg._g('ufunc:', ufunc)
            pg._g('method:', method)
            pg._g('input:', *inputs)
            pg._g('kwargs', kwargs)

        if ufunc == np.multiply:
            return self.__rmul__(inputs[0])

        if ufunc == np.exp:
            return FEAOP(self, op='exp')
        else:
            # pg._r(ufunc, method)
            # pg._r(*inputs, kwargs)
            # pg.critical('implement me.')
            return FEAOP(self, op=ufunc)


    @property
    def mesh(self):
        """Return the mesh based for this solution."""
        return self.space.mesh


    def exportVTK(self, fileName):
        """Export the solution in VTK format.

        Attributes
        ----------
        fileName: string.
            Filename. Suffix '.vtk' will be added.
        """
        self.mesh[self.name] = self.values
        self.mesh.exportVTK(fileName)


    @property
    def values(self):
        """Return the values for the solution.

        The values are the coefficients for the finite element space, i.e.,
        the discrete values for each dof of the fea space.
        """
        return self.space.values


    @values.setter
    def values(self, v):
        """Set the values for the solution.

        The values are the coefficients for the finite element space, i.e.,
        the discrete values for each dof of the fea space.
        """
        self.space.values = v


    @property
    def history(self):
        """Return the values for all time steps of the solution.

        Returns a list of arrays for all past time steps of the solution, if
        there are.
        """
        return self.space._valuesHistory


    @property
    def ndim(self):
        """Return the number of dimensions for the solution."""
        return self.values.ndim


    @property
    def shape(self):
        """Return the shape of the solution."""
        return self.values.shape


    @property
    def aDiff(self):
        r"""Return the absolute difference to the last solution.

        Absolute difference :math:`d` is:

        .. math::
            d =\:& ||u^k - u^{k-1}||_{\infty}\\[10pt]
              =\:& \operatorname{max}\left(|u^k - u^{k-1}|\right)\\

        Returns
        -------
        float:
            Absolute difference between the current and the last solution.

        """
        if len(self.history) < 1:
            pg.critical('Only one solution known.')

        return np.sum(np.abs(self.values - self.history[-2]))


    def subst(self, func):
        """Substitute the solution into a function.

        Return a new function as `func(self(*args, **kwargs))`
        """
        return lambda *args, **kwargs: func(self(*args, **kwargs))


    def show(self, **kwargs):
        """Show the solution.

        Draws the solution using pg.show.
        If the solution is a vector function, it draws the
        field as absolute values with some arrows or streamlines.

        Keyword Args
        ------------
        **kwargs forwarded to pg.show()

        Returns
        -------
        ax, cBar:
            Return axe instance and colorbar from pg.show.
        """
        return _showSolution(self, **kwargs)


    def qpInterpolationMatrix(self, p):
        """Return interpolation Matrix for fi(p) = I(p)*f(mesh).

        TODO
        ----
            * cacheable for more sets of p
        """
        ## simple length check .. hash me
        ha = None
        #if isinstance(p, list):
        p = asPosListPG(p)

        with pg.tictoc('qp-hash'):
            ha = hash(p)

        # if isinstance(p, pg.core.stdVectorR3Vector):
        #     pg._r(ha)
        # pg._g(ha)
        # if not self._qpInterpolationMatrix is None:
        #     if len(p) != len(self._qpInterpolationMatrix):
        #         self._qpInterpolationMatrix = None
        if ha not in self._qpInterpolationMatrixCache:
            pg.debug('qp interpolation matrix for: ', self)

            if isinstance(p, pg.core.stdVectorR3Vector):
                I_ = pg.core.stdVectorRSparseMapMatrix()
            else:
                I_ = pg.core.RSparseMapMatrix()

            with pg.tictoc(f'create Iq for {self}'):
                self.mesh.interpolationMatrix(p, I_)

            self._qpInterpolationMatrixCache[ha] = I_

        I = self._qpInterpolationMatrixCache[ha]

        if isinstance(p, pg.core.stdVectorR3Vector) \
            and len(p[0]) != I[0].rows():

            pg.critical('wrong interpolation matrix')

        return I


    def __length__(self):
        """Return the length of the solution."""
        return len(self.values)


    def eval(self, *args, **kwargs):
        """Call with coordinate and interpolate value from space.

        TODO
        ----
            * refactor with FEASolutionOP.interpolate

        Keyword arguments
        -----------------
        p:

        Keyword arguments
        -----------------
        time: float
            Time for transient solutions

        """
        # pg._y(f' args({args}), kwargs=({kwargs})')
        # pg._y(type(args[0]))
        p = args[0] if len(args) > 0 else None

        values = kwargs.pop('values', None)

        if values is None:
            if 't' in kwargs:
                kwargs['time'] = kwargs.pop('t')
            ## test forward values

            if 'time' in kwargs and len(self.times) > 0:
                time = kwargs.pop('time')

                def getTimeInterpolatedValues_(time):
                    if time >= self.times[-1]:
                        return self.values
                    elif time <= self.times[0]:
                        return self.history[0]
                    else:
                        try:
                            timeID = np.argwhere(
                                abs(np.array(self.times) - time)< 1e-12)[0]
                            if len(timeID) == 1:
                                #print(self.time[timeID[0]])
                                return self.history[timeID[0]]

                            pg._y('fixme', timeID)

                        except BaseException:
                            # interpolate linear between time steps

                            hi = np.argmin(np.array(self.times) < time)
                            lo = hi -1
                            vHi = self.history[hi]
                            vLo = self.history[lo]
                            tHi = self.times[hi]
                            tLo = self.times[lo]
                            # pg._b(time, lo, vLo, (time-tLo)/(tHi-tLo))
                            # pg._b(time, hi, vHi, (time-tLo)/(tHi-tLo))
                            return vLo + (vHi-vLo)*((time-tLo)/(tHi-tLo))

                if hasattr(time, '__iter__'):
                    time = np.array(time)
                    if len(time) == len(self.times) and \
                        np.linalg.norm(time-self.times) < 1e-12:
                        values = np.array(self.history)
                    else:
                        with pg.tictoc('interpolate.times[(t)]'):
                            #pg._y(time)
                            #print(
                            # [getTimeInterpolatedValues_(t) for t in time])
                            values = np.array(
                                [getTimeInterpolatedValues_(t) for t in time])

                else:
                    with pg.tictoc('interpolate.time(t)'):
                        values = getTimeInterpolatedValues_(time)

            else:
                values = self.values


        if p is None:
            return values

        if pg.isScalar(p):
            p = pg.Pos(p, 0)

        ## TODO think about normalization here to vectorize
        ## p need to be PosList then one target

        #pg._b(type(p), values.shape, values.ndim, self.valSize)
        if self.valSize == 1:
            values = np.squeeze(values)

        if values.ndim == 2 and self.valSize == 1:
            # only for scalar solution .. implement me for vector sol
            # pg._b('sol.eval [(p,v_i)]:', values.ndim, values.shape)
            with pg.tictoc('sol.eval [(p,v_i)]:'):
                return np.array([self.eval(p, values=v, **kwargs)
                                    for v in values])

        #pg._b(self.valSize, pg.isR3Array(p))
        if isinstance(p, pg.core.Mesh):
            return self.eval(p.positions(), values=values)

        elif isinstance(p, pg.core.stdVectorR3Vector):
            #pg._b('sol.eval: I*vvr3')
            with pg.tictoc('sol.eval: I*vvr3'):
                return self.qpInterpolationMatrix(p) * values

        elif pg.isR3Array(p) and self.valSize == 1:
            # only for scalar solution .. implement me for vector sol
            #pg._b('sol.eval: I*vr3')
            with pg.tictoc('sol.eval: I*vr3'):
                return self.qpInterpolationMatrix(p) * values

        elif pg.isR3Array(p):
            #pg._b('sol.eval: [(R3), ]')
            with pg.tictoc('sol.eval: [(R3), ]'):
                return np.array([self.eval(pi, values=values, **kwargs)
                                    for pi in p])

        elif isinstance(p, pg.core.stdVectorNodes):
            #pg._b('sol.eval: [nodes, ]')
            with pg.tictoc('sol.eval: [nodes, ]'):
                return np.array([self.eval(pi.pos(), values=values, **kwargs)
                                    for pi in p])

        elif pg.isArray(p) and pg.isPos(p) is False:
            ## 1D array -> interpret as [x, 0, 0]
            #pg._b('sol.eval: [[x], 0, 0]')
            with pg.tictoc('sol.sol: [[x], 0, 0]'):
                return np.array([self.eval([pi, 0], values=values, **kwargs)
                                    for pi in p])

        elif (pg.isArray(p) and self.mesh.dim() == 1) and pg.isPos(p) is False:
            ## needed?
            ## 1D array and 1d case ?? why
            #pg._b('sol.eval: [[x], ]')
            with pg.tictoc('sol.eval: [(R1), ]'):
                return np.array([self.eval([pi, 0], values=values, **kwargs)
                                    for pi in p])

        if self.valSize > 1:
            ## we need prepare a little .. will fail if values had been changed

            c = self.mesh.findCell(p)
            if c is None:
                pg.critical('No cell at:', p)

            if __newFieldOrder__ is True:
                pg.critical("don't use!")
                ## field shape (dim, dof)
                if values.shape[0] == 1:
                    vx = c.pot(p, values[0])
                    return np.array([vx, 0.0, 0.0])
                elif values.shape[0] == 2:
                    vx = c.pot(p, values[0])
                    vy = c.pot(p, values[1])
                    #print(p, [vx, vy])
                    return np.array([vx, vy])
                elif values.shape[0] == 3:
                    vx = c.pot(p, values[0])
                    vy = c.pot(p, values[1])
                    vz = c.pot(p, values[2])
                    return np.array([vx, vy, vz])
            else:
                ## field shape (dof, dim) # old and bad, but still needed, why?
                if values.shape[1] == 1:
                    vx = c.pot(p, values.T[0])
                    return np.array([vx, 0.0, 0.0])
                elif values.shape[1] == 2:
                    vx = c.pot(p, values.T[0])
                    vy = c.pot(p, values.T[1])
                    #print(p, [vx, vy])
                    return np.array([vx, vy])
                elif values.shape[1] == 3:
                    vx = c.pot(p, values.T[0])
                    vy = c.pot(p, values.T[1])
                    vz = c.pot(p, values.T[2])
                    return np.array([vx, vy, vz])

            if values.ndim == 3:
                ## probably multiple times for vector value
                #pg._b('sol.eval: [(p,v_i), ] in R3')
                with pg.tictoc('sol.eval: [(p,v_i), ] in R3'):
                    return np.array([self.eval(p, values=v, **kwargs)
                                     for v in values])

            pg.error('implement me with shape:', type(values),
                     values.shape, self.valSize)

        else:
            # if self._x is None:
            #     # pg.info('assigning scalar field to x')
            #     try:
            #         self._x = pg.Vector(self.values)
            #     except:
            #         print("vals:", self.values)
            #         print("mesh:", self.mesh)
            #         pg.critical('fix me')

            #     if not pg.isArray(self._x, self.mesh.nodeCount()):
            #         print(self.mesh)
            #         print(self._x)
            #         pg.critical('invalid data size')

            #     # if self.space is not None and \
            #     #     pg.isArray(self.space.values,
            #     #               self.mesh.nodeCount()):
            #     #     self._x = pg.Vector(self.space.values)
            #     # else:
            #     #     self._x = pg.Vector(self)

            c = self.mesh.findCell(p)
            if c is None:
                pg.critical(f'There is no cell at {p}')

            #pg._b(p, values.shape)
            return c.pot(p, values)


    def __abs__(self):
        """Return the FEASolution with absolute values of the solution."""
        return FEASolutionOP(self, op='abs')


    def grad(self):
        """Return operator the gradients of the solution."""
        #TODO: Refactor with Grad"
        # pg._r("FEASolution.grad")
        #return FEAOP(self.space, op='grad')
        #TODO but needs heavy refactoring!!!
        #return SolutionGrad(self)
        return FEAOP(self.space, op='grad', solutionGrad=True)


    def div(self):
        """Return operator the divergence of the solution."""
        #TODO: Refactor with Div(FEAOP|FEAFunction|FEASolution)"
        #return SolutionDiv(self)
        #return FEASolutionOP(self.space, op='div', solutionGrad=True)
        return FEAOP(self.space, op='div', solutionGrad=True)


    def norm(self):
        """Return operator the norm of the solution."""
        #Refactor with space"
        pg._r("FEASolution.norm: in use?")
        return FEAOP(self, op='norm')


    def identity(self):
        """Return operator the identity of the solution."""
        #Refactor with space"
        # pg._r("FEASolution.identity: in use?")
        #return FEAOP(self, op='identity')
        return FEAOP(self.space, op='identity')


class FEASolutionOP(OP):
    # TODO Refactor with FEASolution
    """Algebraic operator for finite element solutions."""

    def __init__(self, *args, **kwargs):
        """Initialize the operator.

        Arguments
        ---------
        a: FEASolution
            First operand.
        b: FEASolution
            Second operand.
        op: string
            Operator to apply.

        Keyword Args
        ------------
        **kwargs:
            Forwarded to OP bass class
        """
        self._shape = None

        super().__init__(*args, OP=FEASolutionOP, **kwargs)
        #pg._g(self.a, self.b, self.op, kwargs)

        #pg_r(self._shape)

        self._mesh = None
        if hasattr(self.a, 'mesh') and self.a.mesh is not None:
            self._mesh = self.a.mesh

        if hasattr(self.b, 'mesh') and self.b.mesh is not None:
            if self._mesh is None:
                self._mesh = self.b.mesh
            else:
                pass
                # check this in eval
                # if hash(self._mesh) != hash(self.b.mesh):
                #     print('1', self._mesh)
                #     print('2', self.b.mesh)

                #     pg._y('self:', self)
                #     pg.error('mixed mesh FEA Solution operators not yet '
                #            'supported, implement interpolation mapping here!')

        self.space = None

        if hasattr(self.a, 'space'):
            self.space = self.a.space

        if hasattr(self.b, 'space'):
            if self.space is None:
                self.space = self.b.space
            else:
                pass
                # if id(self.space) != id(self.b.space):
                #     pg.warn('Solution OP with mixed spaces not yet '
                #            'supported, implement interpolation mapping here!')

        self.qpInterpolationMatrix = None

        if hasattr(self.a, 'qpInterpolationMatrix'):
            self.qpInterpolationMatrix = self.a.qpInterpolationMatrix

        if hasattr(self.b, 'qpInterpolationMatrix'):
            if self.qpInterpolationMatrix is None:
                self.qpInterpolationMatrix = self.b.qpInterpolationMatrix
            else:
                if self.qpInterpolationMatrix is not \
                   self.b.qpInterpolationMatrix:
                    pass
                    # pg.warning('maybe mixed mesh FEA Solution operators not
                    #            'yet supported, '
                    #            'implement interpolation mapping here!')


    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        """Communicate with numpy ufuncs."""
        if 0:
            pg._g('ufunc:', ufunc)
            pg._g('method:', method)
            pg._g('input:', *inputs)
            pg._g('kwargs', kwargs)

        if ufunc == np.multiply:
            return self.__rmul__(inputs[0])

        if ufunc == np.exp:
            return OP(self, op='exp')
        else:
            return OP(self, op=ufunc)
            # pg._r(ufunc, method)
            # pg._r(*inputs, kwargs)
            # pg.critical('implement me.')

    @property
    def name(self):
        """Return name of the operator."""
        return repr(self)


    @property
    def shape(self):
        """Shape of the explicit values."""
        if self._shape is None:
            if hasattr(self.a, 'shape'):
                self._shape = self.a.shape

            if hasattr(self.b, 'shape'):
                if self._shape is None:
                    self._shape = self.b.shape
                else:
                    if self.a.shape != self.b.shape:
                        pg.warn('Solution OP with mixed shapes ',
                                'check is needed')

        return self._shape


    @property
    def ndim(self):
        """Number of dimensions for the explicit values."""
        return len(self._shape)


    @property
    def mesh(self):
        """Return the mesh for this solution operator."""
        if self._mesh is not None:
            return self._mesh
        return pg.critical('no mesh for this solution op')


    @property
    def values(self):
        """Return values for the solution operator with `eval()`."""
        # cache me
        return self.eval()


    def show(self, **kwargs):
        """Show the solution.

        Draws the solution using pg.show.
        If the solution is a vector function, it draws the
        field as absolute values with some arrows or streamlines.

        Keyword Args
        ------------
        **kwargs forwarded to pg.show().

        Returns
        -------
        ax, cBar:
            Return axe and color bar from pg.show.
        """
        return _showSolution(self, **kwargs)


    def interpolate(self, p):
        """Interpolate the solution to the given position.

        TODO
        ----
            * cache self.values
            * check if can use interpolation of the operator parts
            itself.
        """
        if p is None:
            pg.critical('p is none, need destination')

        if isinstance(p, pg.core.stdVectorR3Vector):
            with pg.tictoc('solution: Iq*(vvr3)'):
                return self.qpInterpolationMatrix(p) * self.values
        else:
            try:
                # v = self.values
                # ret = pg.interpolate(self.mesh, v, p)
                # pg._g(p)
                # pg._y(v)
                # pg._g(ret)
                # print(ret)
                # return ret
                with pg.tictoc('solution: interpolate'):
                    return pg.interpolate(self.mesh, self.values, p)
            except BaseException as e:
                print(self)
                print('p', p)
                return pg.critical(e)


    def subst(self, a, b):
        """Return a new FEASolutionOP with substituted a with b."""

        def subst_(t, a, b):
            """Copy the operator."""
            # pg._b(t, ',', a, ',',b)

            if not hasattr(t, 'op') or hasattr(t, 'op') and t.op is None:
                if t is a:
                    # pg._y(t, a, b)
                    return b
                else:
                    return t
            else:
                A = subst_(t.a, a, b)
                B = subst_(t.b, a, b)

                if t.op is None:
                    return A

                OP = type(t)
                # pg._g(A, B, t.op)
                return OP(A, B, op=t.op, **t._kwargs)

        return subst_(self, a, b)


    def eval(self, *args, **kwargs):
        """Evaluate the operator with the given arguments.

        Note
        ----
        case1: I*(a*b) != I*a * I*b, so eval first and interpolate the result

        vs.

        case2: I*((1+u)**p) != (1+I*u)**p, so interpolate first and eval result

        Returns either scalar, Vector, stdVectorRVector

        """
        from . elasticity import ElasticityMatrix

        p = args[0] if len(args) > 0 else None

        if pg.core.deepDebug() == -1:
            pg._y('*'*60)
            pg._y('** FEASolutionOP eval PRE')
            pg._y(f'** \tA: {type(self.a)}')
            pg._y(f'\n{self.a}')
            pg._y(f'** \tOP: {self.op}\n')
            pg._y(f'** \tB: {type(self.b)}')
            pg._y(f'\n{self.b}')
            pg._y('at:', args, kwargs)
            pg._y('*'*60)

        a = None
        b = None

        if hasattr(self.a, 'mesh') and self.a.mesh is not None \
             and hasattr(self.b, 'mesh'):

            from . mathOp import I
            if self.b.mesh is None and isinstance(self.b, I):
                # still use the mesh from a just in case is self.b is I()
                #print(self.a.mesh)
                self.b.mesh = self.a.mesh

            if self.b.mesh is not None and \
                hash(self.a.mesh) != hash(self.b.mesh):

                print('1', self.a.mesh)
                print('2', self.b.mesh)

                pg._y('self:', self)
                pg.critical('mixed mesh FEA Solution evaluation not yet '
                            'supported, implement interpolation mapping here!')

        case = 2

        if case == 1 or (hasattr(self, 'interpolationOrder') and \
                         self.interpolationOrder == 1):
            # pg._r(self, p)
            # eval first then interpolate to sought position
            # .. not used .. need tests!!
            if p is not None:
                return self.interpolate(p)
            else:
                a = self.evalTerm(self.a, **kwargs)
                b = self.evalTerm(self.b, **kwargs)

                if isinstance(self.a, Constant) or isinstance(self.b, Constant):
                    pg.critical('implement me')

        elif case == 2:
            # Default: interpolate u value then evaluate,
            # this leads to exact on expression curve
            def _get(a, p, **_kw):
                if isinstance(a, Direction):
                    return a.eval(*args, mesh=self.mesh)
                if isinstance(a, Constant):
                    cell = kwargs.pop('cell')
                    return a(cell.dim())
                if isinstance(a, FEASolution):
                    # special case to make tests happy .. TODO refactor me!
                    return a.eval(p, **kwargs)
                if isinstance(a, ParameterDict):
                    a = a.cellValues(_kw.get('mesh', self.mesh))

                if p is None:
                    if self.space.mesh.dim() == 1:
                        p = pg.x(self.space.mesh)
                    else:
                        p = self.space.mesh

                #pg._b(a, p, _kw)
                return OP.evalTerm(a, p, **kwargs, **_kw)

            ### special case for [cellValues] * b
            ### TODO refactor for kind of cls CellValue(mesh)
            if hasattr(self.b, 'mesh') and 'mesh' not in kwargs:
                # give mesh for cell values
                a = _get(self.a, p, mesh=self.b.mesh)
            else:
                a = _get(self.a, p)

            if hasattr(self.a, 'mesh') and 'mesh' not in kwargs:
                # give mesh for cell values
                b = _get(self.b, p, mesh=self.a.mesh)
            else:
                b = _get(self.b, p)

            # #with tictoc('solOP.evalTERM.a'):
            # a = _get(self.a, p, mesh=self.b.mesh)
            # #with tictoc('solOP.evalTERM.b'):
            # b = _get(self.b, p, mesh=self.a.mesh)

            # pg._r(a)
            # pg._r(b)


        if pg.core.deepDebug() == -1:
            pg._g('FEASolution OP eval POST')
            pg._g(f'** \ta: {type(a)}')
            pg._g(f'\n{a}')
            pg._g(f'** \tOP: {self.op}\n')
            pg._g(f'** \tB: {type(b)}')
            pg._g(f'\n{b}')
            pg._g('*'*60)

        if self.op == 'abs':
            return pg.abs(a)
        elif self.op == 'sqrt':
            return np.sqrt(a)
        elif self.op == 'exp':
            return np.exp(a)
        elif self.op == 'pow':
            # refactor with OP!!
            if isinstance(a, pg.core.stdVectorR3Vector):
                if 0 and self.space.nCoeff == 1:
                    pg.critical('should i be here?')
                    ret = pg.core.stdVectorRVector()
                    pg.core.dot(a, a, ret)
                    return ret

                return a*a

            if 0 and self.space.nCoeff == 1 and self.exponent == 2:
                pg.critical('should i be here?')
                if pg.isPos(a):
                    return (a*a).sum()

            return np.power(a, self.exponent)
        elif self.op == 'neg':
            return -a
        elif self.op == 'grad':
            print('a', a)
            print('b', b)
            pg.critical('implement me')
        elif self.op == 'div':
            print('a', a)
            print('b', b)
            pg.critical('implement me')

        if pg.isScalar(a):
            ## return NotImplemented for generic getattr
            # with int.__mul__(int|float)

            if self.op == '*':
                return a*b
            if self.op == '+':
                return a+b
            if self.op == '-':
                return a-b
            if self.op == '/':
                return a/b

        if self.op == '*':

            if (not pg.isPos(a) and pg.isArray(a)) and pg.isPos(b):
                ## probably span scalar field to vector field a * [b_1,b_2,b_3]
                # pg._g(a)
                # pg._r(b)
                # print(np.outer(a,b))
                return np.outer(a,b)
            if (not pg.isPos(b) and pg.isArray(b)) and pg.isPos(a):
                ## probably span scalar field to vector field [a_1,a_2,a_3] * b
                # pg._g(a)
                # pg._r(b)
                # print(np.outer(a,b).T)
                return np.outer(a,b).T

            if isinstance(a, np.ndarray) and len(a) > 1 and \
               isinstance(b, np.ndarray) and len(b) == 1:
                ## in use? necessary?
                ## (Nx1) [f, ] * (1xMxM) [[[f,],[f,],]] : from [f, ] * I(v)
                return np.squeeze(np.asarray([[a[i]*b] for i in range(len(a))]))
                # print('a', type(a), len(a), a.shape)
                #print('b', type(b), b)

            if isinstance(a, ElasticityMatrix) or pg.isSquareMatrix(a):
                ## C * a
                if isinstance(b, pg.core.stdVectorRVector):
                    ## C * [[b_i, ]_j, ]_Cells = [[C*b_i, ]_j, ]_Cells
                    with pg.tictoc('FEASolutionOP eval: md*vvd'):
                        ret = pg.core.stdVectorRDenseMatrixVector()
                        for j, rj in enumerate(b): ## for each cell_j
                            rv = pg.core.stdVectorRDenseMatrix()
                            for i, bi in enumerate(rj): ## for each quad i
                                rv.append(a * bi)
                            ret.append(rv)
                    return ret
                elif pg.isScalar(b):
                    return a*b
                else:
                    pg._g('p', p, len(p))
                    pg._b('a', a, a.shape, a.ndim, len(a))
                    pg._b('b', b, b.shape, b.ndim, len(b))
                    pg.critical('implement me for', type(b),
                                'with shape', b.shape, 'and ndim', b.ndim)

            if isinstance(a, pg.core.stdVectorRDenseMatrixVector):
                with pg.tictoc('FEASolutionOP eval: vvmd*vvd'):
                    ret = pg.core.stdVectorRDenseMatrixVector()
                    for j, aj in enumerate(a): ## for each cell_j
                        rv = pg.core.stdVectorRDenseMatrix()
                        for i, aij in enumerate(aj): ## for each quad i
                            rv.append(aij * b[j][i])
                        ret.append(rv)
                return ret

            ## refactor with OP.eval
            try:
                ### [a,] * [MxN,] = [a*MxN, ]
                if hasattr(a, '__iter__') and hasattr(b, '__iter__') and \
                    len(a) == len(b) and b.ndim == 3:
                    return np.squeeze(np.asarray([[a[i]*b[i]]
                                                  for i in range(len(a))]))
                # a = np.squeeze(a)
                # b = np.squeeze(b)
                # pg._b(a, a.shape, a.ndim, len(a))
                # pg._b(b, b.shape, b.ndim, len(b))
                # pg._g(a * b)
                # try:
                #     pg._g(np.squeeze(a.T) * np.squeeze(b))
                # except ValueError as e:
                #     print('ValueError in mul', e)

                return np.squeeze(a) * np.squeeze(b)
            except ValueError:
                if len(a) == len(b):

                    if isinstance(a[0], ElasticityMatrix) or \
                    (pg.isSquareMatrix(a[0], 3) and pg.isSquareMatrix(b[0], 2)) or \
                    (pg.isSquareMatrix(a[0], 6) and pg.isSquareMatrix(b[0], 3)):
                        from .elasticity import strainToNotation
                        # print(a.shape, b.shape)
                        # print(a[0].shape, b[0].shape)
                        pg._b('use correct mapping')
                        return [a[i] @ strainToNotation(b[i]) for i in range(len(a))]

                    #pg._b()
                    ## can this be nicer? mul: e.g. (4,) * (4,3)
                    return np.squeeze(np.asarray([[a[i]*b[i]]
                                                  for i in range(len(a))]))
                else:
                    pg._b()
                    return (a.T * b).T

        try:
            # pg._g(type(a), a, len(a))
            # pg._y(self._ops[self.op])
            # pg._g(type(b), b, len(b))
            c = getattr(a, self._ops[self.op])(b)
            # pg._y(c, len(c))
            return c

        except Exception as e:
            pg._r('-'*40)
            print('self:', self)
            print('self.a', self.a)
            print('self.op', self.op)
            print('self.b', self.b)
            print('a', a)
            print('b', b)
            print(e)
            pg.critical('implement me')


#ScalarField = FEASolution

class SolutionGrad(OP):
    # TODO Refactor with FEASolution
    """Gradient operator for finite element solutions."""

    def __init__(self, sol, **kwargs):
        """Initialize the operator.

        Arguments
        ---------
        sol: FEASolution
            First operand.

        Keyword Args
        ------------
        **kwargs:
            Forwarded to bass class.
        """
        #super().__init__(OP=FEAOP)
        super().__init__(OP=FEASolutionOP)
        #super().__init__(self, **kwargs)
        self._sol = sol
        self.evalOrder = sol.evalOrder
        self.space = sol.space


    def __str__(self):
        """Return short (general) name, e.g., print()."""
        return f'grad({self._sol.name})'


    @property
    def mesh(self):
        """Return the mesh for the base solution operator."""
        return self._sol.mesh


    def eval(self, *args, **kwargs):
        """Evaluate the gradient of the solution."""
        if 't' in kwargs:
            kwargs['time'] = kwargs.pop('t')

        if pg.core.deepDebug() == -1:
            pg._y('*'*60)
            pg._y('** SolutionGrad eval')
            pg._y(f'** \tsol: {type(self._sol)}')
            pg._y(f'{self._sol}')
            pg._y('at:', args, kwargs)
            pg._y('*'*60)

        if 0 and isinstance(args[0], pg.core.stdVectorR3Vector):
            return vectorizeEvalQPnts(self.eval, args[0], **kwargs)

        #pg._b(args, kwargs)

        if 'time' in kwargs and hasattr(kwargs['time'], '__iter__'):
            times = kwargs.pop('time')
            # pg._b(times)
            # pg._b(np.asarray([self.eval(*args, time=t, **kwargs)
            #                       for t in times]))
            return np.squeeze(np.asarray([self.eval(*args, time=t,
                                                    **kwargs) for t in times]))

        u = self._sol.eval(**kwargs)
        dim = kwargs.pop('dim', None)

        if not dim:
            keepDim = kwargs.pop('keepDim', False)
            # pg._b(self.mesh.dim())
            dim = self.mesh.dim() if keepDim is False else 3

        if isinstance(args[0], pg.core.stdVectorR3Vector):

            #pg._y(args[0], len(args[0]))

            with pg.tictoc('grad(sol).eval pg.interpolate'):
                if u.ndim == 2:
                    ret = pg.core.stdVectorMatrixVector()
                else:
                    ret = pg.core.stdVectorR3Vector()

                pg.core.interpolateGradients(self.mesh,
                                             args[0], u, ret, dim=dim)

            if pg.core.deepDebug() == -1:
                pg._g('grad(sol).eval pg.interpolate', *ret)
            return ret

        pnts = asPosListNP(args[0]) if len(args) > 0 else asPosListNP(self.mesh)

        # pg._y(pnts)
        # pg._g(u, isVecField(u))
        # pg._y(pnts[0])
        ## vectorize me!

        if dim == 1:
            ret = np.zeros(len(pnts))
        else:
            if isVecField(u) is True:
                if pg.core.deepDebug() == -1:
                    pg._g('u is vector field')
                ret = np.zeros((len(pnts), dim, dim))
            else:
                if pg.core.deepDebug() == -1:
                    pg._g('u is scalar field')
                ret = np.zeros((len(pnts), dim))

        if pg.core.deepDebug() == -1:
            pg._g('grad:', *ret)

        for i, pt in enumerate(pnts):
            #   pg._g(pt)
            with pg.tictoc('grad(sol).eval [pt,]'):
                c = self.mesh.findCell(pt)
                if c is not None:
                    #pg._g(c.grad(pt, u))
                    #ret[i] = np.asarray(c.grad(pt, u))[0:dim, 0:dim]
                    if dim == 1:
                        ret[i] = c.grad(pt, u, dim).x()
                    else:
                        ret[i] = np.asarray(c.grad(pt, u, dim))[0:dim]

        if len(pnts) == len(ret):
            return np.squeeze(ret)

        # pg._g(ret)
        # pg._g(ret.shape)
        ### special case for one pnt. refactor me after switch to newFieldOrder
        if ret.shape == (3,3) or ret.shape == (3,2) or ret.shape == (2,2):
            return ret

        return np.squeeze(asVecField(ret))


class SolutionDiv(SolutionGrad):
    """Divergence operator for finite element solutions."""

    def __init__(self, sol, **kwargs):
        """Initialize the operator.

        Arguments
        ---------
        sol: FEASolution
            First operand.

        Keyword Args
        ------------
        **kwargs:
            Forwarded to bass class.
        """
        super().__init__(sol=sol, **kwargs)

    def eval(self, *args, **kwargs):
        """Evaluate the divergence of the solution."""
        if pg.core.deepDebug() == -1:
            pg._y('*'*60)
            pg._y('** SolutionDiv eval')
            pg._y(f'** \tsol: {type(self._sol)}')
            pg._y(f'{self._sol}')
            pg._y('at:', args, kwargs)
            pg._y('*'*60)

        ret = super().eval(*args, **kwargs)

        if pg.core.deepDebug() == -1:
            pg._g('div:', *ret)

        if isinstance(ret, pg.core.stdVectorMatrixVector):
            return pg.core.trace(ret)

        return ret
