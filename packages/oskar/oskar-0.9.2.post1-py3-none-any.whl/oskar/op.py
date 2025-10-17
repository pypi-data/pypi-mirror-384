#!/usr/bin/env python
"""Generic mathematical operators for the FEA framework."""

from itertools import repeat
import numpy as np
import pygimli as pg

from . utils import isVecField, asPosListNP, asVecField


def findInstance(op, cls):
    """Recursive search for an instance of type Class in this expression."""
    if isinstance(op, cls):
        return op
    a = None
    b = None
    if hasattr(op, 'a'):
        a = findInstance(op.a, cls)

        ## Refactor me after SolutionGrad works
        from .feaSpace import ScalarSpace, VectorSpace
        if isinstance(a, ScalarSpace | VectorSpace) and \
            hasattr(op, '_solutionGrad') and op._solutionGrad is True:
            return None

    if hasattr(op, 'b'):
        b = findInstance(op.b, cls)
    return a or b


def hasInstance(op, cls):
    """Recursive search if the expression has an instance of type Class."""
    return findInstance(op, cls) is not None


def hasOP(op, opStr):
    """Recursive search if the expression has the operator string op."""
    if hasattr(op, 'op') and op.op == opStr:
        return True
    a = None
    b = None
    if hasattr(op, 'a'):
        a = hasOP(op.a, opStr)

    if hasattr(op, 'b'):
        b = hasOP(op.b, opStr)
    return a or b


def factorizeOP(op, ret=None):
    """Return list of all factors."""
    if ret is None:
        ret = []

    if not hasattr(op, 'op'):
        ret.append(op)
        return ret

    if hasattr(op, 'op') and op.b is None:
        ret.append(op)
        return ret

    ret = factorizeOP(op.a, ret)
    ret = factorizeOP(op.b, ret)

    return ret


def splitOP(op, opStr):
    """Recursive search the expression and extract the part with opStr."""
    facts = factorizeOP(op)
    a = None
    b = None

    for f in facts:
        if hasattr(f, 'op') and f.op == opStr:
            b = f
        else:
            if a is None:
                a = f
            else:
                a *= f

    return a, b


def atoms(op):
    """Return a list of all atoms in the expression."""
    if not hasattr(op, 'op'):
        return [op]

    if hasattr(op, 'op') and op.b is None:
        return atoms(op.a)

    ret = []
    ret.extend(atoms(op.a))
    ret.extend(atoms(op.b))
    return ret


