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
import re
from types import DictType, ListType
from urllib import urlencode
from utils import get_logger

# ------------------------------------------------------------
# Classes
#
class Upload:
    """Simple class that lets us identify file uploads in POST data mappings.

    """
    def __init__(self, filename):
        self.filename = filename

    def __cmp__(self, other):
        return cmp(self.filename, other.filename)


class HTTPBaseResponse:
    """Base http response that knows how to split header."""
    splitheader = re.compile('^([^:\n]*): (.*)$', re.M)

    def __init__(self, url, method, params, **kw):
        self.url = url.strip()
        self.method = method
        self.params = params
        self.size_download = 0
        self.code = kw.get('code', '-1')
        self.header = kw.get('header')
        self.body = kw.get('body')
        self.error = str(kw.get('error'))
        self.traceback = kw.get('traceback')
        self.content_type = kw.get('content_type')
        if self.header:
            self.headers = self.getheaders()
        else:
            self.headers = {}

    def __str__(self):
        return ('<httpbaseresponse url="%s"'
                ' params="%s"'
                ' header="%s"'
                ' error="%s" />' % (self.url, self.params, self.header,
                                    self.error))

    def getheaders(self):
        """Return a dict of headers value."""
        headers = self.splitheader.findall(self.header)
        return dict([(key.strip(), value.strip()) for (key, value) in headers])

    def getheader(self, name, default=None):
        """Return the header value for the name."""
        return self.headers.get(name, default)


class BaseFetcher:
    """An html fetcher."""

    def __init__(self, **kw):
        logger = get_logger(name='funkload.browser')
        self.logger = logger
        self.logd = logger.debug
        self.logi = logger.info
        self.logw = logger.warning
        self.loge = logger.error
        self.extra_headers = []

    def reset(self):
        """Reset the fetcher session."""

    def fetch(self, url_in, method='get', params_in=None):
        """Fetch a page.

        Handles save and send cookies.

        return an HTTPBaseResponse or a HTTPBaseError.
        """

    def addHeader(self, key, value):
        """Add an http header."""
        self.extra_headers.append((key, value))

    def setHeader(self, key, value):
        """Add or override an http header.

        If value is None, the key is removed."""
        headers = self.extra_headers
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
        self.extra_headers = []

    def setReferer(self, referer):
        """Set a referer."""
        self.setHeader('Referer', referer)

    def setUserAgent(self, user_agent):
        """Set user agent."""
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
        """Convert post params.

        Return a tuple (is_multipart, params)."""
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
        """Convert an upload file can be overriden."""
        return value
