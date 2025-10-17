#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Classes to hold and manage the Finite Element Space.
"""
import numpy as np
import pygimli as pg

from . utils import getInstanceAssignmentName, __newFieldOrder__
from . feaSolution import FEASolution
from . feaOp import FEAOP
from . op import OP, hasInstance

from . elementMats import duE, uE, createEMap, identityE


def findFEASpace(op):
    """Find FEASpace from expression.

    Attributes
    ----------
    op: OP
        Expression to search for FEASpace.
    """
    def _findSpace(o):
        #pg._g(o, type(o))
        if isinstance(o, FEASpace):
            return o
        if hasattr(o, 'space'):
            return o.space
        a = None
        b = None
        if hasattr(o, 'a'):
            a = _findSpace(o.a)
        if hasattr(o, 'b'):
            b = _findSpace(o.b)
        return a or b
    space = _findSpace(op)

    if space is None:
        pg.critical(ValueError, f'Operator {op} have no FEASpace.')

    return space


def hasFEASpace(op):
    """Check if an expression has a FEASpace.

    Attributes
    ----------
    op: OP
        Expression to search for FEASpace.
    """
    if isinstance(op, FEASpace):
        return True
    if isinstance(op, OP):
        return hasInstance(op, FEASpace)

    return False


# TODO refactor with FEAOP
class FEASpace:
    r"""Finite Element Approximation Space.

    The finite element method approximates a function :math:`u_h` by a linear
    combination of the base functions :math:`N_j` of a finite element space
    :math:`V_h`

    .. math::
        u_h(\boldsymbol{r})
            = \sum_j \hat{u}_j N_j(\boldsymbol{r})
            \quad\text{with}\quad j=1,\ldots,\mathcal{N}

    The coefficients :math:`\hat{u}_j` are discrete values for
    the degrees of freedom (dof) of the
    finite element space.
    The finite element space is the set of all base functions
    and defined by the mesh
    and the polynomial interpolation order of the base functions.

    See user guide for more details: :ref:`userguide-fea`.
    """

    __array_ufunc__ = None
    def __init__(self, mesh, order:int=None, p:int=1, dofOffset:int=0,
                 name:str=None):
        """Initialize a FEASpace.

        Arguments
        ---------
        mesh: pg.Mesh
            Mesh for the FEA space.
        order: long
            Integration order
        p: long
            Polynomial degree for base functions. Only p=1 and p=2 at
            the moment.
        dofOffset: long
            Index offset for the degrees of freedom for resulting vector or
            system matrix. Only useful if the resulting assembling's are not
            part of a block matrix.
        name: str
            Name of the space.
        """
        if name is None:
            self._name = getInstanceAssignmentName(self.__class__.__name__)
        else:
            self._name = name

        # indicate this space is linked to a FEA solution
        self.forAssembling = True
        self._solution = None
        self._values = None # values array reshaped for self.mesh
        self._valuesRaw = None # values array for self.mesh
        self._valuesHistory = [] # store old values, i.e., for time lapse

        self._calcMesh = None
        self._inputMesh = None
        self.p = p

        orderGuess = 2

        if mesh is not None:
            #self._inputMesh = mesh
            if p == 1:
                #self._calcMesh = pg.Mesh(mesh)
                if mesh.cell(0).shape().rtti == \
                    pg.core.MESH_SHAPE_QUADRANGLE_RTTI:
                    orderGuess = 2 # for quad + BC: Neumann + fix
                else:
                    #orderGuess = 1 # fails for quad + BC: Neumann + fix

                    # 2 better for advection problems
                    orderGuess = 2 # maybe better default for all
                #orderGuess = 3
            elif p == 2:
                #self._calcMesh = mesh.createP2()
                orderGuess = 2
                #orderGuess = 4
            else:
                pg.critical('Higher p order than 2 not yet implemented. Sorry.')

            #self._calcMesh.createNeighborInfos()

            self.mesh = mesh

        if order is None:
            self.order = orderGuess
        else:
            self.order = order

        self.useCore = False
        # degrees of freedom for the whole space
        self.u = None
        self.du = None
        self._lastEnt = None
        self.dofOffset = dofOffset
        self.nCoeff = 1
        self._elastic = False
        self.voigt = True
        self.neg = False
        self.cache = True

        self._hash = None

        self.reset()


    def __hash__(self):
        """Return hash value for this space.

        Only the mesh and the order are used to create a unique hash.
        Any solutions are ignored.
        """
        if self._hash is None:
            self._hash = hash(self.mesh) ^ self.order
        return self._hash


    def __str__(self):
        """Return short (general) name, e.g., for print()."""
        return self.name


    def __repr__(self):
        """Return long (unique) name."""
        return str(self)

    # def __reduce__(self):
    #     """Pickle function.
    #     """
    #     return (self.__class__,
    #             (None, ),
    #             self.__dict__.copy())

    def __getstate__(self):
        """Unpickle function.

        We don't pickle caches.
        """
        self.reset()
        state = self.__dict__.copy()
        return state


    def __setstate__(self, state):
        """Unpickle function."""
        self.__dict__.update(state)


    @property
    def name(self):
        """Attribute name of the space."""
        return self._name


    @property
    def solution(self):
        """Solution for this space.

        Attribute solution is a FEASolution, i.e., the approximated field,
        if there was a appropriate calculation.
        """
        return self._solution


    def split(self, *args, **kwargs):
        """Create a FEASolution. *abstract interface*."""
        pg.critical('Nothing known to do, cannot be called from'
                    'base:', self)


    def reset(self):
        """Delete caches."""
        ## caches for {order:elementMap}
        self._uMat = {}
        self._gradUMat = {}
        self._divUMat = {}
        self._identityMat = {}
        self.eMapCache = {}
        self._hash = None


    @property
    def mesh(self):
        """Read only access to input FEA mesh."""
        return self._calcMesh


    @mesh.setter
    def mesh(self, mesh):
        """Set the input FEA mesh.

        Attributes
        ----------
        mesh: pg.Mesh
            Mesh for the FEA space.
        """
        self._inputMesh = pg.Mesh(mesh)
        if self.p == 1:
            self._calcMesh = pg.Mesh(mesh)
        elif self.p == 2:
            self._calcMesh = mesh.createP2()
        else:
            pg.critical('no p refinement strategy', self.p)

        self._calcMesh.createNeighborInfos()
        self.reset()


    @property
    def inputMesh(self):
        """Read only access to input FEA mesh."""
        return self._inputMesh


    @property
    def elastic(self):
        """Is the space contains any tensor mapping for elasticity.

        Attribute elastic is a boolean, if True the element matrices
        are computed with Voigt or Kelvin mapping.
        """
        return self._elastic


    @elastic.setter
    def elastic(self, e:bool):
        """Set the elastic attribute.

        Attributes
        ----------
        e: bool
            If True the element matrices are computed with Voigt or
            Kelvin mapping.
        """
        self._elastic = e
        self.reset()


    @property
    def dofs(self):
        """Return the degrees of freedom for this space.

        Returns
        -------
        slice:
            Slice object for the degrees of freedom from first dof to last dof.
        """
        return slice(self.dofOffset, self.dofOffset + self.dof)


    @property
    def dof(self):
        """Return the number of degrees of freedom for this space."""
        return self.nCoeff * self.dofPerCoeff


    @property
    def dofPerCoeff(self):
        """Return the number of degrees of freedom per coefficient."""
        return self._calcMesh.nodeCount()


    def uMat(self, order=None):
        """Return elementMatrixMap for u."""
        if order is None:
            order = self.order

        if not order in self._uMat:
            pg.debug('create uMat for:', self)
            self._uMat[order] = createEMap(name=f'{self}', space=self)

            with pg.tictoc(f'create u map: {self.name}'):
                pg.core.createUMap(self.mesh, order,
                                   self._uMat[order],
                                   nCoeff=self.nCoeff, dofOffset=self.dofOffset)

            self._uMat[order].dofs = self.dofs
        return self._uMat[order]


    def gradUMat(self, order=None):
        """Read only access to input FEA mesh."""
        if order is None:
            order = self.order

        if not order in self._gradUMat:
            pg.debug('create gradUMat for:', self)
            self._gradUMat[order] = createEMap(name=f'grad({self})', space=self)

            with pg.tictoc(f'create du map: grad({self.name})'):
                pg.core.createdUMap(self.mesh, order,
                                    self._gradUMat[order],
                                    elastic=self.elastic,
                                    div=False,
                                    kelvin=not self.voigt,
                                    nCoeff=self.nCoeff,
                                    dofOffset=self.dofOffset)

            self._gradUMat[order].dofs = self.dofs
            # pg._g(self._gradUMat.size(),
            #       self._gradUMat.dofA(),
            #       self._gradUMat.dofB())
        return self._gradUMat[order]


    def divUMat(self, order=None):
        """Read only access to input FEA mesh."""
        if order is None:
            order = self.order

        if not order in self._divUMat:
            pg.debug('create div map for:', self)
            self._divUMat[order] = createEMap(name=f'div({self})', space=self)

            with pg.tictoc(f'create map: div({self.name})'):
                pg.core.createdUMap(self.mesh, order,
                                    self._divUMat[order],
                                    elastic=self.elastic,
                                    div=True,
                                    kelvin=not self.voigt,
                                    nCoeff=self.nCoeff,
                                    dofOffset=self.dofOffset)

            self._divUMat[order].dofs = self.dofs
        return self._divUMat[order]


    def identityMat(self, order=None):
        """Create an identity matrix map for this space."""
        if order is None:
            order = self.order

        if not order in self._identityMat:
            pg.debug('create identityMat for:', self)
            self._identityMat[order] = createEMap(name=f'I({self})', space=self)

            with pg.tictoc(f'create map: identity({self.name})'):
                pg.core.createIdentityMap(self.mesh, order,
                                          self._identityMat[order],
                                          nCoeff=self.nCoeff,
                                          dofOffset=self.dofOffset)

            self._identityMat[order].dofs = self.dofs
        return self._identityMat[order]


    def blMat(self, a, b, verbose=False):
        """Get Bilinear Matrix map for Maps a x b.

        Parameters
        ----------
        a: pg.core.ElementMatrixMap
            Left side ElementMatrixMap
        b: pg.core.ElementMatrixMap
            Right side ElementMatrixMap

        Returns
        -------
        pg.core.ElementMatrixMap
            Cached ElementMatrixMap for a x b
        """
        verbose=True
        # TODO Disable caching since Donea-Huerta test (07_advection) fails while
        # reuses Scalar space for each Peclet number .. choose better hash
        # and test with this before reenable this cache
        # add order as key name
        self.cache = False
        if self.cache is True:
            key = f'{a.name}{b.name}'

            if key not in self.eMapCache:
                if verbose:
                    pg.info(f'create BL matrix cache: {self} '
                            f': {a.name} : {b.name}')

                bl = createEMap(name=f'{a}*{b}', space=self)
                a.dot(b, bl)
                self.eMapCache[key] = bl
            else:
                if verbose:
                    pg.info(f'restore BL matrix cache: {self} '
                            f': {a.name} : {b.name}')

            return self.eMapCache[key]
        else:
            bl = createEMap(name=f'{a}*{b}', space=self)
            a.dot(b, bl)
            return bl


    def deform(self, eps):
        self._inputMesh.deform(eps)
        self._calcMesh.deform(eps)
        self.reset()


    def createElementMatrix(self):
        """Create an empty but configured pg.core.ElementMatrix."""
        return pg.core.ElementMatrix(nCoeff=self.nCoeff,
                                     dofPerCoeff=self.dof//self.nCoeff,
                                     dofOffset=self.dofOffset)

    def cell(self, i):
        """Read only access to the FEA mesh."""
        return self.mesh.cell(i)

    def boundary(self, i):
        """Read only access to the FEA mesh."""
        return self.mesh.boundary(i)

    def idx(self, n):
        """Return global node ids."""
        return [self.dofOffset + i*self.dof//self.nCoeff + n.id() \
                for i in range(self.nCoeff)]

    def nodeIdx(self, boundaryMarker):
        """Return all node indices (unique sorted) for boundaries by marker."""
        m = self.mesh
        ids = []
        for b in m.boundaries(m.boundaryMarkers() == boundaryMarker):
            ids.extend([n.id() + self.dofOffset for n in b.nodes()])
        return pg.unique(ids)


    def assemble(self, **kwargs):
        """Fallback for vanilla use."""
        return FEAOP(self).assemble(**kwargs)
        # F = pg.Vector(self.dofs.stop, 0.0)
        # for c in self.mesh.cells():
        #     F.add(self.uE(c, core=core))

    def __mul__(self, b):
        #pg._b(self, 'mul', b) #refactor OP
        #pg._g('FEASpace.mul:', self, type(self), ':',  b, type(b))
        return FEAOP(self, b, op='*')

    def __rmul__(self, b):
        #pg._b(self, 'rmul', b) #refactor OP
        #pg._g('FEASpace.rmul:', self, type(self), ':',  b, type(b))
        return FEAOP(b, self, op='*')

    def __truediv__(self, b):
        return FEAOP(self, b, op='/')

    def __rtruediv__(self, b):
        return FEAOP(b, self, op='/')

    def __add__(self, b):
        # print(self, '+', b) #refactor OP
        return FEAOP(self, b, op='+')

    def __sub__(self, b):
        # print(self, '+', b) #refactor OP
        return FEAOP(self, b, op='-')

    def __neg__(self):
        return FEAOP(self, op='neg')

    def grad(self):
        return FEAOP(self, op='grad')

    def div(self):
        return FEAOP(self, op='div')

    def norm(self):
        return FEAOP(self, op='norm')

    # def sym(self):
    #     return FEAOP(self, op='sym')

    # def tr(self):
    #     return FEAOP(self, op='tr')

    def identity(self):
        # pg._r('FEASpace-identity')
        return FEAOP(self, op='identity')


    def apply(self, ent, core=False, **kwargs):
        if isinstance(ent, int):
            return self.uE(self.cell(ent), core=core)
        return self.uE(ent, core=core)


    def gradE(self, ent, scale=1.0, isDivergence=False, core=False):
        """Return the gradient for a given entity as element matrix."""
        # pg._g('du:', id(self), self.order, self.useCore, core)
        if core is True or self.useCore == True:
            self.du = self.createElementMatrix()
            # pg._g(id(self), self.order)
            #  const MeshEntity & ent, Index order,
            #             bool elastic, bool sum, bool div, bool kelvin
            self.du.grad(ent, self.order, elastic=self.elastic, sum=False,
                         div=isDivergence, kelvin=not self.voigt)
        else:
            if self.du is None or ent != self._lastEnt or 1:
                self._lastEnt = ent
                self.du = duE(ent, scale=scale,
                              order=self.order,
                              nCoeff=self.nCoeff,
                              dofPerCoeff=self.mesh.nodeCount(),
                              dofOffset=self.dofOffset,
                              elastic=self.elastic,
                              mesh=self.mesh,
                              isDivergence=isDivergence,
                              voigtNotation=self.voigt)
                # print(self.du)

        return self.du


    def uE(self, ent, scale=1.0, f=None, core=False):
        """"""
        # pg._g('u:', id(self), self.order, self.useCore, core)
        if core is True or self.useCore == True:
            self.u = self.createElementMatrix()
            # pg._g(scale)
            self.u.pot(ent, self.order, sum=False)
            # pg._g(self.u)
            self.u *= scale

        else:
            # print("u({0})".format(ent.id()), self)
            if self.u is None or ent != self._lastEnt or 1:
                self._lastEnt = ent
                self.u = uE(ent, f=f, scale=scale,
                            order=self.order,
                            nCoeff=self.nCoeff,
                            dofPerCoeff=self.mesh.nodeCount(),
                            dofOffset=self.dofOffset, mesh=self.mesh)
                # pg._r('d', self.u.rows())
                # pg._r('d', self.u.cols())
                # pg._r('d', self.u.mat())
                # pg._r('d', self.u.colIDs())
                # pg._r('d', self.u.colIDs()[0])
                # pg._r('d', self.u.rowIDs())
                # pg._r('d', self.u.mat().cols())
                # pg._r('d', self.u.mat().rows())
                # pg._r('d', self.u)

        return self.u


    def identityE(self, ent, core=False):
        """"""
        self.i = identityE(ent,
                           order=self.order,
                           nCoeff=self.nCoeff,
                           dofPerCoeff=self.mesh.nodeCount(),
                           dofOffset=self.dofOffset)
        return self.i


