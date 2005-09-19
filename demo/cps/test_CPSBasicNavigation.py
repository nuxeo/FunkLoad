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
from funkload.utils import xmlrpc_get_credential, xmlrpc_list_credentials

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

        self.cred_admin = xmlrpc_get_credential(credential_host,
                                                credential_port,
                                                'AdminZope')
        self.cred_manager =  xmlrpc_get_credential(credential_host,
                                                   credential_port,
                                                   'AdminCps')
        self.cred_member = xmlrpc_get_credential(credential_host,
                                                 credential_port,
                                                 'FL_Member')
        self.cred_reviewer = xmlrpc_get_credential(credential_host,
                                                   credential_port,
                                                   'FL_Reviewer')
        self.credential_host = credential_host
        self.credential_port = credential_port
        self.section_title = 'FunkLoad test' # Watchout title should generate
        self.section_id = 'funkload-test'    # this id
        self.workspace_title = 'FunkLoad test'
        self.workspace_id = 'funkload-test'


    def test_00_verif_cps(self):
        server_url = self.server_url
        if not self.exists(server_url):
            langs = self.conf_getList('main', 'languages')
            manager_mail = self.conf_get('test_00_verif_cps', 'manager_mail')
            self.cpsCreateSite(self.cred_admin[0], self.cred_admin[1],
                               self.cred_manager[0], self.cred_manager[1],
                               manager_mail, langs=langs,
                               title="CPSBasicNavigation Funkload Test Site")


    def test_05_verif_groups(self):
        server_url = self.server_url
        self.cpsLogin(self.cred_manager[0], self.cred_manager[1], "manager")
        for group in ('FL_Member', 'FL_Reviewer', 'FL_Manager'):
            self.cpsVerifyGroup(group)
        self.cpsLogout()


    def test_06_verif_users(self):
        server_url = self.server_url
        self.cpsLogin(self.cred_manager[0], self.cred_manager[1], "manager")
        for group in ('FL_Member', 'FL_Reviewer', 'FL_Manager'):
            for user_id, user_pwd in xmlrpc_list_credentials(
                self.credential_host, self.credential_port, group):
                self.cpsVerifyUser(user_id=user_id,
                                   user_pwd=user_pwd,
                                   groups=[group])
        self.cpsLogout()


    def test_10_create_doc(self):
        nb_docs = self.conf_getInt('test_10_create_doc', 'nb_docs')
        server_url = self.server_url
        login = self.cred_member[0]
        self.cpsLogin(login, self.cred_member[1], "member")
        for i in range(nb_docs):
            self.cpsCreateDocument("%s/workspaces/members/%s" %
                                   (server_url, login))
        self.cpsLogout()


    def test_20_verif_folders(self):
        server_url = self.server_url
        self.cpsLogin(self.cred_manager[0], self.cred_manager[1], "manager")
        section_url = '%s/sections/%s' % (server_url, self.section_id)
        if not self.exists(section_url):
            rurl = self.cpsCreateSection(
                '%s/sections' % server_url, self.section_title,
                'This is a FunkLoad test section, see '
                'http://svn.nuxeo.org/pub/funkload/trunk/README.txt '
                'for more information.')
            url = '%s/%s' % (server_url, rurl)
            self.cpsSetLocalRole(url, 'group:FL_Manager', 'SectionManager')
            self.cpsSetLocalRole(url, 'group:FL_Reviewer', 'SectionReviewer')
            self.cpsSetLocalRole(url, 'group:FL_Member', 'SectionReader')
        workspace_url = '%s/workspaces/%s' % (server_url, self.workspace_id)
        if not self.exists(workspace_url):
            rurl = self.cpsCreateWorkspace(
                '%s/workspaces' % server_url, self.workspace_title,
                'This is a FunkLoad test workspace, see '
                'http://svn.nuxeo.org/pub/funkload/trunk/README.txt '
                'for more information.')
            url = '%s/%s' % (server_url, rurl)
            self.cpsSetLocalRole(url, 'group:FL_Manager', 'WorkspaceManager')
            self.cpsSetLocalRole(url, 'group:FL_Member', 'WorkspaceMember')
        self.cpsLogout()


    def test_22_publish(self):
        server_url = self.server_url
        base_url = '%s/workspaces/%s' % (server_url, self.workspace_id)
        # begin of ftest ---------------------------------------------

        # login in as member -----------------------------------------
        self.cpsLogin(self.cred_member[0], self.cred_member[1],
                      "member")
        # access test ws
        self.get("%s/folder_contents" % base_url,
                 description="Folder contents")

        # create a document
        doc_rurl, doc_id = self.cpsCreateDocument(base_url)

        # pubish a doc
        doc_url = server_url + '/' + doc_rurl
        self.get("%s/content_submit_form" % doc_url,
                 description="View submit form")
        params = [["submit", "sections/%s" % self.section_id],
                  ["comments", "ftest submit"],
                  ["workflow_action", "copy_submit"]]
        self.post("%s/content_status_modify" % doc_url, params,
                  description="Submit the document")
        self.assert_(self.getLastUrl().find('psm_status_changed') != -1,
                     'Failed to publish %s into sections/%s' % (
            doc_rurl, self.section_id))

        # we sould see only one doc_id
        #self.assertEquals(len(self.cpsSearchDocId(doc_id)), 1,
        #"should see only one doc_id [%s]." % doc_id)
        self.cpsLogout()


        # login as reviewer ---------------------------------------
        self.cpsLogin(self.cred_reviewer[0],
                      self.cred_reviewer[1],
                      "reviewer")

        # accept the doc
        base_url2 = "%s/sections/%s" % (server_url, self.section_id)
        doc_publish_url = "%s/%s" % (base_url2, doc_id)
        self.get("%s/content_accept_form" % doc_publish_url,
                 description="View the accept form")
        params = [["comments", "Nice work %s" % self.cred_member[0]],
                  ["workflow_action", "accept"]]
        self.post("%s/content_status_modify" % doc_publish_url, params,
                  description="Accept the document")
        self.assert_(self.getLastUrl().find('psm_status_changed') != -1,
                     'Failed to accept %s' % doc_publish_url)

        # check that we have 2 doc_ids
        #self.assertEquals(len(self.cpsSearchDocId(doc_id)), 2,
        #                  "should see only one doc_id [%s]." % doc_id)
        self.cpsLogout()
        # end of ftest -----------------------------------------------
        return self.steps


    def test_30_reader_anonymous(self):
        server_url = self.server_url
        self.get('%s' % server_url,
                 description='Home page anonymous')

        self.assert_(self.listHref('login_form'), 'No login link found')

        self.get('%s/login_form' % server_url,
                 description="Login page")

        self.get("%s/accessibility" % server_url,
                 description="View accessibility information")

        self.get("%s/advanced_search_form" % server_url,
                 description="View advanced search form")

        # home page in different languages
        languages = self.conf_getList('main', 'languages')
        languages.reverse()             # to end with the first default one
        for lang in languages:
            self.cpsChangeUiLanguage(lang)
            self.get(server_url, description="Logged home page in %s" % lang)

        # XXX TODO check that private page are unaccessible



    def test_31_reader_member(self):
        server_url = self.server_url
        self.cpsLogin(self.cred_member[0], self.cred_member[1],
                      "member")

        self.get("%s/" % server_url, description="Home page logged")

        # home page in different languages
        languages = self.conf_getList('main', 'languages')
        languages.reverse()             # to end with the first default one
        for lang in languages:
            self.cpsChangeUiLanguage(lang)
            self.get(server_url, description="Logged home page in %s" % lang)

        # perso ws
        self.get("%s/workspaces/members/%s" % (server_url, self._cps_login),
                 description="View personal workspace")


        # test ws
        test_ws_url = '%s/workspaces/%s' % (server_url, self.workspace_id)
        self.get(test_ws_url, description="View FL test workspace")

        # view a random document
        docs = self.listDocumentHref('workspaces/%s/test-' %
                                        self.workspace_id)
        self.assert_(docs, "no doc found in ws %s" % self.workspace_id)

        a_doc = docs[int(len(docs) * random())]
        self.get("%s%s" % (server_url, a_doc),
                 description="View a document")

        # metadata
        self.get("%s%s/cpsdocument_metadata" % (server_url, a_doc),
                 description="View a document metadata")

        # export rss / atom
        self.get("%s/exportRssContentBox?box_url=.cps_boxes_root/nav_content"
                 % test_ws_url, description="View workspace RSS content")

        self.get("%s/exportAtomContentBox?box_url=.cps_boxes_root/nav_content"
                 % test_ws_url, description="View workspace Atom flux")

        # section
        self.get("%s/sections/%s" % (server_url, self.section_id),
                 description="View FL test section")

        # extract a doc link
        docs = self.listDocumentHref('/sections/%s/test-' % self.section_id)
        self.assert_(docs, "no doc found in section %s" % self.section_id)
        a_doc = docs[int(len(docs) * random())]

        self.get("%s%s" % (server_url, a_doc),
                 description="View a published document")

        self.get("%s%s/cpsdocument_metadata" % (server_url, a_doc),
                 description="View a published document metadata")

        self.get("%s%s/content_status_history" % (server_url, a_doc),
                 description="View a published document history")

        # access common cps pages
        self.get("%s/manage_my_subscriptions_form" % server_url,
                 description="View my subscription page.")

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
