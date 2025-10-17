#!/usr/bin/env python
"""Generic finite element solver and some related functions."""

import numpy as np
import pygimli as pg

from . op import hasInstance
from . mathOp import (I, PDE, isStrongFormPDE,
                      grad, sym, trace, norm, Dirac)
from . feaFunction import (FEAFunction, FEAFunction3, FEAFunctionDotNorm,
                           toFEAFunc)
from . feaSpace import FEASpace, ConstantSpace, VectorSpace, findFEASpace, ScalarSpace
from . feaSolution import FEASolution, FEASolutionOP
from . feaOp import (FEAOP, assembleBilinearForm, assembleLinearForm)

from . utils import call, getInstanceAssignmentName
from . linSolve import (LinSolver, linSolve)
from . units import symbols


def normL2(u, order=None, space=None, **kwargs):
    r"""Create Lebesgue (L2) norm for finite element space.

    Find the L2 Norm of a solution for the finite element space with
    :math:`u` exact solution and :math:`{\bf M}` Mass matrix, i.e.,
    Finite element identity matrix.

    .. math::

        e_{L_2}(u) = || u ||_{L^2} &
                   = (\int |u|^2 \mathrm{d}\:x)^{1/2} \\
        e_{L_2}(f(x)) = || f(x) ||_{L^2} &
                      = (\int |f(x)|^2 \mathrm{d}\:x)^{1/2} \\
            & \approx h (\sum |f(x)|^2 )^{1/2} \\

    The error for an approximated FEA solution :math:`u_h` correlates to the L2
    norm of `normL2(u - u_h)`. If you like relative values, you can also
    normalize this error with `normL2(u - u_h) / normL2(u)* 100`.

    Arguments
    ---------
    u: FEASpace | OP | iterable
        Function to compute the L2 norm for.
    order : int [None]
        Specify element integration order. For None, taking from the fea space.
    space: FEASpace
        Space if u is a function.

    Keyword Args
    ------------
    **kwargs : dict()
        Kwargs are forwarded to integration or assembling.

    Returns
    -------
    ret: float
        :math:`L2(u)` norm.
    """
    if isinstance(u, FEASolutionOP) \
        and 'time' not in kwargs and 't' not in kwargs:

        ### assume (Solution OP Function)
        if isinstance(u.a, FEASolution) and len(u.a.times) > 0:
            ## no time in args but .. transient solution .. choose the last
            return normL2(u, order=order, space=space, time=u.a.times[-1])

        ### assume (Function OP Solution)
        if isinstance(u.b, FEASolution) and len(u.b.times) > 0:
            ## no time in args but .. transient solution .. choose the last
            return normL2(u, order=order, space=space, time=u.b.times[-1])

    if pg.isArray(u):
        return np.linalg.norm(u)

    if space is None:
        try:
            space = findFEASpace(u)
        except ValueError as e:
            print(e)
            u.dump()
            pg.critical("Need FEASpace to calculate normL2. " +
                        "You can add them as keyword argument " +
                        "if u is just a function.")

    # TODO: refactor! .. reuse space but space(u) can be VectorSpace!
    space = ScalarSpace(space.inputMesh, p=space.p, order=space.order+1)

    if order is None:
        # check if p-order or quadrature-order is the right
        #r3 = np.sqrt(sum((space*(u**2)).assemble(useMats=True,**kwargs)))
        with pg.tictoc('normL2.a'):
            r3 = np.sqrt(sum((space*(u**2)).assemble(useMats=True,
                                                        **kwargs)))
    else:
        #order = u.space.order
        with pg.tictoc('normL2.i'):
            r3 = np.sqrt((u**2).integrate(space.mesh, order=order,
                                          **kwargs)) ## seems right
    return r3


def normSemiH1(u, order=None, space=None, **kwargs):
    r"""H1-SemiNorm is the L2_norm of the gradient.

    .. math::

        e_{H_1}(f(x)) = || f(x) ||_{H^1} = || \nabla f(x) ||_{L^2}

    Arguments
    ---------
    u: FEASpace | OP | iterable
        Function to compute the H1 semi norm for.
    order : int [None]
        Specify element integration order. For None, taking from the fea space.
    space: FEASpace
        Space if u is a function.

    Keyword Args
    ------------
    **kwargs : dict()
        Keyword arguments forwarded to integration or assembling.

    Returns
    -------
    ret: float
        :math:`H1(u)` semi norm.
    """
    if isinstance(u, FEASolutionOP) \
        and 'time' not in kwargs:

        ### assume (Solution OP Function)
        if isinstance(u.a, FEASolution) and len(u.a.times) > 0:
            ## no time in args but .. transient solution .. choose the last
            return normSemiH1(u, order=order, space=space,
                                time=u.a.times[-1])

        ### assume (Function OP Solution)
        if isinstance(u.b, FEASolution) and len(u.b.times) > 0:
            ## no time in args but .. transient solution .. choose the last
            return normSemiH1(u, order=order, space=space,
                                time=u.b.times[-1])

    with pg.tictoc('normSemiH1'):
        return normL2(grad(u), order=order, space=space, **kwargs)


class DirichletBC(object):
    """Dirichlet Boundary condition.

    This class is used to manage Dirichlet boundary conditions for a
    finite element space. It is used by the DirichletManager.
    """

    def __init__(self, parent, space, nodes, vals):
        self._parent = parent # DirichletManager to get notified for changes
        self.space = space    # associated space
        self._nodes = nodes   # [Nodes]
        self._vals = vals     # [values] # for each Node: scalars, callable etc.

        #self.bcNodes = bc     # {node:value}
        self.bcIDSVals = {}   # {dofID:value} # explicite value per node

    def update(self, **kwargs):
        """"""
        # pg._g('update', self)
        vals = self._vals

        # def _call(cl, node, **kwargs):
        #     try:
        #         val = cl(node.pos())
        #     except Exception as e:
        #         try:
        #             val = cl(node.pos(), node, **kwargs)
        #         except  Exception as e:
        #             val = cl(node.pos(), **kwargs)
        #     return val

        for i, node in enumerate(self._nodes):
            val = None

            if pg.isScalar(vals):
                val = vals

            elif pg.isArray(vals, N=len(vals)) or hasattr(vals, '__iter__'):
                if callable(vals[i]):
                    val = call(vals[i], node.pos(), **kwargs)
                else:
                    val = vals[i]

            else:
                print(vals)
                pg.critical("Can't interpret Dirichlet update values")

            val = np.atleast_1d(val)

            # pg._y(self.space, node, self.space.idx(node))
            for j, idx in enumerate(self.space.idx(node)):
                # pg._y('\t', j, idx, val[j])
                if val[j] is not None:
                    self.bcIDSVals[idx] = val[j]

        self._parent._valMap = None


    def fill(self, valMap, **kwargs):
        # pg._g('fill1', self, valMap)
        self.update(**kwargs)
        valMap.update(self.bcIDSVals)
        return valMap
        # valMap.update(dict(zip(self.bcIDSVals.keys(),
        #                        self.bcIDSVals.values())))
        # pg._g('fill2', self, valMap)


