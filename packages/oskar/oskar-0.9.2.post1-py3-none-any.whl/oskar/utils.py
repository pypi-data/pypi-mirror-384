#!/usr/bin/env python
"""Some useful functions that are used frequently."""

from time import time

import numpy as np
import pygimli as pg

from .units import varNameAsLatex


# pg.warn('fix posList (N,3) vs. vecField (2|3, N)')
__newFieldOrder__ = False

def _toField(v):
    """Convert into field array (Utility function)."""
    if isinstance(v, list):
        v = np.asarray(list)

    #pg._g(v.shape)
    if v.ndim == 2:
        if v.shape[0] == 3:
            ## assuming input is (dim x N) -- new Field order
            if __newFieldOrder__:
                return v
            else:
                return v.T
        elif v.shape[1] == 3 or v.shape[1] == 2:
            ## assuming input is (N x dim)
            if __newFieldOrder__:
                return v.T
            else:
                return v

        if __newFieldOrder__:
            return v
        else:
            return v.T
    else:
        return v


def asVecField(v):
    """Convert into a vector field.

    new field order [3 x N]
    old field order [N x 3] # like posList -- need to be changed!
    """
    return _toField(v)


def isVecField(v):
    """Check only for new order."""
    if __newFieldOrder__:
        if isinstance(v, np.ndarray) and v.ndim == 2 \
            and (v.shape[0] <= 3 and v.shape[1] > 3):
                return True
    else:
        if isinstance(v, np.ndarray) and v.ndim == 2 \
            and (v.shape[1] <= 3 and v.shape[0] > 3):
                return True
    return False


def asPosListNP(p):
    """Convert into ndarray((N,3)) for p.

    x        -> [[x, 0, 0]]
    [x,y]    -> [[x, y, 0]]
    [[x,y],] -> [[x, y, 0], ]
    [x,y,z]  -> [[x, y, z]]
    [x_i]    -> [[x_i, 0, 0],] for len > 3
    [p_i]    -> [p_i] for len(p) = 2 | 3
    """
    if pg.isScalar(p):
        return asPosListNP([float(p), 0.0, 0.0])
    if pg.isArray(p, 2):
        return asPosListNP([float(p[0]), float(p[1]), 0.0])
    if pg.isPos(p):
        return np.asarray([p])
    if pg.isPosList(p):
        ret = np.asarray(p)
        if ret.shape[1] == 2:
            #  [[x,y],] -> [[x, y, 0], ]
            ret = np.c_[ret, np.zeros(ret.shape[0])]
        return ret
    if isinstance(p, pg.core.Mesh):
        return np.asarray(p.positions())
    if pg.isArray(p):
        return np.asarray([p, np.zeros_like(p), np.zeros_like(p)]).T

    pg._y(p)
    pg.critical("Don't know conversion to pos list.")


def asPosListPG(p):
    """Convert into pg.PosList for p."""
    if isinstance(p, (pg.core.stdVectorR3Vector)):
        return p
    p = asPosListNP(p)
    return pg.core.R3Vector(p)


def asAnisotropyMatrix(lon, trans, perp=None, theta=0.0):
    """Create anisotropy matrix with desired properties.

    Anisotropy tensor from longitudinal value lon,
    transverse value trans and the angle theta of the symmetry axis
    relative to the vertical after  cite:WieseGreZho2015
    https://www.researchgate.net/publication/249866312_Explicit_expressions_for_the_Frechet_derivatives_in_3D_anisotropic_resistivity_inversion

    TODO
    ----
        * 3D, with angles

    Arguments
    ---------
    lon: float
        Longitudinal value of the anisotropy tensor.
    trans: float
        Transverse value of the anisotropy tensor.
    theta: float [0.0]
        Angle of the symmetry axis relative to the vertical in radians.
    perp: float [None]
        Perpendicular (to the 2D plane) value of the anisotropy tensor.
        If not given, it is assumed to be 2D anisotropy.

    Returns
    -------
    C: np.ndarray((2,2)) | np.ndarray((3,3))
        Anisotropy matrix with the given properties.
        The matrix is symmetric and positive definite.
    """
    if perp is not None:
        # 3D anisotropy tensor
        C = np.zeros((3,3))
        C[2,2] = perp
    else:
        C = np.zeros((2,2))

    C[0,0] = lon * np.cos(theta)**2 + trans * np.sin(theta)**2
    C[0,1] = 0.5 * (-lon + trans) * np.sin(theta) * np.cos(theta)
    C[1,0] = 0.5 * (-lon + trans) * np.sin(theta) * np.cos(theta)
    # Check what is correct .. the papers are diverged
    # C[0,1] = 0.5 * (-valL + valT) * np.sin(2*theta) * np.cos(theta)
    # C[1,0] = 0.5 * (-valL + valT) * np.sin(2*theta) * np.cos(theta)
    C[1,1] = lon * np.sin(theta)**2 + trans * np.cos(theta)**2
    return C


def addConvergenceForCol(table, colID, addReduction=False):
    """Add convergence rate into a table."""
    reduction = np.zeros(len(table))

    colID = np.atleast_1d(colID)
    cOff = 0
    for c in colID:
        reduction[1:] = 1/(table[1:,c+cOff] / table[0:-1,c+cOff])

        conv = np.zeros_like(reduction)
        conv[1:] = np.log2(reduction.astype(float))[1:]
        if addReduction:
            cOff += 1
            table = np.insert(table, c+cOff, reduction, axis=1)
            cOff += 1
            table = np.insert(table, c+cOff, conv, axis=1)
        else:
            cOff += 1
            table = np.insert(table, c+cOff, conv, axis=1)

    return table


