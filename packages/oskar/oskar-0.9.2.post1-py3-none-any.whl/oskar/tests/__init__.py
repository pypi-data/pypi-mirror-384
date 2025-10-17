#!/usr/bin/env python
r"""Several submodules with unit tests and more complex functionality tests.

The unit tests are simple tests for all basic modules and try
to cover the overall functionality of the library.
The complex functionality tests are more advanced tests and are supposed to
ensure the combination of basic modules are working as expected.

All tests are executed in the CI workflow for quality assurance.
"""
from .utils import (test, testCount, incTestCounter, assertEqual,
                    TestCollection)

from .closedForms import (terzaghi,
                          advectionDiffReactSun1998)

from .test_02_basic_equations import convergencyTest