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
#
"""Dummy test used by test_Install.py

$Id$

simple doctest in a docstring:

  >>> 1 + 1
  2

"""
import os
import unittest
import commands

class TestDummy1(unittest.TestCase):
    """Dummy test case."""
    def test_dummy1_1(self):
        self.assertEquals(1+1, 2)

    def test_dummy1_2(self):
        self.assertEquals(1+1, 2)


class TestDummy2(unittest.TestCase):
    """Dummy test case."""
    def test_dummy2_1(self):
        self.assertEquals(1+1, 2)

    def test_dummy2_2(self):
        self.assertEquals(1+1, 2)

class TestDummy3(unittest.TestCase):
    """Failing test case not part of the test_suite."""
    def test_dummy3_1(self):
        self.assertEquals(1+1, 2)

    def test_dummy3_2(self):
        # failing test case
        self.assertEquals(1+1, 3, 'example of a failing test')

    def test_dummy3_3(self):
        # error test case
        impossible = 1/0
        self.assert_(1+1, 2)


class Dummy:
    """Testing docstring."""
    def __init__(self, value):
        self.value = value

    def double(self):
        """Return the double of the initial value.

        >>> d = Dummy(1)
        >>> d.double()
        2

        """
        return self.value * 2

def test_suite():
    """Return a test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDummy1))
    suite.addTest(unittest.makeSuite(TestDummy2))
    return suite

if __name__ in ('main', '__main__'):
    unittest.main()
