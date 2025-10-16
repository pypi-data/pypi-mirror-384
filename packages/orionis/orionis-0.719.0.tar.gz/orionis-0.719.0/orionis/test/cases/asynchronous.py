import unittest
from orionis.test.output.dumper import TestDumper

class AsyncTestCase(unittest.IsolatedAsyncioTestCase, TestDumper):
    """
    Base class for asynchronous unit tests in the Orionis framework.
    """
    pass