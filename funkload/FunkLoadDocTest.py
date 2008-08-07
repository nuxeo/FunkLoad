# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
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
"""FunkLoad doc test

$Id: FunkLoadDocTest.py 32254 2006-01-26 10:58:02Z bdelbosc $
"""
import os
from tempfile import gettempdir
from FunkLoadTestCase import FunkLoadTestCase
import FunkLoadLogger
import PatchWebunit

class FunkLoadDocTest(FunkLoadTestCase):
    """Class to use in doctest.

    >>> from FunkLoadDocTest import FunkLoadDocTest
    >>> fl = FunkLoadDocTest()
    >>> ret = fl.get('http://localhost')
    >>> ret.code
    200
    >>> 'HTML' in ret.body
    True

    """
    def __init__(self, debug=False, debug_level=1):
        """Initialise the test case."""
        class Dummy:
            pass
        options = Dummy()
        options.ftest_sleep_time_max = .001
        options.ftest_sleep_time_min = .001
        options.verbosity = FunkLoadLogger.INFO

        if debug:
            options.verbosity = FunkLoadLogger.DEBUG
            if debug_level:
                if debug_level >= 2:
                    options.verbosity = FunkLoadLogger.VDEBUG

        if options.verbosity >= FunkLoadLogger.DEBUG:
            log_to = getattr(options, 'ftest_log_to', '')
            if 'console' not in log_to:
                options.ftest_log_to = '%s console' % log_to

        tmp_path = gettempdir()
        options.ftest_log_path = os.path.join(tmp_path, 'fl-doc-test.log')
        options.ftest_result_path = os.path.join(tmp_path, 'fl-doc-test.xml')
        FunkLoadTestCase.__init__(self, 'runTest', options)

    def runTest(self):
        """FL doctest"""
        return


def _test():
    import doctest, FunkLoadDocTest
    return doctest.testmod(FunkLoadDocTest)

if __name__ == "__main__":
    _test()

