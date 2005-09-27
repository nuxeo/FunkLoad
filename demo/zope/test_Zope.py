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
from funkload.Lipsum import Lipsum


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

    def test_00_verifyExample(self):
        if not self.exists(self.zope_url + '/Examples'):
            self.setBasicAuth(self.admin_id, self.admin_pwd)
            self.get(self.zope_url +
                     '/manage_importObject?file=Examples.zexp&set_owner:int=1')
            self.assert_('successfully imported' in self.getBody())
            self.clearBasicAuth()
        self.get(self.zope_url + '/Examples')

    def test_exampleNavigation(self):
        server_url = self.zope_url

        self.get("%s/Examples" % server_url)
        self.get("%s/Examples/Navigation" % server_url)
        self.get("%s/Examples/Navigation/Mammals" % server_url)
        self.get("%s/Examples/Navigation/Mammals/Primates" % server_url)
        self.get("%s/Examples/Navigation/Mammals/Primates/Monkeys" % server_url)
        self.get("%s/Examples/Navigation/Mammals/Whales" % server_url)
        self.get("%s/Examples/Navigation/Mammals/Bats" % server_url)
        self.get("%s/Examples" % server_url)


    def test_exampleGuestBook(self):
        server_url = self.zope_url
        self.get("%s/Examples/GuestBook" % server_url)
        server_url = self.zope_url
        self.setBasicAuth(self.admin_id, self.admin_pwd)
        lipsum = Lipsum()
        self.get("%s/Examples/GuestBook/addEntry.html" % server_url)
        params = [["guest_name", lipsum.getWord().capitalize()],
                  ["comments", lipsum.getParagraph()]]
        self.post("%s/Examples/GuestBook/addEntry" % server_url, params)
        self.clearBasicAuth()


    def test_exampleFileLibrary(self):
        server_url = self.zope_url
        self.get("%s/Examples/FileLibrary" % server_url)
        for sort in ('type', 'size', 'date'):
            params = [["sort", sort],
                      ["reverse:int", "0"]]
            self.post("%s/Examples/FileLibrary/index_html" % server_url,
                      params,
                      description="File Library sort by %s" % sort)

    def test_exampleShoppingCart(self):
        server_url = self.zope_url

        self.get("%s/Examples/ShoppingCart" % server_url)
        params = [["orders.id:records", "510-115"],
                  ["orders.quantity:records", "1"],
                  ["orders.id:records", "510-122"],
                  ["orders.quantity:records", "2"],
                  ["orders.id:records", "510-007"],
                  ["orders.quantity:records", "3"]]
        self.post("%s/Examples/ShoppingCart/addItems" % server_url, params)


    def test_anonymous_reader(self):
        server_url = self.zope_url
        self.get("%s/Examples/Navigation/Mammals/Whales" % server_url)
        self.get("%s/Examples/GuestBook" % server_url)
        self.get("%s/Examples/GuestBook/addEntry.html" % server_url)
        params = [["sort", 'date'],
                  ["reverse:int", "0"]]
        self.get("%s/Examples/FileLibrary/index_html" % server_url, params)
        self.get("%s/Examples/ShoppingCart" % server_url)

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.")

if __name__ in ('main', '__main__'):
    unittest.main()
