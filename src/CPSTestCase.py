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

Author: ben

$Id: CPSTestCase.py 24728 2005-08-31 08:13:54Z bdelbosc $
"""
import time
from random import random
from Lipsum import Lipsum
from FunkLoadTestCase import FunkLoadTestCase

class CPSTestCase(FunkLoadTestCase):
    """Common cps task.

    setUp must set a server_url attrinute."""

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
        html = self.getBody()
        self.assert_(html.find('%s/logout' % self.server_url) >= 0,
                     'invalid credential: [%s:%s].' % (login, password))
        self._cps_login = login


    def cpsLogout(self):
        """Log out the current user."""
        if self._cps_login is not None:
            self.get('%s/logout' % self.server_url,
                     description="Log out [%s]" % self._cps_login)


    def cpsGetRandomLanguage(self):
        """Return a random language."""
        languages = ["en", "en", "en", "en",
                     "fr", "fr", "fr", "fr", "fr", # tsss
                     "de", "it", "es", "pt_BR", "nl", "mg", "ro", "eu"]
        language_count = len(languages)
        return languages[int(random()*language_count)]


    def cpsSearchDocId(self, doc_id):
        """Return the list of url that ends with doc_id.

        Using catalog search."""
        params = [["SearchableText", doc_id]]
        self.post("%s/search_form" % self.server_url, params,
                  description="Searching doc_id %s" % doc_id)
        ret_dup = [x for x in self.listHref() if x.endswith(doc_id)]
        # remove duplicate
        ret = []
        [ret.append(x) for x in ret_dup if not ret.count(x)]
        self.logd('Step %i:   found %s doc_id.' % (self.steps, len(ret)))
        return ret

    def cpsCreateNewsItem(self, parent_url):
        """Create a random news.

        return a tuple: (doc_url, doc_id)."""
        language = self.cpsGetRandomLanguage()
        if not hasattr(self, '_lipsum'):
            self._lipsum = Lipsum()
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

    def listDocumentHref(self, pattern):
        """Return a clean list of document href that matches pattern.

        Try to remove server_url and other cps trailings."""
        return [self.cpsCleanUrl(x) for x in self.listHref()
                if x.find(pattern) != -1]

