========
FunkLoad
========
*$Id: README.txt 24534 2005-08-26 09:16:42Z bdelbosc $*


DESCRIPTION
-----------

FunkLoad is functional and load web tester.

Main FunkLoad features are:

* Compatible with pyUnit framework.

* Simulate a true browser navigation (using Richard Jones' webunit) with:
  - cookies support
  - fetching css, javascript and images
  - simulate caching
  - file uplaod and multipart/form-data submission

* Advanced test runner with many command line options:
  - color mode
  - display the page fetched in real time in your browser
  - debug mode

* Turn a functional test into a load test, just by invoking the bench runner
  you can simulate a load of hundreds users.

* Detail bench report in ReST or html containing:
  - bench configuration
  - tests, pages, requests stats and charts.
  - servers cpu usage, load average, memory/swap usage and network traffic
    charts.

* Easy test customization using configuration file or command line.

* Easy test creation using a TestMaker to records your actions using a Web
  browser to write a test automatically.

* Web assertion helpers like listHref or getDOM to make assertion on the
  fetched page.

* CPSTestCase class to ease cps testing.


INSTALLATION
------------

See the INSTALL.txt file in the FunkLoad package.


SYNOPSIS
--------


DEFINITION
~~~~~~~~~~

* CUs: Concurrent Users, which is the number of threads.
* test: a FunkLoad functional unit test.
* cycle: a bench with a number of CUs. Staging up + logging + Staging down.
* STPS: Average of Successfull Tests Per Second during a cycle
* SPPS: Average of Successfull Page Per Second during a cycle
* RPS: Average Request Per Second, successfull or not.
* max[STPS|SPPS|RPS]: maximum of STPS|SPPS|RPS for a cycle.

TEST
~~~~

A test is made with 3 methods setUp/test_name/tearDown, during the test_name
method each get/post request is called a page.

::

  [setUp][page 1]    [page 2] ... [page n]   [tearDown]
  ======================================================> time
         \___________________________________\ runTest method
                 \___\ sleeptime_min to sleeptime_max
         \_______\ page 1 connection time

PAGE
~~~~

A page is an http get/post request with associated sub requests like
redirects, images or links (css, js files). This is what users see as a
single page.


CYCLE
~~~~~

A cycle is a load of n concurrents test during a 'duration' period.
Threads are launched every 'startupdelay' seconds, each thread executes
ftest in a loop.

Once all threads have been started we start to record stats.

Only tests that ends during the 'duration' period are taken into account
for the test stats (in the representation below test like [---X are not
take into account).

Only pages and requests that finish during the 'duration' are taken into
account for the request and pages statistic

::

  Threads
  ^
  |
  |
  |n           [--ftest--]   [--------]   [--|---X
  |...         |                             |
  |            |                             |
  |2    [------|--]   [--------]   [-------] | [----X
  |            |                             |
  |1 [-------X | [--------]   [-------]   [--|--X
  |
  ===================================================> time
               \______cycle duration_________\
     \_________\ staging                     \_______\ staging
     \__\ startupdelay     \__\ sleeptime


CYCLES
~~~~~~

FunkLoad can execute many cycles with different number of CUs.


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
        \________\   duration    \_________\
                    \______\ cycletime




USAGE
-----


Launching a functional test
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. go to the tests folder::

2. run a functional test like any other unittest::

    python myFile.py
    # or better use the FunkLoad test runner
    fl-run-test myFile.py

See fl-run-test --help for more information about how to launch a test.


Launching a bench
~~~~~~~~~~~~~~~~~

1. go to the ftests folder::

2. run the bench::

     fl-run-bench myFile.py MyTestCase.testSomething

   Note that the clas MyTestCase will use a configuration file named
   MyTestCase.conf.

3. view the html report::

     fl-build-report --html MyTestCase-bench.xml

   Note that you can preview the report for cycles that have been done while
   the bench is still running by invoking the above command.



Credential server
~~~~~~~~~~~~~~~~~

If you are writing a bench that requires to be logged with different users
FunkLoad provides an xmlrpc credential server to serve login/pwd between the
different threads.

Start the credential server::

  fl-credential-ctl CONFIGURATION_FILE start

More options::

  fl-credential-ctl --help


Monitor server
~~~~~~~~~~~~~~

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


Then on your bench host edit your ftest configuration file and this section::

  [monitor]
  hosts = server.to.test.com

  [server.to.test.com]
  description = The web server
  port = 8008

Then run the bench, the report will include server stats.
Note that you can monitor multiple hosts.


Recording a new FunkLoad test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Record using TestMaker

* Launch testmaker UI
* Go to 'Tools/New Agent' then 'Record from a Web-Browser'
  set a whaterver name and click to 'Start Recording"
* Configure your Web Browser to use the TestMaker proxy localhost:8090
* Play your scenario
* Click on 'End Recording'
* Save the tm script into the proper location and set a file_name like
   scenario_name.tm
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

  Assertion are like unit test assertion, but you have helpers to parse http
  response or content

  Helper api:

  - self.get(url, description) or self.post(url, params, description)
  - self.getLastUrl() -> return the last accessed url taking care or redirects
  - self.getLastBaseUrl() -> return the <base /> href value
  - self.listHref() -> return a list of all <a /> href value
  - self.getBody -> the html page

  the response returned by get() or post() have a getDOM method to parse the
  content.

FILES
-----

  fl-run-test                - run a test
  fl-run-bench               - run a test in bench mode
  fl-build-report            - build a bench report
  fl-import-from-tm-recorder - convert a TestMaker test into a FunkLoad script
  fl-credential-ctl          - credential controler
  fl-monitor-ctl             - monitoring controler


BUGS
----

* TestMaker recorder (bitmechanic maxq) failed to record post with
  enctype="multipart/form-data" with an input of type file upload.
  A work around is to record on a version without the
  enctype=mutipart/form-data.

