Installation
===============

This document describes how to install the FunkLoad_ tool.

.. toctree::


Quick installation guide for Debian and Ubuntu
-----------------------------------------------

With Debian Lenny or Ubuntu 8.10, 9.04, 10.04 ..., you can install the
latest snapshot this way ::

  sudo aptitude install python-dev python-xml python-setuptools \
       python-webunit python-docutils gnuplot
  sudo aptitude install tcpwatch-httpproxy --without-recommends
  sudo easy_install -f http://funkload.nuxeo.org/snapshots/ -U funkload

To install the latest stable release replace the last line with ::
 
  sudo easy_install -U funkload

If you want to test the new beta distributed mode (since 1.14.0) you
need to install paramiko and virtualenv::
  
  sudo aptitude install python-paramiko, python-virtualenv

That's all.

Unfortunatly the FunkLoad_ Debian package (old 1.6.2-3) does not work properly.

You can find an old 1.10.0 `Debian package here <http://funkload.nuxeo.org/debian/funkload_1.10.0_all.deb>`_.



Other OS
----------

Some parts are OS specific:

* the monitor server works only on Linux
* the credential server is a unix daemon but can run on windows if launched
  in debug mode (-d)

Under windows there is a trick to install docutils (see below), you may
also rename the scripts with a ``.py`` extension.


Required packages
~~~~~~~~~~~~~~~~~~~

* libexpat1

* funkload 1.14.0 requires python >= 2.5

* python 2.4 is required by the test runner only if you want to launch
  python doctest, other stuff work fine with a python 2.3.5.
  python >= 2.5 are supported with funkload > 1.6.0

* python distutils

* python xml

* EasyInstall_, either use a package or download ez_setup.py_, and run it::

    cd /tmp
    wget http://peak.telecommunity.com/dist/ez_setup.py
    sudo python ez_setup.py

  This will download and install the appropriate setuptools egg for your
  Python version.


Optional packages
~~~~~~~~~~~~~~~~~~

* To produce charts with FunkLoad >= 1.9.0: gnuplot 4.2, either use a
  package or visit the http://www.gnuplot.info/ site.

  gnuplot (or wgnuplot for win) must be in the executable path.

* The recorder use TCPWatch_ which is not yet available using easy_install::

    cd /tmp
    wget http://hathawaymix.org/Software/TCPWatch/tcpwatch-1.3.tar.gz
    tar xzvf tcpwatch-1.3.tar.gz
    cd tcpwatch
    python setup.py build
    sudo python setup.py install


Installation
~~~~~~~~~~~~~

Easy installation
__________________

* Install the latest stable package::

    sudo easy_install -U funkload

  This will install FunkLoad_, webunit_ and docutils_ eggs.

* Install the latest snapshot version::

    sudo easy_install -f http://funkload.nuxeo.org/snapshots/ -U funkload

* Install the development version

  If you want to try the latest unstable sources from svn ::

    easy_install -eb /tmp funkload==dev
 
  or::

    svn co http://svn.nuxeo.org/pub/funkload/trunk /tmp/funkload

  then::

    cd /tmp/funkload/
    python setup.py build
    sudo python setup.py install


Installing without sudo power
______________________________

This can be done using buildout::

  tar zxf funkload-1.13.0.tar.gz
  cd funkload-1.13.0
  python bootstrap.py
  bin/buildout

Then your executable are ready on the bin directory.


Installing without network access
___________________________________

Transfer all the archives from http://funkload.nuxeo.org/3dparty/ in a
directory::

  mkdir -p /tmp/fl
  cd /tmp/fl
  wget -r -l1 -nd http://funkload.nuxeo.org/3dparty/
  
Transfer the latest FunkLoad package.
::
 
  # get setuptools package and untar
  python setup.py install
  
  easy_install docutils*
  easy_install tcpwatch*
  easy_install webunit*
  easy_install funkload*

  

Test it
--------

Install the FunkLoad_ examples::

  fl-install-demo

Go to the demo/xmlrpc folder then::

  cd funkload-demo/xmlrpc/
  make test

To test benching and report building just::

  make bench

See ``funkload-demo/README`` for others examples.



Problems ?
-----------

* got a ::

    error: invalid Python installation: unable to open /usr/lib/python2.4/config/Makefile (No such file or directory)

  Install python2.4-dev package.

