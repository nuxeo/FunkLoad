FAQ
====

**DRAFT - DRAFT - DRAFT - DRAFT**

How to submit high load ?
---------------------------

- GIL limits on multi CPU arch
  - ``taskset -c 0 fl-run-bench`` is always faster than ``fl-run-bench``
  - work around using CPU affinity and multiple bench runner
- High load works fine for IO bound test, not on CPU bould test
- How to prevent CPU bound tests:
  - ``--simple-fetch`` + explicit get
  - limit any html/xml parsing, getDOM, beautiful soup
  - use find/regexp
  - prepare your data on setUp hooks

How to run multiple bencher ?
-----------------------------

Reports can be merged but how to run multiple bencher ?

- The new distribute mode (beta), requires paramiko and virtualenv, it
  adds three new command line options:

   * ``--distributed``: to enable distributed mode
   * ``--distributed-workers=user:password@host1,user:password@host2...``
     (user:password can be skipped if using pub-key)
   * ``--is-distributed``: an internal only option to be used so that
     'worker' nodes don't for instance, start monitoring the
     hosts. this can be generally used to signal to a worker node that
     its only a 'worker' :)

- BenchMaster http://pypi.python.org/pypi/benchmaster

- Old school pssh/Makefile::
   # clean all node workspaces
   parallel-ssh  -h hosts.txt rm -rf /tmp/ftests/
 
   # distribute tests
   parallel-scp -h hosts.txt -r ftests /tmp/ftests
   
   # launch a bench
   parallel-ssh -h hosts.txt -t -1 -o bench "(cd /tmp/ftests&& make bench 
   URL=http://target/)"
   
   # get the results
   parallel-slurp -h hosts.txt -o out -L results-`date -u '+%Y%m%d-%H%M%S'` 
   -r /tmp/ftests/report .
    
   # build the report with fl-build-report, it supports the results merging 
   
- Fabric http://tarekziade.wordpress.com/2010/12/09/funkload-fabric-quick-and-dirty-distributed-load-system/

How to mix different scenarii in a bench ?
-------------------------------------------

- example of percent and fixed number of threads

::
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

- limitation of the details report

How to modify a report ?
--------------------------

- the report is in reStructuredText
- gnuplot

How to automate stuff ?
-----------------------

Makefile usage example

How to write fluent tests ?
-----------------------------

- Nuxeo DM example http://hg.nuxeo.org/nuxeo/nuxeo-distribution/file/5b9d9e397beb/nuxeo-distribution-dm/ftest/funkload/README.txt

:: 
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
     

