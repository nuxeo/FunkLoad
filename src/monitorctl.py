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
"""Simple client that control a monitor_server.

$Id: monitorctl.py 24649 2005-08-29 14:20:19Z bdelbosc $
"""
import sys, os
import socket
from xmlrpclib import ServerProxy
from ConfigParser import ConfigParser, NoOptionError, NoSectionError
from time import sleep

USAGE = """
Usage: ./monitorctl.py CONF_FILE [status|reload|stop|test_monitor]
"""
CONF_PATH = "monitor.conf"


def usage():
    """Display usage."""
    print USAGE

def action_getStatus(server, verbose=True):
    """Test the getStatus method."""
    status = server.getStatus()
    if verbose:
        print "### cli: srv status: %s" % status

def action_stopServer(server, verbose=True):
    """Ask the server to stop."""
    if verbose:
        print "### cli: srv stopServer."
    server.stopServer()

def action_reloadConf(server, verbose=True):
    """Ask the server to reload the configuration file."""
    if verbose:
        print "### cli: ask srv to reloadConf."""
    server.reloadConf()

def action_startRecord(server, key):
    """Start to record for key."""
    print "### cli: ask to start recording for %s" % key
    server.startRecord(key)

def action_stopRecord(server, key):
    """Stop recording for key."""
    print "### cli: ask to stop recording for %s" % key
    server.stopRecord(key)

def action_getResult(server, key):
    """Output the record."""
    print "### cli: record for %s:""" % key
    print server.getXmlResult(key)

def test_monitor(server):
    """Test the  method."""
    key = 'test_monitor'
    server.startRecord(key)
    action_getStatus(server)
    sleep(1)
    # do something
    j = 1.0
    for i in range(100000):
        j = i * 999999.888 * j
    sleep(1)
    server.stopRecord(key)
    print "### cli: getResult(): %s" % str(server.getXmlResult(key))


# ------------------------------------------------------------
# main
#
def main(conf_path, action="action_monitor", key=None):
    """Init and run server."""
    conf = ConfigParser(defaults={'FLOAD_HOME':
                                  os.getenv('FLOAD_HOME','.')})
    conf.read(conf_path)
    try:
        verbose = int(conf.get('client', 'verbose'))
    except (NoOptionError, NoSectionError):
        verbose = True
    if verbose:
        print "### cli: Use configuration file: %s." % conf_path
    conf.read(conf_path)
    host = conf.get('client', 'host')
    port = int(conf.get('client', 'port'))
    if verbose:
        print "### cli: Init XMLRPC proxy http://%s:%s." % (host, port)
    server = ServerProxy("http://%s:%s" % (host, port))

    # check the srv status first
    try:
        action_getStatus(server, verbose or action=="status")
    except socket.error, msg:
        if action == "status" or verbose or '111' not in str(msg):
            print "### cli: Server is not running: %s" % msg
        if action in ('stop', 'status'):
            ret = 0
        else:
            ret = -1
        sys.exit(ret)

    if action == "status":
        sys.exit(0)
    elif action == "reload":
        action_reloadConf(server, verbose)
    elif action == "stop":
        action_stopServer(server, verbose)
    elif action in ("test", "test_monitor"):
        test_monitor(server)
        action_getStatus(server)
    elif action == 'monitor_start':
        action_startRecord(server, key)
    elif action == 'monitor_stop':
        action_stopRecord(server, key)
        action_getResult(server, key)
    elif action == 'monitor_get':
        action_getResult(server, key)
    else:
        usage()

if __name__ == '__main__':
    action = "test_monitor"
    check_status = 0
    if len(sys.argv) >= 2:
        conf_path = sys.argv[1]
    if len(sys.argv) >= 3:
        action = sys.argv[2]
    key = None
    if len(sys.argv) >= 4:
        key = sys.argv[3]
    main(conf_path, action, key)
