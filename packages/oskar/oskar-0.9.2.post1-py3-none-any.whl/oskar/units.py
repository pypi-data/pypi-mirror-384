#!/usr/bin/env python
"""Collection of frequently used physical quantities and their abbreviations.

This module provides a dictionary of physical entities with their
units, dimensions, and symbols. It also provides a Parameter dictionary class
for easy access and visualization of these properties.
"""
import numpy as np

import pygimli as pg
# from sympy import Symbol  # performance hole


UNIT={
    '1':'[$~$]',
    'dTemperature': r'K',
    'pressure':r'MPa',
    'pressureI':r'1/MPa',
    'temperature': r'°C',
    'velocity':r'm/s',
    }
"""Unit strings for some physical quantities.
"""

DIM ={'1':r'$\mathsf{1}$',
      'dTemperature': r'$\mathsf\Theta$',
      'pressure': r'$\mathsf{M     \cdot L^{-1}\cdot T^{-2}}$',
      'pressureI':r'$\mathsf{M^{-1}\cdot L     \cdot T^{2}}$',
      'temperature': r'$\mathsf\Theta$',
      'velocity':r'$\mathsf{L\cdot T^{-1}}$',
      }
"""Dimension string for dimensionless quantity.
"""

ENTITIES = {
    "biot coefficient": {
        'alt': ['biot', 'alphaB'],
        'name': "Biot-Willis coefficient",
        'symbol': r'$\alpha_{\rm B}$',
        'type': '1',
    },
    "bulk modulus": {
        'alt': ['K'],
        'name': "bulk modulus",
        'symbol': r'$K$',
        'type': 'pressure',
    },
    'elasticity tensor': {
        'alt': ['C'],
        'name': 'elasticity tensor',
        'symbol': r'$\mathbf{C}$',
        'type': 'pressure',
    },
    'density': {
        'alt': ['rho'],
        'name': 'volumetric mass density',
        'symbol': r'$\rho$',
        'unit': r'kg/m³',
        'dim':  r'$\mathsf{M\cdot L^{-3}}$'
    },
    'diffusivity': {
        'alt': ['D'],
        'name': 'mass diffusivity',
        'name_de': 'Diffusionskoeffizient',
        'symbol': r'$D$',
        'unit': r'm²/s',
        'dim':  r'$\mathsf{M^{2}\cdot T^{-1}}$'
    },
    'effective diffusivity': {
        'alt': ['De'],
        'name': 'effective mass diffusivity',
        'name_de': 'Effektiver Diffusionskoeffizient',
        'symbol': r'$D_{\text{e}}$',
        'unit': r'm²/s',
        'dim':  r'$\mathsf{M^{2}\cdot T^{-1}}$'
    },
    'fluid compressibility': {
        'alt': ['betaF'],
        'name': 'fluid compressibility',
        'symbol': r'$\beta_{\text{f}}$',
        'type': 'pressureI',
    },
    'solid compressibility': {
        'alt': ['betaS'],
        'name': 'solid compressibility',
        'symbol': r'$\beta_{\text{s}}$',
        'type': 'pressureI',
    },
    'pore diffusivity': {
        'alt': ['Dp'],
        'name': 'pore mass diffusivity',
        'name_de': 'effektiver Diffusionskoeffizient',
        'symbol': r'$D_{\text{p}}$',
        'unit': r'm²/s',
        'dim':  r'$\mathsf{M^{2}\cdot T^{-1}}$'
    },
    'displacement':{
        'alt': ['u'],
        'name': 'displacement vector',
        'symbol': r'$\boldsymbol{u}$',
        'unit': r'm',
        'dim':  r'$\mathsf{L}$'
    },
    'dynamic viscosity': {
        'alt': ['eta'],
        'name': 'dynamic viscosity',
        'symbol': r'$\eta$',
        'unit': r'Pa s',
        'dim':  r'$\mathsf{M\cdot L^{-1}\cdot T^{-1}}$'
    },
    'flux':{
        'alt': ['q'],
        'name': 'fluid mass flux field',
        'symbol': r'$\boldsymbol{q}$',
        'type': 'velocity',
    },
    'gravitational acceleration': {
        'alt': ['g'],
        'name': 'gravitational acceleration',
        'symbol': r'$g$',
        'unit': r'm/s²',
        'dim':  r'$\mathsf{L\cdot T^{-2}}$'
    },
    'half-life': {
        'alt': ['t12'],
        'name': 'half-life time',
        'symbol': r'$t_{½}$', #½
        'unit': r'1/s',
        'dim': r'$\mathsf{T}^{-1}$',
    },
    'heat flow rate': {
        'alt': ['heat'],
        'name': 'specific heat flow rate',
        'symbol': r'$H$',
        'unit': r'W/m', #J/s/m
        'dim':  r'$\mathsf{M\cdot L^{-1}\cdot T^{-3}}$'
    },
    'hydraulic conductivity': {
        'alt': ['Kf'],
        'name': 'hydraulic conductivity',
        'symbol': r'$K$',
        'unit': r'm/s',
        'dim':  r'$\mathsf{L\cdot T^{-1}}$'
    },
    'hydraulic head': {
        'alt': ['h'],
        'name': 'hydraulic head',
        'symbol': r'$h$',
        'unit': r'm',
        'dim':  r'$\mathsf{L}$'
    },
    'hydraulic permeability': {
        'alt': ['k'],
        'name': 'intrinsic hydraulic permeability',
        'symbol': r'$k$',
        'unit': r'm²',
        'dim':  r'$\mathsf{L}^{2}$'
    },
    'identity matrix': {
        'alt': ['I'],
        'name': 'Identity matrix',
        'symbol': r'$\mathbf{I}$',
        'unit': UNIT['1'],
        'dim':  DIM['1'],
    },
    'kinematic viscosity': {
        'alt': ['nu'],
        'name': 'kinematic viscosity',
        'symbol': r'$\nu$',
        'unit': r'm²/s',
        'dim':  r'$\mathsf{L^{2}\cdot T^{-1}}$'
    },
    "Lamé 1": {
        'alt': ['lame1', 'lame_1'],
        'name': "Lamé's first parameter",
        'symbol': r'$\lambda$',
        'type': 'pressure',
    },
    "Lamé 2": {
        'alt': ['lame2','lame_2'],
        'name': "Lamé's second parameter",
        'symbol': r'$\mu$',
        'type': 'pressure',
    },
    "Poisson's ratio": {
        'alt': ['nu_P', 'nuP'],
        'name': "Poisson's ratio",
        'symbol': r'$\nu$',
        'type': '1',
    },
    'pore water pressure': {
        'alt': ['p'],
        'name': 'pore water pressure',
        'symbol': r'$p$',
        'type': 'pressure',
    },
    'porosity': {
        'alt': ['phi'],
        'name': 'porosity',
        'symbol': r'$\phi$',
        'type': '1',
    },
    'saturation':{
        'alt': ['sat'],
        'name': 'saturation',
        'symbol': r'$S$',
        'type': '1',
    },
    'specific heat capacity':{
        'alt': ['cp'],
        'name': 'specific heat capacity',
        'symbol': r'$c_{\text{p}}$',
        'unit': r'J/(K kg)',
        'dim':  r'$\mathsf{L^{2}\cdot\Theta^{-1}\cdot T^{-2}}$'
    },
    'sorption':{
        'alt': ['Kd'],
        'name': 'sorption coefficient',
        'symbol': r'$K_{\text{d}}$',
        'unit': r'm³/kg',
        'dim':  r'$\mathsf{L³}\cdot\mathsf{M}^{-1}$'
    },
    'storage coefficient':{
        'alt': ['S'],
        'name': 'storage coefficient',
        'symbol': r'$S$',
        'type': '1',
    },
    'specific storage':{
        'alt': ['Ss'],
        'name': 'specific storage',
        'symbol': r'$S_{\rm s}$',
        'unit': r'1/m',
        'dim':  r'$\mathsf{L^{-1}}$'
    },
    'small strain tensor':{
        'alt': ['epsT', 'eps'],
        'name': 'small strain tensor',
        'symbol': r'$\boldsymbol{\epsilon}$',
        'type': '1',
    },
    'stress':{
        'alt': ['sigma'],
        'name': 'stress',
        'symbol': r'$\sigma$',
        'type': 'pressure',
    },
    'Cauchy stress tensor':{
        'alt': ['sigmaT'],
        'name': 'Cauchy stress tensor',
        'symbol': r'$\boldsymbol{\sigma}$',
        'type': 'pressure',
    },
    'temperature': {
        'alt': ['T'],
        'name': 'temperature',
        'symbol': r'$T$',
        'type': 'temperature',
    },
    'temperature difference': {
        'alt': ['thetaT', 'dT'],
        'name': 'temperature difference',
        'symbol': r'$\theta$',
        'type': r'dTemperature'
    },
    'transmissivity': {
        'alt': ['Tr'],
        'name': 'transmissivity',
        'symbol': r'$T$',
        'unit': r'm²/s',
        'dim':  r'$\mathsf{L}^2\cdot\mathsf{T}^{-1}$'
    },
    'time': {
        'alt': ['t'],
        'name': 'time',
        'symbol': r'$t$',
        'unit': r's',
        'dim':  r'$\mathsf{T}$'
    },
    'thermal conductivity': {
        'alt': ['lam'],
        'name': 'thermal conductivity',
        'symbol': r'$\lambda$',
        'unit': r'J/(K m s)',
        'dim':  r'$\mathsf{M\cdot L\cdot\Theta^{-1}\cdot T^{-3}}$'
    },
    'thermal conductivity kappa': {
        'alt': ['kappaT'],
        'name': 'thermal conductivity',
        'symbol': r'$\kappa$',
        'unit': r'J/(K m s)',
        'dim':  r'$\mathsf{M\cdot L\cdot\Theta^{-1}\cdot T^{-3}}$'
    },
    'thermal diffusivity': {
        'alt': ['alphaT'],
        'name': 'thermal diffusivity',
        'name_de': 'Temperaturleitfähigkeit',
        'symbol': r'$\alpha_{\rm th}$',
        'unit': r'm²/s',
        'dim':  r'$\mathsf{M^{2}\cdot T^{-1}}$'
    },
    'velocity':{
        'alt': ['v', 'vel'],
        'name': 'pore fluid velocity',
        'symbol': r'$\boldsymbol{v}$',
        'unit': r'm/s',
        'dim':  r'$\mathsf{L\cdot T^{-1}}$'
    },
    'volumetric heat capacity':{
        'alt': ['cv'],
        'name': 'volumetric heat capacity',
        'symbol': r'$c_{\text{v}}$',
        'unit': r'J/(K m³)',
        'dim':  r'$\mathsf{M\cdot L^{-1}\cdot\Theta^{-1}\cdot T^{-2}}$'
    },
    'volumetric heat flow':{
        'alt': ['Hv'],
        'name': 'volumetric heat flow rate',
        'symbol': r'$H_{\text{v}}$',
        'unit': r'W/m³',
        'dim':  r'$\mathsf{M\cdot L^{-1}\cdot T^{-3}}$'
    },
    'volumetric thermal expansion coefficient': {
        'alt': ['betaV'],
        'name': 'volumetric thermal expansion coefficient',
        'symbol': r'$\beta_{\rm v}$',
        'unit': r'1/K',
        'dim':  r'$\mathsf\Theta^{-1}$'
    },
    "Youngs' modulus": {
        'alt': ['E'],
        'name': "Youngs' modulus",
        'symbol': r'$E$',
        'type': 'pressure',
    },
}
"""Dictionaries of predefined physical entities.

The single dictionaries contains name, symbol, alternative abbreviation,
unit, and dimension.
The main purpose is to reduce redundancies in the Oskar documentation.
Best get it with :py:mod:`oskar.units.entity`.
"""


