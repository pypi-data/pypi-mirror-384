#!/usr/bin/env python
"""Test finite element solution for basic equations.

Test consistency and convergence for all cell types using MMS.
"""
import numpy as np
import pygimli as pg

from oskar import (div, grad, OP,
                   derive, parse, solve, norm, normL2, normSemiH1, asFunction,
                   ScalarSpace, FEASolution, TaylorHood)

from oskar.tests import assertEqual, testCount, TestCollection
from oskar.utils import convergenceRate, drawConvergenceOrder

import logging
logging.getLogger('distributed').setLevel(30) # Warning

pg.setThreadCount(1)
__tests__ = {}


# def solvePN(mesh, a=1, b=0, f=0, bc=None, verbose=False):
#     """Solve with pure Neumann. i.e., add additional condition such that the sum
#     of all u should be 0.0.
#     TODO: compare core/non-core
#     """
#     pg.critical("In use?")
#     u = ScalarSpace(mesh)

#     ### add constant space (sum of all u is 0.0)
#     c = ConstantSpace(dofOffset=u.dofs.stop)# with dof = 1 to add u*v + v*u
#     u1, c1 = solve(grad(u)*a*grad(u) + u*b*u + u*c + c*u == u*f,
#                       bc=bc, solver='scipy', core=False)

#     ut, ct = solve(grad(u)*a*grad(u) + u*b*u + u*c + c*u == u*f,
#                       bc=bc, solver='scipy', core=True)
#     assertEqual(0.0, np.linalg.norm((u1-ut).eval()), atol=1e-12)

#     ut, ct = solve(grad(u)*a*grad(u) + u*b*u + u*c + c*u == u*f,
#                       bc=bc, solver='scipy', useMats=True)
#     assertEqual(0.0, np.linalg.norm((u1-ut).eval()), atol=1e-12)


#     ## same like above but with Blockmatrix instead of using constant space
#     # u = ScalarSpace(mesh)
#     S, rhs = (grad(u)*a* grad(u) +  u*b*u == u*f).assemble(core=False)
#     applyBoundaryConditions(bc, u, mat=S, rhs=rhs)

#     r = u.assemble()

#     A = pg.BlockMatrix()
#     A.add(S, 0, 0)
#     A.add(r, 0, mesh.nodeCount())
#     A.add(r, mesh.nodeCount(), 0, transpose=True)

#     rhs = pg.cat(rhs, pg.Vector(1, 0.0))

#     u = pg.solver.linSolve(A, rhs, verbose=verbose, solver='scipy')
#     u2 = u[0:mesh.nodeCount()]
#     c2 = u[mesh.nodeCount()]

#     # compare blockmatrix vs. mixed spaces
#     assertEqual(0.0, np.linalg.norm(u1.values-u2), atol=1e-11)
#     assertEqual(c1, c2, atol=1e-11)

#     #compare with pg core old
#     u3 = pg.solver.solve(mesh, a=a, b=b, c=c, f=f, bc=bc)
#     assertEqual(0.0, np.linalg.norm(u1.values-u3), atol=1e-11)

#     return u1


def showTestResults(test='all'):
    """Create table of testing results."""
    # Create table test per mesh
    # first collect different meshes

    if test == 'all':
        for k, v in __tests__.items():
            pg.info('Test:', k)
            showTestResults(test=k)
        return

    tests = __tests__[test]

    meshes = set()
    for n, v in tests.items():
        ns = n.split('/')
        meshes.add(ns[0])
    meshes = sorted(meshes)

    table = {}

    for n, v in tests.items():
        ns = n.split('/')
        m = ns[0]
        b = ns[1]
        key = ' '.join(ns[2:]) + ' ' + b

        # print(key)
        if key not in table:
            table[key] = [''] * len(meshes)

        table[key][list(meshes).index(m)] = v

    tab = []
    for n, v in table.items():
        tab.append([n, *v])

    print(pg.Table(tab, header=[test, *list(meshes)], align='c'*len(tab[0]),
                   transpose=False))


@pg.cache
def createMeshes():
    """ Create several meshes for testing.
    """
    np.random.seed(1337)
    meshes = {}

    x = np.linspace(-2, 2, 4) # 4 is minimum, 3 leads to ambiguity (Fix me!)
    m1 = pg.createGrid(x)

    m2 = pg.Mesh(m1)
    dx = m2.h()[0]
    for n in m2.nodes()[1:-1]:
        n.setPos(n.pos() + [np.random.rand()*dx/4, 0.0, .0])

    meshes = {'1d': m1,
              '1d-u': m2}

    x = np.linspace(-2, 2, 4) # 4 is minimum, 3 leads to ambiguity (Fix me!)
    ### simple grid
    q1 = pg.createGrid(x, x)
    # move all meshes so that node(0) is at minPosition to ensure
    # the general fixed node BC work for all meshes the same.
    minPos = pg.Pos(q1.node(0).pos())

    ### simple grid -- unstructured with random moved inner nodes
    q2 = pg.Mesh(q1)
    dx = q2.h()[0]
    for n in q2.nodes():
        if not n.onBoundary():
            n.setPos(n.pos() + [(-0.5+np.random.rand())*dx/4,
                                (-0.5+np.random.rand())*dx/4, .0])
    q2.translate(minPos -  q2.node(0).pos())

    ### simple grid -- rotated
    q3 = pg.Mesh(q1)
    q3.rotate([0, 0, np.pi/4])
    q3.translate(minPos -  q3.node(0).pos())
    #pg.show(q3)

    ### simple grid -- non-equidistent cells
    q4 = pg.createGrid([-2, -1.5, 0, 2], [-2, -1.5, 0, 2])

    ### simple grid -- Parallellograms
    q5 = pg.Mesh(q1)
    for n in q5.nodes():
        n.setPos(n.pos() + [n.y()*0.1, n.x()*0.1])
    q5.translate(minPos -  q5.node(0).pos())
    #pg.show(q5)

    #q2 = pg.Mesh(q2)
    t1 = pg.meshtools.refineQuad2Tri(q1)
    t2 = pg.meshtools.refineQuad2Tri(q2, style=1)

    r1 = pg.meshtools.createMesh(pg.meshtools.createCircle(radius=2,
                                                            nSegments=9,
                                                            area=1),
                                                            smooth=[1,10])
    for b in r1.boundaries():
        if b.outside():
            if b.center()[0] < 0:
                b.setMarker(2)
            else:
                b.setMarker(1)

    #r1 = pg.meshtools.refineQuad2Tri(q3)
    r1.translate(minPos -  r1.node(0).pos())
    #pg.show(r1, markers=True)

    r2 = pg.createGrid([0, 1, 3], phi=np.linspace(0, np.pi*2, num=9))
    r2.translate(minPos -  r2.node(0).pos())
    #pg.show(r2)

    meshes.update({'2d-quad': q1,
                    #'2d-quad-u': q2, # unstructured mesh
                    '2d-quad-r': q3, # rotated mesh
                    '2d-quad-i': q4, # increasing sizes
                    '2d-quad-p': q5, # parallelogramms
                    '2d-tri': t1,
                    '2d-tri-u': t2,
                    '2d-tri-r': r1,
                    #'2d-mix': r2,
                })

    x = np.linspace(-2, 2, 3)
    h1 = pg.createGrid(x, x, x)
    minPos = pg.Pos(h1.node(0).pos())

    ### simple hex grid with moved nodes
    h2 = pg.Mesh(h1)
    dx = h2.h()[0]
    for n in h2.nodes():
        if not n.onBoundary():
            n.setPos(n.pos() + [(-0.5+np.random.rand())*dx/4,
                                (-0.5+np.random.rand())*dx/4,
                                (-0.5+np.random.rand())*dx/4])
    h2.translate(minPos - h2.node(0).pos())

    t1 = pg.meshtools.refineHex2Tet(h1)

    meshes.update({'3d-hex': h1,
              #'3d-hex-u': h2,
              '3d-tet': t1,
                })

    return meshes


