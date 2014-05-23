"""
Classes used for defining and running i18n test suites
"""
from pavelib.utils.test.suites import TestSuite

__test__ = False  # do not collect


class I18nTestSuite(TestSuite):
    """
    Subclass of TestSuite for i18n tests
    """
    # TODO: Update this when i18n tasks are deprecated to rake
    @property
    def cmd(self):
        return "rake i18n:test"