class OP(pg.core.FEAFunction):
    """Base class for Expression Operators.

    TODO:
        * mixed continuous binary operators

    Attributes
    ----------
    valueSize: int(i)
        Expected size of evaluated values, 1 for R1 and 3 for functions in R3.
    evalOrder:
        Flag to determine if any entity based evaluation
        returns per quadrature (True) values or a value
        per entity center (False).

        Binary operators set the continuous property to false if at
        least one of the sub functions are not continuous.
    """

    # to allow for: np.ndarray * OP
    __array_ufunc__ = None

    def __init__(self, a=None, b=None, op=None, **kwargs):
        """Initialize an operator.

        Parameters
        ----------
        a: OP
            Left operand.
        b: OP
            Right operand.
        op: str
            Operator string.

        Keyword Args
        ------------
        valueSize: int(1)
            Expected size of evaluated values, 1 for R1 and 3 for
            functions in R3.
        """
        self._op_priority = 99999 ### higher priority than sympy operators
        self._OP = kwargs.pop('OP', OP)
        # f.evalOrder == 0: at Cell center
        # f.evalOrder == 1: at Nodes
        # f.evalOrder == 2: at Quads (default and fallback)
        super().__init__(valueSize=kwargs.pop('valueSize', 1),
                         evalOrder=kwargs.pop('evalOrder', 2))

        ## set them first and check them later again, I(self) need them maybe
        self.a = a
        self.b = b
        self._mesh = None

        def _testForCallable(c):

            if isinstance(c, type) and c.__name__ == 'I' :
                ## special case for c is identity class -> create instance ofI()
                #pg._r(self, b)
                from .mathOp import I
                return I(self)

            from . feaFunction import FEAFunction, FEAFunction3

            if (callable(c)
                and not isinstance(c, OP)
                and not isinstance(c, Constant)):

                try:
                    #r = c([0.0, 0.0, 0.0])
                    # simpler test if 0.0 is interpreted as [0.0, 0.0, 0.0]
                    # e.g. this will work then also for lambda x: x
                    r = c(0.0)
                    if pg.isScalar(r):
                        return FEAFunction(c)
                    if pg.isPos(r):
                        return FEAFunction3(c)
                except BaseException:
                    return FEAFunction(c)
                    #r = c([0.0, 0.0, 0.0], )

                print(r)
                print(c)
                pg.critical("Cannot convert callable to FEAFunction")

            return c

        self.a = _testForCallable(a)
        self.b = _testForCallable(b)
        self.op = op
        self._mulR = 1.0

        # pg._g('a:', a)
        # pg._y('self.a:', self.a)
        # pg._g('b:', b)
        # pg._y('self.b:', self.b)

        if hasattr(self.a, 'evalOrder'):
            # pg._a(f' a {self.a} evalOrder:', self.a.evalOrder)
            self.evalOrder = self.a.evalOrder
        if hasattr(self.b, 'evalOrder'):
            # pg._b(f' b {self.b} evalOrder:', self.b.evalOrder)
            self.evalOrder = self.b.evalOrder


        if hasattr(self.a, 'valueSize') and hasattr(self.b, 'valueSize'):
            if self.a.valueSize() != self.b.valueSize():
                # print(self, self.valueSize())
                # print('a', self.a, self.a.valueSize())
                # print('op', self.op)
                # print('b', self.b)
                self.setValueSize(max(self.a.valueSize(), self.b.valueSize()))
                #pg.critical(fix me)
        elif hasattr(self.a, 'valueSize'):
            self.setValueSize(self.a.valueSize())
        elif hasattr(self.b, 'valueSize'):
            self.setValueSize(self.b.valueSize())

        self._ops = {'+': '__add__',
                     '-': '__sub__',
                     '*': '__mul__',
                     '/': '__truediv__'}

        self._kwargs = kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    # def __setattr__(self, name, value):
    #     pg._r(name, value)

    #     print(self.__dict__)
    #     super(OP, self).__setattr__(name, value)
    #     #exit()


    def __reduce__(self):
        """Pickle function."""
        return (type(self), (), self.__dict__.copy())


    def __call__(self, *args, **kwargs):
        """Evaluate the operator with given arguments."""
        return self.eval(*args, **kwargs)


    def __hash__(self):
        """Hash for FEAOP."""
        from pygimli.utils.cache import valHash

        hsh = valHash(str(self))
        #pg._y(self)
        at = atoms(self)
        for a in at:
            hsh = hsh ^ valHash(a)
            #pg._g(str(type(a)), valHash(a))

        return hsh


    def evalR1(self, *args, **kwargs):
        """Evaluate the operator in R1."""
        # pg._g(*args, kwargs)
        return self.eval(*args, **kwargs)


    def evalR3(self, *args, **kwargs):
        """Evaluate the operator in R3."""
        return self.eval(*args, **kwargs)


    def evalRM(self, *args, **kwargs):
        """Evaluate the operator in R3 for matrices."""
        return self.eval(*args, **kwargs)


    @property
    def evalOrder(self):
        """Get the evaluation order."""
        return super().getEvalOrder()


    @evalOrder.setter
    def evalOrder(self, o):
        """Set the evaluation order."""
        ## TODO: check if this is needed, some tests fail with this
        # def _se(op, o):
        #     """Set the evaluation order for the operator."""
        #     if hasattr(op, 'setEvalOrder'):
        #         op.setEvalOrder(o)
        #
        #     if hasattr(op, 'a'):
        #         _se(op.a, o)
        #     if hasattr(op, 'b'):
        #         _se(op.b, o)
        #
        # _se(self, o)
        self.setEvalOrder(o)


    @property
    def evalOnCells(self):
        """Check if the operator is evaluated on cells.

        Same like evalOrder == 0.
        """
        return self.evalOrder() == 0


    @evalOnCells.setter
    def evalOnCells(self, v):
        """Set the evaluation order to cells.

        Set evalOrder to 0 if v is True or to 2(continuous) otherwise.
        """
        if v is True:
            self.evalOrder = 0
        else:
            self.evalOrder = 2


    @property
    def evalOnNodes(self):
        """Check if the operator is evaluated on nodes.

        Return True is evalOrder is 1.
        """
        return self.evalOrder() == 1


    @evalOnNodes.setter
    def evalOnNodes(self, v):
        """Set the evaluation order to nodes.

        Set evalOrder to 1 if v is True or to 2(continuous) otherwise.
        """
        if v is True:
            self.evalOrder = 1
        else:
            self.evalOrder = 2


    @property
    def evalOnQuads(self):
        """Check if the operator is evaluated on quadrature points."""
        return self.evalOrder() == 2


    @evalOnQuads.setter
    def evalOnQuads(self, v):
        """Set the evaluation order to quadrature points.

        Set evalOrder to 2 if v is True or to 0(cells) otherwise.
        """
        if v is True:
            self.evalOrder = 2
        else:
            self.evalOrder = 0


    @property
    def mesh(self):
        """Search recursive for a mesh."""
        if self._mesh is not None:
            return self._mesh
        if hasattr(self.a, 'mesh'):
            return self.a.mesh
        elif hasattr(self.b, 'mesh'):
            return self.b.mesh
        return None


    @mesh.setter
    def mesh(self, m):
        """Set mesh for this operator."""
        self._mesh = m


    @property
    def mulR(self):
        """Get the multiplication factor."""
        return self._mulR


    @mulR.setter
    def mulR(self, m):
        """Set the multiplication factor."""
        if m != 1:
            self._mulR = self._mulR * m
            if self.op == '+' or self.op == '-':
                pass
                # double mul here -- (A+B)*m != A*m + B*m since A+B not unique
                # self.a.mulR = self.a.mulR * m
                # self.b.mulR = self.b.mulR * m
            else:
                try:
                    self.a.mulR = self.a.mulR * m
                except BaseException:
                    pass


    # to protect for sum but it gives recursion problem ... need check!
    # def __iter__(self):
    #     pg.critical("you don't want this")


    def dump(self, node=None, indent=0):
        """Dump operator tree.

        Debugging function to visualize the OP tree.
        Called recursive.

        Attributes
        ----------
        node: OP[None]
            If None, show the OP itself.

        indent: int[0]
            Indentation for better visuals, filled recursively.
        """
        if node is None:
            node = self

        if isinstance(node, OP):
            if node.b is not None:
                # a OP b
                print(f"{'.'*indent*4}{pg._(node.a, c='g')} "
                      f"{pg._(node.op, c='r')} {pg._(node.b, c='y')}")
                # error: node
                if node.a is None:
                    pg._r(f'{node} {type(node)}')
                else:
                    # -> a
                    self.dump(node.a, indent=indent + 1)
                # -> b
                self.dump(node.b, indent=indent + 1)

            elif node.op is not None:
                # OP(a)
                print(f"{'.'*indent*4}{pg._(node.op, c='r')} "
                      f"({pg._(node.a, c='g')}) {type(node)}")
                if node.a is None:
                    # error: node
                    pg._r(f'{node} {type(node)}')
                else:
                    # -> a
                    self.dump(node.a, indent=indent + 1)
            else:
                print(f"{'.'*indent*4}{pg._(node, c='b')} {type(node)}")
        else:
            print(f"{'.'*indent*4}{pg._(node, c='b')} {type(node)}")

        # if node is None:
        #     node = self

        # print(f'{" "*indent}{node}')

        # if hasattr(node, 'a') and node.a is not None:
        #     print(f'{" "*indent}a:{node.a}')
        #     self.dump(node=node.a, indent=indent+4)

        # if hasattr(node, 'op'):
        #     print(f'{" "*indent}OP:{node.op}')

        # if hasattr(node, 'b') and node.b is not None:
        #     print(f'{" "*indent}b:{node.b}')
        #     self.dump(node=node.b, indent=indent+4)

    @staticmethod
    def bubbleUpNeg(term):
        """Bubble up negation operator."""
        from .feaFunction import FEANegFunction

        # pg._b(term, hasattr(term, 'neg') and term.neg
        #       or hasattr(term, 'op') and term.op == 'neg')
        if term is None:
            return None

        if hasattr(term, 'op'):
            term.a = OP.bubbleUpNeg(term.a)
            term.b = OP.bubbleUpNeg(term.b)

        if hasattr(term, 'op') and term.op == 'pow':
            if term.exponent == 0:
                return 1.0
            if term.exponent == 1:
                return term
            elif term.exponent == 2:
                if isinstance(term.a, OP) and term.a.op == 'neg' or\
                    isinstance(term.a, FEANegFunction):
                    return (-term.a)**2
            else:
                return term
                #pg.critical(f'Implement me. {term.a}, pow {term.exponent}')

        if (hasattr(term, 'op')
            and (term.op == 'div' or term.op == 'grad')
            and (hasattr(term.a, 'op') and term.a.op == 'neg'
                 or isinstance(term.a, FEANegFunction))):

            return -term._OP(term.a.a, term.b, term.op)

        if (hasattr(term, 'op')
            and (term.op=='*' or term.op=='/')
            ## a * -(b) -> -(a*b)
            and (isinstance(term.b, OP) and term.b.op == 'neg' or \
                isinstance(term.b, FEANegFunction))):

            return -term._OP(term.a, -term.b, term.op)

        return term


    def expandTerm(self, term=None, **kwargs):
        """Expand expression and return list of sub terms.

        Arguments
        ---------
        forSpaces: bool[False]
            Don't expand parts that does not contain any FEASpaces.
            These not expanded parts will be evaluated as they are.
            So they are suitable for FEA assembling which
            only depends on FEASpaces.
        splitSolutionOPWithFuncs: bool[False]
            If True, split FEASolutionOP that contains any FEAFunctions.
        """
        from .feaSolution import FEASolutionOP
        from . feaFunction import FEAFunction

        if term is None:
            term = self

        def isSingle(term, **kwargs):
            """Check if term is a single term.

            forSpaces: bool
                If True, check for FEASpaces and return True if
                term does not contain FEASpaces.
            """
            if isinstance(term, FEASolutionOP):
                return not \
                    (kwargs.get('splitSolutionOPWithFuncs', False) is True
                        and hasInstance(term, FEAFunction))

                #     return False
                # return True

            if kwargs.get('forSpaces', False) is True:
                from . feaSpace import FEASpace
                #from . feaOp import FEAOP

                # if isinstance(term, FEAOP):
                #     if term._solutionGrad == True:
                #         return True
                # else:
                if not hasInstance(term, FEASpace):
                    return True


            if not hasattr(term, 'op') or term.op is None:
                ### scalar | FEAFunction | FEASolution
                return True
            if term.b is None and isSingle(term.a, **kwargs):
                ### OP(single)
                return True

            return (isSingle(term.a, **kwargs)
                    and isSingle(term.b, **kwargs)
                    and (term.op == '*' or term.op == '/'))

        #pg._b(term, 'isSingle:', isSingle(term, **kwargs))

        if isSingle(term, **kwargs):
            return [OP.bubbleUpNeg(term)]
            #return [term]

        if term.op == '+':
            #pg._g('\t+\t',term)
            ta = self.expandTerm(term.a, **kwargs)
            tb = self.expandTerm(term.b, **kwargs)
            #pg._y('\t ta ',ta)
            #pg._y('\t tb ',tb)
            for b in tb:
                ta.append(b)
            return ta

        if term.op == '-' or term.op == '==':
            #pg._g('\t-\t',term)
            ta = self.expandTerm(term.a, **kwargs)
            tb = self.expandTerm(term.b, **kwargs)
            #pg._y('\t ta-1 ',ta)
            for b in tb:
                #pg._g('\t b ', b, type(b))
                ta.append(-b)
            #pg._y('\t ta-2 ',ta)
            return ta

        if term.op == '*':
            ta = self.expandTerm(term.a, **kwargs)
            tb = self.expandTerm(term.b, **kwargs)
            r = []
            # pg._g(ta)
            # pg._y(tb)
            for a in ta:
                for b in tb:
                    #pg._g(type(a), a)
                    #pg._y(type(b), b)
                    # if hasattr(b, 'op') and b.op == 'neg':
                    #     r.append(-(a*b.a))

                    if pg.isScalar(b):
                        r.append(b*a)
                    else:
                        r.append(a*b)
            return r

        if term.op == '/':
            ta = self.expandTerm(term.a, **kwargs)
            tb = self.expandTerm(term.b, **kwargs)
            r = []
            for a in ta:
                for b in tb:
                    r.append(a/b)
            return r

        if term.op == 'pow':
            if term.exponent == 2:
                ta = self.expandTerm(term.a, **kwargs)

                if len(ta) == 2:
                    return [ta[0]**2, 2*ta[0]*ta[1], ta[1]**2]
                else:
                    pg.critical(f'Implement me. {ta}, pow {term.exponent}')
            else:
                return [term]
                #pg.critical(f'Implement me. {term.a}, pow {term.exponent}')

        if term.op == 'div':
            ## TODO product rule: div(u V) = u*div(V) + <grad(u),V>
            from .mathOp import div
            #pg._b(term)
            ta = self.expandTerm(term.a, **kwargs)
            #pg._b(ta)
            r = []
            for a in ta:
                a = OP.bubbleUpNeg(a)
                #pg._b(a)
                if hasattr(a, 'op') and a.op == 'neg':
                    if 1 and term.neg is True:
                        #pg._g('neg', a.a)
                        r.append(div(a.a))
                    else:
                        r.append(-div(a.a))
                elif term.neg is True:
                    r.append(-div(a))
                else:
                    r.append(div(a))

            return r

        if term.op == 'neg':
            terms = self.expandTerm(term.a, **kwargs)
            for t in terms:
                t *= -1
            return terms

        if term.op == 'abs':
            return [term]

        pg.critical(f"can find term for: {isSingle(term, **kwargs)},"
                    f"{term}")


    def expand(self, removeDiv:bool=False, combineScalars:bool=True,
               sortSigns:bool=True, **kwargs):
        """Expand operator expression into a list of single terms.

        Arguments
        ---------
        removeDiv: bool[False]
            Remove any division operators by simple multiply with
            the quotients.

        Keyword Args
        ------------
        **kwargs
            Will be forwarded to :py:mod:`oskar.op.OP.expandTerm`.
        """
        terms = self.expandTerm(self, **kwargs)

        if removeDiv is True:
            for t in terms:
                #pg._b(t)
                if hasattr(t, 'op') and t.op == '/' and pg.isScalar(t.b):
                    ##[x, b/c, y] -> [x, b/c, y]*c
                    terms = (self*t.b).expand()

        if sortSigns is True:
            for i, t in enumerate(list(terms)):
                terms[i] = OP.bubbleUpNeg(t)

        # removeZero = True
        ## zero might be needed!
        # if removeZero is True:
        #     for i, t in enumerate(list(terms)):
        #         if t is 0 or t is 0.0:
        #             pg._r(i, t)
        #             del terms[i]

        if combineScalars is True:
            def isOne(a, b, op):
                if op == '*':
                    try:
                        if pg.isScalar(a * b, 1.0):
                            return True
                    except BaseException:
                        pass
                if op == '/':
                    try:
                        if pg.isScalar(a / b, 1.0):
                            return True
                    except BaseException:
                        pass

                return False

            for i, t in enumerate(list(terms)):
                if hasattr(t, 'op') and t.op == '*':
                    try:
                        if isOne(t.a, t.b.a, '*'):
                            terms[i] = t.b.b
                    except BaseException:
                        pass

                    try:
                        #pg._g(t.a, t.b.b, isOne(t.a, t.b.b, t.b.op))
                        if isOne(t.a, t.b.b, t.b.op):
                            terms[i] = t.b.a
                    except BaseException:
                        pass

        return terms


    def __str__(self):
        """Return string representation."""
        if self.a is None:
            return f'{self.b}'
        elif self.b is None:
            if self.op in ['+', '-', '*', '/']:
                return f'{self.a}'
            if self.op is None:
                if hasattr(self.a, 'name'):
                    return f'!#name#!{self.a}'
                return f'{self.a}'
            if self.op == 'pow':
                if hasattr(self.a, 'b') and self.a.b is not None:
                    return f'({self.a})^{self.exponent}'
                return f'{self.a}^{self.exponent}'
            if self.op == 'neg':
                if not hasattr(self.a, 'b'):
                    return f'-{self.a}'
                return f'-({self.a})'
            if self.op == 'identity':
                return 'I'
            return f'{self.op}({self.a})'
        else:
            a = self.a
            b = self.b
            if self.op == '*' or self.op == '/':
                if hasattr(self.a, 'op') and \
                    (self.a.op == '+' or self.a.op == '-'):
                    a = f'({self.a})'
                if hasattr(self.b, 'op') and \
                    (self.b.op == '+' or self.b.op == '-'):
                    b = f'({self.b})'

            if self.op == '==':
                return f'{a} = {b}'

            if self.op == '*' or self.op == '/':

                from . elasticity import ElasticityMatrix

                if isinstance(a, list | np.ndarray):
                    if isinstance(a[0], ElasticityMatrix):
                        a = '[C]'
                    elif pg.isPos(a[0]):
                        a = '[v3]'
                    elif pg.isScalar(a[0]):
                        a = '[d]'
                    else:
                        a = '[...]'
                if isinstance(b, list | np.ndarray):
                    b = '[...]'
                return f'{a}{self.op}{b}'

            return f'{a} {self.op} {b}'


    def __repr__(self):
        """Return string representation."""
        # pg._b(str(self))
        return str(self)


    def _getOP(self, b):
        """Get the current operator class for the given b."""
        #TODO ugly .. refactor me!
        from .solve import PDE
        from .feaSpace import FEASpace
        from .feaOp import FEAOP

        if isinstance(b, (PDE)):
            return PDE
        if isinstance(b, FEASpace | FEAOP):
            return FEAOP
        return self._OP


    def __eq__(self, b):
        """Compare two operators."""
        #pg._y('OP.eq', self, '==', b) #refactor OP
        return self._OP(self, b, '==')


    def __add__(self, b):
        """OP + XX."""
        # print (self, '+', b)
        from . feaSolution import FEASolution
        if isinstance(b, FEASolution):
            return b.__radd__(self)
        return self._OP(self, b, '+')


    def __radd__(self, b):
        """XX + OP."""
        # pg._r('OP.rmul', b, self)
        return self._OP(b, self, '+')


    def __sub__(self, b):
        """OP - XX."""
        #pg._b('OP.sub:', self._OP, b, self)
        from . feaSolution import FEASolution
        if isinstance(b, FEASolution):
            return b.__rsub__(self)
        return self._OP(self, b, '-')


    def __rsub__(self, b):
        """XX - OP."""
        #pg._b('OP.rsub:', self._OP, b, self)
        return self._OP(b, self, '-')


    def __mul__(self, b):
        """OP * XX."""
        #pg._b(self, 'mul', b) #refactor OP
        _OP = self._getOP(b)

        from . feaSolution import FEASolution, FEASolutionOP

        if isinstance(self, FEASolution | FEASolutionOP):
            return _OP(self, b, '*')

        from .mathOp import I

        if isinstance(b, I):
            ## special case for b is instance of identity class -> forward to I
            #pg._y(self, b)
            return b.__mul__(self)
        if isinstance(b, type) and b.__name__ == 'I' :
            ## special case for b is identity class ->
            # create instance and forward to I()
            #pg._r(self, b)
            return I(self).__mul__(self)

        # pg._b(f'OP.mul:\n \ta: {self}, {type(self)}, OP:{self._OP} \n'
        #       +f'\tb: {b}, {type(b)}, OP:{OP}')

        if pg.core.deepDebug() == -1:
            pg._g(_OP, self, '*', b)

        #pg._g(self, 'mul', b) #refactor OP
        return _OP(self, b, '*')


    def __rmul__(self, b):
        """XX * OP."""
        #pg._b(self, 'rmul', b) #refactor OP
        from .mathOp import I
        if isinstance(b, I) or (isinstance(b, type) and b.__name__ == 'I'):
            return self.__mul__(b)

        # pg._b(f'OP.rmul:\n \ta: {self}, {type(self)}, OP:{self._OP} \n'
        #       +f'\tb: {b}, {type(b)}, OP:{OP}')

        _OP = self._getOP(b)

        if pg.core.deepDebug() == -1:
            pg._g(_OP, b, '*', self)

        return _OP(b, self, '*')

        # pg._r('OP.rmul', b, self)
        #return self._OP(b, self, '*')


    def __matmul__(self, b):
        """OP @ XX."""
        #print(self, '*', b)
        return self._OP(self, b, '@')


    def __truediv__(self, b):
        """OP / XX."""
        #pg._b(self, 'truediv', b)
        if pg.isScalar(b):
            return (1.0/b) * self
        return self._OP(self, b, '/')


    def __rtruediv__(self, b):
        """XX / OP."""
        #pg._b(self, 'rtruediv', b)
        return self._OP(b, self, '/')


    def __abs__(self):
        """Absolute value operator."""
        return self._OP(self, op='abs')


    def __pow__(self, exponent):
        """OP ** exponent."""
        #pg._b(f'POW: {self}, exponent: {exponent}')
        return self._OP(self, op='pow', exponent=exponent)


    def __neg__(self):
        """Negation operator."""
        # pg._b(f'NEG: {self}, {type(self)}, self._OP: {self._OP}')
        if hasattr(self, 'op') and self.op == 'neg':
            return self.a

        if hasattr(self, 'op') and self.op == '*'and pg.isScalar(self.a):
            return -self.a * self.b

        from . feaSpace import FEASpace
        from . feaOp import FEAOP

        if isinstance(self, FEASpace | FEAOP):
            if pg.core.deepDebug() == -1:
                pg._g('FEAOP', self, 'neg')
            return FEAOP(self, op='neg')

        if pg.core.deepDebug() == -1:
            pg._g(self._OP, self, 'neg')
        return self._OP(self, op='neg')


    @property
    def T(self):
        """Transpose operator."""
        #temporary property to allow transpose mul
        return self


    def tr(self):
        """Return OP with tr(OP)."""
        return self._OP(self, op='tr')


    def abs(self):
        """Return OP with abs(OP)."""
        return self._OP(self, op='abs')


    def sqrt(self):
        """Return OP with sqrt(OP)."""
        return self._OP(self, op='sqrt')


    def exp(self):
        """Return OP with exp(OP)."""
        return self._OP(self, op='exp')


    def identity(self):
        """Return OP with identity(OP)."""
        #Refactor with space"
        # pg._r('OP-identity', self._OP)
        return self._OP(self, op='identity')


    def derive(self, v):
        """Return OP with derive(OP, v)."""
        return self._OP(self, op='derive', var=v)


    def grad(self):
        """Return OP with grad(OP)."""
        return self._OP(self, op='grad')


    def div(self):
        """Return OP with div(OP)."""
        return self._OP(self, op='div')


    def laplace(self):
        """Return OP with laplace(OP)."""
        return self._OP(self, op='laplace')


    def integrate(self, ent, order=1, **kwargs):
        """Integrate the OP for an entity or list of entities."""
        if isinstance(ent, pg.core.Mesh):
            from . feaSpace import ScalarSpace
            space = ScalarSpace(ent, order=order)
            #return sum((space*self).assemble(useMats=True))
            return sum((space*self).assemble(core=True))
            #return self.integrate(ent.cells(), order=order)

        if hasattr(ent, '__iterate__'):
            return sum([self.integrate(e, order=order, **kwargs) for e in ent])

        if isinstance(ent, pg.core.MeshEntity):
            from . elementMats import uE
            E = uE(ent, f=self, scale=1.0, order=order,
                   nCoeff=1, dofPerCoeff=0, dofOffset=0,
                   mesh=None, core=False)
            return sum(E.mat())[0]

        pg.critical(f'implement me entity={ent}')


    def hasDeriveT(self):
        """Check if this expression has a time derivative operator."""
        from . feaOp import Derive
        op = findInstance(self, Derive)
        if hasattr(op, '_v'):
            return op._v == 't'
        return False


    @staticmethod
    def evalTerm(a, *args, **kwargs):
        """Eval single Term until values reached."""
        from .elasticity import ElasticityMatrix


        if pg.isScalar(a) or pg.isPos(a):
            return a

        p = args[0] if len(args) > 0 else None

        if hasattr(a, '__iter__') and 'mesh' in kwargs:
            # a is cellArray
            m = kwargs.pop('mesh', None)
            if m is not None and len(a) == m.cellCount():
                if isinstance(p, pg.core.stdVectorR3Vector):
                    if isinstance(a[0], ElasticityMatrix) \
                        or (pg.isMatrix(a[0])
                            and a[0].shape[0] == a[0].shape[1]):

                        ## a is list[C] -> Return Matrix for each quad pnts
                        ##              -> [ [C_i,], ]_cells
                        ret = pg.core.stdVectorRDenseMatrixVector()

                        for j, pj in enumerate(p): ## for each cell_j
                            rv = pg.core.stdVectorRDenseMatrix()
                            for _ in repeat(None, len(pj)):
                                rv.append(a[j])
                            ret.append(rv)

                        return ret
                    else:
                        return a
                        # print(a)
                        # print(a[0])
                        # print(p)
                        # pg.critical('implement me for p as stdVectorR3Vector')
                else:
                    return np.asarray([a[m.findCell(_p).id()]
                                    for _p in asPosListNP(p)])

        if isinstance(a, ElasticityMatrix) \
            or (pg.isMatrix(a) and a.shape[0] == a.shape[1]):
            return a

        if pg.isArray(a) and \
            (isinstance(p, pg.core.stdVectorR3Vector) and len(a) == len(p)):
            return a

        if isVecField(a) and p is None:
            return asVecField(a)

        if isinstance(a, np.ndarray) and p is None:
            return asVecField(a)

        if pg.isArray(a):# and p is None:
            #pg._y(a)
            return np.asarray(a)
            # if isinstance(a, list):
            # return a

        # if isinstance(a, np.ndarray):
        #     return a

        elif isinstance(a, OP):
                # pg._g('a:', a)
                # pg._g('p:', p)
                # pg._g('kwargs', kwargs)
                # pg._g(a.eval(p))

            ret = a.eval(*args, **kwargs)

            if isinstance(ret, list):
                return np.asarray(ret)
            return ret

        elif isinstance(a, pg.core.ElementMatrix):
            from . elementMats import copyE

            if a.mulR is not None and a.mulR != 1:
                ret = copyE(a)
                ret *= a.mulR
                ret._mat[:] *= a.mulR
                return ret
            return a

        elif isinstance(a, Constant):
            return a(a.mesh.dim())

        elif a is None:
            return None

            #return None

        pg._r('_'*40)
        print('a',type(a))
        print('a', a.shape)
        print('p', p)
        print('p', len(p))
        print('p', hasattr(p, '__iter__'))

        pg.critical('cannot evaluate at p')


    def eval(self, *args, **kwargs):
        """Evaluate OP for points."""
        if pg.core.deepDebug() == -1:
            pg._y('*'*60)
            pg._y('** OP eval')
            pg._y(f'** \tA: {type(self.a)}')
            pg._y('\n{self.a}')
            pg._y(f'** \tOP: {self.op}\n')
            pg._y(f'** \tB: {type(self.b)}')
            pg._y('\n{self.b}')
            pg._y('at:', args, kwargs)
            pg._y('*'*60)


        if isinstance(self.a, pg.core.ElementMatrixMap):
            if self.op == '+':
                from . elementMats import createEMap

                r = createEMap(f'{self.a}+{self.b}', self.a.space)
                # pg._b(kwargs)
                with pg.tictoc('map + map'):
                    self.a.add(self.b, r, dim=kwargs.pop('dim', 1), b=1.0)

                return r
            else:
                print(self)
                print(self.a)
                print(self.op)
                print(self.b)

                pg.critical('implement me')

        elif isinstance(self.a, pg.core.ElementMatrix) and 1:
            # pg._r('000000000')
            # pg._g(self)
            from . elementMats import copyE, isRefImpl, setMat, _fillMatX

            retA = copyE(self.a)
            if self.op == '+':
                retB = copyE(self.b)

                # pg._r('-------------')
                # pg._g(retA)
                # pg._g(retB)
                # pg._r('-------------')

                if isRefImpl(self.a):

                    if retA._mat.shape == retB._mat.shape:
                        retA += retB
                        retA._mat += retB._mat
                    else:
                        if 'dim' in kwargs and kwargs['dim'] == 1:
                            ## eval with requested for 1-dim result
                            ## (u + v) * u
                            ## A or B is grad and need to be summed (div)
                            retA._mat = \
                                np.sum(retA._mat, axis=1, keepdims=True) + \
                                np.sum(retB._mat, axis=1, keepdims=True)

                            # for i, m in enumerate(retA._mat):
                            #     print('A2:', m)

                            # retA._mat = retA._mat + retB._mat
                            retA.resize(retA.rows(), kwargs['dim'])
                        else:
                            ## eval with requested x-dim result
                            ## (u + v) * v
                            ## A or B is grad and need add per dimension
                            retA._mat = retA._mat + retB._mat

                            retA.resize(retA.rows(),
                                        max(retA.cols(), retB.cols()))

                        setMat(retA, np.tensordot(retA._mat,
                                            retA._w * retA.entity().size(),
                                            axes=(0,0)).T, 'eval')
                        retA.integrated(True)
                        # print(retA)
                else: # core = True
                    retA.add(retB, dim=kwargs.pop('dim', 0), b=1.0)

                _fillMatX(retA)
                retA.mulR = self.mulR
                #print(retA)
                from .elementMats import _applyMulR
                retA = _applyMulR(retA)

                #pg._r(retA)
                # pg._r(retA.order())
                # pg._r('==============')

                return retA

            print(self)
            print(self.a)
            print(self.op)
            print(self.b)

            pg.critical('implement me')

        # pg._y()

        # if len(args) > 0:
        #     p = args[0]
        # else:
        #     p = None
        #     # print(self)
        #     # print('*args', args)
        #     # print('*kwargs', kwargs)
        #     # pg.critical('cannot evaluate for args')

        #pg._y(self.mesh)
        if self.mesh is not None:
            kwargs['mesh'] = self.mesh
        a = self.evalTerm(self.a, *args, **kwargs)
        b = self.evalTerm(self.b, *args, **kwargs)

        if pg.core.deepDebug() == -1:
            pg._g(f'a={a}')
            pg._y(f'b={b}')

        try:
            if self.op == 'neg':
                return -a

            if self.op == 'abs':
                # pg._b(a)
                return pg.abs(a)

            elif self.op == 'pow':
                if 1 and self.exponent == 2:
                    #pg._r(type(a), a.shape)
                    if isinstance(a, pg.core.stdVectorR3Vector):
                        # ret = pg.core.stdVectorRVector()
                        # pg.core.dot(a, a, ret)
                        return a*a
                        #return ret

                    if isinstance(a, pg.core.stdVectorRMatrix):
                        # return Frobenius norms [M*M, ] -> [<M,M>, ]
                        ret = pg.core.RVector()
                        pg.core.dot(a, a, ret)
                        return ret
                        #return ret

                    if pg.isPosList(a):
                        try:
                            return np.sum(a*a, axis=2)
                        except BaseException:
                            # for a is (2x2) matrix
                            return np.sum(a*a)

                    if pg.isPos(a):
                        return (a*a).sum()

                return np.power(a, self.exponent)
            elif self.op == 'exp':
                # TODO test to refactor with the next!!
                return np.exp(a)
            elif isinstance(self.op, np.ufunc):
                return self.op(a)

            elif self.op == '[]':
                # idx = self._kwargs['idx']
                # idx = self.idx
                return a[self.idx]
            elif self.op == '*':
                try:
                    if 0 and pg.isPos(a) and pg.isPos(b):
                        pg.warning('in use?')
                        return np.sum(a*b)

                    if 0 and pg.isPosList(a) and pg.isPosList(b):

                        pg.warning('in use?')
                        pg.error('check if result should be dot(a, b)')
                        return np.sum(a*b, axis=2)

                    elif 0 and isinstance(a, pg.core.stdVectorR3Vector) and \
                        isinstance(b, pg.core.stdVectorR3Vector):

                        pg.critical('in use?')
                        ret = pg.core.stdVectorRVector()
                        pg.core.dot(a, b, ret)
                        return ret
                        #pg._b('check!!')
                        #return np.sum(a*b, axis=2)

                    return a * b
                except BaseException as e:
                    pg.critical('in use?')
                    print(e)
                    if len(a) == len(b):
                        ## can this be nicer? mul: e.g. (4,) * (4,3)
                        return np.squeeze(
                            np.asarray([[a[i]*b[i]] for i in range(len(a))]))
                    else:
                        return (a.T * b).T
            elif self.op == '/':
                try:
                    return a / b
                except BaseException:
                    if len(a) == len(b):
                        ## can this be nicer? mul: e.g. (4,) * (4,3)
                        return np.squeeze(
                            np.asarray([[a[i] / b[i]] for i in range(len(a))]))

            elif self.op == '+':
                # pg._g(a)
                # pg._y(b)
                return a + b
            elif self.op == '-':
                # pg._b(a)
                # pg._b(b)
                return a - b

            pg.critical('not yet implemented')

        except Exception as e:
            pg._r(self)
            print('self:', self)
            print('self.a:', type(self.a), self.a)
            print('self.OP:', self.op)
            print('self.b', type(self.b), self.b)
            print('a:', type(a), a)
            print('b:', type(b), b)

            import traceback
            traceback.print_exc()
            print(e)

        return 0.0


    def iSubst(self, **kwargs):
        """Inline substitution of expressions with kwargs."""
        if self.b is None:
            return self.b

        if isinstance(self.a, OP):
            self.a.iSubst(**kwargs)

        if isinstance(self.b, OP):
            self.b.iSubst(**kwargs)

        return self


