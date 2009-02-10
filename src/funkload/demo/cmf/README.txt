=================
FunkLoad demo/cmf
=================
$Id$

This is a simple CMF tests.

It requires a zope 2.7 or 2.8 test server running, you should *not* run this
script against a production server as it will try to create a CMF Site and
setup test accounts.

You need to have the CMF 1.5.4 products installed on your Zope server.

You need to edit the Cmf.conf configuration file to point to your zope
server (section main url key).

Then you need to edit the passwords.txt file to set the Zope admin credential.

If your zope admin is not called ``admin`` add your credential to the
`passwords.txt` file and edit the `groups.txt` file to add your login in the
``AdminZope`` group.

To run the test::

  fl-credential-ctl credential.conf start
  fl-run-test -v test_Cmf.py

You can view the debug information::

  fl-run-test -d test_Zope.py

If something goes wrong try to view the html output::

  fl-run-test -dV test_Zope.py


Note that all errors are logged in the xml output file ``cmf-test.xml``.
