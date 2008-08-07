# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Tim Baverstock, Matthew Vail, Matt Sparks
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
import Cookie
import re
import Queue
import threading
from mimetypes import guess_type

from webunit import cookie
from webunit.IMGSucker import IMGSucker
from webunit.webunittest import WebTestCase, WebFetcher
from webunit.webunittest import HTTPResponse, HTTPError, VERBOSE
from webunit.utility import Upload

from utils import thread_sleep


FETCH_THREADS = 4
BOUNDARY = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
SEP_BOUNDARY = '--' + BOUNDARY
END_BOUNDARY = SEP_BOUNDARY + '--'


# NOTE(msparks): decodeCookies() below was copied from webunit and modified
# slightly to allow for an option to be less strict about the domain given in a
# cookie.
def decodeCookies(url, server, headers, cookies, strict_cookies=True):
    '''Decode cookies into the supplied cookies dictionary.

    The 'strict_cookies' argument controls the obedience to RFC 2109. A value of
    False will silently ignore cookie domain violations, while a True value will
    throw exceptions.

    See also:
      http://www.ietf.org/rfc/rfc2109.txt
    '''
    # the path of the request URL up to, but not including, the right-most /
    request_path = urlparse.urlparse(url)[2]
    if len(request_path) > 1 and request_path[-1] == '/':
        request_path = request_path[:-1]

    hdrcookies = Cookie.SimpleCookie("\n".join(map(lambda x: x.strip(),
        headers.getallmatchingheaders('set-cookie'))))
    for morsel in hdrcookies.values():
        # XXX: there doesn't seem to be a way to determine if the
        # cookie was set or defaulted to an empty string :(
        if morsel['domain']:
            domain = morsel['domain']

            # reject if The value for the Domain attribute contains no
            # embedded dots or does not start with a dot.
            if strict_cookies and '.' not in domain:
                raise cookie.Error, 'Cookie domain "%s" has no "."'%domain
            if strict_cookies and domain[0] != '.':
                raise cookie.Error, 'Cookie domain "%s" doesn\'t start '\
                    'with "."'%domain
            # reject if The value for the request-host does not
            # domain-match the Domain attribute.
            if strict_cookies and not server.endswith(domain):
                raise cookie.Error, 'Cookie domain "%s" doesn\'t match '\
                    'request host "%s"'%(domain, server)
            # reject if The request-host is a FQDN (not IP address) and
            # has the form HD, where D is the value of the Domain
            # attribute, and H is a string that contains one or more dots.
            if re.search(r'[a-zA-Z]', server):
                H = server[:-len(domain)]
                if strict_cookies and '.' in H:
                    raise cookie.Error, 'Cookie domain "%s" too short '\
                    'for request host "%s"'%(domain, server)
        else:
            domain = server

        # path check
        path = morsel['path'] or request_path
        # reject if Path attribute is not a prefix of the request-URI
        # (noting that empty request path and '/' are often synonymous, yay)
        if strict_cookies and not (request_path.startswith(path) or
                           (request_path == '' and morsel['path'] == '/')):
            raise cookie.Error, 'Cookie path "%s" doesn\'t match '\
                'request url "%s"'%(path, request_path)

        bydom = cookies.setdefault(domain, {})
        bypath = bydom.setdefault(path, {})
        bypath[morsel.key] = morsel


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
            ret.write('; filename="%s"\r\n' % value.filename)
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
    return ret.getvalue()

