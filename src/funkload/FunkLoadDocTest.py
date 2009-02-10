# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
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
"""FunkLoad doc test

$Id$
"""
import os
from tempfile import gettempdir
from FunkLoadTestCase import FunkLoadTestCase
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
        option = Dummy()
        option.ftest_sleep_time_max = .001
        option.ftest_sleep_time_min = .001
        if debug:
            option.ftest_log_to = 'console file'
            if debug_level:
                option.debug_level = debug_level
        else:
            option.ftest_log_to = 'file'
        tmp_path = gettempdir()
        option.ftest_log_path = os.path.join(tmp_path, 'fl-doc-test.log')
        option.ftest_result_path = os.path.join(tmp_path, 'fl-doc-test.xml')
        FunkLoadTestCase.__init__(self, 'runTest', option)

    def runTest(self):
        """FL doctest"""
        return


def _test():
    import doctest, FunkLoadDocTest
    return doctest.testmod(FunkLoadDocTest)

if __name__ == "__main__":
    _test()

