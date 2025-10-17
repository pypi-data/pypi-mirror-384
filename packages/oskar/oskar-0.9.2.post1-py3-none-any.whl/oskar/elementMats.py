#!/usr/bin/env python
r"""Create and handle local Element matrices.

The classes and operators here should usually not used directly.
"""
import numpy as np
import pygimli as pg

from .op import OP
from .utils import call, __newFieldOrder__, asVecField


def createEMap(name, space):
    """Create a new ElementMatrixMap."""
    m = pg.core.ElementMatrixMap()
    m.space = space
    m.name = name
    return m


def createE(nCoeff, dofPerCoeff, dofOffset,
            matX, w, x, ent=None, div=False, order=0, elastic=False):
    """Create a new ElementMatrix."""
    # pg._r(nCoeff, dofPerCoeff, dofOffset,
    #         matX, w, x, ent, div, order)
    E = pg.core.ElementMatrix(nCoeff, dofPerCoeff, dofOffset)
    E.setElastic(elastic)
    E.setDiv(div)
    E.setOrder(order)

    # print(matX[0].shape)
    nVerts = ent.nodeCount()
    if matX is None:
        E.resize(nVerts * nCoeff, 1)
    else:
        E.resize(nVerts * nCoeff, matX[0].shape[0])
    E.setEntity(ent)

    ids = np.zeros(E.rows(), dtype=int)

    for i in range(nCoeff):
        ids[i * nVerts:(i+1) * nVerts] = ent.ids() + i*dofPerCoeff + dofOffset

    E.setIds(ids, [0]*E.cols())

    E._mat = matX
    E._w = w
    E._x = x

    if matX is not None:
        _fillMatX(E)
        integrateE(E, matX, w)
    return E


def isRefImpl(E):
    """Check if ElementMatrix is created by reference implementation."""
    return hasattr(E, '_w')


def _fillMatX(E):
    """Fill the sub matrices of ElementMatrix for reference implementation."""
    if isRefImpl(E) is not True:
        # a was NOT created by reference implementation
        return

    # pg._g(id(E._w), E._w)
    # pg._g(id(E._x), E._x)

    E.setW(E._w)
    E.setX(E._x)
    # pg._y(id(E.x()), E.x())
    # pg._y(id(E.w()), E.w())

    for i, mi in enumerate(E._mat):
        try:
            E.setMatXI(i, mi)
        except RuntimeError:
            print(E)
            print(mi)
            E.setMatXI(i, np.ascontiguousarray(mi))


def setMat(E, mat, dbg=''):
    """Add a data matrix to the ElementMatrix."""
    #pg._b('--'+dbg)
    E.setMat(mat)
    #pg._b('++'+dbg)


def integrateE(E, matX, w):
    """Integrate over the ElementMatrix."""
    #pg._g(E)
    r = np.zeros_like(matX[0])
    for i, w in enumerate(E._w):
        r += matX[i] * w * E.entity().size()
    # print(matX.shape)
    # rt = np.tensordot(matX, w, axes=(0,0))
    # np.assert_allclose(r, rt)

    setMat(E, np.array(r.T), 'intE')

    #pg._g(E.isIntegrated())
    E.integrated(True)
    # pg._g(E.isIntegrated())
    # pg._g(E)


def copyE(A, rows=None, cols=None, matX=None, transpose=False):
    """Create a copy of a ElementMatrix."""
    E = pg.core.ElementMatrix(A)
    # E.setDiv(A.isDiv())
    # E.setEntity(A.entity())

    if hasattr(A, 'isIdentity'):
        #pg._b('äääääääääääääääääääääääääääääääääää')
        E.isIdentity = A.isIdentity

    # print('A.rEntity()',A.rEntity())
    # print('A.pEntity()', A.pEntity())
    # print('A.entity()', A.entity())

    # sys.exit()

    if isRefImpl(A):
        E._w = A._w
        E._x = A._x

    # E._mesh = A._mesh
    # E._nCoeff = A._nCoeff

    # if hasattr(A, '_ref'):
    #     pg.critical('needed?')
    #     E._ref

    if rows is None:
        rows = A.mat().rows()
    if cols is None:
        cols = A.mat().cols()

    if transpose is True:
        E.resize(cols, rows)

        E.setIds(A.colIDs(), A.rowIDs())
        setMat(E, A.mat().T, 'copyE')
        E.integrated(True)

        if matX is None:
            E._mat = np.copy(A._mat)
        else:
            E._mat = matX

        for i, m in enumerate(E._mat):
            E._mat[i] = m.T
    else:
        E.resize(rows, cols)
        E.setIds(A.rowIDs(), A.colIDs())
        # setMat(E,A.mat())
        if matX is None:
            if hasattr(A, '_mat'):
                E._mat = np.copy(A._mat)
        else:
            E._mat = matX

    _fillMatX(E)

    E.mulR = A.mulR
    E = _applyMulR(E)

    return E


def _applyMulR(E, **kwargs):
    """Apply mulR to ElementMatrix."""
    if pg.isScalar(E.mulR):
        if E.mulR != 1.0:
            E *= E.mulR
            if hasattr(E, '_mat') and E._mat is not None:
                E._mat[:] *= E.mulR
        E.mulR = 1.0
    elif pg.isPos(E.mulR):
        if sum(E.colIDs()) == 0 and E.cols() <= len(E.mulR):
            c = E.mulR
            E.mulR = 1.0
            E = mulE(E, f=c, **kwargs)
        else:
            print(E)
            pg.critical('E is no linear form, cannot apply pos mulR')
    elif E.mulR is None:
        pass
    else:
        c = E.mulR
        E.mulR = 1.0
        E = mulE(E, f=c)
        # print(E.mulR)
        # print(E)
        # pg.critical('implement me')

    return E


def getWeights(e, order):
    """Get integration weights and abscissa for mesh entity.

    Shortcut to get integration weights and abscissa for mesh entity.

    Args
    ----
    e: pygimli:MeshEntity
        Cell or boundary element.

    order: int
        Integration order.

    """
    w = pg.core.IntegrationRules.instance().weights(e.shape(), order)
    x = pg.core.IntegrationRules.instance().abscissa(e.shape(), order)
    return x, w


def uE(c, f=None, scale=1.0, order=2, nCoeff=1, dofPerCoeff=0, dofOffset=0,
       mesh=None, core=False, **kwargs):
    """Create base ElementMatrix."""
    if core is True:
        pg.criticle('implementme')

    # print('uE', c)
    if nCoeff > 1 and dofPerCoeff == 0:
        pg.error('number of coefficents > 1 but no dof given')

    x, w = getWeights(c, order=order)
    # pg._g(x,w)
    nVerts = c.nodeCount()

    nRules = len(x)
    mat = np.zeros((nRules, nCoeff, nVerts*nCoeff))

    for i in range(nRules):
        for n in range(nCoeff):
            mat[i][n][n*nVerts:(n+1)*nVerts] = c.N(x[i])

        if scale != 1.0:
            mat[i] *= scale

    E = createE(nCoeff, dofPerCoeff, dofOffset,
                matX=mat, w=w, x=x, ent=c, order=order)

    if f is not None:
        # pg.core.setDeepDebug(-1)
        # print(f)
        E = mulE(E, f, c=1.0, core=core, **kwargs)
        # pg.core.setDeepDebug(0)
        # exit()
    return E


