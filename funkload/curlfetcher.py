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
"""Browser using pyCurl.

$Id$
"""
from cStringIO import StringIO
import time
import pycurl
import traceback
from basefetcher import HTTPBaseResponse, BaseFetcher


class HTTPCurlResponse(HTTPBaseResponse):
    """Collect an http curl response."""
    def __init__(self, url, method, params, **kw):
        HTTPBaseResponse.__init__(self, url, method, params, **kw)
        curl = kw['curl']
        code = curl.getinfo(curl.RESPONSE_CODE)
        if code:
            self.code = code
            self.setType(code, kw.get('type'))
        self.effective_url = curl.getinfo(curl.EFFECTIVE_URL)
        self.connect_time = curl.getinfo(curl.CONNECT_TIME)
        self.transfer_time = curl.getinfo(curl.TOTAL_TIME)
        self.total_time = self.connect_time + self.transfer_time
        self.size_upload = curl.getinfo(curl.SIZE_UPLOAD)
        self.size_download = curl.getinfo(curl.SIZE_DOWNLOAD)
        self.content_type = curl.getinfo(curl.CONTENT_TYPE)
        #self.cookies = curl.getinfo(curl.COOKIELIST)

    def __str__(self):
        return ('<httpcurlresponse url="%s"'
                ' type="%s"'
                ' code="%s"'
                ' content_type="%s"'
                ' size_download="%d"'
                ' connect_time="%.6fs"'
                ' total_time="%.6fs"'
                ' error="%s" />' % (
            self.url, self.type, self.code, self.content_type,
            self.size_download, self.connect_time, self.total_time,
            self.error))


class CurlFetcher(BaseFetcher):
    """An html fetcher using pyCurl."""
    # ------------------------------------------------------------
    # Initialisation
    #
    def __init__(self, **kw):
        BaseFetcher.__init__(self, **kw)
        self.curl = None
        self.initCurl()

    def initCurl(self):
        """Init a curl session.

        Clear the session if exists.
        """
        if self.curl is not None:
            self.curl.close()
        curl = pycurl.Curl()
        curl.setopt(curl.FOLLOWLOCATION, False) # no handle redirect
        curl.setopt(curl.SSL_VERIFYHOST, 0) # no ssl check by default
        curl.setopt(curl.SSL_VERIFYPEER, 0)
        curl.setopt(curl.NOSIGNAL, True)
        self.curl = curl
        self.curlVerbose(0)

    reset = initCurl

    def curlVerbose(self, level):
        """Curl verbose mode."""
        curl = self.curl
        if not level:
            curl.setopt(pycurl.VERBOSE, 0)
        else:
            def debug_curl(level, message):
                """Debug message from curl engine."""
                self.logd("curl [%d]: %s" % (level, message))
            curl.setopt(pycurl.VERBOSE, level)
            curl.setopt(pycurl.DEBUGFUNCTION, debug_curl)

    def setReferer(self, referer):
        """Set a referer."""
        curl = self.curl
        curl.setopt(curl.REFERER, referer)

    def setUserAgent(self, user_agent):
        """Set the user agent."""
        curl = self.curl
        curl.setopt(curl.USERAGENT, user_agent)

    def setBasicAuth(self, login, password):
        """Set http basic authentication."""
        curl = self.curl
        curl.setopt(curl.USERPWD, login +':' + password)
        curl.setopt(curl.HTTPAUTH, curl.HTTPAUTH_BASIC)

    def clearBasicAuth(self):
        """Remove basic authentication."""
        curl = self.curl
        curl.setopt(curl.USERPWD, '')
        #curl.setopt(curl.HTTPAUTH, )

    def setExtraHeaders(self):
        """Setup extra_headers set by set/add/clearHeader."""
        curl = self.curl
        headers_list = ["%s: %s" % (key, value)
                        for (key, value) in self.extra_headers]
        curl.setopt(curl.HTTPHEADER, headers_list)

    def fetch(self, url_in, params_in=None,  method=None, **kw):
        """Curl post impl.

        return an HTTPCurlResponse."""
        body = StringIO()
        headers = StringIO()
        curl = self.curl
        curl.setopt(curl.WRITEFUNCTION, body.write)
        curl.setopt(curl.HEADERFUNCTION, headers.write)
        self.setExtraHeaders()

        if method is None:
            method = params_in and 'post' or 'get'
        if method == 'post':
            url = url_in
            curl.setopt(curl.URL, url)
            is_multipart, params = self.preparePostParams(params_in)
            if is_multipart:
                curl.setopt(curl.HTTPPOST, params)
            else:
                curl.setopt(curl.POST, True)
                if params:
                    curl.setopt(curl.POSTFIELDS, params)
        else:
            params = self.prepareGetParams(params_in)
            if params:
                url = url_in + '?' + params
            else:
                url = url_in
            curl.setopt(curl.URL, url)
            curl.setopt(curl.HTTPGET, True)

        error = None
        start = time.time()
        try:
            curl.perform()
        except pycurl.error, v:
            error = v
            self.loge('pycurl error: ' + str(error))
        except:
            error = 'unknown'
            self.loge(''.join(traceback.format_exception(*sys.exc_info())))

        return HTTPCurlResponse(url, method, params,
                                headers=headers.getvalue(),
                                body=body.getvalue(),
                                error=error, curl=curl,
                                start=start, **kw)

    def prepareUploadParam(self, value):
        """Convert params return params url encoded if not multipart."""
        return (pycurl.FORM_FILE, value.filename)