# NOTE(msparks): the FKLIMGSucker class was modified to support threaded
# fetching.
class FKLIMGSucker(IMGSucker):
    """Image and links loader, patched to log response stats."""
    _MSG_DIE = 0
    _MSG_IMG = 1
    _MSG_LINK = 2

    def __init__(self, url, session, ftestcase=None):
        IMGSucker.__init__(self, url, session)
        self.lock = threading.RLock()
        self.ftestcase = ftestcase
        self.fetch_queue = Queue.Queue()
        self.exception_queue = Queue.Queue()
        self.signal_main = threading.Event()
        self.can_continue = threading.Event()
        self.can_continue.set()
        self.suckers = []
        self.suckers_alive = 0
        for i in range(FETCH_THREADS):
            thread = threading.Thread(target=self.fetcher, args=(i,))
            thread.start()
            self.suckers.append(thread)

    def fetcher(self, thread_id):
        """Threaded image and link fetcher.

        This method is called automatically by a Thread instance created in
        __init__.

        Args:
          thread_id: assigned ID number
        """
        self.lock.acquire()
        self.suckers_alive += 1
        self.lock.release()
        self.ftestcase.flogger.logdd('thread %d starting' % thread_id)
        while True:
            self.can_continue.wait()  # wait until we can proceed
            try:
                (item_type, item_content) = self.fetch_queue.get()
                if item_type == self._MSG_DIE:
                    self.lock.acquire()
                    self.suckers_alive -= 1
                    self.lock.release()
                    if not self.suckers_alive:
                        self.signal_main.set()  # we're the last thread to exit
                    self.ftestcase.flogger.logdd('thread %d exiting' %
                                                 thread_id)
                    return
                elif item_type == self._MSG_IMG:
                    self.process_img(item_content)
                elif item_type == self._MSG_LINK:
                    self.process_link(item_content)
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if (exc_type == HTTPError and
                    self.ftestcase._accept_invalid_links):
                    self.ftestcase.flogger.logd('  ' + str(exc_value))
                else:
                    self.exception_queue.put(exc_value)
                    self.can_continue.clear()   # block fetcher threads
                    self.signal_main.set()      # signal main thread

    def do_img(self, attributes):
        """Add img tag to fetch queue."""
        self.fetch_queue.put((self._MSG_IMG, attributes))

    def process_img(self, attributes):
        """Process img tag."""
        newattributes = []
        for name, value in attributes:
            if name == 'src':
                url = urlparse.urljoin(self.base, value)
                # TODO: figure the re-write path
                # newattributes.append((name, path))
                if not self.session.images.has_key(url):
                    self.ftestcase.logdd('    img: %s ...' % url)
                    t_start = time.time()
                    fetch_content = self.session.fetch(url)
                    t_stop = time.time()
                    self.ftestcase.logdd('     Done in %.3fs' %
                                         (t_stop - t_start))

                    self.lock.acquire()
                    try:
                        self.session.images[url] = fetch_content
                        self.session.history.append(('image', url))
                        self.ftestcase.total_images += 1
                    finally:
                        self.lock.release()

                    self.ftestcase._log_response(self.session.images[url],
                                                 'image', None, t_start,
                                                 t_stop)
                    thread_sleep()      # give a chance to other threads
            else:
                newattributes.append((name, value))
        # Write the img tag to file (with revised paths)
        self.lock.acquire()
        try:
            self.unknown_starttag('img', newattributes)
        finally:
            self.lock.release()

    def do_link(self, attributes):
        """Add link tag to fetch queue."""
        self.fetch_queue.put((self._MSG_LINK, attributes))

    def process_link(self, attributes):
        """Process link tag."""
        newattributes = [('rel', 'stylesheet'), ('type', 'text/css')]
        for name, value in attributes:
            if name == 'href':
                url = urlparse.urljoin(self.base, value)
                # TODO: figure the re-write path
                # newattributes.append((name, path))
                if not self.session.css.has_key(url):
                    self.ftestcase.logdd('    link: %s ...' % url)
                    t_start = time.time()
                    fetch_content = self.session.fetch(url)
                    t_stop = time.time()
                    self.ftestcase.logdd('     Done in %.3fs' %
                                         (t_stop - t_start))

                    self.lock.acquire()
                    try:
                        self.session.css[url] = fetch_content
                        self.session.history.append(('link', url))
                        self.ftestcase.total_links += 1
                    finally:
                        self.lock.release()

                    self.ftestcase._log_response(self.session.css[url],
                                                 'link', None, t_start, t_stop)
                    thread_sleep()      # give a chance to other threads
            else:
                newattributes.append((name, value))
        # Write the link tag to file (with revised paths)
        self.lock.acquire()
        try:
            self.unknown_starttag('link', newattributes)
        finally:
            self.lock.release()

    def send_die_messages(self):
        """Add die messages to the fetch queue."""
        for i in range(FETCH_THREADS):
            self.fetch_queue.put((self._MSG_DIE, None))  # make threads exit

    def kill_suckers(self):
        """Replace all pending messages in the fetch queue with die messages and
        wait until all sucker threads have exited."""
        self.can_continue.clear()
        try:
            while not self.fetch_queue.empty():
                self.fetch_queue.get(block=False)
        except Queue.Empty:
            pass
        self.send_die_messages()
        self.signal_main.clear()
        self.can_continue.set()
        self.signal_main.wait()

    def close(self):
        """Close the sucker."""
        IMGSucker.close(self)
        self.send_die_messages()
        # wait for all threads to exit or one to throw an exception
        while True:
            self.signal_main.wait()
            if self.exception_queue.qsize():
                error = self.exception_queue.get()
                self.kill_suckers()
                raise error
            else:
                break  # all threads are dead, exit


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