class DirichletManager(object):
    """Manage Dirichlet Boundary conditions."""

    def __init__(self, bc={}, dynamic=False):
        """Construct.

        Arguments
        ---------
        bc: dict:
            Extract boundary conditions from `bc` dictionary.
            Dictionary {FEASpace:BC dictionary}
        dynamic: bool
            Flag if the Dirichlet values should be cached or recalculated
            on every use. Default is False.
        """
        self.clean()
        self._bc = []           ## ??
        self._vals = None       ## ??
        self._valMap = None     ## {nodeID: value} # global for all spaces
        self._dynamic = dynamic

        for space, bc in bc.items():
            self.addSpace(space, bc)

        ## Copy of system matrix needed for rhs change of
        # matrix reduction for non homogeneous dirichlet values
        self._S0 = None

        ## Cache for S * uDirchlet, not cached for dynamic = True
        self._cacheSmultDirVals = None

        self.mask = None
        """Mask for Dirichlet values in system matrix."""
        self.diag = None
        """Diagonal values index for Dirichlet values in system matrix."""
        self.diagMask = None
        """Mask for diagonal Dirichlet values in system matrix."""


    def clean(self):
        """Reset the Dirichlet manager.

        Cleans cache and all stored values.
        """
        # pg._r('clean')
        self._bc = []
        self._valMap = None
        self._S0 = None                     # system matrix if any
        self._cacheSmultDirVals = None      # system matrix if any


    def addSpace(self, space, bcDict):
        """Extract Dirichlet-ish boundary conditions associated to a space."""
        # pg._y('add space', self, space, bcDict)
        if not isinstance(space, FEASpace) or not isinstance(bcDict, dict):
            print('feaSpace:', space)
            print('bcDict:', bcDict)
            pg.critical("Can only add a dictionary of Dirichlet "
                        "boundary conditions for FEASpace.")

        for key, vals in bcDict.items():
            bv = {}
            if key.lower() == 'neumann':
                continue
            elif key.lower() == 'assemble':
                continue
            elif key.lower() == 'robin':
                continue

            elif key.lower() == 'dirichlet':
                ## get list of [boundary, values]
                boundVals = pg.solver.parseArgToBoundaries(vals, space.mesh)
                for b, v in boundVals:
                    for n in b.nodes():
                        bv[n] = v

            elif key.lower() == 'node':
                if isinstance(vals, list):
                    if isinstance(vals[0], list):
                        ### [[nodeID, val], ]
                        for IDV in vals:
                            nodeID = IDV[0]
                            val = IDV[1]
                            bv[space.mesh.node(nodeID)] = val
                    else:
                        ### [nodeID, val]
                        nodeID = vals[0]
                        val = vals[1]
                        bv[space.calc.node(nodeID)] = val

            elif key.lower() == 'nodes':
                nodes = []
                if isinstance(vals, list):
                    nodes = vals[0]
                    val = vals[1]
                else:
                    nodes = space.mesh.nodes()
                    val = vals

                if callable(val):
                    for n in nodes:
                        bv[n] = val
                else:
                    pg.critical("Nodes boundary need a callable(Node)")

            elif key.lower() == 'no-slip' or key.lower() == 'fixed':
                bms = pg.solver.parseMarkersDictKey(vals,
                                            space.mesh.boundaryMarkers())
                for bm in bms:
                    boundVals = pg.solver.parseArgToBoundaries(
                                        {bm:[0.0, 0.0, 0.0]}, space.mesh)
                    #pg.solver.parseArgToBoundaries({1:[1.0, 1.0]}, mesh)
                    for b, v in boundVals:
                        for n in b.nodes():
                            bv[n] = v

            elif key.lower() == 'no-flow':
                bms = pg.solver.parseMarkersDictKey(vals,
                                            space.mesh.boundaryMarkers())
                for bm in bms:
                    n_ = space.mesh.findBoundaryByMarker(bm)[0].norm()
                    if abs(n_[0]) == 1.0:
                        boundVals = pg.solver.parseArgToBoundaries(
                                        {bm:[0.0, None, None]}, space.mesh)
                    elif abs(n_[1]) == 1.0:
                        boundVals = pg.solver.parseArgToBoundaries(
                                        {bm:[None, 0.0, None]}, space.mesh)
                    elif abs(n_[2]) == 1.0:
                        boundVals = pg.solver.parseArgToBoundaries(
                                        {bm:[None, None, 0.0]}, space.mesh)
                    else:
                        pg.critical('Only coordinate aligned boundaries'
                                    'can be free-slip for now.')
                        #TODO read about Nitsche's method

                    for b, v in boundVals:

                        for n in b.nodes():
                            bv[n] = v
                #pg.critical('implement me')

            elif key.lower() == 'free-slip':
                pg.critical('implement me')

            elif key.lower() == 'fix':
                def _getFixedNode(p):
                    nNID = space.mesh.findNearestNode(p)
                    nN = space.mesh.node(nNID)

                    if nN.pos().dist(p) > 1e-6:
                        pg.warning(f"DirichletManager: Nearest node: {nN} "
                                    "doesn't fit desired fixed "
                                    f"position {p}.")
                    return nN

                ## Dirichlet for [pos, val] or [[pos, val],] or [[pos,], val]
                if isinstance(vals, list):
                    if pg.isPos(vals[0]) and len(vals) > 1:
                        ## [pos, val]
                        #pg._b(vals[0], vals[1])
                        bv[_getFixedNode(vals[0])] = vals[1]
                    elif pg.isPosList(vals[0]) and \
                        (len(vals) > 1 and not pg.isPosList(vals[1])):
                        ## [[pos], val]
                        #pg._r(vals[0], vals[1])
                        bv[_getFixedNode(vals[0])] = vals[1]
                    else:
                        for valPair in vals:
                            ## [[pos, val], ]
                            #pg._b(valPair[0], valPair[1])
                            bv[_getFixedNode(valPair[0])] = valPair[1]

                ## Dirichlet for [pos, val] or [[pos,], [val,]] or [[pos], val]
                # if isinstance(vals, list) and len(vals) == 2:
                #     if pg.isPos(vals[0]):
                #         ## [pos, val]
                #         bv[_getFixedNode(vals[0])] = vals[1]
                #     elif pg.isPosList(vals[0]):
                #         for i, p in enumerate(vals[0]):
                #             if hasattr(vals[1], '__iter__') and \
                #                 len(vals[1]) == len(vals[0]):
                #                 ## [[pos], [val]]
                #                 pg._b(vals[0][i], vals[1][i])
                #                 bv[_getFixedNode(vals[0][i])] = vals[1][i]
                #             else:
                #                 ## [[pos], val]
                #                 bv[_getFixedNode(vals[0])] = vals[1]
                #     else:
                #         pg.error(f"Dirichlet manager: '{key}' key expects "
                #                 "pos or [pos,] as first list entry.")
                else:
                    pg.error(f"Dirichlet manager: '{key}' key expects: "
                    "[pos, val], [[pos, val],] or [[pos,], val]")
            else:
                if key.lower() != 'neumann' and key.lower() != 'assemble':
                    pg.warn("Dirichlet manager don't know how to handle "
                            "boundary condition:", key)

            ## Add ids and values to the global map
            self.add(space, list(bv.keys()), list(bv.values()))


    def add(self, space, nodes, vals):
        """Add Dirichlet boundary condition for the FEAspace."""
        # pg._y('add:', space, nodes, vals)
        #bc = DirichletBC(self, space, dict(zip(nodes, np.zeros(len(nodes)))))
        bc = DirichletBC(self, space, nodes, vals)
        self._bc.append(bc)
        nr = len(self._bc) - 1
        #bc.update(vals)
        #pg._y('add2:', self._bc)
        return nr


    def createValueMap(self, **kwargs):
        """Create and return global dofID to value dictionary."""
        if self._dynamic is True or self._valMap is None or \
            len(self._valMap.keys()) == 0:

            self._valMap = {}
            for bc in self._bc:
                # doesnt work without return
                self._valMap = bc.fill(self._valMap, **kwargs)

        return self._valMap


    @property
    def idx(self):
        """Return global list of Dirichlet nodes indieces for all spaces."""
        return list(self.createValueMap().keys())


    def apply(self, obj, rhs=None, **kwargs):
        """Apply Dirichlet Boundary condition.

           Apply Dirichlet Boundary condition to matching
           system matrix and right hand side.

        Arguments
        ---------
        obj: SparseMatrix | RVector
            System matrix or right hand side vector.

        rhs: RVector
            Right hand side vector. If None, obj is used.

        Keyword Args
        ------------
        removeEntries: bool[False]
            Remove dof from obj, instead of just mask them.

        Returns
        -------
        A, b or None:
            Inline remove and returns nothing. Return copy
            of A and b with removeEntries == True
        """
        with pg.tictoc('prep'):
            if self._dynamic is True:
                ### delete cached values so they will be created for next call
                self._valMap = None
                self._cacheSmultDirVals = None

            if rhs is not None:
                # rhs need mat processed before
                A = self.apply(obj, **kwargs)
                b = self.apply(rhs, **kwargs)
                if A or b:
                    return A, b
                return

            with pg.tictoc('collect values'):
                vm = self.createValueMap(**kwargs)
                uInd = list(vm.keys())
                vals = list(vm.values())

            # pg._y(self._valMap)
            # pg._b(self._dynamic, obj.ndim, len(uInd))

            if len(uInd) == 0:
                return

            if len(vals) != len(uInd):
                # print(len(obj), type(obj), obj)
                # print(len(vals), type(vals), vals)
                pg.critical('check me')

        if obj.ndim == 2:
            # copy original to keep it for rhs multiplication
            with pg.tictoc('S'):

                with pg.tictoc('copy'):
                    self._S0 = obj.copy()
                    self._cacheSmultDirVals = None
                # pg.toc('prep', stop=True)
                #
                ###
                # think about reduce with different diagonal values
                # instead of 1.0
                # to potential improve matrix ill.-conditiones
                # (variance of eigenvalues very large or very small
                # other diagonal elements,
                # e.g. very big K values)
                with pg.tictoc('reduce'):
                    if kwargs.get('removeEntries', False) is True:
                        # pg._b(len(obj.values()), id(obj))
                        A = pg.math.matrix.removeEntries(obj,
                                                         rows=uInd, cols=uInd)
                        #pg._b(len(obj.values()), id(obj))
                        return A
                        #pg._b(len(A.values()))
                    else:
                        #pg._b(len(obj.values()), id(obj), uInd)
                        if isinstance(obj, pg.SparseMatrix):
                            if self.mask is None:
                                with pg.tictoc('create mask'):
                                    self.mask = obj.createReduceMask(uInd)
                                    self.diag = obj.createDiagonalMask()
                                    self.diagMask = self.mask[
                                    np.nonzero(np.isin(self.mask,
                                                       self.diag))[0]]

                            obj.setMaskValues(self.mask, 0.0)
                            obj.setMaskValues(self.diagMask, 1.0)
                        else:
                            pg.math.matrix.reduceEntries(obj, uInd)

        elif obj.ndim == 1:
            ### right hand side correction for non homogeneous Dirichlet values

            with pg.tictoc('rhs'):
                if not kwargs.pop('setOnly', False):
                    with pg.tictoc('1'):
                        if 1 or any(v != 0 for v in vals):
                            if self._S0 is not None and self._cacheSmultDirVals is None:
                                uDir = np.zeros(len(obj))
                                uDir[uInd] = vals
                                # works only for symmetric matrices,
                                # else use single columns
                                ## see : compare_explicite_fem1d.ipynb(test=4,
                                #                                   Var=1, bcVar=2)
                                self._cacheSmultDirVals = self._S0 * uDir

                            if self._cacheSmultDirVals is not None:
                                obj -= self._cacheSmultDirVals

                obj[uInd] = vals

                if kwargs.get('removeEntries', False) is True:
                    mask = np.zeros(len(obj), dtype=bool)
                    mask[uInd] = True
                    b = np.ma.array(obj, mask=mask)
                    return b


