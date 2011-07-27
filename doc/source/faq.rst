FAQ
====

What does all these dots mean ?
-------------------------------

During a bench cycle the "Starting threads" dots means the number
running threads::

  Cycle #1 with 10 virtual users
  ------------------------------
  
  * setUpCycle hook: ... done.
  * Current time: 2011-01-26T23:23:06.234422
  * Starting threads: ........

During the cycle logging the green dots means a successful test while
the red 'F' are for test failure::

  * Logging for 10s (until 2011-01-26T23:23:16.360602): ......F......


During the stagging down the dots are the number of stopped threads::

  * Waiting end of threads: .........


How to accept invalid Cookies ?
----------------------------------

- ``Error : COOKIE ERROR: Cookie domain "<DOMAINE>" doesn’t start with "."``

  Comment the lines in file /usr/lib/python2.6/site-packages/webunit-1.3.8-py2.6.egg/webunit/cookie.py::

  #if domain[0] != '.':
  #  raise Error, 'Cookie domain "%s" doesn\'t start with "."' % domain


- ``Error : COOKIE ERROR: Cookie domain "."<DOMAINE>" doesn’t match request host "<DOMAINE>"``

  Comment the lines in the file /usr/lib/python2.6/site-packages/webunit-1.3.8-py2.6.egg/webunit/cookie.py::

      #if not server.endswith(domain):
      #  raise Error, 'Cookie domain "%s" doesn\'t match '
      #  'request host "%s"'%(domain, server)


How to submit high load ?
----------------------------

High load works fine for IO Bound test, not on CPU bound test. The
test script must be light:

- When possible don't parse html/xml page, using simple find or regexp
  are much much faster than any html parsing including getDOM, html
  parser or beautifulsoup. If you start emulating a browser then you
  will be as slow as a browser.

- Always use ``--simple-fetch`` option to prevent parsing html page to
  retrieve resources use explicit GET in your code.

- Try to generate or prepare the data before the test to minimize the
  processing during the test.

On 32b OS install psyco, it gives a 50% boost (``aptitude install
python-psyco`` on Debia/Ubuntu OS).

On multi CPU server, GIL is getting infamous, to get all the power you
need to use CPU affinity ``taskset -c 0 fl-run-bench`` is always
faster than ``fl-run-bench``.  Using one bench runner process per CPU
is a work around to use the full server power.

Use multiple machine to perform the load, see the next section.


How to run multiple bencher ?
-------------------------------

Bench result file can be merged by the ``fl-build-report`` command,
but how to run multiple bencher ?

There are many ways: 

* Use the new distribute mode (still in beta), it requires paramiko and
  virtualenv::
  
    sudo aptitude install python-paramiko, python-virtualenv

  It adds 2 new command line options:

  - ``--distribute``: to enable distributed mode

  - ``--distribute-workers=uname@host,uname:pwd@host...``: 
    user:password can be skipped if using pub-key.

  For instance to use 2 workers you can do something like this::
  
      $ fl-run-bench -c 1:2:3 -D 5 -f --simple-fetch  test_Simple.py Simple.test_simple --distribute --distribute-workers=node1,node2 -u http://target/
      ========================================================================
      Benching Simple.test_simple
      ========================================================================
      Access 20 times the main url
      ------------------------------------------------------------------------
            
      Configuration
      =============
      
      * Current time: 2011-02-13T23:15:15.174148
      * Configuration file: /tmp/funkload-demo/simple/Simple.conf
      * Distributed output: log-distributed
      * Server: http://node0/
      * Cycles: [1, 2, 3]
      * Cycle duration: 5s
      * Sleeptime between request: from 0.0s to 0.0s
      * Sleeptime between test case: 0.0s
      * Startup delay between thread: 0.01s
      * Workers :octopussy,simplet
      
      * Preparing sandboxes for 2 workers.....
      * Starting 2 workers..
      
      * [node1] returned
      * [node2] returned
      * Received bench log from [node1] into log-distributed/node1-simple-bench.xml
      * Received bench log from [node2] into log-distributed/node2-simple-bench.xml
      
      # Now building the report 
      $ fl-build-report --html log-distributed/node1-simple-bench.xml  log-distributed/node2-simple-bench.xml
      Merging results files: ..
      nodes: node1, node2
      cycles for a node:    [1, 2, 3]
      cycles for all nodes: [2, 4, 6]
      Results merged in tmp file: /tmp/fl-mrg-o0MI8L.xml
      Creating html report: ...done:
      /tmp/funkload-demo/simple/test_simple-20110213T231543/index.html
 

  Note that the version of FunkLoad installed on nodes is defined in
  the configuration file::

     [distribute]
     log_path = log-distributed
     funkload_location=http://pypi.python.org/packages/source/f/funkload/funkload-1.16.1.tar.gz