def convergenceRate(h, e):
    """Return convergence rate.

    Arguments
    ---------
    h: iterable(float)
        decreasing grid spacing
    e: iterable(float)
        Error values for each grid value
    """
    if len(h) == len(e) and len(h) > 1:
        c = np.zeros(len(h)-1)
        for i in range(len(h)-1):
            try:
                c[i] = np.log(e[i+1] / e[i]) / np.log(h[i+1] / h[i])
            except BaseException as e:
                pg.error(e)
                pass
        return c


def drawConvergenceOrder(ax, limits, order=None, ref=None, inv=None):
    """Draw lines of convergence orders.

    Fill a axe with lines of convergence orders, regarding discretization
    length or mesh size.
    The axe will get log-log scale.
    You can provide some reference values to give a proper offset position
    for the lines.
    The order can be estimated from the reference values.
    The order line can be drawn inverse by flag or if the limits are in
    ascending order.

    Arguments
    ---------
    ax: mpl.Axes

    limits: [hStart, hEnd]
        Limits for the draws. If limits have more than 2 values, limits will be
        chooses as bounding decades.

    order: None | int | [float|int,]
        Orders to draw. If order is None, we try to determine a single order
        from ref and limits, which needs to have the same length.

    ref: float [None]
        Reference value to start from.
        If `ref` is an array, reference value is chosen as the first value.

    inv: bool [None]
        Draw inverse order, i.e., 1/order. If order set to None it depends
        on ascending order of `limits`.

    Example
    -------
    >>> import matplotlib.pyplot as plt
    >>> from oskar.utils import drawConvergenceOrder
    >>> fig, axs = plt.subplots(1,2)
    >>> h = [0.5, 0.25, 0.125, 0.0625]
    >>> N = [20, 40, 80, 160]
    >>> err = [0.1, 0.05, 0.025, 0.0125]
    >>> axs[0].scatter(h, err) # doctest: +ELLIPSIS
    <matplotlib.collections.PathCollection...
    >>> drawConvergenceOrder(axs[0], limits=h, ref=err)
    >>> drawConvergenceOrder(axs[0], limits=h, order=[0.5, 2], ref=err)
    >>> axs[0].grid(True)
    >>> axs[0].legend()  # doctest: +ELLIPSIS
    <matplotlib.legend.Legend...
    >>> axs[1].scatter(N, err) # doctest: +ELLIPSIS
    <matplotlib.collections.PathCollection...
    >>> drawConvergenceOrder(axs[1], limits=N, ref=err)
    >>> drawConvergenceOrder(axs[1], limits=N, order=[0.5, 2], ref=err)
    >>> axs[1].grid(True)
    >>> axs[1].legend()  # doctest: +ELLIPSIS
    <matplotlib.legend.Legend...
    """
    if order is None:
        if len(np.atleast_1d(limits)) == len(np.atleast_1d(ref)):
            c = np.abs(convergenceRate(limits, ref))
            cs = []
            for i, _c in enumerate(c):
                if _c < 0 or ref[i+1] < 1e-13:
                    break
                cs.append(_c)
            order = [int(np.round(np.median(cs)))]

        else:
            c = convergenceRate(ref[:,0], ref[:,1])
            # print(ref[:,0].shape)
            # print(c)
            # print(c.shape)
            cs = []
            for i, _c in enumerate(c):
                if _c < 0 or ref[i+1, 1] < 1e-13:
                    break

                cs.append(_c)

            #order = [int(np.round(np.max(c[np.where(c > 0)[0]])))]
            #order = [int(np.round(np.mean(c[np.where(c > 0)[0]])))]
            order = [int(np.round(np.median(cs)))]
            ref = ref[0,1]

    if len(limits) > 2:
        ht = pg.utils.niceLogspace(vMin=limits[0], vMax=limits[-1], nDec=10)
    else:
        ht = np.logspace(np.log10(limits[0]), np.log10(limits[1]), 10)

    ls = {0.5:'--', 1:'-', 1.5:(0, (3, 5, 1, 5, 1, 5)), 2:'-.', 3:':',
            4:(0, (3, 5, 1, 5, 1, 5)),
            5:'-',
            6:'-',
            7:'-',
            8:'-'}

    if inv is None:
        inv = ht[-1] > ht[0]

    osBase = 'N' if inv else 'h'

    for o in order:
        oStr = f'${osBase}$' if o == 1 else f'${osBase}' + '^{' + str(o) + '}$'

        if ref is not None:
            if np.atleast_1d(ref).ndim == 1 and \
                len(np.atleast_1d(ref) == len(limits)):

                if inv:
                    v = (1/(ht/limits[0]))**o * ref[0]
                else:
                    v = (ht/limits[0])**o * ref[0]
            else:
                if inv:
                    v = ref*(1/(ht/ht[0]))**o
                else:
                    v = ref*(ht/ht[0])**o
        else:
            v = (1/ht)**o if inv else ht**o

        ## assuming H2 refinement means h = h/2
        #dim = 2<matplotlib.legend.Legend...
        ax.loglog(ht, v, color='k', ls=ls[o], lw=0.5, alpha=0.5,
                  label=r'$\cal{O}$ ('+oStr+')')


