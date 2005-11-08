==================
FunkLoad demo/zope
==================
$Id$

This is a simple ZopeTestCase demonstration.

It requires a zope 2.7 or 2.8 test server running, you should *not* run this
script against a production server as it will try to pack the main Zodb, and
setup the default Zope Examples.

Modify the Zope.conf funkload configuration file and set the zope server url
and admin credential ([main] section, url, admin_id and admin_pwd keys).

The test will setup the zope Examples and test them, then it will flush the
zope cache, pack the zodb and restart the zope server.

To run the test::

  fl-run-test -v test_Zope.py

You can view the debug information::

  fl-run-test -d test_Zope.py

