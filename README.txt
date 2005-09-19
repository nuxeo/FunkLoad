========
FunkLoad
========
*$Id: README.txt 24534 2005-08-26 09:16:42Z bdelbosc $*


Description
===========

FunkLoad is a functional and load web tester.

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

* Provide a funkload.CPSTestCase to ease Zope and nuxeo CPS testing.


Installation
============

See the INSTALL.txt file in the FunkLoad package.



FunkLoadTestCase
================

API
---

**FunkLoadTestCase extends the unittest.TestCase with browser capabilities:**

* `self.get(url, params=None, description=None, code=None)`

  This emulate a browser http GET link, it will fetch the url submits
  appropriate cookies, follow redirection, register new cookies, load css
  and javascript that are not already cached.  This method return a webunit
  HTTPResponse.

    - url: the url without parameters
    - params: a dico of parameters that going to be append to the url like
      `url?key1=value1&...`
    - description: is used on the bench report to describe the user action
    - code: is a list of http expected code like [200:301] if the http
      response is not in the list get will raise a test failure exception
      if not provided assume that the default list is [200, 301, 302]

* `self.post(url, params=None, description=None, code=None)`

  Same interface than the get() but it use a http post method.
  You can upload a file by setting a params like this::

    from webunit.utility import Upload
    params['file_up'] = Upload('/tmp/foo.txt')

* `self.exists(url, params=None)`

  Return True if the http return code is 200, 301 or 302,
  return False if return code is 404 or 503.


**FunkLoadTestCase adds configuration file helpers:**

* `self.conf_get(section, key, default=_marker)`

  Return an entry from the command line options or configuration file
  there is also conf_getInt conf_getFloat and conf_getList


**FunkLoadTestCase adds assertions helpers:**

* `self.getLastUrl()`
  Return the last accessed page url taking care of redirects.

* `self.getLastBaseUrl()`
  Return the <base /> href value of the last accessed page.

* `self.listHref()`
  Return a list of all <a /> href value of the last accessed page.

* `self.getBody`
  Return the html page


**The response returned by a get or post are webunit HTTPResponse object:**

* response.code is the http response code

* response.headers['location'] is the Location http header value

* response.body is the html content

* response.getDOM() is a SimpleDOM interface of the fetched html page, for
  example you can do extract all h1 title doing a:
  response.getDOM().getByName('h1'), see the SimpleDOM api instructions for
  details.

To generate dummy document contents you can use the funkload.Lipsum api,
this is a very simple "Lorem ipsum" generator.

Like normal unittest you can define many tests inside a TestClass::

  from funkload.FunkLoadTestCase import FunkLoadTestCase
  ...
  def MyClass(FukLoadTestCase):
    def Setup(self):
    ...
    def test_01_foo(self):
    ...
    def test_02_bar(self):
    ...
    def tearDown(self):
    ...


Configuration
-------------

A FunkLoadTestCase class uses a configuration file to setup variable
configuration like the base server url to be tested, the test description,
credential access, logging files and other test specific parameters. The test
configuration file have the same name of the FunkLoadTestCase with a '.conf'
extension. In the previous example the file is MyClass.conf. See documented
examples in the demo/ folder for more information.

Note that the configuration file is accessible from a test using self.get_conf
method.


Logging
-------

A FunkLoadTestCase store its results in an xml file (like request and test
result) and put other log information into a text log and/or output to the
console.


ZopeTestCase
============

This class extends the FunkLoadTestCase providing common Zope tasks like:

* `zopeRestart()` Stop and Start Zope server

* `zopePackZodb()` Pack a zodb database

* `zopeFlushCache()` Remove all objects from all ZODB in-memory caches

* `zopeAddExternalMethod()` Add an External method an run it



CPSTestCase
===========

This class extends the ZopeTestCase providing common Nuxeo CPS tasks like:

* `cpsCreateSite(...)` build a new cps site

* `cpsLogin(login, password)` cps log in

* `cpsLogout()`

* `cpsCreateGroup(group_name)` Create a cps group

* `cpsVerifyGroup(group_name)` Create a cps group if not present

* `cpsCreateUser(...)` Create a cps users

* `cpsVerifyUser(...)` Create a cps users if not present

* `cpsSetLocalRole(url, name, role)` Grant role to name in url

* `cpsCreateSection(parent_url, title, description)`

* `cpsCreateWorkspace(parent_url, title, description)`

* `cpsCreateDocument(parent_url)` Create a random document in the parent_url
   container

