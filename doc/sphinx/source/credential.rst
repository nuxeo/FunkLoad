The credential server
=======================

If you are writing a bench that requires to be logged with different
users FunkLoad provides an xmlrpc credential server to serve
login/pwd between the different threads.

It requires 2 files with the same pattern as unix /etc/passwd and
/etc/group. The password file have the following format::

  login1:pwd1
  login2:pwd2
  ...

The group file format is::

  group1:user1, user2
  group2:user2
  # you can split group declaration
  group1:user3
  ...

The credential server use a configuration file to point to the user
and group file and define the listening port::
  
  [server]
  host=localhost
  port=22207
  credentials_path=passwords.txt
  groups_path=groups.txt
  # to loop over the entire file set the value to 0
  loop_on_first_credentials=0


To start the credential server::

  fl-credential-ctl credential.conf start

You can find more option in the usage_ page.

In your test case to get a credential::
       from funkload.utils import xmlrpc_get_credential	
       ...
       login, pwd = xmlrpc_get_credential(host, port, "group2")

.. _usage: usage-fl-credential-ctl.html


