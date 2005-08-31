This folder is the FunkLoad home ($FLOAD_HOME)
==============================================
*$Id: README.txt 24534 2005-08-26 09:16:42Z bdelbosc $*


DESCRIPTION
-----------

FunkLoad is functional and load web tester.

Main FunkLoad features are:

* Run a functional test.
* View in real time the execution of the functional test in your browser.
* Turn a functional test into a load test (== bench).
* Easy test customization using configuration file.
* Produce an ReST or html detail report with:

  - test, page, request stats and charts.
  - servers cpu usage, load average, memory/swap usage and network traffic
    charts.

* Records your actions using a Web browser to write a ftest automatically.
* Full compatible with PyUnit test case.


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

To use the demo you need an http server runing on http://localhost/


Launching a functional test
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. go to the ftests folder::

    cd demo

2. run a functional test like any other unittest::

    python test_XXXX.py

Note that you can find a detail log in funkload-ftest.log


Launching a bench
~~~~~~~~~~~~~~~~~

1. go to the ftests folder::

    cd demo

2. run the bench::

   fl-run-bench test_XXX XXX test_XXX

3. view the html report::

     fl-build-report

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

  fl-credential-ctl {start|startd|stop|restart|status|log}


Monitor server
~~~~~~~~~~~~~~

If you want to monitor the server health during the bench, you have to run a
monitor xmlrpc server on the target server, this require to install the
FunkLoad package but you don't need to install TestMaker or Java.

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

* Launch testmaker UI invoking 'TestMaker'
* Go to 'Tools/New Agent' then 'Record from a Web-Browser'
  set a whaterver name and click to 'Start Recording"
* Configure your Web Browser to use the TestMaker proxy localhost:8090
* Play your scenario
* Click on 'End Recording'
* Save the tm script into the proper location and set a file_name like
   scenario_name.tm
* Close TestMaker

2. Converting the TestMaker script into a FunkLoad script::

     tm2fl scenario_name.tm

   This will produce a scenario_name.py and scenario_name.conf

3. Testing

   Test is ready to be launch::

     runftest scenario_name

   To check if the scenario is well executed you can invoke firefox to view
   each step result, edit the configuration file and add the 'view' log::

     [ftests]
     ...
     logto = console file view

   You need to have a firefox already running.

4. Implement the dynamic part and assertion

  The FunkLoad script is a jython script the jython is provided by TestMaker
  it is a python 2.1 implementation :(

  TestMaker provide also a java api http://docs.pushtotest.com/tooldocs/

  Look at ftest done in CPS-3-base-ftests or Messager_ftests for more examples.

  Assertion are like unit test assertion but only limited to:
  `assert_` = failUnless and assertEqual = assertEquals = failUnlessEqual

  Helper api:

  - self.get(url) or self.post(url, params)
  - self.getLastBaseUrl() -> return the <base /> href value
  - self.listUrl() -> return a list of all <a /> href value
  - self.getLastUrl() -> return the last Url loaded by the follow redirect
  - self.getBody -> the html page


FILES
-----


A ftests folder will contains::

  test_Foo.py       a funkload unit test
  Foo.conf          a ftest configuration file
  log/              a log folder
  report/           a report folder


BUGS
----

* TestMaker recorder (bitmechanic maxq) failed to record post with
  enctype="multipart/form-data" with an input of type file upload.
  A work around is to record on a version without the
  enctype=mutipart/form-data.