class NeumannManager(object):
    """Manage Neumann Boundary conditions."""

    def __init__(self, bc={}, dynamic=False):
        """Construct.

        TODO
        ----
            * refactor with Dirichlet Manager

        Args
        ----
        bc: dict:
            Extract boundary conditions from bc dictionary.
            Dictionary {FEASpace:BC dictionary}
        """
        self.boundVals_ = {} # space: [[boundary, func], ]

        for space, bc in bc.items():
            self.addSpace(space, bc)


    def addSpace(self, space, bcDict):
        """Space : BCDict."""
        if not isinstance(space, FEASpace) or not isinstance(bcDict, dict):
            print('feaSpace:', space)
            print('bcDict:', bcDict)
            pg.critical("Can only add a dictionary of Neumann "
                        "boundary conditions for FEASpace.")

        if not space in self.boundVals_:
            self.boundVals_[space] = []

        for bcName, bc in bcDict.items():

            if bcName.lower() == 'neumann':

                boundVals = pg.solver.parseArgToBoundaries(bc,
                                                           space.mesh)

                for [b, v] in boundVals:

                    #pg._g(b, v)
                    if isinstance(v, FEAFunction3) or \
                        (hasattr(v, 'valueSize') and v.valueSize() == 3):

                        self.boundVals_[space].append([b,
                                               FEAFunctionDotNorm(v, name='_')])
                    else:
                        self.boundVals_[space].append([b, v])


    def apply(self, rhs, **kwargs):
        """Fill rhs from registered [[boundaries, values],] list."""
        from .elementMats import mulE
        for space, bv in self.boundVals_.items():

            for b, v in bv:
                #pg._y(b, v)

                if 0:
                    with pg.tictoc('assemble.2b'):
                        with pg.tictoc('assemble.2b.1'):
                            uE = space.uE(b, scale=1, core=True)
                        with pg.tictoc('assemble.2b.2'):
                            A = mulE(uE, v, **kwargs, core=True)
                        #print(A)
                        with pg.tictoc('assemble.2b.3'):
                            rhs.add(A)
                else:
                    with pg.tictoc('assemble.2a'):
                        (space*v).assemble(onBoundaries=[b.id()],
                                    RHS=rhs, **kwargs, core=True)


def applyRHSBoundaryConditions(bcs, rhs=None, mat=None, **kwargs):
    """Apply right-hand side boundary conditions."""
    if rhs is None:
        rhs = pg.Vector(0)
    if isinstance(list(bcs.keys())[0], FEASpace):
        for space, b in bcs.items():

            applyBoundaryConditions(b, space, mat=mat, rhs=rhs,
                                    #noDirichlet=True,
                                    **kwargs)
    else:
        pg.critical('bcs key need to be FEASpace:', bcs)
    return rhs


def applyDirichlet(space, bc, LHS=None, RHS=None, **kwargs):
    """Syntactic sugar to apply Dirichlet boundary conditions."""
    dirichlet = DirichletManager({space:{'Dirichlet':bc}})
    dirichlet.apply(LHS, RHS, **kwargs)
    return dirichlet


