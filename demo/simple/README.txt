====================
FunkLoad demo/simple
====================
$Id$

This is a simple FunkLoadTestCase demonstration.

It requires an web test server (configuration is done for an apache-2
default install)

WARNING: You should *not* run this script against a server that is not under
your responsablity as it can result a DOS in bench mode.

1/ Modify the Simple.conf file

  set the [main] url and pages keys

2/ Test it

   verbose mode::

     fl-run-test -cv test_Simple.py

   debug mode::

     fl-run-test -cd test_Simple.py

   view the downloaded page in real time using firefox::

     fl-run-test -cV test_Simple.py

3/ Bench it

   Start a monitord server to log server activities:

     fl-monitor-ctl monitor.conf start

   Bench it with few cycle

     fl-run-bench -c 1:5 test_Simple.py Simple.test_simple

   Bench it with more cycle in color mode

     fl-run-bench -c 1:25:50:75 -C test_Simple.py Simple.test_simple


4/ Build the report::

   fl-build-report simple-bench.xml --html
