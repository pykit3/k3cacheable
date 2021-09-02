import doctest

import k3cacheable


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(k3cacheable))
    return tests
