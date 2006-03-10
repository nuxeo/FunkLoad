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
"""Parse HTML to extract resources links.

$Id$
"""
from formatter import NullFormatter
from urlparse import urljoin
from htmllib import HTMLParser


class HTMLResourceParser(HTMLParser):
    """Extract img, link, script and base_url ref from an HTML page."""

    def __init__(self, url):
        HTMLParser.__init__(self, NullFormatter())
        self.base = url
        self.links = []

    def do_base(self, attributes):
        """Handles base tag."""
        for name, value in attributes:
            if name == 'href':
                self.base = value

    def do_img(self, attributes):
        """Handles img tag."""
        for name, value in attributes:
            if name == 'src':
                self.links.append(urljoin(self.base, value))

    def do_link(self, attributes):
        """Handles link tag."""
        for name, value in attributes:
            if name == 'href':
                self.links.append(urljoin(self.base, value))

    def do_script(self, attributes):
        """Handles script tag."""
        for name, value in attributes:
            if name == 'src':
                self.links.append(urljoin(self.base, value))