class ConstantSpace(FEASpace):
    r"""ConstantSpace is a special FEASpace for constant values.

    It is used to represent constant values in the finite element space.
    """

    def __init__(self, val=0.0, p=1, dofOffset=0, nCoeff=1, name=None):
        super().__init__(None, order=0, p=p, dofOffset=dofOffset, name=name)
        self.nCoeff = nCoeff
        self.order = 0
        # empty fallback mesh for matrix automatization
        self._calcMesh = pg.Mesh()
        self.val = val


    @property
    def dof(self):
        """Return the number of degrees of freedom for this space."""
        return self.nCoeff


    def split(self, u, skipHistory=False, time=None):
        """Split the values from global vector u and create a FEASolution."""
        return u[self.dofs]


class ScalarSpace(FEASpace):
    r"""ScalarSpace is a special FEASpace for scalar values.

    It is used to represent scalar field in the finite element space.
    """

    def __init__(self, mesh, order=None, p=1, dofOffset=0, name=None):
        self._values = None
        super().__init__(mesh, order=order, p=p, dofOffset=dofOffset,
                         name=name)
        #self.values = np.zeros(self.dof)

    @property
    def values(self):
        #pg._y('get:', self, id(self._values))
        if self._values is None:
            #pg.error("No values defined .. returning unstored zeros")
            return np.zeros(self.dof)
        return self._values


    @values.setter
    def values(self, v):
        if pg.isScalar(v):
            v = np.full(self.dof, v)

        if len(v) == self.mesh.nodeCount():
            self._values = v
            self._valuesRaw = v
        else:
            print('values:', v)
            print('mesh', self.mesh)
            pg.critical("Length of array does not fit mesh node count")

        with pg.tictoc('append history'):
            if self._values is not None:
                self._valuesHistory.append(self._values)
                # if len(self._valuesHistory) == 0:
                #     self._valuesHistory = np.asarray([self._values])
                # else:
                #     #self._valuesHistory.append(self._values)
                #     self._valuesHistory = np.append(self._valuesHistory,
                #                                     [self._values.T], axis=0)
                #pg._y('set:', self._valuesHistory.shape)

    @property
    def valuesRaw(self):
        return self._valuesRaw

    def fill(self, val, solution):
        val[self.dofs] = solution.vals

    def split(self, u, skipHistory=False, time=None):
        """Split values from the global vector u and create a FEASolution."""
        #pg._g(self, len(self._valuesHist))
        # valuesRaw 1d array of values per node
        # values nd array of values per node
        #self.valuesRaw = u[self.dofs]
        self.values = u[self.dofs]

        if skipHistory is True:
            solution = FEASolution(self, values=None, name=str(self),
                                   skipHistory=skipHistory)
            return solution

        if self._solution is None:
            self._solution = FEASolution(self, values=None, name=str(self))

        ## solution holds a copy of this space so we need to set values there too
        self._solution.values = self.values

        if time is not None and not skipHistory:
            self._solution.times.append(time)
            # ensure add a missing 0 if the solution wasn't initialized for
            # time dependent
            if len(self._solution.times) == len(self._solution.history) -1:
                self._solution.times.insert(0, 0)

        return self._solution


