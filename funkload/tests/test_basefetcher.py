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
#
"""Check an basefetcher.

$Id$
"""
import sys
import unittest
sys.path.append('./..')
from basefetcher import HTTPBaseResponse, BaseFetcher, Upload


class TestHTTPBaseResponse(unittest.TestCase):
    """Testing the HTTPBaseResponse."""

    def test_header(self):
        location = "http://127.0.0.1/blah?foo=bar"
        headers = """HTTP/1.1 302 Moved Temporarily
Server: Zope/(Zope 2.9.1-, python 2.1.2, linux) ZServer/1.1 FOO/3.4
Date: Wed, 08 Mar 2002 11:15:53 GMT
Bobo-Exception-Line: 114
Content-Length: 3766
Bobo-Exception-Value: See the server error log for details
Bobo-Exception-Type: Unauthorized
Location: %s
Content-Type: text/html; charset=iso-8859-15
""" % location

        resp = HTTPBaseResponse('http://localhost', 'get', None,
                                headers=headers)
        self.assertEquals(resp.getHeader('Location'), location)
        # case insensitive
        self.assertEquals(resp.getHeader('location'), location)
        self.assert_(resp.getHeader('Server'), resp.headers_dict)
        self.assert_(resp.getHeader('Content-Type'), resp.headers_dict)


class TestBaseFetcher(unittest.TestCase):
    """Testing the BaseFetcher."""

    def test_set_headers(self):
        fetcher = BaseFetcher()
        header = ('Name', 'Value')
        fetcher.setHeader(*header)
        self.assert_(header in fetcher.extra_headers)

        # override value
        header1 = ('Name', 'Value1')
        fetcher.setHeader(*header1)
        self.assert_(header not in fetcher.extra_headers,
                     fetcher.extra_headers)
        self.assert_(header1 in fetcher.extra_headers, fetcher.extra_headers)

        # new header
        header2 = ('Name2', 'Value2')
        fetcher.setHeader(*header2)
        self.assert_(header1 in fetcher.extra_headers, fetcher.extra_headers)
        self.assert_(header2 in fetcher.extra_headers, fetcher.extra_headers)

        # del header
        fetcher.delHeader('Name2')
        self.assert_(header2 not in fetcher.extra_headers,
                     fetcher.extra_headers)
        self.assert_(header1 in fetcher.extra_headers, fetcher.extra_headers)

        fetcher.setUserAgent('Foo')
        self.assert_(('User-Agent', 'Foo') in fetcher.extra_headers,
                     fetcher.extra_headers)

        fetcher.setReferer('Foo')
        self.assert_(('Referer', 'Foo') in fetcher.extra_headers,
                     fetcher.extra_headers)

    def test_get_params_01(self):
        fetcher = BaseFetcher()
        params = [['key', 'value'],
                  ['key2', 'value2']]
        ret = fetcher.prepareGetParams(params)
        self.assertEquals(ret, 'key=value&key2=value2')

    def test_get_params_02(self):
        fetcher = BaseFetcher()
        params = [['key', 'value'],
                  ['key2', 'value2'],
                  ['key2', 'value3']]
        ret = fetcher.prepareGetParams(params)
        self.assertEquals(ret, 'key=value&key2=value2&key2=value3')

    def test_get_params_03(self):
        fetcher = BaseFetcher()
        params = [('key', 'value'),
                  ['key2', 'value2'],
                  ('key2', 'value3')]
        ret = fetcher.prepareGetParams(params)
        self.assertEquals(ret, 'key=value&key2=value2&key2=value3')

    def test_get_params_04(self):
        fetcher = BaseFetcher()
        params = {'key': 'value',
                  'key2': 'value2'}
        ret = fetcher.prepareGetParams(params)
        self.assert_('key=value' in ret, ret)
        self.assert_('key2=value2' in ret, ret)

    def test_post_params_01(self):
        fetcher = BaseFetcher()
        params = [['key', 'value'],
                  ['key2', 'value2']]
        is_multi, ret = fetcher.preparePostParams(params)
        self.assert_(not is_multi)
        self.assertEquals(ret, 'key=value&key2=value2')

    def test_post_params_02(self):
        fetcher = BaseFetcher()
        params = [['key', 'value'],
                  ['key2', 'value2'],
                  ['key2', 'value3']]
        is_multi, ret = fetcher.preparePostParams(params)
        self.assert_(not is_multi)
        self.assertEquals(ret, 'key=value&key2=value2&key2=value3')

    def test_post_params_03(self):
        fetcher = BaseFetcher()
        params = [('key', 'value'),
                  ['key2', 'value2'],
                  ('key2', 'value3')]
        is_multi, ret = fetcher.preparePostParams(params)
        self.assert_(not is_multi)
        self.assertEquals(ret, 'key=value&key2=value2&key2=value3')

    def test_post_params_04(self):
        fetcher = BaseFetcher()
        params = {'key': 'value',
                  'key2': 'value2'}
        is_multi, ret = fetcher.preparePostParams(params)
        self.assert_(not is_multi)
        self.assert_('key=value' in ret, ret)
        self.assert_('key2=value2' in ret, ret)

    def test_post_params_05(self):
        fetcher = BaseFetcher()
        params = {'key': Upload('file-path'),
                  'key2': 'value2'}
        is_multi, ret = fetcher.preparePostParams(params)
        self.assert_(is_multi)
        self.assert_(('key2', 'value2') in ret, ret)

def test_suite():
    """Return a test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestHTTPBaseResponse))
    return suite

if __name__ in ('main', '__main__'):
    unittest.main()