def consistencyTest(pde, bc=None, u=None, tol=1e-8,
                    show=False, verbose=False, **kwargs):
    """Test consistency of a finite element solution.

    The consistency, i.e., the error norm regarding the exact solution
    needs to be lower as a threshold.

    Arguments
    ---------
    pde: expression
        Partial differential equation.

    bc: dict
        Dictionary of boundary conditions.

    u: FEAFunction
        Exact solution.

    tol: float
        Tolerance for L2-Norm and H1SemiNorm.

    show: bool [False]
        Show results.

    verbose: bool [False]
        Be verbose.

    Keyword Arguments
    -----------------
    fast: bool [False]
        Don't test python assembling. Only useMats=True.

    **kwargs: any
        Forwarded to :py:mod:`solve`.
    """
    fast = kwargs.pop('fast', False)

    assertionErrors = []

    # pg._b(pde)
    # pg._b(bc)
    # pg._b(kwargs)
    solver = kwargs.pop('solver', 'scipy')
    solver = 'scipy'

    try:
        u1 = solve(pde, bc=bc, verbose=verbose, solver=solver, useMats=True)
    except BaseException as e:
        pg._r(e)
        pg._y('pde:', pde)
        print(bc)

        import sys, traceback
        traceback.print_exc(file=sys.stdout)
        raise TypeError('solver fail')
        pg.critical(e)
        assertionErrors.append([f'solver fail'])


    if not fast:
        u2 = solve(pde, bc=bc, verbose=verbose, solver=solver, core=True)
        u3 = solve(pde, bc=bc, verbose=verbose, solver=solver, core=False)

        try:
            assertEqual(u1, u2)
        except AssertionError as e:
            assertionErrors.append([f'cT:{pg.pf(abs(max(u1-u2)))}', e])

        try:
            assertEqual(u1, u3)
        except AssertionError as e:
            assertionErrors.append([f'cF:{pg.pf(abs(max(u1-u2)))}', e])

    if isinstance(pde, list):
        # mixed spaces
        for i in range(len(pde)):
            l2 = np.linalg.norm(u[i](u1[i].mesh) - u1[i].values)
            L2 = normL2(u[i]-u1[i])
            H1 = normSemiH1(u[i]-u1[i])

            try:
                assertEqual(L2, 0.0, atol=tol)
            except AssertionError as e:
                assertionErrors.append([f'L2({i}):{pg.pf(abs(0.0-L2))}', e])
            try:
                assertEqual(H1, 0.0, atol=tol)
            except AssertionError as e:
                assertionErrors.append([f'H1({i}):{pg.pf(abs(0.0-H1))}', e])

            if verbose:
                print(f' l2({i})={pg.pf(l2)}\t  L2({i})={pg.pf(L2)}\t'
                      f'H1({i})={pg.pf(H1)}')
    else:
        # single space
        l2 = np.linalg.norm(u(u1.mesh) - u1.values) # is super convergence
        L2 = normL2(u-u1)
        H1 = normSemiH1(u-u1)

        if verbose:
            print(f' l2={pg.pf(l2)}\t  L2={pg.pf(L2)}\t  H1={pg.pf(H1)}')

        if show:

            meshH2 = u1.space.inputMesh.createH2()
            for i in range(1):
                meshH2 = meshH2.createH2()
                meshH2.createNeighbourInfos()

            if meshH2.dim() == 1:
                ax = pg.show(meshH2, u, label='exact')[0]
                pg.show(u1, marker='o', lw=0, label='uh', color='C1', ax=ax)
                pg.show(meshH2, u1, color='C1', ax=ax)
            elif meshH2.dim() == 2:
                fig, axs = pg.plt.subplots(1, 3)
                pg.show(u1.mesh, u, label='u', ax=axs[0], showMesh=True)
                pg.show(u1, label='uh', ax=axs[1], showMesh=True)
                pg.show(meshH2, u-u1, label='u-uh', ax=axs[2],
                        showMesh=True, cMap='RdBu')

                fig.tight_layout()

        try:
            assertEqual(L2, 0.0, atol=tol)
        except AssertionError as e:
            assertionErrors.append([f'L2:{pg.pf(abs(0.0-L2))}', e])
        try:
            assertEqual(H1, 0.0, atol=tol)
        except AssertionError as e:
            assertionErrors.append([f'H1:{pg.pf(abs(0.0-H1))}', e])

    if len(assertionErrors) > 0:
        raise AssertionError(assertionErrors)

    return u1


#@dask.delayed ## import perfhole
def consistencyTestRunner(EQ, u, mesh, bc, p=1,
                          atol=2e-15, verbose=False):
    """Consistency test for EQ(FEASpace) == EQ(u)
    """
    pg.setThreadCount(1)
    # check segfault if I remove the shape function cache mutex!
    #EQ = lambda u: -div(grad(u))
    try:

        if callable(EQ) and not isinstance(EQ, OP):

            s = ScalarSpace(mesh[1], p=p)
            pde = EQ(s) == EQ(u)
        else:
            pde = EQ

        name = f'{mesh[0]}/{bc[0]}/p{p}/consistency'
        #pg._g(name)
        consistencyTest(pde, bc=bc[1], u=u, tol=atol,
                        show=False, verbose=verbose, fast=False)

        res = (pg._('pass', c='g'), True)
    except AssertionError as e:
        es = [e_[0] for e_ in e.args[0]]
        ae = [e_[1] for e_ in e.args[0]]
        res = (pg._(f'{",".join(es)}', c='r'), ae)
    except TypeError as e:
        res = (pg._('fail (type)', c='r'), e)
    except ValueError as e:
        res = (pg._('fail', c='r'), e)

    return [name, res]


def consistencyTestGen(EQ, u, dim, p, atol):
    """Generate delayed consistency tests."""
    tst = []
    ms = {}
    for k, m in createMeshes().items():
        if dim in k:
            ms[k] = m
    u = parse(u=u)

    minPos = pg.Pos(list(ms.values())[0].node(0).pos())
    bcs = {'bc:dir': {'Dirichlet':{'*':u}},
           'bc:neu': {'Neumann':{'*':grad(u)},
                      'Fix':[minPos, u(minPos)]},
           'bc:mix': {'Dirichlet':{'*':u}, 'Neumann':{'2':grad(u)}},
           }

    for m in ms.items():
        for bc in bcs.items():
            tst.append(consistencyTestRunner(EQ, u=u, mesh=m, bc=bc, p=p,
                                             atol=atol))

    return tst