class VectorSpace(FEASpace):
    r"""VectorSpace is a FEASpace for vector values.

    Represents a vector field in the finite element space.
    """

    def __init__(self, mesh, order=None, p=1, dofOffset=0, elastic=False,
                 name=None):
        super().__init__(mesh, order=order, p=p, dofOffset=dofOffset,
                         name=name)
        self.elastic = elastic
        self.nCoeff = self.mesh.dim()

        if __newFieldOrder__ == True:
            self.values = np.zeros((self.nCoeff,
                                self.dof//self.nCoeff))
        else:
            self.values = np.zeros((self.nCoeff,
                                    self.dof//self.nCoeff)).T

    @property
    def values(self):
        """Get values for this space."""
        return self._values


    @property
    def valuesRaw(self):
        """Get raw values for this space.

        Raw values are the FEA coefficients in a 1d array.
        """
        return self._valuesRaw


    @values.setter
    def values(self, v):
        """Set values for this space."""
        if v.ndim == 1:

            self._valuesRaw = v

            if __newFieldOrder__ == True:
                # (nCoeff, dof) # new -- good
                self._values = np.array(v).reshape(self.nCoeff,
                                                self.dof//self.nCoeff)
            else:
                # (dof, nCoeff) # old -- bad
                self._values = np.array(v).reshape(self.nCoeff,
                                                self.dof//self.nCoeff).T

        else:

            if __newFieldOrder__ == False:
                self._values = v
            else:
                self._values = _toField(v)

            # check transpose or flatten dir
            self._valuesRaw = np.array(self._values.flatten())

        # pg._b(id(self))
        if self._values is not None:
            self._valuesHistory.append(self._values)
            #np.append(self._valuesHistory, self._values)


    def fill(self, val, solution):
        """Set the values from FEASolution."""
        val[self.dofs] = solution.vals.flatten()


    def split(self, u, skipHistory=False, time=None):
        """Split values from the global vector u and create a FEASolution."""
        self.values = u[self.dofs]

        if skipHistory is True:
            solution = FEASolution(self, values=None,
                                   name=self.__str__(),
                                   skipHistory=skipHistory)
            return solution

        if self._solution is None:

            # TODO solution holds an own copy of this space for evaluation
            # (clunky, refactor me!)
            # wannehave: #TestFiniteElementBasics.test_FEA_Expression_Eval fail!
            #self._solution = FEASolution(self, self._values,
            # name=self.__str__())
            # or self._solution.values = self.values

            self._solution = FEASolution(self, values=None,
                                         name=self.__str__(),
                                         skipHistory=skipHistory)
            self._solution.space._valuesHistory.append(self._values)

        else:
            # self_solution holds a copy if this space so copy the values too
            self._solution.values = self.values

        if time is not None and not skipHistory:
            self._solution.times.append(time)

            # ensure add a missing 0 if the solution wasn't initialized for
            # time dependent
            if len(self._solution.times) == len(self._solution.history) -1:
                self._solution.times.insert(0, 0)

        return self._solution


    def identityE(self, ent, dim=None, core=False):
        """Create an identity element matrix for the given entity."""
        self.i = identityE(ent,
                           order=self.order,
                           nCoeff=self.nCoeff,
                           dofPerCoeff=self.mesh.nodeCount(),
                           dofOffset=self.dofOffset,
                           mapping=self.elastic,
                           dim=dim)
        return self.i


def TaylorHood(mesh, order:int=4):
    """Return mixed element Taylor Hood spaces for the given mesh.

    The Mixed space consist of a VectorSpace with quadratic base
    function and a ScalarSpace with linear base function.

    TODO
    ----
        * fix default orders, test with order=2 and 2-1,1

    Arguments
    ---------
    mesh: Mesh
        Pygimli Mesh
    order: int
        Quadrature order for numerical integration.

    Returns
    -------
    v, p:
        VectorSpace, ScalarSpace
    """
    v = VectorSpace(mesh, order=order, p=2)
    p = ScalarSpace(mesh, order=order, p=1,
                    dofOffset=v.dofs.stop, name='p')
    return v, p
