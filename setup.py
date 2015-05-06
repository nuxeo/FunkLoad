#! /usr/bin/env python
# (C) Copyright 2005-2011 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Tom Lazar, Ross Patterson
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

"""
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
__version__ = '1.17.1'

setup(
    name="funkload",
    version=__version__,
    description="Functional and load web tester.",
    long_description=''.join(open('README.txt').readlines()),
    author="Benoit Delbosc",
    author_email="bdelbosc@nuxeo.com",
    url="http://funkload.nuxeo.org/",
    download_url="http://pypi.python.org/packages/source/f/funkload/funkload-%s.tar.gz" % __version__,
    license='GPL',
    keywords='testing benching load performance functional monitoring',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    scripts=['scripts/fl-monitor-ctl', 'scripts/fl-credential-ctl',
             'scripts/fl-run-bench', 'scripts/fl-run-test',
             'scripts/fl-build-report',
             'scripts/fl-install-demo',
             'scripts/fl-record'],
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
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Benchmark',
        'Topic :: System :: Monitoring',
    ],
    # setuptools specific keywords
    install_requires = ['webunit  >= 1.3.8',
                        'docutils >= 0.3.7',
                        'setuptools'],
    zip_safe=True,
    package_data={'funkload': ['data/*',
                               'demo/simple/*', 'demo/zope/*',
                               'demo/cmf/*', 'demo/xmlrpc/*', 'demo/cps/*',
                               'demo/seam-booking-1.1.5/*', 'demo/*.txt',
                               'tests/*', ]},
    entry_points = {
        'console_scripts': [
            'fl-monitor-ctl = funkload.Monitor:main',
            'fl-credential-ctl = funkload.CredentialFile:main',
            'fl-run-bench = funkload.BenchRunner:main',
            'fl-run-test = funkload.TestRunner:main',
            'fl-build-report = funkload.ReportBuilder:main',
            'fl-install-demo = funkload.DemoInstaller:main',
            'fl-record = funkload.Recorder:main'],
        'funkload.plugins.monitor': [
            'CUs = funkload.MonitorPluginsDefault:MonitorCUs',
            'MemFree = funkload.MonitorPluginsDefault:MonitorMemFree',
            'CPU = funkload.MonitorPluginsDefault:MonitorCPU',
            'Network = funkload.MonitorPluginsDefault:MonitorNetwork',
        ]
    },

    # this test suite works only on an installed version :(
    # test_suite = "funkload.tests.test_Install.test_suite",
    )
