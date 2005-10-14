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
"""FunkLoad Test Case using Richard Jones' webunit.

$Id: FunkLoadTestCase.py 24757 2005-08-31 12:22:19Z bdelbosc $
"""
import os
import sys
import time
import re
from socket import error as SocketError
from types import ListType
from datetime import datetime
import unittest
import traceback
from random import random
from urllib import urlencode
from tempfile import mkdtemp
from xml.sax.saxutils import quoteattr
from urlparse import urljoin
from ConfigParser import ConfigParser, NoSectionError, NoOptionError

from webunit.webunittest import WebTestCase, HTTPError

import PatchWebunit
from utils import get_default_logger, mmn_is_bench, mmn_decode
from utils import recording, thread_sleep, is_html, get_version
from xmlrpclib import ServerProxy

_marker = []

# ------------------------------------------------------------
# Classes
#
class FunkLoadTestCase(unittest.TestCase):
    """Conducts a functional test of a Web-enabled HTTP application."""
    # ------------------------------------------------------------
    # Initialisation
    #
    def __init__(self, methodName='runTest', options=None):
        """Initialise the test case.

        Extract the testname from the methodName if
        method is encoded like 'methodName:testName'."""
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
        self._funkload_init()
        self.dumping = getattr(options, 'dump_dir', False) and True
        self.viewing = getattr(options, 'firefox_view', False)
        if self.viewing and not self.dumping:
            # viewing requires dumping contents
            self.dumping = True
            self.options.dump_dir = mkdtemp('_funkload')

    def _funkload_init(self):
        """Initialize a funkload test case using a configuration file."""
        # look into configuration file
        config_directory = os.getenv('FL_CONF_PATH', '.')
        config_path = os.path.join(config_directory,
                                   self.__class__.__name__ + '.conf')
        config_path = os.path.abspath(config_path)
        if not os.path.exists(config_path):
            config_path = "Missing: "+ config_path
        config = ConfigParser()
        config.read(config_path)
        self._config = config
        self._config_path = config_path
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
        self.logger = get_default_logger(self.log_to, self.log_path)
        self.logger_result = get_default_logger(log_to="xml",
                                                log_path=self.result_path,
                                                name="FunkLoadResult")
        #self.logd('_funkload_init config [%s], log_to [%s],'
        #          ' log_path [%s], result [%s].' % (
        #    self._config_path, self.log_to, self.log_path, self.result_path))

        # init webunit browser (passing a fake methodName)
        self._browser = WebTestCase(methodName='log')
        self._browser.user_agent =  self.conf_get('main', 'user_agent',
                                                  'FunkLoad/%s' % get_version(),
                                                  quiet=True)
        self.clearContext()
        #self.logd('# FunkLoadTestCase._funkload_init done')


    def clearContext(self):
        """Resset the testcase."""
        self._browser.clearContext()
        self._browser.css = {}                   # css cache
        self._browser.history = []
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
        #self.logd('# FunkLoadTestCase.clearContext done')



    #------------------------------------------------------------
    # configuration file utils
    #
    def conf_get(self, section, key, default=_marker, quiet=False):
        """Return an entry from the options or configuration file."""
        # check for a command line options
        opt_key = '%s_%s' %(section, key)
        opt_val = getattr(self.options, opt_key, None)
        if opt_val:
            #print('[%s] %s = %s from options.' % (section, key, opt_val))
            return opt_val
        # check for the configuration file if opt val is None
        # or nul
        try:
            val = self._config.get(section, key)
        except (NoSectionError, NoOptionError):
            if not quiet:
                self.logi('[%s] %s not found' % (section, key))
            if default is _marker:
                raise
            val = default
        #print('[%s] %s = %s from config.' % (section, key, val))
        return val


    def conf_getInt(self, section, key, default=_marker, quiet=False):
        """Return an integer from th econfiguration file."""
        return int(self.conf_get(section, key, default, quiet))

    def conf_getFloat(self, section, key, default=_marker, quiet=False):
        """Return a float from th econfiguration file."""
        return float(self.conf_get(section, key, default, quiet))

    def conf_getList(self, section, key, default=_marker, quiet=False):
        """Return a list from th econfiguration file."""
        value = self.conf_get(section, key, default, quiet)
        if value is default:
            return value
        if value.count(':'):
            return value.split(':')
        return [value]



    #------------------------------------------------------------
    # browser simulation
    #

    def connect(self, url, params, ok_codes, rtype, description):
        """Handle fetching, logging, errors and history."""
        t_start = time.time()
        try:
            response = self._browser.fetch(url, params, ok_codes=ok_codes)
        except:
            etype, value, tb = sys.exc_info()
            t_stop = time.time()
            t_delta = t_stop - t_start
            self.total_time += t_delta
            self.step_success = False
            self.test_status = 'Failure'
            self.logd(' Failed in %.3fs' % t_delta)
            if etype is HTTPError:
                self.log_response(value.response, rtype, description,
                                  t_start, t_stop, log_body=True)
                if self.dumping:
                    self.dump_content(value.response)
                raise self.failureException, str(value.response)
            else:
                self.log_response_error(url, rtype, description, t_start,
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
        self._browser.history.append((rtype, url))
        self.logd(' Done in %.3fs' % t_delta)
        self.log_response(response, rtype, description, t_start, t_stop)
        if self.dumping:
            self.dump_content(response)
        return response


    def browse(self, url_in, params_in=None,
               description=None, ok_codes=None,
               method='post',
               follow_redirect=True, load_auto_links=True,
               sleep=True):
        """Simulate a browser."""
        self._response = None
        # ok codes
        if ok_codes is None:
            ok_codes = self.ok_codes
        if type(params_in) is ListType:
            # convert list into a dict
            params = {}
            for key, value in params_in:
                params[key] = params.setdefault(key, [])
                params[key].append(value)
            for key, value in params.items():
                if len(value) == 1:
                    params[key] = value[0]
        else:
            params = params_in

        if method == 'get' and params:
            url = url_in + '?' + urlencode(params)
            params = None
        else:
            url = url_in

        if method == 'get':
            self.logd('GET: %s\n\tPage %i: %s ...' % (url, self.steps,
                                                      description or ''))
        else:
            url = url_in
            self.logd('POST: %s %s\n\tPage %i: %s ...' % (url, str(params),
                                                          self.steps,
                                                          description or ''))
        # Fetching
        response = self.connect(url, params, ok_codes, method, description)

        # Check redirection
        if follow_redirect and response.code in (301, 302):
            max_redirect_count = 10
            thread_sleep()              # give a chance to other threads
            while response.code in (301, 302) and max_redirect_count:
                # Figure the location - which may be relative
                newurl = response.headers['Location']
                url = urljoin(url_in, newurl)
                self.logd(' Load redirect link: %s' % url)
                response = self.connect(url, None, ok_codes, 'redirect', None)
                max_redirect_count -= 1
            if not max_redirect_count:
                self.logd(' WARNING Too many redirects give up.')

        # Load auto links (css and images)
        response.is_html = is_html(response.body)
        if load_auto_links and response.is_html:
            self.logd(' Load css and images...')
            page = response.body
            t_start = time.time()
            try:
                # pageImages is patched to log_response on all links
                self._browser.pageImages(url, page, self)
            except HTTPError, error:
                t_stop = time.time()
                t_delta = t_stop - t_start
                self.step_success = False
                self.test_status = 'Failure'
                self.logd('  Failed in %.2fs' % t_delta)
                self.log_response(error.response, 'link', None,
                                  t_start, t_stop, log_body=True)
                raise self.failureException, str(error)
            t_stop = time.time()
            self.logd('  Done in %.3fs' % (t_stop - t_start))
        if sleep:
            self.sleep()
        self._response = response
        return response


    def post(self, url, params=None, description=None, ok_codes=None):
        """POST method on url with params."""
        self.steps += 1
        self.page_responses = 0
        response = self.browse(url, params, description, ok_codes,
                               method="post")
        return response


    def get(self, url, params=None, description=None, ok_codes=None):
        """GET method on url adding params."""
        self.steps += 1
        self.page_responses = 0
        response = self.browse(url, params, description, ok_codes,
                               method="get")
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


    def xmlrpc_call(self, url_in, method_name, params=None, description=None):
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
            etype, value, tb = sys.exc_info()
            t_stop = time.time()
            t_delta = t_stop - t_start
            self.total_time += t_delta
            self.step_success = False
            self.test_status = 'Error'
            self.logd(' Failed in %.3fs' % t_delta)
            self.log_xmlrpc_response(url, method_name, description, response,
                                     t_start, t_stop, -1)
            if etype is SocketError:
                raise SocketError("Can't access %s." % url)
            raise
        t_stop = time.time()
        t_delta = t_stop - t_start
        self.total_time += t_delta
        self.total_xmlrpc += 1
        self.logd(' Done in %.3fs' % t_delta)
        self.log_xmlrpc_response(url, method_name, description, response,
                                 t_start, t_stop, 200)
        self.sleep()
        return response


    def waitUntilAvailable(self, url, time_out=20, sleep_time=2):
        """Wait until url is available.

        Try a get on url every sleep_time until server is reached or
        time is out."""
        time_start = time.time()
        while(True):
            try:
                response = self._browser.fetch(url, None,
                                               ok_codes=[200,301,302])
            except SocketError:
                if time.time() - time_start > time_out:
                    self.fail('Time out service %s not available after %ss' %
                              (url, time_out))
            else:
                return
            time.sleep(sleep_time)


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


    def setBasicAuth(self, login, password):
        """Set http basic authentication."""
        self._browser.setBasicAuth(login, password)
        self._authinfo = '%s:%s@' % (login, password)


    def clearBasicAuth(self):
        """Remove basic authentication."""
        self._browser.clearBasicAuth()
        self._authinfo = None

    #------------------------------------------------------------
    # logging
    #
    def logd(self, message):
        """Debug log."""
        self.logger.debug(self.meta_method_name +': ' +message)

    def logi(self, message):
        """Info log."""
        if hasattr(self, 'logger'):
            self.logger.info(self.meta_method_name+': '+message)
        else:
            print self.meta_method_name+': '+message

    def logr(self, message, force=False):
        """Log a result."""
        if force or not self.in_bench_mode or recording():
            self.logger_result.info(message)

    def open_result_log(self, **kw):
        """Open the result log."""
        xml = ['<funkload version="%s" time="%s">' % (
            get_version(), datetime.now().isoformat())]
        for key, value in kw.items():
            xml.append('<config key="%s" value=%s />' % (
                key, quoteattr(str(value))))
        self.logr('\n'.join(xml), force=True)

    def close_result_log(self):
        """Close the result log."""
        self.logr('</funkload>', force=True)

    def log_response_error(self, url, rtype, description, time_start,
                           time_stop):
        """Log a response that raise an unexpected exception."""
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
        info['type'] = rtype
        info['url'] = quoteattr(url)
        info['code'] = -1
        info['description'] = description and quoteattr(description) or '""'
        info['time_start'] = time_start
        info['duration'] = time_stop - time_start
        info['result'] = 'Error'
        info['traceback'] = quoteattr(' '.join(
            traceback.format_exception(*sys.exc_info())))
        message = '''<response cycle="%(cycle).3i" cvus="%(cvus).3i" thread="%(thread_id).3i" suite="%(suite_name)s" name="%(test_name)s" step="%(step).3i" number="%(number).3i" type="%(type)s" result="%(result)s" url=%(url)s code="%(code)s" description=%(description)s time="%(time_start)s" duration="%(duration)s" traceback=%(traceback)s />''' % info
        self.logr(message)

    def log_response(self, response, rtype, description, time_start, time_stop,
                     log_body=False):
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
        info['type'] = rtype
        info['url'] = quoteattr(response.url)
        info['code'] = response.code
        info['description'] = description and quoteattr(description) or '""'
        info['time_start'] = time_start
        info['duration'] = time_stop - time_start
        info['result'] = self.step_success and 'Successful' or 'Failure'
        response_start = '''<response cycle="%(cycle).3i" cvus="%(cvus).3i" thread="%(thread_id).3i" suite="%(suite_name)s" name="%(test_name)s" step="%(step).3i" number="%(number).3i" type="%(type)s" result="%(result)s" url=%(url)s code="%(code)s" description=%(description)s time="%(time_start)s" duration="%(duration)s"''' % info

        if not log_body:
            message = response_start + ' />'
        else:
            response_start = response_start + '>\n  <headers>'
            header_xml = []
            for key, value in response.headers.items():
                header_xml.append('    <header name="%s" value=%s />' % (
                    key, quoteattr(value)))
            headers = '\n'.join(header_xml) + '\n  </headers>'
            message = '\n'.join([
                response_start,
                headers,
                '  <body><![CDATA[\n%s\n]]>\n  </body>' % response.body,
                '</response>'])
        self.logr(message)

    def log_xmlrpc_response(self, url, method, description, response,
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
        self.logr(message)


    def log_result(self, time_start, time_stop):
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
        self.logr(text)


    def dump_content(self, response):
        """Dump the html content in a file.

        Use firefox to render the content if we are in rt viewing mode."""
        dump_dir = getattr(self.options, 'dump_dir', None)
        if dump_dir is None:
            return
        if getattr(response, 'code', 301) in [301, 302]:
            return
        if not response.body:
            return
        if not os.access(dump_dir, os.W_OK):
            os.mkdir(dump_dir, 0775)
        file_path = os.path.abspath(
            os.path.join(dump_dir, '%3.3i.html' % self.steps))
        f = open(file_path, 'w')
        f.write(response.body)
        f.close()
        if self.viewing:
            cmd = 'firefox -remote  "openfile(file://%s,new-tab)"' % file_path
            ret = os.system(cmd)

    #
    # Assertion helper
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
                ret = [x.href for x in a_links]
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

    #
    # extend unittest.TestCase
    #
    def setUpCycle(self):
        """Called on bench mode before a cycle start."""
        pass

    def tearDownCycle(self):
        """Called after a cycle in bench mode."""
        pass


    #
    # overriding unittest.TestCase
    #
    def __call__(self, result=None):
        """Run the test method.

        Override to trace test result."""
        t_start = time.time()
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._TestCase__testMethodName)
        try:
            try:
                self.logd('Starting -----------------------------------\n\t%s'
                          % self.conf_get(self.meta_method_name, 'description',
                                          ''))
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                self.test_status = 'Error'
                self.log_result(t_start, time.time())
                return

            ok = 0
            try:
                testMethod()
                ok = 1
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
                ok = 0
            if ok:
                result.addSuccess(self)

        finally:
            self.log_result(t_start, time.time())
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