def applyBoundaryConditions(bcs, space, mat=None, rhs=None,
                            **kwargs):
    """Apply boundary conditions to system matrix and rhs.

    Arguments
    ---------
    bcs: dict
        -'assemble': {boundary: FEAExpression}
            Assemble the FEA expression into rhs array
        -'assemble Neumann': {boundary: callable}
            Create FEA expression for Neumann boundary condition with a
            callable(p, boundary), p is a position on the
            boundary and selected for the necessary quadrature points.
    """
    bct = dict(bcs)

    if len(rhs) < space.dofs.stop:
        rhs.resize(space.dofs.stop)

    mesh = space.mesh

    if 'assemble' in bct:
        bc = bct.pop('assemble')
        for key, op in bc.items():

            bIDS = pg.solver.boundaryIdsFromDictKey(mesh, key)

            for k, bID in bIDS.items():
                op.assemble(onBoundaries=bID, RHS=rhs, LHS=mat, **kwargs)

    # if 'assemble Neumann' in bct:
    #     pg.critical('in use?')
    #     # same like 'assemble': space*funct, ->refactor
    #     bc = bct.pop('assemble Neumann')

    #     for key, func in bc.items():
    #         bIDS = pg.solver.boundaryIdsFromDictKey(mesh, key)

    #         # pg._y(bIDS)
    #         for k, bID in bIDS.items():
    #             if len(rhs) < space.dofs.stop:
    #                 rhs.resize(space.dofs.stop)

    #             if isinstance(func, FEAFunction3):
    #                 rhs[0:space.dofs.stop] += \
    #                     (space*(norm(space)*func)).assemble(onBoundaries=bID,
    #                                                         **kwargs)
    #             else:
    #                 rhs[0:space.dofs.stop] += \
    #                     (space*func).assemble(onBoundaries=bID, **kwargs)

    if 'Neumann' in bct:
        #pg._b()
        bc = bct.pop('Neumann')

        for key, func in bc.items():
            with pg.tictoc('assemble.0'):
                bIDs = pg.solver.boundaryIdsFromDictKey(mesh, key)

            # pg._y(func, type(func), f'F3: {isinstance(func, FEAFunction3)}',
            #       hasattr(func, 'valueSize'), bIDs, key, space)

            #TODO, FEAOP without space should be
            # FEAFunction (refactor FEAFunction)

            if isinstance(func, FEAOP) and len(func.spaces) > 0:
                if isinstance(space, VectorSpace):
                    for bID in bIDs.values():
                        (func*norm(space)).assemble(onBoundaries=bID,
                                                    RHS=rhs, LHS=mat, **kwargs)
                else:
                    for bID in bIDs.values():
                        func.assemble(onBoundaries=bID,
                                          RHS=rhs, LHS=mat, **kwargs)

            elif isinstance(func, FEAFunction3) or \
               (hasattr(func, 'valueSize') and func.valueSize() == 3):

                ## for each [marker, list[bounds]]
                #for k, bID in bIDs.items():
                for bID in bIDs.values():

                    with pg.tictoc('assemble.1'):
                        ## cache me!
                        FN = FEAFunctionDotNorm(func, name='_')

                    if 0:
                        with pg.tictoc('assemble.2b'):
                            from .elementMats import mulE
                            for ib in bID:
                                boundary = space.mesh.boundary(ib)
                                uE = space.uE(boundary, scale=1, core=True)
                                A = mulE(uE, FN, **kwargs)
                                #print(A)
                                rhs.add(A)
                    else:
                        with pg.tictoc('assemble.2a'):
                            R = space*FN
                            R.assemble(onBoundaries=bID,
                                       RHS=rhs, **kwargs, core=True)
            else:

                ## for each [marker, list[bounds]]
                for _k, bID in bIDs.items():
                    #if len(rhs) < space.dofs.stop:
                    #    rhs.resize(space.dofs.stop)
                    (space*func).assemble(onBoundaries=bID,
                                          RHS=rhs, **kwargs)

                    #rhs[0:space.dofs.stop] +=

    if 'Robin' in bct:

        bc = bct.pop('Robin')
        with pg.tictoc('robin'):
            # {marker(s):[beta, u0], }
            for key, rbn in bc.items():

                bIDS = pg.solver.boundaryIdsFromDictKey(mesh, key)

                beta = rbn[0]
                u0 = rbn[1]
                #print(beta, u0)
                # [[marker, [bID, ]], ]
                for marker, bID in bIDS.items():
                    #pg._b(marker, bID, mat, rhs)
                    (space*(beta*u0)).assemble(onBoundaries=bID, RHS=rhs)
                    (space*(beta*space)).assemble(onBoundaries=bID, LHS=mat)


def solve(L, bc={}, **kwargs):
    """Solve generic finite element problem.

    Arguments
    ---------
    L: FEAOP | PDE | [FEAOP | PDE]
        Finite element problem to solve.
        If L is a list all components will be solved combined.

    bc: dict
        Boundary conditions for the finite element problem.
        Dictionary `{FEASpace:BC dictionary}`.
        See :ref:`userguide-fea-bc-dict`.

    Keyword Arguments
    -----------------
    ic: any
        Initial condition for transient problems.
    solver: str
        Solver to use. If None, the default solver is used.
    times: [float,] | None
        List of times for transient problems.
        For steady problems `solveMultipleTimes` will be used.
    **kwargs: dic()
        Additional keyword arguments forwarded to the solver or to the
        assembling.

    Returns
    -------
    sol: FEASolution
        Solution field. For multiple solutions return list of solutions, which is
        sorted for the dof start index of the associated space.

    """
    # should not be needed anymore
    ## check if L or L==R have space else solve(pde(u)) as symbolic differentiation
    ## with pde and u is expression

    if hasattr(L, 'op') and L.op == '==':

        if isinstance(L.a, (FEAOP, PDE)) and not hasInstance(L.a, FEASpace):
            if not isinstance(L.a, FEAFunction | FEASolutionOP | FEAOP):
                ## left side is string
                if not 'dirac' in str(L.a): ## hackish .. remove me
                    L.a = asFunction(**{getInstanceAssignmentName('f'):L.a})

        if isinstance(L.b, (FEAOP, PDE)) and not hasInstance(L.b, FEASpace):
            if not isinstance(L.b, FEAFunction | FEASolutionOP | FEAOP):
                # is already
                ## right side is string
                if not 'dirac' in str(L.b): ## hackish .. remove me
                    L.b = asFunction(**{getInstanceAssignmentName('f'):L.b})
    else:
        if isinstance(L, (FEAOP, PDE)):
            if not hasInstance(L, FEASpace):
                return asFunction(**{getInstanceAssignmentName('f'):L})

    ## check if L is transient problem and forward if needed
    if isinstance(L, list):
        #pg.critical('check')

        for l in L:
            if not isinstance(l, FEAOP):
                pg._b()
                if 'derive' in l._repr_str_():
                    return solveTransientAlgebraic(L, bc=bc, **kwargs)
                    #return solveTransient(L, bc=bc, **kwargs)
    else:
        #pg._b(isinstance(L, PDE), type(L))
        #if isinstance(L, PDE):
            #L.dump()
        if L.hasDeriveT():
            return solveTransientAlgebraic(L, bc=bc, **kwargs)
            # if 'derive' in str(L):
            #     return solveTransientAlgebraic(L, bc=bc, **kwargs)
                # return solveTransient(L, bc=bc, **kwargs)

    if 'times' in kwargs and kwargs['times'] is not None:
        return solveMultipleTimes(L, bc=bc, **kwargs)

    verbose = kwargs.pop('verbose', False)
    dirichlet = kwargs.pop('dirichlet', None)
    core = kwargs.pop('core', None)
    useMats = kwargs.pop('useMats', core is None) # True if core is unset
    #useMats = kwargs.pop('useMats', True) # True if core is unset
    solver = kwargs.pop('solver', None)
    ws = kwargs.pop('ws', None)

    A = None
    rhs = None

    def _getSpaces(L):
        if isinstance(L, list):
            spaces = L[0].spaces
            for i in range(1, len(L)):
                spaces.update(L[i].spaces)
        else:
            spaces = L.spaces

        spaces = [s for s in spaces if s.forAssembling]
        spaces = sorted(spaces, key=lambda x: x.dofs.start)

        if pg.core.deepDebug() == -1:
            pg._g('Spaces:', spaces, [s.dof for s in spaces])

        return spaces

    with pg.tictoc(key='solve'):

        ## check if L is PDE then generate FEA formulation
        #pg._b(L, type(L), isinstance(L, PDE), isStrongFormPDE(L))
        if isinstance(L, PDE):
            L = L.weakForm
        elif isStrongFormPDE(L) and not isinstance(L, list):
            #pg._g(L)
            L = PDE(L).weakForm
            #pg._g(L)

        spaces = _getSpaces(L)

        if isinstance(L, list):
            dof = spaces[-1].dofs.stop
            ops = L[0]## needed?
            #pg._g('Spaces:', spaces, [s.dof for s in spaces])
            # print(L[0], core, useMats, kwargs)
            #pg.core.setDeepDebug(-1)
            rhs = pg.Vector(dof)
            #A, rhs = L[0].assemble(core=core, useMats=useMats, **kwargs)
            #pg.core.setDeepDebug(0)
            #ws['Kpp'] = pg.core.RSparseMapMatrix(A)

            # print("L:", A.shape)
            # print("R:", rhs.shape)

            for i, Li in enumerate(L):
                #print(Li)
                ret = Li.assemble(core=core, useMats=useMats,
                                       LHS=A, RHS=rhs, **kwargs)
                if isinstance(ret, tuple):
                    A, rhs = ret
                else:
                    A = ret
                # print("L:", A.shape)
                # print("R:", rhs.shape)

        else:
            dof = L.dof
            ops = L

            with pg.tictoc(key='assembling'):
                # pg._y('Assembling', L, core, useMats, kwargs)
                A, rhs = L.assemble(core=core, useMats=useMats, **kwargs)
                #pg._y(rhs)
        #pg.show(A)
        #pg._y(min(A.values()), max(A.values()), np.median(A.values()))

        if isinstance(rhs, pg.core.MatrixBase):
            print(rhs)
            print(rhs.shape)
            pg.critical('fix me')

        if len(rhs) != dof:
            rhs.resize(dof)

        if len(rhs) != dof or A.shape[0] != dof:
            print('L', dof)
            print('rhs:', len(rhs))
            print('A:', A.shape)
            pg.critical('fix me')

        dirichlet = None

        ### bc need to be associated with a FEASpace (if more than one exists)
        ### if not given identify the space for bc
        ### bc treatment: Dirichlet last

        if len(bc.keys()) > 0:

            ## search through all bc dict to find a single space
            if not isinstance(list(bc.keys())[0], FEASpace):
                space = None
                for _bckey, bci in bc.items():
                    if isinstance(bci, dict):
                        for _bcID, bcj in bci.items():
                            if hasattr(bcj, 'spaces') and space is None:
                                if len(bcj.spaces) > 1:
                                    print(bcj.spaces)
                                    pg.critical('Cannot find suitable space '
                'for the given boundary condition. More than one space found.')
                                elif len(bcj.spaces) == 1:
                                    s = list(bcj.spaces)[0]
                                    if space is not None and space != s:
                                        print(space)
                                        print(bcj.spaces)
                                        pg.critical('Cannot find suitable space'
                'for the given boundary condition. More than one space found.')

                                    else:
                                        space = list(bcj.spaces)[0]

                if space is None:
                    for s in ops.spaces:
                        if s.forAssembling is True \
                            and not isinstance(s, ConstantSpace):

                            if space is not None and space != s:
                                print(space)
                                print(ops.spaces)
                                pg.critical('Cannot find suitable space for'
                ' the given boundary condition. More than one space found.')
                            else:
                                space = s

                bcC = {space:bc}
            else:
                bcC = bc

            dirichlet = DirichletManager(bcC,
                                         dynamic=kwargs.pop('dynamic', False))

            with pg.tictoc(key='apply BC'):
                applyRHSBoundaryConditions(bcC, rhs, mat=A, **kwargs)
        else:
            pg.warning('No boundary conditions defined. '
                       'The default of homogeneous Neumann BC lead to '
                       'ambiguous results.')

        if dirichlet is not None:
            with pg.tictoc(key='dirichlet'):
                dirichlet.apply(A, **kwargs)
                dirichlet.apply(rhs, **kwargs)


        with pg.tictoc(key='linSolve'):
            u = linSolve(A, rhs, verbose=verbose, solver=solver,
                         **kwargs)
            # u = pg.solver.linSolve(A, rhs, verbose=verbose, solver=solver,
            #                        **kwargs)

    if ws is not None:
        ws['A'] = A
        ws['rhs'] = rhs

    ret = []
    for s in spaces:
        ret.append(s.split(u,
                     skipHistory=kwargs.pop('skipHistory', False),
                     time=kwargs.get('time', None)))

    if len(ret) == 1:
        return ret[0]
    return ret


