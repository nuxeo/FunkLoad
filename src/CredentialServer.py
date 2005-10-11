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
"""Simple XMLRPC server that return credentials.

Used by load tests to get a different login/password each time it is called.
See credentialctl.py for client example and credential.conf for server options.

Porvide getCredential, getFileCredential and getRandomCredential methods.

Usage: ./credentiald.py <configuration_file>.

$Id: credentiald.py 24649 2005-08-29 14:20:19Z bdelbosc $
"""
import sys, os
import socket
from random import random
from time import sleep
from ConfigParser import ConfigParser, NoOptionError
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy
import logging
from optparse import OptionParser, TitledHelpFormatter

from utils import create_daemon, get_default_logger, trace


# ------------------------------------------------------------
# globals
#
g_quit = 0                              # flag to stop the xml server


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
# rpc to manage the server
#
class MySimpleXMLRPCServer(SimpleXMLRPCServer):
    """SimpleXMLRPCServer with allow_reuse_address."""
    # this property set SO_REUSEADDR which tells the operating system to allow
    # code to connect to a socket even if it's waiting for other potential
    # packets
    allow_reuse_address = True



# ------------------------------------------------------------
# Service Classes
#

class BaseCredentialServer:
    """Base class for credential server."""
    def __init__(self, conf_path, logger):
        """Initialiase"""
        self.logger = logger
        self.conf_path = conf_path
        conf = ConfigParser()
        conf.read(conf_path)
        self.conf = conf

    def logd(self, message):
        """Debug log."""
        self.logger.debug(message)

    def log(self, message):
        """Log information."""
        self.logger.info(message)

    # xml rpc
    #
    def stopServer(self):
        """Stop the server."""
        global g_quit
        self.log("stopServer stopping credential server.")
        g_quit = 1
        return 1

    def reloadConf(self):
        """Reload the configuration file."""
        raise NotImplementedError

    def getCredential(self, group=None):
        """Return a (login, password)."""
        raise NotImplementedError

    def getStatus(self):
        """Return a status."""
        return "%s running pid = %s" % (self.__class__.__name__, os.getpid())

    def listCredentials(self, group=None):
        """Return a list of credentials."""
        raise NotImplementedError

    def listGroups(self, group=None):
        """Return a list of groups."""
        raise NotImplementedError


class RandomCredentialServer(BaseCredentialServer):
    """A random credential server."""
    def __init__(self, conf_path, logger):
        BaseCredentialServer.__init__(self, conf_path, logger)
        self._call_count = 0

    def getCredential(self, group=None):
        """Return a (login, password)."""
        self._call_count += 1
        ran = int(random() * 1000)
        user = 'user_%s' % ran
        password = 'pwd_%s' % ran
        self.logd("%s getRandomCredential() return (%s, %s)" % (
            self._call_count, user, password))
        return (user, password)


class FileCredentialServer(BaseCredentialServer):
    """A server that render credentials using pwd and group files."""
    CREDENTIAL_SEP = ':'                    # login:password
    USERS_SEP = ','                         # group_name:user1, user2

    def __init__(self, conf_path, logger):
        BaseCredentialServer.__init__(self, conf_path, logger)
        self.lofc = 0
        self._call_count = 0
        self.mode = 'file'
        self._groups = {}
        self._passwords = {}
        self._loadConf()

    def _loadConf(self):
        """Load a configuration file."""
        conf = self.conf
        credentials_path = conf.get('server', 'credentials_path')
        self.lofc = conf.getint('server', 'loop_on_first_credentials')
        self._loadPasswords(credentials_path)
        try:
            groups_path = conf.get('server', 'groups_path')
            self._loadGroups(groups_path)
        except NoOptionError:
            pass

    def _loadPasswords(self, file_path):
        """Load a password file."""
        self.logd("getFileCredential use credential file %s." % file_path)
        lines = open(file_path).readlines()
        self._groups = {}
        group = Group('default')
        self._groups[None] = group
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            user, password = [x.strip() for x in line.split(
                self.CREDENTIAL_SEP, 1)]
            self._passwords[user] = password
            if not self.lofc or len(group) < self.lofc:
                group.add(user)

    def _loadGroups(self, file_path):
        """Load a group file."""
        self.logd("getFileCredential use group file %s." % file_path)
        lines = open(file_path).readlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            name, users = [x.strip() for x in line.split(
                self.CREDENTIAL_SEP, 1)]
            users = filter(
                None, [user.strip() for user in users.split(self.USERS_SEP)])
            group = self._groups.setdefault(name, Group(name))
            for user in users:
                if self.lofc and len(group) >= self.lofc:
                    break
                if self._passwords.has_key(user):
                    group.add(user)
                else:
                    self.logd('Missing password for %s in group %s' % (user,
                                                                       name))

    def reloadConf(self):
        """Reload the configuration file."""
        self._loadConf()


    def getCredential(self, group=None):
        """Return a credential from group if specified.

        Credential are taken incrementally in a loop.
        """
        self._call_count += 1
        user = self._groups[group].next()
        password = self._passwords[user]
        self.logd("%s getFileCredential(%s) return (%s, %s)" % (
            self._call_count, group, user, password))
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


    def listGroups(self, group=None):
        """Return a list of groups."""
        ret = filter(None, self._groups.keys())
        self.logd("listGroup() return (%s)" % str(ret))
        return ret