def comparingLabels(ax, labels):
    """Create custom legend lines and labels for comparison.

    Create custom legend lines and labels for N repeating series labels for
    M comparable entries.
    Combine the legend entries to N + M instead of N x M legend entries.
    The M comparable entries will get black colors,
    but keep the line and marker style.
    Repeatable series get a line, but keep there color.

    Arguments
    ---------
    ax: mpl axes
        Axes object with repeating line styles and label names.
    labels: [str,]
        Labels for comparable.

    Returns
    -------
    lines, labels for legend

    Example
    -------
    >>> import numpy as np
    >>> import pygimli as pg
    >>> import oskar
    >>> ax = pg.plt.subplots()[1]
    >>> t = np.linspace(0, 1)
    >>> for i in range(3): # iterate through series
    ...    _= ax.plot(t, np.sin(np.pi*2*t+i/10),
    ...             label=f'series {i}', c=f'C{i}', ls='-');   #comp. 1
    ...    _= ax.plot(t, np.sin(np.pi*2*t)+i*0.5,
    ...             label=f'series {i}', c=f'C{i}', ls=':');   #comp. 2
    ...    _= ax.plot(t, np.sin(np.pi*2*t)-i*0.5, '.',
    ...             label=f'series {i}', c=f'C{i}');
    >>> ax.legend(*comparingLabels(ax, ['comp1', 'comp2', 'comp3']))  # doctest: +ELLIPSIS
    <matplotlib.legend.Legend...
    """
    from matplotlib.lines import Line2D

    h, _lbl = ax.get_legend_handles_labels()
    lines = []
    names = []
    for i, li in enumerate(labels):
        line = Line2D([0], [0], c='k', lw=1.5)
        line.set_linestyle(h[i].get_linestyle())
        line.set_linewidth(h[i].get_linewidth())
        line.set_marker(h[i].get_marker())
        lines.append(line)
        names.append(li)

    for i, li in enumerate(_lbl):
        if i%len(labels) == 0:
            lines.append(Line2D([0], [0], color=h[i].get_color(), lw=1.5))
            names.append(li)
    return lines, names


def runBenchmark(tests, cached=True, **forEach):
    """Run tests as benchmark."""
    ret = {}

    for test, [f, *callArgs, callKWargs] in tests.items():
        #pg._r(callArgs, callKWargs)
        callKWargs = dict(**callKWargs)
        ret[test] = []

        for k, v in forEach.items():
            for i, vi in enumerate(v):
                callKWargs[k] = vi
                #pg._y(callArgs, callKWargs)
                if cached:
                    if len(callArgs) > 0:
                        ret[test].append(pg.cache(f)(*callArgs,
                                                        **callKWargs))
                    else:
                        ret[test].append(pg.cache(f)(**callKWargs))
                else:
                    if len(callArgs) > 0:
                        ret[test].append(f(*callArgs, **callKWargs))
                    else:
                        ret[test].append(f(**callKWargs))
                # print()getattr(tests[0], **tests[1], k=vi)

            ret[test] = np.array(ret[test])

    return ret


def getInstanceAssignmentName(clsName=None):
    """Get the instance name of the first assignment.

    Get variable 'a' name for:

    'a = Class()'

    Arguments
    ---------
    clsName: str
        Fallback name if the stack search for the name fails.

    Example
    -------
    >>> import oskar
    >>> class foo:
    ...     def __init__(self):
    ...         self.name = oskar.utils.getInstanceAssignmentName('foo')
    >>> a = foo()
    >>> print(a.name)
    a
    >>> def foo():
    ...     return oskar.utils.getInstanceAssignmentName()
    >>> a = foo()
    >>> print(a)
    a
    """
    import inspect
    debug = 0
    # if debug:
    #     # fi = open('dummy.txt', 'w')
    #     pass

    with pg.tictoc('getInstanceAssignmentName'):
        cmp = []
        for i, s in enumerate(inspect.stack()[2:]):
            try:
                cC = s.code_context[0]
                # if debug:
                #     fi.write(f"{i}\n {s}\n {cC} \n")
                #print(cC)

                if 'super()' not in cC and '=' in cC:
                    name, rest = cC.split('(')[0].split('=')
                    #pg._b(name, rest, name.strip())
                    if len(name.strip()) > 0:
                        #pg._y(name, rest, name.strip())
                        cmp.append([name, rest])
            except BaseException:
                pass

        # search for classname
        for name, rest in cmp:
            if rest.strip() == clsName:
                return name.strip()

        # search for first match that is no test runner

        excludePattern = ['testRunner', 'TestRunner',    #pytest
                        'hook_impl', 'TResult', 'doit',  #pytest
                        'pytest', 'CallInfo',            #pytest
                        'reply_content', 'run_cell',     #notebook
                        'runner', 'run_ast_nodes',       #notebook
                        'old_func',                      #vscode
                        'Sphinx',                        #sphinx-gallery
                        'generate_dir_rst',              #sphinx-gallery
                        'parallel',                      #sphinx-gallery
                        'self._result',                  #pytest-xdist
                        'docnames',                      #autodoc
                        'document',                      #autodoc
                        'result',                        #autodoc
                        'absoffset',                     #autodoc
                        'title',                         #mpl
                        'label',                         #mpl
                        'ax',                            #mpl
                        'axs',                           #mpl
                        'code',                          #ruff, tox
                        ]

        #excludePattern = []
        candidates = []

        if debug:
            pg._b('searching ... ')

        for name, rest in cmp:

            if debug:
                print('*'*100)
                print(f'name: "{name}": rest "{rest}"')

            if len(name.lstrip().rstrip().split()) > 1:
                if debug:
                    pg._r(f'exclude (split name) "{name}"')
                continue

            ex = False
            for pat in excludePattern:
                if pat in rest or pat in name:
                    ex = True
                    break

            if ex:
                if debug:
                    pg._r(f'exclude (exclude pattern) "{name}"')
                continue

            if debug:
                pg._g(f'candidates: "{name}" = "{rest}"')
            candidates.append(name.strip())

        if len(candidates) > 0:
            if debug:
                pg._g(f'choose last candidate: "{candidates[-1]}"')
            return candidates[-1]

        return clsName


