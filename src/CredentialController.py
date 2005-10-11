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
from socket import error as SocketError
from xmlrpclib import ServerProxy
from ConfigParser import ConfigParser
from optparse import OptionParser, TitledHelpFormatter
from utils import trace

class CredentialController:
    """A credential server controller."""

    usage = """\
Usage: %prog CONF_FILE [status|reload|stop|test]
"""
    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv
        conf_path, self.action, options = self.parseArgs(argv)
        # read conf
        conf = ConfigParser()
        conf.read(conf_path)
        host = conf.get('server', 'host')
        self.conf_path = conf_path
        port = int(conf.get('server', 'port'))
        self.verbose = options.verbose or int(conf.get('client', 'verbose'))
        self.url = 'http://%s:%s/' % (host, port)
        self.server = ServerProxy(self.url)

    def isServerRunning(self):
        """Check if the server is running."""
        try:
            self.server.getStatus()
        except SocketError:
            return False
        return True

    def parseArgs(self, argv):
        """Parse programs args."""
        parser = OptionParser(self.usage, formatter=TitledHelpFormatter())
        parser.add_option("-v", "--verbose", action="store_true",
                          help="Verbose output")
        options, args = parser.parse_args(argv)
        if len(args) != 3:
            parser.error("Missing configuration file %s" % args)
        return args[1], args[2], options

    def log(self, message, force=False):
        """Log a message."""
        if force or self.verbose:
            trace(message)

    def startServer(self, debug=False):
        """Start a credential server."""
        from CredentialServer import CredentialServer
        argv = ['credentiald.py', self.conf_path]
        if debug:
            argv.append('-dv')
        return CredentialServer(argv)

    def __call__(self, action=None):
        """Call the xml rpc action"""
        server = self.server
        if action is None:
            action = self.action
        self.log('credential-ctl %s: ' % action)
        is_running = self.isServerRunning()
        if action == 'status':
            if is_running:
                ret = server.getStatus()
                self.log('%s\n' % ret, force=True)
            else:
                self.log('%s not available.' % self.url, force=True)
            return 0
        elif action == 'stop':
            if is_running:
                ret = server.stopServer()
                self.log('done.\n')
            else:
                self.log('server is not running.\n')
        elif 'start' in action:
            if is_running:
                self.log('already running.\n')
            else:
                return self.startServer(action=='startd')
        elif not is_running:
            self.log('%s not available.\n' % self.url)
            return -1
        elif action == 'reload':
            ret = server.reloadConf()
            self.log('done\n')
        elif action == 'test':
            for i in range(10):
                self.log("%s getCredential() ... " % i)
                user, password = server.getCredential()
                self.log(" return %s %s\n" % (user, password))
            for group in server.listGroups():
                self.log("group %s\n" % group)
                self.log("  content: %s\n" % server.listCredentials(group))
        else:
            raise NotImplementedError('Unknow action %s' % action)
        return 0

# ------------------------------------------------------------
# main
#
def main():
    """Control credentiald server."""
    ctl = CredentialController()
    ret = ctl()
    sys.exit(ret)

if __name__ == '__main__':
    main()
