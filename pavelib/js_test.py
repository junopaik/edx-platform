"""
Javascript test tasks
"""
from paver.easy import task, cmdopts
from pavelib import assets
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test import suite
from pavelib.utils.envs import Env
import os

__test__ = False  # do not collect


class JsTestSuite(suite.TestSuite):
    """
    A class for running JavaScript tests.
    """
    def  __init__(self, *args, **kwargs):
        super(JsTestSuite, self).__init__(*args, **kwargs)
        self.suite = kwargs.get('suite', None)
        self.run_under_coverage = kwargs.get('with_coverage', True)
        self._make_required_dirs()
        # self.mode = 'dev' or 'run'

    @property
    def cmd(self):
        # def js_test_tool(suite, command):
        """
        Run the tests using js-test-tool
        See js-test-tool docs for description of different command line arguments
        """
        suite_yml = js_test_suite(self.suite)

        cmd = "js-test-tool {command} {suite} --use-firefox --timeout-sec 600 --xunit-report {xunit_report}".format(
            command=command, suite=suite_yml, xunit_report=self.xunit_report)

        return cmd

    @property
    def under_coverage_cmd(self):
        if self.run_under_coverage:
            cmd += " --coverage-xml {report_dir}".format(report_dir=self.coverage_report_dir)
        return cmd

    @property
    def test_id(self):
        """
        Given an environment (a key in `self.suite_options`),
        return the path to the JavaScript test suite description
        If `env` is nil, return a string containing all available descriptions.
        """
        if not self.suite:
            return ' '.join(self.suite_options.values())
        else:
            return self.suite_options[suite]

    @property
    def suite_options(self):
        suites = {
            'lms': 'lms/static/js_test.yml',
            'cms': 'cms/static/js_test.yml',
            'cms-squire': 'cms/static/js_test_squire.yml',
            'xmodule': 'common/lib/xmodule/xmodule/js/js_test.yml',
            'common': 'common/static/js_test.yml',
        }

        # Turn relative paths to absolute paths from the repo root.
        for key, val in suites.iteritems():
            suites[key] = os.path.join(Env.REPO_ROOT, val)

        return suites

    def _set_up(self):
        test_utils.clean_dir(self.report_dir)
        test_utils.clean_test_files()
        assets.compile_coffeescript(suite)

    def _make_required_dirs(self):
        """
        Makes sure that the reports directory and the nodeids
        directory are present.
        """
        self.report_dir = test_utils.get_or_make_dir(
            os.path.join(Env.REPORT_DIR, 'javascript')
        )
        
        self.coverage_report_dir = test_utils.get_or_make_dir(
            os.path.join(self.report_dir, 'coverage.xml')
        )

        self.xunit_report = test_utils.get_or_make_dir(
            os.path.join(self.report_dir, 'javascript_xunit.xml')
        )

    # def _print_js_test_cmds(self):
    #     """
    #     Print a list of js_test commands for all available environments
    #     """
    #     for suite in self.suite_options.keys():
    #         print("    paver test_js --mode={mode} --system={suite}".format(mode=self.mode, system=suite))




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