* easy_install complains about conflict::

    ...
    /usr/lib/site-python/docutils

    Note: you can attempt this installation again with EasyInstall, and use
    either the --delete-conflicting (-D) option or the
    --ignore-conflicts-at-my-risk option, to either delete the above files
    and directories, or to ignore the conflicts, respectively.  Note that if
    you ignore the conflicts, the installed package(s) may not work.
    -------------------------------------------------------------------------
    error: Installation aborted due to conflicts


  If FunkLoad_, webunit_ or docutils_ were previously installed without
  using EasyInstall_.  You need to reinstall the package that raises the
  conflict with the ``--delete-conflicting`` option, see easy_install_
  documentation.

* If you still have conflict try to remove FunkLoad_ from your system::

    easy_install -m funkload
    rm -rf /usr/lib/python2.3/site-packages/funkload*
    rm -rf /usr/local/funkload/
    rm /usr/local/bin/fl-*
    rm /usr/bin/fl-*

  then reinstall

* easy_install ends with::

    error: Unexpected HTML page found at
    http://prdownloads.sourceforge.net...

  Source Forge has changed their donwload page you need to update your
  setuptools::

     sudo easy_install -U setuptools

* Failed to install docutils 0.4 with easy_install 0.6a9 getting a::

    ...
    Best match: docutils 0.4
    Downloading http://prdownloads.sourceforge.net/docutils/docutils-0.4.tar.gz?download
    Requesting redirect to (randomly selected) 'mesh' mirror
    error: No META HTTP-EQUIV="refresh" found in Sourceforge page at http://prdownloads.sourceforge.net/docutils/docutils-0.4.tar.gz?use_mirror=mesh

 It looks like sourceforge change their download page again :(

 - download manually the docutils tar gz from
   http://prdownloads.sourceforge.net/docutils/docutils-0.4.tar.gz?download
 - then ``sudo easy_install /path/to/docutils-0.4.tar.gz``



* When testing ``make test`` return ::

    ### credentialctl: Stopping credential server.
    python: can't open file '/usr/lib/python2.4/site-packages/funkload-1.2.0-py2.4.egg/funkload/credentialctl.py': [Errno 20] Not a directory

  Starting with FunkLoad_ 1.2.0 scripts are installed in /usr/bin, previously
  they were in /usr/local/bin, you need to remove them::

    sudo rm /usr/local/bin/fl-*


* While runing a test you got ::

    Traceback (most recent call last):
    File "/usr/local/bin/fl-run-test", line 8, in <module>
      load_entry_point('funkload==1.11.0', 'console_scripts', 'fl-run-test')()
    File "build/bdist.linux-i686/egg/funkload/TestRunner.py", line 478, in main
    File "build/bdist.linux-i686/egg/funkload/TestRunner.py", line 337, in __init__
    File "build/bdist.linux-i686/egg/funkload/TestRunner.py", line 347, in loadTests
    File "/usr/lib/python2.6/doctest.py", line 2412, in DocFileSuite
      suite.addTest(DocFileTest(path, **kw))
    File "/usr/lib/python2.6/doctest.py", line 2331, in DocFileTest
      doc, path = _load_testfile(path, package, module_relative)
    File "/usr/lib/python2.6/doctest.py", line 219, in _load_testfile
      return open(filename).read(), filename
    IOError: [Errno 2] No such file or directory: 'path/to/your/testcase'

  This means that your test file can not be loaded as a python module, (may
  be due to import error) FunkLoad then badly report it as an invalid doc
  test file.

  To view the original error just run the testcase using python instead of
  fl-run-test (``python your_test_case.py``).

  This is fixed since 1.14.


.. _FunkLoad: http://funkload.nuxeo.org/
.. _webunit: http://mechanicalcat.net/tech/webunit/
.. _demo: http://svn.nuxeo.org/trac/pub/browser/funkload/trunk/funkload/demo/
.. _EasyInstall: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall#command-line-options
.. _ez_setup.py: http://peak.telecommunity.com/dist/ez_setup.py
.. _docutils: http://docutils.sourceforge.net/
.. _TCPWatch: http://hathawaymix.org/Software/TCPWatch/


.. Local Variables:
.. mode: rst
.. End:
.. vim: set filetype=rst:

