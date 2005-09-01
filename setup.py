#! /usr/bin/env python
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
"""FunkLoad package setup

$Id: setup.py 24768 2005-08-31 14:01:05Z bdelbosc $
"""
from distutils.core import setup

from src.FunkLoadTestCase import __version__

setup(
    name = "funkload",
    version = __version__,
    description = "Functional and load web tester.",
    long_description = """FunkLoad is a functional and load web tester.

Main FunkLoad features are:

* Compatible with pyUnit framework, just use funkload.FunkLoadTestCase
  instead of unittest.TestCase.

* Truly emulate a web browser (single-threaded) using Richard Jones' webunit:

  - basic auth support
  - cookies support
  - fetching css, javascript and images
  - emulate a browser cache
  - file upload and multipart/form-data submission
  - https support

* Advanced test runner with many command line options:

  - color mode
  - display the page fetched in real time in your browser
  - debug mode

* Turn a functional test into a load test, just by invoking the bench runner
  you can identify scalability and performance problems.

* Detail bench report in ReST or html containing:

  - bench configuration
  - tests, pages, requests stats and charts.
  - servers cpu usage, load average, memory/swap usage and network traffic
    charts.

* Easy test customization using configuration file or command line.

* Easy test creation using TestMaker recorder, you can use your web browser
  and produce a FunkLoad test automatically.

* Web assertion helpers.

* Provide a funkload.CPSTestCase class to ease nuxeo CPS testing.
""",
    author = "Benoit Delbosc",
    author_email = "bdelbosc@nuxeo.com",
    url = "http://public.dev.nuxeo.com/~ben/funkload/",
    download_url = "http://public.dev.nuxeo.com/~ben/funkload-%s.tar.gz"
    %__version__,
    license='GPL',
    packages = ['funkload'],
    package_dir = {'funkload': 'src'},
    data_files = [('funkload', ['data/funkload.css',
                                'data/ScriptTestCase.tpl',
                                'data/ConfigurationTestCase.tpl'])],
    scripts = ['scripts/fl-monitor-ctl', 'scripts/fl-credential-ctl',
               'scripts/fl-run-bench', 'scripts/fl-run-test',
               'scripts/fl-build-report',
               'scripts/fl-import-from-tm-recorder'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Software Development :: Testing',
        'Topic :: System :: Monitoring',
    ],
)
