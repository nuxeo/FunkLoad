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
"""Simple client that control a credential_server.

$Id: credentialctl.py 24649 2005-08-29 14:20:19Z bdelbosc $
"""
import sys
import socket
from xmlrpclib import ServerProxy
from ConfigParser import ConfigParser

USAGE = """
Usage: ./credentialctl.py CONF_FILE [status|reload|stop|test_credential]
"""
CONF_PATH = "credential.conf"


def usage():
    """Display usage."""
    print USAGE

def action_getStatus(server):
    """Test the getStatus method."""
    print "### cli: srv status: %s" % server.getStatus()

def action_stopServer(server):
    """Ask the server to stop."""
    print "### cli: srv stopServer."
    server.stopServer()

def action_reloadConf(server):
    """Ask the server to reload the configuration file."""
    print "### cli: ask srv to reloadConf."""
    server.reloadConf()

def test_getCredential(server):
    """Test the getCredential method."""
    call_count = 0
    for i in range(10):
        print "### cli: %s getCredential() ..." % call_count
        user, password = server.getCredential()
        print "### cli: %s   return %s %s" % (call_count, user, password)
        call_count += 1
    for group in server.listGroups():
        print "### cli: group %s" % group
        print "###    content: %s" % server.listCredentials(group)

# ------------------------------------------------------------
# main
#
def main():
    """Control credentiald server."""
    check_status = 0
    if len(sys.argv) != 3:
        usage()
        sys.exit(-1)
    conf_path = sys.argv[1]
    action = sys.argv[2]
    conf = ConfigParser()
    print "### cli: Use configuration file: %s." % conf_path
    conf.read(conf_path)
    host = conf.get('server', 'host')
    port = int(conf.get('server', 'port'))
    print "### cli: Init XMLRPC proxy http://%s:%s." % (host, port)
    server = ServerProxy("http://%s:%s" % (host, port))

    # check the srv status first
    try:
        action_getStatus(server)
    except socket.error, msg:
        print "### cli: Server is not running: %s" % msg
        sys.exit(-1)

    if action == "status":
        sys.exit(0)
    elif action == "reload":
        action_reloadConf(server)
    elif action == "stop":
        action_stopServer(server)
    elif action in ("test", "test_credential"):
        test_getCredential(server)
        action_getStatus(server)
    else:
        usage()

if __name__ == '__main__':
    main()
