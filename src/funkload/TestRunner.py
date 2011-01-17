#!/usr/bin/python
# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
"""FunkLoad Test runner.

Similar to unittest.TestProgram but:
* you can pass the python module to load
* able to override funkload configuration file using command line options
* cool color output
* support doctest with python2.4

$Id: TestRunner.py 24758 2005-08-31 12:33:00Z bdelbosc $
"""
try:
    import psyco
    psyco.full()
except ImportError:
    pass
import os
import sys
import types
import time
import unittest
import re
from StringIO import StringIO
from optparse import OptionParser, TitledHelpFormatter
from utils import red_str, green_str, get_version
from funkload.FunkLoadTestCase import FunkLoadTestCase

# ------------------------------------------------------------
# doctest patch to command verbose mode only available with python2.4
#
g_doctest_verbose = False
try:
    from doctest import DocTestSuite, DocFileSuite, DocTestCase, DocTestRunner
    from doctest import REPORTING_FLAGS, _unittest_reportflags
    g_has_doctest = True
except ImportError:
    g_has_doctest = False
else:
    def DTC_runTest(self):
        test = self._dt_test
        old = sys.stdout
        new = StringIO()
        optionflags = self._dt_optionflags
        if not (optionflags & REPORTING_FLAGS):
            # The option flags don't include any reporting flags,
            # so add the default reporting flags
            optionflags |= _unittest_reportflags
        # Patching doctestcase to enable verbose mode
        global g_doctest_verbose
        runner = DocTestRunner(optionflags=optionflags,
                               checker=self._dt_checker,
                               verbose=g_doctest_verbose)
        # End of patch
        try:
            runner.DIVIDER = "-"*70
            failures, tries = runner.run(
                test, out=new.write, clear_globs=False)
        finally:
            sys.stdout = old
        if failures:
            raise self.failureException(self.format_failure(new.getvalue()))
        elif g_doctest_verbose:
            print new.getvalue()

    DocTestCase.runTest = DTC_runTest



# ------------------------------------------------------------
#
#
class TestLoader(unittest.TestLoader):
    """Override to add options when instanciating test case."""
    def loadTestsFromTestCase(self, testCaseClass):
        """Return a suite of all tests cases contained in testCaseClass"""
        if not issubclass(testCaseClass, FunkLoadTestCase):
            return unittest.TestLoader.loadTestsFromTestCase(self,
                                                             testCaseClass)
        options = getattr(self, 'options', None)
        return self.suiteClass([testCaseClass(name, options) for name in
                                self.getTestCaseNames(testCaseClass)])

    def loadTestsFromModule(self, module):
        """Return a suite of all tests cases contained in the given module"""
        global g_has_doctest
        tests = []
        doctests = None
        if g_has_doctest:
            try:
                doctests = DocTestSuite(module)
            except ValueError:
                pass
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, (type, types.ClassType)) and
                issubclass(obj, unittest.TestCase)):
                tests.append(self.loadTestsFromTestCase(obj))
        suite = self.suiteClass(tests)
        if doctests is not None:
            suite.addTest(doctests)
        return suite


    def loadTestsFromName(self, name, module=None):
        """Return a suite of all tests cases given a string specifier.

        The name may resolve either to a module, a test case class, a
        test method within a test case class, or a callable object which
        returns a TestCase or TestSuite instance.

        The method optionally resolves the names relative to a given module.
        """
        parts = name.split('.')
        if module is None:
            if not parts:
                raise ValueError, "incomplete test name: %s" % name
            else:
                parts_copy = parts[:]
                while parts_copy:
                    try:
                        module = __import__('.'.join(parts_copy))
                        break
                    except ImportError:
                        del parts_copy[-1]
                        if not parts_copy: raise
                parts = parts[1:]
        obj = module
        for part in parts:
            obj = getattr(obj, part)
        import unittest
        if type(obj) == types.ModuleType:
            return self.loadTestsFromModule(obj)
        elif (isinstance(obj, (type, types.ClassType)) and
              issubclass(obj, unittest.TestCase)):
            return self.loadTestsFromTestCase(obj)
        elif type(obj) == types.UnboundMethodType:
            # pass funkload options
            if issubclass(obj.im_class, FunkLoadTestCase):
                return obj.im_class(obj.__name__, self.options)
            else:
                return obj.im_class(obj.__name__)
        elif callable(obj):
            test = obj()
            if not isinstance(test, unittest.TestCase) and \
               not isinstance(test, unittest.TestSuite):
                raise ValueError, \
                      "calling %s returned %s, not a test" % (obj,test)
            return test
        else:
            raise ValueError, "don't know how to make test from: %s" % obj



