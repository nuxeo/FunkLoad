# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Tom Lazar
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
"""Patching Richard Jones' webunit for FunkLoad.

* Add cache for links (css, js)
* store a browser history
* add headers
* log response
* remove webunit log
* fix HTTPResponse __repr__
* patching webunit mimeEncode to be rfc 1945 3.6.2 compliant using CRLF
* patching to remove cookie with a 'deleted' value
* patching to have application/x-www-form-urlencoded by default and only
  multipart when a file is posted
* patch fetch postdata must be [(key, value) ...] no more dict or list value

$Id: PatchWebunit.py 24649 2005-08-29 14:20:19Z bdelbosc $
"""
import os
import sys
import time
import urlparse
from urllib import urlencode
import httplib
import cStringIO
from mimetypes import guess_type

from webunit import cookie
from webunit.IMGSucker import IMGSucker
from webunit.webunittest import WebTestCase, WebFetcher
from webunit.webunittest import HTTPResponse, HTTPError, VERBOSE
from webunit.utility import Upload

from utils import thread_sleep, Data
import re

valid_url = re.compile(r'^(http|https)://[a-z0-9\.\-\:]+(\/[^\ \t\<\>]*)?$',
                       re.I)

BOUNDARY = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
SEP_BOUNDARY = '--' + BOUNDARY
END_BOUNDARY = SEP_BOUNDARY + '--'

def mimeEncode(data, sep_boundary=SEP_BOUNDARY, end_boundary=END_BOUNDARY):
    '''Take the mapping of data and construct the body of a
    multipart/form-data message with it using the indicated boundaries.
    '''
    ret = cStringIO.StringIO()
    first_part = True
    for key, value in data:
        if not key:
            continue
        # Don't add newline before first part
        if first_part:
            first_part = False
        else:
            ret.write('\r\n')
        ret.write(sep_boundary)
        if isinstance(value, Upload):
            ret.write('\r\nContent-Disposition: form-data; name="%s"'%key)
            ret.write('; filename="%s"\r\n' % os.path.basename(value.filename))
            if value.filename:
                mimetype = guess_type(value.filename)[0]
                if mimetype is not None:
                    ret.write('Content-Type: %s\r\n' % mimetype)
                value = open(os.path.join(value.filename), "rb").read()
            else:
                value = ''
            ret.write('\r\n')
        else:
            ret.write('\r\nContent-Disposition: form-data; name="%s"'%key)
            ret.write("\r\n\r\n")
        ret.write(str(value))
        if value and value[-1] == '\r':
            ret.write('\r\n')  # write an extra newline
    ret.write('\r\n')
    ret.write(end_boundary)
    ret.write('\r\n')
    return ret.getvalue()


class FKLIMGSucker(IMGSucker):
    """Image and links loader, patched to log response stats."""
    def __init__(self, url, session, ftestcase=None):
        IMGSucker.__init__(self, url, session)
        self.ftestcase = ftestcase

    def do_img(self, attributes):
        """Process img tag."""
        newattributes = []
        for name, value in attributes:
            if name == 'src':
                # construct full url
                url = urlparse.urljoin(self.base, value)
                # make sure it's syntactically valid
                if not valid_url.match(url):
                    continue
                # TODO: figure the re-write path
                # newattributes.append((name, path))
                if not self.session.images.has_key(url):
                    self.ftestcase.logdd('    img: %s ...' % url)
                    t_start = time.time()
                    self.session.images[url] = self.session.fetch(url)
                    t_stop = time.time()
                    self.ftestcase.logdd('     Done in %.3fs' %
                                         (t_stop - t_start))
                    self.session.history.append(('image', url))
                    self.ftestcase.total_time += (t_stop - t_start)
                    self.ftestcase.total_images += 1
                    self.ftestcase._log_response(self.session.images[url],
                                                 'image', None, t_start,
                                                 t_stop)
                    thread_sleep()      # give a chance to other threads
            else:
                newattributes.append((name, value))
        # Write the img tag to file (with revised paths)
        self.unknown_starttag('img', newattributes)

    def do_link(self, attributes):
        """Process link tag."""
        newattributes = [('rel', 'stylesheet'), ('type', 'text/css')]
        for name, value in attributes:
            if name == 'href':
                # construct full url
                url = urlparse.urljoin(self.base, value)
                # make sure it's syntactically valid
                if not valid_url.match(url):
                    continue
                # TODO: figure the re-write path
                # newattributes.append((name, path))
                if not self.session.css.has_key(url):
                    self.ftestcase.logdd('    link: %s ...' % url)
                    t_start = time.time()
                    self.session.css[url] = self.session.fetch(url)
                    t_stop = time.time()
                    self.ftestcase.logdd('     Done in %.3fs' %
                                         (t_stop - t_start))
                    self.session.history.append(('link', url))
                    self.ftestcase.total_time += (t_stop - t_start)
                    self.ftestcase.total_links += 1
                    self.ftestcase._log_response(self.session.css[url],
                                                 'link', None, t_start, t_stop)
                    thread_sleep()      # give a chance to other threads
            else:
                newattributes.append((name, value))
        # Write the link tag to file (with revised paths)
        self.unknown_starttag('link', newattributes)

# remove webunit logging
def WTC_log(self, message, content):
    """Remove webunit logging."""
    pass
WebTestCase.log = WTC_log

# use fl img sucker
def WTC_pageImages(self, url, page, testcase=None):
    '''Given the HTML page that was loaded from url, grab all the images.
    '''
    sucker = FKLIMGSucker(url, self, testcase)
    sucker.feed(page)
    sucker.close()

