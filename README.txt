Introduction
==============

FunkLoad_ is a functional and load web tester, written in Python, whose
main use cases are:

* Functional testing of web projects, and thus regression testing as well.

* Performance testing: by loading the web application and monitoring
  your servers it helps you to pinpoint bottlenecks, giving a detailed
  report of performance measurement.

* Load testing tool to expose bugs that do not surface in cursory testing,
  like volume testing or longevity testing.

* Stress testing tool to overwhelm the web application resources and test
  the application recoverability.

* Writing web agents by scripting any web repetitive task.

Features
---------

Main FunkLoad_ features are:

* Functional test are pure Python scripts using the pyUnit_ framework
  like normal unit test. Python enable complex scenarios to handle
  real world applications.

* Truly emulates a web browser (single-threaded) using an enhanced
  Richard Jones' webunit_:

  - get/post/put/delete support
  - post any kind of content type like ``application/xml``
  - DAV support
  - basic authentication support
  - file upload and multipart/form-data submission
  - cookies support
  - referrer support
  - https support
  - https with ssl/tls by providing a private key and certificate (PEM
    formatted)
  - http_proxy support
  - fetching css, javascript and images
  - emulating a browser cache

* Advanced test runner with many command-line options:

  - set the target server url
  - display the fetched page in real time in your browser
  - debug mode to display http headers
  - check performance of a single page (or set of pages) inside a test
  - green/red color mode
  - select or exclude tests cases using a regex
  - support normal pyUnit_ test
  - support doctest_ from a plain text file or embedded in python
    docstring

* Turn a functional test into a load test: just by invoking the bench
  runner you can identify scalability and performance problems. If
  needed the bench can distributed over a group of worker machines.

* Detailed bench reports in ReST, HTML, Org-mode_, PDF (using
  LaTeX/PDF Org-mode export) containing:

  - the bench configuration
  - tests, pages, requests stats and charts
  - the requets that took the most time
  - monitoring one or many servers cpu usage, load average,
    memory/swap usage and network traffic charts
  - an http error summary list

* Differential reports to compare 2 bench reports giving a quick
  overview of scalability and velocity changes.

* Trend reports to view the performance evolution with multiple
  reports.

* Easy test customization using a configuration file or command line
  options.

* Easy test creation using embeded TCPWatch_ as proxy recorder, so you
  can use your web browser and produce a FunkLoad_ test automatically,
  including file upload or any ajax call.

* Provides web assertion helpers to check expected results in responses.

* Provides helpers to retrieve contents in responses page using DOM.

* Easy to install (EasyInstall_).

* Comes with examples look at the demo_ folder.

* Successfully tested with dozen of differents web servers: PHP,
  python, Java...

License
----------

FunkLoad_ is free software distributed under the `GNU GPL`_ license.

\(C) Copyright 2005-2011 Nuxeo SAS (http://nuxeo.com).

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.


.. _FunkLoad: http://funkload.nuxeo.org/
.. _Org-mode: http://orgmode.org/
.. _TCPWatch: http://hathawaymix.org/Software/TCPWatch/
.. _webunit: http://mechanicalcat.net/tech/webunit/
.. _pyUnit: http://pyunit.sourceforge.net/
.. _API: api/index.html
.. _Nuxeo: http://www.nuxeo.com/
.. _`python cheese shop`: http://www.python.org/pypi/funkload/
.. _EasyInstall: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _`GNU GPL`: http://www.gnu.org/licenses/licenses.html#GPL
.. _doctest: http://docs.python.org/lib/module-doctest.html
.. _demo: https://github.com/nuxeo/FunkLoad/tree/master/src/funkload/demo/

.. Local Variables:
.. mode: rst
.. End:
.. vim: set filetype=rst:
