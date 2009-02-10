# -*- coding: iso-8859-15 -*-
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
"""cmf FunkLoad test

$Id$
"""
import unittest
from random import random
from funkload.FunkLoadTestCase import FunkLoadTestCase
from funkload.utils import xmlrpc_get_credential, xmlrpc_list_credentials
from funkload.Lipsum import Lipsum


class CmfTestCase(FunkLoadTestCase):
    """FL TestCase with common cmf tasks.

    self.server_url must be set.
    """
    def cmfLogin(self, login, pwd):
        params = [["__ac_name", login],
                  ["__ac_password", pwd],
                  ["__ac_persistent", "1"],
                  ["submit", " Login "]]
        self.post('%s/logged_in' % self.server_url, params,
                  description="Log xin user %s" % login)
        self.assert_('Login success' in self.getBody(),
                     "Invalid credential %s:%s" % (login, pwd))
        self._cmf_login = login

    def cmfLogout(self):
        self.get('%s/logout' % self.server_url,
                 description="logout %s" % self._cmf_login)


    def cmfCreateNews(self, parent_url):
        # return the doc_url
        lipsum = Lipsum()
        doc_id = lipsum.getUniqWord().lower()
        params = [["type_name", "News Item"],
                  ["id", doc_id],
                  ["add", "Add"]]
        self.post("%s/folder_factories" % parent_url, params,
                  description="Create an empty news")
        params = [["allow_discussion", "default"],
                  ["title", lipsum.getSubject()],
                  ["description:text", lipsum.getParagraph()],
                  ["subject:lines", lipsum.getWord()],
                  ["format", "text/plain"],
                  ["change_and_view", "Change and View"]]
        doc_url = "%s/%s" % (parent_url, doc_id)
        self.post("%s/metadata_edit_form" % doc_url, params,
                  description="Set metadata")
        self.assert_('Metadata changed.' in self.getBody())

        params = [["text_format", "plain"],
                  ["description:text", lipsum.getParagraph()],
                  ["text:text", lipsum.getMessage()],
                  ["change_and_view", "Change and View"]]
        self.post("%s/newsitem_edit_form" % doc_url, params,
                  description="Set news content")
        self.assert_('News Item changed.' in self.getBody())
        return doc_url





class Cmf(CmfTestCase):
    """Simple test of default CMF Site

    This test use a configuration file Cmf.conf.
    """
    def setUp(self):
        """Setting up test."""
        self.logd("setUp")
        self.server_url = self.conf_get('main', 'url')
        credential_host = self.conf_get('credential', 'host')
        credential_port = self.conf_getInt('credential', 'port')
        self.credential_host = credential_host
        self.credential_port = credential_port
        self.cred_admin = xmlrpc_get_credential(credential_host,
                                                credential_port,
                                                'AdminZope')
        self.cred_member = xmlrpc_get_credential(credential_host,
                                                 credential_port,
                                                 'FL_Member')

    def test_00_verifyCmfSite(self):
        server_url = self.server_url
        if self.exists(server_url):
            self.logd('CMF Site already exists')
            return
        site_id = server_url.split('/')[-1]
        zope_url = server_url[:-(len(site_id)+1)]
        self.setBasicAuth(*self.cred_admin)
        self.get("%s/manage_addProduct/CMFDefault/addPortal" % zope_url)
        params = [["id", site_id],
                  ["title", "FunkLoad CMF Site"],
                  ["create_userfolder", "1"],
                  ["description",
                   "See http://svn.nuxeo.org/pub/funkload/trunk/README.txt "
                   "for more info about FunkLoad"],
                  ["submit", " Add "]]
        self.post("%s/manage_addProduct/CMFDefault/manage_addCMFSite" %
                  zope_url, params, description="Create a CMF Site")
        self.get(server_url, description="View home page")
        self.clearBasicAuth()


    def test_05_verifyUsers(self):
        server_url = self.server_url
        user_mail = self.conf_get('test_05_verifyUsers', 'mail')
        lipsum = Lipsum()
        self.setBasicAuth(*self.cred_admin)
        for user_id, user_pwd in xmlrpc_list_credentials(
            self.credential_host, self.credential_port, 'FL_Member'):
            params = [["member_id", user_id],
                      ["member_email", user_mail],
                      ["password", user_pwd],
                      ["confirm", user_pwd],
                      ["add", "Register"]]
            self.post("%s/join_form" % server_url, params)
            html = self.getBody()
            self.assert_(
                'Member registered' in html or
                'The login name you selected is already in use' in html,
                "Member %s not created" % user_id)
        self.clearBasicAuth()

    def test_anonymous_reader(self):
        server_url = self.server_url
        self.get("%s/Members" % server_url,
                 description="Try to see Members area")
        self.get("%s/recent_news" % server_url,
                 description="Recent news")
        self.get("%s/search_form" % server_url,
                 description="View search form")
        self.get("%s/login_form" % server_url,
                 description="View login form")
        self.get("%s/join_form" % server_url,
                 description="View join form")

    def test_member_reader(self):
        server_url = self.server_url
        self.cmfLogin(*self.cred_member)
        url = '%s/Members/%s/folder_contents' % (server_url,
                                                 self.cred_member[0])
        self.get(url, description="Personal workspace")
        self.get('%s/personalize_form' % server_url,
                 description="Preference page")
        self.cmfLogout()

    def test_10_create_doc(self):
        nb_docs = self.conf_getInt('test_10_create_doc', 'nb_docs')
        server_url = self.server_url
        login = self.cred_member[0]
        self.cmfLogin(*self.cred_member)
        for i in range(nb_docs):
            self.cmfCreateNews("%s/Members/%s" %
                               (server_url, login))
        self.cmfLogout()

        # end of test -----------------------------------------------

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.\n")



if __name__ in ('main', '__main__'):
    unittest.main()