__SYMBOLS__ = {}
"""Dictionary of sympy symbols, also with some alternative names.

Need to be lazy evaluated by the first call :py:mod:`oskar.units.symbols`.
, so best get single symbols with :py:mod:`oskar.units.toSymbol`.
"""


def symbols():
    """Return a dictionary of sympy symbols, also with some alternative names.

    Need to be lazy evaluated, so best get it with
    :py:mod:`oskar.units.toSymbol`.
    """
    if len(list(__SYMBOLS__.keys())) == 0:
        ## lazy eval until import sympy takes 100% of importing oskar
        from sympy import Symbol

        __SYMBOLS__.update( {
        'alpha': Symbol('alpha'),
        'beta': Symbol('beta'),
        'gamma': Symbol('gamma'),
        'delta': Symbol('delta'),
        'eps': Symbol('epsilon'),
        'epsilon': Symbol('epsilon'),
        'lam': Symbol('lambda'),
        'lmbda': Symbol('lambda'),
        'lamda': Symbol('lambda'),
        'mu': Symbol('mu'),
        'nu': Symbol('nu'),
        'sigma': Symbol('sigma'),
        'theta': Symbol('theta'),
        'Theta': Symbol('Theta'),
        'rho': Symbol('rho'),
        })
    return __SYMBOLS__


