First Steps with FunkLoad
==========================

A FunkLoad test is made of a typical unittest and a configuration
file. Let's look at a simple test script that is comming with the
FunkLoad examples.

To get the demo examples you just need to run::

  fl-install-demo
  # Extract FunkLoad examples into ./funkload-demo : ...  done.
  cd funkload-demo/simple


The test case
----------------------

Here is an extract of the simple demo test case ``test_Simple.py``::

  import unittest
  from random import random
  from funkload.FunkLoadTestCase import FunkLoadTestCase
  
  class Simple(FunkLoadTestCase):
      """This test use a configuration file Simple.conf."""
      def setUp(self):
          """Setting up test."""
          self.server_url = self.conf_get('main', 'url')
  
      def test_simple(self):
          # The description should be set in the configuration file
          server_url = self.server_url
          # begin of test ---------------------------------------------
          nb_time = self.conf_getInt('test_simple', 'nb_time')
          for i in range(nb_time):
              self.get(server_url, description='Get url')
          # end of test -----------------------------------------------
    
  if __name__ in ('main', '__main__'):
      unittest.main()

The Simple test case extend ``FunkLoadTestCase`` and implement a test
case named test_simple. this test case loop on a get request.  

The ``FunkLoadTestCase`` extends the ``unittest.TestCase`` to add methods:

* to send HTTP request (get, post, put, delete or xmlrpc)
* to help building assertion with the response (getBody, getLastUrl, ...)
* to customize the test by accessing a configuration file (conf_getInt)
* ...

The target url, the number of requests are defined in the
configuration files.

By convention the name of the configuration file is the name of the
test case class with ".conf" extension in our case: ``Simple.conf``.
  
The configuration file
----------------------------

It is a plain text file with sections::

  # main section for the test case
  [main]
  title=Simple FunkLoad tests
  description=Simply testing a default static page
  url=http://localhost/index.html

  # a section for each test 
  [test_simple]
  description=Access %(nb_time)s times the main url
  nb_time=20
  
  <<snip>>
  # a section to configure the test mode
  [ftest]
  log_to = console file
  log_path = simple-test.log
  result_path = simple-test.xml
  sleep_time_min = 0
  sleep_time_max = 0

  # a section to configure the bench mode
  [bench]
  cycles = 50:75:100:125
  duration = 10
  startup_delay = 0.01
  sleep_time = 0.01
  cycle_time = 1
  log_to =
  log_path = simple-bench.log
  result_path = simple-bench.xml
  sleep_time_min = 0
  sleep_time_max = 0.5

Runing the test
------------------

Check that the url present in the ``main`` section is reachable, then
invoking ``fl-run-test`` will run all the tests present in the
test_Simple module::

  $ fl-run-test -dv test_Simple.py
  test_simple (test_Simple.Simple) ... test_simple: Starting -----------------------------------
          Access 20 times the main url
  test_simple: GET: http://localhost/index.html
          Page 1: Get url ...
  test_simple:  Done in 0.006s
  test_simple:  Load css and images...
  test_simple:   Done in 0.002s
  test_simple: GET: http://localhost/index.html
          Page 2: Get url ...
  <<snip>>
         Page 20: Get url ...
  test_simple:  Done in 0.000s
  test_simple:  Load css and images...
  test_simple:   Done in 0.000s
  Ok
  ----------------------------------------------------------------------
  Ran 1 test in 0.051s
  
  OK


Runing a benchmark
--------------------

To run a benchmark you invoke ``fl-run-bench`` instead of the test
runner, you also need to select which test case to run.

The result of the bench will be saved in a single xml file
``simple-bench.xml``, the name of this result file is set in the
configuration file in the ``bench`` section.

You can override the configuration file using command line option,
here we ask for 3 cycles with 1, 10 and 20 concurrents users (CUs).

