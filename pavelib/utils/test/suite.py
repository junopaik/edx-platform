"""
Classes used for defining and running test suites
"""
import os
import sys
import subprocess
from paver.easy import call_task
from pavelib.utils.process import kill_process
from pavelib.utils.test import utils as test_utils
from pavelib.utils.envs import Env

__test__ = False  # do not collect


class TestSuite(object):
    """
    TestSuite is a base class that defines how tests run. 
    """
    def __init__(self, *args, **kwargs):
        self.root = args[0]
        self.subsuites = kwargs.get('subsuites', list())
        self.run_under_coverage = kwargs.get('with_coverage', False)

        # Initialize vars for tracking failures
        self.failed_suites = list()
        self.failed = False
       
    @property
    def cmd(self):
        """
        The command to run tests (as a string). For this base class there is none.
        """
        return None

    @property
    def under_coverage_cmd(self):
        """
        Returns the given command (str), reformatted to be run with coverage.
        """
        cmd0, cmd_rest = self.cmd.split(" ", 1)
        # We use "python -m coverage" so that the proper python will run the importable coverage
        # rather than the coverage that OS path finds.

        cmd = "python -m coverage run --rcfile={root}/.coveragerc `which {cmd0}` {cmd_rest}".format(
            root=self.root, cmd0=cmd0, cmd_rest=cmd_rest)
        
        return cmd

    def _clean_up(self):
        """
        This is run after the tests in this suite finish. Specific 
        clean up tasks should be defined in each subsuite.

        i.e. Cleaning mongo after a the lms tests run.
        """
        pass

    def _set_up(self):
        """
        This will run before the test suite is run. Specific setup 
        tasks should be defined in each subsuite.
        
        i.e. Checking for and defining required directories.
        """
        pass

    def _test_sh(self):
        """
        Runs a command in a subprocess and waits for it to finish
        """
        msg = test_utils.colorize(
            '\n{bar}\n Running tests for {suite_name} \n{bar}\n'.format(suite_name=self.root, bar='=' * 40), 
            'GREEN'
        )

        sys.stdout.write(msg)
        sys.stdout.flush()

        kwargs = {'shell': True, 'cwd': None}
        process = None
        returncode = None

        if self.run_under_coverage:
            cmd = self.under_coverage_cmd
        else:
            cmd = self.cmd
        
        print cmd

        try:
            process = subprocess.Popen(cmd, **kwargs)
            process.communicate()
        except KeyboardInterrupt:
            kill_process(process)
            returncode = 1
        else:
            returncode = process.returncode
        finally:
            self.failed = (returncode != 0)

    def run_tests(self):
        # set up
        sys.stdout.write("Setting up for {suite_name}\n".format(suite_name=self.root))
        self._set_up()
        self.failed_suites = list()

        # run the tests for this class, and for all subsuites
        if self.cmd:
            self._test_sh()
            if self.failed:
                self.failed_suites.append(self)

        for suite in self.subsuites:
            suite.run_tests()
            if suite.failed:
                self.failed = True
                self.failed_suites.extend(suite.failed_suites)

        # clean up
        sys.stdout.write("Cleaning up after {suite_name}\n".format(suite_name=self.root))
        self._clean_up()

    def report_test_failures(self):
        """
        Runs each of the specified suites while tracking and reporting failures
        """
        if self.failed:
            msg = test_utils.colorize("\n\n{bar}\nTests failed in the following suites:\n* ".format(bar="=" * 48), 'RED')
            msg += test_utils.colorize('\n* '.join([s.root for s in self.failed_suites]) + '\n\n', 'RED')
        else:
            msg = test_utils.colorize("\n\n{bar}\nNo test failures! Yay!\n ".format(bar="=" * 48), 'GREEN')
        
        sys.stderr.write(msg)

    def run(self, with_build_docs=False):
        self.run_tests()

        if with_build_docs:
            call_task('pavelib.docs.build_docs')

        self.report_test_failures()
        
        if self.failed:
            sys.exit(1)


