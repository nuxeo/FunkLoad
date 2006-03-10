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
"""Browser using pyWebunit.

$Id$
"""
import sys
import traceback
from socket import error as SocketError
import time
from webunit.webunittest import WebFetcher, HTTPError
from basefetcher import HTTPBaseResponse, BaseFetcher
import PatchWebunit

class HTTPWebunitResponse(HTTPBaseResponse):
    """Collect an http webunit response."""
    def __init__(self, url, method, params, **kw):
        HTTPBaseResponse.__init__(self, url, method, params, **kw)
        self.total_time = kw['total_time']
        response = kw['response']
        if response:
            code = response.code
            if code:
                self.code = code
            headers = str(response.headers)
            if headers:
                self.headers = headers
                self.headers_dict = self.parseHeaders(headers)
            self.body = response.body
            if self.body:
                self.size_download += len(self.body)
            self.effective_url =  response.url
            self.content_type = self.getHeader('Content-Type')

    def __str__(self):
        return ('<httpwebunitresponse url="%s"'
                ' code="%s"'
                ' content_type="%s"'
                ' size_download="%d"'
                ' total_time="%.6fs"'
                ' error="%s" />' % (
            self.url, self.code, self.content_type, self.size_download,
            self.total_time, self.error))


class WebunitFetcher(BaseFetcher):
    """An html fetcher using Webunit."""
    # ------------------------------------------------------------
    # Initialisation
    #
    def __init__(self, **kw):
        BaseFetcher.__init__(self, **kw)
        self.webunit = None
        self.initWebunit()

    def initWebunit(self):
        """Init a webunit session.

        Clear the session if exists.
        """
        webunit = WebFetcher()
        webunit.clearContext()
        self.webunit = webunit

    reset = initWebunit

    def setBasicAuth(self, login, password):
        """Set http basic authentication."""
        self.webunit.setBasicAuth(login, password)

    def clearBasicAuth(self):
        """Remove basic authentication."""
        self.webunit.clearBasicAuth()

    def setExtraHeaders(self):
        """Setup extra_headers set by set/add/clearHeader."""
        self.webunit.extra_headers = self.extra_headers

    def fetch(self, url_in, params_in=None, method=None):
        """Webunit fetch impl.

        return an HTTPWebunitResponse."""
        webunit = self.webunit
        if method is None:
            method = params_in and 'post' or 'get'
        if method == 'post':
            url = url_in
            is_multipart, params = self.preparePostParams(params_in, False)
        else:
            params = self.prepareGetParams(params_in)
            if params:
                url = url_in + '?' + params
            else:
                url = url_in
        self.setExtraHeaders()
        error = None
        response = None
        t_start = time.time()
        ok_codes = [200, 301, 302, 401, 404, 500]
        try:
            response = webunit.fetch(url, params, ok_codes=ok_codes)
        except:
            etype, value, tback = sys.exc_info()
            if etype is HTTPError:
                error = 'webunit httperror'
                response = value.response
                self.loge(' webunit error: %s' % value.response)
            else:
                if etype is SocketError:
                    error = 'socket error on %s.' % url
                    self.loge(" webunit SocketError: Can't load %s." % url)
                else:
                    error = 'unknown'
                    self.loge(''.join(traceback.format_exception(
                        etype, value, tback)))
        t_stop = time.time()
        t_delta = t_stop - t_start
        return HTTPWebunitResponse(url, method, params,
                                   response=response, error=error,
                                   total_time=t_delta)