def pprint(*args, end='\n'):
    """Pretty print all given objects.

    Calls 'a._repr_str_()' if available.
    """
    if len(args) == 1:
        if hasattr(args[0], '_repr_html_'):
            if pg.isNotebook():
                # create Display object for latex renderer
                from IPython.display import display, Markdown
                display(Markdown(args[0]._repr_html_()))
                return ''
            elif pg.isIPyTerminal():
                # will be caught and rendered as html from sphinx-gallery
                return args[0]._repr_html_()

        try:
            print(args[0]._repr_str_(), end=end)
        except BaseException:
            print(args[0], end=end)
        return

    for a in args:
        pprint(a)


def asLatex(obj, lhs=None, mode='equation'):
    """Return latex str for obj."""
    try:
        if obj.hasSympy():
            obj = obj.sympy()
    except BaseException:
        pass

    import sympy as sp
    tex = sp.latex(obj, mode=mode, itex=True)

    para = []
    if r'\mathbf{{x}_{C}}' in tex:
        para.append('x')

    if r'\mathbf{{y}_{C}}' in tex:
        para.append('y')

    if r'\mathbf{{z}_{C}}' in tex:
        para.append('z')

    for s in obj.free_symbols:
        if s.name == 't':
            para.append('t')

    tex = tex.replace(r'\mathbf{{x}_{C}}', 'x')
    tex = tex.replace(r'\mathbf{{y}_{C}}', 'y')
    tex = tex.replace(r'\mathbf{{z}_{C}}', 'z')

    if lhs is not None:
        lhs = varNameAsLatex(lhs, skipDollar=True)

        if len(para) > 0:
            tex = tex[0:2] + f'{lhs}({",".join(para)}) = ' + tex[2:]
        else:
            tex = tex[0:2] + f'{lhs} = ' + tex[2:]

    if mode == 'inline':
        tex = tex.replace('frac', 'dfrac')

    return tex


def asString(obj, lhs=None):
    """Convert sympy obj into str.

    TODO
    ----
        Find better name

    """
    para = []

    # pg._g(obj)
    # pg._y(obj.free_symbols)

    #if 't' in obj.free_symbols:
    #pg._b('t' in obj.free_symbols)

    tex = str(obj)
    if 'C.x' in tex:
        para.append('x')

    if 'C.y' in tex:
        para.append('y')

    if 'C.z' in tex:
        para.append('z')

    for s in obj.free_symbols:
        if s.name == 't':
            para.append('t')

    tex = tex.replace('C.x', 'x')
    tex = tex.replace('C.y', 'y')
    tex = tex.replace('C.z', 'z')

    if lhs is not None:
        if len(para) > 0:
            tex = f'{lhs}({",".join(para)}) = ' + tex[:]
        else:
            tex = f'{lhs} = ' + tex[:]

    for c in ['x', 'y', 'z']:
        tex = tex.replace(f'{c}**2', f'{c}²')
        tex = tex.replace(f'{c}**3', f'{c}³')

    return tex


def _disables_array_ufunc(obj):
    """To allow reverse op for numpy ndarray."""
    try:
        return obj.__array_ufunc__ is None
    except AttributeError:
        return False


def dumpSP(expr):
    """For debugging: dump infos to sympy expression."""
    import sympy as sp
    pg._b('+'*50)
    pg._g(expr)
    pg._g(type(expr))

    if hasattr(expr, 'components'):
        pg._y('components', expr.components)

    print('isMatrix', isinstance(expr, sp.matrices.MatrixBase))
    pg._y('free symbols:', expr.free_symbols)
    pg._y('atoms:', expr.atoms(sp.Symbol))
    pg._b('-'*50)


def call(func, p, entity=None, **kwargs):
    """Evaluate function values for a positions inside an entity."""
    # pg._b(id(func), type(func), func, p, entity, kwargs,
    #      'lambdified:', hasattr(func, 'hasLambdified'))

    if hasattr(func, 'hasLambdified'):
        #pg._b(func, hasattr(func, 'hasLambdified'), p, kwargs)
        return func(p, **kwargs)

    # lot of tests fail with this
    # if hasattr(func, '_func'):# and 'elementMap' not in kwargs:
    #     # dont call FEAFunction() when meant FEAFunction.func()
    #     func = func._func

    # TODO
    # val = None ## failed tests with this
    try:
        ### For lambda functions
        #pg._g(p)
        val = func(p)
        #pg._g(val)
    except BaseException as e:
        #pg._g(e, entity)
        try:
            #pg._y(p, entity, kwargs)
            val = func(p, entity, **kwargs)
            #pg._y(val)
        except BaseException as e:
            #pg._y(e)
            try:
                #pg._r()
                val = func(p, **kwargs)
                #pg._r(val)
            except BaseException as e:
                #pg._r(e)
                # print('p:',p)
                # print('entity', entity)
                # print('kwargs', kwargs)
                #print(val)
                #pg.critical("Don't know how to evaluate function:", func)
                # test and check which val is this!!!!
                #python test_01_assembling.py TestFEAEval.test_FEAFunction_call
                #pg._b(val)
                return val
    #pg._b(val)
    return val


