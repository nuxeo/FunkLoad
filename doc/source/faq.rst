FAQ
====

What do all these dots mean ?
-------------------------------

During a bench cycle each "Starting threads" dot represents a
running thread::

  Cycle #1 with 10 virtual users
  ------------------------------

  * setUpCycle hook: ... done.
  * Current time: 2011-01-26T23:23:06.234422
  * Starting threads: ........

During the cycle logging each green dot represents a successful test while
each red 'F' represents a test failure::

  * Logging for 10s (until 2011-01-26T23:23:16.360602): ......F......


During the tear-down each dot represents a stopped thread::

  * Waiting end of threads: .........


How can I accept invalid Cookies ?
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


How can I share a counter between concurrent users ?
--------------------------------------------------

The credential server can serve a sequence. Using ``xmlrpc_get_seq``
threads can share a sequence::

    from funkload.utils import xmlrpc_get_seq
    ...
    seq = xmlrpc_get_seq()



How can I set a timeout on request ?
-----------------------------------

FunkLoad uses (a patched) webunit, which uses httplib for the actual
requests. It does not explicitly set a timeout, so httplib uses the
global default from socket. By default, the global default is None,
meaning "wait forever". Setting it to a value will cause HTTP requests
made by FunkLoad to time out if the server does not respond in time.
::

  import socket
  socket.setdefaulttimeout(SECONDS)

where SECONDS is, of course, your preferred timeout in seconds.

How can I submit high load ?
----------------------------

High load works fine for IO Bound tests, not on CPU bound tests. The
test script must be light:

- When possible don't parse HTML/xml pages, use string find methods
  or regular expressions - they are much much faster than any HTML
  parsing including getDOM and BeautifulSoup. If you start emulating
  a browser, you will be as slow as a browser.

- Always use the ``--simple-fetch`` option to prevent parsing HTML
  pages and retrieving resources.

- Try to generate or prepare the data before the test to minimize the
  processing during the test.

On 32-bit Operating Systems, install psyco, it gives a 50%
boost (``aptitude install python-psyco`` on Debian/Ubuntu OS).

On multi-CPU servers, the Python GIL is getting infamous.
To maximize FunkLoad's CPU usage, you need to set the CPU affinity.
``taskset -c 0 fl-run-bench`` is always faster than ``fl-run-bench``.
Using one bench runner process per CPU is a work around to use the
full server power.

Use multiple machines to perform the load test, see the next section.


How can I run multiple benchers ?
-------------------------------

Bench result files can be merged by the ``fl-build-report`` command,
but how do you run multiple benchers?

There are many ways: 

* Use the new "distribute" mode (still in beta), it requires paramiko and
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
      * Channel timeout: None
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
     funkload_location=http://pypi.python.org/packages/source/f/funkload/funkload-1.17.0.tar.gz

  You can have multiple benchers per server by defining many workers with
  the same hostname in your configuration file. Add a workers section
  to your configuration file::

      [workers]
      hosts = host1cpu1 host1cpu2 host2cpu1 host2cpu2

  And then define these workers::

      [host1cpu1]
      host = host1
      username = user
      password = password

      [host1cpu2]
      host = host1
      username = user
      password = password

      [host2cpu1]
      host = host2
      username = user
      password = password

      [host2cpu2]
      host = host2
      username = user
      password = password

  When defining workers in the conf file you can alternatively specify a
  path to a private key file instead of writing your passwords in cleartext::

      [worker1]
      host = worker1
      username = user
      ssh_key = /path/to/my_key_name.private.key

  Then run adding just the --distribute option::

      $ fl-run-bench -c 1:2:3 -D 5 -f --simple-fetch  test_Simple.py Simple.test_simple --distribute -u http://target/

  If your node uses a non standard ssh port (for instance, if you are using
  ssh tunneling) you can use::

      [host1]
      host = host1:port

  By default, the timeout on the ssh channel with the workers is set to
  None (ie timeouts are disabled). To configure the number of seconds to
  wait for a pending read/write operation before raising socket.timeout
  you can use::

       [distribute]
       channel_timeout = 250

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


How can I accept gzip content encoding ?
---------------------------------------

You just need to add the appropriate header::

     self.setHeader('Accept-encoding', 'gzip')


How can I mix different scenarios in a bench ?
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

How can I modify a report ?
--------------------------

The report is in `reStructuredText 
<http://docutils.sourceforge.net/rst.html>`_, the ``index.rst`` can be
edited by hand. The HTML version can then be rebuilt::

    rst2html --stylesheet=funkload.css   index.rst --traceback > index.html

Charts are built with gnuplot. The gplot script files are present in the
report directory. To rebuild the pages charts, for instance::

    gnuplot pages.gplot

Since FunkLoad 1.15 you can also use an org-mode_ output to edit or
extend the report before exporting it as a PDF.


How can I automate stuff ?
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


How can I write fluent tests ?
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


How can I get release announcements ?
---------------------------------------

Watch the github repository:
https://github.com/nuxeo/FunkLoad



.. _org-mode: http://orgmode.org/