class Constant(OP):
    """Constant operator class."""

    def __init__(self, name='Const'):
        self._name = name
        super().__init__(OP=OP)

    def __str__(self):
        """Return string representation."""
        return self._name

    def __repr__(self):
        """Return string representation."""
        # pg._b(str(self))
        return str(self)


class Direction(Constant):
    """Direction operator class."""

    def __init__(self, d, name='D'):
        super().__init__(name=name)
        self._d = [np.asarray(d_) for d_ in d]


    def __call__(self, dim):
        """Return direction for given dimension."""
        if pg.core.deepDebug() == -1:
            pg._b(self, dim)
        return self._d[dim-1]


    def eval(self, *args, **kwargs):
        """Evaluate Direction for points."""
        # implement me
        pnts = asPosListNP(args[0])
        m = kwargs.pop('mesh', None)
        if m is not None:
            return np.asarray(len(pnts)*[self._d[m.dim()-1]])

        pg.critical('implement me')
        return self._d[m.dim()-1]


DX = Direction([[ 1.0, 0.0, 0.0], [1.0,  0.0, 0.0], [1.0,  0.0,  0.0]], 'DX')
 # maybe 1 and 2d meaningless
DY = Direction([[ 1.0, 0.0, 0.0], [0.0,  1.0, 0.0], [0.0,  1.0,  0.0]], 'DY')
DZ = Direction([[-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0,  0.0, -1.0]], 'DZ')