* `cpsCreateNewsItem(parent_url)` Create a simple news in the parent_url
   container

* `cpsChangeUiLanguage(lang)` Change the ui locale selection

* `cpsListDocumentHref(pattern)` Return a clean list of document href that
   matches pattern in the previous page fetched.

* `cpsSearchDocId(doc_id)` Return the list of url that ends with doc_id,
  using catalog search.


Test runner
===========

A FunkLoad test can be used like a standard unittest using a unittest.main()
and a 'python MyFile.py'.

To ease testing FunkLoad come with an advanced test runner to override
the static configuration file.


Usage
-----
::

  fl-run-test [options] file [class.method|class|suite] [...]


Examples
~~~~~~~~
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
~~~~~~~
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
bench runner fl-run-bench.


Definition
----------

* CUs: Concurrent Users, which is the number of threads.
* Test: a FunkLoad functional test.
* cycle: a bench with a number of CUs: Staging up + logging + Staging down.
* STPS: Average of Successful Tests Per Second during a cycle
* SPPS: Average of Successfully Page Per Second during a cycle
* RPS: Average Request Per Second, successfully or not.
* max[STPS|SPPS|RPS]: maximum of STPS|SPPS|RPS for a cycle.


Test
~~~~

A test is made with 3 methods setUp/test_name/tearDown, during the test_name
method each get/post request is called a page.

::

  [setUp][page 1]    [page 2] ... [page n]   [tearDown]
  ======================================================> time
         <-----------------------------------> test metho
                 <---> sleeptime_min to sleeptime_max
         <------> page 1 connection time

Page
~~~~

A page is an http get/post request with associated sub requests like
redirects, images or links (css, js files). This is what users see as a
single page.


Cycle
~~~~~

A cycle is a load of n concurrents test during a 'duration' period.
Threads are launched every 'startupdelay' seconds, each thread executes
test in a loop.

Once all threads have been started we start to record stats.

Only tests that ends during the 'duration' period are taken into account
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

FunkLoad can execute many cycles with different number of CUs, this way you
can find easily the maximum number of users that your application can
handle.

Running n cycles with the same CUs is a good way to see how the
application handle a writing test over time.

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
        <-------->   duration    <--------->
                    <------> cycletime



Bench runner
============

::

  fl-run-bench [options] file class.method


Examples
--------
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
-------
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

To produce an html or ReST report you need to invoke the fl-build-report:

Usage
-----
::

  fl-build-report [options] xmlfile

fl-build-report analyze a FunkLoad bench xml result file and output a report.


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
FunkLoad provides an xmlrpc credential server to serve login/pwd between the
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

See the demo/ folder for example of credential configuration file.

To get credential from a FunkLoad test::
  from funkload.utils import xmlrpc_get_credential
  user, pwd = xmlrpc_get_credential(credential_host, credential_port)

To get credential from a group::
  reviewer, pwd = xmlrpc_get_credential(credential_host, credential_port,
                                       'Reviewer')


Monitor server
==============

If you want to monitor the server health during the bench, you have to run a
monitor xmlrpc server on the target server, this require to install the
FunkLoad package.

On the server side init the FunkLoad env as above and ::

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

1. Record using TestMaker

  * Launch testmaker UI
  * Go to 'Tools/New Agent' then 'Record from a Web-Browser'
    set a whatever name and click to 'Start Recording"
  * Configure your Web Browser to use the TestMaker proxy `localhost:8090`
  * Play your scenario
  * Click on `End Recording`
  * Save the tm script into the proper location and set a file_name like
    `scenario_name.tm`
  * Close TestMaker

2. Converting the TestMaker script into a FunkLoad script::

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
  * Add assertion using FunkLoad helpers


Files
=====

  fl-run-test                - run a test
  fl-run-bench               - run a test in bench mode
  fl-build-report            - build a bench report
  fl-import-from-tm-recorder - convert a TestMaker test into a FunkLoad script
  fl-credential-ctl          - credential controller
  fl-monitor-ctl             - monitoring controller


Bugs
====

* WebUnit don't handle Referer header, thus page that redirect to a referer
  will not work.

* TestMaker recorder (bitmechanic maxq) failed to record post with
  enctype="multipart/form-data" with an input of type file upload.
  A work around is to record on a version without the
  enctype=mutipart/form-data.


Author
======

* Benoit Delbosc bdelbosc@nuxeo.com
  Credits goes to Frank Cohen's TestMaker framework and Richard Jones
  webunit package.