def splitLeftRight(L):
    """Separate weak FEA expression into left and right part."""
    if hasattr(L, 'op') and L.op == '==':
        # needed ?
        # terms = L.a.expand()
        # for t in terms:
        #     pg._b(t)
        #     if isBilinearForm(t):
        #         pg._g(t)
        #     elif isLinearForm(t):
        #         pg._y(t)
        #     else:
        #         pg.critical("Unknown term in weak FEA expression:", t)

        return L.a, L.b

    return L, 0


def splitDeriveTime(pde):
    """Separate PDE expression into time depending part and the rest.

    Ensure the rest part is a PDE expression.
    """
    #pg._b(pde)
    terms = pde.expand()
    ret = None

    dt = None
    ## search for term that contains time derivative
    for t_ in terms:

        if not isinstance(t_, (int, float)) and t_.hasDeriveT():
            dt = t_
        else:
            if ret is None:
                ret = t_
            else:
                ret +=t_

    ### don't call str(FEAFunction) .. this will give html representation.
    #dt.dump() # fix me .. don't use str
    if 0 and '-' in str(dt):
        ## needed .. there is no test for this?
        dt = -dt
        #ret = -ret ## wannehave
        ret = -1*ret


    if not isinstance(ret, PDE):
        ret = PDE(ret)
    # pg._g(dt)
    # pg._g(ret)

    return dt, ret


def splitTransientLeftRight(pde):
    r"""Split transient PDE into left and right part.

    c \partial_t u = L(u) + R

    return Finite element formulation in weak form for L, R, c
    """
    dT, L = splitDeriveTime(pde)

    # pg._y(dT)
    # pg._y(L)
    deriveTerm = dT.a if dT.op == '*' else 1.0

    L, R = splitLeftRight(L.weakForm)

    return L, R, deriveTerm


def ensureInitialSolution(ic, space, **kwargs):
    """Ensure ic a suitable initial condition."""
    if pg.isArray(ic) or pg.isScalar(ic):
        ic = FEASolution(space, name=space.name + '_h',
                         values=ic, time=kwargs.pop('time', 0.0))

    if isinstance(ic, FEASolution):
        # ensure there are at least initial values for starting time
        if len(ic.history) == 0:
            ic.values = np.zeros(space.dof)

        ## ensure the initial time is been stored
        if len(ic.times) == 0:
            ic.times.append(kwargs.pop('time', 0.0))

    elif isinstance(ic, Dirac) \
        or hasInstance(ic, Dirac) and len(ic.spaces) == 0:

        ic = ensureInitialSolution((space*ic).assemble(useMats=True),
                                   space, **kwargs)
    elif callable(ic):
        ic_ = np.array([call(ic, _, **kwargs) for _ in space.mesh.positions()])
        ic = ensureInitialSolution(ic_, space, **kwargs)
    else:
        print(ic, type(ic))
        pg.critical("Can't interpret initial values. "
                    "Give: array, scalar or FEASolution.")

    return ic


def solveMultipleTimes(L, bc, times, **kwargs):
    """Solve PDE for multiple times.

    Not suitable for transient problems, use
    :func:`solveTransientAlgebraic` instead.

    PDE or weak formulation does not depend on time but the some coefficients
    for the right hand side might.

    Function speedup by reusing the system matrix with a one-timed factorized
    direct solver.
    Only the right hand side is updated for each time step.

    The Dirichlet boundary conditions need to be constant over time.

    Arguments
    ---------
    L: FEAOP | PDE
        Finite element problem or weak formulation to solve.
        If pde is a list all components will be solved combined.
    bc: dict
        Boundary conditions for the finite element problem.
        Dictionary {FEASpace:BC dictionary}.
        See :ref:`userguide-fea-bc-dict`.
    times: list
        List of time steps to solve the problem for.

    Keyword Arguments
    -----------------
    progress: bool
        If True, a progress bar is shown.
    """
    # core = kwargs.pop('core', None)
    # useMats = kwargs.pop('useMats', core == None) # True if core is unset

    # pg._b()
    P = kwargs.pop('progress', None)
    P = pg.utils.ProgressBar(len(times)) if P is True else lambda t: t

    if isinstance(L, PDE):
        L = L.weakForm
    elif isStrongFormPDE(L) and not isinstance(L, list):
        L = PDE(L).weakForm

    rhs, lhs = L.findForms()
    S = None
    b = pg.Vector(L.dof)
    solver = None

    for i, ti in enumerate(times[0:]):
        P(i)
        with pg.tictoc('S0'):
            if S is None:
                dirichlet = DirichletManager(bc)
                S = assembleBilinearForm(lhs)
                dirichlet.apply(S)
                solver = pg.core.LinSolver(S)

        with pg.tictoc('rhs'):
            b *= 0.0
            b = assembleLinearForm(rhs, b=b, time=ti)
            applyRHSBoundaryConditions(bc, b)

        with pg.tictoc('dir'):
            dirichlet.apply(b)

        # solve system and assign values
        with pg.tictoc('sol'):
            u_ = solver.solve(b)

        uh = L.split(u_, time=ti)

    return uh


def solveTransientAlgebraic(pde, ic, bc, times, theta=1, **kwargs):
    """Solve transient PDE with algebraic approach using matrices."""
    P = kwargs.pop('progress', None)
    L, R, c = splitTransientLeftRight(pde)

    space = None
    if len(L.spaces) == 1:
        space = list(L.spaces)[0]
    else:
        pg.critical('implement me')

    if isinstance(R, (int, float)) and R == 0:
        R = space*0

    ic = ensureInitialSolution(ic, space, time=times[0], **kwargs)

    kwargs['bc'] = {space:bc} ## for neumann BC .. create manager for it?
    ##TODO refactor into BCManager
    dirichlet = DirichletManager({space:bc},
                                 dynamic=kwargs.pop('Dirichlet_dynamic', True))
    neumann = NeumannManager({space:bc},
                              dynamic=kwargs.pop('Neumann_dynamic', True))


    if kwargs.get('adaptiveTime', 0.0) > 0:
        P = pg.utils.ProgressBar(100) if P is True else None  # in percent t

        uh = solveAlgebraicAdaptiveTime(ic, L, R, c, dirichlet, times,
                                        theta=theta, progress=P,
                                        tol=kwargs.pop('adaptiveTime', 0.0),
                                        **kwargs)

    else:
        P = pg.utils.ProgressBar(len(times)) if P is True else None

        uh = solveAlgebraicCrankNicolson(ic, L, R, c, dirichlet,
                                          neumann, times,
                                          theta=theta, progress=P,
                                          **kwargs)
    return uh


def solveAlgebraicCrankNicolson(uh, LHS, RHS, c, dirichlet,
                                 neumann, times, theta,
                                 **kwargs):
    """Solve transient problem with Crank-Nicolson scheme.

    Algebraic, i.e., matrix based approach.

    TODO:
        [] A-stationary
        [] A-transient
        [] M-stationary
        [] M-transient
        [] R-stationary
        [] R-transient
        [] bc-stationary
        [] bc-transient
        [] dt-konstant
        [] dt-variable

    Arguments
    ---------
    uh: FEASolution
        Initial solution.
    LHS: FEAOperator
        Left hand side of the weak form.
    RHS: FEAOperator
        Right hand side of the weak form.
    c: FEAFunction | scalar
        Time derivative coefficient.
    dirichlet: dict
        Boundary conditions.
    neumann: dict
        Neumann boundary conditions.
    times: list
        Time steps.
    theta: float
        Crank-Nicolson scheme parameter.
    """
    kwargs.pop('useMats', None)
    P = kwargs.pop('progress', None)
    if P is None:
        P = lambda t: t

    RisTransient = kwargs.pop('R_dynamic', True)

    lSolve = kwargs.pop('solver', 'cholmod')
    if isinstance(lSolve, str):
        lSolve = LinSolver(solver=lSolve,
                           verbose=kwargs.get('verbose', False))

    skipHistory = kwargs.pop('skipHistory', False)

    with pg.tictoc('CrankNicolson'):

        with pg.tictoc('assemble_0'):
            A = LHS.assemble(useMats=True, time=times[0], **kwargs)
            #print(A.values(), np.mean(A.values()), np.std(A.values()))
            s = list(LHS.spaces)[0]

            if pg.isScalar(c):
                M = (s*s).assemble(useMats=True, time=times[0], **kwargs)
                # pg._b(s)
                # pg._b(s.order)
                # pg._b(M.values(), np.mean(M.values()), np.std(M.values()))
                ## keep mass matrix for caching
                s._M = pg.matrix.asSparseMatrix(M)
                M = M*c

            else:
                M = (s*c*s).assemble(useMats=True, time=times[0], **kwargs)

            Rk = RHS.assemble(useMats=True, time=times[0], **kwargs)

            with pg.tictoc(key='apply BC'):
                neumann.apply(Rk, time=times[0], **kwargs)

                # applyRHSBoundaryConditions(kwargs['bc'],
                #                           Rk, time=times[0], **kwargs)

            Rprev = Rk

            # needed?
            # if not skipHistory:
            #     if hasattr(uh, 'times') and len(uh.times) == 0:
            #         uh.times.append(times[0])

            # dirichlet.apply(A) #
            # dirichlet.apply(M) #
            A = pg.matrix.asSparseMatrix(A)
            M = pg.matrix.asSparseMatrix(M)

            S = pg.matrix.asSparseMatrix(M+A) ## TODO WHY? compare pattern

            # pyM = pg.matrix.asCSR(M)
            # pyRk = np.array(Rk)
            #Ms = pg.matrix.asSparseMatrix(M)

        lastDt = -1
        rhs = None

        for k in range(1, len(times)):
            P(k)
            dt = times[k] - times[k-1]

            with pg.tictoc('lhs'):

                if abs(dt-lastDt)/dt > 1e-10:
                    with pg.tictoc('S'):
                        ##TODO: this only works if A (coefficients)
                        ## does not depend on t. Fix and create test
                        ##
                        S = M + A * (theta * dt)
                        #S.update(M.values() + A.values() * (theta * dt))
                    with pg.tictoc('dir'):
                        dirichlet.apply(S, time=times[k], **kwargs)
                    with pg.tictoc('solver.factorize'):
                        lSolve.factorize(S)
                        # lSolve = LinSolver(S, solver=solver,
                        #                 verbose=kwargs.get('verbose', False))
                    lastDt = dt
                    _MACache = None
                else:
                    pass

            with pg.tictoc('rhs'):

                if RisTransient:
                    with pg.tictoc('RK'):
                        Rprev = Rk
                        if RHS.isZero is False:
                            Rk = RHS.assemble(useMats=True, time=times[k],
                                              **kwargs)
                        else:
                            Rk = np.zeros_like(Rprev)

                with pg.tictoc(key='apply BC'):

                    neumann.apply(Rk, time=times[k], **kwargs)
                    # applyRHSBoundaryConditions(kwargs['bc'],
                    #                            Rk, time=times[k], **kwargs)

                with pg.tictoc('sum'):
                    if theta == 1:
                        ## implicit
                        if rhs is None:
                            rhs = M * uh.values + dt * Rk
                        else:
                            # rhs = M * uh.values + dt * Rk
                            ### by factor 2 faster
                            pg.core.mult_Mv_add_sv(rhs, M, uh.values, dt, Rk)

                    else:
                        ## Crank Nicolson
                        if _MACache is None:
                            _MACache = M - A * (dt*(1.-theta))
                            #_MACache = pg.core.toSparseMatrix(M - A * (dt*(1.-theta)))

                        rhs = _MACache * uh.values \
                                + (1-theta) * dt * Rprev  \
                                +     theta * dt * Rk

                with pg.tictoc(key='apply dirichlet'):
                    dirichlet.apply(rhs, time=times[k], **kwargs)

                u_ = lSolve(rhs)
                uh = s.split(u_, skipHistory=skipHistory, time=times[k])

    return uh