class _ColoredTextTestResult(unittest._TextTestResult):
    """Colored version."""
    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        if self.showAll:
            self.stream.writeln(green_str("Ok"))
        elif self.dots:
            self.stream.write(green_str('.'))

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        if self.showAll:
            self.stream.writeln(red_str("ERROR"))
        elif self.dots:
            self.stream.write(red_str('E'))

    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        if self.showAll:
            self.stream.writeln(red_str("FAIL"))
        elif self.dots:
            self.stream.write(red_str('F'))

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (red_str(flavour),
                                            self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)


class ColoredTextTestRunner(unittest.TextTestRunner):
    """Override to be color powered."""
    def _makeResult(self):
        return _ColoredTextTestResult(self.stream,
                                      self.descriptions, self.verbosity)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        startTime = time.time()
        test(result)
        stopTime = time.time()
        timeTaken = float(stopTime - startTime)
        result.printErrors()
        self.stream.writeln(result.separator2)
        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()
        if not result.wasSuccessful():
            self.stream.write(red_str("FAILED") + " (")
            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                self.stream.write("failures=%d" % failed)
            if errored:
                if failed: self.stream.write(", ")
                self.stream.write("errors=%d" % errored)
            self.stream.writeln(")")
        else:
            self.stream.writeln(green_str("OK"))
        return result

def filter_testcases(suite, cpattern, negative_pattern=False):
    """Filter a suite with test names that match the compiled regex pattern."""
    new = unittest.TestSuite()
    for test in suite._tests:
        if isinstance(test, unittest.TestCase):
            name = test.id() # Full test name: package.module.class.method
            name = name[1 + name.rfind('.'):] # extract method name
            if cpattern.search(name):
                if not negative_pattern:
                    new.addTest(test)
            elif negative_pattern:
                new.addTest(test)
        else:
            filtered = filter_testcases(test, cpattern, negative_pattern)
            if filtered:
                new.addTest(filtered)
    return new


def display_testcases(suite):
    """Display test cases of the suite."""
    for test in suite._tests:
        if isinstance(test, unittest.TestCase):
            name = test.id()
            name = name[1 + name.find('.'):]
            print name
        else:
            display_testcases(test)


