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
"""Check an htmlresourceparser

$Id$
"""
import sys
import unittest
sys.path.append('./..')
from htmlresourceparser import HTMLResourceParser

class TestHTMLResourceParser(unittest.TestCase):
    """Check the html parser."""

    def test_img(self):
        parser = HTMLResourceParser('http://localhost')
        page = ('<html><a href="foo">bar</a>'
                '<img src="fooimg.png" />'
                '<img src=http://foo.bar/fooimg.png>'
                '<img src="bar.png" <a href=""></a>'
                '<img invalid>'
                '</html>')
        parser.feed(page)
        parser.close()
        links = parser.links
        self.assert_('http://localhost/fooimg.png' in links, links)
        self.assert_('http://foo.bar/fooimg.png' in links, links)
        self.assert_('http://localhost/bar.png' in links, links)
        self.assertEquals(len(links), 3)

    def test_base(self):
        base = 'http://127.0.0.1/'
        parser = HTMLResourceParser('http://localhost')
        page = '<html><base href="%s"><img src=foo.png></html>' % base
        parser.feed(page)
        parser.close()
        links = parser.links
        self.assertEquals(parser.base, base)
        self.assert_('%sfoo.png' % base in links)

    def test_css(self):
        parser = HTMLResourceParser('http://localhost')
        page = ('<html><head>'
                '<link rel="stylesheet" type="text/css" media="all"'
                ' title="foo" href="foo.css" /> '
                '</head></html>')
        parser.feed(page)
        parser.close()
        links = parser.links
        self.assert_('http://localhost/foo.css' in links, links)

    def failed_test_css(self):
        # @import is not hanlde by the parser
        parser = HTMLResourceParser('http://localhost')
        page = ('<html><head>'
                '<style type="text/css" media="all">'
                '  @import url(/bar.css);</style>'
                '</head></html>')
        parser.feed(page)
        parser.close()
        links = parser.links
        self.assert_('http://localhost/bar.css' in links, links)

    def test_script(self):
        parser = HTMLResourceParser('http://localhost')
        page = ('<html'
                '<script type="text/javascript" src="/foo.js"></script>'
                '</html>')
        parser.feed(page)
        parser.close()
        links = parser.links
        self.assert_('http://localhost/foo.js' in links, links)
        self.assertEquals(len(links), 1)


def test_suite():
    """Return a test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestHTMLResourceParser))
    return suite

if __name__ in ('main', '__main__'):
    unittest.main()