WebTestCase.pageImages = WTC_pageImages


# WebFetcher fetch
def WF_fetch(self, url, postdata=None, server=None, port=None, protocol=None,
             ok_codes=None, key_file=None, cert_file=None, method="GET"):
    '''Run a single test request to the indicated url. Use the POST data
    if supplied. Accepts key and certificate file paths for https (ssl/tls)
    connections.

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
    if server is None:
        server = self.server
    if port is None:
        port = self.port
    if protocol is None:
        protocol = self.protocol
    if ok_codes is None:
        ok_codes = self.expect_codes
    webproxy = {}

    if protocol == 'http':
        try:
            proxystring = os.environ["http_proxy"].replace("http://", "")
            webproxy['host'] = proxystring.split(":")[0]
            webproxy['port'] = int(proxystring.split(":")[1])
        except (KeyError, IndexError, ValueError):
            webproxy = False

        if webproxy:
            h = httplib.HTTPConnection(webproxy['host'], webproxy['port'])
        else:
            h = httplib.HTTP(server, int(port))
        if int(port) == 80:
            host_header = server
        else:
            host_header = '%s:%s' % (server, port)
    elif protocol == 'https':
        #if httpslib is None:
            #raise ValueError, "Can't fetch HTTPS: M2Crypto not installed"

        # FL Patch -------------------------

        # patched to use the given key and cert file
        h = httplib.HTTPS(server, int(port), key_file, cert_file)

        # FL Patch end  -------------------------

        if int(port) == 443:
            host_header = server
        else:
            host_header = '%s:%s' % (server, port)
    else:
        raise ValueError, protocol

    headers = []
    params = None
    if postdata is not None:
        if webproxy:
            h.putrequest(method.upper(), "http://%s%s" % (host_header, url))
        else:
            # Normal post
            h.putrequest(method.upper(), url)
        if postdata:
            if isinstance(postdata, Data):
                # User data and content_type
                params = postdata.data
                if postdata.content_type:
                    headers.append(('Content-type', postdata.content_type))
            else:
                # Check for File upload
                is_multipart = False
                for field, value in postdata:
                    if isinstance(value, Upload):
                        # Post with a data file requires multipart mimeencode
                        is_multipart = True
                        break
                if is_multipart:
                    params = mimeEncode(postdata)
                    headers.append(('Content-type', 'multipart/form-data; boundary=%s'%
                                    BOUNDARY))
                else:
                    params = urlencode(postdata)
                    headers.append(('Content-type', 'application/x-www-form-urlencoded'))
            headers.append(('Content-length', str(len(params))))
    else:
        if webproxy:
            h.putrequest(method.upper(), "http://%s%s" % (host_header, url))
        else:
            h.putrequest(method.upper(), url)

    # Other Full Request headers
    if self.authinfo:
        headers.append(('Authorization', "Basic %s"%self.authinfo))
    if not webproxy:
        # HTTPConnection seems to add a host header itself.
        # So we only need to do this if we are not using a proxy.
        headers.append(('Host', host_header))

    # FL Patch -------------------------
    for key, value in self.extra_headers:
        headers.append((key, value))

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
                # TODO: check for expires (max-age is working)
                # hard coded value that application can use to work
                # around expires
                if sendcookie.coded_value in ('"deleted"', "null", "deleted"):
                    continue
                cookie_list.append("%s=%s;"%(sendcookie.key,
                                            sendcookie.coded_value))
                cookies_used.append(sendcookie.key)

    if cookie_list:
        headers.append(('Cookie', ' '.join(cookie_list)))

    # check that we sent the cookies we expected to
    if self.expect_cookies is not None:
        assert cookies_used == self.expect_cookies, \
            "Didn't use all cookies (%s expected, %s used)"%(
            self.expect_cookies, cookies_used)


    # write and finish the headers
    for header in headers:
        h.putheader(*header)
    h.endheaders()

    if self.debug_headers:
        for header in headers:
            print "Putting header -- %s: %s" % header

    if params is not None:
        h.send(params)

    # handle the reply
    if webproxy:
        r = h.getresponse()
        errcode = r.status
        errmsg = r.reason
        headers = r.msg
        if headers is None or headers.has_key('content-length') and headers['content-length'] == "0":
            data = None
        else:
            data = r.read()
        response = HTTPResponse(self.cookies, protocol, server, port, url,
                                errcode, errmsg, headers, data,
                                self.error_content)

    else:
        # get the body and save it
        errcode, errmsg, headers = h.getreply()
        if headers is None or headers.has_key('content-length') and headers['content-length'] == "0":
            response = HTTPResponse(self.cookies, protocol, server, port, url,
                                    errcode, errmsg, headers, None,
                                    self.error_content)
        else:
            f = h.getfile()
            g = cStringIO.StringIO()
            d = f.read()
            while d:
                g.write(d)
                d = f.read()
            response = HTTPResponse(self.cookies, protocol, server, port, url,
                                    errcode, errmsg, headers, g.getvalue(),
                                    self.error_content)
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
                msg = "Matched error: %s" % content
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


def HR___repr__(self):
    """fix HTTPResponse rendering."""
    return """<response url="%s://%s:%s%s" code="%s" message="%s" />""" % (
        self.protocol, self.server, self.port, self.url, self.code,
        self.message)

HTTPResponse.__repr__ = HR___repr__