class TestProgram(unittest.TestProgram):
    """Override to add a python module and more options."""
    USAGE = """%prog [options] file [class.method|class|suite] [...]

%prog launch a FunkLoad unit test.

A FunkLoad unittest use a configuration file named [class].conf, this
configuration is overriden by the command line options.

See http://funkload.nuxeo.org/ for more information.


Examples
========
  %prog myFile.py
                        Run all tests.
  %prog myFile.py test_suite
                        Run suite named test_suite.
  %prog myFile.py MyTestCase.testSomething
                        Run a single test MyTestCase.testSomething.
  %prog myFile.py MyTestCase
                        Run all 'test*' test methods in MyTestCase.
  %prog myFile.py MyTestCase -u http://localhost
                        Same against localhost.
  %prog --doctest myDocTest.txt
                        Run doctest from plain text file (requires python2.4).
  %prog --doctest -d myDocTest.txt
                        Run doctest with debug output (requires python2.4).
  %prog myfile.py -V
                        Run default set of tests and view in real time each
                        page fetch with firefox.
  %prog myfile.py MyTestCase.testSomething -l 3 -n 100
                        Run MyTestCase.testSomething, reload one hundred
                        time the page 3 without concurrency and as fast as
                        possible. Output response time stats. You can loop
                        on many pages using slice -l 2:4.
  %prog myFile.py -e [Ss]ome
                        Run all tests that match the regex [Ss]ome.
  %prog myFile.py -e '!xmlrpc$'
                        Run all tests that does not ends with xmlrpc.
  %prog myFile.py --list
                        List all the test names.
  %prog -h
                        More options.
"""
    def __init__(self, module=None, defaultTest=None,
                 argv=None, testRunner=None,
                 testLoader=unittest.defaultTestLoader):
        if argv is None:
            argv = sys.argv
        self.module = module
        self.testNames = None
        self.verbosity = 1
        self.color = True
        self.defaultTest = defaultTest
        self.testLoader = testLoader
        self.progName = os.path.basename(argv[0])
        self.parseArgs(argv)
        self.testRunner = testRunner
        self.checkAsDocFile = False

        module = self.module
        if type(module)  == type(''):
            try:
                self.module = __import__(module)
            except ImportError:
                global g_has_doctest
                if g_has_doctest:
                    # may be a doc file case
                    self.checkAsDocFile = True
                else:
                    raise
            else:
                for part in module.split('.')[1:]:
                    self.module = getattr(self.module, part)
        else:
            self.module = module
        self.loadTests()
        if self.list_tests:
            display_testcases(self.test)
        else:
            self.runTests()

    def loadTests(self):
        """Load unit and doc tests from modules or names."""
        if self.checkAsDocFile:
            self.test = DocFileSuite(os.path.abspath(self.module),
                                     module_relative=False)
        else:
            if self.testNames is None:
                self.test = self.testLoader.loadTestsFromModule(self.module)
            else:
                self.test = self.testLoader.loadTestsFromNames(self.testNames,
                                                               self.module)
        if self.test_name_pattern is not None:
            test_name_pattern = self.test_name_pattern
            negative_pattern = False
            if test_name_pattern.startswith('!'):
                test_name_pattern = test_name_pattern[1:]
                negative_pattern = True
            cpattern = re.compile(test_name_pattern)
            self.test = filter_testcases(self.test, cpattern, negative_pattern)

    def parseArgs(self, argv):
        """Parse programs args."""
        global g_doctest_verbose
        parser = OptionParser(self.USAGE, formatter=TitledHelpFormatter(),
                              version="FunkLoad %s" % get_version())
        parser.add_option("-q", "--quiet", action="store_true",
                          help="Minimal output.")
        parser.add_option("-v", "--verbose", action="store_true",
                          help="Verbose output.")
        parser.add_option("-d", "--debug", action="store_true",
                          help="FunkLoad and doctest debug output.")
        parser.add_option("--debug-level", type="int",
                          help="Debug level 3 is more verbose.")
        parser.add_option("-u", "--url", type="string", dest="main_url",
                          help="Base URL to bench without ending '/'.")
        parser.add_option("-m", "--sleep-time-min", type="string",
                          dest="ftest_sleep_time_min",
                          help="Minumum sleep time between request.")
        parser.add_option("-M", "--sleep-time-max", type="string",
                          dest="ftest_sleep_time_max",
                          help="Maximum sleep time between request.")
        parser.add_option("--dump-directory", type="string",
                          dest="dump_dir",
                          help="Directory to dump html pages.")
        parser.add_option("-V", "--firefox-view", action="store_true",
                          help="Real time view using firefox, "
                          "you must have a running instance of firefox "
                          "in the same host.")
        parser.add_option("--no-color", action="store_true",
                          help="Monochrome output.")
        parser.add_option("-l", "--loop-on-pages", type="string",
                          dest="loop_steps",
                          help="Loop as fast as possible without concurrency "
                          "on pages, expect a page number or a slice like 3:5."
                          " Output some statistics.")
        parser.add_option("-n", "--loop-number", type="int",
                          dest="loop_number", default=10,
                          help="Number of loop.")
        parser.add_option("--accept-invalid-links", action="store_true",
                          help="Do not fail if css/image links are "
                          "not reachable.")
        parser.add_option("--simple-fetch", action="store_true",
                          dest="ftest_simple_fetch",
                          help="Don't load additional links like css "
                          "or images when fetching an html page.")
        parser.add_option("--stop-on-fail", action="store_true",
                          help="Stop tests on first failure or error.")
        parser.add_option("-e", "--regex", type="string", default=None,
                          help="The test names must match the regex.")
        parser.add_option("--list", action="store_true",
                          help="Just list the test names.")
        parser.add_option("--doctest", action="store_true", default=False,
                          help="Check for a doc test.")
        parser.add_option("--pause", action="store_true",
                          help="Pause between request, "
                          "press ENTER to continue.")

        options, args = parser.parse_args()
        if self.module is None:
            if len(args) == 0:
                parser.error("incorrect number of arguments")
            # remove the .py
            module = args[0]
            if module.endswith('.py'):
                module =  os.path.basename(os.path.splitext(args[0])[0])
            self.module = module
        else:
            args.insert(0, self.module)
        if not options.doctest:
            global g_has_doctest
            g_has_doctest = False
        if options.verbose:
            self.verbosity = 2
        if options.quiet:
            self.verbosity = 0
            g_doctest_verbose = False
        if options.debug or options.debug_level:
            options.ftest_debug_level = 1
            options.ftest_log_to = 'console file'
            g_doctest_verbose = True
        else:
            options.ftest_log_to = 'file'
        if options.debug_level:
            options.ftest_debug_level = int(options.debug_level)
        self.color = not options.no_color
        self.test_name_pattern = options.regex
        self.list_tests = options.list

        # set testloader options
        self.testLoader.options = options
        if self.defaultTest is not None:
            self.testNames = [self.defaultTest]
        elif len(args) > 1:
            self.testNames = args[1:]
        # else we have to load all module test

    def runTests(self):
        """Launch the tests."""
        if self.testRunner is None:
            if self.color:
                self.testRunner = ColoredTextTestRunner(
                    verbosity=self.verbosity)
            else:
                self.testRunner = unittest.TextTestRunner(
                    verbosity=self.verbosity)
        result = self.testRunner.run(self.test)
        sys.exit(not result.wasSuccessful())



# ------------------------------------------------------------
# main
#
def main():
    """Default main."""
    # enable to load module in the current path
    cur_path = os.path.abspath(os.path.curdir)
    sys.path.insert(0, cur_path)
    # use our testLoader
    test_loader = TestLoader()
    TestProgram(testLoader=test_loader)


if __name__ == '__main__':
    main()
