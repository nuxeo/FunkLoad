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
from utils import recording, thread_sleep

_marker = []
__version__ = '1.0.0'

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
        expect_codes = self.conf_getList(section, 'expect_codes',
                                         [200, 301, 302])
        self.expect_codes = map(int, expect_codes)
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
        self.response_count = 0
        self.total_time = 0.0
        self.total_pages = self.total_images = 0
        self.total_links = self.total_redirects = 0
        #self.logd('# FunkLoadTestCase.clearContext done')



    #------------------------------------------------------------
    # configuration file utils
    #
    def conf_get(self, section, key, default=_marker):
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
            self.logi('[%s] %s not found' % (section, key))
            if default is _marker:
                raise
            val = default
        #print('[%s] %s = %s from config.' % (section, key, val))
        return val


    def conf_getInt(self, section, key, default=_marker):
        """Return an integer from th econfiguration file."""
        return int(self.conf_get(section, key, default))

    def conf_getFloat(self, section, key, default=_marker):
        """Return a float from th econfiguration file."""
        return float(self.conf_get(section, key, default))

    def conf_getList(self, section, key, default=_marker):
        """Return a list from th econfiguration file."""
        value = self.conf_get(section, key, default)
        if value is default:
            return value
        if value.count(':'):
            return value.split(':')
        return [value]



    #------------------------------------------------------------
    # browser simulation
    #

    def connect(self, url, params, code, rtype, description):
        """Handle fetching, logging, errors and history."""
        t_start = time.time()
        try:
            response = self._browser.fetch(url, params, ok_codes=code)
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
                raise self.failureException, str(value.response)
            else:
                self.log_response_error(url, rtype, description, t_start,
                                        t_stop)
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
        return response


    def browse(self, url_in, params_in=None,
               description=None, code=None,
               method='post',
               follow_redirect=True, load_auto_links=True,
               sleep=True):
        """Simulate a browser."""
        self._response = None
        # ok codes
        if code is None:
            code = self.expect_codes
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
            url = url_in + '?' + urlencode(params_in)
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
        response = self.connect(url, params, code, method, description)

        # Check redirection
        if follow_redirect and response.code in (301, 302):
            max_redirect_count = 10
            thread_sleep()              # give a chance to other threads
            while response.code in (301, 302) and max_redirect_count:
                # Figure the location - which may be relative
                newurl = response.headers['Location']
                url = urljoin(url, newurl)
                self.logd(' Load redirect link: %s' % url)
                response = self.connect(url, None, code, 'redirect', None)
                max_redirect_count -= 1

        # Load auto links (css and images)
        if load_auto_links:
            self.logd(' Load css and images...')
            page = response.body
            t_start = time.time()
            try:
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
        if self.dumping:
            self.dump_content(response)
        return response


    def post(self, url, params=None, description=None, code=None):
        """POST method on url with params."""
        self.steps += 1
        response = self.browse(url, params, description, code, method="post")
        return response


    def get(self, url, params=None, description=None, code=None):
        """GET method on url adding params."""
        self.steps += 1
        response = self.browse(url, params, description, code, method="get")
        return response


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
            __version__, datetime.now().isoformat())]
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
        self.response_count += 1
        info = {}
        info['cycle'] = self.cycle
        info['cvus'] = self.cvus
        info['thread_id'] = self.thread_id
        info['suite_name'] = self.suite_name
        info['test_name'] = self.test_name
        info['step'] = self.steps
        info['number'] = self.response_count
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
        self.response_count += 1
        info = {}
        info['cycle'] = self.cycle
        info['cvus'] = self.cvus
        info['thread_id'] = self.thread_id
        info['suite_name'] = self.suite_name
        info['test_name'] = self.test_name
        info['step'] = self.steps
        info['number'] = self.response_count
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
        info['requests'] = self.response_count
        info['pages'] = self.total_pages
        info['redirects'] = self.total_redirects
        info['images'] = self.total_images
        info['links'] = self.total_links
        info['result'] = self.test_status
        if self.test_status != 'Successful':
            info['traceback'] = 'traceback=' + quoteattr(' '.join(
                traceback.format_exception(*sys.exc_info()))) + ' '
        else:
            info['traceback'] = ''
        text = '''<testResult cycle="%(cycle).3i" cvus="%(cvus).3i" thread="%(thread_id).3i" suite="%(suite_name)s" name="%(test_name)s"  time="%(time_start)s" result="%(result)s" steps="%(steps)s" duration="%(duration)s" connection_duration="%(connection_duration)s" requests="%(requests)s" pages="%(pages)s" redirects="%(redirects)s" images="%(images)s" links="%(links)s" %(traceback)s/>''' % info
        self.logr(text)


    def dump_content(self, response):
        """Dump the html content in a file.

        Use firefox to render the content if we are in rt viewing mode."""
        dump_dir = getattr(self.options, 'dump_dir', None)
        if dump_dir is None:
            return
        if not os.access(dump_dir, os.W_OK):
            os.mkdir(dump_dir, 0775)
        file_path = os.path.abspath(
            os.path.join(dump_dir, '%3.3i.html' % self.steps))
        f = open(file_path, 'w')
        f.write(response.body)
        f.close()
        if self.viewing:
            cmd = 'firefox -remote  "openfile(file://%s, new-tab)"' % file_path
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
        """Return the current response content."""
        response = self._response
        if response is not None:
            return response.body
        return ''

    def listHref(self, pattern=None):
        """Return a list of href anchor url present in the html response.

        that match sub pattern regex if present"""
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

