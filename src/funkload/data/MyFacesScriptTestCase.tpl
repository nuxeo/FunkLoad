# -*- coding: iso-8859-15 -*-
"""%(test_name)s FunkLoad test

$Id: $
"""
import unittest
from funkload.FunkLoadTestCase import FunkLoadTestCase
from webunit.utility import Upload
from funkload.utils import Data
#from funkload.utils import xmlrpc_get_credential

class %(class_name)s(FunkLoadTestCase):
    """XXX

    This test use a configuration file %(class_name)s.conf.
       """
    MYFACES_STATE = 'org.apache.myfaces.trinidad.faces.STATE'
    MYFACES_FORM = 'org.apache.myfaces.trinidad.faces.FORM'
    MYFACES_TAG = '<input type="hidden" name="org.apache.myfaces.trinidad.faces.STATE" value="'

    def myfacesParams(self, params, form=None):
        """Add MyFaces states to the params."""
        html = self.getBody()
        tag = self.MYFACES_TAG
        start = html.find(tag) + len(tag)
        end = html.find('"', start)
        if start < 0 or end < 0:
            raise ValueError('No MyFaces STATE found in the previous page.')
        state = html[start:end]
        params.insert(
                0, [self.MYFACES_STATE, state])
        if form:
            params.insert(
                0, [self.MYFACES_FORM, form])
        return params

    def setUp(self):
        """Setting up test."""
        self.logd("setUp")
        self.server_url = self.conf_get('main', 'url')
        # XXX here you can setup the credential access like this
        # credential_host = self.conf_get('credential', 'host')
        # credential_port = self.conf_getInt('credential', 'port')
        # self.login, self.password = xmlrpc_get_credential(credential_host,
        #                                                   credential_port,
        # XXX replace with a valid group
        #                                                   'members')

    def test_%(test_name)s(self):
        # The description should be set in the configuration file
        server_url = self.server_url
        # begin of test ---------------------------------------------
%(script)s

        # end of test -----------------------------------------------

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.\n")



if __name__ in ('main', '__main__'):
    unittest.main()
