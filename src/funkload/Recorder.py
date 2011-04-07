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
"""TCPWatch FunkLoad Test Recorder.

Requires tcpwatch-httpproxy or tcpwatch.py available at:

* http://hathawaymix.org/Software/TCPWatch/tcpwatch-1.3.tar.gz

Credits goes to Ian Bicking for parsing tcpwatch files.

$Id$
"""
import os
import sys
import re
from cStringIO import StringIO
from optparse import OptionParser, TitledHelpFormatter
from tempfile import mkdtemp
import rfc822
from cgi import FieldStorage
from urlparse import urlsplit
from utils import truncate, trace, get_version, Data

def get_null_file():
    if sys.platform.lower().startswith('win'):
        return "NUL"
    else:
        return "/dev/null"

class Request:
    """Store a tcpwatch request."""
    def __init__(self, file_path):
        """Load a tcpwatch request file."""
        self.file_path = file_path
        f = open(file_path, 'rb')
        line = f.readline().split(None, 2)
        if not line:
            trace('# Warning: empty first line on %s\n' % self.file_path)
            line = f.readline().split(None, 2)
        self.method = line[0]
        url = line[1]
        scheme, host, path, query, fragment = urlsplit(url)
        self.host = scheme + '://' + host
        self.rurl = url[len(self.host):]
        self.url = url
        self.path = path
        self.version = line[2].strip()
        self.headers = dict(rfc822.Message(f).items())
        self.body = f.read()
        f.close()

    def extractParam(self):
        """Turn muti part encoded form into params."""
        params = []
        try:
            environ = {
                'CONTENT_TYPE': self.headers['content-type'],
                'CONTENT_LENGTH': self.headers['content-length'],
                'REQUEST_METHOD': 'POST',
                }
        except KeyError:
            trace('# Warning: missing header content-type or content-length'
                  ' in file: %s not an http request ?\n' % self.file_path)
            return params

        form = FieldStorage(fp=StringIO(self.body),
                            environ=environ,
                            keep_blank_values=True)
        try:
            keys = form.keys()
        except TypeError:
            trace('# Using custom data for request: %s ' % self.file_path)
            params = Data(self.headers['content-type'], self.body)
            return params

        for item in form.list:
            
            key = item.name
            value = item.value
            filename = item.filename
            
            if filename is None:
                params.append([key, value])
            else:
                # got a file upload
                filename = filename or ''
                params.append([key, 'Upload("%s")' % filename])
                if filename:
                    if os.path.exists(filename):
                        trace('# Warning: uploaded file: %s already'
                              ' exists, keep it.\n' % filename)
                    else:
                        trace('# Saving uploaded file: %s\n' % filename)
                        f = open(filename, 'w')
                        f.write(str(value))
                        f.close()
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
    tcpwatch_cmd = ['tcpwatch-httpproxy', 'tcpwatch.py', 'tcpwatch']
    MYFACES_STATE = 'org.apache.myfaces.trinidad.faces.STATE'
    MYFACES_FORM = 'org.apache.myfaces.trinidad.faces.FORM'
    USAGE = """%prog [options] [test_name]

%prog launch a TCPWatch proxy and record activities, then output
a FunkLoad script or generates a FunkLoad unit test if test_name is specified.

The default proxy port is 8090.

Note that tcpwatch.py executable must be accessible from your env.

See http://funkload.nuxeo.org/ for more information.

Examples
========
  %prog foo_bar
                        Run a proxy and create a FunkLoad test case,
                        generates test_FooBar.py and FooBar.conf file.
                        To test it:  fl-run-test -dV test_FooBar.py
  %prog -p 9090
                        Run a proxy on port 9090, output script to stdout.
  %prog -i /tmp/tcpwatch
                        Convert a tcpwatch capture into a script.
"""
    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        self.verbose = False
        self.tcpwatch_path = None
        self.prefix = 'watch'
        self.port = "8090"
        self.server_url = None
        self.class_name = None
        self.test_name = None
        self.loop = 1
        self.script_path = None
        self.configuration_path = None
        self.use_myfaces = False
        self.parseArgs(argv)

    def getTcpWatchCmd(self):
        """Return the tcpwatch cmd to use."""
        tcpwatch_cmd = self.tcpwatch_cmd[:]
        if os.getenv("TCPWATCH"):
            tcpwatch_cmd.insert(0, os.getenv("TCPWATCH"))
        for cmd in tcpwatch_cmd:
            ret = os.system(cmd + ' -h  2> %s' % get_null_file())
            if ret == 0:
                return cmd
        raise RuntimeError('Tcpwatch is not installed no %s found. '
                           'Visit http://funkload.nuxeo.org/INSTALL.html' %
                           str(self.tcpwatch_cmd))

    def parseArgs(self, argv):
        """Parse programs args."""
        parser = OptionParser(self.USAGE, formatter=TitledHelpFormatter(),
                              version="FunkLoad %s" % get_version())
        parser.add_option("-v", "--verbose", action="store_true",
                          help="Verbose output")
        parser.add_option("-p", "--port", type="string", dest="port",
                          default=self.port, help="The proxy port.")
        parser.add_option("-i", "--tcp-watch-input", type="string",
                          dest="tcpwatch_path", default=None,
                          help="Path to an existing tcpwatch capture.")
        parser.add_option("-l", "--loop", type="int",
                          dest="loop", default=1,
                          help="Loop mode.")

        options, args = parser.parse_args(argv)
        if len(args) == 1:
            test_name = args[0]
        else:
            test_name = None

        self.verbose = options.verbose
        self.tcpwatch_path = options.tcpwatch_path
        self.port = options.port
        if not test_name and not self.tcpwatch_path:
            self.loop = options.loop
        if test_name:
            test_name = test_name.replace('-', '_')
            class_name = ''.join([x.capitalize()
                                  for x in re.split('_|-', test_name)])
            self.test_name = test_name
            self.class_name = class_name
            self.script_path = './test_%s.py' % class_name
            self.configuration_path = './%s.conf' % class_name

    def startProxy(self):
        """Start a tcpwatch session."""
        self.tcpwatch_path = mkdtemp('_funkload')
        cmd = self.getTcpWatchCmd() + ' -p %s -s -r %s' % (self.port,
                                                           self.tcpwatch_path)
        if os.name == 'posix':
            if self.verbose:
                cmd += ' | grep "T http"'
            else:
                cmd += ' > %s' % get_null_file()
        trace("Hit Ctrl-C to stop recording.\n")
        try:
            os.system(cmd)
        except KeyboardInterrupt:
            pass

    def searchFiles(self):
        """Search tcpwatch file."""
        items = {}
        prefix = self.prefix
        for filename in os.listdir(self.tcpwatch_path):
            if not filename.startswith(prefix):
                continue
            name, ext = os.path.splitext(filename)
            name = name[len(self.prefix):]
            ext = ext[1:]
            if ext == 'errors':
                trace("Error in response %s\n" % name)
                continue
            assert ext in ('request', 'response'), "Bad extension: %r" % ext
            items.setdefault(name, {})[ext] = os.path.join(
                self.tcpwatch_path, filename)
        items = items.items()
        items.sort()
        return [(v['request'], v['response'])
                for name, v in items
                if v.has_key('response')]

    def extractRequests(self, files):
        """Filter and extract request from tcpwatch files."""
        last_code = None
        filter_ctypes = ('image', 'css', 'javascript', 'x-shockwave-flash')
        filter_url = ('.jpg', '.png', '.gif', '.css', '.js', '.swf')
        requests = []
        for request_path, response_path in files:
            response = Response(response_path)
            request = Request(request_path)
            if self.server_url is None:
                self.server_url = request.host
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

    def reindent(self, code, indent=8):
        """Improve indentation."""
        spaces = ' ' * indent
        code = code.replace('], [', '],\n%s    [' % spaces)
        code = code.replace('[[', '[\n%s    [' % spaces)
        code = code.replace(', description=', ',\n%s    description=' % spaces)
        code = code.replace('self.', '\n%sself.' % spaces)
        return code

    def convertToFunkLoad(self, request):
        """return a funkload python instruction."""
        text = []
        text.append('        # ' + request.file_path)
        if request.host != self.server_url:
            text.append('self.%s("%s"' % (request.method.lower(),
                                          request.url))
        else:
            text.append('self.%s(server_url + "%s"' % (
                request.method.lower(),  request.rurl.strip()))
        description = "%s %s" % (request.method.capitalize(),
                                 request.path | truncate(42))
        if request.body:
            params = request.extractParam()
            if isinstance(params, Data):
                params = "Data('%s', '''%s''')" % (params.content_type,
                                                       params.data)
            else:
                myfaces_form = None
                if self.MYFACES_STATE not in [key for key, value in params]:
                    params = 'params=%s' % params
                else:
                    # apache myfaces state add a wrapper
                    self.use_myfaces = True
                    new_params = []
                    for key, value in params:
                        if key == self.MYFACES_STATE:
                            continue
                        if key == self.MYFACES_FORM:
                            myfaces_form = value
                            continue
                        new_params.append([key, value])
                    params = "    self.myfacesParams(%s, form='%s')" % (
                        new_params, myfaces_form)
                params = re.sub("'Upload\(([^\)]*)\)'", "Upload(\\1)", params)
            text.append(', ' + params)
        text.append(', description="%s")' % description)
        return ''.join(text)

    def extractScript(self):
        """Convert a tcpwatch capture into a FunkLoad script."""
        files = self.searchFiles()
        requests = self.extractRequests(files)
        code = [self.convertToFunkLoad(request)
                for request in requests]
        if not code:
            trace("Sorry no action recorded.\n")
            return ''
        code.insert(0, '')
        return self.reindent('\n'.join(code))

    def writeScript(self, script):
        """Write the FunkLoad test script."""
        trace('Creating script: %s.\n' % self.script_path)
        from pkg_resources import resource_string
        if self.use_myfaces:
            tpl_name = 'data/MyFacesScriptTestCase.tpl'
        else:
            tpl_name = 'data/ScriptTestCase.tpl'
        tpl = resource_string('funkload', tpl_name)
        content = tpl % {'script': script,
                         'test_name': self.test_name,
                         'class_name': self.class_name}
        if os.path.exists(self.script_path):
            trace("Error file %s already exists.\n" % self.script_path)
            return
        f = open(self.script_path, 'w')
        f.write(content)
        f.close()

    def writeConfiguration(self):
        """Write the FunkLoad configuration test script."""
        trace('Creating configuration file: %s.\n' % self.configuration_path)
        from pkg_resources import resource_string
        tpl = resource_string('funkload', 'data/ConfigurationTestCase.tpl')
        content = tpl % {'server_url': self.server_url,
                         'test_name': self.test_name,
                         'class_name': self.class_name}
        if os.path.exists(self.configuration_path):
            trace("Error file %s already exists.\n" %
                  self.configuration_path)
            return
        f = open(self.configuration_path, 'w')
        f.write(content)
        f.close()

    def run(self):
        """run it."""
        count = self.loop
        while count:
            count -= 1
            if count:
                print "Remaining loop: %i" % count
            if self.tcpwatch_path is None:
                self.startProxy()
            script = self.extractScript()
            if not script:
                self.tcpwatch_path = None
                continue
            if self.test_name is not None:
                self.writeScript(script)
                self.writeConfiguration()
            else:
                print script
                print
            self.tcpwatch_path = None


def main():
    RecorderProgram().run()

if __name__ == '__main__':
    main()