def convergencyTest(L, mesh, u=None, f=None, bc=None, ic=None, times=None,
                    p:int=1,
                    rLvl:int=3, refine:str='space', eOrder=None, tol=None,
                    show:bool=False, verbose:bool=False, ax=None, **kwargs):
    r"""Run convergency test.

    Apply method of manufactured solutions to
    test the convergency behavior regarding space or time refinement
    for solving partial differential equations.

    .. math::
        \mathcal{L}(s) = \mathcal{L}(u)

    with manufactured exact solution :math:`u`, a finite element space
    :math:`s` with polynomial degree math:`p` and \mathcal{L} be a partial
    differential operator:

    .. math::
        \mathcal{L}(u, \partial_t u, \nabla u, \Delta u, \ldots)

    The test calculates the convergence rates of the L2-norm and H1-seminorm
    and compares the result with expected values.
    Raises `AssertionError` if a test fails.

    Arguments
    ---------
    L : FEAOP
        Left side of a partial differential equation.

    mesh : pg.Mesh
        A :std:doc:`pygimli.Mesh <pygimli:pygimliapi/_generated/pygimli.meshtools>`

    u : FEAFunction | FEAFunction3
        Exact manufactured solution.

    f : FEAFunction | FEAFunction3 [None]
        Force function for right hand side.
        If `f` is not set then `f=L(u)` for MMS is assumed.

    bc : dict
        Boundary conditions. See :py:mod:`oskar.solve.solve`.

    ic : FEAFunction
        Initial condition. Usually the same like u. Will be called with
        `u(mesh, t=0)`.

    times : iterable [float]
        Times to solve for will be refined factor 2 if refine
        strategy is 'time'.

    p : int [1]
        Polynomial degree for the finite element space.

    rLvl : int [3]
        Refinement level for convergency test.

    refine : str ['space']
        Refinement strategy.

        * `refine='space'`
            the mesh will be `h`-refined, i.e., every edge in
            will be halved.

        * `refine='time'`
            the times array will be doubles by halving the time steps.

    eOrder : [float,float][None]
        Expected convergence rates for L2 and H1-semi norm to compare with.

    tol : float[None]
        Tolerance to pass the test with the expected convergence rate.
        Default is no None to omit the testing.

    show : bool[False]
        Show drawing of the convergence rate. Enabling show, disables the
        abortion on failing tests.

    ax : Matplotlib axes[None]
        Draw convergence into the axe or create a new axe instance.
        L2 and H1 convergence rates will be drawn into the same axe,
        or in two different if `ax` is list of two axe instances.

    Keyword Args
    ------------
    **kwargs:
        Forwarded to :py:mod:`oskar.solve.solve`.

    """
    L2 = []
    H1 = []
    c = []
    h = []

    solver = kwargs.pop('solver', 'scipy')
    #solver = kwargs.pop('solver', 'cholmod')

    ### cache f here as this could be the most expensive here
    if f is None:
        f = L(u)
    for i in range(rLvl):

        if i > 0:
            if refine == 'space':
                mesh = mesh.createH2()
                if verbose:
                    pg.info(f'p={p}', s.mesh)
            elif refine == 'time':
                times = np.linspace(times[0], times[-1], len(times)*2)
                if verbose:
                    pg.info(f'dt={times[1]-times[0]}')
            else:
                pg.critical('Refinement strategy unknown:', refine)

        if 'hex2tet' in kwargs:
            s = ScalarSpace(pg.meshtools.refineHex2Tet(mesh),
                            p=p, order=p+2, name='u')
        else:
            s = ScalarSpace(mesh, p=p, order=p+2, name='u')

        print('', end='', flush=True)

        u0 = None
        if ic is not None:
            u0 = ic(s.mesh, time=0, **kwargs)

        uh = solve(L(s) == f, bc=bc, ic=u0, times=times,
                   solver=solver,
                   verbose=verbose, useMats=True, **kwargs)
        L2.append(normL2(u-uh))
        H1.append(normSemiH1(u-uh))

        if refine == 'space':
            c.append(s.mesh.cellCount())
            h.append(min(s.mesh.h()))
        elif refine == 'time':
            c.append(len(times))
            h.append(times[1]-times[0])

    cL2 = convergenceRate(h, L2)
    cH1 = convergenceRate(h, H1)

    if verbose:
        pg.info(f'Convergence rate L2:{cL2}')
        pg.info(f'Convergence rate H1:{cH1}')

    if eOrder is None:
        if refine == 'space':
            cL2Ref = 2
            cH1Ref = 1
            if p == 2:
                cL2Ref = 3
                cH1Ref = 2
        elif refine == 'time':
            cL2Ref = 1
            cH1Ref = 1
            if kwargs.get("theta", 1) == 0.5:
                cL2Ref = 2
                cH1Ref = 2
    else:
        if not isinstance(eOrder, list):
            pg.critical("Expected convergency order 'eOrder' need to be a "
                        "list of 2 expected values.")
        else:
            cL2Ref = eOrder[0]
            cH1Ref = eOrder[1]

    if show:
        if ax is None:
            _, ax = pg.plt.subplots(1, 2)

        if hasattr(ax, '__iter__') and len(ax) > 1:
            a1 = ax[0]
            a2 = ax[1]
        else:
            a1 = ax
            a2 = ax

        xlabel = ''
        labelAdd = ''

        if refine == 'space':
            labelAdd = f'p={p}'
            xlabel = 'cell width $h$'
        elif refine == 'time':
            labelAdd = r'$\theta=' + str(kwargs.get("theta",1)) +'$'
            xlabel = 'time discretization d$t$'

        drawConvergenceOrder(a1, h, [cL2Ref], ref=L2)
        drawConvergenceOrder(a2, h, [cH1Ref], ref=H1)

        l = a1.loglog(h, L2, '-', alpha=0.3)
        a1.loglog(h, L2, 'o', color=l[0].get_color(), alpha=1.0,
                  label=f'$L_2$ ({labelAdd})')

        l = a2.loglog(h, H1, '-', alpha=0.3)
        a2.loglog(h, H1, 'o', color=l[0].get_color(), alpha=1.0,
                  label=f'$H_1$ ({labelAdd})')

        a1.set(xlabel=xlabel, ylabel='$||u-uh||_{L_2}$')
        a1.legend()
        a1.grid(True)

        if hasattr(ax, '__iter__') and len(ax) > 1:
            a2.set(xlabel=xlabel, ylabel='$||u-uh||_{H_1}$')
        else:
            a2.set(xlabel=xlabel, ylabel='$||u-uh||$')
        a2.legend()
        a2.grid(True)

        a1.figure.tight_layout()

    ## start the test

    assertionErrors = []
    if tol:
        try:
            assertEqual(cL2[-1], cL2Ref, tol=tol)
        except AssertionError as e:
            assertionErrors.append([f'cL2[-1]:{pg.pf(abs(cL2Ref-cL2[-1]))}',e])
        try:
            assertEqual(cH1[-1], cH1Ref, tol=tol)
        except AssertionError as e:
            assertionErrors.append([f'cH2[-1]:{pg.pf(abs(cH1Ref-cH1[-1]))}',e])

    if len(assertionErrors) > 0:
        raise AssertionError(assertionErrors)

    return ax