def toSymbol(k:str):
    """Return SymPy symbol for predefined names.

    This mainly used for shiny math render.
    The defined symbols can be found in the source of
    :py:mod:`oskar.units.SYMBOLS`.

    Return `k` if the symbol is not known.

    Arguments
    ---------
    k : str
        Name for the symbol.

    Returns
    -------
    SymPy Symbol.
    """
    try:
        return symbols()[k]
    except BaseException:
        return k


def entity(name:str) -> dict:
    """Return a dictionary of information about a physical entity.

    The dictionary only contains a few physical quantities frequently used
    in the documentation to reduce redundancies.
    The single dictionaries contain at minimum the name, symbol,
    alternative abbreviations, unit and dimension of the physical entity.

    See source of :py:mod:`oskar.units.ENTITIES` of predefined entities.

    Returns a empty dictionary if the `name` is not known.

    Arguments
    ---------
    name : str
        Name or alternative abbreviation for the physical entity.

    Returns
    -------
    dict:
        Dictionary of physical entity information.
    """
    u = None

    if name.lower() in ENTITIES:
        u = ENTITIES[name.lower()]

    else:
        u = None
        for _k, v in ENTITIES.items():
            for a in v['alt']:
                if a.lower == name.lower:
                    u = v
                    break
            if u is not None:
                break

    if u is None:
        u = {'name': name, 'symbol': '', 'unit': '[]', 'dim': '1'}
    return u


