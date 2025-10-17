#!/usr/bin/env python
r"""Utility functions for oskar.tests."""
import os
import sys
from os.path import join, realpath

import unittest
import warnings

import numpy as np
import pygimli as pg

import oskar as oc


def testCount():
    """Return number of performed tests per session."""
    return oc.Globals.testCounter


def incTestCounter():
    """Increment test counter."""
    oc.Globals.testCounter += 1


def listTests(filename=None, pre=''):
    """List all tests in the given file."""
    import os
    def _showSuite(s):
        if hasattr(s, '__iter__'):
            for _s in s:
                _showSuite(_s)
        else:
            fbase = os.path.splitext(os.path.basename(filename))[0]
            if fbase in s.id():
                print(pre, '.'.join(s.id().split('.')[1:]))

    _showSuite(unittest.defaultTestLoader.discover('.', pattern='test_*.py'))


def parseTestArgs():
    """Parse command line arguments for test script."""
    import sys
    if 'help' in sys.argv or '-h' in sys.argv:
        print(f'Usage: python {sys.argv[0]} test [show|-s]\n')
        print('Available tests:')
        listTests(sys.argv[0], '\t')
        sys.exit()

    _show_ = False

    if 'show' in sys.argv:
        sys.argv.remove('show')
        _show_ = True

    if '-s' in sys.argv:
        sys.argv.remove('-s')
        _show_ = True

    return _show_


