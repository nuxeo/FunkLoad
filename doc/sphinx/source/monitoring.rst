The monitor server
===================

If you want to monitor a linux server health during the bench, you
have to run a monitor xmlrpc server on the target server, this require
to install the FunkLoad package.

On the server side you need to install the FunkLoad tool then launch
the server using a configuration file (example in the demo_/simple
folder.)::

  fl-monitor-ctl monitor.conf start

  # more info
  fl-monitor-ctl --help


On the bench host side setup your test configuration like this::

  [monitor]
  hosts = server.to.test.com

  [server.to.test.com]
  description = The web server
  port = 8008

Then run the bench, the report will include server stats.

Note that you can monitor multiple hosts and that the monitor is linux
specific.

A new contribution will be added in 1.15 to extend the monitoring, it
will comes with Nagios and Munin plugins.

.. _demo: http://svn.nuxeo.org/trac/pub/browser/funkload/trunk/src/funkload/demo/
