# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Olivier Grisel ogrisel@nuxeo.com
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
"""Doctest support for CPS340TestCase

$Id$
"""

from CPS340TestCase import CPSTestCase
from FunkLoadDocTest import FunkLoadDocTest


class CPSDocTest(FunkLoadDocTest, CPSTestCase):
    """Class to use to doctest a CPS portal

    >>> from CPS340DocTest import CPSDocTest
    >>> cps_url = 'http://localhost:8080/cps'
    >>> fl = CPSDocTest(cps_url)
    >>> fl.cps_test_case_version
    (3, 4, 0)
    >>> fl.server_url == cps_url
    True

    Then you can use the CPS340TestCase API like fl.cpsLogin('manager', 'pwd').
    """
    def __init__(self, server_url, debug=False, debug_level=1):
        """init CPSDocTest

        server_url is the CPS server url."""
        FunkLoadDocTest.__init__(self, debug=debug, debug_level=debug_level)
        # FunkLoadDocTest handles the init of FunkLoadTestCase which is the
        # same as CPSTestCase
        self.server_url = server_url

def _test():
    import doctest, CPS340DocTest
    return doctest.testmod(CPS340DocTest)

if __name__ == "__main__":
    _test()
