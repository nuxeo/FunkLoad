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
"""FunkLoad test case using Richard Jones' webunit.

$Id: FunkLoadTestCase.py 24757 2005-08-31 12:22:19Z bdelbosc $
"""
import unittest
from FunkLoadWebTestCase import FunkLoadWebTestCase


class FunkLoadTestCase(FunkLoadWebTestCase):
    """Wrapper class around FunkLoadWebTestCase for backward compatibility."""
    def __init__(self, methodName='runTest', options=None):
        FunkLoadWebTestCase.__init__(self, methodName, options)


if __name__ == '__main__':
    unittest.main()
