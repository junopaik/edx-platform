"""
Classes used for defining and running python test suites
"""
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites import TestSuite

__test__ = False  # do not collect


class PythonTestSuite(TestSuite):
    """
    A subclass of TestSuite with extra
    """
    def _set_up(self):
        test_utils.clean_test_files()
        test_utils.clean_reports_dir()
