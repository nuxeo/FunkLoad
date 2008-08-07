# -*- coding: iso-8859-15 -*-
"""Simple FunkLoad test

$Id: test_Simple.py 29381 2005-11-09 10:38:21Z bdelbosc $
"""
import unittest
from random import random
from funkload.FunkLoadTestCase import FunkLoadTestCase

class Simple(FunkLoadTestCase):
    """This test use a configuration file Simple.conf."""

    def setUp(self):
        """Setting up test."""
        self.logd("setUp")
        self.server_url = self.conf_get('main', 'url')

    def test_simple(self):
        # The description should be set in the configuration file
        server_url = self.server_url
        # begin of test ---------------------------------------------
        nb_time = self.conf_getInt('test_simple', 'nb_time')
        pages = self.conf_getList('test_simple', 'pages')

        for i in range(nb_time):
            self.logd('Try %i' % i)
            for page in pages:
                self.get(server_url + page, description='Get %s' % page)

        # end of test -----------------------------------------------

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.\n")


if __name__ in ('main', '__main__'):
    unittest.main()