def quadratureRules(ent, order:int, show:bool=False, **kwargs):
    """Quadrature rules for mesh entity.

    Return quadrature points and weights for a mesh entity.
    The quadrature rules are in coordinates of the reference element shape.

    TODO
    ----
        * show with 3D
        * alternative quadrature rules, e.g., Gauss-Loboto

    Arguments
    ---------
    ent: pg.MeshEntity
        `pg.Boundary`, `pg.Cell`, or `pg.Shape` for the quadrature rules.

    order: int
        Quadrature rules of specific order.

    show: bool [False]
        Show quadrature points on the reference shape if ent if if type
        `pg.Shape` or being transformed to the cell itself.

    Keyword Args
    ------------
    **kwargs: **dict
         Forwarded to pg.show()

    Returns
    -------
    x: [[Pos],]
        Quadrature points.
    w: [float,]
        Quadrature weights.
    """
    isShape = False
    xL = ''
    yL = ''
    if isinstance(ent, pg.core.Shape):
        x = pg.core.IntegrationRules.instance().abscissa(ent, order)
        w = pg.core.IntegrationRules.instance().weights(ent, order)
        isShape = True
        xL = '$r$'
        yL = '$s$'
    elif hasattr(ent, 'type'):
        if 'T' in ent.type:
            x = pg.core.IntegrationRules.instance().triAbscissa(order)
            ## scale them here by two so we don't need to scale individual
            ## cell Jacobian determinants .. move it into the core!!
            w = pg.core.IntegrationRules.instance().triWeights(order)/2
        elif 'Q' in ent.type:
            x = pg.core.IntegrationRules.instance().quaAbscissa(order)
            ## scale them here by two so we don't need to scale individual
            ## cell Jacobian determinants .. move it into the core!!
            w = pg.core.IntegrationRules.instance().quaWeights(order)

    else:
        x = pg.core.IntegrationRules.instance().abscissa(ent.shape(), order)
        w = pg.core.IntegrationRules.instance().weights(ent.shape(), order)
        xL = '$x$ in m'
        yL = '$y$ in m'

    if show:
        pg.error("Don't us me .. use cell.show()")
        ax = kwargs.pop('ax', None)
        noAxe = True if ax is None else False

        m = pg.Mesh(ent.dim())
        nc = []
        for n in ent.nodes():
            if isShape:
                nc.append(m.createNode(ent.rst(n.pos())).id())
            else:
                nc.append(m.createNode(n.pos()).id())

        ax = pg.show(m, ax=ax)[0]
        c = m.createCell(nc)

        # draw node ids
        for i, n_ in enumerate(m.nodes()):
            p = n_.pos() + (n_.pos()-c.center())*0.08
            if isShape:
                ax.text(p[0], p[1], n_.id(), va='center', ha='center')
            else:
                ax.text(p[0], p[1], ent.node(i).id(), va='center', ha='center')

        # after first show, re-force createNeighborInfos
        m.createNeighborInfos(True)
        ax = pg.show(m, showMesh=True, xl=xL, yl=yL, ax=ax)[0]

        if noAxe:
            ax.margins(0.2)

        if ent.dim() < 3:
            if len(x) > 0:
                xXY = x
                if not isShape:
                    xXY = [ent.shape().xyz(_) for _ in x ]
                pg.show(xXY, ax=ax, color='b', s=12)
        else:
            pg.critical('implement me')

    return x, w


class FEFuncModelling(pg.frameworks.modelling.ParameterModelling):
    """Forward modelling operator to be able to fit FEAFunctions."""

    def __init__(self, func):
        super().__init__()
        self._func = func
        self._coef = self._func._func.coefficients
        self.regionManager().setParameterCount(len(self._coef.keys()))
        self.space = None

    def startModel(self):
        """Return a start model for the function coefficients."""
        return np.full(self.parameterCount, 1.0)

    def response(self, param):
        """Evaluate the function for the given parameters."""
        return self._func(self.space, **dict(zip(self._coef, param)))

    def subst(self, params):
        """Substitute the function coefficients."""
        return self._func(**dict(zip(self._coef, params)))


#@pg.cache
def fitShapeFunctions(func, dof):
    """Fit a function to be a shape functions.

    Automatic fitting of a function to the Kronecker property
    for some dof inside the unity range.
    Note, the numbers of coefficients need to fit the amount of dof.

    Tests for **Kronecker** and **Partition of Unity**
    property.

    Arguments
    ---------
    func: FeaFunction
        Function whish is supposed to be a shape function.
    dof: [[Pos],]
        Positions for the shape functions.

    Returns
    -------
    N_i: [FEAFunctions]
        A shape function for each dof.
    """
    from .solve import asFunction
    from .tests import assertEqual
    import sympy as sp

    if isinstance(func, str):
        func = asFunction(func)
    fop = FEFuncModelling(func)

    if np.asarray(dof).ndim == 1:
        fop.space = [[_x, 0] for _x in dof]
    else:
        fop.space = dof

    N = []
    for i, xi in enumerate(dof):
        data = np.zeros(len(dof))
        data[i] = 1.0
        inv = pg.core.RInversion(data, fop, False, False)
        inv.setRelativeError(0.0)
        inv.stopAtChi1(False)
        inv.setCGLSTolerance(1e-40)
        inv.setLambda(0)
        inv.setMaxIter(200)
        inv.run()
        Ni = fop.subst(inv.model()).round(42)
        Ni._name = f'N_{i}'

        try:
            assertEqual(Ni(fop.space), data, tol=1e-10)
        except AssertionError:
            print(Ni(fop.space), data)
            pg.error('Shape functions does not fulfil '
                     'Kronecker Delta Property')

        Ni.x = xi
        N.append(Ni)

    try:
        assertEqual(sum(N)(0), 1.0, tol=1e-12)
    except AssertionError:
        print(sum(N)(0))
        pg.error('Shape functions does not fulfil '
                     'Partition of unity property')

    return N