def varNameAsLatex(s:str, skipDollar:bool=False) -> str:
    r"""Convert a variable name to LaTeX.

    Some special convention are made.
    If the variable name is known in
    :py:mod:`oskar.units.ENTITIES` ['alt'] then the latex representation will be
    :py:mod:`oskar.units.ENTITIES` ['symbol'].

    Arguments
    ---------
    s: str
        Variable name

    skipDollars: bool[False]
        As default the output is formatted as latex math with '$' symbols.
        This can be skipped.

    Returns
    -------
    str:
        Latex representation of variable name `s`.

    Example
    -------
    >>> from oskar.units import varNameAsLatex
    >>> from oskar.utils import pprint
    >>> pprint(varNameAsLatex('cp'))
    $$c_{\text{p}}$$
    """
    vs = s.split('_')
    name = vs[0]

    greeks = ['alpha', 'beta', 'gamma', 'rho',
              'sigma', 'kappa', 'lambda']

    out = '\\' + name if name in greeks else name

    u = entity(name)
    if u['symbol'] != '':
        out = u['symbol']

    if len(vs) > 1:
        out += r'_{\mathrm{' + ','.join(vs[1:]) + '}}'

    #pg._g(out)

    if skipDollar:
        return out.replace('$','')

    return f'${out}$'


