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
#
"""Check FunkLoad installation

$Id$
"""
import os
import unittest

class TestInstall(unittest.TestCase):
    """Check installation."""

    def test_01_checkImport(self):
        try:
            import webunit
        except ImportError:
            self.fail('Missing Required module webunit')
        try:
            import funkload
        except ImportError:
            self.fail('Unable to import funkload module.')
        try:
            import docutils
        except ImportError:
            print ("WARNING: missing docutils module, "
                   "no HTML report available.")
        try:
            import gdchart
        except ImportError:
            print ("WARNING: missing gdchart module, "
                   "no charts available in the HTML report.")


    def system(self, cmd):
        """Execute a shell cmd and exit on fail."""
        ret = os.system(cmd)
        if ret != 0:
            self.fail("exec [%s] return code %s" % (cmd, ret))

    def test_xmlrpc(self):
        from tempfile import mkdtemp
        pwd = os.getcwd()
        print ""
        tmp_path = mkdtemp('funkload')
        os.chdir(tmp_path)
        self.system('fl-install-demo')
        os.chdir(os.path.join(tmp_path, 'funkload-demo', 'xmlrpc'))
        self.system("fl-credential-ctl cred.conf restart")
        self.system("fl-monitor-ctl monitor.conf restart")
        self.system("fl-run-test -v test_Credential.py")
        self.system("fl-run-bench -c 1:10:20 -D 4 "
                    "test_Credential.py Credential.test_credential")
        self.system("fl-monitor-ctl monitor.conf stop")
        self.system("fl-credential-ctl cred.conf stop")
        self.system("fl-build-report credential-bench.xml --html")
        os.chdir(pwd)


def test_suite():
    """Return a test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestInstall))
    return suite

if __name__ in ('main', '__main__'):
    unittest.main()
