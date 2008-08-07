# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Tim Baverstock, Matthew Vail, Matt Sparks
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
from FunkLoadConfig import FunkLoadConfig
from FunkLoadLogger import FunkLoadLogger

from utils import mmn_is_bench, mmn_decode, thread_sleep
from utils import has_method

import sys
import time
import unittest

_marker = []


class FunkLoadBaseTestCase(unittest.TestCase):
    """Unit test with logging and configuration capabilities.

    This is a base class, from which HTTP, UDP, LDAP classes can derive."""
    # ------------------------------------------------------------
    # Initialization
    #
    def __init__(self, methodName='runTest', options=None):
        """Initialize the test case.

        Note that methodName is encoded in bench mode to provide additional
        information like thread_id, concurrent virtual users, e.g.:

          test_Foo:1:20:2

        encodes: test_Foo test, cycle 1, 20 CVUs, thread id 2.
        """

        self.meta_method_name = methodName

        self.test_name, self.cycle, self.cvus, self.thread_id = mmn_decode(
            methodName)
        unittest.TestCase.__init__(self, methodName=self.test_name)

        suite_name = self.__class__.__name__
        self.fcontext = {}
        self.fcontext['name'] = self.test_name
        self.fcontext['cycle'] = '%.3i' % self.cycle
        self.fcontext['cvus'] = '%.3i' % self.cvus
        self.fcontext['thread'] = '%.3i' % self.thread_id
        self.fcontext['suite'] = suite_name

        if mmn_is_bench(methodName):
            in_bench_mode = True
            section = 'bench'
        else:
            in_bench_mode = False
            section = 'ftest'

        # TODO(msparks): clean up conf/logger interaction
        self.fconf = FunkLoadConfig(section, methodName, suite_name, options,
                                    class_name=self.__class__.__name__)
        self.logger = FunkLoadLogger(methodName, self.fconf)
        # NOTE(msparks): tell config where the real logger is now that one has
        # been created.
        self.fconf.set_logger(self.logger)
        self.sleep_time_min = self.fconf.getFloat('sleep_time_min', 0)
        self.sleep_time_max = self.fconf.getFloat('sleep_time_max', 0)
        self._stop_on_fail = self.fconf.opt_get('stop_on_fail', False)
        self.clearContext()

    def __getattr__(self, name):
        """Wrap around methods available in FunkLoadLogger.

        This method is automatically called when an attribute is requested from
        an instance of FunkLoadBaseTestCase which does not already exist in the
        namespace. This method intentionally only wraps around the methods in
        FunkLoadLogger, as opposed to all attributes.

        Args:
          name: attribute name

        Raises:
          AttributeError: if requested attribute is not found

        Returns:
          requested attribute
        """
        if "logger" in self.__dict__ and has_method(self.logger, name):
            return getattr(self.logger, name)
        else:
            raise AttributeError, ("object has no attribute '%s'" % name)

    def clearContext(self):
        """Reset the testcase."""
        self.test_status = 'Successful'
        self.logger.logdd('FunkLoadBaseTestCase.clearContext done')

    #------------------------------------------------------------
    # Configuration access methods for backward-compatibility
    #
    def conf_get(self, section, key, default=_marker, quiet=False):
        """Return an entry from the options or configuration file."""
        return self.fconf.get(section=section, key=key, default=default,
                              quiet=quiet)

    def conf_getInt(self, section, key, default=_marker, quiet=False):
        """Return an integer from the configuration file."""
        return self.fconf.getInt(section=section, key=key, default=default,
                                 quiet=quiet)

    def conf_getFloat(self, section, key, default=_marker, quiet=False):
        """Return a float from the configuration file."""
        return self.fconf.getFloat(section=section, key=key, default=default,
                                   quiet=quiet)

    def conf_getList(self, section, key, default=_marker, quiet=False,
                     separator=None):
        """Return a list from the configuration file."""
        return self.fconf.getList(section=section, key=key, default=default,
                                  quiet=quiet, separator=separator)

    def sleep(self):
        """Sleeps a random amount of time.

        Between the predefined sleep_time_min and sleep_time_max values.
        """
        s_min = self.sleep_time_min
        s_max = self.sleep_time_max
        if s_max > s_min:
            s_val = s_min + (s_max - s_min) * random()
        else:
            s_val = s_min
        # we should always sleep something
        thread_sleep(s_val)

    #------------------------------------------------------------
    # Extend unittest.TestCase to provide bench cycle hook
    #
    def setUpCycle(self):
        """Called on bench mode before a cycle start."""
        pass

    def tearDownCycle(self):
        """Called after a cycle in bench mode."""
        pass


    #------------------------------------------------------------
    # Overriding unittest.TestCase
    #
    def __call__(self, result=None):
        """Run the test method.

        Override to log test result."""
        t_start = time.time()
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        if sys.version_info >= (2, 5):
            testMethod = getattr(self, self._testMethodName)
        else:
            testMethod = getattr(self, self._TestCase__testMethodName)
        try:
            ok = False
            try:
                self.logger.logd(
                    'Starting -----------------------------------\n\t%s'
                    % self.fconf.get('description', default='',
                        section=self.meta_method_name))
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                self.test_status = 'Error'
                self._log_result(t_start, time.time())
                return
            try:
                testMethod()
                ok = True
            except self.failureException:
                if sys.version_info >= (2, 5):
                    result.addFailure(self, self._exc_info())
                else:
                    result.addFailure(self, self._TestCase__exc_info())
                self.test_status = 'Failure'
            except KeyboardInterrupt:
                raise
            except:
                if sys.version_info >= (2, 5):
                    result.addFailure(self, self._exc_info())
                else:
                    result.addError(self, self._TestCase__exc_info())
                self.test_status = 'Error'
            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                if sys.version_info >= (2, 5):
                    result.addFailure(self, self._exc_info())
                else:
                    result.addError(self, self._TestCase__exc_info())
                self.test_status = 'Error'
                ok = False
            if ok:
                result.addSuccess(self)
        finally:
            self._log_result(t_start, time.time())
            if not ok and self._stop_on_fail:
                result.stop()
            result.stopTest(self)

    def gather_result(self):
        """Return a dictionary of a test case's final test results.

        Implementations should enlarge on the dictionary returned by the
        superclass's implementation. The default set of values provided by the
        base class (test start and stop times, test and suite name, cvus,
        cycle count, thread id, and test success/failure). For example, the
        web test case gives total connection time, number of requests made,
        pages loaded, images loaded, etc."""
        info = {}
        info.update(self.fcontext)
        info['result'] = self.test_status
        return info

    def _log_result(self, time_start, time_stop):
        """Log the overall result of each test."""
        info = self.gather_result()
        info['time'] = '%.6f' % time_start
        info['duration'] = '%.6f' % (time_stop - time_start)
        self.logger.results.write('testResult', info)

