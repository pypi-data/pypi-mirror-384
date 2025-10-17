#!/usr/bin/env python
"""Test PDE expression parsing.

Also tests for string parsing into FEAFunctions using sympy.
"""
import sys
import numpy as np
import pygimli as pg

from oskar.utils import asPosListNP, etaWater
from oskar.solve import splitDeriveTime, splitTransientLeftRight
from oskar import (FEAFunction, FEAFunction3, FEASolution, ScalarSpace,
                   ConstantSpace, ScalarSpace, VectorSpace,
                   Div, PDE, Laplace, I,
                   derive, dirac, div, grad, integrate, laplace,
                   normL2, parse, solve, sym,
                   asFunction, tr, trace,
                   )

from oskar.tests.utils import testCount, TestCollection, _testExp
from oskar.feaOp import findForms
from oskar.mathOp import isStrongFormPDE
from oskar.elasticity import createElasticityMatrix
from oskar.units import ParameterDict


def vacStr(s):
    """Remove spaces from expression string (Helper).

    Remove spaces from expression string representation to be comparable.
    """
    return ''.join(str(s).split())


class TestParsing(TestCollection):
    """Test function generator based on sympy expressions."""

    def test_parse_str(self):
        """Parse string to FEAFunction and string representation."""
        #### START DEBUG WORKSPACE ############################################

        # f, r = parse(f='r', r='sqrt(x²+y²)')
        #pprint(f)
        # print(f)

        #exit()
        #### END DEBUG WORKSPACE ##############################################
        f = parse(f='x')
        self.assertEqual(vacStr(f._repr_str_()), vacStr('f(x) = x'))

        f, r = parse(f='r', r='x')
        self.assertEqual(vacStr(f._repr_str_()), vacStr('f(x) = x'))

        f, r = parse(f='r*t', r='x')
        self.assertEqual(vacStr(f._repr_str_()), vacStr('f(x,t) = x*t'))

        f = parse(f='x+y')
        self.assertEqual(vacStr(f._repr_str_()), vacStr('f(x,y) = x + y'))

        f, r = parse(f='r', r='sqrt(x²+y²)')
        self.assertEqual(vacStr(f._repr_str_()), vacStr('f(x,y)=sqrt(x² + y²)'))

        f, r = parse(f='r*t', r='x')
        self.assertEqual(vacStr(f._repr_str_()), vacStr('f(x,t) = x*t'))


    def test_parse(self):
        """Parse string to FEAFunction and check lazy evaluation."""
        x = np.linspace(-1, 1, 5)
        m1 = pg.createGrid(x)
        m2 = pg.createGrid(x, x)
        m3 = pg.createGrid(x, x, x)

        #### START DEBUG WORKSPACE ############################################
        # f = parse(f='1, sin(y)')

        # self.assertEqual(isinstance(f, FEAFunction3), True)
        # self.assertEqual(f([0.0, 0.0]), [1, .0])
        # self.assertEqual(f([[0.0, 1.0]]*10), [[1, np.sin(1)]]*10)

        # exit()
        #### END DEBUG WORKSPACE ##############################################

        a, f = parse(a=1, f=2.2)
        self.assertEqual(a, 1)
        self.assertEqual(f, 2.2)

        ## pure 1D in R1
        f, df = parse(f='x', df='diff(f, x)')
        self.assertEqual(f(x), x)
        self.assertEqual(df(x), 1)
        self.assertEqual(f(m1), x)
        self.assertEqual(df(m1), 1)

        ## 1D in R1 but grad is 3d result
        f, df = parse(f='x²', df='grad(f)')
        self.assertEqual(f(x), x*x)
        self.assertEqual(df(m1), [[2*p[0], 0.0] for p in m1.positions()])
        self.assertEqual(df(x), [[2*x_, 0.0] for x_ in x])

        ## 2D in R1 but grad is 3d result
        f, df = parse(f='x²+y²', df='grad(f)')
        self.assertEqual(f(m2), pg.x(m2)**2 + pg.y(m2)**2)
        self.assertEqual(f([1.0, 2.0]), 1 + 4)
        self.assertEqual(df(m2), [[2*p[0], 2*p[1]] for p in m2.positions()])
        self.assertEqual(df([1.0, 2.0]), [2.0, 4.0])
        self.assertEqual(df([[1.0, 2.0], [2.0, 1.0]]), [[2.0, 4.0], [4.0, 2.0]])

        ## 1D in R3 and grad is matrix
        f, df = parse(f='x, y', df='div(f)')
        self.assertEqual(isinstance(f, FEAFunction3), True)
        self.assertEqual(df([3.14, -42.0]), 2)
        self.assertEqual(div(f)([3.14, -42.0]), 2)

        f, df = parse(f='(x, y)', df='div(f)')
        self.assertEqual(isinstance(f, FEAFunction3), True)
        self.assertEqual(df([3.14, -42.0]), 2)
        self.assertEqual(div(f)([3.14, -42.0]), 2)

        f, df = parse(f='[x, y]', df='div(f)')
        self.assertEqual(isinstance(f, FEAFunction3), True)
        self.assertEqual(df([3.14, -42.0]), 2)
        self.assertEqual(div(f)([3.14, -42.0]), 2)

        f = parse(f='[1, sin(y)]')
        self.assertEqual(isinstance(f, FEAFunction3), True)
        self.assertEqual(f([0.0, 0.0]), [1, .0])
        self.assertEqual(f([[0.0, 1.0]]*10), [[1, np.sin(1)]]*10)

        f = parse(f='[1, 0]')
        self.assertEqual(isinstance(f, FEAFunction3), True)
        self.assertEqual(f([0.0, 0.0]), [1, .0])
        self.assertEqual(f([[0.0, 1.0]]*10), [[1, 0]]*10)

        f, gf = parse(f='(-y*x, x**2)', gf='grad(f)')
        self.assertEqual(f([1.0, 2.0]), [-2.0, 1.0])
        self.assertEqual(f([[1.0, 2.0], [2.0, 1.0]]),
                         [[-2.0, 1.0], [-2.0, 4.0]])
        self.assertEqual(gf([1.0, 2.0]), [[-2.0, -1.0], [2.0, 0.0]])

        f, gf = parse(f='(x² + x*y + y², x² - x*y - y² )', gf='grad(f)')
        self.assertEqual(gf([1.0, 0.0]), [[2.0, 1.0], [2.0, -1.0]])

        f, gf = parse(f='(x² + x*y + y², x² - x*y - y², 0)', gf='grad(f)')
        self.assertEqual(grad(f,keepDim=True)([1.0, 0.0]),
                         [[2.0, 1.0, 0.0], [2.0, -1.0, 0.0], [0,0,0]])

        f, gf = parse(f='(x² + x*y + y², x² - x*y - y²)', gf='sym(grad(f))')
        self.assertEqual(gf([1.0, 1.0]), [[3.0, 2.0], [2.0, -3.0]])
        self.assertEqual(sym(grad(f))([1.0, 1.0]), [[3.0, 2.0], [2.0, -3.0]])

        f, gf = parse(f='(x² + x*y + y², x² - x*y - y², 0)', gf='sym(grad(f))')
        self.assertEqual(gf([1.0, 1.0]),
                         [[3.0, 2.0, 0.0], [2.0, -3.0, 0.0],[0.0, 0.0, 0.0]])
        self.assertEqual(sym(grad(f))([1.0, 1.0]),
                         [[3.0, 2.0, 0.0], [2.0, -3.0, 0.0], [0,0,0]])

        f, df, ddf, gdf = parse(f='(x²*-(y²))', df='grad(f)',
                                ddf='div(df)', gdf='grad(df)')

        x = 3
        y = 4
        self.assertEqual(  f([x, y]), -x**2 * y**2)
        self.assertEqual( df([x, y]), [-2*x * y**2, -x**2 * 2*y])
        self.assertEqual(ddf([x, y]), -2*y**2    + -x**2 * 2)
        self.assertEqual(gdf([x, y]),
                         [[-2*y**2, -2*x*2*y],[ -2*x*2*y, -x**2 * 2]])

        self.assertEqual(  f(m2),
                         [-p.x()**2 * p.y()**2 for p in m2.positions()])
        self.assertEqual( df(m2),
                         [[-2*p.x() * p.y()**2,
                           -p.x()**2 * 2*p.y()] for p in m2.positions()])
        self.assertEqual(ddf(m2),
                         [-2*p.y()**2 + -p.x()**2*2 for p in m2.positions()])
        self.assertEqual(gdf(m2),
                         [[[-2*p.y()**2,    -2*p.x()*2*p.y()],
                [-2*p.x()*2*p.y(), -p.x()**2 * 2]] for p in m2.positions()])

        ## separate test for rot-ish field cannot be grad(u)
        uF, df = parse(u='(x² + x*y + y², x² - x*y - y²)', df='grad(u)')
        p = [1, 1, 1, 1]
        a1 = np.squeeze([df(p_) for p_ in asPosListNP(p)])
        a2 = grad(uF)(p)
        self.assertEqual(a1, a2)

        #### START DEBUG WORKSPACE ############################################
        # f, df, ddf = parse(f='x*t', df='grad(f)', ddf='grad(df)')
        # f, df, ddf = parse(f='x²*t', df='grad(f)', ddf='grad(df)')
        # f, df, ddf = parse(f='(x²+y²)*t', df='grad(f)', ddf='grad(df)')
        # f, df, ddf = parse(f='((x² + y²)*z²)*t', df='grad(f)', ddf='grad(df)')
        # f, df, ddf = parse(f='((x³ + y³)*z³)*t', df='grad(f)', ddf='grad(df)')
        # f, df, ddf = parse(f='sin(x)*cos(y)', df='grad(f)', ddf='grad(df)')

        # # p = 0.3
        # p = 1
        # #p = [1, 1, 1]
        # #p = [[1,1], [1,1]]
        # #p = [[1,1,1]]*2
        # #p = [[1,1,1]]*3
        # #p = [[1,1,1]]*4
        # #p = [[0.1, 0.0, 0.0]]*3

        t = [1.]
        # t = [1, 2]
        # # t = [1., 2., 3., 4.]
        # # t = np.linspace(0, 10, 5)
        # #t = [1., 2., 3.]


        # print('*'*40, 'pnts:', asPosListNP(p))
        # print('*'*40, 't:', t)

        # print('*** grad')
        # print(df)
        # print(grad(f))
        # a1 = np.squeeze([[df(p_, time=t_)
        #       for p_ in asPosListNP(p)] for t_ in t])
        # pg._g(a1)

        # a2 = df(p, time=t)
        # pg._y(a2)

        # self.assertEqual(a1, a2)

        # a3 = grad(f)(p, time=t)
        # self.assertEqual(a1, a3)

        # s = ScalarSpace(pg.createGrid(2,3)); eMat = s.uMat()
        # p = eMat.quadraturePoints()
        # pg._b(p)
        # print('*** grad(grad)')
        # print(ddf)
        # print(grad(df))
        # print(grad(grad(f)))
        # b1 = np.squeeze([[ddf(p_, time=t_)
        #       for p_ in p] for t_ in t])
        # pg._g(b1)

        # b2 = ddf(p)
        # pg._y(b2)

        # print(b2[0][0])
        # print(b2[0][0]*0.1)
        # #b1[0][0] = b2[0][0]*0.1

        # print(b2[0][0])

        # self.assertEqual(b1, b2)


        # b2 = ddf(p, time=t)
        # pg._y(b2)

        # b3 = grad(grad(f))(p, time=t)
        # pg._y(b3)

        # self.assertEqual(b1, b2)
        # self.assertEqual(b1, b3)

        # self.assertEqual(df(p, time=t), a1)
        # self.assertEqual(grad(f)(p, time=t), a1)
        # self.assertEqual(ddf(p, time=t), b1)
        # self.assertEqual(grad(df)(p, time=t), b1)
        # self.assertEqual(grad(grad(f))(p, time=t), b1)

        #exit()
        #### END DEBUG WORKSPACE ##############################################

        for f, df, ddf in [
            parse(f='x*t', df='grad(f)', ddf='grad(df)'),
            parse(f='x²*t', df='grad(f)', ddf='grad(df)'),
            parse(f='(x²+y²)*t', df='grad(f)', ddf='grad(df)'),
            parse(f='((x² + y²)*z²)*t', df='grad(f)', ddf='grad(df)'),
            ]:
            for pnts in [  1,           # p
                          [1,1],        # p
                          [1,1,1],      # p
                          [1,1,1,1],    # [p]*4
                          [[1,1]]*2,    # [p]*2
                          [[1,1]]*4,    # [p]*4
                          [[1,1,1]]*2,  # [p]*2
                          [[1,1,1]]*3,  # [p]*3
                          [[1,1,1]]*4,  # [p]*4
                          m1, m2, m3,
                    ]:

                for t in [
                            1.,
                            [1.],
                            [1., 2.],
                            [1., 2., 3.],
                            [1., 2., 3., 4.],
                         ]:

                    ts = np.atleast_1d(t)
                    dfR = np.squeeze([[df(p_, time=t_)
                                       for p_ in asPosListNP(pnts)]
                                        for t_ in ts])
                    ddfR = np.squeeze([[ddf(p_, time=t_)
                                        for p_ in asPosListNP(pnts)]
                                            for t_ in ts])

                    try:
                        self.assertEqual(df(pnts, time=t), dfR)
                        self.assertEqual(grad(f)(pnts, time=t), dfR)
                        self.assertEqual(ddf(pnts, time=t), ddfR)
                        self.assertEqual(grad(df)(pnts, time=t), ddfR)
                        self.assertEqual(grad(grad(f))(pnts, time=t), ddfR)
                        print('.', end='', flush=True)

                    except BaseException as e:
                        pg._r('#'*50)
                        pg._r(f'f={f.expr}')
                        pg._r(f'pnts={pnts}')
                        pg._y(f't={t}')
                        pg._y(f'grad(f)={grad(f)}')

                        print(e)
                        import traceback
                        traceback.print_exc(file=sys.stdout)
                        exit()

        print()
        ## test for more complex pnt types, e.g., pg.core.stdVectorR3Vector
        for f in [
                parse(f='x'),
                parse(f='x + y'),
                parse(f='x + y + z'),
                # grad(parse(f='sin(x)*cos(y)')) ## need fixed sizes
                # grad(grad(parse(f='sin(x)*cos(y)'))) ## need fixed sizes
            ]:

            for m in [m1, m2, m3]:
                s = ScalarSpace(m)
                eMat = s.uMat()
                qP = eMat.quadraturePoints()

                try:
                    self.assertEqual(f(qP), [f(qi) for qi in qP])
                except BaseException as e:
                    pg._r('#'*50)
                    pg._r(f'f={f}')

                    print(e)
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    exit()


    def test_ParsedFunctionArithm(self):
        """Test basic arithmetic with parsed symbolic functions."""
        a = asFunction('2*x')
        b = asFunction('x')
        #### START DEBUG WORKSPACE ############################################
        # p = asFunction('sin(x)*sin(y)')
        # print(p)
        # v = asFunction('grad(p)', p=p)
        # pg._g(v)
        # print(vacStr(v))
        # print(vacStr(grad(p)))
        # self.assertEqual(v, grad(p))

        # # print(a+1)
        # exit()
        #### END DEBUG WORKSPACE ##############################################
        self.assertEqual(vacStr(a._repr_str_()), vacStr('a(x) = 2*x'))
        self.assertEqual(vacStr(b._repr_str_()), vacStr('b(x) = x'))

        # __add__
        c = a + b
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c(x) = 3*x'))
        self.assertEqual(c(2), 6)
        self.assertEqual(vacStr((a+b)._repr_str_()), vacStr('3*x'))
        c = a + 2
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c(x) = 2*x+2'))
        self.assertEqual(c(2), 6)
        self.assertEqual(vacStr((a+1)._repr_str_()), vacStr('2*x+1'))
        self.assertEqual((a+1)(2), 2*2+1)
        self.assertEqual((a+1.2)(2), 2*2+1.2)

        # __radd__
        c = 2 + a
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c(x) = 2*x+2'))
        self.assertEqual(c(2), 6)
        self.assertEqual(vacStr((1+a)._repr_str_()), vacStr('2*x+1'))
        self.assertEqual((1+a)(2), 2*2+1)
        self.assertEqual((1.2+a)(2), 2*2+1.2)

        # __sub__
        c = a - 2
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c(x) = 2*x-2'))
        self.assertEqual(c(2), 2*2-2)
        self.assertEqual(vacStr((a-1)._repr_str_()), vacStr('2*x-1'))
        self.assertEqual((a-1)(2), 2*2-1)
        self.assertEqual((a-1.2)(2), 2*2-1.2)
        self.assertEqual((a-a)(2), 0)
        c = a - a
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c = 0'))

        # __rsub__
        c = 2 - a
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c(x) = 2-2*x'))
        self.assertEqual(c(2), 2-2*2)
        self.assertEqual(vacStr((1-a)._repr_str_()), vacStr('1-2*x'))
        self.assertEqual((1-a)(2), 1-2*2)
        self.assertEqual((1.2-a)(2), 1.2-2*2)

        # __radd__
        c = 2 + a
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c(x) = 2*x+2'))
        self.assertEqual(c(2), 6)
        self.assertEqual(vacStr((1+a)._repr_str_()), vacStr('2*x+1'))
        self.assertEqual((1+a)(2), 1+2*2)
        self.assertEqual((1.2+a)(2), 1.2+2*2)

        # __mul__
        c = a * 2
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c(x) = 4*x'))
        self.assertEqual(c(2), 8)
        self.assertEqual(vacStr((a*2)._repr_str_()), vacStr('4*x'))
        self.assertEqual((a*2)(2), 8)
        self.assertEqual((a*1.2)(2), 2*2*1.2)

        # __rmul__
        c = 2 * a
        self.assertEqual(vacStr(c._repr_str_()), vacStr('c(x) = 4*x'))
        self.assertEqual(c(2), 8)
        self.assertEqual(vacStr((2*a)._repr_str_()), vacStr('4*x'))
        self.assertEqual((2*a)(2), 8)
        self.assertEqual((1.2*a)(2.2), 1.2*2*2.2)

        #### some advanced tests with functions and parameters ####
        p = asFunction('sin(x)*sin(y)')
        v = asFunction('grad(p)', p=p)
        self.assertEqual(v, grad(p))


    def test_ParsedSubst(self):
        """Test substitution of parsed symbolic functions."""
        x = np.linspace(-1, 1, 3)
        mesh = pg.createGrid(x)
        s = ScalarSpace(mesh, p=1)
        h_sym = asFunction('x³')
        h_fea = FEASolution(s, values=h_sym)

        # K = lambda h: h**gamma
        # Ks = asFunction('h**gamma')

        K_lam = lambda h: abs(h)**gamma
        K_sym = asFunction('abs(h)**gamma')
        gamma = 6.1415
        xP = np.linspace(-1, 1, 100)

        #### START DEBUG WORKSPACE ############################################

        # print('K_sym(hs) =', K_sym)
        # dK_sym = derive(K_sym, 'h')
        #dK_lam = derive(K_lam, h_sym)
        #print(dK_lam)
        #pg._g(K_lam(h_fea(xP)))

        K_sym_fea = K_sym(h=h_fea, gamma=gamma)
        pg._g(K_sym_fea)

        dK_sym_fea = derive(K_sym_fea, h_fea)
        pg._y(dK_sym_fea)

        # pg._y(type(K_sym_fea))
        # pg._y(K_sym_fea)
        # pg._y(K_sym_fea(xP))

        #exit()
        #### START DEBUG WORKSPACE ############################################

        show = False

        self.assertEqual(K_lam(h_sym(xP)), K_lam(h_sym)(xP)) # exact
        self.assertEqual(K_lam(h_sym(xP)), K_sym(h=h_sym, gamma=gamma)(xP))

        self.assertEqual(K_lam(h_fea(xP)), K_lam(h_fea)(xP), )
        self.assertEqual(K_lam(h_fea(xP)), K_sym(h=h_fea, gamma=gamma)(xP))

        ## exact
        if show is True:
            axs = pg.plt.subplots(2,2, figsize=(16, 9))[1]
            axs[0][0].set_title(K_sym.itex() + '  $h_{sym} = x³$, p=1')
            axs[0][0].plot(xP, K_lam(h_sym)(xP),
                           label='$K_{lam}(h_{sym})(x)$')
            axs[0][0].plot(xP, K_sym(h=h_sym, gamma=gamma)(xP),
                           label='$K_{sym}(h_{sym})(x)$')

            axs[0][0].plot(xP, K_lam(h_fea)(xP),
                           label='$K_{lam}(h_{fea})(x)$') ## interpolated
            axs[0][0].plot(xP, K_sym(h=h_fea, gamma=gamma)(xP),
                           label='$K_{sym}(h_{fea})(x)$') ## interpolated

        #print('K_sym(hs) =', K_sym)
        dK_sym = derive(K_sym, 'h')
        #print(dK_sym)
        dK_sym_sym = dK_sym(h=h_sym, gamma=gamma)
        dK_sym_fea = dK_sym(h=h_fea, gamma=gamma)

        if np.isnan(dK_sym_sym(1)):
            pg._r('dK_sym_sym(1) fails')
            print('h_sym:', h_sym)
            print('K_h_sym:', K_sym)
            print('dK_sym_sym:', dK_sym_sym)

            dK_sym_sym = dK_sym(h=h_sym, gamma=gamma, verbose=True)
            print('dK_sym_sym:', dK_sym_sym)
            pg._r(1)
            halt
        else:
            dK_sym_sym = dK_sym(h=h_sym, gamma=gamma, verbose=False)
            if np.isnan(dK_sym_sym(1)):
                pg._r(2)
                halt

        dK_lam_sym = derive(K_lam, h_sym)
        dK_lam_fea = derive(K_lam, h_fea)

        # exact
        self.assertEqual(dK_lam_fea(xP), dK_sym_fea(xP), atol=3e-10)
        self.assertEqual(dK_lam_sym(xP), dK_sym_sym(xP), atol=3e-10)

        # exact
        if show is True:
            axs[1][0].plot(xP, dK_sym_sym(xP),
                           label=r'$\partial_h K_{sym}(h_{sym})(x)$')
            axs[1][0].plot(xP, dK_lam_sym(xP),
                           label=r'$\partial_h K_{lam}(h_{sym})(x)$')

            # interpolated
            axs[1][0].plot(xP, dK_sym_fea(xP),
                           label=r'$\partial_h K_{sym}(h_{fem})(x)$')
            axs[1][0].plot(xP, dK_lam_fea(xP),
                           label=r'$\partial_h K_{lam}(h_{fem})(x)$')

            # interpolated
            #axs[1][0].plot(xP, derive(K_lam, h_fea)(xP), label=r'$\partial_h K_{lam}(h_{fem})')
            # axs[1][0].plot(xP, derive(K, h)(h(xP)), label=r'$\partial_h K(h_{fem})(x)$')
            # axs[1][0].plot(xP, derive(K, h)(xP), label=r'$\partial_h K(h_{fem})(x)$')
            # axs[1][0].plot(xP, dK_sym(h=h, gamma=gamma)(xP), label=r'$\partial_h K_{sym}(h_{fem})(x)$')


        ## same like above but with p=2 for h
        s = ScalarSpace(mesh, p=2)
        h_fea = FEASolution(s, values=h_sym)

        dK_sym_fea = dK_sym(h=h_fea, gamma=gamma)
        dK_lam_fea = derive(K_lam, h_fea)

        self.assertEqual(dK_lam_fea(xP), dK_sym_fea(xP), atol=2e-10)
        self.assertEqual(dK_lam_sym(xP), dK_sym_sym(xP), atol=2e-10)

        if show is True:
            axs[0][1].set_title(K_sym.itex() + '  $h_{sym} = x³$, p=2')
            axs[0][1].plot(xP, K_lam(h_sym)(xP),
                           label='$K_{lam}(h_{sym})(x)$') ## exact
            axs[0][1].plot(xP, K_sym(h=h_sym, gamma=gamma)(xP),
                           label='$K_{sym}(h_{sym})(x)$')

            axs[0][1].plot(xP, K_lam(h_fea)(xP),
                           label='$K_{lam}(h_{fea})(x)$') ## interpolated
            axs[0][1].plot(xP, K_sym(h=h_fea, gamma=gamma)(xP),
                           label='$K_{sym}(h_{fea})(x)$') ## interpolated

            # exact
            axs[1][1].plot(xP, dK_sym_sym(xP),
                           label=r'$\partial_h K_{sym}(h_{sym})(x)$')
            axs[1][1].plot(xP, dK_lam_sym(xP),
                           label=r'$\partial_h K_{lam}(h_{sym})(x)$')

            # interpolated
            axs[1][1].plot(xP, dK_sym_fea(xP),
                           label=r'$\partial_h K_{sym}(h_{fem})(x)$')
            axs[1][1].plot(xP, dK_lam_fea(xP),
                           label=r'$\partial_h K_{lam}(h_{fem})(x)$')

            axs[0][0].legend()
            axs[0][0].grid()
            axs[0][1].legend()
            axs[0][1].grid()
            axs[1][0].legend()
            axs[1][0].grid()
            axs[1][1].legend()
            axs[1][1].grid()

        # print(a.subst(b))
        # exit()
        #### END DEBUG WORKSPACE ##############################################


