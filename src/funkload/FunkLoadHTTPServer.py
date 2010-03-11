#!/usr/bin/python
# (C) Copyright 2010 Nuxeo SAS <http://nuxeo.com>
# Author: Goutham Bhat
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

"""Debug HTTPServer module for Funkload."""

import BaseHTTPServer
import threading
import urlparse
from utils import trace

class FunkLoadHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Handles HTTP requests from client in debug bench mode.

    These are the requests currently supported:
    /cvu?inc=<INTEGER> :: Increments number of CVU by given value.
    /cvu?dec=<INTEGER> :: Decrements number of CVU by given value.
    """
    benchrunner = None
    def do_GET(self):
        benchrunner = FunkLoadHTTPRequestHandler.benchrunner

        parsed_url = urlparse.urlparse(self.path)
        if parsed_url.path == '/cvu':
            query_args = parsed_url.query.split('&')
            if len(query_args) > 0:
                query_parts = query_args[0].split('=')
                if len(query_parts) == 2:
                    message = 'Number of threads changed from %d to %d.'
                    old_num_threads = benchrunner.getNumberOfThreads()
                    if query_parts[0] == 'inc':
                        benchrunner.addThreads(int(query_parts[1]))
                    elif query_parts[0] == 'dec':
                        benchrunner.removeThreads(int(query_parts[1]))
                    new_num_threads = benchrunner.getNumberOfThreads()
                    self.respond('CVU changed from %d to %d.' %
                                 (old_num_threads, new_num_threads))
        elif parsed_url.path == '/getcvu':
            self.respond('CVU = %d' % benchrunner.getNumberOfThreads())

    def respond(self, message):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(message)

class FunkLoadHTTPServer(threading.Thread):
    """Starts a HTTP server in a separate thread."""

    def __init__(self, benchrunner, port):
        threading.Thread.__init__(self)
        self.benchrunner = benchrunner
        self.port = port
        FunkLoadHTTPRequestHandler.benchrunner = benchrunner

    def run(self):
        port = 8000
        if self.port:
            port = int(self.port)
        server_address = ('', port)
        trace("Starting debug HTTP server at port %d\n" % port)

        httpd = BaseHTTPServer.HTTPServer(server_address, FunkLoadHTTPRequestHandler)
        httpd.serve_forever()