def assertEqual(a, b, **kwargs):
    """Assure two things are equal, or almost equal.

    Syntactic sugar to numpy testing.
    Increases an internal test counter.

    Arguments
    ---------
    a: any
        Any supported type. See examples.
    b: any
        Any supported type. See examples.

    Keyword Arguments
    -----------------
    atol: float
        Absolute tolerance.
    rtol: float
        Relative tolerance.
    tol: float
        Same like absolute tolerance.

    Examples
    --------
    >>> import pygimli as pg
    >>> from oskar.tests import assertEqual
    >>> # None of the following should throw AssertionError
    >>> assertEqual(None, None)
    >>> assertEqual(pg.Vector(10, 1.0), pg.Vector(10, 1.0))
    >>> try:
    ...     assertEqual(pg.Vector(10, 1.0), pg.Vector(10, 1.0)+1e-6)
    ... except AssertionError:
    ...     print('Default test fails.')
    ...     assertEqual(pg.Vector(10, 1.0), pg.Vector(10, 1.0)+1e-6, atol=1e-6)
    Default test fails.
    >>> assertEqual(pg.Vector(10, 1.0), pg.Vector(10, 1.0)*(1+1e-6), rtol=1e-6)
    >>> print(oc.tests.testCount()) # doctest: +SKIP
    """
    #pg._b(f'{type(a)}: {a}, {type(b)}: {b}')
    ### Forward list of tests
    if isinstance(a, list | tuple) and isinstance(b, list | tuple) and \
        len(a) == len(b):

        for i, ai in enumerate(a):
            assertEqual(ai, b[i], **kwargs)
        return

    ### Test explicit cases first
    if a is None:
        if a is not b:
            raise AssertionError(f"{a} is not {b}")
        incTestCounter()
        return

    ### a and b are OP expressions but no FEASolutions
    if hasattr(a, 'op') and hasattr(b, 'op') \
        and (not hasattr(a, 'values') and not hasattr(b, 'values')):
        #pg._g(a, b)

        assertEqual(str(a), str(b))
        return

    ### Test explicit cases first
    if isinstance(a, pg.core.stdVectorMatrixVector| \
                     pg.core.stdVectorMatrixVector):
        for i, ai in enumerate(a):
            assertEqual(ai, b[i])
        return

    if isinstance(a, pg.core.stdVectorRMatrix | \
                     pg.core.stdVectorRMatrix):
        for i, ai in enumerate(a):
            assertEqual(ai, b[i])
        return

    if isinstance(a, pg.core.stdVectorR3Vector | \
                     pg.core.stdVectorRVector):
        for i, ai in enumerate(a):
            assertEqual(ai, b[i])
        return

    if pg.isScalar(a) and pg.isScalar(b):
        if 'tol' in kwargs:
            if abs(a-b) > kwargs['tol']:
                raise AssertionError(f'|{a}-{b}|={abs(a-b)}'
                                     f' > {kwargs["tol"]}')

        elif 'atol' in kwargs:
            if abs(a-b) > kwargs['atol']:
                raise AssertionError(f'|{a}-{b}|={abs(a-b)}'
                                     f' > {kwargs["atol"]}')

        elif 'rtol' in kwargs:
            if abs(1-a/b) > kwargs['rtol']:
                raise AssertionError(f'|1-{a}/{b}|='
                                     f'{abs(1-a/b)} > {kwargs["rtol"]}')

        else:
            if abs(a-b) > 0:
                raise AssertionError(f'|{a}-{b}|={abs(a-b)}'
                                     f' > {0}')

        incTestCounter()
        return

    if isinstance(a, str) and isinstance(b, str):
        incTestCounter()
        if a != b:
            raise AssertionError(f'"{a}" != "{b}"')
        return

    if isinstance(a, pg.core.SparseMatrixBase):
        rA, cA, vA = pg.matrix.sparseMatrix2Array(a, indices=True,getInCRS=True)
        rB, cB, vB = pg.matrix.sparseMatrix2Array(b, indices=True,getInCRS=True)
        assertEqual(rA, rB)
        assertEqual(cA, cB)
        assertEqual(vA, vB, **kwargs)
        incTestCounter()
        return

    elif isinstance(a, pg.core.SparseMatrixBase | pg.core.ElementMatrix):
        np.testing.assert_equal(a == b, True)
        incTestCounter()
        return


    ### Test generic type
    if hasattr(a, 'values') and callable(a.values):
        a = a.values()
    elif hasattr(a, 'values'):
        a = a.values

    if hasattr(b, 'values') and callable(b.values):
        b = b.values()
    elif hasattr(b, 'values'):
        b = b.values

    if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        # pg._g(a.ndim, a.shape)
        # pg._y(b.ndim, b.shape)
        if a.ndim != b.ndim:
            a = np.squeeze(a)
            b = np.squeeze(b)
        assertEqual(a.shape, b.shape)
    else:
        pass
        # pg._g(type(a), a.ndim, a.shape)
        # pg._g(a)
        # pg._y(type(b), b.ndim, b.shape)
        # pg._y(b)

    #pg._g(np.linalg.norm(a), np.linalg.norm(b), np.linalg.norm(a-b))

    # elif hasattr(a, 'expr') and hasattr(b, 'expr'):
    #     # pg._b(a)
    #     # pg._b(b)
    #     np.testing.assert_equal(str(a)==str(b), True)

    if 'tol' in kwargs:
        np.testing.assert_allclose(a, b, atol=kwargs['tol'])
        return
    elif 'atol' in kwargs:
        np.testing.assert_allclose(a, b, atol=kwargs['atol'], rtol=0)
        return
    elif 'rtol' in kwargs:
        np.testing.assert_allclose(a, b, rtol=kwargs['rtol'], atol=0)
        return
    elif hasattr(a, '__iter__') and hasattr(b, '__iter__'):
        np.testing.assert_allclose(a, b, atol=1e-12,
                                         rtol=1e-12)
        return
    else:
        #pg._g(3)
        np.testing.assert_equal(a, b)
        #return

    # pg._b(f'{type(a)}: {a}, {type(b)}: {b}')
    incTestCounter()
    #assertEqual(type(a),type(b))


class TestCollection(unittest.TestCase):
    """Base class to collect some tests.

    This is just a wrapper to overwrite default api doc from
    unittest.TestCase.__init__.
    """

    def __init__(self, methodName: str="runTest") -> None:
        """Initialize test collection without special setup."""
        super().__init__(methodName)
        # keep the linter from complaining W0246:useless-super-delegation
        self._dummy = 0


    def assertEqual(self, first, second, msg=None, **kwargs):
        """Assert two thing equal. Increase test counter."""
        try:
            return assertEqual(first, second, **kwargs)
        except np.exceptions.DTypePromotionError:
            incTestCounter()
            #pg._y(1)
            return super().assertEqual(first, second, msg)

        pg.critical('here?')


    def assertTrue(self, cond):
        """Assert True if conditional.

        Increase test counter.
        """
        incTestCounter()
        return super().assertTrue(cond)


# def testSolve(L, **kwargs):
#     ref = kwargs.pop('ref', None)
#     atol = kwargs.pop('atol', 1e-14)
#     #skipHistory to create new FEASolution for each test
#     ret = solve(L, **kwargs, skipHistory=True, core=False)

