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
"""Patching Richard Jones' webunit, to :

 * cache css
 * store a browser history
 * log response

$Id: PatchWebunit.py 24649 2005-08-29 14:20:19Z bdelbosc $
"""

import sys
import time
import urlparse
import httplib
import cStringIO
from webunit import cookie
from webunit.utility import mimeEncode, boundary
from webunit.IMGSucker import IMGSucker
from webunit.webunittest import WebTestCase, WebFetcher
from webunit.webunittest import HTTPResponse, HTTPError, VERBOSE

from utils import thread_sleep

class FKLIMGSucker(IMGSucker):
    def __init__(self, url, session, ftestcase=None):
        IMGSucker.__init__(self, url, session)
        self.ftestcase = ftestcase

    def do_img(self, attributes):
        newattributes = []
        for name, value in attributes:
            if name == 'src':
                url = urlparse.urljoin(self.base, value)
                # TODO: figure the re-write path
                # newattributes.append((name, path))
                if not self.session.images.has_key(url):
                    t_start = time.time()
                    self.session.images[url] = self.session.fetch(url)
                    t_stop = time.time()
                    self.session.history.append(('image', url))
                    self.ftestcase.total_time += (t_stop - t_start)
                    self.ftestcase.total_images += 1
                    self.ftestcase.log_response(self.session.images[url],
                                                'image', None, t_start, t_stop)
                    thread_sleep()      # give a chance to other threads
            else:
                newattributes.append((name, value))
        # Write the img tag to file (with revised paths)
        self.unknown_starttag('img', newattributes)

    def do_link(self, attributes):
        newattributes = [('rel', 'stylesheet'), ('type', 'text/css')]
        for name, value in attributes:
            if name == 'href':
                url = urlparse.urljoin(self.base, value)
                # TODO: figure the re-write path
                # newattributes.append((name, path))
                if not self.session.css.has_key(url):
                    t_start = time.time()
                    self.session.css[url] = self.session.fetch(url)
                    t_stop = time.time()
                    self.session.history.append(('link', url))
                    self.ftestcase.total_time += (t_stop - t_start)
                    self.ftestcase.total_links += 1
                    self.ftestcase.log_response(self.session.css[url],
                                                'link', None, t_start, t_stop)
                    thread_sleep()      # give a chance to other threads
            else:
                newattributes.append((name, value))
        # Write the link tag to file (with revised paths)
        self.unknown_starttag('link', newattributes)

# remove webunit logging
def log(self, message, content):
    """Remove webunit logging."""
    pass
WebTestCase.log = log

def pageImages(self, url, page, testcase=None):
    '''Given the HTML page that was loaded from url, grab all the images.
    '''
    sucker = FKLIMGSucker(url, self, testcase)
    sucker.feed(page)
    sucker.close()

WebTestCase.pageImages = pageImages