# NOTE(mattv): The following is a patch that allows one to print out the headers
# that are being sent.
def putheader(self, http, header, value, log_headers):
  if log_headers:
    print "Putting Header -- %s: %s" % (header, value)
  http.putheader(header, value)

# WebFetcher fetch
def WF_fetch(self, url, postdata=None, server=None, port=None, protocol=None,
             ok_codes=None, log_headers=False, strict_cookies=True):
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
        h = httplib.HTTPS(server, int(port))
        if int(port) == 443:
            host_header = server
        else:
            host_header = '%s:%s' % (server, port)
    else:
        raise ValueError, protocol

    params = None
    if postdata:
        if webproxy:
            h.putrequest('POST', "http://%s%s" % (host_header, url))
        else:
            # Normal post
            h.putrequest('POST', url)
        is_multipart = False

        # NOTE(mattv): The following "try" was not originally part of the
        # FunkLoad package.  I put this in here because this would fail when
        # you tried to post XML, rather than <key, value> pairs.  Now, when it
        # fails to find a <key, value> pair, it will set the params to
        # params_in automatically.

        try:
            for field, value in postdata:
                if isinstance(value, Upload):
                    # Post with a data file requires multipart mimeencode
                   is_multipart = True
            if is_multipart:
                params = mimeEncode(postdata)
                putheader(self, h,'.Content-type',
                            'multipart/form-data; boundary=%s' % BOUNDARY,
                            log_headers)
            else:
                params = urlencode(postdata)
                putheader(self, h,'Content-type',
                            'application/x-www-form-urlencoded',
                            log_headers)
        except:
            params = str(postdata)
        putheader(self, h, 'Content-length', str(len(params)), log_headers)
    else:
        if webproxy:
            h.putrequest('GET', "http://%s%s" % (host_header, url))
        else:
            # Normal GET
            h.putrequest('GET', url)

    # Other Full Request headers
    if self.authinfo:
        putheader(self, h, 'Authorization', "Basic %s"%self.authinfo,
            log_headers)
    if not webproxy:
        # HTTPConnection seems to add a host header itself.
        # So we only need to do this if we are not using a proxy.
        putheader(self, h, 'Host', host_header, log_headers)

    # FL Patch -------------------------
    for key, value in self.extra_headers:
        putheader(self, h, key, value, log_headers)

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
                if sendcookie.coded_value == '"deleted"':
                    continue
                # TODO: check max-age
                cookie_list.append("%s=%s;"%(sendcookie.key,
                                             sendcookie.coded_value))
                cookies_used.append(sendcookie.key)

    if cookie_list:
        putheader(self, h, 'Cookie', ' '.join(cookie_list), log_headers)

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
    if webproxy:
        r = h.getresponse()
        errcode = r.status
        errmsg = r.reason
        headers = r.msg
        data = r.read()
        response = HTTPResponse(self.cookies, protocol, server, port, url,
                                errcode, errmsg, headers, data,
                                self.error_content)

    else:
        # get the body and save it
        errcode, errmsg, headers = h.getreply()
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
            decodeCookies(url, server, headers, self.cookies,
                          strict_cookies=strict_cookies)
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
