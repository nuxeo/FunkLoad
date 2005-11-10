====================
FunkLoad demo/simple
====================
$Id$

This is a simple FunkLoadTestCase demonstration.

It requires an web test server (configuration is done for an apache2
default install)

WARNING: You should *not* run this script against a server that is not under
your responsablity as it can result a DOS in bench mode.

1/ Modify the Simple.conf file

  Set the [main] url and pages keys

2/ Test it

   verbose mode::

     fl-run-test -v test_Simple.py

   debug mode::

     fl-run-test -d test_Simple.py

   view the downloaded page in real time using firefox::

     fl-run-test -V test_Simple.py

   check performance of a single page::

     fl-run-test -l 4 -n 100 test_Simple.py


3/ Bench it

   Start a monitord server to log server activities::

     fl-monitor-ctl monitor.conf start

   Bench it with few cycles::

     fl-run-bench -c 1:25:50:75 test_Simple.py Simple.test_simple

   Note that for correct interpretation you should run the FunkLoad bencher
   in a different host than the server, the server should be 100% dedicated
   to the application.

   If you want to bench with more than 200 users, you need to reduce the
   default stack size used by a thread, for example try a `ulimit -s 2048`
   before running the bench.

   Performance limits are hit by FunkLoad before apache's limit is reached,
   since it uses significant CPU resources.

4/ Build the report::

   fl-build-report --html simple-bench.xml