# WebFetcher fetch
def WF_fetch(self, url, postdata=None, server=None, port=None, protocol=None,
             ok_codes=None):
    '''Run a single test request to the indicated url. Use the POST data
    if supplied.

    Raises failureException if the returned data contains any of the
    strings indicated to be Error Content.
    Returns a HTTPReponse object wrapping the response from the server.
    '''
    # see if the url is fully-qualified (not just a path)
    t_protocol, t_server, t_url, x, t_args, x = urlparse.urlparse(url)
    if t_server:
        protocol = t_protocol
        if ':' in t_server:
            server, port = t_server.split(':')
        else:
            server = t_server
            if protocol == 'http':
                port = '80'
            else:
                port = '443'
        url = t_url
        if t_args:
            url = url + '?' + t_args
        # ignore the machine name if the URL is for localhost
        if t_server == 'localhost':
            server = None
    elif not server:
        # no server was specified with this fetch, or in the URL, so
        # see if there's a base URL to use.
        base = self.get_base_url()
        if base:
            t_protocol, t_server, t_url, x, x, x = urlparse.urlparse(base)
            if t_protocol:
                protocol = t_protocol
            if t_server:
                server = t_server
            if t_url:
                url = urlparse.urljoin(t_url, url)

    # TODO: allow override of the server and port from the URL!
    if server is None: server = self.server
    if port is None: port = self.port
    if protocol is None: protocol = self.protocol
    if ok_codes is None: ok_codes = self.expect_codes

    if protocol == 'http':
        h = httplib.HTTP(server, int(port))
        if int(port) == 80:
           host_header = server
        else:
           host_header = '%s:%s'%(server, port)
    elif protocol == 'https':
        #if httpslib is None:
            #raise ValueError, "Can't fetch HTTPS: M2Crypto not installed"
        h = httplib.HTTPS(server, int(port))
        if int(port) == 443:
           host_header = server
        else:
           host_header = '%s:%s'%(server, port)
    else:
        raise ValueError, protocol

    params = None
    if postdata:
        for field,value in postdata.items():
            if type(value) == type({}):
                postdata[field] = []
                for k,selected in value.items():
                    if selected: postdata[field].append(k)

        # Do a post with the data file
        params = mimeEncode(postdata)
        h.putrequest('POST', url)
        h.putheader('Content-type', 'multipart/form-data; boundary=%s'%
            boundary)
        h.putheader('Content-length', str(len(params)))
    else:
        # Normal GET
        h.putrequest('GET', url)

    # Other Full Request headers
    if self.authinfo:
        h.putheader('Authorization', "Basic %s"%self.authinfo)
    h.putheader('Host', host_header)

    # FL Patch -------------------------
    for key, value in self.extra_headers:
        h.putheader(key, value)

    # FL Patch end ---------------------

    # Send cookies
    #  - check the domain, max-age (seconds), path and secure
    #    (http://www.ietf.org/rfc/rfc2109.txt)
    cookies_used = []
    cookie_list = []
    for domain, cookies in self.cookies.items():
        # check cookie domain
        if not server.endswith(domain):
            continue
        for path, cookies in cookies.items():
            # check that the path matches
            urlpath = urlparse.urlparse(url)[2]
            if not urlpath.startswith(path) and not (path == '/' and
                    urlpath == ''):
                continue
            for sendcookie in cookies.values():
                # and that the cookie is or isn't secure
                if sendcookie['secure'] and protocol != 'https':
                    continue
                # TODO: check max-age
                cookie_list.append("%s=%s;"%(sendcookie.key,
                    sendcookie.coded_value))
                cookies_used.append(sendcookie.key)

    if cookie_list:
        h.putheader('Cookie', ' '.join(cookie_list))

    # check that we sent the cookies we expected to
    if self.expect_cookies is not None:
        assert cookies_used == self.expect_cookies, \
            "Didn't use all cookies (%s expected, %s used)"%(
            self.expect_cookies, cookies_used)

    # finish the headers
    h.endheaders()

    if params is not None:
        h.send(params)

    # handle the reply
    errcode, errmsg, headers = h.getreply()

    # get the body and save it
    f = h.getfile()
    g = cStringIO.StringIO()
    d = f.read()
    while d:
        g.write(d)
        d = f.read()
    response = HTTPResponse(self.cookies, protocol, server, port, url,
        errcode, errmsg, headers, g.getvalue(), self.error_content)
    f.close()

    if errcode not in ok_codes:
        if VERBOSE:
            sys.stdout.write('e')
            sys.stdout.flush()
        raise HTTPError(response)

    # decode the cookies
    if self.accept_cookies:
        try:
            # decode the cookies and update the cookies store
            cookie.decodeCookies(url, server, headers, self.cookies)
        except:
            if VERBOSE:
                sys.stdout.write('c')
                sys.stdout.flush()
            raise

    # Check errors
    if self.error_content:
        data = response.body
        for content in self.error_content:
            if data.find(content) != -1:
                msg = "Matched error: %s"%content
                if hasattr(self, 'results') and self.results:
                    self.writeError(url, msg)
                self.log('Matched error'+`(url, content)`, data)
                if VERBOSE:
                    sys.stdout.write('c')
                    sys.stdout.flush()
                raise self.failureException, msg

    if VERBOSE:
        sys.stdout.write('_')
        sys.stdout.flush()
    return response

WebFetcher.fetch = WF_fetch
