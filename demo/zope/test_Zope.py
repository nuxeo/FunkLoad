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
"""Simple funkload zope tests

$Id$
"""
import unittest
from random import random
from funkload.ZopeTestCase import ZopeTestCase

class Zope(ZopeTestCase):
    """Testing the funkload ZopeTestCase

    This test use a configuration file Zope.conf.
    """

    def setUp(self):
        """Setting up test."""
        self.logd("setUp.")
        self.zope_url = self.conf_get('main', 'url')
        self.admin_id = self.conf_get('main', 'admin_id')
        self.admin_pwd = self.conf_get('main', 'admin_pwd')

    def test_flushCache(self):
        self.zopeFlushCache(self.zope_url, self.admin_id, self.admin_pwd)

    def test_restart(self):
        self.zopeRestart(self.zope_url, self.admin_id, self.admin_pwd,
                         time_out=10)

    def test_packZodb(self):
        self.zopePackZodb(self.zope_url, self.admin_id, self.admin_pwd)

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.")

if __name__ in ('main', '__main__'):
    unittest.main()