class ParameterDict(dict):
    """Dictionary for region parameters.

    This dictionary is used to store parameters for different regions in a mesh.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the parameter dictionary."""
        super().__init__(*args, **kwargs)


    def cellValues(self, mesh: pg.Mesh) -> np.ndarray:
        """Create cell values for the dictionary with a mesh.

        Returns an array of the parameters based on the cell markers
        of the mesh.
        """
        try:
            if isinstance(mesh, pg.Mesh):
                return np.asarray([self[reg] for reg in mesh.cellMarkers()])
        except KeyError:
            print(f'Found cell markers {pg.unique(mesh.cellMarkers())}')
            print(f'for parameter keys {self.keys()}')

            pg.critical('ParameterDict.cellValues.',
                         'The mesh does not have cell markers for the '
                         'parameter keys.'
                         ' Please use a mesh with correct cell markers.'
                         'or change the parameter keys.')


    def __str__(self):
        """Return the string representation of the parameter dictionary.

        Returns
        -------
        str:
            String representation of the parameter dictionary.
            The length of the dictionary is shown in the format "P{n}".
            Where n is the number of parameters in the dictionary.
        """
        return "P{"+f"{len(self)}"+"}"


    def __mul__(self, d: any):
        """Multiplication operator.

        Attributes
        ----------
        d: ParameterDict, int, float
            The dictionary is multiplied with the given value.
            If the value is a dictionary, the multiplication is done
            element-wise.
        """
        if isinstance(d, ParameterDict):
            return ParameterDict(zip(self.keys(),
                                     [self[k]*d[k] for k in self.keys()],
                                     strict=True))
        elif isinstance(d, int | float):
            return ParameterDict(zip(self.keys(),
                                     [self[k]*d for k in self.keys()],
                                     strict=True))
        else:
            return d.__rmul__(self)


    def __add__(self, d):
        """Addition operator.

        Attributes
        ----------
        d: ParameterDict, int, float
            The dictionary is added with the given value.
            If the value is a dictionary, the addition is done
            element-wise.
        """
        if isinstance(d, ParameterDict):
            return ParameterDict(zip(self.keys(),
                                     [self[k]+d[k] for k in self.keys()],
                                     strict=True))
        elif isinstance(d, int | float):
            return ParameterDict(zip(self.keys(),
                                     [self[k]+d for k in self.keys()],
                                     strict=True))
        else:
            return d.__radd__(self)


    def __radd__(self, d):
        """Reverse Addition operator.

        Attributes
        ----------
        d: ParameterDict, int, float
            The dictionary is added with the given value.
            If the value is a dictionary, the addition is done
            element-wise.
        """
        if isinstance(d, ParameterDict):
            return ParameterDict(zip(self.keys(),
                                     [d[k]+self[k] for k in self.keys()],
                                     strict=True))
        elif isinstance(d, int | float):
            return ParameterDict(zip(self.keys(),
                                     [d+self[k] for k in self.keys()],
                                     strict=True))
        else:
            return d.__add__(self)


    def __sub__(self, d):
        """Subtraction operator.

        Attributes
        ----------
        d: ParameterDict, int, float
            The dictionary is subtracted with the given value.
            If the value is a dictionary, the subtraction is done
            element-wise.
        """
        if isinstance(d, ParameterDict):
            return ParameterDict(zip(self.keys(),
                                     [self[k]-d[k] for k in self.keys()],
                                     strict=True))
        elif isinstance(d, int | float):
            return ParameterDict(zip(self.keys(),
                                     [self[k]-d for k in self.keys()],
                                     strict=True))
        else:
            return d.__rsub__(self)


    def __rsub__(self, d):
        """Reverse Subtraction operator.

        Attributes
        ----------
        d: ParameterDict, int, float
            The dictionary is subtracted with the given value.
            If the value is a dictionary, the addition is done
            element-wise.
        """
        if isinstance(d, ParameterDict):
            return ParameterDict(zip(self.keys(),
                                     [d[k]-self[k] for k in self.keys()],
                                     strict=True))
        elif isinstance(d, int | float):
            return ParameterDict(zip(self.keys(),
                                     [d-self[k] for k in self.keys()],
                                     strict=True))
        else:
            return d.__sub__(self)


    def __rmul__(self, d):
        """Reverse Multiplication operator.

        Attributes
        ----------
        d: ParameterDict, int, float
            The dictionary is multiplied with the given value.
            If the value is a dictionary, the multiplication is done
            element-wise.
        """
        if isinstance(d, int | float):
            return ParameterDict(zip(self.keys(),
                                     [d*self[k] for k in self.keys()],
                                     strict=True))
        else:
            return d.__mul__(self)


    def __truediv__(self, d):
        """Division operator.

        Attributes
        ----------
        d: ParameterDict, int, float
            The dictionary is divided by the given value.
            If the value is a dictionary, the division is done
            element-wise.
        """
        if isinstance(d, ParameterDict):
            return ParameterDict(zip(self.keys(),
                                     [self[k]/d[k] for k in self.keys()],
                                     strict=True))
        else:
            return d.__rmul__(self)

    def __neg__(self):
        """Negation operator.

        Returns
        -------
        ParameterDict:
            The negated dictionary.
        """
        return ParameterDict(zip(self.keys(),
                                 [-self[k] for k in self.keys()], strict=True))


