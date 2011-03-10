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
"""FunkLoad test case for Zope.

$Id$
"""
import time
from socket import error as SocketError
from FunkLoadTestCase import FunkLoadTestCase


class ZopeTestCase(FunkLoadTestCase):
    """Common zope 2.8 tasks."""

    def zopeRestart(self, zope_url, admin_id, admin_pwd, time_out=600):
        """Stop and Start Zope server."""
        self.setBasicAuth(admin_id, admin_pwd)
        params = {"manage_restart:action": "Restart"}
        url = "%s/Control_Panel" % zope_url
        self.post(url, params, description="Restarting Zope server")
        down = True
        time_start = time.time()
        while(down):
            time.sleep(2)
            try:
                self.get(url, description="Checking zope presence")
            except SocketError:
                if time.time() - time_start > time_out:
                    self.fail('Zope restart time out %ss' % time_out)
            else:
                down = False

        self.clearBasicAuth()

    def zopePackZodb(self, zope_url, admin_id, admin_pwd,
                     database="main", days=0):
        """Pack a zodb database."""
        self.setBasicAuth(admin_id, admin_pwd)
        url = '%s/Control_Panel/Database/%s/manage_pack' % (
            zope_url, database)
        params = {'days:float': str(days)}
        resp = self.post(url, params,
                         description="Packing %s Zodb, removing previous "
                         "revisions of objects that are older than %s day(s)."
                         % (database, days), ok_codes=[200, 302, 500])
        if resp.code == 500:
            if self.getBody().find(
                "Error Value: The database has already been packed") == -1:
                self.fail("Pack_zodb return a code 500.")
            else:
                self.logd('Zodb has already been packed.')
        self.clearBasicAuth()

    def zopeFlushCache(self, zope_url, admin_id, admin_pwd, database="main"):
        """Remove all objects from all ZODB in-memory caches."""
        self.setBasicAuth(admin_id, admin_pwd)
        url = "%s/Control_Panel/Database/%s/manage_minimize" % (zope_url,
                                                                database)
        self.get(url, description="Flush %s Zodb cache" % database)

    def zopeAddExternalMethod(self, parent_url, admin_id, admin_pwd,
                              method_id, module, function,
                              run_it=True):
        """Add an External method an run it."""
        self.setBasicAuth(admin_id, admin_pwd)
        params = [["id", method_id],
                  ["title", ""],
                  ["module", module],
                  ["function", function],
                  ["submit", " Add "]]
        url = parent_url
        url += "/manage_addProduct/ExternalMethod/manage_addExternalMethod"
        resp = self.post(url, params, ok_codes=[200, 302, 400],
                         description="Adding %s external method" % method_id)
        if resp.code == 400:
            if self.getBody().find('is invalid - it is already in use.') == -1:
                self.fail('Error got 400 on manage_addExternalMethod')
            else:
                self.logd('External method already exists')
        if run_it:
            self.get('%s/%s' % (parent_url, method_id),
                     description="Execute %s external method" % method_id)
        self.clearBasicAuth()
