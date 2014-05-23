"""
Javascript test tasks
"""
from paver.easy import task, cmdopts
from pavelib import assets
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.suites import TestSuite, JsTestSuite
from pavelib.utils.envs import Env
import os

__test__ = False  # do not collect


@task
@cmdopts([
    ("suite=", "s", "Test suite to run"),
])
def test_js_run(options):
    """
    Run the JavaScript tests and print results to the console
    """
    suite = getattr(options, 'suite', '')

    # test_utils.clean_test_files()
    # assets.compile_coffeescript(suite)

    if not suite:
        print("Running all test suites.  To run a specific test suite, try:")
        print_js_test_cmds('run')
        js_test_tool(None, 'run', False)
    else:
        js_test_tool(suite, 'run', False)


@task
@cmdopts([
    ("suite=", "s", "Test suite to run"),
])
def test_js(options):
    """
    Run the JavaScript tests and print results to the console
    """
    test_js_run(options)


@task
@cmdopts([
    ("suite=", "s", "Test suite to run"),
])
def test_js_dev(options):
    """
    Run the JavaScript tests in your default browser
    """
    suite = getattr(options, 'suite', '')

    # test_utils.clean_test_files()
    # assets.compile_coffeescript(suite)

    if not suite:
        print("Error: No test suite specified.  Try one of these instead:")
        print_js_test_cmds('dev')
    else:
        js_test_tool(suite, 'dev', False)


@task
def test_js_coverage():
    """
    Run all JavaScript tests and collect coverage information
    """
    # test_utils.clean_dir(JS_REPORT_DIR)
    # test_utils.clean_test_files()

    assets.compile_coffeescript("lms", "cms", "common")

    js_test_tool(None, 'run', True)
