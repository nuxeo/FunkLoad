# -*- coding: iso-8859-15 -*-
"""Simple FunkLoad test

$Id$
"""
import unittest
from random import random
from funkload.FunkLoadTestCase import FunkLoadTestCase

class Credential(FunkLoadTestCase):
    """This test use a configuration file Credential.conf."""

    def setUp(self):
        """Setting up test."""
        self.logd("setUp")
        self.server_url = self.conf_get('main', 'url')

    def test_credential(self):
        server_url = self.server_url
        ret = self.xmlrpc_call(server_url, 'getStatus',
                               description="Check getStatus")
        self.assert_('Server running' in ret, 'Server is down %s' % ret)
        self.logd('ret %s' % ret)
        ret = self.xmlrpc_call(server_url, 'reloadConf',
                               description="Reload configuration file")
        self.logd('ret %s' % ret)
        ret = self.xmlrpc_call(server_url, 'getRandomCredential',
                               description="Get a random credential")
        self.assertEquals(len(ret), 2, 'Invalid return %s' % ret)
        self.logd('ret %s' % ret)
        ret = self.xmlrpc_call(server_url, 'getFileCredential',
                               description="Get a credential from a file")
        self.assertEquals(len(ret), 2, 'Invalid return %s' % ret)
        self.logd('ret %s' % ret)
        ret = self.xmlrpc_call(server_url, 'listCredentials',
                               description="list all credential of the file")
        self.logd('ret %s' % ret)
        ret = self.xmlrpc_call(server_url, 'listGroups',
                               description="list groups from the group file")
        self.logd('ret %s' % ret)

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.\n")


if __name__ in ('main', '__main__'):
    unittest.main()