def solveAlgebraicAdaptiveTime(uh, L, R, c, dirichlet, times,
                               theta=0.5, tol=1e-2, **kwargs):
    """Solve transient problem with adaptive time step size.

    Experimental, not tested yet.
    """
    tictoc = pg.tictoc

    with tictoc('adaptive time'):

        P = kwargs.pop('progress', None)
        if P is None:
            P = lambda t: t

        uh.times = [times[0]]
        tMax = times[-1]

        dt = tMax / 2

        t = 0
        p = 1
        if theta == 0.5:
            p = 2

        s = list(L.spaces)[0]

        while t < tMax:
            P(t/tMax*100)

            uLo = solveAlgebraicCrankNicolson(uh, L, R, c, dirichlet,
                                                times=[t, t+dt], theta=theta,
                                                skipHistory=True)

            uHi = solveAlgebraicCrankNicolson(uh, L, R, c, dirichlet,
                                                times=[t, t+dt/2, t+dt], theta=theta,
                                                skipHistory=True)

            errorEst = normL2(uHi-uLo) / (2**p - 1)

            rho = 0.9
            dtNew = dt * (rho * tol / errorEst)**(1/p)

            #print(errorEst, tol, dtNew)
            if errorEst > tol:
                dt = dtNew
                continue

            uh.values = s.split(uHi.values, skipHistory=True, time=t).values
            t += dt

            dt = dtNew

    return uh


def solveTransient(pde, ic=None, bc={}, times=None, **kwargs):
    """Rename.. transient isn't good
    """
    pg.critical('inuse?')
    pg._g(pde)
    L, R, deriveTerm = splitTransientLeftRight(pde)

    # pg._r(f'deriveTerm: {deriveTerm}')
    # pg._r(f'L:{L}')
    # pg._r(f'R:{R}')

    if len(L.spaces) > 1:
        pg._r(L)
        pg.critical('implement me for mixed formulations')

    s = list(L.spaces)[0]

    if pg.isArray(ic):
        ic = FEASolution(s, name='uh', values=ic)
    uh = ic
    uh.times = [times[0]]

    #print(s)
    theta = kwargs.pop('theta', 1)

    assembleArgs = {'useMats':True}

    P = pg.utils.ProgressBar(len(times))


    # Lu = L(uh)
    #Lu = (grad(s)*grad(uh))

    Rk = R.assemble(useMats=True, time=times[0])

    for k in range(1, len(times)):
        P(k)
        dt = times[k]-times[k-1]

        if 0 and theta == 1:
            # fixme !! see transient mms example with b values != 0.. CN with 1 works!!
            uh = solve(s*s + dt*L == s*uh + dt*R,
                       bc=bc, time=times[k], dynamic=True, **assembleArgs)
        else:
            # uh = solve(s*s + theta * dt*L == s*uh - (1-theta)*dt*Lu + (1-theta)*dt*R + theta*dt*R,
            #            bc=bc, time=times[k], dynamic=True, **assembleArgs)

            dirichlet = DirichletManager({s:bc}, dynamic=True)

            M = (s*deriveTerm*s).assemble(useMats=True, time=times[k])
            A = L.assemble(useMats=True, time=times[k])
            S = M + theta * dt * A
            dirichlet.apply(S, time=times[k], **kwargs)
            solver = pg.solver.LinSolver(S)

            #A_ = L.assemble(useMats=True, time=times[k-1])
            RkPrev = Rk
            Rk = R.assemble(useMats=True, time=times[k])

            rhs = (M - (1-theta) * dt * A) * uh.values + \
                  (1-theta) * dt * RkPrev + \
                      theta * dt * Rk

            dirichlet.apply(rhs, time=times[k], **kwargs)
            u_ = solver(rhs)
            uh = s.split(u_)

            # uh = solve(s*s + theta * dt*L == s*uh - (1-theta)*dt*Lu + (1-theta)*dt*R + theta*dt*R,
            #            bc=bc, time=times[k], dynamic=True, **assembleArgs)


        uh.times.append(times[k])

    return uh