class NoseTestSuite(TestSuite):
    """
    A subclass of TestSuite with extra methods that are specific to nose tests
    """
    def  __init__(self, *args, **kwargs):
        super(NoseTestSuite, self).__init__(*args, **kwargs)
        self.failed_only = kwargs.get('failed_only', False)
        self.fail_fast = kwargs.get('fail_fast', False)
        self._make_required_dirs()

    @property
    def _test_options_flags(self):
        opts = " "

        # Handle "--failed" as a special case: we want to re-run only
        # the tests that failed within our Django apps
        # This sets the --failed flag for the nosetests command, so this
        # functionality is the same as described in the nose documentation
        if self.failed_only:
            opts += "--failed"

        # This makes it so we use nose's fail-fast feature in two cases.
        # Case 1: --fail_fast is passed as an arg in the paver command
        # Case 2: The environment variable TESTS_FAIL_FAST is set as True
        if self.fail_fast or ('TESTS_FAIL_FAST' in os.environ and os.environ['TEST_FAIL_FAST']):
            opts += " --stop".format(test_id=test_id)

        return opts

    def _clean_up(self):
        """
        Cleans mongo afer the tests run.
        """
        test_utils.clean_mongo()

    def _make_required_dirs(self):
        """
        Makes sure that the reports directory and the nodeids
        directory are present.
        """
        self.report_dir = test_utils.get_or_make_dir(
            os.path.join(Env.REPORT_DIR, self.root)
        )

        self.test_id_dir = test_utils.get_or_make_dir(
            os.path.join(Env.TEST_DIR, self.root)
        )

        # no need to create test_ids file, since nose will do that
        self.test_ids = os.path.join(self.test_id_dir, 'noseids')


class SystemTestSuite(NoseTestSuite):
    """
    TestSuite class for lms and cms nosetests
    """
    def  __init__(self, *args, **kwargs):
        super(SystemTestSuite, self).__init__(*args, **kwargs)
        self.test_id = kwargs.get('test_id', self._default_test_id)
        self.fasttest = kwargs.get('fasttest', False)
        self.run_under_coverage = kwargs.get('with_coverage', True)
    
    @property
    def cmd(self):
        """
        Runs the tests for the 'lms' and 'cms' systems
        """
        
        cmd = './manage.py {system} test {test_id} {test_opts} --traceback --settings=test'.format(
            system=self.root, test_id=self.test_id, test_opts=self._test_options_flags)
        return cmd

    @property
    def _default_test_id(self):
        # If no test id is provided, we need to limit the test runner
        # to the Djangoapps we want to test.  Otherwise, it will
        # run tests on all installed packages.

        # We need to use $DIR/*, rather than just $DIR so that
        # django-nose will import them early in the test process,
        # thereby making sure that we load any django models that are
        # only defined in test files.
        default_test_id = "{system}/djangoapps/* common/djangoapps/*".format(system=self.root)

        if self.root in ('lms', 'cms'):
            default_test_id += " {system}/lib/*".format(system=self.root)

        if self.root == 'lms':
            default_test_id += " {system}/tests.py".format(system=self.root)

        return default_test_id

    def _set_up(self):
        call_task('pavelib.prereqs.install_prereqs')
        call_task('pavelib.utils.test.utils.clean_test_files')
        call_task('pavelib.utils.test.utils.clean_reports_dir')

        if not self.fasttest:
            # TODO: Fix the tests so that collectstatic isn't needed
            # add --skip-collect to this when the tests are fixed
            args = [self.root, '--settings=test']
            call_task('pavelib.assets.update_assets', args=args)


class LibTestSuite(NoseTestSuite):
    """
    TestSuite class for edx-platform/common/lib nosetests
    """
    def  __init__(self, *args, **kwargs):
        super(LibTestSuite, self).__init__(*args, **kwargs)
        self.test_id = kwargs.get('test_id', self.root)
        self.run_under_coverage = kwargs.get('with_coverage', True)

    @property
    def cmd(self):
        cmd = "nosetests --id-file={test_ids} {test_id} {test_opts}".format(
            test_ids=self.test_ids, test_id=self.test_id, test_opts=self._test_options_flags)

        return cmd

    def _set_up(self):
        if os.path.exists(os.path.join(self.report_dir, "nosetests.xml")):
            os.environ['NOSE_XUNIT_FILE'] = os.path.join(self.report_dir, "nosetests.xml")

        call_task('pavelib.utils.test.utils.clean_test_files')
        call_task('pavelib.utils.test.utils.clean_reports_dir')
        call_task('pavelib.prereqs.install_prereqs')


class I18nTestSuite(TestSuite):
    """
    Subclass of TestSuite for i18n tests
    """
    # TODO: Update this when i18n tasks are deprecated to rake
    @property
    def cmd(self):
        return "rake i18n:test"
