========
FunkLoad
========

:author: Benoit Delbosc

:address: bdelbosc _at_ nuxeo.com

:version: FunkLoad/1.1.0

:revision: $Id$

:Copyright: (C) Copyright 2005 Nuxeo SARL (http://nuxeo.com).
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

.. contents::   :depth: 3


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

* Functional test are pure Python scripts using the pyUnit_ framework like
  normal unit test. Python enable complex scenarios to handle real world
  applications.

* Truly emulates a web browser (single-threaded) using Richard Jones'
  webunit_:

  - basic authentication support
  - cookies support
  - fetching css, javascript and images
  - emulating a browser cache
  - file upload and multipart/form-data submission
  - https support

* Advanced test runner with many command-line options:

  - set the target server url
  - display the fetched page in real time in your browser
  - debug mode
  - green/red color mode

* Turn a functional test into a load test: just by invoking the bench runner
  you can identify scalability and performance problems.

* Detailed bench reports in ReST or HTML (and PDF via ps2pdf)
  containing:

  - bench configuration
  - tests, pages, requests stats and charts.
  - 5 slowest requests
  - servers cpu usage, load average, memory/swap usage and network traffic
    charts.
  - http error summary list

* Easy test customization using a configuration file or command line options.

* Easy test creation using TestMaker_ / maxq_ recorder, so you can use your web
  browser and produce a FunkLoad_ test automatically.

* Provides web assertion helpers.

* Provides a funkload.CPSTestCase to ease Zope_ and Nuxeo_ CPS_ testing.

* Easy to use, see examples in the demo_ folder.


Where to find FunkLoad ?
------------------------

Check the latest package at http://funkload.nuxeo.org/

Or from bleeding edge svn sources, if you want to try the latest unstable
sources::

    svn co https://svn.nuxeo.org/pub/funkload/trunk funkload


Installation
------------

See the INSTALL.txt_ file for requirement and installation.


Examples
--------

See the demo_ folder contents and a report_ example.

.. _demo: http://svn.nuxeo.org/trac/pub/browser/funkload/trunk/demo/
.. _report: http://funkload.nuxeo.org/report-example.pdf

Credits
-------

Thanks to Frank Cohen's TestMaker_ framework and Richard Jones webunit_
package.


The FunkLoadTestCase
====================

FunkLoadTestCase extends the pyUnit_ unittest.TestCase with browser
capabilities, configuration file helpers and assertions helpers. FunkLoad_
provides also some tools to generate random inputs and communicate with
credential servers.


Browser API
-----------

get
~~~
::

  get(url, params=None, description=None, ok_codes=None)

This emulates a browser http GET link. It will fetch the url, submits
appropriate cookies, follow redirection, register new cookies, load css and
javascript that are not already cached.
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

Remove basic auth credential set by setBasicAuth

XML RPC API
-----------

You can test or bench xmlrpc services using the following API.

xmlrpc_call
~~~~~~~~~~~
::

  xmlrpc_call(url, method_name, params=None, description=None)

Call the ``method_name`` at ``url`` using xmlrpclib. You can use the
setBasicAuth_ method before to handle the http basic authentication. Note
that due to xmlrpclib limitation you can not use an http proxy.

Parameters:

- *url* the url of the xmlrpc server
- *method_name* the name of the procedure to call
- *params* a list of parameters to pass to the method
- *description* is used on the bench report to describe the action


Configuration file API
----------------------

A FunkLoadTestCase class uses a configuration file to setup variable
configuration, like the base server url to be tested, the test description,
credential access, logging files and other test specific parameters. The test
configuration file have the same name of the FunkLoadTestCase with a '.conf'
extension. See documented examples in the demo/ folder.

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

Return a list, the default separators is a colon ':'.


Assertion helpers API
---------------------

FunkLoad_ uses the unittest assertion (``assert_``, ``assertEquals``,
``fail``, ...), but provides some methods to check the http response.


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

  listHref()

Return a list of all <a /> href value of the last accessed page.


getBody
~~~~~~~
::

  getBody()

Return the html page content.


The response object
~~~~~~~~~~~~~~~~~~~

The response returned by a get or post are webunit_ HTTPResponse object

::

  repsonse = self.get(url)
  print "http response code %s" % response.code
  print "http header location %s" % response.headers['location']


::

  response.getDOM().getByName('h1')

getDOM return a SimpleDOM interface of the fetched html page, see the
webunit_ SimpleDOM api instructions for details.


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


Other TestCases
===============

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

This class extends the ZopeTestCase providing common Nuxeo_ CPS_ tasks.

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


Test runner
===========

A FunkLoad_ test can be used like a standard unittest using a unittest.main()
and a 'python MyFile.py'.

To ease testing FunkLoad_ come with an advanced test runner to override
the static configuration file.


Usage
-----
::

  fl-run-test [options] file [class.method|class|suite] [...]


Examples
--------
::

  fl-run-test myFile.py              - run default set of tests
  fl-run-test myFile.py MyTestSuite  - run suite 'MyTestSuite'
  fl-run-test myFile.py MyTestCase.testSomething
                                     - run MyTestCase.testSomething
  fl-run-test myFile.py MyTestCase   - run all 'test*' test methods
                                       in MyTestCase
  fl-run-test myFile.py -c -u http://localhost MyTestCase
                                     - same in color against localhost
  %prot myfile.py -V                 - run default set of tests and view in
                                       real time each page fetch with firefox
  fl-run-test -h                     - more options


Options
-------
::

  --help, -h              show this help message and exit
  --quiet, -q             Minimal output
  --verbose, -v           Verbose output
  --debug, -d             FunkLoad debug output
  --color, -c             Colored output
  --url=MAIN_URL, -uMAIN_URL
                          Base URL to bench without ending '/'.
  --sleep-time-min=TEST_SLEEP_TIME_MIN, -mTEST_SLEEP_TIME_MIN
                          Minimum sleep time between request.
  --sleep-time-max=TEST_SLEEP_TIME_MAX, -MTEST_SLEEP_TIME_MAX
                          Maximum sleep time between request.
  --dump-directory=DUMP_DIR, -DDUMP_DIR
                          Directory to dump html pages.
  --firefox-view, -V      Real time view using firefox, you must have a running
                          instance of firefox in the same host.



Benching
========

The same FunkLaod test can be turned into a load test, just by invoking the
bench runner ``fl-run-bench``.

Since it uses significant CPU resources, make sure that performance limits
are not hit by FunkLoad_ before your server's limit is reached.

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
                                           - bench MyTestCase.testSomething
                                             using MyTestCase.conf
  fl-run-bench -u http://localhost:8080 -c 10:20 -d 30 myFile.py \
        MyTestCase.testSomething
                                           - bench MyTestCase.testSomething
                                             on localhost:8080 with 2 cycles
                                             of 10 and 20 users during 30s
  fl-run-bench -h                                 - more options


Options
~~~~~~~
::

  --help, -h              show this help message and exit
  --url=MAIN_URL, -uMAIN_URL
                          Base URL to bench.
  --cycles=BENCH_CYCLES, -cBENCH_CYCLES
                          Cycles to bench, this is a list of number of virtual
                          concurrent users, to run a bench with 3 cycles with 5,
                          10 and 20 users use: -c 2:10:20
  --duration=BENCH_DURATION, -dBENCH_DURATION
                          Duration of a cycle in seconds.
  --sleep-time-min=BENCH_SLEEP_TIME_MIN, -mBENCH_SLEEP_TIME_MIN
                          Minimum sleep time between request.
  --sleep-time-max=BENCH_SLEEP_TIME_MAX, -MBENCH_SLEEP_TIME_MAX
                          Maximum sleep time between request.
  --startup-delay=BENCH_STARTUP_DELAY, -sBENCH_STARTUP_DELAY
                          Startup delay between thread.
  --color, -C             Colored output



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

  fl-build-report funkload.xml                    - ReST rendering into stdout
  fl-build-report --html -o /tmp funkload.xml     - Build an HTML report in /tmp
  fl-build-report -h                              - more options


Options
-------
::

  --help, -h              show this help message and exit
  --html, -H              Produce an html report.
  --output-directory=OUTPUT_DIR, -oOUTPUT_DIR
                          Directory to store reports.




 Note that you can preview the report for cycles that have been done while
 the bench is still running by invoking the above command.



Credential server
=================

If you are writing a bench that requires to be logged with different users
FunkLoad_ provides an xmlrpc credential server to serve login/pwd between the
different threads.

It requires 2 files (like unix /etc/passwd and /etc/group) the passwd file
have the following format::

  login1:pwd1
  ...

the group file format is::

  group1:user1, user2
  group2:user2
  ...

Start the credential server::

  fl-credential-ctl CONFIGURATION_FILE start

More options::

  fl-credential-ctl --help

See the demo/cmf folder for example of credential configuration file.


Monitor server
==============

If you want to monitor the server health during the bench, you have to run a
monitor xmlrpc server on the target server, this require to install the
FunkLoad_ package.

On the server side init the FunkLoad_ env as above and ::

  # edit monitor.conf if needed and run
  fl-monitor-ctl $FLOAD_HOME/lib/monitor.conf start

  # check if it is fine
  fl-monitor-ctl $FLOAD_HOME/lib/monitor.conf test

  # more info
  fl-monitor-ctl --help


Then on your bench host edit your test configuration file and this section::

  [monitor]
  hosts = server.to.test.com

  [server.to.test.com]
  description = The web server
  port = 8008

Then run the bench, the report will include server stats.
Note that you can monitor multiple hosts.


Recording a new FunkLoad test
=============================

TestMaker_ java framework include a maxq_ proxy recorder, see INSTALL.txt_ for
information on how to install TestMaker.

1. Record using TestMaker_

  * Launch testmaker UI
  * Go to 'Tools/New Agent' then 'Record from a Web-Browser'
    set a whatever name and click to 'Start Recording"
  * Configure your Web Browser to use the TestMaker_ proxy `localhost:8090`
  * Play your scenario
  * Click on `End Recording`
  * Save the tm script into the proper location and set a file_name like
    `scenario_name.tm`
  * Close TestMaker_

2. Converting the TestMaker_ script into a FunkLoad_ script::

     fl-import-from-tm-recorder scenario_name.tm

   This will produce a test_ScenarioName.py and ScenarioName.conf

3. Testing

   Test is ready to be launch::

     fl-run-test test_ScenarioName.py

   To check if the scenario is well executed you can invoke firefox to view
   each step result and add debug information::

     fl-run-test -V -d test_ScenarioName.py

   You need to have a firefox already running on the same host.

4. Implement the dynamic part and assertion

  * Use the configuration file for settings like server_url
  * Use a credential server if you want to make bench with different users
  * Add assertion using FunkLoad_ helpers


Bugs
====

* See the trac tickets: http://svn.nuxeo.org/trac/pub/report/12


.. _FunkLoad: http://funkload.nuxeo.org/
.. _TestMaker: http://www.pushtotest.com/
.. _webunit: http://mechanicalcat.net/tech/webunit/
.. _pyUnit: http://pyunit.sourceforge.net/
.. _INSTALL.txt: INSTALL.html
.. _maxq: http://maxq.tigris.org/
.. _Zope: http://www.zope.org/
.. _Cmf: http://www.zope.org/Products/CMF/
.. _Nuxeo: http://www.nuxeo.com/
.. _CPS: http://www.cps-project.org/
