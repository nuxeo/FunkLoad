=================
FunkLoad demo/cps
=================
$Id$

This is a CPSTestCase demonstration.

It requires a zope 2.7 or 2.8 test server running.

WARNING: You should *not* run this script against a production server as it
will create test accounts and documents.

1/ Modify the CPSBasicNavigation.conf file

  set the [main] url, the base url (ex: http://localhost:8080) should
  point to an existing running zope server, the cps id (/fl_cps) will be
  created by the test.

2/ Modify the passwords.txt file

   This file contains the test users credentials. You need to setup the
   zope admin and cps manager password.

   fl_* accounts will be created by the test but you can change their password.

3/ Run the credential server

   The tests need credentials that are served by a credential server::

     fl-credential-ctl credential.conf start

4/ Run the tests::

   fl-run-test -cv test_CPSBasicNavigation.py


5/ Playing

   to debug a test::

     fl-run-test -cd test_CPSBasicNavigation.py CPSBasicNavigation.test_30_reader_anonymous

   to view the downloaded page in real time:

     fl-run-test -cvV test_CPSBasicNavigation.py CPSBasicNavigation.test_30_reader_anonymous

   to run the whole test in a different server:

     fl-run-test -cv -u http://localhost:8080/fl_test2 test_CPSBasicNavigation.py