# ------------------------------------------------------------
# main
#

class CredentialServer:
    """The credential server Runner."""

    usage = """%prog [options] config_file

%prog launch a credential server.
"""
    def __init__(self, argv=None):
        self.server = None
        if argv is None:
            argv = sys.argv
        conf_path, options = self.parseArgs(argv)
        # read conf
        conf = ConfigParser()
        conf.read(conf_path)
        self.conf_path = conf_path
        self.host = conf.get('server', 'host')
        self.port = int(conf.get('server', 'port'))
        if self.isServerRunning():
            trace("Server already running on %s:%s." % (self.host, self.port))
            sys.exit(0)
        try:
            self.pid_path = conf.get('server', 'pid_path')
        except NoOptionError:
            self.pid_path = 'credentiald.pid'
        self.mode = conf.get('server', 'mode')
        log_path = conf.get('server', 'log_path')
        if not options.debug:
            trace('Starting credential server as daemon\n')
            create_daemon()
        if options.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        if options.debug:
            log_to = 'file console'
        else:
            log_to = 'file'
        self.logger = get_default_logger(log_to, log_path,
                                         level=level,
                                         name='credentiald')
        self.initServer()
        self.run()

    def isServerRunning(self):
        """Check if the server is already running."""
        server = ServerProxy("http://%s:%s" % (self.host, self.port))
        try:
            server.getStatus()
        except socket.error:
            return False
        return True

    def parseArgs(self, argv):
        """Parse programs args."""
        parser = OptionParser(self.usage, formatter=TitledHelpFormatter())
        parser.add_option("-q", "--quiet", action="store_true",
                          help="Minimal output")
        parser.add_option("-v", "--verbose", action="store_true",
                          help="Verbose output")
        parser.add_option("-d", "--debug", action="store_true",
                          help="debug mode not in background")

        options, args = parser.parse_args(argv)
        if len(args) == 0:
            parser.error("Missing configuration file")
        return args[-1], options

    def initServer(self):
        """init the XMLRPC Server."""
        logger = self.logger
        mode = self.mode
        if mode == 'file':
            credential = FileCredentialServer(self.conf_path, logger)
        elif mode == 'random':
            credential = RandomCredentialServer(self.conf_path, logger)
        else:
            raise NotImplementedError("mode %s" % mode)

        # setup rpc
        logger.info("Init XMLRPC server %s:%s." % (self.host, self.port))
        server = MySimpleXMLRPCServer((self.host, self.port))
        server.register_function(credential.stopServer)
        server.register_function(credential.getStatus)
        server.register_function(credential.reloadConf)
        server.register_function(credential.getCredential)
        server.register_function(credential.listCredentials)
        server.register_function(credential.listGroups)
        self.server = server

    def run(self):
        """Init and run XMLRPC Server."""
        global g_quit
        pid = os.getpid()
        server = self.server
        open(self.pid_path, "w").write(str(pid))
        self.logger.info("credential server pid=%i started." % pid)
        while not g_quit:
            server.handle_request()
        sleep(1)
        server.server_close()
        self.logger.info("credential server pid=%i stopped." % pid)
        os.remove(self.pid_path)


if __name__ == '__main__':
    CredentialServer()
