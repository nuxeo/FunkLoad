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
"""FunkLoad test case using Richard Jones' webunit.

$Id: FunkLoadTestCase.py 24757 2005-08-31 12:22:19Z bdelbosc $
"""
import os
import sys
import time
import re
from warnings import warn
from socket import error as SocketError
from types import ListType
from datetime import datetime
import unittest
import traceback
from random import random
from tempfile import mkdtemp
from xml.sax.saxutils import quoteattr
from utils import get_logger, mmn_is_bench, mmn_decode
from utils import recording, thread_sleep, is_html, get_version
from optionconfigparser import OptionConfigParser
from browser import Browser
from curlfetcher import CurlFetcher
from webunitfetcher import WebunitFetcher
from xmlrpclib import ServerProxy

_marker = []

# ------------------------------------------------------------
# Classes
#
class FunkLoadTestCase(unittest.TestCase):
    """Unit test with browser and configuration capabilties."""
    # ------------------------------------------------------------
    # Initialisation
    #
    def __init__(self, methodName='runTest', options=None):
        """Initialise the test case.

        Note that methodName is encoded in bench mode to provide additional
        information like thread_id, concurrent virtual users..."""
        if mmn_is_bench(methodName):
            self.in_bench_mode = True
        else:
            self.in_bench_mode = False
        self.test_name, self.cycle, self.cvus, self.thread_id = mmn_decode(
            methodName)
        self.meta_method_name = methodName
        self.suite_name = self.__class__.__name__
        unittest.TestCase.__init__(self, methodName=self.test_name)


        self._response = None
        self.options = options
        self.debug_level = getattr(options, 'debug_level', 0)
        self._funkload_init()
        self._dump_dir = getattr(options, 'dump_dir', None)
        self._dumping =  self._dump_dir and True or False
        self._viewing = getattr(options, 'firefox_view', False)
        self._accept_invalid_links = getattr(options, 'accept_invalid_links',
                                             False)
        self._simple_fetch = getattr(options, 'simple_fetch', False)
        self._stop_on_fail = getattr(options, 'stop_on_fail', False)
        if self._viewing and not self._dumping:
            # viewing requires dumping contents
            self._dumping = True
            self._dump_dir = mkdtemp('_funkload')
        self._loop_mode = getattr(options, 'loop_steps', False)
        if self._loop_mode:
            if options.loop_steps.count(':'):
                steps = options.loop_steps.split(':')
                self._loop_steps = range(int(steps[0]), int(steps[1]))
            else:
                self._loop_steps = [int(options.loop_steps)]
            self._loop_number = options.loop_number
            self._loop_recording = False
            self._loop_records = []

    def _funkload_init(self):
        """Initialize a funkload test case using a configuration file."""
        # look into configuration file
        config_directory = os.getenv('FL_CONF_PATH', '.')
        config_path = os.path.join(config_directory,
                                   self.__class__.__name__ + '.conf')
        config_path = os.path.abspath(config_path)
        config = OptionConfigParser(config_path, self.options)
        self._config = config
        self.conf_get = self._config.get
        self.conf_getInt = self._config.getInt
        self.conf_getFloat = self._config.getFloat
        self.conf_getList = self._config.getList
        self._config_path = config_path
        self.default_user_agent = self.conf_get('main', 'user_agent',
                                                'FunkLoad/%s' % get_version(),
                                                quiet=True)
        if self.in_bench_mode:
            section = 'bench'
        else:
            section = 'ftest'
        ok_codes = self.conf_getList(section, 'ok_codes', [200, 301, 302],
                                     quiet=True)
        self.ok_codes = map(int, ok_codes)
        self.sleep_time_min = self.conf_getFloat(section, 'sleep_time_min', 0)
        self.sleep_time_max = self.conf_getFloat(section, 'sleep_time_max', 0)
        self.log_to = self.conf_get(section, 'log_to', 'console file')
        self.log_path = self.conf_get(section, 'log_path', 'funkload.log')
        self.result_path = os.path.abspath(
            self.conf_get(section, 'result_path', 'funkload.xml'))

        # init loggers
        self.logger = get_logger(name="funkload.log",
                                 log_path=self.log_path,
                                 log_console=self.log_to.count('console'))
        self.logger_result = get_logger(name="funkload.result",
                                        log_console=False,
                                        log_path=self.result_path,
                                        format=None, propagate=True)
        # init a browser
        fetcher_type = self.conf_get('main', 'fetcher', 'curl')
        if fetcher_type == 'webunit':
            # webunit fetcher
            self.fetcher_type = fetcher_type
            browser = Browser(WebunitFetcher)
        else:
            # curl fetcher setup
            self.fetcher_type = 'curl'
            browser = Browser(CurlFetcher)
            if self.conf_getInt('main', 'curl_concurrency', 0, quiet=True):
                browser.concurrency = options.concurrency
            if self.conf_getInt('main', 'curl_verbose', 0, quiet=True):
                browser.fetcher.curlVerbose(1)

        self._browser = browser
        self.clearContext()

        #self.logd('# FunkLoadTestCase._funkload_init done')

    def clearContext(self):
        """Resset the testcase."""
        self._browser.reset()
        self.step_success = True
        self.test_status = 'Successful'
        self.steps = 0
        self.page_responses = 0
        self.total_responses = 0
        self.total_time = 0.0
        self.total_pages = self.total_images = 0
        self.total_links = self.total_redirects = 0
        self.total_xmlrpc = 0
        self.clearBasicAuth()
        self.clearHeaders()
        self.setUserAgent(self.default_user_agent)

        self.logdd('FunkLoadTestCase.clearContext done')



    #------------------------------------------------------------
    # browser simulation
    #
    def _browse(self, url_in, params_in, method=None, fetch_resources=None,
               use_resource_cache=None, description=None, ok_codes=None,
               sleep=True):
        """Simulate a browser log responses."""
        self._response = None
        if ok_codes is None:
            ok_codes = self.ok_codes
        for response in self._browser.browse(
            url_in, params_in, method, fetch_resources, use_resource_cache,
            description=description):
            self.total_time += response.total_time
            code = response.code
            if code in ok_codes:
                self.step_success = True
                self._log_response(response)
            else:
                self.step_success = False
                self.test_status = 'Failure'
                self._log_response(response)
                if code == -1:
                    raise str(response.error)
                else:
                    self.fail('invalide return code %s, extpected %s' % (
                        code, ok_codes))
            rtype = response.type
            if rtype == 'page':
                self._response = response
                self.total_pages += 1
            elif rtype == 'redirect':
                self.total_redirects += 1
            elif rtype == 'resource':
                self.total_links += 1
        if self._dumping:
            self._dump_content(self._response)
        if sleep:
            self.sleep()
        return self._response

    def post(self, url, params=None, description=None, ok_codes=None):
        """POST method on url with params."""
        self.steps += 1
        self.page_responses = 0
        response = self._browse(url, params, description=description,
                                ok_codes=ok_codes, method="post")
        return response

    def get(self, url, params=None, description=None, ok_codes=None):
        """GET method on url adding params."""
        self.steps += 1
        self.page_responses = 0
        response = self._browse(url, params, description=description,
                                ok_codes=ok_codes, method="get")
        return response

    def exists(self, url, params=None, description="Checking existence"):
        """Try a GET on URL return True if the page exists or False."""
        resp = self.get(url, params, description=description,
                        ok_codes=[200, 301, 302, 404, 503])
        if resp.code not in [200, 301, 302]:
            self.logd('Page %s not found.' % url)
            return False
        self.logd('Page %s exists.' % url)
        return True

    def xmlrpc(self, url_in, method_name, params=None, description=None):
        """Call an xml rpc method_name on url with params."""
        self.steps += 1
        self.page_responses = 0
        self.logd('XMLRPC: %s::%s\n\tCall %i: %s ...' % (url_in, method_name,
                                                         self.steps,
                                                         description or ''))
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
            self.test_status = 'Error'
            self.logd(' Failed in %.3fs' % t_delta)
            self._log_xmlrpc_response(url_in, method_name, description,
                                      response, t_start, t_stop, -1)
            if etype is SocketError:
                raise SocketError("Can't access %s." % url)
            raise
        t_stop = time.time()
        t_delta = t_stop - t_start
        self.total_time += t_delta
        self.total_xmlrpc += 1
        self.logd(' Done in %.3fs' % t_delta)
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
            response = self._browser.fetch(url, None, ok_codes=[200, 301, 302])
            if response.code == -1:
                if time.time() - time_start > time_out:
                    self.fail('Time out service %s not available after %ss' %
                              (url, time_out))
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
        self._browser.addHeader(key, value)

    def setHeader(self, key, value):
        """Add or override an http header.

        If value is None, the key is removed."""
        self._browser.setHeader(key, value)

    def delHeader(self, key):
        """Remove an http header key."""
        self._browser.delHeader(key)

    def clearHeaders(self):
        """Remove all http headers set by addHeader or setUserAgent.

        Note that the Referer is also removed."""
        self._browser.clearHeaders()

    def setUserAgent(self, agent):
        """Set User-Agent http header for the next requests.

        If agent is None, the user agent header is removed."""
        self._browser.setUserAgent(agent)

    def sleep(self):
        """Sleeps a random amount of time.

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
        return ret
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
        # XXX
        return self._response.url


    #------------------------------------------------------------
    # Extend unittest.TestCase to provide bench cycle hook
    #
    def setUpCycle(self):
        """Called on bench mode before a cycle start."""
        pass

    def tearDownCycle(self):
        """Called after a cycle in bench mode."""
        pass



    #------------------------------------------------------------
    # logging
    #
    def logd(self, message):
        """Debug log."""
        self.logger.debug(self.meta_method_name +': ' +message)

    def logdd(self, message):
        """Verbose Debug log."""
        if self.debug_level >= 2:
            self.logger.debug(self.meta_method_name +': ' +message)

    def logi(self, message):
        """Info log."""
        if hasattr(self, 'logger'):
            self.logger.info(self.meta_method_name+': '+message)
        else:
            print self.meta_method_name+': '+message

    def _logr(self, message, force=False):
        """Log a result."""
        if force or not self.in_bench_mode or recording():
            self.logger_result.info(message)

    def _open_result_log(self, **kw):
        """Open the result log."""
        xml = ['<funkload version="%s" time="%s">' % (
            get_version(), datetime.now().isoformat())]
        for key, value in kw.items():
            xml.append('<config key="%s" value=%s />' % (
                key, quoteattr(str(value))))
        self._logr('\n'.join(xml), force=True)

    def _close_result_log(self):
        """Close the result log."""
        self._logr('</funkload>', force=True)

    def _log_response(self, response):
        """Log a response."""
        self.total_responses += 1
        self.page_responses += 1
        info = {}
        info['cycle'] = self.cycle
        info['cvus'] = self.cvus
        info['thread_id'] = self.thread_id
        info['suite_name'] = self.suite_name
        info['test_name'] = self.test_name
        info['step'] = self.steps
        info['number'] = self.page_responses
        info['type'] = response.type
        info['url'] = quoteattr(response.url)
        info['code'] = response.code
        description = response.description
        info['description'] = description and quoteattr(description) or '""'
        info['time_start'] = response.start
        info['duration'] = response.total_time
        info['result'] = self.step_success and 'Successful' or 'Failure'
        response_start = '''<response cycle="%(cycle).3i" cvus="%(cvus).3i" thread="%(thread_id).3i" suite="%(suite_name)s" name="%(test_name)s" step="%(step).3i" number="%(number).3i" type="%(type)s" result="%(result)s" url=%(url)s code="%(code)s" description=%(description)s time="%(time_start)s" duration="%(duration)s"''' % info
        if self.step_success:
            message = response_start + ' />'
        else:
            if response.error:
                response_start = response_start + 'error=%s' % quoteattr(
                    response.error)
            # dump header and body
            if response.headers_dict:
                response_start = response_start + '>\n  <headers>'
                header_xml = []
                for key, value in response.headers_dict.items():
                    header_xml.append('    <header name="%s" value=%s />' % (
                        key, quoteattr(value)))
                headers = '\n'.join(header_xml) + '\n  </headers>'
                message = '\n'.join([
                    response_start,
                    headers,
                    '  <body><![CDATA[\n%s\n]]>\n  </body>' % response.body,
                    '</response>'])
        self._logr(message)

    def _log_xmlrpc_response(self, url, method, description, response,
                             time_start, time_stop, code):
        """Log a response."""
        self.total_responses += 1
        self.page_responses += 1
        info = {}
        info['cycle'] = self.cycle
        info['cvus'] = self.cvus
        info['thread_id'] = self.thread_id
        info['suite_name'] = self.suite_name
        info['test_name'] = self.test_name
        info['step'] = self.steps
        info['number'] = self.page_responses
        info['type'] = 'xmlrpc'
        info['url'] = quoteattr(url + '#' + method)
        info['code'] = code
        info['description'] = description and quoteattr(description) or '""'
        info['time_start'] = time_start
        info['duration'] = time_stop - time_start
        info['result'] = self.step_success and 'Successful' or 'Failure'
        message = '''<response cycle="%(cycle).3i" cvus="%(cvus).3i" thread="%(thread_id).3i" suite="%(suite_name)s" name="%(test_name)s" step="%(step).3i" number="%(number).3i" type="%(type)s" result="%(result)s" url=%(url)s code="%(code)s" description=%(description)s time="%(time_start)s" duration="%(duration)s" />"''' % info
        self._logr(message)

    def _log_result(self, time_start, time_stop):
        """Log the test result."""
        info = {}
        info['cycle'] = self.cycle
        info['cvus'] = self.cvus
        info['thread_id'] = self.thread_id
        info['suite_name'] = self.suite_name
        info['test_name'] = self.test_name
        info['steps'] = self.steps
        info['time_start'] = time_start
        info['duration'] = time_stop - time_start
        info['connection_duration'] = self.total_time
        info['requests'] = self.total_responses
        info['pages'] = self.total_pages
        info['xmlrpc'] = self.total_xmlrpc
        info['redirects'] = self.total_redirects
        info['images'] = self.total_images
        info['links'] = self.total_links
        info['result'] = self.test_status
        if self.test_status != 'Successful':
            info['traceback'] = 'traceback=' + quoteattr(' '.join(
                traceback.format_exception(*sys.exc_info()))) + ' '
        else:
            info['traceback'] = ''
        text = '''<testResult cycle="%(cycle).3i" cvus="%(cvus).3i" thread="%(thread_id).3i" suite="%(suite_name)s" name="%(test_name)s"  time="%(time_start)s" result="%(result)s" steps="%(steps)s" duration="%(duration)s" connection_duration="%(connection_duration)s" requests="%(requests)s" pages="%(pages)s" xmlrpc="%(xmlrpc)s" redirects="%(redirects)s" images="%(images)s" links="%(links)s" %(traceback)s/>''' % info
        self._logr(text)

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
                self.logi('Failed to remote control firefox: %s' % cmd)
                self._viewing = False


    #------------------------------------------------------------
    # Overriding unittest.TestCase
    #
    def __call__(self, result=None):
        """Run the test method.

        Override to log test result."""
        t_start = time.time()
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._TestCase__testMethodName)
        try:
            ok = False
            try:
                if not self.in_bench_mode:
                    self.logd(
                        'Starting -----------------------------------\n\t%s' %
                        self.conf_get(self.method_name, 'description', ''))
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                self.test_status = 'Error'
                self._log_result(t_start, time.time())
                return
            try:
                testMethod()
                ok = True
            except self.failureException:
                result.addFailure(self, self._TestCase__exc_info())
                self.test_status = 'Failure'
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                self.test_status = 'Error'
            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                self.test_status = 'Error'
                ok = False
            if ok:
                result.addSuccess(self)
        finally:
            self._log_result(t_start, time.time())
            if not ok and self._stop_on_fail:
                result.stop()
            result.stopTest(self)




# ------------------------------------------------------------
# testing
#
class DummyTestCase(FunkLoadTestCase):
    """Testing Funkload TestCase."""

    def test_apache(self):
        """Simple apache test."""
        self.logd('start apache test')
        for i in range(2):
            self.get('http://localhost/')
            self.logd('base_url: ' + self.getLastBaseUrl())
            self.logd('url: ' + self.getLastUrl())
            self.logd('hrefs: ' + str(self.listHref()))
        self.logd("Total connection time = %s" % self.total_time)

if __name__ == '__main__':
    unittest.main()