def parse(*args, **vars):
    """Parse strings into FEAFunctions.

    TODO
    ----
    * argument safeguard to catch missing kwargs
    * simple validity check of str (number '(' == number ')' )

    Note
    ----
        Prefer 'sympyfied' instead of rationals, e.g., 1/2 might
        be 0.50000000001, so the use of 0.5 directly might improve
        simplifications.

    Allways us `*` where it should be, e.g., `xy` will be interpreted as
    a variable with this name and also `x y` will no be `x*y`.

    Keyword Arguments
    -----------------
    loc: dict
        Dictionary of local known functions or translations.

    returnDicts: False

    *: string
        Return dicts, instead a list of functions.

    simplify: bool=False
        Simplify result, use with care you want to reuse the expression.

    Returns
    -------
    *vars: []
        List of converted functions in the order of vars.

    Or alternative give two dictionaries.

    f: dict
        All {vars: FEAFunction}
    loc, dict
        local dictionary for {name: sympy Expressions}

    Example
    -------
    >>> from oskar import parse, pprint
    >>> f = parse(f='x')
    >>> pprint(f)
    f(x) = x
    >>> print(f(1)) # single arguments is x-coordinate
    1.0
    >>> f = parse(f='x+y')
    >>> pprint(f)
    f(x,y) = x + y
    >>> print(f([1, 2.0])) # First argument is interpreted as position
    3.0
    >>> print(f([[1., 2.0]]*2)) # or as list of position
    [3. 3.]
    >>> # combine multiple functions with auto substitution
    >>> f, r = parse(f='r', r='sqrt(x²+y²)')
    >>> pprint(f)
    f(x,y) = sqrt(x² + y²)
    >>> print(f([3.0, 4.0]))
    5.0
    """
    if len(args) > 0:
        if len(args) == 1:
            vars[f'{getInstanceAssignmentName("dummy_0")}'] = vars[0]
        elif len(args) > 1:
            for i, a in enumerate(args):
                vars[f'dummy_{i}'] = a
        return parse(**vars)

    with pg.tictoc('parse'):
        # pg._g(vars)
        import sympy as sp
        from sympy import parse_expr, lambdify, Matrix, diff, simplify, Symbol
        from sympy.vector import CoordSys3D, gradient, divergence
        from sympy.physics.vector import ReferenceFrame, vector, dynamicsymbols

        ### optional return functions, loc
        returnDicts = vars.pop('returnDicts', False)
        wantSimplify = vars.pop('simplify', False)
        maxIter = vars.pop('maxIter', len(list(vars.keys())))

        loc = vars.pop('loc', {})

        ### search for FEAFunctions and use there expression, if they are priori
        ### created by toFunctions
        for k, v in loc.items():
            if hasattr(v, 'expr') and v.expr != '':
                loc[k] = v.expr

        ### ensure FEAOP are translated into strings
        for k, v in vars.items():

            if isinstance(v, FEAOP | PDE) and not hasattr(v, 'expr'):

                vars[k] = str(v).replace('(pnt)', '')
                #pg._g(str(v))

                def _fillExprIntoLoc_(o, loc):
                    #pg._b(o, type(o), hasattr(o, 'expr'), hasattr(o, 'field'))
                    if hasattr(o, 'expr'):
                        #pg._r(o.expr)
                        loc[str(o).replace('(pnt)', '')] = o.expr
                    if hasattr(o, 'field'):
                        _fillExprIntoLoc_(o.field, loc)
                    if hasattr(o, 'a'):
                        _fillExprIntoLoc_(o.a, loc)
                    if hasattr(o, 'b'):
                        _fillExprIntoLoc_(o.b, loc)

                _fillExprIntoLoc_(v, loc)

        def _div(u):
            """Refactor with div."""
            # pg._r('** Symbolic div **')
            # pg._y(u)
            # print(hasattr(u, 'shape'), u.shape, len(u.shape))
            if hasattr(u, 'shape') and len(u.shape) == 2:
                return _tensorDiv(u)
                #return sp.simplify(_tensorDiv(u))
            #return sp.simplify(divergence(u))
            return divergence(u)

        def _identity(dim):
            """Refactor with identity."""
            return sp.eye(dim)

        # def _trace(u):
        #     """ Refactor with trace
        #     """
        #     return sp.simplify(u.trace())

        def _tensorDiv(u):
            """Return divergenz for tensor of type 2.

            return [du_i_x/d_x + du_i_y/dy + du_i_z/dz] i = 1..dim
            """
            # pg._r('** Symbolic tensor div **')
            # pg._y(u)
            _C = CoordSys3D('C')

            dim = u.shape[0]
            ret = sp.zeros(1, dim)
            x = [_C.x, _C.y, _C.z]

            for i in range(dim):
                for j in range(dim):
                    ret[i] += sp.diff(u[i, j], x[j])

            return ret

        _C = CoordSys3D('C', variable_names=['x', 'y', 'z'],
                             vector_names=['i', 'j', 'k'])
        t = dynamicsymbols('t', positive=True)

        loc.update({#'C': _C,
                    'x': _C.x,
                    'y': _C.y,
                    'z': _C.z,
                    'N': sp.Symbol('N'), ## overwrite N for sp.numeric evaluation
                    #'t': t,### check use of it
                    'div': _div,
                    'divergence': _div,
                    'grad': grad,
                    'Laplace': lambda _u: _div(grad(_u)),
                    'laplace': lambda _u: _div(grad(_u)),
                    'derive': diff,
                    'sym': sym,
                    'pi': sp.pi,
                    '1/2': 0.5,
                    '1 / 2': 0.5,
                    'I': I,
                    #'I': _identity,
                    'tr': trace,
                    'trace': trace,
                    })

        ## don't overwrite existing loc with symbols
        loc = dict(list(symbols().items()) + list(loc.items()))

        #loc.update(SYMBOLS)
        # print(loc)
        ret = {}

        # do it a few times to ensure all nested unknowns are parsed,
        # independed of kwargs order
        for i in range(maxIter):
            for k, v in list(vars.items()):

                if hasattr(v, 'expr'):
                    loc[k] = v.expr
                    ret[k] = v.expr
                    continue

                if pg.isScalar(v):
                    #v = str(v)
                    loc[k] = v #expr
                    ret[k] = v
                    continue

                if isinstance(v, str):
                    nO = v.count('(')
                    nC = v.count(')')
                    if nO != nC:
                        pg.critical(f"Paranthesis missmatch for '{v}': open: " + \
                                    f"{nO} closing: {nC}")

                if isinstance(v, str):
                    v = v.replace('[', '')  ## list is interpreted as R3 function
                    v = v.replace(']', '')
                    #v = v.replace('(p)', '')
                    v = v.replace('(pnt)', '')
                    v = v.replace('²', '**2')
                    v = v.replace('³', '**3')
                    v = v.replace('⁴', '**4')
                    v = v.replace('⁵', '**5')
                    v = v.replace('⁶', '**6')
                    v = v.replace('^', '**')
                    v = v.replace('1/2', '0.5')
                    v = v.replace('1 / 2', '0.5')

                #pg._g(type(v), v)
                # from sympy.parsing.sympy_parser import (standard_transformations,
                #                                         implicit_multiplication,
                #                                         implicit_multiplication_application,
                #                                         )
                # transformations = standard_transformations + \
                #                 (implicit_multiplication, implicit_multiplication_application)

                if isinstance(v, str):
                    #pg._b(v)
                    with pg.tictoc('sp.parse'):
                        expr = parse_expr(v, local_dict=loc, evaluate=True,
                                    #transformations=transformations
                                    )
                else:
                    #pg._r(v)
                    #expr = v
                    #continue
                    mapping = { Symbol('x'): _C.x,
                                Symbol('y'): _C.y,
                                Symbol('z'): _C.z,
                                #Symbol('lam'): Symbol('lambda'),
                                }

                    if isinstance(v, (tuple, list)) and len(v) == 3:
                        expr = Matrix([asFunction(v[0]),
                                       asFunction(v[1]),
                                       asFunction(v[2])])

                    else:
                        expr = v.xreplace(mapping)
                #pg._y(expr)

                if wantSimplify is True:
                    expr = simplify(expr)

                ## simple auto conversion from (x,y) -> sp.Matrix(x,y)
                if isinstance(expr, tuple):
                    expr = simplify(expr)

                # pg._r(expr)
                # print(type(expr),
                #       isinstance(expr, sp.physics.vector.vector.Vector),
                #       isinstance(expr, tuple), isinstance(expr, list)
                #       )

                if isinstance(expr, sp.core.containers.Tuple):
                    #N = ReferenceFrame('N', indices=['x', 'y', 'z'])
                    if len(expr.args) == 2:
                        #expr = N.x*expr[0] + N.y*expr[1] + N.z*0
                        expr = _C.i*expr[0] + _C.j*expr[1] + _C.k*0
                    elif len(expr.args) == 3:
                        ## will lead to 2D if expr[2] is 0
                        #expr = C.i*expr[0] + C.j*expr[1] + C.k*expr[2]
                        expr = Matrix([expr[0], expr[1], expr[2]])
                        #expr = N.x*expr[0] + N.y*expr[1] + N.z*expr[2]

                loc[k] = expr

                if isinstance(expr, (sp.physics.vector.vector.Vector |
                                     sp.matrices.MatrixBase)):
                    ### from e.g, _tenserDiv()
                    #pg._g(expr)
                    ## moveme to toFEAFunction!
                    ret[k] = toFEAFunc(expr, isVec=True, name=k)

                ### We need the wrapper (closure) since pure lambda loose reference
                # elif hasattr(expr, 'components'):

                #     comp = []
                #     if 1 or expr.components.get(C.i, 0) != 0:
                #         comp.append(expr.components.get(C.i, 0))

                #     if 1 or expr.components.get(C.j, 0) != 0:
                #         comp.append(expr.components.get(C.j, 0))

                #     if 0 or expr.components.get(C.k, 0) != 0:
                #         comp.append(expr.components.get(C.k, 0))

                #     ### maybe better use all components to ensure if its allways in R3
                #     vexpr = Matrix(comp)

                #     # pg._y(vexpr)
                #     # pg._g(expr)
                #     ret[k] = toFEAFunc(vexpr, isVec=True, name=k)
                else:
                    ret[k] = toFEAFunc(expr, isVec=False, name=k)

    if returnDicts is True:
        return ret, loc

    if len(ret.values()) == 1:
        return list(ret.values())[0]
    return list(ret.values())


def asFunction(*args, **kwargs) -> FEAFunction:
    """Convert string to a single FEAFunction.

    Similar like :py:mod:`oskar.solve.parse` if you like this name more.
    It allows for function creation without keyword name.

    Arguments
    ---------
    *args: [string]
        Forwarded to :py:mod:`oskar.solve.parse` with default name be the
        variable name or 'dummy_#' for more than one argument.

    Keyword Arguments
    -----------------
        Forwarded to :py:mod:`oskar.solve.parse`.

    Returns
    -------
    FEAFunction
        Single FEAFunction if there is only one arg but multiple kwargs.

    Example
    -------
    >>> from oskar import asFunction, pprint
    >>> f = asFunction('x²')
    >>> pprint(f)
    f(x) = x²
    >>> print(f(2))
    4.0
    """
    name = getInstanceAssignmentName("dummy_0")
    if len(args) == 1:
        kwargs[name] = args[0]
    elif len(args) > 1:
        for i, a in enumerate(args):
            kwargs[f'dummy_{i}'] = a

    ret = parse(**kwargs)
    if len(args) == 1:
        if isinstance(ret, FEAFunction):
            return ret
        return ret[list(kwargs.keys()).index(name)]
    return ret



def asFunctions(**kwargs) -> FEAFunction:
    """Convert a keyword dictionary to a multiple FEAFunctions."""
    return parse(**kwargs)