def createEmptyElementMatrix(nRules, dim, nVerts, nCoeff, mapping=False):
    """Create an empty ElementMatrix with given dimensions."""
    mat = None
    if mapping is True:
        if dim == 2:
            mat = np.zeros((nRules, dim + 1, nVerts*nCoeff))
        elif dim == 3:
            mat = np.zeros((nRules, dim + 3, nVerts*nCoeff))
    else:
        mat = np.zeros((nRules, dim*nCoeff, nVerts*nCoeff))
    return mat


def duE(c, scale=1.0, order=2, nCoeff=1, dofPerCoeff=0, dofOffset=0,
        elastic=False, mesh=None, isDivergence=False, voigtNotation=True,
        core=False):
    """Create a base gradient ElementMatrix."""
    if core is True:
        ## should ne be here
        pg.critical('implement me')

    # print('duE', c, scale, order, nCoeff, dofPerCoeff, dofOffset)
    if nCoeff > 1 and dofPerCoeff == 0:
        pg.error('number of coefficients > 1 but no dofPerCoeff given')

    x, w = getWeights(c, order=order)
    #pg.info(c, order, w, x)
    nVerts = c.nodeCount()
    nRules = len(x)

    # if elastic is True:
    #     pg._b()
    #     if c.dim() == 2:
    #         dN = np.zeros((nRules, c.dim() + 1, nVerts*nCoeff))
    #     elif c.dim() == 3:
    #         dN = np.zeros((nRules, c.dim() + 3, nVerts*nCoeff))
    # else:
    #     dN = np.zeros((nRules, c.dim()*nCoeff, nVerts*nCoeff))

    dN = createEmptyElementMatrix(nRules, c.dim(), nVerts, nCoeff,
                                  mapping=elastic)

    drdx = c.shape().drstdxyz(0, 0)
    drdy = c.shape().drstdxyz(0, 1)
    drdz = c.shape().drstdxyz(0, 2)
    dsdx = c.shape().drstdxyz(1, 0)
    dsdy = c.shape().drstdxyz(1, 1)
    dsdz = c.shape().drstdxyz(1, 2)
    dtdx = c.shape().drstdxyz(2, 0)
    dtdy = c.shape().drstdxyz(2, 1)
    dtdz = c.shape().drstdxyz(2, 2)

    if voigtNotation is True:
        # pg._r('du Voigt')
        a = 1.0
    else:
        # Kelvin
        # pg._y('du Kelvin')
        a = 1./np.sqrt(2.)

    for i in range(nRules):
        dNdr = c.dNdL(x[i], 0)
        dNds = c.dNdL(x[i], 1)
        dNdt = c.dNdL(x[i], 2)

        if c.dim() == 1:
            # print(dN[i])
            # print(dNdr)
            # print(drdx)
            if nCoeff == 1:
                dN[i][0] = (dNdr * drdx) # U/dx
            else:
                dN[i][0][0*nVerts:1*nVerts] = (dNdr * drdx) # U_x/dx
                dN[i][1][1*nVerts:2*nVerts] = (dNdr * drdx) # U_y/dx
        elif nCoeff == 1:
            if c.dim() == 2:
                dN[i][0] = (dNdr * drdx + dNds * dsdx) # U/dx
                dN[i][1] = (dNdr * drdy + dNds * dsdy) # U/dy
            elif c.dim() == 3:
                dN[i][0] = (dNdr * drdx + dNds * dsdx + dNdt * dtdx) # U/dx
                dN[i][1] = (dNdr * drdy + dNds * dsdy + dNdt * dtdy) # U/dy
                dN[i][2] = (dNdr * drdz + dNds * dsdz + dNdt * dtdz) # U/dz
        elif nCoeff == c.dim():
            dNdx = (dNdr * drdx + dNds * dsdx)
            dNdy = (dNdr * drdy + dNds * dsdy)

            if c.dim() == 2:
                if elastic is True:

                    dN[i][0][0*nVerts:1*nVerts] = dNdx # U_x/dx
                    dN[i][1][1*nVerts:2*nVerts] = dNdy # U_y/dy
                    dN[i][2][0*nVerts:1*nVerts] = dNdy * a
                    dN[i][2][1*nVerts:2*nVerts] = dNdx * a
                else:
                    dN[i][0][0*nVerts:1*nVerts] = dNdx # U_x/dx
                    dN[i][1][0*nVerts:1*nVerts] = dNdy # U_x/dy

                    dN[i][2][1*nVerts:2*nVerts] = dNdx # U_y/dx
                    dN[i][3][1*nVerts:2*nVerts] = dNdy # U_y/dy

            if c.dim() == 3:
                dNdx = (dNdr * drdx + dNds * dsdx + dNdt * dtdx)
                dNdy = (dNdr * drdy + dNds * dsdy + dNdt * dtdy)
                dNdz = (dNdr * drdz + dNds * dsdz + dNdt * dtdz)

                if elastic is True:
                    dN[i][0][0*nVerts:1*nVerts] = dNdx
                    dN[i][1][1*nVerts:2*nVerts] = dNdy
                    dN[i][2][2*nVerts:3*nVerts] = dNdz

                    dN[i][3][0*nVerts:1*nVerts] = dNdy * a
                    dN[i][3][1*nVerts:2*nVerts] = dNdx * a

                    dN[i][4][1*nVerts:2*nVerts] = dNdz * a
                    dN[i][4][2*nVerts:3*nVerts] = dNdy * a

                    dN[i][5][0*nVerts:1*nVerts] = dNdz * a
                    dN[i][5][2*nVerts:3*nVerts] = dNdx * a
                else:
                    dN[i][0][0*nVerts:1*nVerts] = dNdx # U_x/dx
                    dN[i][1][0*nVerts:1*nVerts] = dNdy # U_x/dy
                    dN[i][2][0*nVerts:1*nVerts] = dNdz # U_x/dz

                    dN[i][3][1*nVerts:2*nVerts] = dNdx # U_y/dx
                    dN[i][4][1*nVerts:2*nVerts] = dNdy # U_y/dy
                    dN[i][5][1*nVerts:2*nVerts] = dNdz # U_y/dz

                    dN[i][6][2*nVerts:3*nVerts] = dNdx # U_z/dx
                    dN[i][7][2*nVerts:3*nVerts] = dNdy # U_z/dy
                    dN[i][8][2*nVerts:3*nVerts] = dNdz # U_z/dz

        if scale != 1.0:
            dN[i] *= scale

    E = createE(nCoeff, dofPerCoeff, dofOffset,
                matX=dN, w=w, x=x, ent=c,
                div=isDivergence, elastic=elastic)
    return E


