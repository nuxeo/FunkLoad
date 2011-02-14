Introduction
==============

This is the documentation for the FunkLoad tool. 

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

Features
---------

Main FunkLoad_ features are:

* FunkLoad_ is free software distributed under the `GNU GPL`_ license.

* Functional test are pure Python scripts using the pyUnit_ framework like
  normal unit test. Python enable complex scenarios to handle real world
  applications.

* Truly emulates a web browser (single-threaded) using an enhanced Richard
  Jones' webunit_:

  - get/post/put/delete support
  - post any kind of content type like ``application/xml``
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
  - support doctest_ from a plain text file or embedded in python docstring

* Turn a functional test into a load test: just by invoking the bench
  runner you can identify scalability and performance problems. If
  needed the bench can distributed over a group of worker machines.

* Detailed bench reports in ReST or HTML (and PDF via ps2pdf)
  containing:

  - the bench configuration
  - tests, pages, requests stats and charts.
  - the requets that took the most time.
  - monitoring one or many servers cpu usage, load average, memory/swap
    usage and network traffic charts.
  - an http error summary list

* Differential reports to compare 2 bench reports giving a quick overview of
  scalability and velocity changes.

* Easy test customization using a configuration file or command line options.

* Easy test creation using embeded TCPWatch_ as proxy recorder, so you can
  use your web browser and produce a FunkLoad_ test automatically, including
  file upload or any ajax call.

* Provides web assertion helpers to check expected results in responses.

* Provides helpers to retrieve contents in responses page using DOM.

* Easy to install (EasyInstall_).

* Comes with examples look at the demo_ folder.

* Successfully tested with dozen of differents web servers: PHP,
  python, Java...


.. _FunkLoad: http://funkload.nuxeo.org/
.. _TCPWatch: http://hathawaymix.org/Software/TCPWatch/
.. _webunit: http://mechanicalcat.net/tech/webunit/
.. _pyUnit: http://pyunit.sourceforge.net/
.. _INSTALL: INSTALL.html
.. _CHANGES: CHANGES.html
.. _TODO: TODO.txt
.. _contributors: http://svn.nuxeo.org/trac/pub/browser/funkload/trunk/THANKS
.. _API: api/index.html
.. _Slides: http://blogs.nuxeo.com/sections/blogs/fermigier/2005_11_17_slides-introducing
.. _epydoc: http://epydoc.sourceforge.net/
.. _Zope: http://www.zope.org/
.. _Cmf: http://www.zope.org/Products/CMF/
.. _Nuxeo: http://www.nuxeo.com/
.. _CPS: http://www.cps-project.org/
.. _`python cheese shop`: http://www.python.org/pypi/funkload/
.. _EasyInstall: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _demo: http://svn.nuxeo.org/trac/pub/browser/funkload/trunk/src/funkload/demo/
.. _report: http://funkload.nuxeo.org/report-example/
.. _`GNU GPL`: http://www.gnu.org/licenses/licenses.html
.. _`svn sources`: http://svn.nuxeo.org/pub/funkload/trunk/#egg=funkload-dev
.. _trac: http://svn.nuxeo.org/trac/pub/report/12
.. _doctest: http://docs.python.org/lib/module-doctest.html


.. Local Variables:
.. mode: rst
.. End:
.. vim: set filetype=rst:
