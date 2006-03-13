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
"""Base class for Response and Fetcher.

$Id$
"""
import re
from types import DictType, ListType
from urllib import urlencode
from utils import get_logger

# ------------------------------------------------------------
# Classes
#
class Upload:
    """Simple class that identify file uploads in POST data mappings."""
    def __init__(self, filename):
        self.filename = filename

    def __cmp__(self, other):
        return cmp(self.filename, other.filename)


class HTTPBaseResponse:
    """Base class for http response.

    Collects response information and provides a simple header parser.
    """
    splitheader = re.compile('^([^:\n]*): (.*)$', re.M)

    def __init__(self, url, method, params, **kw):
        self.url = url.strip()
        self.method = method
        self.params = params
        # init default
        self.type = 'unknown'
        self.size_download = 0
        self.code = -1
        self.headers = None
        self.body = None
        self.error = None
        self.traceback = None
        self.content_type = None
        self.connect_time = -1
        self.transfer_time = -1
        self.total_time = -1
        self.start = 0
        self.description = ''
        self.page = 0
        self.request = 0
        # user extra kw
        for key, value in kw.items():
            setattr(self, key, value)
        self.setType(self.code, self.type)
        if self.headers:
            self.headers_dict = self.parseHeaders(self.headers)
        else:
            self.headers_dict = {}

    def __str__(self):
        return ('<httpbaseresponse url="%s"'
                ' type="%s"'
                ' page="%s"'
                ' request="%s"'
                ' params="%s"'
                ' headers="%s"'
                ' error="%s" />' % (self.url, self.type, self.page,
                                    self.request,
                                    self.params, self.headers,
                                    self.error))

    def parseHeaders(self, headers):
        """Return a dict of headers key, value."""
        match = self.splitheader.findall(headers)
        return dict([(name.strip().lower(), value.strip())
                     for (name, value) in match])

    def getHeader(self, name, default=None):
        """Return the header value for the name."""
        return self.headers_dict.get(name.lower(), default)

    def setType(self, code, default=None):
        """Set the type depending on the code."""
        if code == -1:
            self.type = "error"
        elif code in (301, 302):
            self.type = "redirect"
        elif default:
            self.type = default

class BaseFetcher:
    """A base class for a fetcher."""

    def __init__(self, **kw):
        logger = get_logger(name='funkload.browser')
        self.logger = logger
        self.logd = logger.debug
        self.logi = logger.info
        self.logw = logger.warning
        self.loge = logger.error
        self.extra_headers = []

    def fetch(self, url_in, params_in=None, method=None, **kw):
        """Fetch a page using http method (get or post).

        The default method is get or post if there are params.

        The fetcher must hanldle cookies.

        return an HTTPBaseResponse or derived.

        extra kw are set as response attribute.
        """
        raise NotImplemented()

    def reset(self):
        """Reset the fetcher session."""
        raise NotImplemented()

    def addHeader(self, name, value):
        """Add an extra http header."""
        self.extra_headers.append((name, value))

    def setHeader(self, name, value):
        """Add or override an http header.

        If value is None, the name is removed."""
        headers = self.extra_headers
        for i, (k, v) in enumerate(headers):
            if k == name:
                if value is not None:
                    headers[i] = (name, value)
                else:
                    del headers[i]
                break
        else:
            if value is not None:
                headers.append((name, value))

    def delHeader(self, name):
        """Remove an http header name."""
        self.setHeader(name, None)

    def clearHeaders(self):
        """Remove all extra http headers."""
        self.extra_headers = []

    def setReferer(self, referer):
        """Set a referer using extra headers."""
        self.setHeader('Referer', referer)

    def setUserAgent(self, user_agent):
        """Set user agent using extra headers."""
        self.setHeader('User-Agent', user_agent)

    def prepareGetParams(self, params_in, encode=True):
        """Convert params for a get."""
        if not params_in:
            return params_in
        if isinstance(params_in, DictType):
            params = params_in
        elif isinstance(params_in, ListType):
            params = []
            for param in params_in:
                if isinstance(param, ListType):
                    # convert List into Tuple for urlencode
                    param = tuple(param)
                params.append(param)
        else:
            raise ValueError('Invalid params: %s' % str(params_in))
        if encode:
            return urlencode(params)
        return params

    def preparePostParams(self, params_in, encode=True):
        """Convert params for a post.

        Return a tuple (is_multipart, params).

        is_multipart is True if params contains a file upload."""
        is_multipart = False
        if not params_in:
            return params_in
        if isinstance(params_in, DictType):
            params_list = params_in.items()
        else:
            params_list = params_in
        params = []
        for (key, value) in params_list:
            if isinstance(value, Upload):
                is_multipart = True
                value = self.prepareUploadParam(value)
            params.append((key, value))
        if is_multipart:
            return (is_multipart, params)
        if encode:
            params = urlencode(params)
        return (is_multipart, params)

    def prepareUploadParam(self, value):
        """Hook to prepare file upload convertion."""
        return value
