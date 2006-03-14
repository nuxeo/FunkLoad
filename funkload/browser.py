# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
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
"""Browser implementation.

$Id$
"""
# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.
try:
    import signal
    from signal import SIGPIPE, SIG_IGN
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except ImportError:
    pass


import os
import sys
import time
import logging
from tempfile import mkdtemp
from urlparse import urljoin
from optparse import OptionParser, TitledHelpFormatter
from curlfetcher import CurlFetcher
from webunitfetcher import WebunitFetcher
from htmlresourceparser import HTMLResourceParser
from utils import get_logger, get_version, truncate, guess_file_extension

class Browser:
    """Simulate a browser using a fetcher.

    Handles redirects, referer, fetching html resources, history.
    Simulates a cache for resources."""

    def __init__(self, fetcher_cls):
        logger = get_logger()
        self.logd = logger.debug
        self.logi = logger.info
        self.logw = logger.warning
        self.logger = logger
        self.concurrency = 0

        self.fetcher = fetcher_cls()
        self.fetch = self.fetcher.fetch
        self.setHeader = self.fetcher.setHeader
        self.clearHeaders = self.fetcher.clearHeaders
        self.setUserAgent = self.fetcher.setUserAgent
        self.setBasicAuth = self.fetcher.setBasicAuth
        self.clearBasicAuth = self.fetcher.clearBasicAuth

        self.page_count = 0             # count during a session
        self.request_count = 0
        self.page_history = []          # history for a session
        self.request_history = []
        self.auto_referer = True        # set referer automaticly
        self.max_redirs = 10            # number of redirects to follow
        self.fetch_resources = True     # extract html resources
        self.use_resource_cache = True  # simulate a cache for resources
        self.setUserAgent('FunkLoad/%s' % get_version())

    def reset(self):
        """Reset the browser session."""
        self.fetcher.reset()
        self.page_count = 0
        self.page_history = []
        self.request_history = []
        self.setUserAgent('FunkLoad/%s' % get_version())

    def browse(self, url_in, params_in, method=None, fetch_resources=None,
               use_resource_cache=None, **kw):
        """Handle redirect and fetch HTML ressources.

        return an iter list of HTTP<Fetcher>Responses"""
        request_history = self.request_history
        if fetch_resources is None:
            fetch_resources = self.fetch_resources
        if use_resource_cache is None:
            use_resource_cache = self.use_resource_cache
        if method is None:
            method = params_in and 'post' or 'get'
        history_append = request_history.append
        request_count = 0
        page_count = self.page_count

        # 1. fetch the requested page
        self.logd('%s: %s' % (method, url_in | truncate(70)))
        response = self.fetch(url_in, params_in, method, type='page',
                              page=page_count, request=request_count,
                              **kw)
        request_count += 1
        history_append((method, url_in, params_in))
        self.setReferer(url_in, False)
        self.logd(' return code %s done in %.6fs.' % (
            response.code, response.total_time))
        if response.error:
            self.logi(' Error: ' + str(response.error))
        yield response

        # 2. handles redirection
        redirect_count = self.max_redirs
        while response.type == 'redirect':
            if not redirect_count:
                self.logw('Too many redirects (%s) on %s, give up.' % (
                    self.max_redirs, url_in))
                break
            url = response.getHeader('Location')
            url = urljoin(url_in, url)
            self.logd(' redirect: %s' % url | truncate(70))
            response = self.fetch(url, params_in, method, type="page",
                                  page=page_count, request=request_count,
                                  **kw)
            request_count += 1
            history_append((method, url, params_in))
            self.setReferer(url, False)
            redirect_count -= 1
            self.logd('  return code %s done in %.6fs.' % (
                response.code, response.total_time))
            yield response

        # 3. extract html resources
        if (fetch_resources and
            response.content_type and response.content_type.count('html')):
            parser = HTMLResourceParser(response.effective_url)
            parser.feed(response.body)
            parser.close()
            links = parser.links

            if use_resource_cache:
                # 4. simulate an optimal cache
                links = [link for link in links
                         if ('get', link, None) not in self.request_history]

            if self.concurrency > 1:
                for response in self.fetcher.multiGet(
                    links, concurrency=self.concurrency, **kw):
                    request_count += 1
                    history_append(('get', response.url, None))
                    self.logd(' multi fetch resources: %s\n'
                              '  return code %s done in %.6fs.' % (
                        response.url, response.code, response.total_time))
                    yield response
            else:
                for link in links:
                    self.logd(' fetch resource:  %s' % link | truncate(70))
                    response = self.fetch(
                        link, method='get', type="resource",
                        page=page_count, request=request_count)
                    request_count += 1
                    history_append(('get', link, None))
                    self.logd('  return code %s done in %.6fs.' % (
                        response.code, response.total_time))
                    yield response
        self.page_count += 1

    def post(self, url_in, params_in=None):
        """Simulate a browser post."""
        for response in self.browse(url_in, params_in, method='post'):
            yield response
        self.page_history.append(('post', url_in, params_in))

    def get(self, url_in, params_in=None):
        """Simulate a browser get."""
        for response in self.browse(url_in, params_in=None, method='get'):
            yield response
        self.page_history.append(('get', url_in, params_in))

    def setReferer(self, url, force=True):
        """Set the referer."""
        if force or self.auto_referer:
            self.fetcher.setReferer(url)

    def perf(self, url_in, params=None, method=None, count=10):
        """Loop on a request output stats."""
        stats = {}
        volume = 0
        requests = 0
        url_order = []
        start = time.time()
        for i in xrange(count):
            for response in self.browse(url_in, params, method):
                url = response.url
                if url not in url_order:
                    url_order.append(url)
                stats.setdefault(url, []).append(
                    (response.total_time,
                     response.connect_time,
                     response.transfer_time))
                volume += response.size_download
                requests += 1
        stop = time.time()
        self._renderStat(stats, requests, stop-start, volume, url_order)

    def _computeStat(self, times):
        """Returns the (average, standard deviation,
            min, median, percentil 90, 95, 98, max,
            per second) of a list of times."""
        total = sum(times)
        avg = total / len(times)
        pers = avg and 1/avg or 0
        count = len(times)
        stddev = (sum([(i - avg)**2 for i in times]) / (count - 1 or 1)) ** .5
        sort = list(times)
        sort.sort()
        return (avg, stddev,
                sort[0], sort[count//2],
                sort[int(count * .90)], sort[int(count * .95)],
                sort[int(count * .98)], sort[-1], pers)

    def _renderStat(self, stats, requests, elapsed, volume, url_order):
        """Render perf stats."""
        self.logi("Performing %d requests, during %.3fs, download: %.2fKb" % (
            requests, elapsed, volume/1024))
        self.logi("  Effective requests per second: %.3f RPS" % (
            requests/elapsed))
        self.logi("                 Transfert rate: %.3f Kb/s\n" % (
            volume/elapsed/1024))
        thead = ('average:', 'std dev:', 'minimum:', 'median:',
                 '90%:', '95%:', '98%:', 'maximum:', 'per second:')
        for request in url_order:
            values = stats[request]
            self.logi("Stat for %d requests of: %s" % (len(values), request))
            self.logi("                 total      connect    transfert")
            self.logi("----------- ----------- ------------ ------------")
            times = zip(*[self._computeStat(x) for x in zip(*values)])
            for title, line in zip(thead, times):
                self.logi("%11s" % title + "%12.6f %12.6f %12.6f" % line)
            self.logi("----------- ----------- ------------ ------------\n")


class BrowserProgram:
    """Simple browser command line."""

    USAGE = """%prog [options] url [url2] ...

Simulate a browser request on urls.

See http://funkload.nuxeo.org/ for more information.


Examples
========
  %prog http://localhost/ -d
                        Display requests used to browse http://localhost/
  %prog http://localhost/ -d -S
                        Do not fetch html resources.
  %prog http://localhost/ -d --webunit
                        Use the WebUnit fetcher (default is pyCurl).
  %prog http://localhost/ -D
                        Dump responses.
  %prog http://localhost/ -t
                        Verbose trace for request.
  %prog http://localhost/ -u login:pwd -d
                        Use http basic auth.
  %prog http://localhost/ -n 100
                        Perform 100 requests and output detail statistics.
"""

    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv
        options, args = self.parseArgs(argv)
        if options.trace or options.debug:
            logger = get_logger(level=logging.DEBUG)
        else:
            logger = get_logger(level=logging.INFO)
        self.logi = logger.info
        self.logd = logger.debug
        self.logw = logger.warning
        if options.webunit:
            # webunit fetcher
            browser = Browser(WebunitFetcher)
        else:
            # curl fetcher setup
            browser = Browser(CurlFetcher)
            if options.concurrency:
                browser.concurrency = options.concurrency
            if options.trace:
                browser.fetcher.curlVerbose(1)
                options.debug = True
        self.options = options
        browser.fetch_resources = not options.simple_fetch
        if options.user_agent:
            browser.setUserAgent(options.user_agent)
        if options.user_password:
            cred = options.user_password.split(':', 1)
            browser.setBasicAuth(cred[0], cred[-1])
        if options.no_auto_referer:
            browser.auto_referer = False
        if options.no_cache:
            browser.use_resource_cache = False
        if options.dump_responses or options.firefox_view:
            if not options.dump_dir:
                options.dump_dir = mkdtemp('_funkload')
                self.logi('Dumping responses into %s' % options.dump_dir)
        self.browser = browser
        self.urls = args[1:]

    def run(self, urls=None):
        """Browse urls."""
        browser = self.browser
        options = self.options
        use_http_post = options.post
        if urls is None:
            urls = self.urls

        for url in urls:
            if options.perf:
                browser.perf(url, count=int(options.perf))
            else:
                if use_http_post:
                    meth = browser.post
                else:
                    meth = browser.get
                for response in meth(url):
                    if options.dump_dir:
                        self.dumpResponse(response)

    def parseArgs(self, argv):
        """Parse programs args."""
        parser = OptionParser(self.USAGE, formatter=TitledHelpFormatter(),
                              version="FunkLoad %s" % get_version())
        parser.add_option("-d", "--debug", action="store_true",
                          help="Debug mode.")
        parser.add_option("-t", "--trace", action="store_true",
                          help="Trace fetcher activity.")
        parser.add_option("-S", "--simple-fetch", action="store_true",
                          help="Don't load additional resources like css "
                          "or images when fetching an html page.")
        parser.add_option("", "--curl", action="store_true",
                          help="Use curl fetcher, "
                          "this is the default fetcher.")
        parser.add_option("", "--webunit", action="store_true",
                          help="Use Webunit fetcher.")
        parser.add_option("-G", "--get", action="store_true",
                          help="Send data with a HTTP GET.")
        parser.add_option("-P", "--post", action="store_true",
                          help="Send data with a HTTP POST.")
        parser.add_option("-D", "--dump-responses", action="store_true",
                          help="Dump responses.")
        parser.add_option("", "--no-auto-referer", action="store_true",
                          help="Don't set auto referer.")
        parser.add_option("-A", "--user-agent", type="string",
                          dest="user_agent",
                          help="User-Agent to send to server.")
        parser.add_option("", "--no-cache", action="store_true",
                          help="Don't cache resources already fetched.")
        parser.add_option("-u", "--user", type="string",
                          dest="user_password",
                          help="<user[:password]> "
                          "Set server basic auth user and password.")
        parser.add_option("-n", "--perf", type="int",
                          help="Number of requests to perform, return stats.")
        parser.add_option("--dump-directory", type="string",
                          dest="dump_dir",
                          help="Directory to dump html pages.")
        parser.add_option("-V", "--firefox-view", action="store_true",
                          help="Real time view using firefox, "
                          "you must have a running instance of firefox "
                          "in the same host.")
        parser.add_option("-c", "--resource-concurrency", type="int",
                          dest="concurrency",
                          help="Fetching html resources asyncronously with "
                          "concurrency (single threaded).")
        options, args = parser.parse_args(argv)
        if len(args) == 0:
            parser.error("incorrect number of arguments")

        return options, args

    def dumpResponses(self, responses):
        """Dump responses."""
        for response in responses:
            self.dumpResponse(response)

    def dumpResponse(self, response):
        """Dump the html content in a file.

        Use firefox to render the content if we are in rt viewing mode."""
        options = self.options
        dump_dir = options.dump_dir
        if not os.access(dump_dir, os.W_OK):
            os.mkdir(dump_dir, 0775)
        if response.headers:
            file_path = os.path.abspath(
                os.path.join(dump_dir, 'response-%3.3i-%2.2i.head' % (
                response.page, response.request)))
            f = open(file_path, 'w')
            f.write(response.headers)
            f.close()
        if not response.body or response.code in (301, 302):
            self.logd('  dump header into: %s' % file_path)
            return
        ext = guess_file_extension(response.url, response.content_type)
        file_path = os.path.abspath(
            os.path.join(dump_dir, 'response-%3.3i-%2.2i%s' % (
            response.page, response.request, ext)))
        self.logd('  dump into: %s' % file_path)
        f = open(file_path, 'w')
        f.write(response.body)
        f.close()
        if response.type ==  'page' and options.firefox_view:
            self.logd('  firefox view ...')
            cmd = 'firefox -remote  "openfile(file://%s,new-tab)"' % file_path
            ret = os.system(cmd)
            if ret != 0:
                self.logw('Failed to remote control firefox: %s' % cmd)
                options.firefox_view = False


    def dumpHistory(self):
        """Dump history."""
        self.logi('Page history:')
        for page in self.browser.page_history:
            self.logi(page)

    def dumpRequestHistory(self):
        """Dump request history."""
        self.logi('Request history:')
        for request in self.browser.request_history:
            self.logi(request)



def main():
    """Default main."""
    prog = BrowserProgram()
    prog.run()


if __name__ == '__main__':
    main()