#@dask.delayed import perfhole
def convergencyTestRunner(EQ, mesh, bc, p, u, **kwargs):
    """Convergency test for EQ(FEASpace) == EQ(u)
    """
    #TODO: check for segfault if the shapfunction cache mutex has been removed!
    pg.setThreadCount(1)
    try:
        if kwargs.get('hex2tet', False):
            name = f'3d-tet/{bc[0]}/p{p}/convergency'
        else:
            name = f'{mesh[0]}/{bc[0]}/p{p}/convergency'
        convergencyTest(EQ, mesh[1], u=u, f=None, bc=bc[1],
                        p=p, refine='space')

        #convergencyTest_(EQ, mesh[1], bc=bc[1], u=u, p=p, show=False, **kwargs)
        res = (pg._('pass', c='g'), True)
    except AssertionError as e:
        es = [e_[0] for e_ in e.args[0]]
        ae = [e_[1] for e_ in e.args[0]]
        res = (pg._(f'{",".join(es)}', c='r'), ae)
    except TypeError as e:
        res = (pg._('fail (type)', c='r'), e)
    except ValueError as e:
        res = (pg._('fail', c='r'), e)

    return [name, res]


def convergencyTestGen(EQ, u:str, dim:str=None, mesh:str=None, p:int=1,
                       **kwargs):
    """Generate delayed consistency tests.

    Generate delayed consistency tests for predefined meshs.

    Arguments
    ---------
    EQ: PDE function
        Left side part of PDE to test for.
    u: str
        Function to be parsed.
    dim: str
        Name token for multiple meshes to test for.
    mesh: str
        Name of a single mesh to test for.
    p: int
        Polynominal order to test for.

    """
    tst = []
    ms = {}

    meshes = createMeshes()

    if mesh is not None:
        ms[mesh] = meshes[mesh]
    else:
        ms = {}
        for k, m in meshes.items():
            if dim in k:
                ms[k] = m
    u = parse(u=u)

    minPos = pg.Pos(list(ms.values())[0].node(0).pos())
    bcs = {'bc:dir': {'Dirichlet':{'*':u}},
           'bc:neu': {'Neumann':{'*':grad(u)},
                       'Fix':[minPos, u(minPos)]},
           'bc:mix': {'Dirichlet':{'*':u}, 'Neumann':{'2':grad(u)}},
            }

    for m in ms.items():
        for bc in bcs.items():
            tst.append(convergencyTestRunner(EQ, u=u, mesh=m, bc=bc, p=p,
                                             **kwargs))

    return tst


def runTests(tests, testName, workers=1):
    """Run tests in parallel or serial."""
    # lazy imports for expensive dask import
    try:
        pass
        # import dask
        # import dask.delayed
        # from dask.distributed import Client
    except ImportError:
        pg.warning('Dask is not installed. Run tests serially.')
        workers = 1

    pg.tic()
    if testName not in __tests__:
        __tests__[testName] = {}

    if workers == 1:
        results = []
        for _i, t in enumerate(tests):
            print('.', end='', flush=True)
            res = t()
            #res = t
            #print(res, end='')
            results.append(res)

        print()
        if len(results) > 0:
            __tests__[testName].update({k[0]:k[1][0] for k in results})
    else:

        try:
            with Client(n_workers=workers, threads_per_worker=1) as client:
                results = dask.compute(tests)
        except BaseException:
            results  = [t for t in tests]

        if len(results) > 0:
            __tests__[testName].update({k[0]:k[1][0] for k in results})

    pg.toc(f'worker: {workers}')


