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
"""Base class to build XML RPC daemon server.

$Id$
"""
import sys, os
from socket import error as SocketError
from time import sleep
from ConfigParser import ConfigParser, NoOptionError
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy
import logging
from optparse import OptionParser, TitledHelpFormatter

from utils import create_daemon, get_default_logger, close_logger
from utils import trace, get_version


def is_server_running(host, port):
    """Check if the XML/RPC server is running checking getStatus RPC."""
    server = ServerProxy("http://%s:%s" % (host, port))
    try:
        server.getStatus()
    except SocketError:
        return False
    return True



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
# Server
#
class XmlRpcBaseServer:
    """The base class for xml rpc server."""

    usage = """%prog [options] config_file

Start %prog XML/RPC daemon.
"""
    server_name = None
    # list RPC Methods
    method_names = ['stopServer', 'getStatus']

    def __init__(self, argv=None):
        if self.server_name is None:
            self.server_name = self.__class__.__name__
        if argv is None:
            argv = sys.argv
        conf_path, options = self.parseArgs(argv)
        self.default_log_path = self.server_name + '.log'
        self.default_pid_path = self.server_name + '.pid'
        self.server = None
        self.quit = False

        # read conf
        conf = ConfigParser()
        conf.read(conf_path)
        self.conf_path = conf_path
        self.host = conf.get('server', 'host')
        self.port = conf.getint('server', 'port')
        try:
            self.pid_path = conf.get('server', 'pid_path')
        except NoOptionError:
            self.pid_path = self.default_pid_path
        try:
            log_path = conf.get('server', 'log_path')
        except NoOptionError:
            log_path = self.default_log_path

        if is_server_running(self.host, self.port):
            trace("Server already running on %s:%s." % (self.host, self.port))
            sys.exit(0)

        trace('Starting %s server at http://%s:%s/' % (self.server_name,
                                                       self.host, self.port))
        # init logger
        if options.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        if options.debug:
            log_to = 'file console'
        else:
            log_to = 'file'
        self.logger = get_default_logger(log_to, log_path, level=level,
                                         name=self.server_name)
        # subclass init
        self._init_cb(conf, options)

        # daemon mode
        if not options.debug:
            trace(' as daemon.\n')
            close_logger(self.server_name)
            create_daemon()
            # re init the logger
            self.logger = get_default_logger(log_to, log_path, level=level,
                                             name=self.server_name)
        else:
            trace(' in debug mode.\n')

        # init rpc
        self.initServer()

    def _init_cb(self, conf, options):
        """init procedure intend to be implemented by subclasses.

        This method is called before to switch in daemon mode.
        conf is a ConfigParser object."""
        pass

    def logd(self, message):
        """Debug log."""
        self.logger.debug(message)

    def log(self, message):
        """Log information."""
        self.logger.info(message)

    def parseArgs(self, argv):
        """Parse programs args."""
        parser = OptionParser(self.usage, formatter=TitledHelpFormatter(),
                              version="FunkLoad %s" % get_version())
        parser.add_option("-v", "--verbose", action="store_true",
                          help="Verbose output")
        parser.add_option("-d", "--debug", action="store_true",
                          help="debug mode, server is run in forground")

        options, args = parser.parse_args(argv)
        if len(args) != 2:
            parser.error("Missing configuration file argument")
        return args[1], options

    def initServer(self):
        """init the XMLR/PC Server."""
        self.log("Init XML/RPC server %s:%s." % (self.host, self.port))
        server = MySimpleXMLRPCServer((self.host, self.port))
        for method_name in self.method_names:
            self.logd('register %s' % method_name)
            server.register_function(getattr(self, method_name))
        self.server = server

    def run(self):
        """main server loop."""
        server = self.server
        pid = os.getpid()
        open(self.pid_path, "w").write(str(pid))
        self.log("XML/RPC server pid=%i running." % pid)
        while not self.quit:
            server.handle_request()
        sleep(.5)
        server.server_close()
        self.log("XML/RPC server pid=%i stopped." % pid)
        os.remove(self.pid_path)

    __call__ = run

    # RPC
    #
    def stopServer(self):
        """Stop the server."""
        self.log("stopServer request.")
        self.quit = True
        return 1

    def getStatus(self):
        """Return a status."""
        self.logd("getStatus request.")
        return "%s running pid = %s" % (self.server_name, os.getpid())





# ------------------------------------------------------------
# Controller
#
class XmlRpcBaseController:
    """An XML/RPC controller."""

    usage = """%prog config_file action

action can be: start|startd|stop|restart|status|test

Execute action on the XML/RPC server.
"""
    # the server class
    server_class = XmlRpcBaseServer

    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv
        conf_path, self.action, options = self.parseArgs(argv)
        # read conf
        conf = ConfigParser()
        conf.read(conf_path)
        self.host = conf.get('server', 'host')
        self.conf_path = conf_path
        self.port = conf.getint('server', 'port')
        self.url = 'http://%s:%s/' % (self.host, self.port)
        self.verbose = not options.quiet
        self.server = ServerProxy(self.url)


    def parseArgs(self, argv):
        """Parse programs args."""
        parser = OptionParser(self.usage, formatter=TitledHelpFormatter(),
                              version="FunkLoad %s" % get_version())
        parser.add_option("-q", "--quiet", action="store_true",
                          help="Verbose output")
        options, args = parser.parse_args(argv)
        if len(args) != 3:
            parser.error("Missing argument")
        return args[1], args[2], options

    def log(self, message, force=False):
        """Log a message."""
        if force or self.verbose:
            trace(str(message))

    def startServer(self, debug=False):
        """Start an XML/RPC server."""
        argv = ['cmd', self.conf_path]
        if debug:
            argv.append('-dv')
        daemon = self.server_class(argv)
        daemon.run()

    def __call__(self, action=None):
        """Call the xml rpc action"""
        server = self.server
        if action is None:
            action = self.action
        is_running = is_server_running(self.host, self.port)
        if action == 'status':
            if is_running:
                ret = server.getStatus()
                self.log('%s %s.\n' % (self.url, ret))
            else:
                self.log('No server reachable at %s.\n' % self.url)
            return 0
        elif action in ('stop', 'restart'):
            if is_running:
                ret = server.stopServer()
                self.log('Server %s is stopped.\n' % self.url)
                is_running = False
            elif action == 'stop':
                self.log('No server reachable at %s.\n' % self.url)
            if action == 'restart':
                self('start')
        elif 'start' in action:
            if is_running:
                self.log('Server %s is already running.\n' % self.url)
            else:
                return self.startServer(action=='startd')
        elif not is_running:
            self.log('No server reachable at %s.\n' % self.url)
            return -1
        elif action == 'reload':
            ret = server.reloadConf()
            self.log('done\n')
        elif action == 'test':
            return self.test()
        else:
            raise NotImplementedError('Unknow action %s' % action)
        return 0

    # this method is done to be overriden in sub classes
    def test(self):
        """Testing the XML/RPC.

        Must return an exit code, 0 for success.
        """
        ret = self.server.getStatus()
        self.log('Testing getStatus: %s\n' % ret)
        return 0

def main():
    """Main"""
    ctl = XmlRpcBaseController()
    ret = ctl()
    sys.exit(ret)

if __name__ == '__main__':
    main()
