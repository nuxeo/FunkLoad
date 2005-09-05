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
"""CPS basic navigation funkload test

$Id: test_CPSBasicNavigation.py 24747 2005-08-31 10:00:13Z bdelbosc $
"""
import unittest
from random import random
from funkload.CPSTestCase import CPSTestCase
from funkload.utils import xmlrpc_get_credential

class CPSBasicNavigation(CPSTestCase):
    """The funktional test case.

    This test use a configuration file CPSBasicNavigation.conf.
    """

    def setUp(self):
        """Setting up test."""
        self.logd("setUp.")
        self.server_url = self.conf_get('main', 'url')
        credential_host = self.conf_get('credential', 'host')
        credential_port = self.conf_getInt('credential', 'port')
        login, password = xmlrpc_get_credential(credential_host,
                                                credential_port,
                                                'Ftest_Manager')
        self.cred_manager = {'login': login,
                             'password': password}
        login, password = xmlrpc_get_credential(credential_host,
                                                credential_port,
                                                'Ftest_Member')
        self.cred_member = {'login': login,
                            'password': password}
        login, password = xmlrpc_get_credential(credential_host,
                                                credential_port,
                                                'Ftest_Reviewer')
        self.cred_reviewer = {'login': login,
                              'password': password}

    def test_01_create_doc(self):
        nb_docs = self.conf_getInt('test_01_create_doc', 'nb_docs')
        server_url = self.server_url
        login = self.cred_member['login']
        self.cpsLogin(login, self.cred_member['password'], "member")
        for i in range(nb_docs):
            self.cpsCreateNewsItem("%s/workspaces/members/%s" %
                                   (server_url, login))
        self.cpsLogout()


    def test_10_publish(self):
        server_url = self.server_url
        base_url = '%s/workspaces/ftest-workspace' % server_url
        # begin of ftest ---------------------------------------------

        # login in as member -----------------------------------------
        self.cpsLogin(self.cred_member['login'], self.cred_member['password'],
                      "member")
        # access ftest ws
        self.get("%s/folder_contents" % base_url,
                 description="Folder contents")
        params = [["theme", "default"],
                  ["page", "1713069120"]]
        self.get("%s/cpsskins_renderJS" % base_url,
                 description="CPSSkin js")

        # create a news
        doc_url, doc_id = self.cpsCreateNewsItem(base_url)

        # pubish a doc
        self.get("%s/content_submit_form" % doc_url,
                 description="View submit form")
        params = [["submit", "sections/ftest-section"],
                  ["comments", "ftest submit"],
                  ["workflow_action", "copy_submit"]]
        self.post("%s/content_status_modify" % doc_url, params,
                  description="Submit the document")
        # we sould see only one doc_id
        #self.assertEquals(len(self.cpsSearchDocId(doc_id)), 1,
        #"should see only one doc_id [%s]." % doc_id)
        self.cpsLogout()


        # login as reviewer ---------------------------------------
        self.cpsLogin(self.cred_reviewer['login'],
                      self.cred_reviewer['password'],
                      "reviewer")

        # accept the doc
        base_url2 = "%s/sections/ftest-section" % server_url
        doc_publish_url = "%s/%s" % (base_url2, doc_id)
        self.get("%s/content_accept_form" % doc_publish_url,
                 description="View the accept form")
        params = [["comments", "nice ftest work"],
                  ["workflow_action", "accept"]]
        self.post("%s/content_status_modify" % doc_publish_url, params,
                  description="Accept the document")

        # check that we have 2 doc_ids
        #self.assertEquals(len(self.cpsSearchDocId(doc_id)), 2,
        #                  "should see only one doc_id [%s]." % doc_id)
        self.cpsLogout()
        # end of ftest -----------------------------------------------
        return self.steps


    def test_20_reader(self):
        server_url = self.server_url

        # home page
        self.get('%s' % server_url,
                 description='Home page anonymous')

        self.assert_(self.listHref('login_form'), 'No login link found')

        # login page
        self.get('%s/login_form' % server_url,
                 description="Login page")

        # login in as member
        self.cpsLogin(self.cred_member['login'],
                      self.cred_member['password'],
                      "member")

        # home page
        self.get("%s/" % server_url, description="Home page logged")

        # home page in different languages
        for lang in self.conf_getList('test_20_reader', 'languages'):
            self.post("%s/cpsportlet_change_language" % server_url,
                      params=[['lang', lang]],
                      description="Home page in %s" % lang,
                      code=[200, 302, 204])

        # perso ws
        self.get("%s/workspaces/members/%s" % (server_url, self._cps_login),
                 description="View personal workspace")

        # extract a doc link and view the document
        my_docs = self.listDocumentHref('/workspaces/members/%s/test-' %
                                        self._cps_login)
        self.assert_(my_docs, "no doc found in personal ws")

        a_doc = my_docs[int(len(my_docs) * random())]
        self.get("%s%s" % (server_url, a_doc),
                 description="View a user document")

        # metadata
        self.get("%s%s/cpsdocument_metadata" % (server_url, a_doc),
                 description="View a user document metadata")

        # export rss / atom
        self.get("%s/workspaces/members/%s/exportRssContentBox?box_url=.cps_boxes_root/nav_content" % (server_url, self._cps_login),
                 description="View section RSS flux")

        self.get("%s/workspaces/members/%s/exportAtomContentBox?box_url=.cps_boxes_root/nav_content" % (server_url, self._cps_login),
                 description="View section Atom flux")

        # section
        self.get("%s/sections/ftest-section" % server_url,
                 description="View the main section")

        # extract a doc link
        my_docs = self.listDocumentHref('/sections/ftest-section/test-')
        self.assert_(my_docs, "no doc found in ftest-section")
        a_doc = my_docs[int(len(my_docs) * random())]

        self.get("%s%s" % (server_url, a_doc),
                 description="View a published document")

        self.get("%s%s/cpsdocument_metadata" % (server_url, a_doc),
                 description="View a published document metadata")

        self.get("%s%s/content_status_history" % (server_url, a_doc),
                 description="View a published document history")

        # access common cps pages
        self.get("%s/accessibility" % server_url,
                 description="View accessibility information")

        self.get("%s/advanced_search_form" % server_url,
                 description="View advanced search form")

        self.get("%s/cpsdirectory_view" % server_url,
                 description="View directories")

        params = [["dirname", "members"]]
        self.post("%s/cpsdirectory_entry_search_form" % server_url, params,
                  description="View member directory search form")

        params = [["dirname", "members"],
                  ["id", self._cps_login]]
        self.post("%s/cpsdirectory_entry_view" % server_url, params,
                  description="View user directory entry")

        self.cpsLogout()



    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.")


if __name__ in ('main', '__main__'):
    # even if fl-run-test is much better
    unittest.main()