class TestOperators(TestCollection):
    """Test parsing and runtime use for `oskar.mathOP` operators."""

    def test_BasicFuncExpr(self):
        """Test some basic function expressions."""
        x = np.linspace(10, 90, 11)
        mesh = pg.createGrid([0, 100])
        s = ScalarSpace(mesh)
        u = FEASolution(s, values=pg.x(mesh))

        #### START DEBUG WORKSPACE ############################################
        f = lambda _x: np.exp(1/_x)
        # pg._g(f(x))
        # pg._y(f(u))
        # pg._r(f(u)(x))
        # fx = u.subst(f)
        # pg._g(fx(x))
        #fx = lambda x: f(u(x))

        # return
        #### END DEBUG WORKSPACE ##############################################

        for f in [lambda _x: _x,
                  lambda _x: _x*_x,
                  np.exp,
                  lambda _x: np.exp(1/_x),
                  etaWater,
                  ]:

            try:
                self.assertEqual(f(x), f(u)(x))
                self.assertEqual(f(x), u.subst(f)(x))
            except BaseException as e:
                pg._r('+'*80)
                pg._y('f')
                pg._r('-'*80)

                print(e)
                import traceback
                traceback.print_exc(file=sys.stdout)
                exit()


        # >>> T = np.linspace(0, 100, 101)
        # >>> eta = etaWater(T)
        # >>> ax.plot(T, 1000*eta) # doctest: +ELLIPSIS
        # [...
        # >>> ax.set(xlabel='Temperature in °C',
        # ...        ylabel='dynamic viscosity in mPa s') # doctest: +ELLIPSIS
        # [...
        # >>> mesh = pg.createGrid([0, 100])
        # >>> s = FEASpace(mesh)
        # >>> Th = FEASolution(s, [0, 100])
        # >>> x = T
        # >>> eta = etaWater(Th)
        # >>> ax.plot(x, 1000*eta(x)) # doctest: +ELLIPSIS
        # >>> ax.grid()


    def test_Derive(self):
        """Test function generator for Derive operator."""
        #### START DEBUG WORKSPACE ############################################

        #exit()
        #### END DEBUG WORKSPACE ##############################################

        # solve symbolic
        dfSym, f = parse(du='derive(f, x)', f='x² + x³', simplify=True)

        self.assertEqual(f(2.0), 2**2 + 2**3)
        self.assertEqual(dfSym(2.0), 4.0 + 3*2**2)

        self.assertEqual(dfSym.sympy().expand(),
                         derive(f, 'x').sympy().expand())

        # solve symbolic
        df = derive(f, 'x')
        self.assertEqual(df(2.0), dfSym(2.0), atol=1e-13)

        # solve numeric
        df = derive(f, 'x', numeric=True)
        self.assertEqual(df(2.0), dfSym(2.0), atol=1e-13)

        # TODO:
        # this should be possible to mix symbolic and numeric in one call
        # dfSym, f = parse(du='d(f)', f='x² + x³', loc={'d':derive})


    def test_Div(self):
        """Test function generator for Divergence operator.

        v, dv = parse(v=*, dv='div(v)')

        vS = FEASolution()

        * dv                    -> should call symbolic
        * div(v)                -> should call symbolic same like du
        * div(v, numeric=True)  -> should call numeric
        * div(FEAFunction(*))   -> should call numeric
        * div(vS)               -> div on FEASpace with interpolation
        """
        #### START DEBUG WORKSPACE ############################################

        #exit()
        #### END DEBUG WORKSPACE ##############################################


    def test_Grad(self):
        """Test function generator for gradient operator.

        u, du = parse(u=*, du='grad(u)')

        uS = FEASolution()

        * du                    -> should call symbolic
        * grad(u)               -> should call symbolic same like du
        * grad(u, numeric=True) -> should call numeric
        * grad(FEAFunction(*))  -> should call numeric
        * grad(uS)              -> grad on FEASolution with interpolation
        * grad(f(uS))           -> grad on function of FEASolution

        TODO
        ----
            * decide return shapes for
                - du(array)      # 1D aka [x, 0, 0]
                - du(pos)
                - du([pos])
                - du(mesh)

        """
        u, duSym, uduSym = parse(u='x² + y²', du='grad(u)', udu='u*du')

        #### START DEBUG WORKSPACE ############################################
        # print(grad(u))
        # print(grad(u)*[1., 0.0])
        # print([1., 0.0] * grad(u))
        # print(grad(u)*grad(u))
        # print(grad(u)[0]*grad(u)[0]+grad(u)[1]*grad(u)[1])
        #exit()
        #### END DEBUG WORKSPACE ##############################################

        ### general expressions
        self.assertEqual(duSym, grad(u))

        ### evaluate expressions
        self.assertEqual(u(2.0), 4.0)
        self.assertEqual(u([2.0, 1.5, 0.0]), 6.25)

        ### TEST u du == du * u
        self.assertEqual(uduSym, u*grad(u))
        self.assertEqual(grad(u)*u, u*grad(u))

        # this squeeze out dimension
        self.assertEqual((grad(u)*u)(0), (u*grad(u))(0))
        # Important!
        self.assertEqual((grad(u)*u).valueSize(), (u*grad(u)*u).valueSize())
        self.assertEqual((grad(u)*u)(0).shape, (u*grad(u))(0).shape)

        # expression with grad <n, grad(u)> == <grad(u), n>
        self.assertEqual([1, 0] * grad(u), grad(u)[0])
        self.assertEqual(grad(u) * [0., 1], grad(u)[1])
        self.assertEqual([2, 2] * grad(u), 2*grad(u)[0] + 2*grad(u)[1])
        self.assertEqual(grad(u)*grad(u),
                         grad(u)[0]*grad(u)[0] + grad(u)[1]*grad(u)[1])
        self.assertEqual(grad(u)**2,
                         grad(u)[0]*grad(u)[0] + grad(u)[1]*grad(u)[1])

        x = np.linspace(0, 4, 5)
        mesh = pg.createGrid(x, x)
        s = ScalarSpace(mesh, p=2)
        uS = FEASolution(s, values=u(s.mesh))

        self.assertEqual(uS(2.0), 4.0)
        self.assertEqual(uS([2.0, 1.5, 0.0]), 6.25)

        self.assertEqual(duSym([2.0, 1.5, 0.0]), [4.0, 3.0])

        qPnts = s.uMat().quadraturePoints()

        for p in [ 2.0,                  # 1D convenience for [x_i, 0, 0]
                   np.linspace(1, 3, 5), # 1D convenience for [[x_i, 0, 0]]
                   [2.0, 1.5],           # 2D pos
                   [[2.0, 1.5]]*2,       # 2D [pos, pos] -> toField shape[2] < 3
                   [[2.0, 1.5]]*4,       # 2D [pos]*4 to -> toField shape[2] > 3
                   [2.0, 1.5, 0.0],      # 3D pos
                   [[2.0, 1.5, 0.0]]*2,  # 3D [pos, pos] -> toField shape[2] < 3
                   [[2.0, 1.5, 0.0]]*4,  # 3D [pos]*4 -> toField shape[2] > 3
                   mesh,                 #
                   qPnts,                # list if [PosList]
                  ]:
            try:
                self.assertEqual(duSym(p), grad(u)(p), atol=1e-18)
                self.assertEqual(duSym(p), grad(uS)(p), atol=1e-18)
                # self.assertEqual(duSym(p), grad(u, numeric=True)(p)[:,0:2],
                #                  atol=1e-10)
                #self.assertEqual(duSym(p), grad(u, numeric=True,
                #       simple=True, method='central')(p)[:,0:2], atol=1e-10),
            except BaseException as e:
                pg._r('+'*80)
                pg._y(f'p: {p}')
                pg._g(f'duSym(p): {duSym(p)}')
                pg._y(f'du(p): {grad(uS)(p)}')
                #self.assertEqual(duSym(p), du(p))
                pg._r('-'*80)

                print(e)
                import traceback
                traceback.print_exc(file=sys.stdout)
                exit()


        ### TEST index operator
        u = parse(u='x²*A + y³*L')
        self.assertEqual((grad(u)[0])(2, A=2), 8)           # numeric
        self.assertEqual((grad(u)[0])(x=2)(99, A=2), 8)     # symbolic
        self.assertEqual((grad(u)[1])([0, 2], L=2), 24)     # numeric
        self.assertEqual((grad(u)[1])(y=2, L=2)(99), 24)    # symbolic



        #######################################################################
        # TODO: performance test -> move to a better place

        ###############################
        # more expensive test
        ###############################
        f, u, duSym, _ = parse(f='-div(grad(u)) + u',
                    # u='exp(-((x - -0.5)**2 + (y -  0.5)**2)/sigma**2) +'
                    #   'exp(-((x - -0.5)**2 + (y - -0.5)**2)/sigma**2) +'
                    #   'exp(-((x -  0.5)**2 + (y - -0.5)**2)/sigma**2)',
                    u='exp(x²)',
                    du='grad(u)', sigma='1/8')

        @FEAFunction3
        def uF(p):
            return pg.x(p)**2

        px = np.random.randn(3*1024).reshape(1024,3)
        pg.tic()
        for p in px:
            with pg.tictoc('array access'):
                p[0]**2
            with pg.tictoc('pg.x access'):
                pg.x(p)**2
            with pg.tictoc('manual FEAF'):
                uF(p)
            with pg.tictoc('automated FEAF'):
                u(p)
        pg.toc()


    def testGrad_uS(self):
        """Test function generator for gradient operator with FEASolutionOP.

        Test chain rule for function generator.
        """
        u = parse(u='x² + y²')
        x = np.linspace(0, 4, 5)
        mesh = pg.createGrid(x, x)
        s = ScalarSpace(mesh, p=2)
        uS = FEASolution(s, u)
        pnt = [2.0, 1.5]
        def F(h):
            return (h**1.4 + h)/2

        #### START DEBUG WORKSPACE ############################################

        # grad(F(u)-u)
        # grad(F(u)-uS)

        # pg._g(grad(F(u)-u)[0])
        # pg._g(grad(F(u)-u)[0](pnt))

        # pg._y(grad(F(uS)-uS)[0])
        # pg._y(grad(F(uS)-uS)[0](pnt))

        # pg._y(grad(F(u)-uS)[0])
        # pg._y(grad(F(u)-uS)[0](pnt))

        #exit()
        #### END DEBUG WORKSPACE ##############################################

        self.assertEqual(grad(uS)(pnt), grad(u)(pnt))
        self.assertEqual((derive(F, uS) * grad(uS))(pnt), grad(F(u))(pnt),
                         atol=3e-10)
        self.assertEqual((derive(F(uS), uS) * grad(uS))(pnt), grad(F(u))(pnt),
                         atol=3e-10)
        self.assertEqual(grad(F(uS))(pnt), grad(F(u))(pnt), atol=3e-10)

        self.assertEqual(grad(F(uS)-uS)(pnt), grad(F(u)-u)(pnt), atol=9e-10)
        self.assertEqual(grad(F(u)-uS)(pnt), grad(F(u)-u)(pnt))
        self.assertEqual(grad(F(u)-uS)[0](pnt), grad(F(u)-u)[0](pnt))


    def test_Identity(self):
        """Test function generator with Identity operator.

            Test identity operator for function generator.
            Also test for some aux function, e.g., `sym`, `tr`.
        """
        la = 2
        mu = 0.3
        eps  = lambda u: sym(grad(u))
        sig  = lambda u: la*tr(eps(u))*I(u) + 2.0*mu*eps(u)
        sigE = lambda u, p: la*tr(eps(u))*I(u) + 2.0*mu*eps(u) - I(u)*p


        u2 = parse(u='x² + x*y + y², x² + x*y - y²')
        u3 = parse(u='x² + x*y + y², x² + x*y - y², z² - x*z + y*x')
        p = parse(u='x')

        #### START DEBUG WORKSPACE ############################################
        #print(sigE(u2, p))
        # print(L(f2))
        # print(L(f3))

        # print(grad(f3))
        # print(grad(f3)*I(3))
        # print(grad(f3)*I)
        # print((grad(f3)*I(3))(1))
        # print((grad(f3)*I(3))((1.0, 1.0, 1.0)))

        #return
        #### END DEBUG WORKSPACE ##############################################

        f, loc = parse(u='(x² + x*y + y², x² + x*y - y²)',
                       eps='sym(grad(u))',
                       tr1='tr(eps)',
                       latr1='la*(tr1)',
                       sig1='la*tr(eps)*I(2)',
                       #sig0='la*tr(eps)*I',
                       returnDicts = True
                       )

        la = 2
        u = f['u']
        tr1 = f['tr1']
        latr1 = f['latr1']
        sig1 = f['sig1']
        latr1.iSubst(la=la)
        sig1.iSubst(la=la)

        test = parse(test='tr(eps)*I(2)', loc=loc)
        self.assertEqual(test, tr(eps(u))*I(2))
        test = parse(test='grad(u)', loc=loc)
        self.assertEqual(test, grad(u))

        self.assertEqual(tr1, tr(eps(u)))
        self.assertEqual(tr1(1), 3.0)
        self.assertEqual(tr(grad(u))(1), 3.0)

        self.assertEqual(latr1, la*tr(eps(u)))
        self.assertEqual(latr1(1), 6.0)
        self.assertEqual(la*tr(grad(u))(1), 6.0)

        self.assertEqual((grad(u))([1,1]), [[3.0, 3.0],
                                            [3.0, -1.0]])

        ## Note Sympy mult is always dot .. so we change here *I to element-wise
        self.assertEqual((grad(u3)*I(3))(1), [[2.0, 0.0, 0.0],
                                              [0.0, 1.0, 0.0],
                                              [0.0, 0.0, -1.0]])
        self.assertEqual((grad(u3)*I)(1), [[2.0, 0.0, 0.0],
                                           [0.0, 1.0, 0.0],
                                           [0.0, 0.0, -1.0]])
        self.assertEqual((grad(u3)*I(3))([1.0, 1.0, 1.0]),
                                        [[3.0, 0.0, 0.0],
                                         [0.0, -1.0, 0.0],
                                         [0.0, 0.0, 1.0]])
        self.assertEqual((grad(u3)*I)([1.0, 1.0, 1.0]),
                                      [[3.0, 0.0, 0.0],
                                       [0.0, -1.0, 0.0],
                                       [0.0, 0.0, 1.0]])
        self.assertEqual((grad(u)*I(2))([1,1]), [[3.0, 0.0],
                                                 [0.0, -1.0]])
        self.assertEqual((I(2)*grad(u))([1,1]), [[3.0, 0.0],
                                                 [0.0, -1.0]])
        self.assertEqual((grad(u)*I)([1, 1]), [[3.0, 0.0],
                                               [0.0, -1.0]])
        self.assertEqual((I*grad(u))([1, 1]), [[3.0, 0.0],
                                               [0.0, -1.0]])

        # wannehave? self.assertEqual((grad(u)*I)([1, 1], dim=3),
        #                                                    [[3.0, 0.0, 0.0],
        #                                                     [0.0, -1.0, 0.0],
        #                                                     [0.0, 0.0, 0.0]])

        self.assertEqual(sig1, la*tr(eps(u))*I(2))
        self.assertEqual(sig1(1), [[6.0, 0.0],
                                   [0.0, 6.0]])
        self.assertEqual((la*tr(eps(u))*I(2))(1), [[6.0, 0.0],
                                                   [0.0, 6.0]])
        ## allways 3D because of scalar * I
        self.assertEqual((la*tr(eps(u))*I)(1), [[6.0, 0.0, 0.0],
                                                [0.0, 6.0, 0.0],
                                                [0.0, 0.0, 6.0]])

        for L in [p*I(2),
                  I(2)*p,
                  I(u2)*p,
                  p*I(u2),
                  ]:
            self.assertEqual(L(2), [[2.0, 0.0],
                                    [0.0, 2.0]])
        for L in [p*I(3),
                  I(3)*p,
                  I(u3)*p,
                  p*I(u3),
                  #I*p,
                  p*I,
                  ]:

            self.assertEqual(L(2), [[2.0, 0.0, 0.0],
                                    [0.0, 2.0, 0.0],
                                    [0.0, 0.0, 2.0]])

        self.assertEqual((la*tr(eps(u))*I - 6*p*I)(1), [[0.0, 0.0, 0.0],
                                                        [0.0, 0.0, 0.0],
                                                        [0.0, 0.0, 0.0]])
        self.assertEqual((la*tr(eps(u2))*I(u2) - 6*p*I(u2))(1), [[0.0, 0.0],
                                                                 [0.0, 0.0]])

        self.assertEqual((grad(u3)*I(3))(1), [[2.0, 0.0, 0.0],
                                              [0.0, 1.0, 0.0],
                                              [0.0, 0.0, -1.0]])
        self.assertEqual((grad(u3)*I)(1), [[2.0, 0.0, 0.0],
                                           [0.0, 1.0, 0.0],
                                           [0.0, 0.0, -1.0]])
        self.assertEqual((grad(u3)*I(3))([1.0, 1.0, 1.0]), [[3.0, 0.0, 0.0],
                                                            [0.0, -1.0, 0.0],
                                                            [0.0, 0.0, 1.0]])
        self.assertEqual((grad(u3)*I)([1.0, 1.0, 1.0]), [[3.0, 0.0, 0.0],
                                                         [0.0, -1.0, 0.0],
                                                         [0.0, 0.0, 1.0]])
        self.assertEqual((grad(u)*I)([1.0, 1.0]), [[3.0, 0.0],
                                                   [0.0, -1.0]])


        # ## START debug
        # # pnts = 0.3
        # pnts = 1
        # # pnts = [1, 1, 1]
        # # pnts = [[1,1], [1,1]]
        # # pnts = [[1,1,1]]*3
        # # pnts = [[1,1,1]]*4
        # # pnts = [[0.1, 0.0, 0.0]]*3

        # print('*'*40, 'pnts:', asPosListNP(pnts))


        # a1 = tr1(pnts)
        # a1 = sig1(pnts)
        # a1 = latr1(pnts)
        # pg._g(a1)


        # L = la*tr(eps(u))
        # a2 = L(pnts)
        # pg._y(a2)

        # self.assertEqual(a1, a2)
        # ## END debug

        for pnts in [  1,           # p
                       [1,1],        # p
                       [1,1,1],      # p
                       [1,1,1,1],    # [p]*4
                       [[1,1]]*2,    # [p]*2
                       [[1,1]]*4,    # [p]*4
                       [[1,1,1]]*2,  # [p]*2
                       [[1,1,1]]*3,  # [p]*3
                       [[1,1,1]]*4,  # [p]*4
                    ]:
            try:
                self.assertEqual(tr1(pnts), tr(eps(u))(pnts))
                self.assertEqual(latr1(pnts), (la*trace(eps(u)))(pnts))
                self.assertEqual(sig1(pnts), (la*trace(eps(u))*I(2))(pnts))
                ## 3D result
                #self.assertEqual(sig1(pnts), (la*trace(eps(u))*I)(pnts))
                self.assertEqual(sig1(pnts), (I(2)*(la*trace(eps(u))))(pnts))

            except BaseException as e:
                pg._r('#'*50)
                pg._r(f'pnts={pnts}')

                print(e)
                import traceback
                traceback.print_exc(file=sys.stdout)
                exit()


        # sig1.iSubst(la=la)
        # pg._g(sig1)
        # sig2 = la*tr(eps)*I(2)
        # pg._y(sig2)

        # pg._r('#########')
        # pg._g(sig1(1.0))
        # sig2 = la*(tr(eps)*I(2))
        # pg._y(sig2(1.0))


    def test_Integrate(self):
        """Test function generator with integrate.

            Test `integrate` operator for function generation.
        """
        f = asFunction('x')

        A = integrate(f)
        ## int x dx = A(x) = 0.5 x²
        self.assertEqual(str(A), "C.x**2/2")
        ## A(2) = 2
        self.assertEqual(A(2), 2.0)

        ## int_0^2 x dx = A(x) = A(2) - A(0) = 2
        AL = integrate(f, d='x', limits=[0, 2])
        self.assertEqual(AL(1), A(2)-A(0))
        self.assertEqual(AL(1), 2)

        #f = asFunction('x²')
        ## int_0^2 x-xi d xi = -> x*xi - x*xi²/2
        AL = integrate(f(x='x-xi'), d='xi', simplify=False)
        self.assertEqual(str(AL), "C.x*xi - xi**2/2")
        self.assertEqual(AL(1, xi=3), 3-4.5)


    def test_Mixed(self):
        """Test function generator for mixed operations."""
        #### START DEBUG WORKSPACE ############################################
        # u = asFunction('sin(x)*cos(y)')
        # #EQ = lambda u: -div(grad(u))
        # EQ = lambda u: -u

        # f = EQ(u)
        # pprint(f)
        # # self.assertEqual(vacStr(f._repr_str_()),
        # #                  vacStr('f(x,y) = 2*sin(x)*cos(y)'))

        # exit()
        #### END DEBUG WORKSPACE ##############################################
        u = asFunction('sin(x)*cos(y)')

        f = -div(grad(u))
        # print(f)
        # print(f._repr_str_())
        self.assertEqual(vacStr(f._repr_str_()),
                         vacStr('f(x,y) = 2*sin(x)*cos(y)'))

        EQ = lambda u: -div(grad(u))
        f = EQ(u)
        self.assertEqual(vacStr(f._repr_str_()),
                         vacStr('f(x,y) = 2*sin(x)*cos(y)'))