* Using BenchMaster http://pypi.python.org/pypi/benchmaster

* Using Fabric http://tarekziade.wordpress.com/2010/12/09/funkload-fabric-quick-and-dirty-distributed-load-system/

* Old school pssh/Makefile::

   # clean all node workspaces 
   parallel-ssh -h hosts.txt rm -rf /tmp/ftests/
   # distribute tests 
   parallel-scp -h hosts.txt -r ftests /tmp/ftests
   # launch a bench
   parallel-ssh -h hosts.txt -t -1 -o bench “(cd /tmp/ftests&& make bench URL=http://target/)”
   # get the results 
   parallel-slurp -h hosts.txt -o out -L results-date -u ‘+%Y%m%d-%H%M%S’ -r /tmp/ftests/report .
   # build the report with fl-build-report, it supports the results merging
 

How to mix different scenarii in a bench ?
-------------------------------------------

Simple example with percent of users::

    import random
    ...
    def testMixin(self):
        if random.randint(1, 100) < 30:
            # 30% writer
            return self.testWriter()
        else:
            # 70% reader
            return self.testReader()

Example with fixed number of users::

    def testMixin(self):
        if self.thread_id < 2:
            # 2 importer threads
            return self.testImporter()
        elif self.thread_id < 16:
            # 15 back office with sleep time
            return self.testBackOffice()
        else:
            # front office users
            return self.testFrontOffice()


Note that when mixing tests the detail report for each page is
meaningless because you are mixing pages from multiple tests.

How to modify a report ?
--------------------------

The report is in `reStructuredText 
<http://docutils.sourceforge.net/rst.html>`_, the ``index.rst`` can be
edited in text mode, to rebuild the html version::

    rst2html --stylesheet=funkload.css   index.rst --traceback > index.html

Charts are build with gnuplot the gplot script file are present in the
report directory to rebuild the pages charts for instance::

    gnuplot pages.gplot

Since FunkLoad 1.15 you can also use an org-mode_ output to edit or
extend the report before exporting it as a PDF.


How to automate stuff ?
-----------------------

Here is a sample Makefile

::

    CREDCTL := fl-credential-ctl credential.conf
    MONCTL := fl-monitor-ctl monitor.conf
    LOG_HOME := ./log
    
    ifdef URL
    	FLOPS = -u $(URL) $(EXT)
    else
    	FLOPS = $(EXT)
    endif
    
    ifdef REPORT_HOME
    	REPORT = $(REPORT_HOME)
    else
    	REPORT = report
    endif
    
    all: test
    
    test: start test-app stop
    
    bench: start bench-app stop
    
    start:
    	-mkdir -p $(REPORT) $(LOG_HOME)
    	-$(MONCTL) restart
    	-$(CREDCTL) restart
    
    stop:
    	-$(MONCTL) stop
    	-$(CREDCTL) stop
    
    test-app:
    	fl-run-test -d --debug-level=3 --simple-fetch test_app.py App.test_app $(FLOPS)
    
    bench-app:
    	-fl-run-bench --simple-fetch test_app.py App.test_app -c 1:5:10:15:20:30:40:50 -D 45 -m 0.1 -M .5 -s 1 $(FLOPS)
    	-fl-build-report $(LOG_HOME)/app-bench.xml --html -o $(REPORT)
    
    clean:
    	-find . "(" -name "*~" -or  -name ".#*" -or  -name "*.pyc" ")" -print0 | xargs -0 rm -f


It can be used like this::
   
   make test
   make test URL=http://override-url/
   # add extra parameters to the FunkLoad command
   make test EXT="-V"
   make bench


How to write fluent tests ?
-----------------------------

You can use the `PageObject 
<http://code.google.com/p/webdriver/wiki/PageObjects>`_ and `fluent
interface <http://www.martinfowler.com/bliki/FluentInterface.html>`_
patterns as in the `Nuxeo DM tests 
<http://hg.nuxeo.org/nuxeo/nuxeo-distribution/file/57fbd264dd17/nuxeo-distribution-dm/ftest/funkload/README.txt>`_
to write test like this::

     class MySuite(NuxeoTestCase):
          def testMyScenario(self):
              (LoginPage(self)
               .login('Administrator', 'Administrator')
               .getRootWorkspaces()
               .createWorkspace('My workspace', 'Test ws')
               .rights().grant('ReadWrite', 'members')
               .view()
               .createFolder('My folder', 'Test folder')
               .createFile('My file', 'Test file', 'foo.pdf')
               .getRootWorkspaces().deleteItem("My workspace")
               .logout())


How to receive release announcement ?
---------------------------------------

Subscribe to the freshmeat project:
http://freshmeat.net/projects/funkload




.. _org-mode: http://orgmode.org/
