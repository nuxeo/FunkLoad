# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Tim Baverstock, Matthew Vail, Matt Sparks
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
import os
import re
import time
import sys
import traceback
import urlparse
import tempfile
import unittest
import urllib

from warnings import warn
from types import DictType, ListType, TupleType
from xml.sax.saxutils import quoteattr
from socket import error as SocketError
from random import random
from xmlrpclib import ServerProxy
from utils import get_version, is_html, thread_sleep, trace

from webunit.webunittest import WebTestCase, HTTPError

import PatchWebunit

class FunkLoadWebBrowser:
    """Wrapper around a webunit test, for a loggy sort of browser."""

    def __init__(self, fconf, flogger):
        self.fconf = fconf
        self.flogger = flogger
        self._response = None
        self._viewing = fconf.opt_get('firefox_view', False)
        self._accept_invalid_links = fconf.opt_get('accept_invalid_links',
                                                    False)
        self._simple_fetch = fconf.opt_get('simple_fetch', False)
        self._dump_dir = fconf.opt_get('dump_dir', None)
        self._dumping =  self._dump_dir and True or False
        self._strict_cookies = fconf.opt_get('strict_cookies', True)
        self._fetch_threads = fconf.opt_get('fetch_threads', 4)
        self.sleep_time_min = fconf.getFloat('sleep_time_min', 0)
        self.sleep_time_max = fconf.getFloat('sleep_time_max', 0)

        PatchWebunit.FETCH_THREADS = self._fetch_threads

        if self._viewing and not self._dumping:
            # viewing requires dumping contents
            self._dumping = True
            self._dump_dir = tempfile.mkdtemp('_funkload')

        """TODO: (weasel) I am unkeen on loop_mode. Can it be reworked?"""
        self._loop_mode = fconf.opt_get('loop_steps', False)
        if self._loop_mode:
            loop_steps = self._loop_mode
            if ':' in loop_steps:
                steps = loop_steps.split(':')
                self._loop_steps = range(int(steps[0]), int(steps[1]))
            else:
                self._loop_steps = [int(loop_steps)]
            self._loop_number = fconf.opt_get('loop_number')
            self._loop_recording = False
            self._loop_records = []
        self.default_user_agent = fconf.get('user_agent',
                                            'FunkLoad/%s' % get_version(),
                                            section='main',
                                            quiet=True)
        ok_codes = fconf.getList('ok_codes', [200, 301, 302], quiet=True)
        self.ok_codes = map(int, ok_codes)
        # init webunit browser (passing a fake methodName)
        self._browser = WebTestCase(methodName='log')
        self.clearContext()

    def clearContext(self):
        """Reset the browser"""
        self._browser.clearContext()
        self._browser.css = {}
        self._browser.history = []
        self._browser.extra_headers = []
        self.page_responses = 0
        self.total_responses = 0
        self.total_time = 0.0
        self.total_pages = self.total_images = 0
        self.total_links = self.total_redirects = 0
        self.total_xmlrpc = 0
        self.clearBasicAuth()
        self.clearHeaders()
        self.setUserAgent(self.default_user_agent)
        self.steps = 0
        self.step_success = True
        self.browser_status = 'Successful'

    #------------------------------------------------------------
    # browser simulation
    #
    def _connect(self, url, params, ok_codes, rtype, description,
                 log_headers=False):
        """Handle fetching, logging, errors and history."""
        t_start = time.time()
        try:
            response = self._browser.fetch(url, params, ok_codes=ok_codes,
                                           log_headers=log_headers,
                                           strict_cookies=self._strict_cookies)
        except:
            etype, value, tback = sys.exc_info()
            t_stop = time.time()
            t_delta = t_stop - t_start
            self.total_time += t_delta
            self.step_success = False
            self.browser_status = 'Failure'
            self.flogger.logd(' Failed in %.3fs' % t_delta)
            if etype is HTTPError:
                self._log_response(value.response, rtype, description,
                                   t_start, t_stop, log_body=True)
                if self._dumping:
                    self._dump_content(value.response)
                raise unittest.TestCase.failureException, str(value.response)
            else:
                self._log_response_error(url, rtype, description, t_start,
                                         t_stop)
                if etype is SocketError:
                    raise SocketError("Can't load %s." % url)
                raise
        t_stop = time.time()
        # Log response
        t_delta = t_stop - t_start
        self.total_time += t_delta
        if rtype in ('post', 'get'):
            self.total_pages += 1
        elif rtype == 'redirect':
            self.total_redirects += 1
        elif rtype == 'link':
            self.total_links += 1
        if rtype in ('post', 'get', 'redirect'):
            # this is a valid referer for the next request
            self.setHeader('Referer', url)
        self._browser.history.append((rtype, url))
        self.flogger.logd(' Done in %.3fs' % t_delta)
        self._log_response(response, rtype, description, t_start, t_stop)
        if self._dumping:
            self._dump_content(response)
        return response

    def _browse(self, url_in, params_in=None,
                description=None, ok_codes=None,
                method='post',
                follow_redirect=True, load_auto_links=True,
                sleep=True, log_headers=False):
        """Simulate a browser handle redirects, load/cache css and images."""
        self._response = None
        # Loop mode
        if self._loop_mode:
            if self.steps == self._loop_steps[0]:
                self._loop_recording = True
                self.flogger.logi('Loop mode start recording')
            if self._loop_recording:
                self._loop_records.append((url_in, params_in, description,
                                           ok_codes, method, follow_redirect,
                                           load_auto_links, False))
        # ok codes
        if ok_codes is None:
            ok_codes = self.ok_codes
        if type(params_in) is DictType:
            params_in = params_in.items()
        params = []
        if params_in:
            # NOTE(mattv): The following "try" was not originally part of the
            # FunkLoad package.  I put this in here because this would fail
            # when you tried to post XML, rather than <key, value> pairs.  Now,
            # when it fails to find a <key, value> pair, it will set the params
            # to params_in automatically
            try:
                for key, value in params_in:
                   if type(value) is DictType:
                       for val, selected in value.items():
                           if selected:
                               params.append((key, val))
                   elif type(value) in (ListType, TupleType):
                       for val in value:
                           params.append((key, val))
                   else:
                       params.append((key, value))
            except:
                params = params_in

        if method == 'get' and params:
            url = url_in + '?' + urllib.urlencode(params)
            params = None
        else:
            url = url_in

        if method == 'get':
            self.flogger.logd('GET: %s\n\tPage %i: %s ...' %
                              (url, self.steps, description or ''))
        else:
            url = url_in
            self.flogger.logd('POST: %s %s\n\tPage %i: %s ...' %
                              (url, str(params), self.steps, description or ''))
        # Fetching
        response = self._connect(url, params, ok_codes, method, description,
            log_headers)

        # Check redirection
        if follow_redirect and response.code in (301, 302):
            max_redirect_count = 10
            thread_sleep()              # give a chance to other threads
            while response.code in (301, 302) and max_redirect_count:
                # Figure the location - which may be relative
                newurl = response.headers['Location']
                url = urlparse.urljoin(url_in, newurl)
                self.flogger.logd(' Load redirect link: %s' % url)
                response = self._connect(url, None, ok_codes, 'redirect', None,
                    log_headers)
                max_redirect_count -= 1
            if not max_redirect_count:
                self.flogger.logd(' WARNING Too many redirects give up.')

        # Load auto links (css and images)
        response.is_html = is_html(response.body)
        if load_auto_links and response.is_html and not self._simple_fetch:
            self.flogger.logd(' Load css and images...')
            page = response.body
            c_start = t_start = time.time()
            try:
                # pageImages is patched to call _log_response on all links, and
                # will handle the case that self._accept_invalid_links is set.
                self._browser.pageImages(url, page, self)
            except HTTPError, error:
                t_stop = time.time()
                t_delta = t_stop - t_start
                self.step_success = False
                self.browser_status = 'Failure'
                self.flogger.logd('  Failed in ~ %.2fs' % t_delta)
                # XXX The duration logged for this response is wrong
                self._log_response(error.response, 'link', None,
                                   t_start, t_stop, log_body=True)
                raise unittest.TestCase.failureException, str(error)
            c_stop = time.time()
            self.total_time += c_stop - c_start
            self.flogger.logd('  Done in %.3fs' % (c_stop - c_start))
        if sleep:
            self.sleep()
        self._response = response

        # Loop mode
        if self._loop_mode and self.steps == self._loop_steps[-1]:
            self._loop_recording = False
            self.flogger.logi('Loop mode end recording.')
            t_start = self.total_time
            count = 0
            for i in range(self._loop_number):
                self.flogger.logi('Loop mode replay %i' % i)
                for record in self._loop_records:
                    count += 1
                    self.steps += 1
                    self._browse(*record)
            t_delta = self.total_time - t_start
            text = ('End of loop: %d pages rendered in %.3fs, '
                    'avg of %.3fs per page, '
                    '%.3f SPPS without concurrency.' % (count, t_delta,
                                                        t_delta/count,
                                                        count/t_delta))
            self.flogger.logi(text)
            trace(text + '\n')

        return response

    def post(self, url, params=None, description=None, ok_codes=None,
             log_headers=False):
        """POST method on url with params."""
        self.steps += 1
        self.page_responses = 0
        response = self._browse(url, params, description, ok_codes,
                                method="post", log_headers=log_headers)
        return response

    def get(self, url, params=None, description=None, ok_codes=None,
            log_headers=False):
        """GET method on url adding params."""
        self.steps += 1
        self.page_responses = 0
        response = self._browse(url, params, description, ok_codes,
                                method="get", log_headers=log_headers)
        return response

    def exists(self, url, params=None, description="Checking existence"):
        """Try a GET on URL return True if the page exists or False."""
        resp = self.get(url, params, description=description,
                        ok_codes=[200, 301, 302, 404, 503])
        if resp.code not in [200, 301, 302]:
            self.flogger.logd('Page %s not found.' % url)
            return False
        self.flogger.logd('Page %s exists.' % url)
        return True

    def xmlrpc(self, url_in, method_name, params=None, description=None):
        """Call an xml rpc method_name on url with params."""
        self.steps += 1
        self.page_responses = 0
        self.flogger.logd('XMLRPC: %s::%s\n\tCall %i: %s ...' %
                          (url_in, method_name, self.steps, description or ''))
        response = None
        t_start = time.time()
        if self._authinfo is not None:
            url = url_in.replace('//', '//'+self._authinfo)
        else:
            url = url_in
        try:
            server = ServerProxy(url)
            method = getattr(server, method_name)
            if params is not None:
                response = method(*params)
            else:
                response = method()
        except:
            etype, value, tback = sys.exc_info()
            t_stop = time.time()
            t_delta = t_stop - t_start
            self.total_time += t_delta
            self.step_success = False
            self.browser_status = 'Error'
            self.flogger.logd(' Failed in %.3fs' % t_delta)
            self._log_xmlrpc_response(url_in, method_name, description,
                                      response, t_start, t_stop, -1)
            if etype is SocketError:
                raise SocketError("Can't access %s." % url)
            raise
        t_stop = time.time()
        t_delta = t_stop - t_start
        self.total_time += t_delta
        self.total_xmlrpc += 1
        self.flogger.logd(' Done in %.3fs' % t_delta)
        self._log_xmlrpc_response(url_in, method_name, description, response,
                                  t_start, t_stop, 200)
        self.sleep()
        return response

    def xmlrpc_call(self, url_in, method_name, params=None, description=None):
        """BBB of xmlrpc, this method will be removed for 1.6.0."""
        warn('Since 1.4.0 the method "xmlrpc_call" is renamed into "xmlrpc".',
             DeprecationWarning, stacklevel=2)
        return self.xmlrpc(url_in, method_name, params, description)

    def waitUntilAvailable(self, url, time_out=20, sleep_time=2):
        """Wait until url is available.

        Try a get on url every sleep_time until server is reached or
        time is out."""
        time_start = time.time()
        while(True):
            try:
                self._browser.fetch(url, None, ok_codes=[200, 301, 302],
                                    strict_cookies=self._strict_cookies)
            except SocketError:
                # TODO(msparks): we can no longer call fail() here because we're
                # not inheriting from unittest.TestCase.
                if time.time() - time_start > time_out:
                    self.flogger.logd('Time out service %s not available after '
                                      '%ss' % (url, time_out))
                break
            else:
                return
            time.sleep(sleep_time)

    def setBasicAuth(self, login, password):
        """Set http basic authentication."""
        self._browser.setBasicAuth(login, password)
        self._authinfo = '%s:%s@' % (login, password)

    def clearBasicAuth(self):
        """Remove basic authentication."""
        self._browser.clearBasicAuth()
        self._authinfo = None

    def addHeader(self, key, value):
        """Add an http header."""
        self._browser.extra_headers.append((key, value))

    def setHeader(self, key, value):
        """Add or override an http header.

        If value is None, the key is removed."""
        headers = self._browser.extra_headers
        for i, (k, v) in enumerate(headers):
            if k == key:
                if value is not None:
                    headers[i] = (key, value)
                else:
                    del headers[i]
                break
        else:
            if value is not None:
                headers.append((key, value))

    def delHeader(self, key):
        """Remove an http header key."""
        self.setHeader(key, None)

    def clearHeaders(self):
        """Remove all http headers set by addHeader or setUserAgent.

        Note that the Referer is also removed."""
        self._browser.extra_headers = []

    def setUserAgent(self, agent):
        """Set User-Agent http header for the next requests.

        If agent is None, the user agent header is removed."""
        self.setHeader('User-Agent', agent)


    #------------------------------------------------------------
    # Assertion helpers
    #
    def getLastUrl(self):
        """Return the last accessed url taking into account redirection."""
        response = self._response
        if response is not None:
            return response.url
        return ''

    def getBody(self):
        """Return the last response content."""
        response = self._response
        if response is not None:
            return response.body
        return ''

    def listHref(self, pattern=None):
        """Return a list of href anchor url present in the last html response.

        Filtering href using the pattern regex if present."""
        response = self._response
        ret = []
        if response is not None:
            a_links = response.getDOM().getByName('a')
            if a_links:
                ret = [getattr(x, 'href', '') for x in a_links]
            if pattern is not None:
                pat = re.compile(pattern)
                ret = [href for href in ret if pat.search(href) is not None]
        return ret

    def getLastBaseUrl(self):
        """Return the base href url."""
        response = self._response
        if response is not None:
            base = response.getDOM().getByName('base')
            if base:
                return base[0].href
        return ''


    # --------------------------------------------------------------
    # Logging helpers
    #
    def _log_response_error(self, url, rtype, description, time_start,
                            time_stop):
        """Log a response that raise an unexpected exception."""
        self.total_responses += 1
        self.page_responses += 1
        info = {}
        info['step'] = '%.3i' % self.steps
        info['number'] = '%.3i' % self.page_responses
        info['type'] = rtype
        info['url'] = quoteattr(url)
        info['code'] = -1
        info['description'] = description and quoteattr(description) or '""'
        info['time'] = '%.6f' % time_start
        info['duration'] = '%.6f' % (time_stop - time_start)
        info['result'] = 'Error'
        info['traceback'] = quoteattr(' '.join(
            traceback.format_exception(*sys.exc_info())))
        self.flogger.results.write('response', info)

    def _log_response(self, response, rtype, description, time_start,
                      time_stop, log_body=False):
        """Log a response."""
        self.total_responses += 1
        self.page_responses += 1
        info = {}
        info['step'] = '%.3i' % self.steps
        info['number'] = '%.3i' % self.page_responses
        info['type'] = rtype
        info['url'] = quoteattr(response.url)
        info['code'] = response.code
        info['description'] = description and quoteattr(description) or '""'
        info['time'] = '%.6f' % time_start
        info['duration'] = '%.6f' % (time_stop - time_start)
        info['result'] = self.step_success and 'Successful' or 'Failure'

        if not log_body:
            body = None
        else:
            header_xml = []
            for key, value in response.headers.items():
                header_xml.append('    <header name="%s" value=%s />' % (
                    key, quoteattr(value)))
            headers = '\n  <headers>\n'.join(header_xml) + '\n  </headers>'
            body = '\n'.join([
                headers,
                '  <body><![CDATA[\n%s\n]]>\n  </body>' % response.body,
                ''])
        self.flogger.results.write('response', info, body)

    def _log_xmlrpc_response(self, url, method, description, response,
                             time_start, time_stop, code):
        """Log a response."""
        self.total_responses += 1
        self.page_responses += 1
        info = {}
        info['step'] = '%.3i' % self.steps
        info['number'] = '%.3i' % self.page_responses
        info['type'] = 'xmlrpc'
        info['url'] = quoteattr(url + '#' + method)
        info['code'] = code
        info['description'] = description and quoteattr(description) or '""'
        info['time'] = '%.6f' % time_start
        info['duration'] = '%.6f' % (time_stop - time_start)
        info['result'] = self.step_success and 'Successful' or 'Failure'
        self.flogger.results.write('response', info)

    def gather_result(self):
        """Return a dictionary of the browser's cumulative test results."""
        info = {}
        info['steps'] = self.steps
        info['connection_duration'] = '%.6f' % self.total_time
        info['requests'] = self.total_responses
        info['pages'] = self.total_pages
        info['xmlrpc'] = self.total_xmlrpc
        info['redirects'] = self.total_redirects
        info['images'] = self.total_images
        info['links'] = self.total_links
        info['browser_status'] = self.browser_status
        if self.browser_status != 'Successful':
            info['traceback'] = 'traceback=' + quoteattr(' '.join(
                traceback.format_exception(*sys.exc_info()))) + ' '
        else:
            info['traceback'] = ''
        return info

    def _dump_content(self, response):
        """Dump the html content in a file.

        Use firefox to render the content if we are in rt viewing mode."""
        dump_dir = self._dump_dir
        if dump_dir is None:
            return
        if getattr(response, 'code', 301) in [301, 302]:
            return
        if not response.body:
            return
        if not os.access(dump_dir, os.W_OK):
            os.mkdir(dump_dir, 0775)
        content_type = response.headers.get('content-type')
        if content_type == 'text/xml':
            ext = '.xml'
        else:
            ext = os.path.splitext(response.url)[1]
            if not ext.startswith('.') or len(ext) > 4:
                ext = '.html'
        file_path = os.path.abspath(
            os.path.join(dump_dir, '%3.3i%s' % (self.steps, ext)))
        f = open(file_path, 'w')
        f.write(response.body)
        f.close()
        if self._viewing:
            cmd = 'firefox -remote  "openfile(file://%s,new-tab)"' % file_path
            ret = os.system(cmd)
            if ret != 0:
                self.flogger.logi('Failed to remote control firefox: %s' % cmd)
                self._viewing = False

    def logdd(self, message):
        """Grubby log through-put to cope with PatchWebunit"""
        self.flogger.logdd(message)

    def sleep(self):
        """Sleeps a random amount of time.

        (cut'n'pasted from FunkLoadBaseTestCase; should be moved to utils)
        Between the predefined sleep_time_min and sleep_time_max values.
        """
        s_min = self.sleep_time_min
        s_max = self.sleep_time_max
        if s_max != s_min:
            s_val = s_min + abs(s_max - s_min) * random()
        else:
            s_val = s_min
        # we should always sleep something
        thread_sleep(s_val)