def vectorizeEvalQPnts(func, qPnts, **kwargs):
    """Vectorize evaluation quadrature points.

    Speedup for evaluation of function calls from
    quadrature points that are a list of pos lists `[[Pos,],]`.

    Arguments
    ---------
    func : callable
        Function to be evaluated. Should be able to evaluate `[Pos,]` or
        `np.ndarray((N,3))`.

    qPnts: pygimli.stdVectorR3Vector | [[Pos,],]
        Quadrature points, i.e., `[[Pos,],]`.

    Keyword Args
    ------------

    time : float | [float, ] | None
        Additional time parameter.

    t :
        Abbreviation for 'time'.

    rest :
        Forwarded to function call.

    Returns
    -------
    pygimli.stdVectorRVector or pygimli.stdVectorR3Vector
        Result from evaluating the callable in the same structure like
        qPnts, e.i., `[[float,],]` or `[[Pos,],]`.
    """
    if 't' in kwargs:
        kwargs['time'] = kwargs.pop('t')

    if 'time' in kwargs and hasattr(kwargs['time'], '__iter__'):
        times = kwargs.pop('time')
        return np.squeeze(np.asarray([
                vectorizeEvalQPnts(func, qPnts, time=t, **kwargs)
                    for t in times]))

    with pg.tictoc('eval.vec: f(vqp)'):
        vqp = pg.PosList()
        with pg.tictoc('qp->p'):
            pg.core.vectorizePosVectorList(qPnts, vqp)
        with pg.tictoc('call'):
            rf = func(vqp, **kwargs)
        with pg.tictoc('r->vr'):

            if pg.isScalar(rf[0]):
                ret = pg.core.stdVectorRVector()
                pg.core.deVectorizeRVectorToPosVectorList(ret, rf, qPnts)
                return ret
            elif pg.isPos(rf[0]):
                ret = pg.core.stdVectorR3Vector()

                count = 0
                for iq in qPnts:
                    ri = []
                    for j in range(len(iq)):
                        ri.append(rf[count])
                        count += 1
                    ret.append(ri)

                #pg.core.deVectorizeR3VectorToPosVectorList(ret, rf, qPnts)
                return ret
            else:
                ret = pg.core.stdVectorMatrixVector()

                count = 0
                for iq in qPnts:
                    ri = pg.core.stdVectorRMatrix()
                    for j in range(len(iq)):
                        ri.append(rf[count])
                        count += 1
                    ret.append(ri)

                return ret


def bulk(pS, pF, pG=0, phi=0, S=1):
    """Create bulk property for solid, fluid and gaseous phases.

    See :ref:`userGuide-thm-bulk`.

    Values can be scalars, arrays, functions or expressions.

    Arguments
    ---------
    pS: any
        Parameter for solid phase outside pores.
    pF: any
        Parameter for fluid phase inside pores.
    pG: any
        Parameter for gaseous phase inside pores.
    phi: any
        Porosity.
    S: any
        Saturation.

    Returns
    -------
    Value or expression depending on input parameter.
    """
    return pS * (1-phi) + phi* S*pF + phi*(1-S)*pG


def etaWater(T=10):
    r"""Dynamic viscosity of water.

    Return the dynamic viscosity :math:`\eta` of water in Pa s for
    a temperature :math:`T` in °C after the:
    `Vogel–Fulcher–Tammann equation <https://en.wikipedia.org/wiki/Vogel%E2%80%93Fulcher%E2%80%93Tammann_equation>`_:

    .. math::
        \eta(T) = \eta_0\operatorname{e}^{\frac{B}{T-T_{\rm VF}}}

    with :math:`\eta_0 = 0.02939` mP s, :math:`B = 507.88` K and
    :math:`T_{\rm VF} = 149.3` K.

    Arguments
    ---------
    T: any [10]
        Temperature in °C.

    Returns
    -------
    Value or expression depending on input parameter
        Dynamic viscosity for water :math:`\eta` in Pa s.

    Example
    -------
    >>> import numpy as np
    >>> import pygimli as pg
    >>> from oskar import *
    >>> ax = pg.show()[0]
    >>> T = np.linspace(0, 100, 21)
    >>> eta = etaWater(T)
    >>> ax.plot(T, 1000*eta, label='$\eta(T)$') # doctest: +ELLIPSIS
    [...
    >>> ax.set(xlabel='temperature in °C',
    ...        ylabel='dynamic viscosity in mPa s') # doctest: +ELLIPSIS
    [...
    >>> # Just a small test for function expressions.
    >>> # Create linear interpolator function for x [0..10]
    >>> mesh = pg.createGrid([0, 100])
    >>> s = ScalarSpace(mesh)
    >>> # Create a function T(x), e.g, a FEA solution for T(r)
    >>> Th = FEASolution(s, values=pg.x(mesh))
    >>> x = T
    >>> # Create the function for eta(t(x)) which accept coordinates
    >>> eta = etaWater(Th)
    >>> # which results in the same like:
    >>> # eta = Th.subst(etaWater)
    >>> ax.plot(x, 1000*eta(x), 'o', label='$\eta(T(x)(x))$') # doctest: +ELLIPSIS
    [...
    >>> ax.grid()
    >>> ax.legend() # doctest: +ELLIPSIS
    <...
    """
    eta0 = 0.02939e-3# Pa·s
    B = 507.88 # in K
    TVF = 149.3 # in K
    return eta0 * np.exp(B/(T + (273.15 -TVF)))


