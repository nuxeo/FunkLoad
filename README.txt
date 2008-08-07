=========
FunkLoad_
=========

:author: Benoit Delbosc

:address: bdelbosc _at_ nuxeo.com

:version: FunkLoad/1.6.2

:revision: $Id: README.txt 51461 2007-04-06 08:36:07Z bdelbosc $

:Copyright: (C) Copyright 2005 Nuxeo SAS (http://nuxeo.com).
    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    version 2 as published by the Free Software Foundation.
    This program is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
    Public License for more details.
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


:abstract: This document describes the usage of the FunkLoad_ tool. This tool
    enables to do functional and load testing of web application.


.. sectnum::    :depth: 2

.. contents:: Table of Contents


Introducing FunkLoad
====================

What is FunkLoad ?
------------------

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

* Writing web agents by scripting any web repetitive task, like checking if
  a site is alive.


Main FunkLoad_ features are:

* FunkLoad_ is free software distributed under the `GNU GPL`_.

* Functional test are pure Python scripts using the pyUnit_ framework like
  normal unit test. Python enable complex scenarios to handle real world
  applications.

* Truly emulates a web browser (single-threaded) using Richard Jones'
  webunit_:

  - basic authentication support
  - cookies support
  - referrer support
  - fetching css, javascript and images
  - emulating a browser cache
  - file upload and multipart/form-data submission
  - https support
  - http_proxy support

* Advanced test runner with many command-line options:

  - set the target server url
  - display the fetched page in real time in your browser
  - debug mode
  - check performance of a single page (or set of pages) inside a test
  - green/red color mode
  - select or exclude tests cases using a regex
  - support normal pyUnit_ test
  - support doctest_ from a plain text file or embedded in python docstring

* Turn a functional test into a load test: just by invoking the bench runner
  you can identify scalability and performance problems.

* Detailed bench reports in ReST or HTML (and PDF via ps2pdf)
  containing:

  - the bench configuration
  - tests, pages, requests stats and charts.
  - the 5 slowest requests.
  - servers cpu usage, load average, memory/swap usage and network traffic
    charts.
  - an http error summary list

* Easy test customization using a configuration file or command line options.

* Easy test creation using TCPWatch_ as proxy recorder, so you can use your web
  browser and produce a FunkLoad_ test automatically.

* Provides web assertion helpers.

* Provides a funkload.CPSTestCase to ease Zope_ and Nuxeo_ CPS_ testing.

* Easy to install (EasyInstall_) and use, see examples in the demo_ folder.


Where to find FunkLoad ?
------------------------

Either:

* Latest stable package using EasyInstall_::

   sudo easy_install -U funkload

* EasyInstall_ the latest snapshot ::

   sudo easy_install -f http://funkload.nuxeo.org/snapshots/ funkload

* Bleeding edge `svn sources`_::

   easy_install -eb . funkload==dev
   # or
   svn co http://svn.nuxeo.org/pub/funkload/trunk funkload


See CHANGES_ file for information about distribution contents.


Installation
------------

See the INSTALL_ file for requirement and installation.


Examples
--------

See the demo_ folder contents and a report_ example.

For package installed with easy_install you need to run ``fl-install-demo``
to extract the demo examples.


Documentation
-------------

This page is the main FunkLoad_ documentation, there are also:

* CHANGES_ for information about distribution contents.
* INSTALL_ for requirement and installation.
* API_ documentation generated with epydoc_.
* SLIDES_ introducing FunkLoad_.


Credits
-------

Thanks to Frank Cohen's TestMaker_ framework and Richard Jones webunit_
package.


Test runner
===========

A FunkLoad_ test can be used like a standard unittest using a unittest.main()
and a 'python MyFile.py'.

To ease testing FunkLoad_ come with an advanced test runner to override
the static configuration file.

The ``loop-on-pages`` option enable to check response time of some specific
pages inside a test without changing the script, which make easy to tune a
page in a complex context. Use the ``debug`` option to find the page numbers.

Note that ``fl-run-test`` can be used to launch normal unittest.TestCase and
(if you use python2.4) doctest_ in a plain text file or embedded in a python
docstring. The ``--debug`` option makes doctests verbose.


Usage
-----
::

  fl-run-test [options] file [class.method|class|suite] [...]


Examples
--------
::

  fl-run-test myFile.py
                        Run all tests (including doctest with python2.4).
  fl-run-test myFile.py test_suite
                        Run suite named test_suite.
  fl-run-test myFile.py MyTestCase.testSomething
                        Run a single test MyTestCase.testSomething.
  fl-run-test myFile.py MyTestCase
                        Run all 'test*' test methods in MyTestCase.
  fl-run-test myFile.py MyTestCase -u http://localhost
                        Same against localhost.
  fl-run-test myDocTest.txt
                        Run doctest from plain text file (requires python2.4).
  fl-run-test myDocTest.txt -d
                        Run doctest with debug output (requires python2.4).
  fl-run-test myfile.py -V
                        Run default set of tests and view in real time each
                        page fetch with firefox.
  fl-run-test  myfile.py MyTestCase.testSomething -l 3 -n 100
                        Run MyTestCase.testSomething, reload one hundred
                        time the page 3 without concurrency and as fast as
                        possible. Output response time stats. You can loop
                        on many pages using slice -l 2:4.
  fl-run-test myFile.py -e [Ss]ome
                        Run all tests that match the regex [Ss]ome.
  fl-run-test myFile.py -e '!foo$'
                        Run all tests that does not ends with foo.
  fl-run-test myFile.py --list
                        List all the test names.
  fl-run-test -h
                        More options.


Options
-------
::

  --version               show program's version number and exit
  --help, -h              show this help message and exit
  --quiet, -q             Minimal output.
  --verbose, -v           Verbose output.
  --debug, -d             FunkLoad and doctest debug output.
  --debug-level=DEBUG_LEVEL
                          Debug level 2 is more verbose.
  --url=MAIN_URL, -uMAIN_URL
                          Base URL to bench without ending '/'.
  --sleep-time-min=FTEST_SLEEP_TIME_MIN, -mFTEST_SLEEP_TIME_MIN
                          Minumum sleep time between request.
  --sleep-time-max=FTEST_SLEEP_TIME_MAX, -MFTEST_SLEEP_TIME_MAX
                          Maximum sleep time between request.
  --dump-directory=DUMP_DIR
                          Directory to dump html pages.
  --firefox-view, -V      Real time view using firefox, you must have a running
                          instance of firefox in the same host.
  --no-color              Monochrome output.
  --loop-on-pages=LOOP_STEPS, -lLOOP_STEPS
                          Loop as fast as possible without concurrency on pages
                          expect a page number or a slice like 3:5. Output some
                          statistics.
  --loop-number=LOOP_NUMBER, -nLOOP_NUMBER
                          Number of loop.
  --accept-invalid-links  Do not fail if css/image links are not reachable.
  --simple-fetch          Don't load additional links like css or images when
                          fetching an html page.
  --stop-on-fail          Stop tests on first failure or error.
  --regex=REGEX, -eREGEX  The test names must match the regex.
  --list                  Just list the test names.




Benching
========

The same FunkLaod test can be turned into a load test, just by invoking the
bench runner ``fl-run-bench``.

Principle
---------

Here are some definitions used in bench mode:

* CUs: Concurrent Users, which is the number of threads.
* STPS: Average of Successful Tests Per Second during a cycle.
* SPPS: Average of Successfully Page Per Second during a cycle.
* RPS: Average Request Per Second, successfully or not.
* max[STPS|SPPS|RPS]: maximum of STPS|SPPS|RPS for a cycle.

Page
~~~~

A page is an http get/post request with associated sub requests like
redirects, images or links (css, js files). This is what users see as a
single page.


Test
~~~~

A test is made with 3 methods: setUp/test_name/tearDown. During the test_name
method each get/post request is called a page.

::

  [setUp][page 1]    [page 2] ... [page n]   [tearDown]
  ======================================================> time
         <----------------------------------> test method
                 <--> sleeptime_min to sleeptime_max
         <-----> page 1 connection time

Cycle
~~~~~

A cycle is a load of n concurrents test during a 'duration' period.
Threads are launched every 'startupdelay' seconds, each thread executes
test in a loop.

Once all threads have been started we start to record stats.

Only tests that end during the 'duration' period are taken into account
for the test stats (in the representation below test like [---X are not
take into account).

Only pages and requests that finish during the 'duration' are taken into
account for the request and pages statistic

Before a cycle a setUpCycle method is called, after a cycle a tearDownCycle
method is called, you can use these methods to test differents server
configuration for each cycle.

::

  Threads
  ^
  |
  |
  |n                   [---test--]   [--------]   [--|---X
  |...
  |                    |                             |
  |2            [------|--]   [--------]   [-------] |
  |                    |                             |
  |1          [------X | [--------]   [-------]   [--|--X
  |                    |                             |
  |[setUpCycle]        |                             |    [tearDownCycle]
  ===========================================================> time
                       <------ cycle duration ------->
   <----- staging ----->                             <---- staging ----->
              <-> startupdelay    <---> sleeptime


Cycles
~~~~~~

FunkLoad_ can execute many cycles with different number of CUs, this way you
can find easily the maximum number of users that your application can
handle.

Running n cycles with the same CUs is a good way to see how the application
handles a writing test over time.

Running n cycles with the same CUs with a reading test and a setUpCycle that
change the application configuration will help you to find the right tuning.


::

  cvus = [n1, n2, ...]

  Threads
  ^
  |
  |
  |n2                            __________
  |                             /          \
  |                            /            \
  |n1   _________             /              \
  |    /         \           /                \
  |   /           \         /                  \
  |  /             \       /                    \
   ==================================================> time
        <------->   duration     <-------->
                    <-----> cycle sleep time



Bench runner
------------

Usage
~~~~~
::

  fl-run-bench [options] file class.method


Examples
~~~~~~~~
::

  fl-run-bench myFile.py MyTestCase.testSomething
                        Bench MyTestCase.testSomething using MyTestCase.conf.
  fl-run-bench -u http://localhost:8080 -c 10:20 -d 30 myFile.py MyTestCase.testSomething
                        Bench MyTestCase.testSomething on localhost:8080
                        with 2 cycles of 10 and 20 users during 30s.
  fl-run-bench -h
                        More options.

Options
~~~~~~~
::

  --version               show program's version number and exit
  --help, -h              show this help message and exit
  --url=MAIN_URL, -uMAIN_URL
                          Base URL to bench.
  --cycles=BENCH_CYCLES, -cBENCH_CYCLES
                          Cycles to bench, this is a list of number of virtual
                          concurrent users, to run a bench with 3 cycles with 5,
                          10 and 20 users use: -c 2:10:20
  --duration=BENCH_DURATION, -DBENCH_DURATION
                          Duration of a cycle in seconds.
  --sleep-time-min=BENCH_SLEEP_TIME_MIN, -mBENCH_SLEEP_TIME_MIN
                          Minimum sleep time between request.
  --sleep-time-max=BENCH_SLEEP_TIME_MAX, -MBENCH_SLEEP_TIME_MAX
                          Maximum sleep time between request.
  --startup-delay=BENCH_STARTUP_DELAY, -sBENCH_STARTUP_DELAY
                          Startup delay between thread.
  --no-color              Monochrome output.
  --accept-invalid-links  Do not fail if css/image links are not reachable.
  --simple-fetch          Don't load additional links like css or images when
                          fetching an html page.


Tips
----

Here are few remarks/advices to obtain workable metrics.

* Since it uses significant CPU resources, make sure that performance limits
  are not hit by FunkLoad_ before your server's limit is reached.
  Check this by launching a bench from another host.

* Having a cycle with one user gives a usefull reference.

* A bench is composed of a benching test (or scenario) run many times. A good
  benching test should not be too long so you have a higher testing rate (that
  is, more benching tests can come to their end).

* The cycle duration for the benching test should be long enough.
  Around 5 times the duration of a single benching test is a value that is
  usually a safe bet. You can obtain this duration of a single benching test by
  running ``fl-run-test myfile.py MyTestCase.testSomething``.

  Rationale : Normally a cycle duration of a single benching test should be
  enough. But from the testing platform side if there are more than one
  concurrent user, there are many threads to start and it takes some time. And on
  from the tested platform side it is common that a benching test will last
  longer and longer as the server is used by more and more users.

* You should use many cycles with the same step interval to produce readable
  charts (1:10:20:30:40:50:60 vs 1:10:100)

* A benching test must have the same number of page and in the same
  order.

* Use a Makefile to make reproductible bench.

* There is no debug option while doing a bench (since this would be illegible
  with all the threads). So, if a bench fails (that is using `fl-run-bench`),
  use ``fl-run-test -d`` to debug.

* Using `fl-record` is very easy and very fast to create a scenario. But since
  it doesn't support HTTPS, the good practise is to first record a scenario
  with `fl-record` on HTTP, and then change the `url` back to `https` in your
  FunkLoad test configuration file.

* Always use description in post/get/xmlrpc, this improves the
  readability of the report.


Bench report
============

To produce an HTML or ReST report you need to invoke the ``fl-build-report``,
you can easily produce PDF report using Firefox 'Print To File' in
PostScript then use the ps2pdf converter.

Usage
-----
::

  fl-build-report [options] xmlfile

``fl-build-report`` analyze a FunkLoad_ bench xml result file and output a
report.


Examples
--------
::

  fl-build-report funkload.xml
                        ReST rendering into stdout.
  fl-build-report --html -o /tmp funkload.xml
                        Build an HTML report in /tmp.
  fl-build-report -h
                        More options.

Options
-------
::

    --version               show program's version number and exit
    --help, -h              show this help message and exit
    --html, -H              Produce an html report.
    --output-directory=OUTPUT_DIR, -oOUTPUT_DIR
                            Directory to store reports.


 Note that you can preview the report for cycles that have been done while
 the bench is still running by invoking the above command.



Test Recorder
=============


Recording a new FunkLoad test
-----------------------------

Starting with FunkLoad_ 1.3.0 you can use ``fl-record`` to record your
navigator activity, this requires the TCPWatch_ python proxy see INSTALL_
for information on how to install TCPWatch_.

1. Start the recorder::

    fl-record basic_navigation


  This will output something like this::

    Hit Ctrl-C to stop recording.
    HTTP proxy listening on :8090
    Recording to directory /tmp/tmpaYDky9_funkload.


2. Setup your browser proxy and play your scenario

  * in Firefox: Edit > Preferencies > General; Connection Settings set
    `localhost:8090` as your HTTP proxy

  * Play your scenario using your navigator

  * Hit Ctrl-C to stop recording::

      ^C
      # Saving uploaded file: foo.png
      # Saving uploaded file: bar.pdf
      Creating script: ./test_BasicNavigation.py.
      Creating configuration file: ./BasicNavigation.conf.


3. Replay you scenario::

     fl-run-test -dV test_BasicNavigation.py

  You should see all the steps on your navigator.

4. Implement the dynamic part and assertion

  * Code the dynamic part like getting new url of a created document
  * Add assertion using FunkLoad_ helpers
  * Use a credential server if you want to make a bench with different users
    or simply don't want to hard code your login/password.


Note that ``fl-record`` works fine with multi-part encoded form and file upload
but will failed to record https session.


The fl-record command
---------------------

Usage
~~~~~
::

    fl-record [options] [test_name]

  fl-record launch a TCPWatch_ proxy and record activities, then output
  a FunkLoad script or generates a FunkLoad unit test if test_name is specified.
  The default proxy port is 8090.

  Note that tcpwatch.py executable must be accessible from your env.


Examples
~~~~~~~~
::

  fl-record foo_bar
                        Run a proxy and create a FunkLoad test case,
                        generates test_FooBar.py and FooBar.conf file.
                        To test it:  fl-run-test -dV test_FooBar.py
  fl-record -p 9090
                        Run a proxy on port 9090, output script to stdout.
  fl-record -i /tmp/tcpwatch
                        Convert a tcpwatch capture into a script.

Options
~~~~~~~
::

  --version               show program's version number and exit
  --help, -h              show this help message and exit
  --verbose, -v           Verbose output
  --port=PORT, -pPORT     The proxy port.
  --tcp-watch-input=TCPWATCH_PATH, -iTCPWATCH_PATH
                          Path to an existing tcpwatch capture.


Credential server
=================

If you are writing a bench that requires to be logged with different users
FunkLoad_ provides an xmlrpc credential server to serve login/pwd between the
different threads.

It requires 2 files (like unix /etc/passwd and /etc/group) the password file
have the following format::

  login1:pwd1
  ...

The group file format is::

  group1:user1, user2
  group2:user2
  # you can split group declaration
  group1:user3
  ...

Setup a configuration file like in the demo_/cmf folder, then start the
credential server::

  fl-credential-ctl credential.conf start

More options::

  fl-credential-ctl --help

See the funkload-demo/cmf example for a credential configuration file.


Monitor server
==============

If you want to monitor a linux server health during the bench, you have to
run a monitor xmlrpc server on the target server, this require to install
the FunkLoad_ package.

On the server side you need to install the FunkLoad_ tool then launch the
server using a configuration file (example in the demo_/simple folder.)::

  fl-monitor-ctl monitor.conf start

  # more info
  fl-monitor-ctl --help


On the bench host side setup your test configuration like this::

  [monitor]
  hosts = server.to.test.com

  [server.to.test.com]
  description = The web server
  port = 8008

Then run the bench, the report will include server stats.

Note that you can monitor multiple hosts and that the monitor is linux
specific.


The FunkLoadTestCase
====================

FunkLoadTestCase extends the pyUnit_ unittest.TestCase with browser
capabilities, configuration file helpers and assertions helpers. FunkLoad_
provides also some tools to generate random inputs and communicate with
credential servers.

Here is an overview of the api, you can find more on

Browser API
-----------

get
~~~
::

  get(url, params=None, description=None, ok_codes=None)

This emulates a browser http GET link. It will fetch the url, submits
appropriate cookies, follow redirection, register new cookies, load css and
javascript.

It also simulates a browser cache by not reloading a css, a javascript or an
image twice.

Note that this is an emulation with some limitation:

* It is single threaded (it loads images one after the other)
* It does not interpret javascript
* See trac_ tickets that starts with `Browser:` for other limitations

This method returns a webunit_ HTTPResponse.


Parameters:

- *url* the url without parameters
- *params* a dico of parameters that going to be append to the url like
  `url?key1=value1&...`
- *description* is used on the bench report to describe the user action
- *ok_codes* is a list of http expected code like [200:301] if the http
  response is not in the list `get` will raise a test failure exception,
  if not provided assume that the default list is [200, 301, 302].

post
~~~~
::

  post(url, params=None, description=None, ok_codes=None)


Same interface than the get() but it uses a http post method.
You can upload a file by setting a params like this::

  from webunit.utility import Upload
  params['file_up'] = Upload('/tmp/foo.txt')


exists
~~~~~~
::

  exists(url, params=None, description="Checking existence")


Return True if the http response code is 200, 301 or 302, and return False if
http code is 404 or 503, other codes will raise a test failure exception.


setBasicAuth
~~~~~~~~~~~~
::

  setBasicAuth(login, password)

Next requests will use the http basic authentication.


clearBasicAuth
~~~~~~~~~~~~~~
::

  clearBasicAuth()

Remove basic auth credential set by setBasicAuth.


setUserAgent
~~~~~~~~~~~~
::

  setUserAgent(agent)

New in 1.3.0. version.

Set a ``User-Agent`` http header for the next requests, the default browser
behaviour is to use the agent defined in the configuration file under
``[main] user_agent`` or to use the default ``FunkLoad/version``
string. Using this method enable to change the user agent during a test
case.


addHeader
~~~~~~~~~
::

  addHeader(key, value)

New in 1.3.0. version.

Add an http header for the next requests.


clearHeaders
~~~~~~~~~~~~
::

  clearHeaders()

New in 1.3.0. version.

Remove all headers previously added by `addHeader`_ or `setUserAgent`_,
and remove the referer as well.


XML RPC API
-----------

You can test or bench xmlrpc services using the following API.

xmlrpc
~~~~~~
::

  xmlrpc(url, method_name, params=None, description=None)

Call the ``method_name`` at ``url`` using xmlrpclib. You can use the
setBasicAuth_ method before to handle the http basic authentication. Note
that due to xmlrpclib limitation you can not use an http proxy.

Parameters:

- *url* the url of the xmlrpc server
- *method_name* the name of the procedure to call
- *params* a list of parameters to pass to the method
- *description* is used on the bench report to describe the action


Assertion helpers API
---------------------

FunkLoad_ uses the unittest assertion (``assert_``, ``assertEquals``,
``fail``, ...), but provides some methods to check the http response.
After fetching a page you can use the following methods.


getLastUrl
~~~~~~~~~~
::

  getLastUrl()

Return the last accessed page url taking care of redirects.


getLastBaseUrl
~~~~~~~~~~~~~~
::

  getLastBaseUrl()

Return the <base /> href value of the last accessed page.


listHref
~~~~~~~~
::

  listHref(pattern=None)

Return a list of href anchor url present in the last html response,
filtering href using the ``pattern`` regex if present.


getBody
~~~~~~~
::

  getBody()

Return the last response content.


The response object
~~~~~~~~~~~~~~~~~~~

The response returned by a get or post are webunit_ HTTPResponse object

::

  response = self.get(url)
  print "http response code %s" % response.code
  print "http header location %s" % response.headers['location']
  self.assert_('HTML' in response.body)

::

  response.getDOM().getByName('h1')

getDOM return a SimpleDOM interface of the fetched html page, see the
webunit_ SimpleDOM api instructions for details.



Configuration file API
----------------------

A FunkLoadTestCase class uses a configuration file to setup variable
configuration, like the base server url to be tested, the test description,
credential access, logging files and other test specific parameters. The test
configuration file have the same name of the FunkLoadTestCase with a '.conf'
extension. See documented examples in the demo_ folder (``fl-install-demo``).

conf_get
~~~~~~~~
::

  conf_get(section, key, default=_marker)

Return an entry from the configuration file. Note that the entry may be
overriden by a command line option.

Parameters:

- *section* the section in the configuration file.
- *key* the key.
- *default* a default value.


conf_getInt
~~~~~~~~~~~

Return an integer.

conf_getFloat
~~~~~~~~~~~~~

Return a float.

conf_getList
~~~~~~~~~~~~

Additional parameter:

- *separator* the default separator is a colon ':'.

Return a list


Logging
-------

A FunkLoadTestCase store its results in an xml file (like request and test
result) and put other log information into a text log and/or output to the
console.

logd
~~~~
::

  logd(message)

Debug log message

logi
~~~~
::

  logi(message)

Information log message


Lipsum API
----------

To generate dummy document contents you can use the funkload.Lipsum api,
this is a very simple "Lorem ipsum" generator.

You can see some examples by doing::

  python -c "from funkload.Lipsum import main; main()"


Lipsum
~~~~~~
::

  from funkload.Lipsum import Lipsum
  lipsum = Lipsum(vocab=V_ASCII, chars=CHARS, sep=SEP)

Parameters:

- *vocab* a list of word, Lipsum provide 3 lists V_ASCII, V_DIAC, V_8859_15
- *chars* the list of char used to build an identifier
- *sep* some separators used in sentences like coma, question mark ...


getWord
~~~~~~~
::

  lipsum.getWord()

Return a random word from the vocabulary.


getUniqWord
~~~~~~~~~~~
::

  lipsum.getUniqWord(length_min=None, length_max=None):

Generate a kind of uniq id.


getSubject
~~~~~~~~~~
::

  lipsum.getSubject(length=5, prefix=None, uniq=False,
                    length_min=None, length_max=None)

Return a subject of length word.

Parameters:

- *length* the number of words in the subject
- *prefix* a prefix to add at the beginning of a the subject
- *uniq* add an uniq identifier in the subject
- *length_min/max* the words length is a random between min and max


getSentence
~~~~~~~~~~~
::

  lipsum.getSentence()

Return a sentence with some separators and and a ending point.


getParagraph
~~~~~~~~~~~~
::

  lipsum.getParagraph(length=4)

Return a paragraph of length sentences.


getMessage
~~~~~~~~~~
::

  lipsum.getMessage(length=7)

Return a message with length Paragraphs.


getPhoneNumber
~~~~~~~~~~~~~~
::

  lipsum.getPhoneNumber(lang="fr", format="medium")

Return a random phone number.

Parameters:

- *lang* can be fr or en_US
- *format* can be short, medium or long


getAddress
~~~~~~~~~~
::

  lipsum.getAddress(lang="fr")

Return a random address.


Utils
-----

To communicate with FunkLoad_ services like the credential server, there are
some wrappers in the utils module.

xmlrpc_get_credential
~~~~~~~~~~~~~~~~~~~~~
::

  from funkload.utils import xmlrpc_get_credential
  xmlrpc_get_credential(credential_host, credential_port, group=None)

Return a tuple login, password of a user that belong to group if specified.

xmlrpc_list_groups
~~~~~~~~~~~~~~~~~~

List groups name served by the credential server.

xmlrpc_list_credentials
~~~~~~~~~~~~~~~~~~~~~~~

List all login/password served by the credential server.

FunkLoadDocTest
===============

Since FunkLoad_ 1.5 you can use funkload easily from a doctest_::

    >>> from funkload.FunkLoadDocTest import FunkLoadDocTest
    >>> fl = FunkLoadDocTest()
    >>> response = fl.get('http://localhost/')
    >>> 'HTML' in response.body
    True
    >>> response
    <response url="http://127.0.0.1:80/" code="200" message="OK" />

FunkLoadDocTest_ exposes the same API than `The FunkLoadTestCase`_.

Other Test Cases
================

The ZopeTestCase
----------------

This class extends the FunkLoadTestCase providing common Zope_ tasks.

zopeRestart
~~~~~~~~~~~
::

  zopeRestart(zope_url, admin_id, admin_pwd, time_out=600)

Stop and Start the Zope_ server.

Parameters:

- *zope_url* the zope url.
- *admin_id* and *admin_pwd* the zope admin credential.
- *time_out* maximum time to wait until the zope server restart.

zopePackZodb
~~~~~~~~~~~~
::

  zopePackZodb(zope_url, admin_id, admin_pwd, database="main", days=0)

Pack a zodb database.

Parameters:

- *database* the database to pack.
- *days* removing previous revision that are older than *days* ago


zopeFlushCache
~~~~~~~~~~~~~~
::

  zopeFlushCache(zope_url, admin_id, admin_pwd, database="main")

Remove all objects from all ZODB in-memory caches.

zopeAddExternalMethod
~~~~~~~~~~~~~~~~~~~~~
::

  zopeAddExternalMethod(parent_url, admin_id, admin_pwd,
                        method_id, module, function, run_it=True)

Add an External method an run it.

CPSTestCase
-----------

This class extends the ZopeTestCase providing common Nuxeo_ CPS_ tasks. You
need to import the CPSTestCase that works with your CPS_ for example
CPS338TestCAse or CPS340TestCase.


cpsCreateSite
~~~~~~~~~~~~~
::

  cpsCreateSite(admin_id, admin_pwd,
                manager_id, manager_password,
                manager_mail, langs=None,
                title=None, description=None,
                interface="portlets", zope_url=None, site_id=None)

Build a new CPS_ site.

Parameters:

- *admin_id* and *admin_pwd* the zope admin credential.
- *manager_id* and *manager_pwd* the cps manager credential.
- *zope_url* the Zope_ server url [*]_.
- *site_id* the CPS_ site id.

.. [*] if the zope_url and site_id is not given we guess it using the
       server_url


cpsLogin
~~~~~~~~
::

  cpsLogin(login, password)

CPS log in.

cpsLogout
~~~~~~~~~

Logout the user logged in using cpsLogin.

cpsCreateGroup
~~~~~~~~~~~~~~
::

  cpsCreateGroup(group_name)

Create a CPS_ group.

cpsVerifyGroup
~~~~~~~~~~~~~~
::

  cpsVerifyGroup(group_name)

Create a CPS_ group if not present.

cpsCreateUser
~~~~~~~~~~~~~
::

  cpsCreateUser(user_id=None, user_pwd=None,
                user_givenName=None, user_sn=None,
                user_email=None, groups=None):


Create a CPS_ users.

cpsVerifyUser
~~~~~~~~~~~~~

Create a CPS_ users if not present.


cpsSetLocalRole
~~~~~~~~~~~~~~~
::

  cpsSetLocalRole(url, name, role)

Grant role to name in url.

cpsCreateSection
~~~~~~~~~~~~~~~~
::

  cpsCreateSection(parent_url, title, description)


cpsCreateWorkspace
~~~~~~~~~~~~~~~~~~
::

  cpsCreateWorkspace(parent_url, title, description)


cpsCreateDocument
~~~~~~~~~~~~~~~~~
::

  cpsCreateDocument(parent_url)

Create a random document in the parent_url container.

cpsCreateNewsItem
~~~~~~~~~~~~~~~~~
::

  cpsCreateNewsItem(parent_url)

Create a simple news in the parent_url container.

cpsChangeUiLanguage
~~~~~~~~~~~~~~~~~~~
::

  cpsChangeUiLanguage(lang)

Change the ui locale selection


cpsListDocumentHref
~~~~~~~~~~~~~~~~~~~
::

  cpsListDocumentHref(pattern)

Return a clean list of document href that matches pattern in the previous
page fetched.

cpsSearchDocId
~~~~~~~~~~~~~~
::

  cpsSearchDocId(doc_id)

Return the list of url that ends with doc_id, using catalog search.


Todo and bugs
=============

* See the trac tickets: http://svn.nuxeo.org/trac/pub/report/12

If you want to report a bug or if you think that something is
missing, send me an email.



.. _FunkLoad: http://funkload.nuxeo.org/
.. _TestMaker: http://www.pushtotest.com/
.. _TCPWatch: http://hathawaymix.org/Software/TCPWatch/
.. _webunit: http://mechanicalcat.net/tech/webunit/
.. _pyUnit: http://pyunit.sourceforge.net/
.. _INSTALL: INSTALL.html
.. _CHANGES: CHANGES.html
.. _API: api/index.html
.. _Slides: http://blogs.nuxeo.com/sections/blogs/fermigier/2005_11_17_slides-introducing
.. _epydoc: http://epydoc.sourceforge.net/
.. _Zope: http://www.zope.org/
.. _Cmf: http://www.zope.org/Products/CMF/
.. _Nuxeo: http://www.nuxeo.com/
.. _CPS: http://www.cps-project.org/
.. _`python cheese shop`: http://www.python.org/pypi/funkload/
.. _EasyInstall: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _demo: http://svn.nuxeo.org/trac/pub/browser/funkload/trunk/funkload/demo/
.. _report: http://funkload.nuxeo.org/report-example.pdf
.. _`GNU GPL`: http://www.gnu.org/licenses/licenses.html
.. _`svn sources`: http://svn.nuxeo.org/pub/funkload/trunk/#egg=funkload-dev
.. _trac: http://svn.nuxeo.org/trac/pub/report/12
.. _doctest: http://docs.python.org/lib/module-doctest.html


.. Local Variables:
.. mode: rst
.. End:
.. vim: set filetype=rst:
