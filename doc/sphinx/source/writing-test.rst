Writing test script
======================

**DRAFT - DRAFT - DRAFT - DRAFT**

Submiting requests
-------------------

The FunkLoadTestCase_ API:

* HTTP GET

  Here are some example on how to perform a get request::

     self.get(self.server_url + "/search?query=foo", description="Search")
     self.get(self.server_url + "/search", params=[['query', 'foo']],
              description="Search again")
     self.get(self.server_url + "/logout", description="Logout ")


* HTTP POST
   
  Here are some example on how to perform a post request::
     
     from webunit.utility import Upload
     from funkload.utils import Data
     ...
     # simple post
     self.post(self.server_url + "/login",
               params=[['user_name', 'scott'],
                       ['user_password', 'tiger']],
               description="Login as scott")

     # upload a file
     self.post(self.server_url + "/uploadFile",
               params=[['file', Upload('/tmp/foo.pdf'),
                       ['title', 'foo file']],
               description="Upload a file")
 
     # post xml
     self.post(self.server_url + "/xmlAPI",
               params=Data('text/xml', '<foo>bar</foo>'),
               description="Call xml API")

* HTTP PUT/DELETE::

     from funkload.utils import Data
     ...
     self.put(self.server_url + '/xmlAPI", 
              Data('text/xml', '<foo>bar</foo>', 
              description="Put query")
     self.delete(self.server_url + '/some/rest/path/object',
                 description="Delete object')


* xmlrc::
  
     self.xmlrpc(server_url, 'getStatus',
      		 description="Check getStatus")
  
You should always set a description when submiting a request, this
improves the readability of the report.

If you run your test in debug mode you can see what is being send, the 
debug mode is activated with the ``--debug --debug-leve=3`` options.

By running your test with the ``-V`` option you will see each response
in your running instance of firefox.


Adding assertion
-------------------

After each request you should add an assertion to make sure you are on 
the expected page.

You can check the response content using ``self.getBody()`` ::

   self.get(server_url, description="home page")
   self.assert_('Welcome' in self.getBody(), "Wrong home page")

You can check for the last URL (including any redirects)::

     self.post(self.server_url + "/login",
               params=[['user_name', 'scott'],
                       ['user_password', 'tiger']],
               description="Login as scott")
     self.assert_('dashboard' in self.getLastURL(), "Login failure")

You can check an expected HTTP return code::
    
     ret = self.get(...)
     self.assert_(ret.code in [200, 301], "expecting a 200 or 301")


* TODO: token extraction

* TODO: interpreting html
  getDOM
  listHref ...
  beautiful soup ...

Configuration file
---------------------

You can get information from the configuration file, using the
approriate ``self.conf_get*(section, key)`` methods.

TODO: add code snippet

Sharing credentials
---------------------

TODO: The credentials server, start/stop and API.
::

  from funkload.utils import xmlrpc_get_credential
  ...
  # get the host and port from the config file  
  credential_host = self.conf_get('credential', 'host')
  credential_port = self.conf_getInt('credential', 'port')
  # get a login/pwd from the members group
  login, password = xmlrpc_get_credential(credential_host,
			                  credential_port,
                                          'members')
        



Generating data
------------------

TODO: finish
::

    from funkload import Lipsum

    print 'Word: %s\n' % (Lipsum().getWord())
    print 'UniqWord: %s\n' % (Lipsum().getUniqWord())
    print 'Subject: %s\n' % (Lipsum().getSubject())
    print 'Subject uniq: %s\n' % (Lipsum().getSubject(uniq=True))
    print 'Sentence: %s\n' % (Lipsum().getSentence())
    print 'Paragraph: %s\n' % (Lipsum().getParagraph())
    print 'Message: %s\n' % (Lipsum().getMessage())
    print 'Phone number: %s\n' % Lipsum().getPhoneNumber()
    print 'Phone number fr short: %s\n' % Lipsum().getPhoneNumber(
        lang="fr", format="short")
    print 'Phone number fr medium: %s\n' % Lipsum().getPhoneNumber(
        lang="fr", format="medium")
    print 'Phone number fr long: %s\n' % Lipsum().getPhoneNumber(
        lang="fr", format="long")
    print 'Phone number en_US short: %s\n' % Lipsum().getPhoneNumber(
        lang="en_US", format="short")
    print 'Phone number en_US medium: %s\n' % Lipsum().getPhoneNumber(
        lang="en_US", format="medium")
    print 'Phone number en_US long: %s\n' % Lipsum().getPhoneNumber(
        lang="en_US", format="long")
    print 'Address default: %s' % Lipsum().getAddress()


Adding information to the report
----------------------------------

TODO: finish

* At runtime from the API using ``self.addMetadata``

* At runtime from the command line ``--label``



.. _FunkLoadTestCase: http://public.dev.nuxeo.com/~ben/funkload/sphinx/api/core_api.html#module-funkload.FunkLoadTestCase 
