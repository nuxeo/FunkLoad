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
"""A file credential server/controller.

$Id$
"""
import sys
from ConfigParser import NoOptionError

from XmlRpcBase import XmlRpcBaseServer, XmlRpcBaseController
from CredentialBase import CredentialBaseServer


# ------------------------------------------------------------
# classes
#
class Group:
    """A class to handle groups."""
    def __init__(self, name):
        self.name = name
        self.index = 0
        self.count = 0
        self.users = []

    def add(self, user):
        """Add a user to the group."""
        if not self.users.count(user):
            self.users.append(user)

    def __len__(self):
        """Return the lenght of group."""
        return len(self.users)

    def next(self):
        """Return the next user or the group.

        loop from begining."""
        nb_users = len(self.users)
        if nb_users == 0:
            raise ValueError('No users for group %s' % self.name)
        self.index = self.count % nb_users
        user = self.users[self.index]
        self.count += 1
        return user

    def __repr__(self):
        """Representation."""
        return '<group name="%s" count="%s" index="%s" len="%s" />' % (
            self.name, self.count, self.index, len(self))



# ------------------------------------------------------------
# Server
#
class CredentialFileServer(XmlRpcBaseServer, CredentialBaseServer):
    """A file credential server."""
    server_name = "file_credential"
    method_names = XmlRpcBaseServer.method_names + [
        'getCredential', 'listCredentials', 'listGroups', 'getSeq']

    credential_sep = ':'                    # login:password
    users_sep = ','                         # group_name:user1, user2

    def __init__(self, argv=None):
        self.lofc = 0
        self._groups = {}
        self._passwords = {}
        self.seq = 0
        XmlRpcBaseServer.__init__(self, argv)

    def _init_cb(self, conf, options):
        """init procedure to override in sub classes."""
        credentials_path = conf.get('server', 'credentials_path')
        self.lofc = conf.getint('server', 'loop_on_first_credentials')
        try:
            self.seq = conf.getint('server', 'seq')
        except NoOptionError:
            self.seq = 0
        self._loadPasswords(credentials_path)
        try:
            groups_path = conf.get('server', 'groups_path')
            self._loadGroups(groups_path)
        except NoOptionError:
            pass

    def _loadPasswords(self, file_path):
        """Load a password file."""
        self.logd("CredentialFile use credential file %s." % file_path)
        lines = open(file_path).readlines()
        self._groups = {}
        group = Group('default')
        self._groups[None] = group
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            user, password = [x.strip() for x in line.split(
                self.credential_sep, 1)]
            self._passwords[user] = password
            if not self.lofc or len(group) < self.lofc:
                group.add(user)

    def _loadGroups(self, file_path):
        """Load a group file."""
        self.logd("CredentialFile use group file %s." % file_path)
        lines = open(file_path).readlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            name, users = [x.strip() for x in line.split(
                self.credential_sep, 1)]
            users = filter(
                None, [user.strip() for user in users.split(self.users_sep)])
            group = self._groups.setdefault(name, Group(name))
            for user in users:
                if self.lofc and len(group) >= self.lofc:
                    break
                if self._passwords.has_key(user):
                    group.add(user)
                else:
                    self.logd('Missing password for %s in group %s' % (user,
                                                                       name))
    #
    # RPC
    def getCredential(self, group=None):
        """Return a credential from group if specified.

        Credential are taken incrementally in a loop.
        """
        user = self._groups[group].next()
        password = self._passwords[user]
        self.logd("getCredential(%s) return (%s, %s)" % (
            group, user, password))
        return (user, password)

    def listCredentials(self, group=None):
        """Return a list of credentials."""
        if group is None:
            ret = list(self._passwords)
        else:
            users = self._groups[group].users
            ret = [(user, self._passwords[user]) for user in users]
        self.logd("listUsers(%s) return (%s)" % (group, ret))
        return ret

    def listGroups(self):
        """Return a list of groups."""
        ret = filter(None, self._groups.keys())
        self.logd("listGroup() return (%s)" % str(ret))
        return ret

    def getSeq(self):
        """Return a sequence."""
        self.seq += 1
        return self.seq


# ------------------------------------------------------------
# Controller
#
class CredentialFileController(XmlRpcBaseController):
    """A file credential controller."""
    server_class = CredentialFileServer

    def test(self):
        """Testing credential server."""
        server = self.server
        self.log(server.listGroups())
        for i in range(10):
            self.log("%s getCredential() ... " % i)
            user, password = server.getCredential()
            self.log(" return (%s, %s)\n" % (user, password))
        for group in server.listGroups():
            self.log("group %s\n" % group)
            self.log("  content: %s\n" % server.listCredentials(group))
        for i in range(5):
            self.log("seq : %d" % server.getSeq())
        return 0

# ------------------------------------------------------------
# main
#
def main():
    """Control credentiald server."""
    ctl = CredentialFileController()
    sys.exit(ctl())

if __name__ == '__main__':
    main()