::

  $ fl-run-bench -c 1:10:20 test_Simple.py Simple.test_simple
  ========================================================================
  Benching Simple.test_simple
  ========================================================================
  Access 20 times the main url
  ------------------------------------------------------------------------
  
  Configuration
  =============
  
  * Current time: 2011-01-26T23:22:51.267757
  * Configuration file: /tmp/funkload-demo/simple/Simple.conf
  * Log xml: /tmp/funkload-demo/simple/simple-bench.xml
  * Server: http://localhost/index.html
  * Cycles: [1, 10, 20]
  * Cycle duration: 10s
  * Sleeptime between request: from 0.0s to 0.5s
  * Sleeptime between test case: 0.01s
  * Startup delay between thread: 0.01s
  
  Benching
  ========
  
  * setUpBench hook: ... done.
  
  Cycle #0 with 1 virtual users
  -----------------------------
  
  * setUpCycle hook: ... done.
  * Start monitoring localhost: ... failed, server is down.
  * Current time: 2011-01-26T23:22:51.279718
  * Starting threads: . done.
  * Logging for 10s (until 2011-01-26T23:23:01.301664): .. done.
  * Waiting end of threads: . done.
  * Waiting cycle sleeptime 1s: ... done.
  * tearDownCycle hook: ... done.
  * End of cycle, 14.96s elapsed.
  * Cycle result: **SUCCESSFUL**, 2 success, 0 failure, 0 errors.
  
  Cycle #1 with 10 virtual users
  ------------------------------
  
  * setUpCycle hook: ... done.
  * Current time: 2011-01-26T23:23:06.234422
  * Starting threads: .......... done.
  * Logging for 10s (until 2011-01-26T23:23:16.360602): .............. done.
  * Waiting end of threads: .......... done.
  * Waiting cycle sleeptime 1s: ... done.
  * tearDownCycle hook: ... done.
  * End of cycle, 16.67s elapsed.
  * Cycle result: **SUCCESSFUL**, 14 success, 0 failure, 0 errors.
  
  Cycle #2 with 20 virtual users
  ------------------------------
    
  * setUpCycle hook: ... done.
  * Current time: 2011-01-26T23:23:06.234422
  * Starting threads: .......... done.
  * Logging for 10s (until 2011-01-26T23:23:16.360602): .............. done.
  * Waiting end of threads: .......... done.
  * Waiting cycle sleeptime 1s: ... done.
  * tearDownCycle hook: ... done.
  * End of cycle, 16.67s elapsed.
  * Cycle result: **SUCCESSFUL**, 14 success, 0 failure, 0 errors.
  
  * tearDownBench hook: ... done.
  
  Result
  ======
  
  * Success: 40
  * Failures: 0
  * Errors: 0
  
  Bench status: **SUCCESSFUL**
  

Generating a report
--------------------

The xml result file can be turn into an html report this way::

  $ fl-build-report --html simple-bench.xml
  Creating html report: ...done: 
  /tmp/funkload-demo/simple/test_simple-20110126T232251/index.html

It should generate something like this: 
   http://funkload.nuxeo.org/report-example/test_simple-20110126T232251/

Note that there were no monitoring in our simple benchmark.


Write your own test
-------------------

The process to write a new test is the following:

* Use the recorder_ to initialize the test case and the configuration
  files and to grab requests.

* Play the test and display each response in firefox, this will help
  you to add assertion and check the response::

     fl-run-test -dV test_BasicNavigation.py


* Implement the dynamic part:

  - For each request add an assertion to make sure the page is the one
    you expect. this can be done by checking if a term is present in
    a response::

       self.assert_('logout' in self.getBody(), "Login failure")


  - Generates random input, you can use the FunkLoad.Lipsum module::

       from FunkLoad import Lipsum
       ...
       lipsum = Lipsum()
       # Get a random title
       title = lipsum.getSubject()


  - Extracts a token from a previous response::

       from FunkLoad.utils import extract_token
       ...
       jsf_state = extract_token(self.getBody(), ' id="javax.faces.ViewState" value="', '"')

    	 
  - Uses a credential_ server if you want to make a bench with different users
    or simply don't want to hard code your login/password::

       from funkload.utils import xmlrpc_get_credential	
       ...
       # get an admin user
       login, pwd = xmlrpc_get_credential(host, port, "admin")


* Configure the monitoring_ and automate your benchmark using a Makefile_.


.. _recorder: recorder.html
.. _credential: credential.html
.. _monitoring: monitoring.html
.. _Makefile: makefile.html
