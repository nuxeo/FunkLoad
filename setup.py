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
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
#from distutils.core import setup
from funkload.version import __version__

setup(
    name="funkload",
    version=__version__,
    description="Functional and load web tester.",
    long_description="""\
FunkLoad is a functional and load web tester, written in Python, whose
main use cases are:

* Functional testing of web projects, and thus regression testing as well.

* Performance testing: by loading the web application and monitoring
  your servers it helps you to pinpoint bottlenecks, giving a detailed
  report of performance measurement.

* Load testing tool to expose bugs that do not surface in cursory testing,
  like volume testing or longevity testing.

* Stress testing tool to overwhelm the web application resources and test
  the application recoverability.

* Writing web agents by scripting any web repetitive task, like checking if
  a site is alive.


Main FunkLoad features are:

* FunkLoad is free software distributed under the `GNU GPL`.

* Functional test are pure Python scripts using the pyUnit framework like
  normal unit test. Python enable complex scenarios to handle real world
  applications.

* Truly emulates a web browser (single-threaded) using Richard Jones'
  webunit:

  - basic authentication support
  - cookies support
  - referrer support
  - http proxy support
  - fetching css, javascript and images
  - emulating a browser cache
  - file upload and multipart/form-data submission
  - https support

* Advanced test runner with many command-line options:

  - set the target server url
  - display the fetched page in real time in your browser
  - debug mode
  - green/red color mode
  - select test case using a regex
  - support normal pyUnit test
  - support doctest from a plain text file or embedded in python docstring

* Turn a functional test into a load test: just by invoking the bench runner
  you can identify scalability and performance problems.

* Detailed bench reports in ReST or HTML (and PDF via ps2pdf)
  containing:

  - the bench configuration
  - tests, pages, requests stats and charts with percentiles.
  - the 5 slowest requests.
  - servers cpu usage, load average, memory/swap usage and network traffic
    charts.
  - an http error summary list

* Easy test customization using a configuration file or command line options.

* Easy test creation using TCPWatch as proxy recorder, so you can use your web
  browser and produce a FunkLoad test automatically.

* Provides web assertion helpers.

* Provides a funkload.CPSTestCase to ease Zope and Nuxeo CPS testing.

* Easy to install (EasyInstall) and use, see examples in the demo folder.
""",
    author="Benoit Delbosc",
    author_email="bdelbosc@nuxeo.com",
    url="http://funkload.nuxeo.org/",
    download_url="http://funkload.nuxeo.org/funkload-%s.tar.gz"%__version__,
    license='GPL',
    keywords='testing benching load performance functional monitoring',
    packages= ['funkload'],
    package_dir={'funkload': 'funkload'},
    scripts=['scripts/fl-monitor-ctl', 'scripts/fl-credential-ctl',
             'scripts/fl-run-bench', 'scripts/fl-run-test',
             'scripts/fl-build-report',
             'scripts/fl-import-from-tm-recorder',
             'scripts/fl-install-demo',
             'scripts/fl-record'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Benchmark',
        'Topic :: System :: Monitoring',
    ],
    # setuptools specific keywords
    install_requires = ['webunit  == 1.3.8',
                        'docutils >= 0.3.7'],
    zip_safe=True,
    package_data={'funkload': ['data/*',
                               'demo/simple/*', 'demo/zope/*',
                               'demo/cmf/*', 'demo/xmlrpc/*',
                               'demo/*.txt',
                               'tests/*',]},
    # this test suite works only on an installed version :(
    # test_suite = "funkload.tests.test_Install.test_suite",
    )