def identityE(c, order=2, nCoeff=1, dofPerCoeff=0, dofOffset=0,
              mapping=False, dim=None):
    """Create an identity ElementMatrix.

    Attributes
    ----------
    dim: int
        Dimension of the identity matrix, e.g. 2 for 2D, 3 for 3D.
        If not given, it is determined from the mesh entity.
    """
    if nCoeff > 1 and dofPerCoeff == 0:
        pg.error('number of coefficients > 1 but no dofPerCoeff given')

    x, w = getWeights(c, order=order)
    #pg.info(c, order, w, x)
    nVerts = c.nodeCount()
    nRules = len(x)

    if dim is None:
        dim = c.dim()

    if mapping is True:
        dim = 3

    # if mapping is True:
    #     dN = np.zeros((nRules, c.dim()*nCoeff, nVerts*nCoeff))
    #     pg._b()
    # else:
    dN = createEmptyElementMatrix(nRules, dim, nVerts, nCoeff,
                                  mapping=mapping)

    #dN = np.zeros((nRules, c.dim()*nCoeff, nVerts*nCoeff))

    for i in range(nRules):
        #scale = 1.0
        scale = 1.0/c.size()
        if c.dim() == 1:
            dN[i][0][0:2] = scale
            # print(dN[i])
            # exit()
        elif nCoeff == 1:
            pg.critical('implement me')
            if dim == 2:
                pass
                #dN[i][1] = (dNdr * drdy + dNds * dsdy)
            elif dim == 3:
                pass
                #dN[i][0] = (dNdr * drdx + dNds * dsdx + dNdt * dtdx)
        elif nCoeff == c.dim():
            if dim == 2:
                # checkme or 1/c.size() which leads to integrated=1
                if mapping is True:
                    dN[i][0][:] = scale # U_x/dx
                    dN[i][1][:] = scale # U_y/dy
                else:
                    dN[i][0][:] = scale # U_x/dx
                    dN[i][3][:] = scale # U_y/dy
                    # dN[i][0][0*nVerts:1*nVerts] += 1.0 # U_x/dx
                    # dN[i][3][1*nVerts:2*nVerts] += 1.0 # U_y/dy
            if dim == 3:
                if mapping is True:
                    dN[i][0][:] = scale # U_x/dx
                    dN[i][1][:] = scale # U_y/dy
                    dN[i][2][:] = scale # U_z/dz
                else:
                    dN[i][0][:] = scale # U_x/dx // checkme
                    dN[i][4][:] = scale # U_y/dy // checkme
                    dN[i][8][:] = scale # U_z/dz // checkme
                    # dN[i][0][0*nVerts:1*nVerts] += 1.0 # U_x/dx
                    # dN[i][4][1*nVerts:2*nVerts] += 1.0 # U_y/dy
                    # dN[i][8][2*nVerts:3*nVerts] += 1.0 # U_z/dz

        # if scale != 1.0:
        #     dN[i] *= scale

    E = createE(nCoeff, dofPerCoeff, dofOffset,
                matX=dN, w=w, x=x, ent=c, order=order)

    E.setElastic(mapping)
    E.isIdentity = True

    return E


def symE(A):
    """Create a symmetric ElementMatrix as 0.5 * (A + A.T)."""
    if not hasattr(A, '_w'):
        # assuming non reference core Matrix
        return pg.core.sym(A)
    E = copyE(A)
    r = np.zeros_like(E._mat[0])

    for i, m in enumerate(E._mat):

        if E.entity().dim() == 1:
            m[0] = A._mat[i][0]
        elif E.entity().dim() == 2:
            #xy
            m[1] = 0.5*A._mat[i][1] + 0.5*A._mat[i][2]
            m[2] = np.copy(m[1])

        elif E.entity().dim() == 3:
            #xy
            m[1] = 0.5*A._mat[i][1] + 0.5*A._mat[i][3]
            m[3] = np.copy(m[1])
            #yz
            m[2] = 0.5*A._mat[i][2] + 0.5*A._mat[i][6]
            m[6] = np.copy(m[2])
            #zx
            m[5] = 0.5*A._mat[i][5] + 0.5*A._mat[i][7]
            m[7] = np.copy(m[5])

        r += (m * E._w[i] * E.entity().size())

    setMat(E, np.array(r.T), 'symE')
    E.integrated(True)
    return E


def trE(A):
    """Create a trace for ElementMatrix as I(v) * trace(E)."""
    if pg.isMatrix(A):
        return np.trace(A)

    trace = []
    ### DODO!! check if trace work on integrated matrices too, need fix in mulE
    #for i, m in enumerate(A.mat()):
    if isRefImpl(A):
        E = copyE(A)
        r = np.zeros_like(E._mat[0])

        #pg._g(E._mat)
        #pg._r('')
        for i, m in enumerate(E._mat):
            if len(m) == 1:
                # assuming 1d
                trace.append(m[0])
            elif len(m) == 4:
                # assuming 2d
                trace.append(m[0] + m[3])
                m*= 0
                m[0] = trace[-1]
                m[3] = trace[-1]
            elif len(m) == 9:
                # assuming 3d
                trace.append(m[0] + m[4] + m[8])
                m*= 0
                m[0] = trace[-1]
                m[4] = trace[-1]
                m[8] = trace[-1]
            else:
                print(A)
                print(m)
                pg.critical("Can't determine trace of A. "
                            "Elastic flag need to be false.")

            r += (m * E._w[i] * E.entity().size())

        setMat(E, np.array(r.T), 'trE')
        E.integrated(True)
    else:
        # print(A)
        # if len(A) == 1:
        #     return A[0]

        return pg.core.trace(A)
        #A.traceX()

    #return np.array(trace)
    return E
    # pg._b(E)
    # pg._b(E._mat)
    # # pg._y(np.array(trace))


