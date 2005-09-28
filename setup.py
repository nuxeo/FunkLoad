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

from src.version import __version__

setup(
    name="funkload",
    version=__version__,
    description="Functional and load web tester.",
    long_description="""\
FunkLoad is a functional and load web tester, main use cases are:

* Functional testing of web projects and thus regression testing.

* Performance testing tool by loading the web application and monitoring
  your servers it helps you to pinpoint bottlenecks, giving a detail
  report of performance measurement.

* Load testing tool to expose bugs that do not surface in cursory testing,
  like volume testing or longevity testing.

* Stress testing tool to overwhelming the web application resources and test
  the application recoverability.

* Writing web agents by scripting any web repetitive task, like checking if
  a site is alive.


Main FunkLoad features are:

* Functional test are pure python script using the pyUnit framework like
  normal unit test, python enable complex scenarios to handle real world
  app.

* Truly emulate a web browser (single-threaded) using Richard Jones'
  webunit:

  - basic authentication support
  - cookies support
  - fetching css, javascript and images
  - emulate a browser cache
  - file upload and multipart/form-data submission
  - https support

* Advanced test runner with many command line options:

  - set the target server url
  - display the fetched page in real time in your browser
  - debug mode
  - green/red color mode

* Turn a functional test into a load test, just by invoking the bench runner
  you can identify scalability and performance problems.

* Detail bench report in ReST or HTML (PDF via ps2pdf) containing:

  - bench configuration
  - tests, pages, requests stats and charts.
  - 5 slowest requests
  - servers cpu usage, load average, memory/swap usage and network traffic
    charts.
  - http error summary list

* Easy test customization using configuration file or command line options.

* Easy test creation using TestMaker / maxq recorder, you can use your web
  browser and produce a FunkLoad test automatically.

* Provide web assertion helpers.

* Provide a funkload.CPSTestCase to ease Zope and Nuxeo CPS testing.

* Easy to use, see examples in the demo folder.
""",
    author="Benoit Delbosc",
    author_email="bdelbosc@nuxeo.com",
    url="http://public.dev.nuxeo.com/~ben/funkload/",
    download_url="http://public.dev.nuxeo.com/~ben/funkload-%s.tar.gz"%__version__,
    license='GPL',
    packages=['funkload'],
    package_dir={'funkload': 'src'},
    data_files=[('funkload', ['data/funkload.css',
                              'data/ScriptTestCase.tpl',
                              'data/ConfigurationTestCase.tpl'])],
    scripts=['scripts/fl-monitor-ctl', 'scripts/fl-credential-ctl',
             'scripts/fl-run-bench', 'scripts/fl-run-test',
             'scripts/fl-build-report',
             'scripts/fl-import-from-tm-recorder'],
    classifiers=[
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
