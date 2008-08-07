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
import unittest

from FunkLoadLogger import FunkLoadLogger
from FunkLoadBaseTestCase import FunkLoadBaseTestCase
from FunkLoadWebBrowser import FunkLoadWebBrowser

from utils import has_method


class FunkLoadWebTestCase(FunkLoadBaseTestCase):
    """FunkLoadBaseTestCase which happens to have a browser to play with."""

    def __init__(self, methodName='runTest', options=None):
        """Initialise the test case"""
        FunkLoadBaseTestCase.__init__(self, methodName=methodName,
                                      options=options)
        self.browser = FunkLoadWebBrowser(self.fconf, self.logger)

    def __getattr__(self, name):
        """Wrap around methods available in FunkLoadWebBrowser.

        This method is automatically called when an attribute is requested from
        an instance of FunkLoadWebTestCase which does not already exist in the
        namespace. This method intentionally only wraps around the methods in
        FunkLoadWebBrowser, as opposed to all attributes.

        Args:
          name: attribute name

        Raises:
          AttributeError: if requested attribute is not found

        Returns:
          requested attribute
        """
        if "browser" in self.__dict__ and has_method(self.browser, name):
            return getattr(self.browser, name)
        else:
            return FunkLoadBaseTestCase.__getattr__(self, name)

    def clearContext(self):
        """Reset the testcase."""
        FunkLoadBaseTestCase.clearContext(self)
        # NOTE(msparks): the base class calls self.clearContext() in its
        # __init__, and since we create self.browser after calling the base's
        # __init__ (because we need the base to set up self.fconf and
        # self.logger for us), we may not be prepared to call
        # self.browser.clearContext().
        if "browser" in self.__dict__:
            self.browser.clearContext()

    def gather_result(self):
        """Return a dictionary of a test case's final test results."""
        info = FunkLoadBaseTestCase.gather_result(self)
        info.update(self.browser.gather_result())
        return info


# ------------------------------------------------------------
# testing
#
class DummyTestCase(FunkLoadWebTestCase):
    """Testing Funkload TestCase."""

    def test_apache(self):
        """Simple apache test."""
        self.logger.logd('start apache test')
        for i in range(2):
            self.browser.get('http://localhost/')
            self.logger.logd('base_url: ' + self.browser.getLastBaseUrl())
            self.logger.logd('url: ' + self.browser.getLastUrl())
            self.logger.logd('hrefs: ' + str(self.browser.listHref()))
        self.logger.logd("Total connection time = %s" % self.browser.total_time)


if __name__ == '__main__':
    unittest.main()