def mulE(A, f, c=1.0, core=False, **kwargs):
    """Create a multiplication of A * f(x)."""
    from . feaFunction import FEAFunction, FEAFunction3

    if pg.core.deepDebug() == -1:
        A.integrate()

        pg._y('*'*60)
        pg._y(f'** Mul: core:{core}, c:{c}')
        pg._y(f'** \tA: {type(A)} valid: {A.valid()}')
        pg._y(f'\n{A}')
        pg._y(f'f:{type(f)}: {f}\n')
        pg._y(f'** \tf: {type(f)}')
        pg._y('*'*60)

    if sum(A.colIDs()) > 0:

        # assuming an already assembled bilinear expression in A
        if isinstance(f, OP):
            if f.evalOrder != 0:
                pg.warn('A*f: Function f is marked for eval order != 0 but only cell '
                'center values allowed and used here. If you want to apply it '
                'continuously you should reformulate '
                'your equation, e.g. move it inside the bilinear expression.')

            scale = f(A.entity().center())
            A.mulR = A.mulR * scale * c
            return A

        print(f'A:{A}')
        print(f'f:{f}')
        print(f'c:{c}')
        pg.critical("Mul E only non bilinear ElementMatrices")

    ### simple element wise multiplication for two ElementMatrices without
    # bilinear span
    from .elasticity import ElasticityMatrix

    if isinstance(f, pg.core.ElementMatrix):

        A.integrate()
        f.integrate()
        E = copyE(A)
        # x = E._x

        if pg.isScalar(f.mulR) and f.mulR != 1.0:
            E.mulR *= f.mulR

        if isinstance(f.mulR, ElasticityMatrix) or pg.isMatrix(f.mulR):
            ## E * f(C) * I(v)
            if f.entity().dim() == 2:
                if f.mulR.shape == (6,6):
                    if pg.core.deepDebug() == -1:
                        pg._b('E.mat(2D) * C(3D)*I(3)')
                    E.setMat(E.mat()*(np.asarray(f.mat())@f.mulR[:,[0,1,3]]))

                elif f.mulR.shape == (3,3):
                    if pg.core.deepDebug() == -1:
                        pg._b('E.mat(2D) * C(2D)*I(3)')
                    E.setMat(E.mat()*(np.asarray(f.mat())[:,[0,1,3]]@f.mulR))

                else:
                    pg._y('** E', E)
                    pg._y('** f', f)

                    pg.critical("Don't know how to multiply.")
            else:
                if pg.core.deepDebug() == -1:
                    pg._b('E.mat * C*I(v)')
                E.setMat(E.mat()*(np.asarray(f.mat())@f.mulR))
            E.integrated(True)
            return E

        if hasattr(f, 'isIdentity') and f.elastic() is True:

            if f.entity().dim() == 2:
                if pg.core.deepDebug() == -1:
                    print(f'c={c}')
                    pg._b('E(2, mapped) * I(3)')
                E.setMat(E.mat()*(np.asarray(f.mat())[:,[0,1,3]]))
            else:
                if pg.core.deepDebug() == -1:
                    pg._b('E(3, mapped) * I(3)')
                E.setMat(E.mat()*f.mat())
            E.integrated(True)
            return E

        elif E.colIDs() == f.colIDs() and E.rowIDs() == f.rowIDs():
            #pg._r('dddddddddddd')
            if pg.core.deepDebug() == -1:
                pg._b('E.mat() * f.mat()')

            ### mainly used for E*I .. needed?
            #E.setMat(E.mat()*(f.mat()/E.entity().size()))
            E.setMat(E.mat()*f.mat())
            E.integrated(True)
            return E
        else:
            pg._y(f'** \tA: {type(A)} valid: {A.valid()}')
            pg._y(f'\n{A}')
            pg._y(f'** \tA: {type(B)} valid: {B.valid()}')
            pg._y(f'\n{B}')
            pg.critical("Don't know how to multiply.")


    if pg.isPos(A.mulR) or (pg.isScalar(A.mulR) and A.mulR != 1.0):
        if pg.isScalar(A.mulR):
            c = c * A.mulR
        elif pg.isPos(A.mulR):
            c = c * np.array(A.mulR)
        else:
            print('c:', c)
            print('A', A)
            print('A.mulR', A.mulR)
            pg.critical('implement me')

        A.mulR = 1.0

    nRules = len(A.w())

    def _createFAtCellCenter(f, A, **kw):
        if callable(f):
            return call(f, A.entity().center(),
                        entity=A.entity(), **kw)
        return f

    def _createFAtNodes(f, A, **kw):
        if callable(f):
            # pg._b('++++++++', len(A.entity().nodes()), kw)
            return call(f, A.entity().nodes(),
                        entity=A.entity(), **kw)
        return f

    def _createFAtQuads(f, A, **kw):
        if pg.isScalar(f):
            return np.full(nRules, f)

        if callable(f):
            if f.evalOrder == 0:
                #fi = np.full(nRules, _createFAtCellCenter(f, A, **kw))
                fi = np.array([_createFAtCellCenter(f, A, **kw)]*nRules)
            elif f.evalOrder == 1:
                pg.critical('implement me')
            else:
                fi = []
                for i, w in enumerate(A.w()):
                    # pg._g(f, A.entity().shape().xyz(A.x()[i]),
                    #           A.entity())
                    fi.append(call(f, A.entity().shape().xyz(A.x()[i]),
                              entity=A.entity(), **kw))
            return np.array(fi)
        return f

    def _createF(f, A, **kw):
        """Create aux function values for ElementMatrix."""
        #pg._b(f)
        if hasattr(f, 'op') and f.op == '*' and \
            hasattr(f.a, 'evalOrder') and hasattr(f.b, 'evalOrder'):
            ### for space * solution * function
            ### solution and function can life on different spaces itself
            _a = _createF(f.a, A, **kw)
            _b = _createF(f.b, A, **kw)
            # pg._g(f'f.a: {f.a} continuous: {f.a.evalOrder}')
            # pg._y(f'a: {_a}', pg.isPos(_a), pg.isPosList(_a))
            # pg._g(f'f.b: {f.b} continuous: {f.b.evalOrder}')
            # pg._y(f'b: {_b}', pg.isPos(_b), pg.isPosList(_b))

            # if 0 and hasattr(_a, 'ndim') and _a.ndim == 3 and\
            #    hasattr(_b, 'ndim') and _b.ndim == 3:
            #     #pg._b(_a.shape, _b.shape)
            #     #print(_a * _b)
            #     print(np.array([np.sum(ab) for ab in (_a * _b)]))
            #     return np.array([np.sum(ab) for ab in (_a * _b)])
            #     #return np.sum(_a * _b, axis=2)

            if 0 and pg.isPosList(_a) and pg.isPosList(_b):
                pg.waring('in use?')
                #pg._b(np.sum(_a * _b, axis=1))
                return np.sum(_a * _b, axis=1)
            return _a * _b
            #return (_a*_b.T).T

        elif callable(f):

            if hasattr(f, 'evalOrder'):
                # pg._b(f.evalOrder)
                if f.evalOrder == 0:
                    # pg._g(type(f), f.continuous, f.evalOrder)
                    _f = _createFAtCellCenter(f, A, **kw)
                    # pg._g(_f)
                elif f.evalOrder == 1:
                    _f = _createFAtNodes(f, A, **kw)
                    # pg._b(_f)
                elif f.evalOrder == 2:
                    #pg._y(type(f), f.continuous, f.evalOrder)
                    _f = _createFAtQuads(f, A, **kw)
                    # pg._y(_f)
            else:
                _f = _createFAtQuads(f, A, **kw)
                # pg._y(_f)

            _f = np.squeeze(_f)
            if hasattr(_f, 'ndim') and _f.ndim == 0:
                # squeezed to scalar
                return float(_f)
            return _f
        else:
            return f

    if isinstance(f, list) and any(callable(fi) for fi in f):
        ###
        # check f for [(), scalar, array]
        ###
        ret = np.zeros((len(A.w()), len(f)))
        for i, fi in enumerate(f):
            ret[:,i] = _createFAtQuads(fi, A)

        if __newFieldOrder__ is False:
            #// for edgecases .. remove me if after final transform
            #f = _toField(ret)
            f = pg.core.PosList(ret)
        else:
            f = asVecField(ret)

    try:
        from .feaSolution import FEASolution

        if not isinstance(f, FEASolution) and pg.isMatrix(f) and \
            f.shape[0]*f.shape[1] == A.cols():
            ###
            #f might be a matrix but should be a array that scale each component
            ###
            if pg.core.deepDebug() == -1:
                pg._b('->mulE(A * f.flatten())')
            return mulE(A, f.flatten(), c=c, core=core, **kwargs)
    except BaseException:
        pg._g(f)
        pg._g(pg.isMatrix(f))
        pg._g(type(f))

        v = f
        print(isinstance(v, pg.core.RMatrix))
        print(hasattr(v, 'ndim'))
        print(isinstance(v, list))
        print(pg.isArray(v[0]))

        pg.critical("don't know what to do")

    if core is True or not hasattr(A, '_x'):

        if pg.isPos(c) or (pg.isScalar(c) and c != 1.0):

            # TODO:Refactor me!
            # f is FEAOP but have solution (grad, div)
            if hasattr(f, '_solutionGrad') and not f._solutionGrad:

                if pg.core.deepDebug() == -1:
                    pg._b('core->mult(A*c, f)')

                # print(A)
                # print(c)
                # print(type(f))
                # print(f)
                # print(pg.core.mult(A, c))

                return pg.core.mult(pg.core.mult(A, c), f)
            else:
                # TODO:Refactor me!
                # f is FEAOP but have solution (grad, div)
                A = pg.core.mult(A, c)

        E = pg.core.ElementMatrix()

        #pg._b(f)
        _f = _createF(f, A, **kwargs)
        #pg._r(_f)

        if pg.core.deepDebug() == -1:
            pg._g('core mult')
            pg._g(f'A={A}')
            pg._g(f'f={f}')
            pg._y(f'_f={_f}')
            if hasattr(f, 'evalOrder'):
                pg._y(f'f.evalOrder={f.evalOrder}')

        if pg.isScalar(_f):
            if pg.core.deepDebug() == -1:
                pg._b('core->mult(A, f) f=scalar')
            pg.core.mult(A, _f, E)

        elif (hasattr(f, 'evalOrder') and f.evalOrder == 0):
            if pg.core.deepDebug() == -1:
                pg._b('core->mult(A, f) per cell')
            pg.core.mult(A, _f, E)

        elif (hasattr(f, 'evalOrder') and f.evalOrder == 1):
            ## scalar per node
            if pg.core.deepDebug() == -1:
                pg._b('core->mult_d_n(A, f)')
            pg.core.mult_d_n(A, _f, E)

        elif (hasattr(f, 'evalOrder') and f.evalOrder == 2):
            if pg.isArray(_f, len(A.x())):
                ## Space * R1(qp)
                if pg.core.deepDebug() == -1:
                    pg._b('core->mult_d_q(A, f) f(quad) in R')
                pg.core.mult_d_q(A, _f, E)

            elif pg.isPosList(_f, len(A.x())):
                ## R3 per quadrature _f
                if pg.core.deepDebug() == -1:
                    pg._b('core->mult_d_q(A, f)')

                if A.entity().dim() > 1 and \
                    A.nCoeff() == 1 and A.cols() == 1:
                    ## (ScalarSpace and not grad(u)) * R3(qp)
                    ## need to become ScalarSpace * sum(R3(qp))
                    fs = pg.Vector()
                    pg.core.sum(_f, fs)
                    pg.core.mult_d_q(A, fs, E)
                else:
                    pg.core.mult_p_q(A, _f, E)
            elif hasattr(_f[0], 'ndim') and _f[0].ndim == 2:
                ## matrix per quadrature
                if A.entity().dim() > 1 and \
                    A.nCoeff() == 1 and A.cols() == 1:
                    #fs = pg.Vector()
                    #print(np.sum(_f, axis=2))
                    _f = np.sum(np.sum(_f, axis=2), axis=1)
                    #pg.core.sum_vm(_f, fs)
                    pg.core.mult_d_q(A, _f, E)
                    #pg._b()
                    #exit()
                else:
                    if not isinstance(_f, pg.core.stdVectorRDenseMatrix):
                        _fM = pg.core.stdVectorRDenseMatrix()
                        for f_ in _f:
                            _fM.append(f_)
                        _f = _fM
                    pg.core.mult_m_q(A, _f, E)
            else:
                if pg.core.deepDebug() == -1:
                    pg._b('core->mult(A, f) per quad default')
                pg.core.mult(A, _f, E)

        elif pg.isArray(f, A.nCoeff()*A.dofPerCoeff()) or \
            pg.isArray(f, A.dofPerCoeff()):
            ## scalar per node from input array
            if pg.core.deepDebug() == -1:
                pg._b('core->mult_d_n(A, f) f = [scalar]*nodeCount')
            pg.core.mult_d_n(A, _f, E)

        else:
            ## per cell
            if pg.core.deepDebug() == -1:
                pg._b('core->mult(A, f) default', (type(_f)))

            if isinstance(_f, ElasticityMatrix) \
                or pg.isMatrix(_f) and _f.shape[0] == _f.shape[1] \
                and _f.shape[0] == 6 and A.entity().dim() == 2:
                    _f = np.asarray([[_f[0,0] + _f[0,2], _f[0,1], 0.],
                            [_f[1,0], _f[1,1] + _f[1,2], 0.],
                            [0., 0., _f[2,2]]])
                    #pg._b('-----------------')
            pg.core.mult(A, _f, E)

        if pg.core.deepDebug() == -1:
            E.integrate()
            pg._y(f'result (core): E({id(E)})', E)

        return E

    ## finish prep. start multiplication for core == False

    E = copyE(A)
    # x = E._x
    # ent = E.entity()

    r = np.zeros_like(E._mat[0])

    if isinstance(f, OP):
    #if isinstance(f, FEAFunction) or isinstance(f, FEASolution):
        ## f is callable or length of ent.nodes

        fi = 0
        if pg.isPos(c) or c != 1.0:
            if isinstance(f, FEAFunction) and pg.isPos(c):
                f = FEAFunction3(c*f)
            else:
                f = f*c
            c = 1.0

        #pg._b(f, c)
        f_ = _createF(f, A, **kwargs)
        #pg._g(f_, c)

        if pg.core.deepDebug() == -1:
            pg._y('f:', type(f_))
            pg._y('f:', f_)

        for i, w in enumerate(E._w):

            if hasattr(f_, '__iter__') and len(f_) == len(E._w) and not \
                (hasattr(f, 'evalOrder') and f.evalOrder == 1):
                fi = np.squeeze(f_[i])
                #fi = f_[i]
            else:
                fi = f_
            ## TODO  if f_ is scalar -- refactor me

            if pg.core.deepDebug() == -1:
                pg._y(f'f({i})', type(fi))
                pg._y(f'f({i})', fi)

            #### for each quadrature, optimize scalars
            if pg.isScalar(fi):
                if pg.core.deepDebug() == -1:
                    pg._b('mulE(A, f) f(quad) in R1')

                ### Scalar value per quadrature point
                # print('r', i, E._mat[i])
                # print('fi:', fi)
                # print('c:', c)

                E._mat[i] *= c * fi
            elif pg.isMatrix(fi):
                ### Matrix per quadrature point

                if pg.core.deepDebug() == -1:
                    pg._b('mulE(A, f) f(quad) is C ')

                if A.entity().dim() > 1 and A.cols() == 1:
                    # dim > 1
                    # ScalarSpace and not grad(u) * R3 -> ScalarSpace * sum(R3)
                    E._mat[i] *= (c * np.sum(fi))
                else:
                    # print(pg.isMatrix(fi*c), (fi*c).shape == (6,6), E.entity().dim() == 2)
                    if pg.isMatrix(fi*c) and ((fi*c).shape == (6,6) and E.entity().dim() == 2):
                        ### C is 3D elasticity Matrix but A is 2D space
                        if pg.core.deepDebug() == -1:
                            pg._b('mulE(A, f) f(quad) is C(3D) @ 2D VectorSpace')

                        # pg._b(E)
                        # pg._b(E.mulR)
                        # pg._b(c)
                        # pg._b(fi)
                        # pg._g(fi*c)
                        # AI = np.zeros((6,3))
                        # AI[0][:] = 1./E.entity().size()
                        # AI[1][:] = 1./E.entity().size()
                        # AI[2][:] = 1./E.entity().size()
                        # CI = ((fi*c) @ AI).T
                        # CI = CI[:,[0,1,3]]
                        #pg._y((fi*c)[:,[0,1,3]][[0,1,3],:])
                        #E._mat[i] = (E._mat[i].T @ (fi*c)[:,[0,1,3]][[0,1,3],:]).T
                        fic = (fi*c)
                        CI = fic[:,[0,1,3]][[0,1,3],:]
                        CI[0,0] += fic[0,2] ## 3rd. component
                        CI[1,1] += fic[1,2]
                        #pg._y(CI)

                        E._mat[i] = (E._mat[i].T @ CI).T
                    else:
                        if pg.core.deepDebug() == -1:
                            pg._b('mulE(A, f) f(quad) is C @ VectorSpace')
                        E._mat[i] = (E._mat[i].T @ (fi*c)).T
                    #pg._y(E._mat[i])

            elif (hasattr(f, 'evalOrder') and f.evalOrder == 1):
                ### Scalar value per node
                if pg.isArray(fi, A.rows()):
                    if pg.core.deepDebug() == -1:
                        pg._b('mulE(A, f) f(cell.nodes) in R1 A in R1')
                    E._mat[i] *= fi
                else:
                    if pg.core.deepDebug() == -1:
                        pg._b('mulE(A, f) f(cell.nodes) in R1 A in R3')
                    E._mat[i] *= np.tile(fi, A.nCoeff())
            else:
                # print(f)
                # print('E._mat[i]:', E._mat[i])
                # print('fi:', fi)
                # print('c:', c)

                if pg.core.deepDebug() == -1:
                    pg._b(f'mulE(A, f) fallback: A.cols():{A.cols()}')
                # pg._g(A.nCoeff())
                # pg._y(fi)

                if A.entity().dim() > 1 and pg.isPos(fi) and A.cols() == 1:
                    # dim > 1
                    # ScalarSpace and nor grad(u) * R3 -> ScalarSpace * sum(R3)
                    E._mat[i] *= (c * sum(fi))
                else:
                    try:
                        E._mat[i] *= (c * np.array([fi[0:A.cols()]]).T)
                    except BaseException:
                        E._mat[i] *= (c @ np.array([fi[0:A.cols()]]).T)

            # print(E._mat[i])
            # pg._r('.......')

            r += (E._mat[i] * w * E.entity().size())
        #pg._r('mat:', r)

        setMat(E, np.array(r.T), 'mulE-a')
        E.integrated(True)
        #pg._g(E)

    else: ## f is const over entity
        if pg.core.deepDebug() == -1:
            pg._y(f'f({type(f)})\n', f)

        if pg.isScalar(f):
            if pg.core.deepDebug() == -1:
                pg._y('f is global scalar per cell')

            fi = f * c
            for i, m in enumerate(E._mat):
                m *= fi
                r += (m * E._w[i] * E.entity().size())

            setMat(E, np.array(r.T), 'mulE-b')

        elif (pg.isPosList(f, nRules)
              and not (isinstance(f, ElasticityMatrix)
                        or (isinstance(f, np.ndarray)
                            and f.ndim == 2
                            and f.shape[0] == f.shape[1]))):
            ## posList but no elasticity Matrix or square matrix
            if pg.core.deepDebug() == -1:
                pg._y('f is pos per quadrature')

            for i, w in enumerate(E.w()):
                fi = f[i]
                try:
                    E._mat[i] *= (c * np.array([fi[0:A.cols()]]).T)
                except BaseException:
                    E._mat[i] *= (c @ np.array([fi[0:A.cols()]]).T)

                r += (E._mat[i] * w * E.entity().size())
                setMat(E, np.array(r.T), 'mulE-c')

        elif pg.isArray(f[0], len(E._mat[0][0])):
            ###
            # f is array of length(nRules)
            ###
            if pg.core.deepDebug() == -1:
                pg._b('f is scalar per quadrature')

            if len(f) == len(E._mat):
                for i, m in enumerate(E._mat):
                    m *= f[i] * c
                    r += (m * E._w[i] * E.entity().size())
                setMat(E, np.array(r.T), 'mulE-d')
            else:
                pg.critical("size doesn't fit")

        elif pg.isMatrix(f):

            ##########################################################
            # f is cell constant matrix
            ##########################################################
            if A.entity().dim() == 2 and f.shape == (6,6):
                if pg.core.deepDebug() == -1:
                    pg._b('f is 2D C(3D) per cell')

                fc = f*c
                CI = fc[:,[0,1,3]][[0,1,3],:]
                CI[0,0] += fc[0,2] ## add 3rd. component
                CI[1,1] += fc[1,2]

                setMat(E, np.asarray(A.mat()) @ CI, 'mulE-f')

            else:
                if pg.core.deepDebug() == -1:
                    pg._b('f is Mat per cell')

                #pg._b(f)
                #pg._b(c)
                #setMat(E, A.mat() @ (f*c), 'mulE-f')
                setMat(E, np.array(A.mat()) @ (f*c), 'mulE-f')
                #setMat(E,np.array([np.sum(A.mat() @ (f*c), axis=1)]))

            #sys.exit()
        elif pg.isArray(f, E.nCoeff()*E.dofPerCoeff()) and not \
            isinstance(E.entity(), pg.core.Boundary):
            ### scalar per node from f array for scalar spaces

            if pg.core.deepDebug() == -1:
                pg._b('f is scalar per node per scalar space')

            fi = f[E.rowIDs()] * c

            for i, m in enumerate(E._mat):
                m *= fi
                r += (m * E._w[i] * E.entity().size())

            setMat(E, np.array(r.T), 'mulE-b')

        elif pg.isArray(f, E.dofPerCoeff()) and E.nCoeff() > 1 and not \
            isinstance(E.entity(), pg.core.Boundary):
            ### scalar per node from f array for vector spaces

            if pg.core.deepDebug() == -1:
                pg._b('f is scalar per node per vector space')

            fi = f[np.mod(E.rowIDs(), E.dofPerCoeff())] * c
            #pg._b(fi)
            for i, m in enumerate(E._mat):
                m *= fi

                # pg._b(fi)
                # pg._b(E._mat.T)
                # exit
                r += (m * E._w[i] * E.entity().size())

            #print(E)
            setMat(E, np.array(r.T), 'mulE-b')
            #pg._y(E)

        elif pg.isPos(f) or pg.isArray(f, A.cols()):
            if pg.core.deepDebug() == -1:
                pg._y('f is pos')

            try:
                fi = f * c
            except BaseException:
                # could be []
                fi = pg.Pos(f) * c

            E._mat = np.zeros((len(A._mat), A.cols(), A.rows()))

            for i, mi in enumerate(A._mat):
                E._mat[i] = mi
                #print(E._mat[i])
                for j in range(A.cols()):
                    E._mat[i][j] *= fi[j]
                #print(E._mat[i])

            _fillMatX(E)
            #print(E)
            integrateE(E, E._mat, E._w )
            #print(E)

        else:
            pg._r()
            print(f'A: {A}')
            print(f'c: {c}')
            print(f'f: {type(f)} {f}')
            pg.critical("Can't interpret f")

    E.integrated(True)
    if pg.core.deepDebug() == -1:
        pg._y(f'result: E({id(E)})', E)

    #sys.exit()
    return E


