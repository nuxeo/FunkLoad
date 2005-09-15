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
"""CPS Layer for funkload test.

$Id: CPSTestCase.py 24728 2005-08-31 08:13:54Z bdelbosc $
"""
import time
import random
from Lipsum import Lipsum
from ZopeTestCase import ZopeTestCase

class CPSTestCase(ZopeTestCase):
    """Common CPS tasks.

    setUp must set a server_url attribute."""
    server_url = None
    _lipsum = Lipsum()
    _all_langs = ['en', 'fr', 'de', 'it', 'es', 'pt_BR',
                  'nl', 'mg', 'ro', 'eu']
    _default_langs = _all_langs[:4]
    _cps_login = None

    def cpsLogin(self, login, password, comment=None):
        """Log in a user.

        Raise on invalid credential."""
        self._cps_login = None
        params = [['__ac_name', login],
                  ['__ac_password', password],
                  ['__ac_persistent', 'on'],
                  ['submit', 'Login'],
                  ]
        self.post("%s/logged_in" % self.server_url, params,
                  description="Log in user [%s] %s" % (login, comment or ''))
        # assume we are logged in if we have a logout link...
        self.assert_('%s/logout' % self.server_url in self.listHref(),
                     'invalid credential: [%s:%s].' % (login, password))
        self._cps_login = login


    def cpsLogout(self):
        """Log out the current user."""
        if self._cps_login is not None:
            self.get('%s/logout' % self.server_url,
                     description="Log out [%s]" % self._cps_login)


    def cpsGetRandomLanguage(self):
        """Return a random language."""
        return random.choice(self._all_langs)


    def cpsSearchDocId(self, doc_id):
        """Return the list of url that ends with doc_id.

        Using catalog search."""
        params = [["SearchableText", doc_id]]
        self.post("%s/search_form" % self.server_url, params,
                  description="Searching doc_id %s" % doc_id)
        ret = self.listDocumentHref(pattern='%s$' % doc_id)
        self.logd('found %i link ends with %s' % (len(ret), doc_id))
        return ret

    def cpsCreateNewsItem(self, parent_url):
        """Create a random news.

        return a tuple: (doc_url, doc_id)."""
        language = self.cpsGetRandomLanguage()
        title = self._lipsum.getSubject(uniq=True,
                                        prefix='test %s' % language)
        params = [["type_name", "News Item"],
                  ["widget__Title", title],
                  ["widget__Description", self._lipsum.getSubject(10)],
                  ["widget__LanguageSelectorCreation", language],
                  ["widget__photo_title", "none"],
                  ["widget__photo_filename", ""],
                  ["widget__photo_choice", "keep"],
                  ["widget__photo", ""],
                  ["widget__photo_resize", "img_auto_size"],
                  ["widget__photo_rposition", "left"],
                  ["widget__photo_subtitle", ""],
                  ["widget__content", self._lipsum.getMessage()],
                  ["widget__content_rformat", "text"],
                  ["widget__Subject:tokens:default", ""],
                  ["widget__Subject:list", "Business"],
                  ["widget__publication_date_date", time.strftime('%m/%d/%Y')],
                  ["widget__publication_date_hour", time.strftime('%H')],
                  ["widget__publication_date_minute", time.strftime('%M')],
                  ["cpsdocument_create_button", "Create"]]
        self.post("%s/cpsdocument_create_form" % parent_url, params,
                  description="Creating a news item")
        doc_url = self.getLastBaseUrl()[:-1]
        doc_id = doc_url[len(parent_url)+1:]
        return doc_url, doc_id

    def cpsCleanUrl(self, url_in):
        """Try to remove server_url and clean ending."""
        url = url_in
        server_url = self.server_url
        for ending in ('/', '/view', '/folder_contents',
                       '/folder_view', '/cpsdocument_metadata',
                       '/cpsdocument_edit_form'):
            if url.endswith(ending):
                url = url[:-len(ending)]
            if url.startswith(server_url):
                url = url[len(server_url):]
        return url

    def listDocumentHref(self, pattern=None):
        """Return a clean list of document href that matches pattern.

        Try to remove server_url and other cps trailings,
        return a list of uniq url."""
        ret = []
        for href in [self.cpsCleanUrl(x) for x in self.listHref(pattern)]:
            if href not in ret:
                ret.append(href)
        return ret


    def cpsGuessZopeUrl(self):
        """Guess a zope url and site_id from a CPS Site url.

        return a tuple (zope_url, site_id)
        """
        server_url = self.server_url
        site_id = server_url.split('/')[-1]
        zope_url = server_url[:-(len(site_id)+1)]
        return zope_url, site_id


    def cpsCreateSite(self, admin_id, admin_pwd,
                      manager_id, manager_password,
                      manager_mail, langs=None, title=None,
                      description=None,
                      interface="portlets",
                      zope_url=None,
                      site_id=None):
        """Create a CPS Site.

        if zope_url or site_id is not provided guess them from the server_url.
        """
        if zope_url is None or site_id is None:
            zope_url, site_id = self.cpsGuessZopeUrl()
        self._browser.setBasicAuth(admin_id, admin_pwd)
        params = {"id": site_id,
                  "title": title or "CPS Portal",
                  "description": description or "A funkload cps test site",
                  "manager_id": manager_id,
                  "manager_password": manager_password,
                  "manager_password_confirmation": manager_password,
                  "manager_email": manager_mail,
                  "manager_sn": "CPS",
                  "manager_givenName": "Manager",
                  "langs_list:list": langs or self._default_langs,
                  "interface": interface,
                  "submit": "Create"}
        self.post("%s/manage_addProduct/CPSDefault/manage_addCPSDefaultSite" %
                  zope_url, params, description="Create a CPS Site")
        self._browser.clearBasicAuth()


    def cpsCreateGroup(self, group_name):
        """Create a cps group."""
        self.logd("Check that group [%s] exists." % group_name)
        server_url = self.server_url

        params = [["dirname", "groups"],
                  ["id", group_name],]
        params = [["dirname", "groups"],
                  ["id", ""],
                  ["widget__group", group_name],
                  ["widget__members:tokens:default", ""],
                  ["cpsdirectory_entry_create_form:method", "Create"]]
        self.post("%s/" % server_url, params)
        self.assert_(self.getLastUrl().find('psm_entry_created')!=-1,
                     '%s entry not created last url is %s' % (
            group_name, self.getLastUrl()))


    def cpsSetLocalRole(self, url, name, role):
        """Grant role to name in url."""
        self.logd('Grant local role [%s] to [%s]' % (
            role, name))
        params = [["member_ids:list", name],
                  ["member_role", role]]
        self.post("%s/folder_localrole_add" % url, params)


    def cpsCreateSection(self, parent_url, title,
                         description="ftest section for funkload testing.",
                         lang=None):
        """Create a section."""
        self.cpsCreateFolder('Section', parent_url, title, description,
                             lang or self.cpsGetRandomLanguage())


    def cpsCreateWorkspace(self, parent_url, title,
                           description="ftest workspace for funkload testing.",
                           lang=None):
        """Create a workspace."""
        self.cpsCreateFolder('Workspace', parent_url, title, description,
                             lang or self.cpsGetRandomLanguage())

    def cpsCreateFolder(self, type, parent_url, title,
                        description, lang):
        """Create a section or a workspace.

        Return the section full url."""
        params = [["type_name", type],
                  ["widget__Title", title],
                  ["widget__Description",
                   description],
                  ["widget__LanguageSelectorCreation", lang],
                  ["widget__hidden_folder", "0"],
                  ["cpsdocument_create_button", "Create"]]
        self.post("%s/cpsdocument_create_form" % parent_url,
                  params, "Create a %s" % type)
        return self.getLastBaseUrl()[:-1]


