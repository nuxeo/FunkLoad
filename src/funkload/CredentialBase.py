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
"""Interface of a Credential Server.

$Id$
"""

class CredentialBaseServer:
    """Interface of a Credential server."""

    def getCredential(self, group=None):
        """Return a credential (login, password).

        If group is not None return a credential that belong to the group.
        """

    def listCredentials(self, group=None):
        """Return a list of all credentials.

        If group is not None return a list of credentials that belong to the
        group.
        """

    def listGroups(self):
        """Return a list of all groups."""