def dotE(A, B, c=1.0, core=False, **kwargs):
    """Create a dot product of two ElementMatrices.

    This is a bilinear operation, so it will return an ElementMatrix
    with the size of < A, B > = < A.rows(), B.cols() >
    and the values of < A, B.T > = < A.cols(), B.rows()
    """
    if pg.core.deepDebug() == -1:
        pg._g('*'*60)
        pg._g(f'** DOT: core:{core}, c:{c}')
        pg._g(f'** \tA: {type(A)}')
        pg._g(f'** \tB: {type(B)}')
        pg._g('*'*60)
        sAdd = ''
        if hasattr(A, 'isIdentity'):
            sAdd +=f' I={A.isIdentity}'
        if hasattr(A, 'mulR'):
            sAdd +=f' mulR={A.mulR}'

        try:
            pg._g(f'A: {type(A)} {sAdd} div:{A.isDiv()}, order:{A.order()} \n{A}\n')
        except BaseException:
            pg._g(f'A: {type(A)} {sAdd} \n{A}\n')

        sAdd = ''
        if hasattr(B, 'isIdentity'):
            sAdd +=f' I={B.isIdentity}'
        if hasattr(B, 'mulR'):
            sAdd +=f' mulR={B.mulR}'

        try:
            pg._g(f'B: {type(B)} {sAdd} div:{B.isDiv()}, order:{B.order()} \n{B}\n')
        except BaseException:
            pg._g(f'B: {type(B)} {sAdd} \n{B}\n')


    ### check for non bilinear multiplications first
    ## refactor me!
    from .feaSpace import ConstantSpace
    from .feaSolution import FEASolution, FEASolutionOP
    from .feaFunction import FEAFunction
    from .feaOp import FEAOP
    from .elasticity import ElasticityMatrix
    from .op import OP


    if isinstance(A, ConstantSpace):
        E = pg.core.ElementMatrix()
        E.resize(B.cols(), B.rows())
        E.setIds(range(A.dofs.start, A.dofs.stop), B.rowIDs())
        if not B.isIntegrated():
            B.integrate()
        setMat(E, np.array(B.mat()).T, 'dotE-a')
        E.integrated(True)
        return E

    if isinstance(B, ConstantSpace):
        E = pg.core.ElementMatrix()
        E.setIds(A.rowIDs(), range(B.dofs.start, B.dofs.stop))
        E.resize(A.rows(), A.cols())
        if not A.isIntegrated():
            A.integrate()
        setMat(E, np.array(A.mat()), 'dotE-b')
        E.integrated(True)
        return E

    if isinstance(A, pg.core.ElementMatrix) and hasattr(B, 'isIdentity') is True:
        return mulE(A, f=B, core=core, **kwargs)

    if isinstance(B, pg.core.ElementMatrix) and hasattr(A, 'isIdentity') is True:
        return mulE(B, f=A, core=core, **kwargs)

    # check with generic need assembly (lin or blin check)
    if isinstance(A, (FEASolution, FEASolutionOP, FEAFunction, list)):
        return mulE(B, f=A, c=c, core=core, **kwargs)

    # check with generic need assembly (lin or blin check)
    if isinstance(B, (FEASolution, FEASolutionOP, FEAFunction, list)):
        return mulE(A, f=B, c=c, core=core, **kwargs)

    if isinstance(B, FEASolution) or \
        isinstance(B, FEASolutionOP) or \
        isinstance(B, FEAFunction):
        pg.critical('in use?') #0.9.1 250717
        return mulE(A, f=B, c=c, core=core, **kwargs)

    if pg.isPos(A):
        return mulE(B, f=A, c=c, core=core, **kwargs)
    if pg.isPos(B):
        return mulE(A, f=B, c=c, core=core, **kwargs)

    if isinstance(A, FEAOP) and not A.needsAssembling():
        return mulE(B, f=A, c=c, core=core, **kwargs)
    if isinstance(B, FEAOP) and not B.needsAssembling():
        return mulE(A, f=B, c=c, core=core, **kwargs)

    if isinstance(A, OP) and isinstance(B, OP):
        #pg._g(OP, B)
        # expect here OP with ready made matrices
        return dotE(A.eval(), B.eval(), core=core, **kwargs)

    if isinstance(A, OP):
        # pg._g(OP, B)
        # pg._y(B.cols())
        # expect here OP with ready made matrices
        return dotE(A.eval(dim=B.cols()), B, core=core, **kwargs)

    if isinstance(B, OP):
        #pg._g(OP, B)
        # expect here OP with ready made matrices
        return dotE(A, B.eval(dim=A.cols()), core=core, **kwargs)

    if isinstance(A, pg.core.ElementMatrix) and isinstance(B, np.ndarray):
        return mulE(A, f=B, c=c, core=core, **kwargs)

    if isinstance(A, np.ndarray) and isinstance(B, pg.core.ElementMatrix):
        return mulE(B, f=A, c=c, core=core, **kwargs)

    sign = 1.0
    if pg.isScalar(c) and c == -1.0:
        sign = -1.0

    if pg.isPos(A.mulR) and pg.isPos(B.mulR):
        ca = A.mulR
        cb = B.mulR
        A.mulR = 1.0
        B.mulR = 1.0
        # print('A', A, ca)
        # print('B', B, cb)
        A = mulE(A, f=ca, core=core, **kwargs)
        B = mulE(B, f=cb, core=core, **kwargs)
        # print('A1', A1)
        # print('B1', B1)
        # A2 = mulE(A, f=ca, core=True)
        # B2 = mulE(B, f=cb, core=True)
        # print('A2', A2)
        # print('B2', B2)

        c = sign
    else:
        c = c * A.mulR * B.mulR

    A.mulR = 1.0
    B.mulR = 1.0

    if pg.isPos(c):
        # pg._r(c)
        # pg._y(A.cols())
        # pg._y(B.cols())
        if A.cols() == len(c):
            # print(A)
            # print(A._mat)

            A = mulE(A, f=c, core=core, **kwargs)
            c = sign
        elif B.cols() == len(c):
            B = mulE(B, f=c, core=core, **kwargs)
            c = sign
        else:
            pg.critical('c is vector but neighter A or B are')
        # elif pg.isPos(A.mulR):
        #     A = mulE(A, f=A.mulR, core=core)
        # elif pg.isPos(B.mulR):
        #     B = mulE(B, f=B.mulR, core=core)

    if pg.isArray(c, B.nCoeff()*B.dofPerCoeff()):
        ### c is per node
        B = mulE(B, f=c, core=core, **kwargs)
        c = sign

    if A.entity().dim() == 1 and pg.isArray(c, 1):
        c = c[0]

    #pg._r(c)
    if core is True or isRefImpl(A) == False:
        #assuming non reference core Matrix
        return pg.core.dot(A, B, c=c)

    ### bilinear multiplications starts here ###

    # pg._r('dotE')
    ## Mult dot(E, E)
    # pg.info('dot(A, B)')
    # print('A', A)
    # print('B', B)

    w = A._w
    if not np.allclose(w, B._w):
        print(w, B._w)
        pg.critical('A and B need to have same integration order')

    AisDiv = False
    BisDiv = False

    if len(A.colIDs()) > len(B.colIDs()) or A.isDiv():
        AisDiv = True
    if len(B.colIDs()) > len(A.colIDs()) or B.isDiv():
        BisDiv = True

    nRules = len(w)

    E = copyE(A, cols=B.rows(),
              matX=np.zeros((nRules, A.rows(), B.rows())))
    E.setIds(A.rowIDs(), B.rowIDs())

    m = np.zeros((A.rows(), B.rows()))

    if pg.isScalar(c):
        # pg._r('dotE', c, AisDiv , BisDiv)

        for i in range(nRules):
            if AisDiv is True and BisDiv is False:
                ids = range(A.cols())

                if A.isDiv() is True:
                    if A.entity().dim() == 1:
                        ids = [0]
                    elif A.entity().dim() == 2:
                        ids = [0, 3]
                    elif A.entity().dim() == 3:
                        ids = [0, 4, 8]

                E._mat[i] += c * np.sum(A._mat[i][ids],
                                        axis=0, keepdims=True).T@B._mat[i]

                # print(i, E._mat[i])

            elif BisDiv is True and AisDiv is False:
                ids = range(B.cols())

                if B.isDiv() is True:
                    #if hasattr(B, '_isDivergence') and B._isDivergence is True:
                    if B.entity().dim() == 1:
                        ids = [0]
                    elif B.entity().dim() == 2:
                        ids = [0, 3]
                    elif B.entity().dim() == 3:
                        ids = [0, 4, 8]

                E._mat[i] += c * A._mat[i].T @ np.sum(B._mat[i][ids],
                                                      axis=0, keepdims=True)

            else:
                E._mat[i] = c * A._mat[i].T @ B._mat[i]

            m += E._mat[i] * w[i] * E.entity().size()

    elif 0 and isinstance(c, np.ndarray) and c.shape == (A.cols(), ):
        for i, wi in enumerate(w):
            E._mat[i] = (A._mat[i].T * c.T) @ B._mat[i]
            m += E._mat[i] * wi * E.entity().size()
    elif isinstance(c, np.ndarray) and c.shape == (A.cols(), B.cols()):
        # TODO: integrate needed for const c per cell, assemble enough?
        #
        # pg._r(A.rows(), A.cols(), A._mat[0].shape)
        # pg._y(B.rows(), B.cols(), B._mat[0].shape)
        # pg._g(c)
        if pg.core.deepDebug() == -1:
            pg._b('integrate A*C*A')

        for i, wi in enumerate(w):
            E._mat[i] = A._mat[i].T @ c @ B._mat[i]
            m += E._mat[i] * wi * E.entity().size()

    elif isinstance(c, ElasticityMatrix) or pg.isMatrix(c) \
        and (c.shape == (6,6) and A.entity().dim() == 2):
        ### C is 3D elasticity Matrix but A is 2D space
        if pg.core.deepDebug() == -1:
            pg._b('integrate A(2d)*C(3d)*A(2d)')


        for i, wi in enumerate(w):
            # print(i, wi)
            # print('A', A._mat[i])
            # print('c', c)
            # print('B', B._mat[i])
            # print('A@c', A._mat[i].T @ c[:,[0,1,3]][[0,1,3],:])
            E._mat[i] = A._mat[i].T @ c[:,[0,1,3]][[0,1,3],:] @ B._mat[i]
            m += E._mat[i] * wi * E.entity().size()

        #print(m)
    else:
        print(A, B)
        print(c)
        print('c.shape():', c.shape, 'expected:', (A.cols(), B.cols()))
        pg.critical("Can't interpret c", c)

    _fillMatX(E)
    setMat(E, m, 'dotE-c')
    E.integrated(True)
    return E
