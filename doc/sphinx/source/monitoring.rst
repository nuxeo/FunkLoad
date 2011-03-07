The monitor server
===================

If you want to monitor a linux server health during the bench, you
have to run a monitor xmlrpc server on the target server, this requires
to install a minimal FunkLoad package, on Debian/Ubunutu ::

    sudo aptitude install python-dev python-setuptools \
       python-webunit python-docutils
    sudo easy_install -f http://funkload.nuxeo.org/snapshots/ -U funkload

Then create a configuration file ``monitor.conf``::
  
  [server]
  host = <IP or FQDN>
  port = 8008
  interval = .5
  interface = eth0
  [client]
  host = <IP or FQDN>
  port = 8008

And start the monitor server::

  fl-monitor-ctl monitor.conf start


On the bench server add to your test configuration file the following section::

  [monitor]
  hosts = <IP or FQDN>

  [<IP or FQDN>]
  description = The application server
  port = 8008


Then run the bench, the report will include server stats.

Note that you can monitor multiple hosts and that the monitor is linux
specific.

A new contribution will be added in 1.16 to extend the monitoring, it
will enable to use Nagios or Munin plugins.