class TestPDEExpressions(TestCollection):
    """Test pde expression parsing containing a FEASpace."""

    def test_Advection(self):
        """Test advection-diffusion equation parsing."""
        mesh = pg.createGrid(11)
        s = ScalarSpace(mesh)
        v = parse(f=1)
        R = 1
        a = 2

        pde = v*grad(s) == div(a*grad(s)) + R
        pde = PDE(pde)
        # pg._g('#'*60)
        # pg._g(str(pde))
        # pg._y(str(pde.weakForm))
        #pde = div(v*s) == div(a*grad(s)) + R


    def test_Derive_t(self):
        """Test expression with time derivatives."""
        #### START DEBUG WORKSPACE ############################################
        mesh = pg.createGrid(11)
        s = ScalarSpace(mesh)

        f = asFunction('x')
        cv = 2; lam = 2; H = 100

        pde = cv*derive(s, 't') == div(lam*grad(s))
        dt, L = splitDeriveTime(pde)
        # pg._g(splitDeriveTime(pde))
        # pg._g(splitTransientLeftRight(pde))


        pde = cv*derive(s, 't') - div(lam*grad(s)) == 0
        dt, L = splitDeriveTime(pde)
        # pg._y(splitDeriveTime(pde))
        # pg._y(splitTransientLeftRight(pde)) #ok

        pde = cv*derive(s, 't') == div(lam*grad(s)) + f + 1
        # pg._g(splitDeriveTime(pde))
        # pg._g(splitTransientLeftRight(pde)) # OK

        pde = cv*derive(s, 't') - div(lam*grad(s)) -1 == f
        # pg._y(splitDeriveTime(pde))
        # pg._y(splitTransientLeftRight(pde))  # OK

        pde = cv*derive(s, 't') - div(lam*grad(s)) -f -1== 0
        # pg._b(splitDeriveTime(pde))
        # pg._b(splitTransientLeftRight(pde)) # FAIL +s*0

        # from oskar.solve import splitTransientLeftRight, splitDeriveTime,
        # splitLeftRight

        # PDE = derive(s, 't') -div(a*grad(s)) == 0
        # L, R, c = splitTransientLeftRight(PDE)
        # pg._g(L, R, c)
        # dT, L = splitDeriveTime(PDE)
        # pg._g(dT, L)
        # #dT, L = splitDeriveTime(L)
        # pg._b(splitLeftRight(L.weakForm))

        # PDE = derive(s, 't') == div(a*grad(s))
        # L, R, c = splitTransientLeftRight(PDE)
        # pg._y(L, R, c)
        # dT, L = splitDeriveTime(PDE)
        # pg._y(dT, L)
        # pg._b(splitLeftRight(L.weakForm))

        # T_fea = solve(L(s) == dirac(s, rs=[0.0, 0.0])*H,
        #       ic=0, bc={'Dirichlet':{'*':0.0}}, times=1, useMats=True)

        #exit()
        #### END DEBUG WORKSPACE ##############################################

        mesh = pg.createGrid(11)
        s = ScalarSpace(mesh)
        uh = FEASolution(s)
        f = FEAFunction(lambda x:1)
        dt = 0.1
        a = 3.0

        pde = -dt*(div(a*grad(s))) + s == dt*f + uh

        # pg._g(pde)
        # pg._g(pde.weakForm)

        #exit()
        np.testing.assert_equal(vacStr(pde.weakForm),
                vacStr("0.1*grad(s)*3.0*grad(s) + s*s = s*(0.1*f(pnt) + uh)"))
        np.testing.assert_equal(vacStr(pde.createWeakForm(splitSolutionOPWithFuncs=True)),
                vacStr("0.1*grad(s)*3.0*grad(s) + s*s = s*0.1*f(pnt) + s*uh"))

        pde = (s - uh)/dt + (div(a*grad(s))) == f
        np.testing.assert_equal(vacStr(PDE(pde).weakForm),
                vacStr("s*10.0*s-grad(s)*3.0*grad(s)=s*10.0*uh+s*f(pnt)"))

        pde = 1/dt*(s - uh) + (div(a*grad(s))) == f
        np.testing.assert_equal(vacStr(PDE(pde).weakForm),
                vacStr("s*10.0*s - grad(s)*3.0*grad(s) = s*10.0*uh + s*f(pnt)"))

        pde = (s - uh)/dt == - (div(a*grad(s)))
        np.testing.assert_equal(vacStr(PDE(pde).weakForm),
                                vacStr("s*10.0*s-grad(s)*3.0*grad(s)=s*10.0*uh"))

        cv = 2; lam = 2; H = 100

        pde = derive(s, 't') - div(grad(s)) == dirac(s, rs=[0.0, 0.0])
        self.assertTrue(pde.hasDeriveT())

        dt, L = splitDeriveTime(pde)
        #print(L.weakForm)

        pde = cv*derive(s, 't') - div(lam*grad(s)) == dirac(s, rs=[0.0, 0.0])*H
        dt, L = splitDeriveTime(pde)
        #print(L.weakForm)

        return
        # TODO: cleanme
        # pde = derive(s, 't') == Laplace(s)
        # dt, L = splitDeriveTime(pde)
        # np.testing.assert_equal(vacStr(L.weakForm), vacStr("grad(s)*grad(s)"))

        # pde = derive(s, 't') - Laplace(s) == 0
        # dt, L = splitDeriveTime(pde)
        # np.testing.assert_equal(vacStr(L.weakForm), vacStr("grad(s)*grad(s)=s*0"))

        # pde = c*derive(s, 't') == Laplace(s) + f
        # dt, L = splitDeriveTime(pde)
        # np.testing.assert_equal(vacStr(L.weakForm), vacStr("grad(s)*grad(s)=s*f"))

        # pde = c*derive(s, 't') - Laplace(s) == f
        # dt, L = splitDeriveTime(pde)
        # np.testing.assert_equal(vacStr(L.weakForm), vacStr("grad(s)*grad(s)=s*f"))

        # pde = c*derive(s, 't') + Laplace(s) == f
        # dt, L = splitDeriveTime(pde)
        # np.testing.assert_equal(vacStr(L.weakForm),
        #                         vacStr("-(grad(s)*grad(s))=s*f"))

        # pde = derive(s, 't') - div(grad(s)) == dirac(s, rs=[0.0, 0.0])
        # dt, L = splitDeriveTime(pde)
        # np.testing.assert_equal(vacStr(L.weakForm),
        #                         vacStr("grad(s)*grad(s)=s*dirac(r)"))

        #print(L.weakForm)
        #pde = derive(s, 't') - Laplace(s) == f
        #pde = derive(s, 't') == Laplace(s) + f
        #pde = derive(s, 't')*c == Laplace(s) + f

        #pde = a*derive(s, 't') - div(b*grad(s)) == f
        #pde.fea(s0=FEASolution())
        #times = np.linspace(0, 1, 11) # auto would be nice
        #! throw exception if missing ic or times while having derive from t
        #! throw exception if missing bc
        #uh = solve(pde, ic=uh, bc={'Dirichlet':{'*':0}},
        #           times=times, theta=0.5)

        # pg._g('#'*60)
        # pg._g(str(pde))
        # pg._y(str(pde.weakForm))


    def test_Div(self):
        """Test pde expression with divergence operator."""
        mesh = pg.createGrid(11)
        s = ScalarSpace(mesh)
        uh = FEASolution(s)

        #### START DEBUG WORKSPACE ############################################
        # pg._g(type(div(-uh)))

        # pg._y(type(div(uh)))

        # pg._y(type(-div(uh)))

        #self.assertEqual(type(div(-uh)), type(-div(uh)))
        #return
        #### START DEBUG WORKSPACE ############################################

        ## need to be fixed
        # self.assertEqual(type(div(-uh)), type(-div(uh))) ## TODO: fix this

        pde = div(grad(s))
        np.testing.assert_equal(vacStr(pde), vacStr('div(grad(s))'))
        np.testing.assert_equal(vacStr(pde.weakForm),
                                vacStr('-(grad(s)*grad(s))'))

        pde = div(2.0 * grad(s))
        np.testing.assert_equal(vacStr(pde), vacStr('div(2.0*grad(s))'))
        np.testing.assert_equal(vacStr(pde.weakForm),
                                vacStr('-(grad(s)*2.0*grad(s))'))

        pde = -div(2.0 * grad(s))
        np.testing.assert_equal(vacStr(pde),    vacStr('-div(2.0*grad(s))'))
        np.testing.assert_equal(vacStr(pde.weakForm),
                                vacStr('grad(s)*2.0*grad(s)'))

        pde = -div(2.0 * grad(s)) == 1
        np.testing.assert_equal(vacStr(pde), vacStr('-div(2.0*grad(s))=1'))
        np.testing.assert_equal(vacStr(pde.weakForm),
                                vacStr('grad(s)*2.0*grad(s)=s*1'))

        pde = -div(2.0 * grad(s)) + s
        np.testing.assert_equal(vacStr(pde), vacStr('-div(2.0*grad(s))+s'))
        np.testing.assert_equal(vacStr(pde.weakForm),
                                vacStr('grad(s)*2.0*grad(s)+s*s'))

        pde = -div(2.0 * grad(s)) + 3*s
        np.testing.assert_equal(vacStr(pde), vacStr('-div(2.0*grad(s))+3*s'))
        np.testing.assert_equal(vacStr(pde.weakForm),
                                vacStr('grad(s)*2.0*grad(s)+s*3*s'))

        pde = -div(2.0 * grad(s)) + 3*s == 2
        np.testing.assert_equal(vacStr(pde), vacStr('-div(2.0*grad(s))+3*s=2'))
        np.testing.assert_equal(vacStr(pde.weakForm),
                                vacStr('grad(s)*2.0*grad(s)+s*3*s=s*2'))

        ## random MMS tests
        f, u, a = parse(f='-div(a*grad(u))', u='x', a='1+x²')
        pde = -div(a*grad(s)) == f
        uh = solve(pde, bc={'Dirichlet':{'*':u}})
        np.testing.assert_almost_equal(normL2(u-uh), 1e-12)

        pde = f == -div(a*grad(s))
        uh = solve(pde, bc={'Dirichlet':{'*':u}})
        np.testing.assert_almost_equal(normL2(u-uh), 1e-12)

        f, u, a, b = parse(f='-div(a*grad(u)) + b*u', u='x', a='1+x²', b='1-x²')
        uh = solve(-div(a * grad(s)) + b*s == f, bc={'Dirichlet':{'*':u}})
        np.testing.assert_almost_equal(normL2(u-uh), 1e-12)


    def test_Elastic(self):
        """Test expression for elastic problems."""
        def eps(v):
            return sym(grad(v))

        def sigma(v):
            return lam*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        def sigmaEff1(v, T):
            return C*(eps(v) - alpha*T*I(v))

        def sigmaEff1b(v, T):
            return C*eps(v) - C*alpha*T*I(v)

        def sigmaEff2(v, T):
            return sigma(v) - alpha*T*I(v)

        T = asFunction('1+x²')
        lam = 1.42
        mu = 0.3
        alpha = 2
        C = createElasticityMatrix(lam, mu)
        mesh = pg.createGrid(3, 3)
        v = VectorSpace(mesh)
        s = ScalarSpace(mesh)
        Th = FEASolution(s, values=T(mesh), name='Th')
        T0 = 20

        ##### Test #############################################################
        pg._g()


        # def sigmaEff(v, T):

        #     return sigma(v) - alpha*T*I(v)
        #     return sigma(v) - (alpha*(3*lam + 2*mu)*T*I(v))

        # dT = 10.0
        # #dT = Th
        # L1 = grad(v)*sigmaEff(v, dT)
        # pg._g(L1)
        # pg._g(findForms(L1))
        # A1, b1 = L1.assemble(core=False)
        # #pg._g(b1)

        # L2 = (-div(sigmaEff(v, dT))).weakForm
        # pg._y(L2)
        # pg._y(findForms(L2))

        # L3 = (-div(sigmaEff(v, dT))==0).weakForm
        # pg._r(L3)
        # pg._r(findForms(L3))

        # #self.assertEqual(findForms(L2), findForms(L1))



        # halt
        ##### Test #############################################################

        self.assertEqual(findForms((-div(sigma(v))).weakForm),
                         findForms(grad(v)*sigma(v)))

        self.assertEqual(findForms((-div(sigmaEff1(v, 100))).weakForm),
                         findForms(grad(v)*sigmaEff1(v, 100)))

        self.assertEqual(findForms((-div(sigmaEff2(v, 100))).weakForm),
                         findForms(grad(v)*sigmaEff2(v, 100)))

        self.assertEqual(findForms((-div(sigmaEff1(v, T))).weakForm),
                         findForms(grad(v)*sigmaEff1(v, T)))

        self.assertEqual(findForms((-div(sigmaEff2(v, T))).weakForm),
                         findForms(grad(v)*sigmaEff2(v, T)))

        self.assertEqual(findForms((-div(sigmaEff1(v, Th))).weakForm),
                         findForms(grad(v)*sigmaEff1(v, Th)))

        self.assertEqual(findForms((-div(sigmaEff1(v, Th-T0))).weakForm),
                         findForms(grad(v)*sigmaEff1(v, Th-T0)))

        self.assertEqual(findForms((-div(sigmaEff1(v, Th-T0))).weakForm),
                         findForms(grad(v)*sigmaEff1(v, Th-T0)))

        self.assertEqual(findForms((-div(sigmaEff1(v, T0-Th))).weakForm),
                         findForms(grad(v)*sigmaEff1(v, T0-Th)))

        self.assertEqual(findForms((-div(sigmaEff2(v, Th))).weakForm),
                         findForms(grad(v)*sigmaEff2(v, Th)))

        la = ParameterDict({0:lam})
        mu = ParameterDict({0:mu})
        alpha = ParameterDict({0:alpha})

        #la = lam

        def sigmaEffective(v):
            return la*tr(eps(v))*I(v) + 2.0*mu*eps(v)

        def sigmaTotal(v):
            return sigmaEffective(v) - (alpha*(3*la + 2*mu)*(Th-T0))*I(v) # orig

        L = grad(v)*sigmaTotal(v) == v*0
        pg._g(L)
        LF, BF = findForms(L)
        print(BF)
        for l in LF:
            pg._g(l)
        #pg._g(BF)

        L = -div(sigmaTotal(v)) == 0
        pg._y(L.weakForm)
        LF, BF = findForms(L.weakForm)
        print(BF)
        for l in LF:
            pg._y(l)


    def test_Expand(self):
        """Test expression expansion."""
        mesh = pg.createGrid(2)
        s = ScalarSpace(mesh)
        uh = FEASolution(s, values=3, name='uh')
        a = FEAFunction(lambda _p:2 )
        f = FEAFunction(lambda _p:3 )
        aS, fS = parse(a='a', f='f')

        dt = 0.1

        #### START DEBUG WORKSPACE ############################################
        # L = s*(f-uh)
        # L = s*((f-uh)**2)
        # L = -uh*-f

        # ut = fS-uh
        # L = s*grad(uh)

        # print(uh)
        # print(grad(uh))
        # print(type(grad(uh).a))

        #L = -div(uh)
        #L = -div(-uh)
        C = createElasticityMatrix(1.42, 0.3)
        C = f

        def eps(v):
            return sym(grad(v))

        def f1(v):
            return C*(eps(v) - uh*I(v))

        def f2(v):
            return C*eps(v) - C*uh*I(v)

        L = div(f2(s))
        L = f + uh

        # print(L, type(L))
        # print(L.expandTerm())
        # print(L.expand())
        # print(L.expand(forSpaces=True))
        # print(L.expand(splitSolutionOPWithFuncs=True))
        # print(L.expand(removeDiv=True))

        # self.assertEqual((a + uh).expand(forSpaces=False), [a, uh])
        # self.assertEqual((a + uh).expand(forSpaces=True), [a + uh])
        # L = (s + a/2).expand(removeDiv=True)
        # , [2*s, a]

        #self.assertEqual(div(-uh).expand(), [-div(uh)])
        #exit()
        #### END DEBUG WORKSPACE ##############################################

        self.assertEqual((a).expand(), [a])
        self.assertEqual((s*2).expand(), [s*2])
        self.assertEqual((s + a/2).expand(removeDiv=True), [s, 0.5*a])
        self.assertEqual((a + uh).expand(forSpaces=True), [a + uh])
        self.assertEqual((a + uh).expand(splitSolutionOPWithFuncs=True), [a, uh])
        self.assertEqual((a + a).expand(), [a, a])

        self.assertEqual((2*a + a).expand(), [2*a,a])
        self.assertEqual((a - 2*a).expand(), [a, -(2*a)])
        self.assertEqual((2*a - f).expand(), [2*a, -f])
        self.assertEqual((a * (2 + a)).expand(), [2*a, a*a])
        self.assertEqual(((2 + a)*f).expand(), [2*f, a*f])
        self.assertEqual(((a + s)/0.1).expand(), [10.0*a, 10.0*s])
        self.assertEqual((f/(2 + a)).expand(), [f/2, f/a])
        self.assertEqual((a*(2 + a)/0.1).expand(), [2*a/0.1, a*a/0.1])
        self.assertEqual(((a + f)*(s - uh)).expand(),
                        [a*s, -(a*uh), f*s, -(f*uh)])

        ### START test bubbleUpNeg
        self.assertEqual((s*-uh).expand(), [-(s*uh)])
        self.assertEqual((a*-f).expand(), [-(a*f)])
        self.assertEqual((s * f * -uh).expand(), [-(s*f*uh)])
        self.assertEqual((s * -(f * uh)).expand(), [-(s*f*uh)])
        self.assertEqual((s * (f * -uh)).expand(), [-(s*f*uh)])
        #self.assertEqual(div(-uh).expand(), [-div(uh)])
        ### END test bubbleUpNeg

        self.assertEqual((s*((f-uh)**2)).expand(splitSolutionOPWithFuncs=True),
                        [s*f**2, -(s*(2*f*uh)), s*uh**2])

        self.assertEqual((s*((f-uh)**2)).expand(forSpaces=False),
                        [s*((f-uh)**2)])

        self.assertEqual((s*((f-uh)**2)).expand(forSpaces=True),
                        [s*((f-uh)**2)])

        self.assertEqual((s*grad(uh)).expand(forSpaces=True),
                         [s*grad(uh)])

        pde = a*(s-uh)/dt - Laplace(s) == f
        # self.assertEqual(vacStr(pde.expand()),
        #                         vacStr([a*s/dt, -(a*uh)/dt, -Laplace(s), -f]))
        # self.assertEqual(vacStr(pde.fea.expand()),
        #                         vacStr([s*a*s/dt, s*a*-u/dt, -grad(s)*grad(s), -s*f]))


    def test_FindForms(self):
        """Find linear and bilinear forms of a expression."""
        mesh = pg.createGrid(5)
        s = ScalarSpace(mesh)
        v = VectorSpace(mesh)
        c = ConstantSpace(mesh)
        u = parse(u='x²')
        q = parse(q='x, y')
        f = asFunction('x')
        ftS = asFunction('x*t')

        ft = FEAFunction(lambda p, t: pg.x(p)*t)

        uh = FEASolution(s, values=u)
        qh = FEASolution(v, values=q)
        dt = 0.1
        theta = 0.5
        ti = 0.1
        a = ParameterDict({0:2.0})
        C = createElasticityMatrix(1.42, 0.3)
        #### START DEBUG WORKSPACE ############################################

        # def eps(v):
        #     return sym(grad(v))

        # lam = 2.
        # mu = 0.3
        # #L = tr(eps(v))*I(v) #ok
        # #L = I(v)*tr(eps(v)) # ok


        L = grad(v)*(C*(grad(v) - a*I(v))) == 0

        if (isStrongFormPDE(L)):
            L = PDE(L)
            L = L.weakForm

        # print(L)
        # print(L.expandTerm())
        # print(L.expand())
        # print(L.expand(forSpaces=True))

        # pg.core.setDeepDebug(-1)
        # lF, bF = findForms(L)
        # pg.core.setDeepDebug(0)
        # pg._g(lF)
        # pg._y(bF)


        # _assemble(L, t=1)
        # _testExp(L, t=1)
        #halt
        #### END DEBUG WORKSPACE ##############################################

        self.assertEqual(findForms(s*grad(s))[1], [['+', s*grad(s), None]])
        self.assertEqual(findForms(s*grad(uh))[0], [['+', s*grad(uh), None]])
        self.assertEqual(findForms(s * (grad(u)-grad(qh)))[0],
                        [['+', s * (grad(u)-grad(qh)), None]])

        ### test scale-shift for linear form
        self.assertEqual(findForms(grad(s)*(((1-theta)*dt)*grad(uh))),
                         findForms((1-theta)*dt*grad(s)*grad(uh)))
        self.assertEqual(findForms(s*(((1-theta)*dt)*ft)),
                         findForms((1-theta)*dt*s*ft))

        ### div(u-uh)
        self.assertEqual(findForms(s*div(s-uh)),
                         [[['+', s*div(uh), None]], # LF
                          [['+', s*div(s), None]]]) # BF



        # negFunction not yet considered as -() #TODO
        # self.assertEqual(vacStr(findForms(-s*-f)[0]),
        #                  vacStr([['+', -s*-f, None]]))

        # self.assertEqual(vacStr(findForms(-s*-u)[0]),
        #                  vacStr([['+', s, u]]))

        # self.assertEqual(vacStr(findForms(-(-s*u))[0]),
        #                  vacStr([['+', s, u]]))

        # self.assertEqual(vacStr(findForms(tr(eps(v))*I(v))[0]),
        #                  vacStr([['+', tr(eps(v)), 1.0]]))

        # self.assertEqual(vacStr(findForms(I(v)*tr(eps(v)))[0]),
        #                  vacStr([['+', tr(eps(v)), 1.0]]))


    def test_ToWeak(self):
        """Test conversion from strong PDE to WEAK."""
        mesh = pg.createGrid(5)
        s = ScalarSpace(mesh)
        v = VectorSpace(mesh)
        c = ConstantSpace(mesh)
        u, a, b = parse(u='x²', a='x', b='(x)²')
        q = parse(q='x, y')
        fS = asFunction('x')
        ftS = asFunction('x*t')

        ft = FEAFunction(lambda p, t=1: pg.x(p)*t)

        uh = FEASolution(s, values=u)
        qh = FEASolution(v, values=q)
        dt = 0.1
        theta = 0.5
        ti = 0.1
        #### START DEBUG WORKSPACE ############################################
        # LR = s*s + theta*dt*grad(s)*grad(s) == s*uh + theta*dt*s*ftS \
        #       - (1-theta)*dt*grad(s)*grad(uh) + (1-theta)*dt*s*ftS(t=ti)

        # L = (s-uh)/dt == theta * (laplace(s) + ftS) \
        #                 + (1-theta) * (laplace(uh) + ftS(t=ti))

        # L = 1/dt*s - 1/dt*uh == theta * (laplace(s) + ftS) \
        #                 + (1-theta) * (laplace(uh) + ftS(t=ti))

        # L = s*(1/dt*s) + theta*grad(s)*grad(s) == s*(1/dt*uh) + theta*s*ftS \
        #       - (1-theta)*grad(s)*grad(uh) + (1-theta)*s*ftS(t=ti)

        # L = PDE(L).weakForm
        # print(L)
        # LF, BF = findForms(L)
        # # pg._g(BF)
        # # pg._y(LF)
        # _assemble(L, t=1)
        # _assemble(LR, t=1)

        # _testExp(L, time=ti)
        #return
        #### END DEBUG WORKSPACE ##############################################
        LR = s*s + theta*dt*grad(s)*grad(s) == s*uh + theta*dt*s*ftS \
              - (1-theta)*dt*grad(s)*grad(uh) + (1-theta)*dt*s*ftS(t=ti)

        L = (s-uh)/dt == theta * (laplace(s) + ftS) \
                        + (1-theta) * (laplace(uh) + ftS(t=ti))
        L = PDE(L).weakForm

        _testExp(L, LR *1/dt, time=ti) ## 1/dt scaling ()

        ## same as above but without same dt scaling
        LR = s*(1/dt*s) + theta*grad(s)*grad(s) == s*1/dt*uh + theta*s*ftS \
              - (1-theta)*grad(s)*grad(uh) + (1-theta)*s*ftS(t=ti)
        _testExp(L, LR, time=ti)

        # same as above but without sympy func
        LR = s*s + theta*dt*grad(s)*grad(s) == s*uh + theta*dt*s*ft \
              - (1-theta)*dt*grad(s)*grad(uh) + (1-theta)*dt*s*ft

        L = (s-uh)/dt == theta * (laplace(s) + ft) \
                        + (1-theta) * (laplace(uh) + ft)
        L = PDE(L).weakForm
        _testExp(L, LR*1/dt, time=ti) ## 1/dt scaling

        # little bit more complicated
        BEQ = lambda u: - div(a*grad(u)) + b*u
        LR = s*s == - dt*(BEQ(s).weakForm) + s*uh + dt*s*ft # weak form  -- OK
        L = (s-uh)/dt == -BEQ(s) + ft
        L = PDE(L).weakForm
        _testExp(L, LR*1/dt, time=ti) ## 1/dt scaling


    def test_GEN_MMS(self):
        """Simple test for MMS based test strategies."""
        u, a, b = parse(u='sin(x)*exp(-x)', a='1+x²', b='sin(x/4)')

        #### START DEBUG WORKSPACE ############################################
        # mesh = pg.meshtools.createGrid(x=np.linspace(0, 1, 11))
        # s = ScalarSpace(mesh, name='uh')

        #L = lambda u: -laplace(u)
        #L = lambda u: -div(grad(u))
        #L = lambda u: div(grad(u))  + u*b

        #print(L(u)(1))

        #uh = solve(L(s) == L(u), bc={'Dirichlet':{'*':u}}, useMats=True)
        # #L = lambda u: div(a*grad(u))
        # #L = lambda u: Laplace(u)
        # #a = 2
        # L = lambda u: a*laplace(u)

        # wf = (L(s)).fea
        # A1 = wf.assemble(core=False)
        # A2 = wf.assemble(core=True)
        # A3 = wf.assemble(useMats=True)
        # pg._g(A1)
        # pg._y(A2)
        # pg._r(A3)

        # #L = lambda u: laplace(u)

        # print((L(s)).weakForm)

        # pg._g(div(a*grad(s)).fea.assemble(useMats=True))

        # # print('u', u)
        # # print('du', grad(u))
        # # print('L(u)', L(u))
        # # print(L(u).__repr__())
        # # f = L(u)
        # # print('f', f)
        # # print('f', f.__repr__())
        # uh = solve(L(s) == L(u), bc={'Dirichlet':{'*':u}}, useMats=True)
        # print(uh.values)
        # print(normL2(u-uh))
        # print(normL2(u, space=uh.space))
        #self.assertLess(normL2(u-uh)/normL2(u, space=uh.space)*100, 0.5)
        #return
        #### END DEBUG WORKSPACE ##############################################

        mesh = pg.meshtools.createGrid(x=np.linspace(0, 1, 11))
        s = ScalarSpace(mesh, name='uh')

        for L in [
                    lambda u: laplace(u),
                    lambda u: -laplace(u),
                    #lambda u: -Laplace(-u),
                    lambda u: laplace(u) + a*u,
                    lambda u: laplace(u) + a*u*a + b*u,
                    lambda u: laplace(u) + (a*a + b)*u,
                    lambda u: div(grad(u)),
                    lambda u: div(a*grad(u)) + u*b,
                    lambda u: div(a*grad(u)),
                    #lambda u: a*laplace(u),     # a/cell makes no sense for mms
                    #lambda u: a*div(grad(u)),   # a/cell makes no sense for mms
                 ]:

            try:
                uh = solve(L(s) == L(u), bc={'Dirichlet':{'*':u}}, useMats=True)
                #uh = solve(L(s) == L(u), bc={'Dirichlet':{'*':u}})

                ## check for relative normL2 < 0.5%
                #pg._b(normL2(u-uh)/normL2(u, space=uh.space)*100)
                #pg._b(normL2(u-uh)/normL2(u(mesh))*100)
                self.assertLess(normL2(u-uh)/normL2(u, space=uh.space)*100, 0.5)
                # np.testing.assert_equal(normSemiH1(u-uh)/\
                #                       normSemiH1(u, space=uh.space)*100 < 0.5,
                #                         True) # implementme
                print('.', end='')

            except BaseException as e:
                pg._r('+'*60)
                pg._y('L(s):', L(s))
                pg._y('L(u):', L(u))
                pg._y('f=', repr(L(u)))
                pg._r('rel normL2L:',
                        normL2(u-uh)/normL2(u, space=uh.space)*100)
                pg._r('-'*60)

                #ax = pg.show(uh, marker='o', lw=0.5)[0]
                #pg.show(mesh, u, ax=ax)
                print(e)
                import traceback
                traceback.print_exc(file=sys.stdout)
                exit()


    def test_Greens(self):
        """Test parsing and differentiation for some Greens functions.

        Test if Greens- or Fundamental solutions solve there counterpart.
        """
        #### START DEBUG WORKSPACE ############################################
        f, u, D = parse(f='derive(u,t)-D*Laplace(u)',
                        u='1/(4*pi*D*t)**(1/2)*exp(-x²/(4*D*t))',
                        D=2)

        self.assertEqual(f(42., t=42.), 0)
        f = derive(u,'t') - div(D*grad(u))
        self.assertEqual(type(derive(u,'t')), FEAFunction)
        self.assertEqual(type(div(D*grad(u))), FEAFunction)

        self.assertEqual(type(f), FEAFunction)

        #print(type(f))
        self.assertEqual(f(42., t=42.), 0, tol=1e-20)
        self.assertEqual(f(42., t=42., numeric=True), 0, tol=1e-20)

        # f = derive(u,'t') - div(2*grad(u))
        # #f = div(D*grad(u))
        #print(f)
        # pprint(f)

        # f, r = parse(f='r', r='sqrt(x²+y²)')

        # print(f)

        #exit()
        #### END DEBUG WORKSPACE ##############################################

        # 1D closed form diffusion equation -> f = 0
        f, u, D = parse(f='derive(u,t)-D*Laplace(u)',
                        u='1/(4*pi*D*t)**(1/2)*exp(-x²/(4*D*t))',
                        D=2)
        self.assertEqual(f(1), 0)
        self.assertEqual(f(42.42, t=42.42), 0)
        self.assertEqual(str(f), '0')
        self.assertEqual(f._repr_str_(), 'f = 0')

        # with math OP instead of parsing
        f = derive(u,'t') - div(D*grad(u))
        self.assertEqual(f(42.42, t=42.), 0, tol=1e-20)


        # 2D closed form diffusion equation -> f = 0
        f, u, D = parse(f='derive(u,t)-D*Laplace(u)',
                        u='1/(4*pi*D*t)**(2/2)*exp(-(x²+y²)/(4*D*t))',
                        D=3.14, simplify=True)
        self.assertEqual(f(1), 0)
        self.assertEqual(str(f), '0')
        self.assertEqual(f._repr_str_(), 'f = 0')

        f = derive(u,'t') - div(D*grad(u))
        self.assertEqual(f([42.42, 42.42], t=42.), 0, tol=1e-20)

        # 3D closed form diffusion equation -> f = 0
        f, u, D = parse(f='derive(u,t)-D*Laplace(u)',
                        u='1/(4*pi*D*t)**(3/2)*exp(-(x²+y²+z²)/(4*D*t))',
                        D=2.0, simplify=True)

        self.assertEqual(f(1), 0)
        self.assertEqual(str(f), '0')
        self.assertEqual(f._repr_str_(), 'f = 0')

        # 3D closed form diffusion equation -> f = 0
        # some tolerance problems for uneven D, but numerical checks to 0
        # TODO Search for sympy simplifies to handle tolerance problem
        f, u, D = parse(f='derive(u,t)-D*Laplace(u)',
                        u='1/(4*pi*D*t)**(3/2)*exp(-(x²+y²+z²)/(4*D*t))',
                        D=42.0, simplify=True)
        self.assertEqual(f(1, t=1), 0, tol=1e-16)
        self.assertEqual(f(42, t=42), 0, tol=1e-16)

        f = derive(u,'t') - div(D*grad(u))
        self.assertEqual(f([42.42, 42.42, 42.42], t=42.), 0, tol=1e-20)


    def test_isStrongFormPDE(self):
        """Test strong form check.
        """
        mesh = pg.createGrid(2)
        s = ScalarSpace(mesh)
        v = VectorSpace(mesh)
        u = parse(u='x²')
        q = parse(q='x, y')
        f = asFunction('x')

        uh = FEASolution(s, values=u, name='u')
        qh = FEASolution(v, values=q, name='q')
        #### START DEBUG WORKSPACE ############################################

        dt = 0.1

        # dt = np.float64(0.1)
        # #L = s*s - dt*grad(s)*grad(s) == s*uh + dt*s*f
        L = [s - dt*laplace(s) == uh + dt*f, True]
        self.assertEqual(isStrongFormPDE(L[0]), L[1])

        #return
        #### END DEBUG WORKSPACE ##############################################

        for L in [
                    [s*s == 0, False],
                    [s*dt*s == 0, False],
                    [grad(s)*grad(s) == 0, False],
                    [s*s + dt*grad(s)*grad(s) == 0, False],
                    [s*s + dt*grad(s)*grad(s) == s*uh + dt*s*f, False],

                    [s - dt*laplace(s) == 0, True],
                    [s - dt*laplace(s) == uh + dt*f, True],
                 ]:

            try:
                self.assertEqual(isStrongFormPDE(L[0]), L[1])
                print('.', end='')

            except BaseException as e:
                pg._r('+'*80)
                pg._y('L', L[0], L[1])
                pg._r('-'*80)

                print(e)
                import traceback
                traceback.print_exc(file=sys.stdout)
                exit()


    def test_PDE(self):
        """
        """
        #### START DEBUG WORKSPACE ############################################

        mesh = pg.meshtools.createGrid(x=np.linspace(0, 1, 11))
        s = ScalarSpace(mesh, name='s')

        #### END DEBUG WORKSPACE ############################################


        # pde = derive(s, 't') +1 == Dirac() # check direction of equal operator!!!!!!
        # print(pde)
        # pde = Dirac() == derive(s, 't') +1 # check direction of equal operator!!!!!!
        # print(pde)
        # pde = derive(s, 't') == Dirac() # check direction of equal operator!!!!!!
        # print(pde)
        # pde = Dirac() == derive(s, 't') # check direction of equal operator!!!!!!
        # print(pde)

        #pde = 2.0*Laplace(s) == 0
        #pde = -f*Laplace(s) == dirac()
        #fixme!! pde = (2.0 + f)*Laplace(s) == 0
        #fixme!! print(div((2.0+f)*grad(s)).fea==0)

        #pde = derive(s, 't') - Laplace(s) == f
        #pde = -f*Laplace(s) == dirac()
        # pde = Laplace(s) - 1
        # #pde = Laplace(s) == 1
        # print(type(pde))
        # print(pde)
        # print('a:', pde.a)
        # print('b:', pde.b)
        # print(vacStr(pde))
        # # pde.dump()

        # print(pde.weakForm)


        #exit()

        pde = Laplace(s)
        self.assertEqual(vacStr(pde), 'Laplace(s)')
        self.assertEqual(vacStr(pde.weakForm), '-(grad(s)*grad(s))')

        pde = Laplace(s) == 1
        self.assertEqual(vacStr(pde), 'Laplace(s)=1')
        self.assertEqual(vacStr(pde.weakForm), '-(grad(s)*grad(s))=s*1')

        pde = Laplace(s) + 1
        self.assertEqual(vacStr(pde), 'Laplace(s)+1')
        self.assertEqual(vacStr(pde.weakForm), '-(grad(s)*grad(s))=s*-1')

        pde = Laplace(s) - 1
        self.assertEqual(vacStr(pde), 'Laplace(s)-1')
        self.assertEqual(vacStr(pde.weakForm), '-(grad(s)*grad(s))=s*1')

        # pde = -Laplace(s) == 0
        # self.assertEqual(vacStr(pde), '-Laplace(s)=0')
        # self.assertEqual(vacStr(pde.weakForm), 'grad(s)*grad(s)=s*0')

        # pde = -Laplace(s) == dirac()
        # self.assertEqual(vacStr(pde), '-Laplace(s)=dirac(r)')
        # self.assertEqual(vacStr(pde.weakForm), 'grad(s)*grad(s)=s*dirac(r)')

        # pde = -f*Laplace(s) == dirac()
        # self.assertEqual(vacStr(pde) == '-f(p)*Laplace(s)=dirac(r)', True)
        # self.assertEqual(vacStr(pde.weakForm) == 'grad(s)*f(p)*grad(s)=s*dirac(r)', True)

        pde = 2.0*Laplace(s) == 0
        self.assertEqual(vacStr(pde), '2.0*Laplace(s)=0')
        self.assertEqual(vacStr(pde.weakForm), '-2.0*grad(s)*grad(s)=s*0')
        pde = -2.0*Laplace(s) == 0
        self.assertEqual(vacStr(pde), '-2.0*Laplace(s)=0')
        self.assertEqual(vacStr(pde.weakForm), '2.0*grad(s)*grad(s)=s*0')

        a = 2.0
        pde = a*laplace(s) == 0
        self.assertEqual(vacStr(pde.weakForm), '-2.0*grad(s)*grad(s)=s*0')
        a = 2.0
        pde = -a*laplace(s) == 0
        self.assertEqual(vacStr(pde.weakForm), '2.0*grad(s)*grad(s)=s*0')

        pde = derive(s, 't') - div(a*grad(s)) == 0
        dT, L = splitDeriveTime(pde)
        self.assertEqual(vacStr(L.weakForm), 'grad(s)*2.0*grad(s)=s*0')

        pde = derive(s, 't') - a*laplace(s) == 0
        dT, L = splitDeriveTime(pde)
        self.assertEqual(vacStr(L.weakForm), '2.0*grad(s)*grad(s)=s*0')

        pde = derive(s, 't') + a*laplace(s) == 0
        dT, L = splitDeriveTime(pde)
        self.assertEqual(vacStr(L.weakForm), '-2.0*grad(s)*grad(s)=s*0')


        # pde =(2.0 + f)*Laplace(s) == 0
        # self.assertEqual(vacStr(pde) == '(2.0+f(p))*Laplace(s)=0', True)
        # self.assertEqual(vacStr(pde.weakForm) == 'grad(s)*f(p)*grad(s)=s*dirac(r)', True)


if __name__ == '__main__':
    import unittest
    pg.tic()
    unittest.main(exit=False)
    print()

    pg.info(f'Absolut tests: {testCount()}, took {pg.dur()} s')