class Parameters(dict):
    """Store parameters.

    Store parameters and print a shiny table in jupyter environment.

    See: :ref:`userguide-misc-units` for available defaults.

    Example
    -------
    >>> import oskar
    >>> # Just a simple explanation table
    >>> p = Parameters()
    >>> p.add(type='displacement')
    >>> p.add(type='eps')
    >>> p.add(type='sigmaT')
    >>> p.show() # doctest: +SKIP
    >>> # Parameters with values
    >>> p = oskar.Parameters()
    >>> rho = p.add(rho=1, type='rho')
    >>> gamma = p.add(gamma=2, name='custom gamma', unit='m', dim='L')
    >>> p.show() # doctest: +SKIP
    """

    def __init__(self, showDim:bool=False, regions=None):
        """Initialize the parameter dictionary.

        Arguments
        ---------
        showDim: bool(False)
            Show dimensions in the parameter table.
        """
        self._showDim = showDim
        if regions is None:
            regions = {}
        self._regions = regions

        self.isTypeListOnly = False


    def __call__(self, **kwargs):
        """Call the add method with the given keyword arguments."""
        return self.add(**kwargs)


    @property
    def regions(self):
        """Return the regions dictionary."""
        return self._regions


    def add(self, **kwargs):
        """Add values to the parameter dictionary.

        The first kwargs should be a variable key, or 'type' for pure
        description tables.
        If `type` is given all parameter properties are taken from
        :py:mod:`oskar.units.entity`, but can be overwritten with `kwargs`.

        Keyword Arguments
        -----------------
        any: value
            `any=value` is Parameter=value.

        type: string
            Predefined type from Unit dictionary.
            See: :ref:`userguide-misc-units` for available defaults.

        sname: string [optional]
            Additional name for name as `sname name`.

        name: string [optional]
            Parameter name.

        unit: string [optional]
            Parameter unit.

        dim: string [optional]
            Parameter dimension.

        symbol: string [optional]
            Parameter symbol representation.

        Returns
        -------
        value is kwargs does not start with `type`

        """
        key = list(kwargs.keys())[0]

        if key == 'type':
            quant = dict(entity(kwargs['type']))
            key = quant['alt'][0]
            val = 0
            self.isTypeListOnly = True
        else:
            val = kwargs.pop(key)

        if len(self._regions.items()) > 0 and isinstance(val, list):
                if len(val) == len(self._regions.items()):
                    val = dict(zip(self._regions.keys(), val, strict=True))
                else:
                    pg.critical(f'Number of values for {key} does not'
                                ' match number of given regions.')

        if 'type' not in kwargs:
            if 'unit' in kwargs:
                u = kwargs.pop('unit')
                quant = dict(entity(u))
                quant['unit'] = u
                quant['name'] = kwargs.pop('name', 'no-name')
            else:
                quant = entity('')

            #pg._r(quant)
            quant['symbol'] = varNameAsLatex(key)
        else:
            quant = dict(entity(kwargs.pop('type')))

            if '_' in key:
                ks = key.split('_')
                keySubScript = ks[-1]

                if 'altsymbol' in kwargs:
                    sym = kwargs.pop('altsymbol')
                    if sym[0] != '\\':
                        sym = '\\' + sym
                    quant['symbol'] = '${' + sym + '}_' + \
                                r'{\mathrm{'+keySubScript+'}}$'

                else:
                    symbolTeX = quant['symbol'].replace('$', '')

                    quant['symbol'] = '${' + symbolTeX + '}_' + \
                                r'{\mathrm{'+keySubScript+'}}$'

        quant['key'] = key
        quant['value'] = val
        quant['description'] = kwargs.pop('description',
                                          kwargs.pop('name', quant['name']))

        if 'sname' in kwargs:
            kwargs['description'] = f"{kwargs['sname']} {quant['description']}"
            quant['description'] = kwargs['description']

        if 'unit' not in quant or 'dim' not in quant:
            quant.update({'unit': UNIT[quant['type']],
                          'dim': DIM[quant['type']]})

        quant.update(kwargs)

        # pg._g(key, quant)
        # print(key, quant)
        if key in super().keys():
            print(quant)
            print(self[key])
            pg.error(f'Parameter with key:{key} already exists.')


        super().__setitem__(key, quant)

        if self.isTypeListOnly:
            return

        if isinstance(val, dict):
            return ParameterDict(val)

        return val


    def __setitem__(self, key, val):
        """Overwrite the value of a parameter."""
        super().__getitem__(key)['value'] = val

        #pa = Parameters()


    def _table(self, columns=None):
        """Create table object."""
        if columns is None:
            cols = ['dim'] if self.isTypeListOnly else ['value', 'unit', 'dim']
        else:
            cols = columns.copy()
        table = []

        if self._showDim is False and 'dim' in cols:
            cols.remove('dim')

        if len(list(self._regions.keys())) > 0:

            for _key, v in super().items():
                header = []
                align = 'l'
                if pg.isIPyTerminal():
                    table.append([v['symbol']])
                    header.append('')
                else:
                    table.append([v['key']])
                    header.append('')

                table[-1].append(v['description'])
                header.append('')
                align += 'l'

                for reg, name in self._regions.items():
                    table[-1].append(v['value'][reg])
                    header.append(name)
                    align += 'r'

                table[-1].append(v['unit'])
                header.append('Unit')
                align += 'l'

                if self._showDim is True and pg.isIPyTerminal() is True:
                    table[-1].append(v['dim'])
                    header.append('Dim')
                    align += 'r'

            return pg.utils.Table(table, header=header, align=align,
                                  transpose=False)

        else:

            if pg.isIPyTerminal():
                cols.insert(0, 'symbol')
                cols.insert(1, 'description')
            else:
                cols.insert(0, 'key')
                cols.insert(1, 'description')

            if self._showDim is True and pg.isIPyTerminal() is True:
                # don't use!
                cols.append('dim')

            for _key, v in super().items():
                row = []
                for c in cols:
                    row.append(v[c.lower()])
                table.append(row)

            align='ll'
            for _c in cols[2:]:
                align += 'r'

            return pg.utils.Table(table,
                                  header=['','', *cols[2:]],
                                  align=align, transpose=False)


    def show(self, columns=None):
        """Show the table with selected columns.

        Always shows at least ['symbol', 'name'].
        """
        # if pg.isNotebook():
        #     return self._table(columns)._repr_html_()

        # elif pg.isIPyTerminal():
        #     # for Sphinx-gallery
        #     pg._y('IPT')
        #     return self._table(columns)._repr_rst_()

        # pg._r('IPT')
        print(self._table(columns))


    def __str__(self):
        """Return string representation of the parameter table."""
        return str(self._table())


    def _repr_html_(self):
        """Return html representation for notebooks and sphinx-gallery."""
        if pg.isNotebook():
            return self._table()._repr_html_()

        elif pg.isIPyTerminal():
            ## table in sphinx-gallery will be wrongly rendered as html
            ## -> fallback to __repr__
            return None

        return None


    def __repr__(self):
        """Return string representation for ipy-terminal or sphinx-gallery."""
        if pg.isNotebook():
            ## covered by _repr_html, we don't need both
            return ""

        elif pg.isIPyTerminal():
            # for Sphinx-gallery
            return self._table()._repr_rst_()

        return str(self)