#     if ref is not None:
#         try:
#             testEqual(ret, ref, atol=atol)
#         except Exception as e:
#             pg._r('#'*20, "core=False (compare to ref)")
#             pg._y(L)
#             print(kwargs)
#             print(e)
#             print('#'*20)
#             pg.critical('Test fail')
#     else:
#         ref = ret

#     ## core
#     ret = solve(L, **kwargs, skipHistory=True, core=True)
#     try:
#         testEqual(ret, ref, atol=atol)
#     except Exception as e:
#         pg._r('#'*20, "core=True (compare to core=False)")
#         pg._y(L)
#         print(e)
#         print(kwargs)
#         print('#'*20)
#         pg.critical('Test fail')

#     ## usemats
#     #pg.core.setDeepDebug(-1)
#     ret = solve(L, **kwargs, skipHistory=True, useMats=True)
#     #pg.core.setDeepDebug(0)
#     try:
#         testEqual(ret, ref, atol=atol)
#     except Exception as e:
#         pg._r('#'*20, "useMats=True  (compare to core=True)")
#         pg._y(L)
#         print(e)
#         print(kwargs)
#         print('#'*20)
#         print(f'ret:{ret.values}')
#         print(f'ref:{ref.values}')
#         pg.critical('Test fail')

#     return ret


# lend from pygimli
def test(target=None, show=False, onlydoctests=False, coverage=False,
         htmlreport=False, n:int=1, abort=False, verbose=True):
    """Run docstring examples and additional tests.

    Parameters
    ----------
    target : function or string or pattern (-k flag in pytest), optional
        Function or method to test. By default everything is tested.
    show : boolean, optional
        Show viewer windows during test run. They will be closed
        automatically.
    onlydoctests : boolean, optional
        Run test files in testing as well.
    abort : boolean, optional
        Return correct exit code, e.g. abort documentation build when a test
        fails.
    coverage : boolean, optional
        Create a coverage report. Requires the pytest-cov plugin.
    htmlreport : str, optional
        Filename for HTML report such as www.pygimli.org/build_tests.html.
        Requires pytest-html plugin.
    n: int [1]
        Number of workers for parallel execution. Needs `pytest-xdist` installed.

    Examples
    --------
    >>> import oskar as oc
    >>> # Run the whole test suite.
    >>> oc.test() # doctest: +SKIP
    >>> # Test a single function by a string.
    >>> oc.test("utils.Report", verbose=False) # doctest: +SKIP
    >>> # The target argument can also be the function directly
    >>> from oskar.utils import Report
    >>> oc.test(Report, verbose=False) # doctest: +SKIP
    """
    pytest = pg.optImport('pytest', "pytest is required to run test suite. "
                          "Try 'pip install pytest'.")

    # Remove figure warnings
    np.random.seed(1337)
    plt = pg.plt
    plt.rcParams["figure.max_open_warning"] = 1000
    warnings.filterwarnings("ignore", category=UserWarning,
                            message='Matplotlib is currently using agg, a '
                                    'non-GUI backend, so cannot show figure.')

    printopt = np.get_printoptions()

    old_backend = plt.get_backend()
    # pg._r(old_backend, show)
    if not show:
        plt.switch_backend("Agg")
    else:
        plt.ion()

    cwd = join(realpath(oc.__path__[0]))

    excluded = ['testCount',]

    if onlydoctests:
        excluded.append("tests")

    cmd = (["--color", "yes", "--doctest-modules", "-p", "no:warnings"])

    string = f"oskar {oc.__version__}"

    target_source = False
    if target:
        if not isinstance(target, str):
            import inspect
            target_source = inspect.getsourcefile(target)
            target = target.__name__
        else:
            target = target.replace("oc.", "")
            target = target.replace("oskar.", "")

        cmd.extend(["-k", target, "--no-header", "--doctest-report", "udiff"])
        if not verbose:
            cmd.extend(["-qq", "-rN"])

        if show:  # Keep figure opened if single function is tested
            plt.ioff()

        string = f"'{target}' from {string}"

    if verbose:
        cmd.extend(["-v", "--durations", "15"])
        pg.boxprint(f"Testing {string}", sym="+", width=90)
        print(pg.versionStr(), pg.__version__, pg.__path__)

    if coverage:
        pc = pg.optImport("pytest_cov", "create a code coverage report")
        if pc:
            ocpath = os.path.dirname(oc.__file__)
            pg.info(f'Collecting coverage for {ocpath}')
            cmd.extend(["--cov", ocpath])

            covcfg = os.path.abspath(ocpath + '/../.coveragerc' )
            if os.path.exists(covcfg):
                pg.info(f'Coverage cfgfile: {covcfg}')
                cmd.extend(["--cov-config", covcfg])

            # show coverage in log file
            cmd.extend(["--cov-report", "term"])
            # for coverage badges
            cmd.extend(["--cov-report", "xml:cobertura.xml"])
            # for number of tests as badge
            cmd.extend(["--junit-xml", "TEST-unittest.xml"])
            #cmd.extend(["--cov-report", "json:TEST-coverage.json"])

    if htmlreport:
        ph = pg.optImport("pytest_html", "create a html report")
        if ph:
            cmd.extend(["--html", htmlreport])

    for directory in excluded:
        cmd.extend(["--ignore", join(cwd, directory)])

    if n > 1:
        cmd.extend([f"-n {n}"])

    plt.close("all")
    if target_source:
        cmd.extend([target_source])
    else:
        cmd.extend([cwd])

    #pg._b(cmd)
    exitcode = pytest.main(cmd)

    plt.switch_backend(old_backend)
    np.set_printoptions(**printopt)

    if not abort:
        if verbose:
            print("Exiting with exitcode", exitcode)
        sys.exit(exitcode)


