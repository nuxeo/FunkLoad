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
"""Simple FunkLoad Test Recorder.

require tcpwatch.py
* http://hathawaymix.org/Software/TCPWatch/tcpwatch-1.3.tar.gz

Credits goes to Ian Bicking for parsing tcpwatch files.

$Id$
"""
import os
import sys
from cStringIO import StringIO
from optparse import OptionParser, TitledHelpFormatter
from tempfile import mkdtemp
import rfc822
import cgi

class Request:
    """Store a tcpwatch request."""
    def __init__(self, file_path):
        """Load a tcpwatch request file."""
        self.file_path = file_path
        f = open(file_path, 'rb')
        line = f.readline().split(None, 2)
        self.method = line[0]
        self.url = line[1]
        self.version = line[2].strip()
        self.headers = dict(rfc822.Message(f).items())
        self.body = f.read()
        f.close()

    def extractParam(self):
        """Turn muti part encoded form into params."""
        environ = {
            'CONTENT_TYPE': self.headers['content-type'],
            'CONTENT_LENGTH': self.headers['content-length'],
            'REQUEST_METHOD': 'POST',
            }
        form = cgi.FieldStorage(fp=StringIO(self.body),
                                environ=environ,
                                keep_blank_values=True)
        params = []
        for key in form.keys():
            if not isinstance(form[key], list):
                values = [form[key]]
            else:
                values = form[key]
            for form_value in values:
                params.append((key, form_value.value))
        return params

    def __repr__(self):
        params = ''
        if self.body:
            params = self.extractParam()
        return '<request method="%s" url="%s" %s/>' % (
            self.method, self.url, str(params))


class Response:
    """Store a tcpwatch response."""
    def __init__(self, file_path):
        """Load a tcpwatch response file."""
        self.file_path = file_path
        f = open(file_path, 'rb')
        line = f.readline().split(None, 2)
        self.version = line[0]
        self.status_code = line[1].strip()
        if len(line) > 2:
            self.status_message = line[2].strip()
        else:
            self.status_message = ''
        self.headers =  dict(rfc822.Message(f).items())
        self.body = f.read()
        f.close()

    def __repr__(self):
        return '<response code="%s" type="%s" status="%s" />' % (
            self.status_code, self.headers.get('content-type'),
            self.status_message)


class RecorderProgram:
    """A tcpwatch to funkload recorder."""
    USAGE = """%prog [options] test_name

%prog launch a proxy and record activities, then create a FunkLoad unit test.

Examples
========

  %prog myFile.py -p 9090 foo         - run a proxy in port 9090
"""
    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        self.verbose = False
        self.name = None
        self.tmp_path = None
        self.prefix = 'watch'
        self.port = "8090"
        self.parseArgs(argv)

    def parseArgs(self, argv):
        """Parse programs args."""
        parser = OptionParser(self.USAGE, formatter=TitledHelpFormatter())
        parser.add_option("-v", "--verbose", action="store_true",
                          help="Verbose output")
        parser.add_option("-p", "--port", type="string", dest="port",
                          default=self.port, help="The proxy port.")
        options, args = parser.parse_args(argv)
        if len(args) != 1:
            parser.error("incorrect number of arguments")
        self.verbose = options.verbose
        self.port = options.port
        self.name = args[0]


    def startProxy(self):
        """Start a tcpwatch session."""
        self.tmp_path = mkdtemp('_funkload')
        cmd = 'tcpwatch.py -p %s -s -r %s' % (self.port,
                                               self.tmp_path)
        if self.verbose:
            cmd += ' | grep "T http"'
        else:
            cmd += ' > /dev/null'
        os.system(cmd)

    def searchFiles(self):
        """Search tcpwatch file."""
        items = {}
        prefix = self.prefix
        for filename in os.listdir(self.tmp_path):
            if not filename.startswith(prefix):
                continue
            name, ext = os.path.splitext(filename)
            name = name[len(self.prefix):]
            ext = ext[1:]
            if ext == 'errors':
                print "Error in response %s" % name
                continue
            assert ext in ('request', 'response'), "Bad extension: %r" % ext
            items.setdefault(name, {})[ext] = os.path.join(
                self.tmp_path, filename)
        items = items.items()
        items.sort()
        return [(v['request'], v['response'])
                for name, v in items
                if v.has_key('response')]

    def extractRequests(self, files):
        """Filter and extract request from tcpwatch files."""
        last_code = None
        filter_ctypes = ('image', 'css', 'javascript')
        filter_url = ('.png', '.gif', '.css', '.js')
        requests = []
        for request_path, response_path in files:
            response = Response(response_path)
            request = Request(request_path)
            ctype = response.headers.get('content-type', '')
            url = request.url
            if request.method != "POST" and (
                last_code in ('301', '302') or
                [x for x in filter_ctypes if x in ctype] or
                [x for x in filter_url if url.endswith(x)]):
                last_code = response.status_code
                continue
            last_code = response.status_code
            requests.append(request)
        return requests

    def convertToFunkLoad(self, request):
        """return a funkload python instruction."""
        text = []
        text.append('self.%s("%s"' % (request.method.lower(), request.url))
        if request.body:
            text.append(', params=%s' % request.extractParam())
        return ''.join(text) + ')'

    def run(self):
        """run it."""
        self.startProxy()
        files = self.searchFiles()
        requests = self.extractRequests(files)
        code = [self.convertToFunkLoad(request) for request in requests]
        code.insert(0, '')
        print ('\n' + ' '*8).join(code)


if __name__ == '__main__':
    RecorderProgram().run()
