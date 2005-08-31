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

import time
from webunit.IMGSucker import IMGSucker
from webunit.webunittest import WebTestCase
from urlparse import urljoin
from utils import thread_sleep

class FKLIMGSucker(IMGSucker):
    def __init__(self, url, session, ftestcase=None):
        IMGSucker.__init__(self, url, session)
        self.ftestcase = ftestcase

    def do_img(self, attributes):
        newattributes = []
        for name, value in attributes:
            if name == 'src':
                url = urljoin(self.base, value)
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
                url = urljoin(self.base, value)
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