def compSolve(L, **kwargs):
    """Test and compare different solver variants.

    Run test and compare different solver variant, i.e.,
    core=True|False and useMats=True
    """
    ref = kwargs.pop('ref', None)
    atol = kwargs.pop('atol', 1e-14)

    #skipHistory to create new FEASolution for each test
    ret = oc.solve(L, **kwargs, skipHistory=True, core=False)

    if ref is not None:
        try:
            assertEqual(ret, ref, atol=atol)
        except Exception as e:
            pg._r('#'*20, "core=False (compare to ref)")
            pg._y(L)
            print(kwargs)
            print(e)
            print('#'*20)
            pg.critical('Test fail')
    else:
        ref = ret
    print('.', end='', flush=True)

    ## core
    ret = oc.solve(L, **kwargs, skipHistory=True, core=True)
    try:
        assertEqual(ret, ref, atol=atol)
    except Exception as e:
        pg._r('#'*20, "core=True (compare to core=False)")
        pg._y(L)
        print(e)
        print(kwargs)
        print('#'*20)
        pg.critical('Test fail')

    print('.', end='', flush=True)
    ## usemats
    #pg._g('#####################################', L)
    ret = oc.solve(L, **kwargs, useMats=True)

    try:
        assertEqual(ret, ref, atol=atol)
    except Exception as e:
        pg._r('#'*20, "useMats=True  (compare to core=True)")
        pg._y(L)
        print(e)
        print(kwargs)
        print('#'*20)
        print(f'ret:{ret.values}')
        print(f'ref:{ref.values}')
        pg.critical('Test fail')

    print('.', end='', flush=True)
    return ret


def _assemble(L, **kwargs):
    """Short test and show of assembling of."""
    A1 = L.assemble(core=False, **kwargs)
    pg._g(A1)
    A2 = L.assemble(core=True, **kwargs)
    pg._y(A2)
    A3 = L.assemble(useMats=True, **kwargs)
    pg._r(A3)


def _testExp(L, L2=None, ref=None, useMats=True, **kwargs):
    """Test assembling of expression L with different strategies."""
    atol = kwargs.pop('atol', 1e-12)
    if isinstance(L, list):
        return _testExp(L[0], L[1], **kwargs)
    try:
        A1 = L.assemble(core=False, **kwargs)
        # pg._g(A1)
        A2 = L.assemble(core=True, **kwargs)
        # pg._y(A2)
        assertEqual(A1, A2, atol=atol)

        if useMats:
            A3 = L.assemble(useMats=True, **kwargs)
            # pg._r(A3)
            assertEqual(A1, A3, atol=atol)

        if L2 is not None:
            # pg._b(L2)
            B1 = L2.assemble(useMats=True, **kwargs)
            #pg._b(B1)
            assertEqual(A1, B1, atol=atol)

        if ref is not None:
            if isinstance(ref, oc.OP):
                ref = ref.assemble(useMats=True)
            assertEqual(A1, ref, atol=atol)

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout)
        pg._y('test Expr:', L)
        pg.critical(e)

    return A1