try:
    from scooby import Report as ScoobyReport

except ImportError:
    class ScoobyReport:
        """Local scooby reporting class."""

        def __init__(self, *args, **kwargs):
            """Do nothing."""
            pass

        def __str__(self):
            return self.__repr__()

        def __repr__(self):
            """Representation."""
            message = (
                "`Report` requires `scooby`. Install via `pip install scooby` "
                "or `conda install -c conda-forge scooby`."
            )
            return message

        def to_dict(self):
            """Dictionary representation (empty for now)."""
            return {}


class Report(ScoobyReport):
    r"""Report date, time, system, and package version information.

    Use ``scooby`` to report date, time, system, and package version
    information in any environment, either as html-table or as plain text.

    Parameters
    ----------
    additional : {package, str}, default: None
        Package or list of packages to add to output information (must be
        imported beforehand or provided as string).

    Example
    -------
    >>> import oskar
    >>> print(oskar.Report()) # doctest: +ELLIPSIS
    <BLANKLINE>
    ...
    """

    def __init__(self, additional=None, **kwargs):
        """Initialize a scooby. Report instance."""
        # Mandatory packages.
        core = ['oskar', 'pygimli', 'pgcore', 'numpy', 'matplotlib',
                'scipy', 'sympy']
        # Optional packages.
        optional = ['tqdm', 'IPython', 'meshio', 'tetgen', 'pyvista']
        inp = {
            'additional': additional,
            'core': core,
            'optional': optional,
            **kwargs  # User input overwrites defaults.
        }

        super().__init__(**inp)


#taken from jupyter-widgets documentation
class Timer:
    """Simple Timer for gui objects."""

    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = None

    async def _job(self):
        """Run timer."""
        import asyncio
        await asyncio.sleep(self._timeout)
        self._callback()

    def start(self):
        """Start timer."""
        import asyncio
        self._task = asyncio.ensure_future(self._job())

    def cancel(self):
        """Cancel the timer."""
        self._task.cancel()


#taken from jupyter-widgets documentation
def debounce(wait):
    """Debounce gui object.

    Decorator that will postpone a function's execution until after
    `wait` seconds have elapsed since the last time it was invoked.
    """
    def decorator(fn):
        timer = None
        def debounced(*args, **kwargs):
            nonlocal timer
            def call_it():
                fn(*args, **kwargs)
            if timer is not None:
                timer.cancel()
            timer = Timer(wait, call_it)
            timer.start()
        return debounced
    return decorator


#taken from jupyter-widgets documentation
def throttle(wait):
    """Throttle gui object.

    Decorator that prevents a function from being called
    more than once every wait period.
    """
    def decorator(fn):
        time_of_last_call = 0
        scheduled, timer = False, None
        new_args, new_kwargs = None, None
        def throttled(*args, **kwargs):
            nonlocal new_args, new_kwargs, time_of_last_call, scheduled, timer
            def call_it():
                nonlocal new_args, new_kwargs, time_of_last_call, scheduled, timer
                time_of_last_call = time()
                fn(*new_args, **new_kwargs)
                scheduled = False
            time_since_last_call = time() - time_of_last_call
            new_args, new_kwargs = args, kwargs
            if not scheduled:
                scheduled = True
                new_wait = max(0, wait - time_since_last_call)
                timer = Timer(new_wait, call_it)
                timer.start()
        return throttled
    return decorator


def setMPlDefault():
    """Set matplotlib default parameters for oskar.

    Don't set it on default until there is a lazy import of matplotlib.
    """
    from matplotlib import rcParams
    #import matplotlib as mpl
    rcParams["axes.facecolor"] = "#fffffa"


def figSize(size, landscape=True, cm=False):
    """Get the paper size in inches or centimeters.

    Arguments
    ---------
    size : str
        'a4', 'letter', 'legal'
    landscape : bool
        True or False
    cm : bool
        If True, return size in centimeters

    Returns
    -------
    tuple
        (width, height) in inches or centimeters

    """
    if size == 'a4':
        width = 11.69
        height = 8.27
    elif size == 'letter':
        width = 11
        height = 8.5
    elif size == 'legal':
        width = 14
        height = 8.5
    elif size == '16:9':
        width = 16
        height = 9
    elif size == '4:3':
        width = 4
        height = 3
    else:
        raise ValueError('Invalid paper size')

    if landscape:
        dimensions = np.array((width, height))
    else:
        dimensions = np.array((height, width))
    if cm:
        dimensions *= 2.54  # Convert inches to centimeters
    return dimensions


