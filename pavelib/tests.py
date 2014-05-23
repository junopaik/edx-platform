"""
Unit test tasks
"""
import os
import sys
from paver.easy import sh, task, cmdopts, needs
# from pavelib import js_test
from pavelib.utils.test import suites as suite
from pavelib.utils.test import utils as test_utils
from pavelib.utils.envs import Env

__test__ = False  # do not collect

TEST_TASK_DIRS = []

for item in os.listdir('{}/common/lib'.format(Env.REPO_ROOT)):
    if os.path.isdir(os.path.join('{}/common/lib'.format(Env.REPO_ROOT), item)):
        TEST_TASK_DIRS.append(os.path.join('common/lib', item))

LIB_SUITES = [suite.LibTestSuite(d) for d in TEST_TASK_DIRS]
SYSTEM_SUITES = [suite.SystemTestSuite('cms'), suite.SystemTestSuite('lms')]

PYTHON_SUITE = suite.PythonTestSuite('Python Tests', subsuites=SYSTEM_SUITES + LIB_SUITES)
I18N_SUITE = suite.I18nTestSuite('i18n')
JS_SUITE = suite.JsTestSuite('JavaScript Tests')
ALL_UNITTESTS_SUITE = suite.TestSuite('All Tests', subsuites=[PYTHON_SUITE, I18N_SUITE, JS_SUITE])


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
    ("test_id=", "t", "Test id"),
    ("failed", "f", "Run only failed tests"),
    ("fail_fast", "x", "Run only failed tests"),
    ("fasttest", "a", "Run without collectstatic")
])
def test_system(options):
    """
    Run all django tests on our djangoapps for system
    """
    system = getattr(options, 'system', 'lms')
    test_id = getattr(options, 'test_id', None)
    failed_only = getattr(options, 'failed', False)
    fail_fast = getattr(options, 'fail_fast', False)
    fasttest = getattr(options, 'fasttest', False)

    system_tests = suite.SystemTestSuite(system, failed_only=failed_only, fail_fast=fail_fast, fasttest=fasttest)
    test_suite = suite.PythonTestSuite(system + ' python tests', subsuites =[system_tests])
    test_suite.run()


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("lib=", "l", "lib to test"),
    ("test_id=", "t", "Test id"),
    ("failed", "f", "Run only failed tests"),
    ("fail_fast", "x", "Run only failed tests"),
])
def test_lib(options):
    """
    Run tests for common/lib/
    """
    lib = getattr(options, 'lib', None)
    test_id = getattr(options, 'test_id', lib)
    failed_only = getattr(options, 'failed', False)
    fail_fast = getattr(options, 'fail_fast', False)

    if not lib:
        raise Exception(test_utils.colorize('Missing required arg. Please specify --lib, -l', 'RED'))

    lib_tests = suite.LibTestSuite(lib, options)
    test_suite = suite.PythonTestSuite(lib+ ' python tests', subsuites =[lib_tests])
    test_suite.run()


@task
@needs('pavelib.prereqs.install_prereqs')
def test_python():
    """
    Run all python tests
    """
    PYTHON_SUITE.run()


@task
def test_i18n():
    """
    Run all i18n tests
    """
    I18N_SUITE.run()


@task
@needs('pavelib.prereqs.install_prereqs')
def test():
    """
    Run all tests
    """
    ALL_UNITTESTS_SUITE.run(with_build_docs=True)


@task
def coverage():
    """
    Build the html, xml, and diff coverage reports
    """
    for directory in TEST_TASK_DIRS:
        report_dir = os.path.join(Env.REPORT_DIR, directory)

        if os.path.isfile(os.path.join(report_dir, '.coverage')):
            # Generate the coverage.py HTML report
            sh("coverage html --rcfile={dir}/.coveragerc".format(dir=directory))

            # Generate the coverage.py XML report
            sh("coverage xml -o {report_dir}/coverage.xml --rcfile={dir}/.coveragerc".format(
                report_dir=report_dir,
                dir=directory
            ))

    # Find all coverage XML files (both Python and JavaScript)
    xml_reports = []

    for subdir, _dirs, files in os.walk(Env.REPORT_DIR):
        if 'coverage.xml' in files:
            xml_reports.append(os.path.join(subdir, 'coverage.xml'))

    if len(xml_reports) < 1:
        err_msg = test_utils.colorize(
            "No coverage info found.  Run `paver test` before running `paver coverage`.",
            'RED'
        )
        sys.stderr.write(err_msg)
    else:
        xml_report_str = ' '.join(xml_reports)
        diff_html_path = os.path.join(Env.REPORT_DIR, 'diff_coverage_combined.html')

        # Generate the diff coverage reports (HTML and console)
        sh("diff-cover {xml_report_str} --html-report {diff_html_path}".format(
            xml_report_str=xml_report_str, diff_html_path=diff_html_path))
        sh("diff-cover {xml_report_str}".format(xml_report_str=xml_report_str))
        print("\n")