class TestFEABasicEquations(TestCollection):

    def test_Poisson(self, show=False, verbose=False):
        r"""Test Poisson's equation.

        ..math::

            -\nabla\cdot(\alpha \nabla u) = f

        Note, with :math:`f = 0` this becomes the Laplace equation. We choose
        for negative left hand side so we don't need to switch sign for Neumann
        boundary condition.
        """
        #### START DEBUG WORKSPACE ############################################
        EQ = lambda u: -div(grad(u))

        ms = createMeshes()
        p = 1
        #u = asFunction('x+y')
        u = asFunction('sin(x)')
        #u = asFunction('sin(x)*cos(y)')

        u2 = asFunction('sin(x)+cos(y)')
        #u = asFunction('1.1 + 2.2*x + 3.3*y')

        mesh = list(ms.values())[2]
        minPos = pg.Pos(mesh.node(0).pos())

        bcs = {'bc:dir': {'Dirichlet':{'*':u}},
               'bc:neu': {'Neumann':{'*':grad(u)},
                          'Fix':[minPos, u(minPos)],},
               'bc:mix': {'Dirichlet':{'*':u}, 'Neumann':{'2':grad(u)}},
                }

        bc = bcs['bc:dir']
        #bc = bcs['bc:neu']
        #bc = bcs['bc:mix']
        #mesh = ms['2d-tri']
        #mesh = ms['2d-quad-p']
        #mesh = ms['2d-quad']
        mesh = ms['1d']
        #mesh = ms['3d-hex']
        #mesh = ms['3d-tet']
        # print(mesh)
        # s = ScalarSpace(mesh, p=2, name='u', order=2)
        # consistencyTest(EQ(s) == EQ(u), bc=bc, u=u, tol=1e-11, #solver='cholmod',
        #                 show=True, verbose=True, fast=False)
        with pg.tictoc('tst'):
            try:
                pass

                #convergencyTest(EQ, u1, dim='1d',p=1,cLvl=4,tol=2.7e-3)
                # convergencyTest_(EQ, mesh, bc, u, p=1, cLvl=4, tol=2.7e-3,
                #                 show=True, verbose=True,
                #                 #hex2tet=True
                #                 )


                # convergencyTest(EQ, mesh, u=u, f=None, bc=bc,
                #                 p=1, rLvl=4, refine='space',
                #                 tol=2.7e-3,
                #                 show=True, verbose=True)


            except BaseException as e:
                import sys, traceback
                traceback.print_exc(file=sys.stdout)
                pg.critical(e)

        #print(pg.timings('tst'))

        #return
        #exit()

        #### END DEBUG WORKSPACE ##############################################

        EQName = 'Poisson'

        #EQ = lambda u: -Laplace(u)  # fix extra parsing!
        EQ = lambda u: -div(grad(u))

        tests = []
        u11 = '1.1 + 2.2*x'
        u12 = '1.1 + 2.2*x + 3.3*x²'
        u21 = '1.1 + 2.2*x + 3.3*y'
        u22 = '1.1 + 2.2*x + 3.3*y + 4.4*x² + 5.5*y² + 6.6*x*y'
        u31 = '1.1 + 2.2*x + 3.3*y + 4.4*z'
        u32 = '1.1 + 2.2*x + 3.3*y + 4.4*z + 5.5*x² + 6.6*y² + 7.7*z² + '+\
                '8.8*x*y + 9.9*x*z + 10.10*y*z'

        tests.extend(consistencyTestGen(EQ, u11, dim='1d', p=1, atol=2e-15))
        tests.extend(consistencyTestGen(EQ, u12, dim='1d', p=2, atol=5e-14))
        tests.extend(consistencyTestGen(EQ, u21, dim='2d', p=1, atol=9e-14))
        tests.extend(consistencyTestGen(EQ, u22, dim='2d', p=2, atol=6e-12))
        tests.extend(consistencyTestGen(EQ, u31, dim='3d', p=1, atol=2e-9))
        tests.extend(consistencyTestGen(EQ, u32, dim='3d', p=2, atol=7e-11))

        u1 = 'sin(x)'
        u2 = 'sin(x) + cos(y)'
        u3 = 'sin(x) + cos(y) + sin(z)'

        tests.extend(convergencyTestGen(EQ, u1, dim='1d',p=1,cLvl=4,tol=2.7e-3))
        tests.extend(convergencyTestGen(EQ, u1, dim='1d',p=2,cLvl=4,tol=5.9e-3))
        tests.extend(convergencyTestGen(EQ, u2, dim='2d',p=1,cLvl=4,tol=3.0e-2))
        tests.extend(convergencyTestGen(EQ, u2, dim='2d',p=2,cLvl=4,tol=6.3e-2))

        runTests(tests, EQName, workers=min(len(tests),
                                            pg.core.numberOfCPU()//2))

        tests = []
        tests.extend(convergencyTestGen(EQ, u3,dim='hex',p=1,cLvl=3,tol=1.8e-2))
        tests.extend(convergencyTestGen(EQ, u3,dim='hex',p=2,cLvl=3,tol=2.6e-2))

        tests.extend(convergencyTestGen(EQ, u3, mesh='3d-hex', p=1, cLvl=3,
                                        tol=1.9e-2, hex2tet=True))
        tests.extend(convergencyTestGen(EQ, u3, mesh='3d-hex', p=2, cLvl=3,
                                        tol=2.5e-2, hex2tet=True))

        ## Tester allocate maxMem/workers for each job .. 3D needs some more
        ## so reduce worker count
        workers = min(len(tests), int(pg.core.GByte(pg.core.maxMem())*0.8/2))
        pg._r('workers:',  workers)
        runTests(tests, EQName, workers=workers)
        showTestResults()


    def test_Poisson_Mixed(self, show=False, verbose=False):
        r"""
        Test Mixed formulation of Poisson Equation using Taylor Hood elements.

        ..math::

            v + (\alpha \nabla u) \:&= fv \\
            \nabla\cdot v \:& = f \\

        """
        # TODO need fixes
        return

        # lazy imports for expensive dask import
        #import dask
        #import dask.delayed

        def genWeak(mesh, u, v, var):
            """Gen weak formulation for the mixed poisson testcase."""
            f = div(v)
            alpha = 1e-2
            fv = v + alpha*grad(u)

            # fv = parse(p='sin(x), cos(y)')   #ok -- same like above
            # v = fv - alpha*grad(u)           #ok -- same like above

            w, s = TaylorHood(mesh)

            if var == 'sym:grad':

                pde = [w*(1/alpha*w) + w*grad(s) == w*(1/alpha*fv),
                       grad(s)*w == -s*f]

                bcp = {'Dirichlet': {'*': u}}
                bcv = {'Dirichlet': {'*': v}}
                bc = [var, {s:bcp, w:bcv}]

            elif var == 'sym:div':
                pde = [w*(1/alpha*w) - div(w)*s == w*(1/alpha*fv),
                       - s*div(w) == -s*f]

                bcv = {'assemble':{'*':w*norm(w)*-u}}
                bc = [var, {w:bcv}]

            return pde, bc


        def consistencyTestGen_(u, v, dim, atol):
            """Generate delayed consistency tests."""
            tst = []
            ms = {}
            for k, m in createMeshes().items():
                if dim in k:
                    ms[k] = m

            u, v = parse(u=u, v=v)
            for var in ['sym:grad', 'sym:div']:

                for key, mesh in ms.items():
                    pde, bc = genWeak(mesh, u, v, var=var)

                    tst.append(consistencyTestRunner(pde, u=[v, u],
                               bc=bc, mesh=[key,None],
                               atol=atol, verbose=False))
            return tst


        def convergencyTest_(mesh, u, v, var, cLvl, atol,
                             verbose=False, show=False):
            L2v = []; L2u = []
            H1v = []; H1u = []
            h = []

            for r in range(cLvl):
                mesh = mesh.createH2()
                h.append(min(mesh.h()))

                pde, bc = genWeak(mesh, u, v, var=var)
                vh, uh = solve(pde, bc[1], useMats=True)
                L2u.append(normL2(u-uh))
                L2v.append(normL2(v-vh))
                H1u.append(normSemiH1(u-uh))
                H1v.append(normSemiH1(v-vh))

                if verbose:
                    print('.', end='', flush=True)

            if verbose:
                print()
                pg.info('normL2-u', L2u)
                pg.info('normL2-v', L2v)
                pg.info('normH1-u', H1u)
                pg.info('normH1-v', H1v)

            cuL2 = convergenceRate(h, L2u)
            cvL2 = convergenceRate(h, L2v)
            cuH1 = convergenceRate(h, H1u)
            cvH1 = convergenceRate(h, H1v)

            if verbose:
                pg.info(f'Convergence u L2:{cuL2}')
                pg.info(f'Convergence v L2:{cvL2}')
                pg.info(f'Convergence u H1:{cuH1}')
                pg.info(f'Convergence v H1:{cvH1}')

            if show:
                fig, axs = pg.plt.subplots(2, 2, figsize=(8,8))

                pg.show(uh, ax=axs[0][0], showMesh=True)
                pg.show(abs(vh), ax=axs[0][1])
                pg.show(vh, ax=axs[0][1])

                axs[1][0].loglog(h, L2u, label=f'L2(u)')
                axs[1][0].loglog(h, L2v, label=f'L2(v)')
                axs[1][1].loglog(h, H1u, label=f'H1(u)')
                axs[1][1].loglog(h, H1v, label=f'H1(v)')

                axs[1][0].legend()
                axs[1][0].grid()
                axs[1][0].set_xlabel('cell width $h$')
                axs[1][0].set_ylabel('$||u-uh||_{L_2}$')
                axs[1][1].legend()
                axs[1][1].grid()
                axs[1][1].set_xlabel('cell width $h$')
                axs[1][1].set_ylabel('$|u-uh|_{H_1}$')
                fig.tight_layout()

            # Taylor Hood .. u and v need to converge (h) with O(2)
            assertionErrors = []

            try:
                assertEqual(cuL2[-1], 2.0, atol=atol)
            except AssertionError as e:
                assertionErrors.append([f'cL2u[-1]:{pg.pf(abs(2-cuL2[-1]))}',e])

            try:
                assertEqual(cvL2[-1], 2.0, atol=atol)
            except AssertionError as e:
                assertionErrors.append([f'cL2v[-1]:{pg.pf(abs(2-cvL2[-1]))}',e])

            try:
                assertEqual(cuH1[-1], 1.0, atol=atol)
            except AssertionError as e:
                assertionErrors.append([f'cH1u[-1]:{pg.pf(abs(1-cuH1[-1]))}',e])

            try:
                assertEqual(cvH1[-1], 1.0, atol=atol)
            except AssertionError as e:
                assertionErrors.append([f'cH1v[-1]:{pg.pf(abs(1-cvH1[-1]))}',e])

            if len(assertionErrors) > 0:
                raise AssertionError(assertionErrors)

        #@dask.delayed
        def convergencyTestRunner_(u, v, mesh, var, cLvl, **kwargs):
            """Convergency test for EQ(FEASpace) == EQ(u)."""
            #TODO: check for segfault if the shapfunction cache mutex has been removed!
            pg.setThreadCount(1)
            try:
                if kwargs.get('hex2tet', False):
                    name = f'3d-tet/{var}/convergency'
                else:
                    name = f'{mesh[0]}/{var}/convergency'

                convergencyTest_(mesh[1], u, v, var, cLvl, **kwargs)
                res = (pg._('pass', c='g'), True)
            except AssertionError as e:
                es = [e_[0] for e_ in e.args[0]]
                ae = [e_[1] for e_ in e.args[0]]
                res = (pg._(f'{",".join(es)}', c='r'), ae)
            except TypeError as e:
                res = (pg._('fail (type)', c='r'), e)
            except ValueError as e:
                res = (pg._('fail', c='r'), e)

            return [name, res]


        def convergencyTestGen_(u, v, dim, cLvl, atol):
            """Generate delayed consistency tests."""
            tst = []
            ms = {}
            for k, m in createMeshes().items():
                if dim in k:
                    ms[k] = m

            u, v = parse(u=u, v=v)
            for var in ['sym:grad', 'sym:div']:

                for key, mesh in ms.items():

                    tst.append(convergencyTestRunner_(u=u, v=v,
                               mesh=[key, mesh], var=var, cLvl=cLvl,
                               atol=atol, verbose=False))
            return tst

        #### START DEBUG WORKSPACE #############################################

        ms = createMeshes()
        # u = parse(u='x+y')
        # v = parse(v='x², -(x*y)')

        # mesh = ms['2d-quad']
        # for i in range(1):
        #     mesh = mesh.createH2()

        # pde = [w*(1/alpha*w) + w*grad(s) == w*(1/alpha*fv),
        #        grad(s)*w == -s*f]

        # vh1, uh1 = solve(pde, bc={s:bcp, w:bcv}, useMats=True, solver='scipy')

        # print(normL2(v-vh1))
        # print(normL2(u-uh1))
        # print(normSemiH1(v-vh1))
        # print(normSemiH1(u-uh1))

        #print(vh1[0])
        #ax = pg.show(uh1)[0]
        # pg.show(uh1.mesh, u, ax=ax)

        # pg.show(vh1, ax=ax)
        # pg.show(vh1.mesh, v1, ax=ax)
        #pg.show(vh1.mesh, v1(vh1.mesh)[:,0], ax=ax)
        # pde = [w*(1/alpha*w) + w*grad(s) == w*(1/alpha*fv),
        #        grad(s)*w == -s*f]
        # vh1, uh1 = solve(pde, bc={s:bcp, w:bcv}, core=False)

        # consistencyTest(pde=pde, bc={s:bcp, w:bcv},
        #                 u=[v, u], tol=1e-12, show=False, verbose=True)
        tests  = []

        # tests.extend(consistencyTestGen_(u='x', v='x², 0',
        #                                  dim='1d', atol=1.1e-12))

        tests.extend(consistencyTestGen_(u='x+y', v='x², -(x*y)',
                                         dim='2d', atol=6e-12))

        tests.extend(consistencyTestGen_(u='x+y+z',
                                         v='x², -(x*y)+(y*z), (y*z)-(x*z)',
                                         dim='3d', atol=2.0e-11))

        #runTests(tests, 'Poisson-mixed', workers=1)

        # showTestResults()
        # return
        u1 = 'sin(x)'
        v1 = 'cos(x), 0'   #TODO no the need for vector function 1D
        u2 = 'sin(x)*cos(y)'
        v2 = 'sin(x)*cos(y), cos(x)*sin(y)'
        u, v = parse(u=u2, v=v2)

        pg.tic()
        #convergencyTest_(ms['2d-tri'], u, v, var='sym:grad', cLvl=4, atol=0.21, verbose=True)
        #convergencyTest_(ms['2d-tri-u'], u, v, var='sym:grad', cLvl=4, atol=0.21, verbose=True, show=True)
        #convergencyTest_(ms['2d-tri-r'], u, v, var='sym:grad', cLvl=5, atol=0.21, verbose=True, show=True)
        #convergencyTest_(ms['2d-tri-r'], u, v, var='sym:div', cLvl=4, atol=0.21, verbose=True, show=True)

        #return


        #convergencyTestGen_(u1, v1, dim='2d-quad', cLvl=4, atol=0.21)[0].compute()

        #return
        #### END DEBUG WORKSPACE ##############################################

        u1 = 'sin(x)'
        v1 = 'cos(x), 0'   #TODO no the need for vector function 1D
        #tests.extend(convergencyTestGen_(u=u1, v=v1, dim='1d', cLvl=5, atol=0.08))

        u2 = 'sin(x)*cos(y)'
        v2 = 'sin(x)*cos(y), cos(x)*sin(y)'


        tests.extend(convergencyTestGen_(u=u2, v=v2, dim='2d',
                                         cLvl=4, atol=0.32))
        # _testConv(ms['2d-quad'], u2, v2, cLvl=4, atol=0.2)
        # _testConv(ms['2d-quad-r'], u2, v2, cLvl=4, atol=0.27)
        # _testConv(ms['2d-tri'], u2, v2, cLvl=4, atol=0.22)

        u3 = 'sin(x)*cos(y) + sin(z)*cos(x)'
        v3 = 'sin(x)*cos(y), cos(x)*sin(y), sin(z)*cos(y)'
        tests.extend(convergencyTestGen_(u=u3, v=v3, dim='3d',
                                         cLvl=2, atol=0.32))

        workers = min(len(tests), int(pg.core.GByte(pg.core.maxMem())*0.8/2))

        pg._r('workers:',  workers)
        workers = 1
        runTests(tests, 'Poisson-mixed', workers=workers)
        showTestResults()
        # return

        # # need better solver for larger cLvl
        # u3 = 'sin(x)*cos(y) + sin(z)*cos(x)'
        # v3 = 'sin(x)*cos(y), cos(x)*sin(y), sin(z)*cos(y)'
        # _testConv(ms['3d-hex'], u3, v3, cLvl=2, atol=0.95)
        # _testConv(ms['3d-tet'], u3, v3, cLvl=2, atol=0.46)


    def test_1D_Helmholtz_R1_Steady(self, show=False, verbose=False):
        """
        """
        return
        pdeName = 'Helmholtz-R1'
        np.random.seed(1337)
        ##################
        # Notes:
        #  * Order and complexity of parameter functions a, b, etc.
        #    are needed to fit integration order for exact tests.
        #  * mesh dimension need to fit field dimensions.
        #    e.g, can't simulate 2D field in 1D space because of
        #    missing gradient parts which are part of f
        #  * For trigonometric functions ensure sample theorem,
        #    i.e., at least 2 sample points (h) per period or aliasing kicks in
        ###################

        x = np.linspace(-2, 2, 7) # 4 is minimum, 3 leads to ambiguity (Fixme!)
        m1 = pg.createGrid(x)

        m2 = pg.Mesh(m1)
        dx = m2.h()[0]
        for n in m2.nodes()[1:-1]:
            n.setPos(n.pos() + [np.random.randn()*dx/4, 0.0, .0])

        meshs = {'1d-struct': m1,
                 '1d-unstruct': m2}

        ##################
        # 1D Exact - p1
        ##################
        f, u, du, a, b = parse(f='-div(a*grad(u)) + b*u',
                                 u='1.1 + 2.2 * x', du='grad(u)',
                                 a='3.3 + x²', b='4.4 + x²')

        bcs = {'bc:dir': {'Dirichlet':{'*':u}},
               'bc:neu': {'Neumann':{'2':a*du}, 'Fix':[pg.Pos(x[0],0), u(x[0])]},
               'bc:mix': {'Dirichlet':{'2':u}, 'Neumann':{'1':a*du}}}

        s = ScalarSpace(meshs['1d-unstruct'], p=1)
        # testPDEConsistency(-div(a*grad(s)) + b*s == f, bc=bcs['bc:dir'],
        #                    u=u, du=du, tol=1e-12, show=True, verbose=False)

        runConsistencyTests(pdeName, lambda s: -div(a*grad(s)) + b*s == f,
                            meshs, bcs, u, du, tol=1e-12, p=1)

        ##################
        # 1D Exact - p2
        ##################
        f, u, du, a, b = parse(f='-div(a*grad(u)) - b*u',
                                 u='1.1 + 2.2 * x²', du='grad(u)',
                                 a='3.3 + x**2', b='4.4 + x³')

        bcs = {'bc:dir': {'Dirichlet':{'*':u}},
               'bc:neu': {'Neumann':{'2':a*du}, 'Fix':[pg.Pos(x[0],0), u(x[0])]},
               'bc:mix': {'Dirichlet':{'2':u}, 'Neumann':{'1':a*du}}}

        s = ScalarSpace(meshs['1d-struct'], p=2)
        # testPDEConsistency(-div(a*grad(s)) - b*s == f, bc=bcs['bc:neu'],
        #                    u=u, du=du, tol=3.1e-8,
        #                    show=True, verbose=verbose)

        runConsistencyTests(pdeName, lambda s: -div(a*grad(s)) - b*s == f,
                            meshs, bcs, u, du, tol=3.1e-8, p=2)

        ######################
        # 1D Convergence rate
        ######################
        f, u, du, a, b, eps = parse(f='-div(a*grad(u)) + b*u',
                                      u='1.1 + tanh(x)*cos(x**2)', du='grad(u)',
                                      a='2 + cos(pi*x/4)', b='2 + sin(pi*x/4)', eps='0.2e-1')

        bcs = {'bc:dir': {'Dirichlet':{'*':u}},
               'bc:neu': {'Neumann':{'2':a*du}, 'Fix':[pg.Pos(x[0],0), u(x[0])]},
               'bc:mix': {'Dirichlet':{'2':u}, 'Neumann':{'1':a*du}}}


        # testPDEConvergence(lambda s: -div(a*grad(s)) + b*s == f, meshs['1d-struct'], bc=bcs['bc:neu'],
        #                     u=u, du=du, convLvl=4, tol=0.01,
        #                     show=True, verbose=verbose)

        runConvergenceTests(pdeName, lambda s: -div(a*grad(s)) + b*s == f, meshs, bcs, u, du, convLvl=4, tol=0.02)

        showTestResults(pdeName)


    def test_2D_Helmholtz_R1_Steady(self, show=False, verbose=False):
        """
        """
        return
        pdeName = 'Helmholtz-R1'
        np.random.seed(1337)
        ##################
        # Notes:
        #  * Order and complexitiy of parameter functions a, b, etc.
        #    are needed to fit integration order for exact tests.
        #  * mesh dimension need to fit field dimensions.
        #    e.g, can't simulate 2D field in 1D space because of
        #    missing gradient parts which are part of f
        #  * For trigonometric functions ensure sample theorem,
        #    i.e., at least 2 sample points (h) per period or aliasing kicks in
        ###################

        x = np.linspace(-2, 2, 5) # 4 is minimum, 3 leads to ambiguity (Fixme!)
        q1 = pg.createGrid(x, x)

        q2 = pg.Mesh(q1)
        dx = q2.h()[0]
        for n in q2.nodes():
            if not n.onBoundary():
                n.setPos(n.pos() + [np.random.randn()*dx/8, np.random.randn()*dx/8, .0])

        t1 = pg.meshtools.refineQuad2Tri(q1)
        t2 = pg.meshtools.refineQuad2Tri(q2, style=1)

        meshs = {'2d-quad-struct': q1,
                 '2d-quad-unstruct': q2,
                 '2d-tri-struct': t1,
                 '2d-tri-unstruct': t2}

        ##################
        # 2D Exact - p1
        ##################
        f, u, du, a, b = parse(f='-div(a*grad(u)) + b*u',
                                 u='1.1 + 2.2 * x + 3.3 * y', du='grad(u)',
                                 a='3.3 + x² + y²', b='4.4 + x² + y²')

        bcs = {'bc:dir': {'Dirichlet':{'*':u}},
               'bc:neu': {'Neumann':{'*':a*du}, 'Fix':[pg.Pos(x[0],x[0]), u(pg.Pos(x[0],x[0]))]},
               'bc:mix': {'Dirichlet':{'1,2':u}, 'Neumann':{'3,4':a*du}}}

        # s = ScalarSpace(meshs['2d-tri-unstruct'], p=1)
        # testPDEConsistency(-div(a*grad(s)) + b*s == f, bc=bcs['bc:dir'],
        #                     u=u, du=du, tol=1e-12, show=True, verbose=True)

        #runConsistencyTests(pdeName, lambda s: -div(a*grad(s)) + b*s == f, meshs, bcs, u, du, tol=1e-12, p=1)


        ##################
        # 2D Exact - p2
        ##################
        f, u, du, a, b = parse(f='-div(a*grad(u)) - b*u',
                                 u='1.1 + 2.2 * x² + 3.3*y²', du='grad(u)',
                                 a='3.3 + x² + y²', b='4.4 + x² + y²')

        bcs = {'bc:dir': {'Dirichlet':{'*':u}},
               'bc:neu': {'Neumann':{'*':a*du}, 'Fix':[pg.Pos(x[0],x[0]), u(pg.Pos(x[0],x[0]))]},
               'bc:mix': {'Dirichlet':{'1,2':u}, 'Neumann':{'3,4':a*du}}}

        # s = ScalarSpace(meshs['2d-tri-unstruct'], p=2)
        # testPDEConsistency(-div(a*grad(s)) - b*s == f, bc=bcs['bc:neu'],
        #                    u=u, du=du, tol=3e-8,
        #                    show=True, verbose=verbose)

        #runConsistencyTests(pdeName, lambda s: -div(a*grad(s)) - b*s == f, meshs, bcs, u, du, tol=4e-8, p=2)

        ######################
        # 2D Convergence rate
        ######################
        f, u, du, a, b, eps = parse(f='-div(a*grad(u)) + b*u',
                                      u='1.1 + cos(pi*(x/2)²)*sin(pi*(y/2)²)', du='grad(u)',
                                      a='2 + cos(pi*x/4)*sin(pi*x/2)', b='2 + sin(pi*x/4)*cos(pi*x/2)', eps='0.2e-1')

        bcs = {'bc:dir': {'Dirichlet':{'*':u}},
               'bc:neu': {'Neumann':{'*':a*du}, 'Fix':[pg.Pos(x[0],x[0]), u(pg.Pos(x[0],x[0]))]},
               'bc:mix': {'Dirichlet':{'1,2':u}, 'Neumann':{'3,4':a*du}}}

        # s = ScalarSpace(meshs['2d-quad-unstruct'], p=2)
        # testPDEConsistency(-div(a*grad(s)) + b*s == f, bc=bcs['bc:neu'],
        #                    u=u, du=du, tol=3e-8,
        #                    show=True, verbose=True)

        testPDEConvergence(lambda s: -div(a*grad(s)) + b*s == f, meshs['2d-quad-unstruct'], bc=bcs['bc:dir'],
                            u=u, du=du, convLvl=4, tol=0.1,
                            show=True, verbose=True)

        #runConvergenceTests(pdeName, lambda s: -div(a*grad(s)) + b*s == f, meshs, bcs, u, du, convLvl=4, tol=0.02)

        showTestResults(pdeName)


    def test_unsteady(self):
        """Test time dependent problems.
        """

        def test_(var, **solvingArgs):

            theta = solvingArgs.pop('theta', 1)

            if theta == 0.5:
                u, a = parse(u='1 + x*t²', a='1+x')
            else:
                u, a = parse(u='1 + x*t', a='1+x')

            x = np.linspace(0, 0.5, 10)
            t = np.linspace(0, 0.5, 10)
            # for explicit its unstable for later times with a smaller amount
            mesh = pg.createGrid(x)

            EQ = lambda s: derive(s, 't') - div(a*grad(s))
            f = EQ(u)
            s = ScalarSpace(mesh, p=1)
            bc = {'Dirichlet':{'*':u}}

            uh = FEASolution(space=s, values=u)

            if var == 0:

                uh = solve(EQ(s) == f, bc=bc,
                           ic=uh, times=t, theta=theta, solver='scipy',
                           dynamic=True)

                #assertEqual(normL2(uh-u), 0.0, atol=1e-15)
                #return uh
            else:
                for i in range(1, len(t)):
                    dt = t[i] - t[i-1]

                    if var == 1:
                        # explicit
                        # uh = solve(s*s == s*u - dt*Lu + dt*R,
                        #           bc=bc, **solvingArgs, time=t[i])

                        # u = testSolve(s*s == s*u - dt*Lu + dt*R,
                        #              bc=bc, time=t[i])
                        pass
                    elif var == 2:
                        # implicit
                        #L = s*s + grad(s)*dt*a*grad(s) == dt*s*f + s*uh  # ok
                        #L = s*1/dt*(s-uh) + grad(s)*a*grad(s) == s*f     # ok
                        L = s*(s-uh)/dt == - grad(s)*a*grad(s) + s*f        # ok

                        uh = solve(L, bc=bc, **solvingArgs, time=t[i])
                    elif var == 3:
                        L = s*(s-uh)/dt == theta * (-grad(s)*a*grad(s) + s*f) \
                                    + (1-theta) * (-grad(s)*a*grad(uh) + s*f(t=t[i-1]))

                        uh = solve(L, bc=bc, **solvingArgs, time=t[i])

                    elif var == 4:
                        # theta scheme algebraic
                        if i == 1:
                            dirichlet = DirichletManager({s:bc}, dynamic=True)
                            A = L.assemble(useMats=True)
                            M = (s*s).assemble(useMats=True)
                            S = M + theta * dt * A
                            dirichlet.apply(S, time=0)
                            solver = pg.solver.LinSolver(S)

                        rhs = (M - (1-theta) * dt * A) * u.values + \
                        (1-theta) * dt * R.assemble(useMats=True, time=t[i-1]) + \
                            theta * dt * R.assemble(useMats=True, time=t[i])

                        dirichlet.apply(rhs, time=t[i])
                        uf = solver(rhs)
                        u = s.split(uf)


            assertEqual(normL2(uh-u), 0.0, atol=2.6e-14)

            return uh


        # var = 0  # strong form automatic solve
        # var = 1  # explicite with expressions
        # var = 2  # implicite with expressions
        # var = 3  # theta scheme with expressions
        # var = 4  # theta scheme algebraic

        def _s(**kwargs):
            T0 = test_(core=False, **kwargs)
            T1 = test_(core=True, **kwargs)
            T2 = test_(useMats=True, **kwargs)
            assertEqual(T0, T1)
            assertEqual(T0, T2)

        for var in [0,
                    2,
                    ]:
            _s(var=var)

        ## test theta schemes

        for var in [0,
                    3,
                    ]:
            _s(var=var, theta=1.0)
            #_s(var=var, theta=0) # need tweaks
            _s(var=var, theta=0.5)


    def test_Picard(self, show=False):
        """
        Nonlinear Poisson's equation. See notebook Picard
        """
        return
        m = 3
        uExact = lambda x_: ((2**(m+1)-1)*x+1)**(1/(m+1)) -1

        x = np.linspace(0, 1, 21)
        mesh = pg.createGrid(x)


        def p1(x, ent):
            if isinstance(u, int):
                return (1 + u)**m
            return (1 + u(x))**m
        u = 0

        def p2(u):
            return (1 + u)**m

        bc = {'Dirichlet':{1:0, 2:1}}

        for var1 in [1, 2, 3]:
        #for var1 in [1]:

            for var2 in [1, 2, 3]:
            #for var2 in [1, 3]:

                s = ScalarSpace(mesh, p=1)
                u = FEASolution(space=s)

                if var1 == 1:
                    L = p1 * grad(s) * grad(s) == 0
                elif var1 == 2:
                    L = p2(u) * grad(s) * grad(s) == 0
                elif var1 == 3:
                    p3 = (1 + u)**m
                    L = p3 * grad(s) * grad(s) == 0

                for i in range(10):
                    pg.tic()
                    # u = testSolve(L, bc=bc)  ## will not work because L depends on u
                    if var2 == 1:
                        u = solve(L, bc=bc, core=False)
                    elif var2 == 2:
                        u = solve(L, bc=bc, core=True)
                    else:
                        u = solve(L, bc=bc, useMats=True)

                    # pg._g(min(u.values), max(u.values), np.median(u.values))
                    #u = solve(L, bc=bc, useMats=True)
                    # u.continuous = True
                    # u.continuous = False

                    # print(i, u.history)
                    if i > 1:
                        err = pg.solver.normL2(u.history[-1]- u.values, u.mesh)
                        #print(err, pg.dur())

                ux = u([[xi,0] for xi in x])
                err = pg.solver.normL2(ux-uExact(x))
                #print(var1, var2, err)
                try:
                    assertEqual(err, 1.72041085607096e-05)
                except:
                    pg._r('fail: ', var1, var2)
                    assertEqual(err, 1.72041085607096e-05)

        if show:
            pg.plt.plot(x, uExact(x), label='exact')
            pg.plt.plot(x, ux, 'o', label=f'u Picard iteration err:{pg.pf(err)}')
            pg.plt.grid()
            pg.plt.legend()


if __name__ == '__main__':

    import unittest
    pg.tic()
    unittest.main(exit=False)

    print()
    pg.info(f'Absolut tests: {testCount()}, took {pg.dur()} s')
