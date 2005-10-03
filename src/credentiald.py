#!/usr/bin/python

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
from time import gmtime, strftime, sleep
from ConfigParser import ConfigParser, NoOptionError
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy

CONF_PATH = "credential.conf"
CREDENTIAL_SEP = ':'                    # login:password
USERS_SEP = ','                         # group_name:user1, user2

# ------------------------------------------------------------
# globals
#
g_quit = 0                              # flag to stop the xml server
g_conf_path = ''                        # the credential configuration path
g_call_count = 0                        # number of getCredential call

g_mode = 'file'                         # file or random mode
g_groups = {}                           # map of groups
g_passwords = {}                        # user pwd


# ------------------------------------------------------------
# utils
#
def get_time_stamp():
    """Return a time stamp string."""
    return strftime('%Y-%m-%dT%H-%M-%S', gmtime())

def log(msg):
    """Print to stdout and flush."""
    print get_time_stamp() + " srv " + msg
    sys.stdout.flush()


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
    # this property set SO_REUSEADDR which tells the operating system to allow
    # code to connect to a socket even if it's waiting for other potential
    # packets
    allow_reuse_address = True


def stopServer():
    """Stop the server."""
    global g_quit
    log("""stopServer stopping credential server.""")
    g_quit = 1
    return 1


def getStatus():
    """Return the server status."""
    global g_mode, g_groups
    return "Server running mode %s: %s" % (g_mode, g_groups.values())


def reloadConf():
    """Reload the configuration file."""
    global g_conf_path, g_mode, g_groups, g_passwords

    conf = ConfigParser(defaults={'FLOAD_HOME':
                                  os.getenv('FLOAD_HOME','.')})
    conf.read(g_conf_path)
    g_mode = conf.get('server', 'mode')
    if g_mode == 'file':
        # load credential file
        credentials_path = conf.get('server', 'credentials_path')
        lofc = conf.getint('server', 'loop_on_first_credentials')
        log("getFileCredential use credential file %s." % credentials_path)
        lines = open(credentials_path).readlines()
        g_groups = {}
        group = Group('default')
        g_groups[None] = group
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            user, password = [x.strip() for x in line.split(CREDENTIAL_SEP, 1)]
            g_passwords[user] = password
            if not lofc or len(group) < lofc:
                group.add(user)

        # load group file
        try:
            groups_path = conf.get('server', 'groups_path')
        except NoOptionError:
            return 1
        log("getFileCredential use group file %s." % groups_path)
        lines = open(groups_path).readlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            name, users = [x.strip() for x in line.split(CREDENTIAL_SEP, 1)]
            users = filter(None,
                           [user.strip() for user in users.split(USERS_SEP)])
            group = g_groups.setdefault(name, Group(name))
            for user in users:
                if lofc and len(group) >= lofc:
                    break
                if g_passwords.has_key(user):
                    group.add(user)
                else:
                    log('Missing password for %s in group %s' % (user, name))

    return 1


# ------------------------------------------------------------
# rpc services
#
def getRandomCredential():
    """Return a (login, password)."""
    global g_call_count
    g_call_count += 1
    ran = int(random()*1000)
    user = 'user_%s' % ran
    password = 'pwd_%s' % ran
    log("%s getRandomCredential() return (%s, %s)" % (
        g_call_count, user, password))
    return (user, password)


def getFileCredential(group=None):
    """Return a credential from group if specified.

    Credential are taken incrementally in a loop.
    """
    global g_passwords, g_groups, g_call_count
    g_call_count += 1
    user = g_groups[group].next()
    password = g_passwords[user]
    log("%s getFileCredential(%s) return (%s, %s)" % (
        g_call_count, group, user, password))
    return (user, password)

def getCredential(mode=None, group=None):
    """Return credential according mode or serveur configuration."""
    global g_mode
    if mode is None:
        choice = g_mode
    else:
        choice = mode

    if choice == 'random':
        return getRandomCredential()
    elif choice == 'file':
        return getFileCredential(group)
    else:
        raise NotImplemented("mode %s" % choice)


def listCredentials(group=None):
    """Return a list of credentials."""
    global g_passwords
    global g_groups
    if group is None:
        ret = list(g_passwords)
    else:
        users = g_groups[group].users
        ret = [(user, g_passwords[user]) for user in users]
    log("listUsers(%s) return (%s)" % (group, ret))
    return ret


def listGroups(group=None):
    """Return a list of groups."""
    global g_groups
    ret = filter(None, g_groups.keys())
    log("listGroup() return (%s)" % str(ret))
    return ret

# ------------------------------------------------------------
# testing
#
def test_getCredential(repeat=10):
    """Test getCredential."""
    for i in range(repeat):
        getCredential(mode='file')
    for i in range(repeat):
        getCredential(mode='random')


def is_server_running(host, port):
    """Check if the server is already running."""
    server = ServerProxy("http://%s:%s" % (host, port))
    try:
        server.getStatus()
    except socket.error, msg:
        return 0
    return 1



# ------------------------------------------------------------
# main
#
def main(conf_path=None):
    """Init and run XMLRPC Server."""
    global g_conf_path, g_quit, CONF_PATH

    if conf_path is None:
        if len(sys.argv) >= 2:
            conf_path = sys.argv[1]
        else:
            conf_path = CONF_PATH

    g_conf_path = conf_path

    # load credentials files
    reloadConf()

    #test_getCredential(20)

    # setup rpc server
    conf = ConfigParser(defaults={'FLOAD_HOME':
                                  os.getenv('FLOAD_HOME','.')})
    conf.read(g_conf_path)
    host = conf.get('server', 'host')
    port = int(conf.get('server', 'port'))
    if is_server_running(host, port):
        log("Server already running on %s:%s." % (host, port))
        return

    log("Init XMLRPC server %s:%s." % (host, port))
    server = MySimpleXMLRPCServer((host, port))
    server.register_function(getStatus)
    server.register_function(reloadConf)
    server.register_function(stopServer)
    server.register_function(getRandomCredential)
    server.register_function(getFileCredential)
    server.register_function(getCredential)
    server.register_function(listCredentials)
    server.register_function(listGroups)
    log("credential server started.")

    # loop
    while not g_quit:
        server.handle_request()
    sleep(1)
    server.server_close()


if __name__ == '__main__':
    main()
