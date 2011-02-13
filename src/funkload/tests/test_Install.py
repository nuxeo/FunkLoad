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
"""Check an installed FunkLoad.

$Id$
"""
import os
import sys
import unittest
import commands

def winplatform_getstatusoutput(cmd):
    """A replacement for commands.getstatusoutput on the windows platform.
    commands.getstatusoutput only works on unix platforms.
    This only works with python2.6+ as the subprocess module is required.
    os.system provides the return code value but not the output streams of the
    commands.
    os.popen provides the output streams but no reliable easy to get return code.
    """
    try:
        import subprocess
    except ImportError:
        return None

    # create a new handle for the stdout pipe of cmd, and redirect cmd's stderr to stdout
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               shell=True, universal_newlines=True)
    stdoutdata, stderrdata = process.communicate()
    return (process.returncode, stdoutdata)


class TestInstall(unittest.TestCase):
    """Check installation."""

    def setUp(self):
        self.test_file = 'test_dummy.py'
        self.doctest_file = 'doctest_dummy.txt'

    def system(self, cmd, expected_code=0):
        """Execute a cmd and exit on fail return cmd output."""

        if sys.platform.lower().startswith('win'):
            ret = winplatform_getstatusoutput(cmd)
            if not ret:
                self.fail('Cannot run self.system on windows without the subprocess module (python 2.6)')
        else:
            ret = commands.getstatusoutput(cmd)

        if ret[0] != expected_code:
            self.fail("exec [%s] return code %s != %s output:\n%s" %
                      (cmd, ret[0], expected_code, ret[1]))
        return ret[1]

    def test_01_requires(self):
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

        if sys.platform.lower().startswith('win'):
            ret = winplatform_getstatusoutput('wgnuplot --version')
            if not ret:
                self.fail('Cannot run self.system on windows without the subprocess module (python 2.6)')
        else:
            ret = commands.getstatusoutput('gnuplot --version')

        print ret[1]
        if ret[0]:
            print ("WARNING: gnuplot is missing, no charts available in "
                   "HTML reports.")

        from funkload.TestRunner import g_has_doctest
        if not g_has_doctest:
            print "WARNING: Python 2.4 is required to support doctest"


    def test_testloader(self):
        # check testrunner loader
        test_file = self.test_file
        # listing test
        output = self.system("fl-run-test %s --list" % test_file)
        self.assert_('test_dummy1_1' in output)
        self.assert_('test_dummy2_1' in output)
        self.assert_('test_dummy3_1' in output)

        # list a test suite
        output = self.system("fl-run-test %s test_suite --list" % test_file)
        self.assert_('test_dummy1_1' in output)
        self.assert_('test_dummy2_1' in output)
        self.assert_('test_dummy3_1' not in output)

        # list all test in a test case class
        output = self.system("fl-run-test %s TestDummy1 --list" % test_file)
        self.assert_('test_dummy1_1' in output)
        self.assert_('test_dummy1_2' in output)
        self.assert_('test_dummy2_1' not in output)

        # match regex
        output = self.system("fl-run-test %s --list -e dummy1_1" % test_file)
        self.assert_('test_dummy1_1' in output)
        self.assert_('test_dummy2_1' not in output)

        output = self.system("fl-run-test %s TestDummy1 --list -e dummy1_1" %
                             test_file)
        self.assert_('test_dummy1_1' in output)
        self.assert_('test_dummy2_1' not in output)

        output = self.system("fl-run-test %s --list -e 2$" % test_file)
        self.assert_('test_dummy1_2' in output)
        self.assert_('test_dummy2_2' in output)
        self.assert_('test_dummy1_1' not in output)
        self.assert_('test_dummy2_1' not in output)

        output = self.system("fl-run-test %s --list -e '!2$'" % test_file)
        self.assert_('test_dummy1_1' in output, output)
        self.assert_('test_dummy2_1' in output)
        self.assert_('test_dummy1_2' not in output)
        self.assert_('test_dummy2_2' not in output)


    def test_doctestloader(self):
        # check testrunner loader
        from funkload.TestRunner import g_has_doctest
        if not g_has_doctest:
            self.fail('Python 2.4 is required to support doctest')

        test_file = self.test_file
        # listing test
        output = self.system("fl-run-test %s --doctest --list" % test_file)
        self.assert_('Dummy.double' in output, 'missing doctest')

        # list a test suite
        output = self.system("fl-run-test %s  --doctest test_suite --list" % test_file)
        self.assert_('Dummy.double' not in output,
                     'doctest is not part of the suite')

        # list all test in a test case class
        output = self.system("fl-run-test %s --doctest TestDummy1 --list" % test_file)
        self.assert_('Dummy.double' not in output,
                     'doctest is not part of the testcase')

        # pure doctest
        doctest_file = self.doctest_file
        output = self.system("fl-run-test %s --doctest --list" % doctest_file)
        self.assert_(doctest_file.replace('.', '_') in output,
                     'no %s in output %s' % (doctest_file, output))

        # match regex
        output = self.system("fl-run-test %s --doctest --list -e dummy1_1" % test_file)


    def test_testrunner(self):
        # try to launch a test
        test_file = self.test_file
        output = self.system('fl-run-test %s TestDummy1 -v' % test_file)
        self.assert_('Ran 0 tests' not in output,
                     'not expected output:"""%s"""' % output)

        output = self.system('fl-run-test %s TestDummy2 -v' % test_file)
        self.assert_('Ran 0 tests' not in output,
                     'not expected output:"""%s"""' % output)
        # doctest
        from funkload.TestRunner import g_has_doctest
        if g_has_doctest:
            output = self.system('fl-run-test %s --doctest -e double -v' % test_file)
            self.assert_('Ran 0 tests' not in output,
                         'not expected output:"""%s"""' % output)

        # failing test
        output = self.system('fl-run-test %s TestDummy3 -v' % test_file,
                             expected_code=256)
        self.assert_('Ran 0 tests' not in output,
                     'not expected output:"""%s"""' % output)
        self.assert_('FAILED' in output)
        self.assert_('ERROR' in output)


    def test_xmlrpc(self):
        # windows os does not support the monitor server
        if not sys.platform.lower().startswith('win'):
            # extract demo example and run the xmlrpc test
            from tempfile import mkdtemp
            pwd = os.getcwd()
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
