Benchmarks concepts
=====================


The same FunkLaod test can be turned into a load test, just by invoking the
bench runner ``fl-run-bench``.

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

FunkLoad_ can execute many cycles with different number of CUs
(Concurrent Users), this way you can find easily the maximum number of
users that your application can handle.

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




Tips
~~~~~

Here are few remarks/advices to obtain workable metrics.

* Since it uses significant CPU resources, make sure that performance
  limits are not hit by FunkLoad_ before your server's limit is
  reached.  Check this by launching a bench from another host.

* Having a cycle with one user gives a usefull reference.

* A bench is composed of a benching test (or scenario) run many
  times. A good benching test should not be too long so you have a
  higher testing rate (that is, more benching tests can come to their
  end).

* The cycle duration for the benching test should be long enough.
  Around 5 times the duration of a single benching test is a value
  that is usually a safe bet. You can obtain this duration of a single
  benching test by running ``fl-run-test myfile.py
  MyTestCase.testSomething``.

  Rationale : Normally a cycle duration of a single benching test
  should be enough. But from the testing platform side if there are
  more than one concurrent user, there are many threads to start and
  it takes some time. And on from the tested platform side it is
  common that a benching test will last longer and longer as the
  server is used by more and more users.

* You should use many cycles with the same step interval to produce
  readable charts (1:10:20:30:40:50:60 vs 1:10:100)

* A benching test must have the same number of page and in the same
  order.

* Use a Makefile to make reproductible bench.

* There is no debug option while doing a bench (since this would be
  illegible with all the threads). So, if a bench fails (that is using
  `fl-run-bench`), use ``fl-run-test -d`` to debug.


.. _FunkLoad: http://funkload.nuxeo.org/