def drawBoundaryConditions(ax, mesh, bc, wallLength=0.05):
    """Draw boundary conditions.

    [Experimental]

    TODO
    ----
        * Add support for Dirichlet BCs with non-zero values
        * Add support for other boundary conditions
        * Add support for 3D meshes

    Example
    -------
    >>> import pygimli as pg
    >>> import oskar
    >>> mesh = pg.createGrid(10, 4)
    >>> bc = {'Dirichlet': {1: [0.0, 0.0, 0.0], 3: [0.0, 0.0, 0.0]}}
    >>> ax = mesh.show(markers=True, showMesh=True)[0]
    >>> oskar.utils.drawBoundaryConditions(ax, mesh, bc, wallLength=0.6)
    """
    import matplotlib as mpl

    def _findBoundary(bs, p):
        for b in bs:
            if b.shape().touch(p):
                return b
        pg.critical('No boundary found for point', p)

    for key, val in bc.items():
        if key == 'Dirichlet':
            for marker, values in val.items():
                if values == [0.0, 0.0, 0.0]:

                    markers = pg.solver.parseMarkersDictKey(marker,
                                                    mesh.boundaryMarkers())

                    for m in markers:
                        if m == 0:
                            continue
                        bs = mesh.findBoundaryByMarker(m)
                        paths = mesh.findPaths(bs)

                        for p in paths:
                            xs = pg.x(mesh.nodes(p))
                            ys = pg.y(mesh.nodes(p))
                            ax.plot(xs, ys, color='k', lw=1)

                            path = np.array([xs, ys]).T

                            pLen = pg.utils.cumDist(path)[-1]
                            pos = pg.meshtools.interpolateAlongCurve(path,
                                            np.linspace(0, pLen,
                                                        int(pLen/wallLength)))

                            segments = []
                            dPos = wallLength
                            rot = np.asarray([[np.cos(np.pi/4),
                                               -np.sin(np.pi/4)],
                                            [np.sin(np.pi/4),
                                             np.cos(np.pi/4)]])

                            for p in pos:
                                b = _findBoundary(bs, p)
                                n = np.asarray(b.shape().norm())[:2]
                                #p += n*dPos
                                pEnd = np.asarray(n*dPos + p)[:2]
                                segments.append([p, np.dot(pEnd-p, rot)+p])

                            lines = mpl.collections.LineCollection(segments,
                                                                   linewidths=1,
                                                                   color='k')
                            ax.add_collection(lines)

                            #print(p)

                else:
                    pg.warning('Only Dirichlet [0.0, 0.0, 0.0] supported')

            ax.autoscale_view()
            ax.margins(x=0.02, y=0.02)


def showVectorField(v, mesh=None, **kwargs):
    """Show solutions.

    Arguments
    ---------
    v: np.ndarray | FEASolution | FEAFunction3
        Finite element solution or appropriate Function.

    mesh: Mesh
        Mesh to show the solution on. If not set, the mesh of the
        solution is used.

    Keyword Args
    ------------
    noAbs: bool [False]
        If set, draw only arrows or streamlines for vector functions.

    label: str [u.name]
        Label for the color bar.

    quiverPos: [[Pos],] | None
        Positions to draw quiver arrows. If None, streamlines are drawn.

    u: FEASolution | FEAFunction3
        Function to get the vector values for quiverPos. Default: v

    kwargs: dict
        Forwarded to pg.show()
    """
    u = kwargs.pop('u', v) ## just in case we need more points for quivers

    if mesh is None:
        mesh = u.mesh

    v_ = v if isinstance(v, np.ndarray) else u(mesh)
    noAbs = kwargs.pop('noAbs', False)
    label = kwargs.pop('label', 'v')
    quiverPos = kwargs.pop('quiver', None)

    if not noAbs:
        # ax, cBar = pg.show(mesh, pg.abs(v_),
        #                   label=f'|{label}|', **kwargs)
        ax, cBar = pg.show(mesh, pg.abs(v_), label=f'|{label}|',
                            ax=kwargs.pop('ax', None),
                            **kwargs)

        label = 'direction'
    else:
        ax = kwargs.pop('ax', None)
        cBar = None

    if mesh.dim() == 2:
        if quiverPos is not None:
            tol = kwargs.pop('tol', 0.0)

            uv = u(quiverPos)
            sID = np.where(abs(uv) > tol)[0]
            pos = quiverPos[sID]

            XY = pos[:,0:2]
            ax.scatter(XY[:,0], XY[:,1], color='k', s=3)
            UV = uv[sID][:,0:2]
            q = ax.quiver(XY[:,0], XY[:,1], UV[:,0], UV[:,1], pivot='mid')
            ax.quiverkey(q, 0.05, -0.1, 0.1, r'direction', labelpos='E',
                            coordinates='axes')
            return ax, cBar
        else:
            ax = pg.show(mesh, v_, ax=ax, **kwargs)[0]

            if cBar is None and hasattr(ax, '__cBar__'):
                cBar = ax.__cBar__

            if cBar is not None:
                q = cBar.ax.quiver(0.0, 1.35, 0.04, 0.0, pivot='tail',
                                    width=0.0025, scale=1.0,
                                    headwidth=4, headlength=4,
                                    headaxislength=3,
                                    color='k', transform=cBar.ax.transAxes)
                q.set_clip_on(False)

                q = cBar.ax.text(0.05, 1.0, label,
                                horizontalalignment='left',
                                verticalalignment='bottom',
                                transform=cBar.ax.transAxes)
            return ax, cBar
    else:
        ## mesh.dim() == 3 | ## mesh.dim() == 1
        return ax, cBar
