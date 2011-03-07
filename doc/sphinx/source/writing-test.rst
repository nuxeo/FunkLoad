Writing test script
======================

Submiting requests
-------------------

* HTTP GET

  Here are some example on how to perform a get request::

     self.get(self.server_url + "/logout", description="Logout ")
     self.get(self.server_url + "/search?query=foo", 
              description="Search with params in the URL")
     self.get(self.server_url + "/search", params=[['query', 'foo']],
              description="Search using params")


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
 
     # post with text/xml content type
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


* xmlrc helper::
  
     ret = self.xmlrpc(server_url, 'getStatus',
      		 description="Check getStatus")


You should set a description when submiting a request, this improves
the readability of the report.

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

You can check an expected HTTP return code::
    
     ret = self.get(...)
     self.assert_(ret.code in [200, 301], "expecting a 200 or 301")

Note that FunkLoad is testing the HTTP return code by default,
assuming that a different code thant 200:301:302 is an error, this can
be changed using the ok_codes parameters or config file option::

     ret = self.get(self.server_url + '/404.hmtl', ok_codes=[200, 404],
                description="Accept 404")
     self.assert_(ret.code == 404)


You can check the returned URL wich may be different if you have been
redirected::

     self.post(self.server_url + "/login",
               params=[['user_name', 'scott'],
                       ['user_password', 'tiger']],
               description="Login as scott")
     self.assert_('dashboard' in self.getLastURL(), "Login failure")


Basic Authentication
-----------------------

::

  self.setBasicAuth('scott', 'tiger')
  self.get(self.server_url, description="Get using basic auth")
  # remove basic auth
  self.clearBasicAuth()


Extra headers
---------------

::

   self.setHeader('Accept-Language', 'de')
   # this header is set for all the next requests
   ...
   # Remove all additional headers
   self.clearHeaders()


Extracting information
------------------------

At some point you will need to extract information from the
response. When possible the best way to do it is using string find or
regex. Parsing XML or HTML has such an extra cost that it will prevent
you to submit hight load.

FunkLoad comes with a simple extract_token working with string finds::

    from FunkLoad.utils import extract_token
    ...
    token = extract_token(self.getBody(), 'id="mytoken" value="', '"')

Of course for pure functional testing you can use FunkLoad helpers::
 
       ret = self.get(self.server_url, description="Get some page")
       urls = self.listHref(url_pattern="view_document",
                            content_pattern="View")
       base_url = self.getLastBaseUrl()

Or the WebUnit minidom::

       title = self.getDom().getByName('title')[0].getContents()


Or any python XML/HTML processing library including beautiful soup.


Using the configuration file
---------------------------------

You can get information from the configuration file, using the
approriate ``self.conf_get*(section, key)`` methods::

   # Getting value from the main section
   value = self.get_conf('main', 'key', 'default')
   count = self.get_confInt('main', 'nb_docs', 10)
   percent = self.get_confFloat('main', 'percent', 5.5)
   items = self.get_confList('main', 'names')
   # The names in the conf file are separated with a semi column
   # names=name1:name2:name3


Sharing credentials
---------------------

If you need to share credentials among your tests you can use the FunkLoad `credential server <./credential.html>`_. Here is an example to request credentials::

  from funkload.utils import xmlrpc_get_credential
  ...
  # get the credential host and port from the config file  
  credential_host = self.conf_get('credential', 'host')
  credential_port = self.conf_getInt('credential', 'port')
  # get a login/pwd from the members group
  login, password = xmlrpc_get_credential(credential_host,
			                  credential_port,
                                          'members')

Since FunkLoad 1.15 the credential server can return a sequence::
      
  from funkload.utils import xmlrpc_get_seq
  ...  
  seq = xmlrpc_get_seq()


The sequence starts with 0 but can be initialized in the credential
server configuration file.



Generating data
------------------

FunkLoad comes with a simple text random generator a Lipsum like::

    >>> from funkload.Lipsum import Lipsum
    >>> print 'Word: %s\n' % (Lipsum().getWord())
    Word: albus
        
    >>> print 'UniqWord: %s\n' % (Lipsum().getUniqWord())
    UniqWord: fs3ywpxg
    
    >>> print 'Subject: %s\n' % (Lipsum().getSubject())
    Subject: Fulvus orientalis albus hortensis dorsum
    
    >>> print 'Subject uniq: %s\n' % (Lipsum().getSubject(uniq=True))
    Subject uniq: F26v3y fuscus variegatus dolicho caulos cephalus
    
    >>> print 'Sentence: %s\n' % (Lipsum().getSentence())
    Sentence: Argentatus arvensis diplo familiaris tetra trich ; vulgaris montanus folius tetra so echinus, trich pteron phyton so brachy officinalis.
    
    >>> print 'Paragraph: %s\n' % (Lipsum().getParagraph())
    Paragraph: Sit pteron, tetra dermis viridis cyanos. Tetra novaehollandiae cyanos indicus major ortho archaeos montanus. Viridis cephalus, niger, it occidentalis volans delorum sativus gaster arctos phyllo dermis archaeos. Archaeos montanus erythro mauro minimus biscortborealis occidentalis morphos biscortborealis silvestris punctatus variegatus ! phyton mauro hexa.
    
    >>> print 'Message: %s\n' % (Lipsum().getMessage())
    Message: Familiaris fulvus flora xanthos tomentosus lutea lineatus ?, dolicho campus maculatus ad platy gaster punctatus. So pachys rufus tris, trich montanus so variegatus cristatus orientalis diplo minimus. Petra lateralis bradus, chilensis unus officinalis striatus ad. Xanthos dolicho arvensis ennea tinctorius phyton, sit arctos mauro.
    
    Dermis zygos, ventrus oeos glycis dulcis chloreus verrucosus lineatus, pteron sinensis officinalis cyanos. Cephalus occidentalis verrucosus echinus ; lateralis protos tinctorius punctatus parvus volans. Pteron palustris gaster ad tomentosus platy arctos rhytis pedis indicus mono. Chilensis phyton, ; hortensis fuscus aquam.
    
    Variegatus deca fuscus petra rubra biscortborealis familiaris sativus leucus xanthos phyton argentatus novaehollandiae brachy. Mauro rufus saurus deca oeos thrix rostra archaeos, ortho rufus phyllo cristatus campus rostra oleum xanthos chilensis. Archaeos protos tinctorius gaster arctos niger niger variegatus thrix, mauro arctos verrucosus ennea delorum. Pedis melanus mauro occidentalis pratensis chilensis arctos gaster noveboracensis, rufus ennea minimus saurus dermis fulvus octa.
    
    >>> print 'Phone number: %s\n' % Lipsum().getPhoneNumber()
    Phone number: 07 20 25 56 06
    
    >>> print 'Phone number fr short: %s\n' % Lipsum().getPhoneNumber(
    ...     lang="fr", format="short")
    Phone number fr short: 0787117995
    
    >>> print 'Phone number fr medium: %s\n' % Lipsum().getPhoneNumber(
    ...     lang="fr", format="medium")
    Phone number fr medium: 07 88 31 30 06
    
    >>> print 'Phone number fr long: %s\n' % Lipsum().getPhoneNumber(
    ...     lang="fr", format="long")
    Phone number fr long: +33 (0)7 41 08 36 56
    
    >>> print 'Phone number en_US short: %s\n' % Lipsum().getPhoneNumber(
    ...     lang="en_US", format="short")
    Phone number en_US short: 863-3655
    
    >>> print 'Phone number en_US medium: %s\n' % Lipsum().getPhoneNumber(
    ...     lang="en_US", format="medium")
    Phone number en_US medium: (327) 129-2863
    
    >>> print 'Phone number en_US long: %s\n' % Lipsum().getPhoneNumber(
    ...     lang="en_US", format="long")
    Phone number en_US long: +00 1 (283) 158-7134
    
    >>> print 'Address default: %s' % Lipsum().getAddress()
    Address default: 85 place Brevis
    99612 Trich


Adding information to the report
----------------------------------

* At runtime a bench can add metadata to the report using the
  setUpBench hook and the addMetadata method::
  
    def setUpBench(self):
       ret = self.get(self.server_url + "/getVersion", 
                      description="Get the server version")
       self.addMetadata('Application version', ret.getBody()) 

* At runtime from the command line using the ``--label`` option of the
  bench runner.

* After the bench using a file named ``funkload.metadata`` with a list
  of ``key:value``. At the moment this file is only used by the trend
  reports to add charts label and bench description.  This file must
  be put on the report directory::

    label: label used by trend report
    build: 666
    builtOn: hostname
    Text taken as description `using ReST power <http://url/>`__
    Can be multine text.


API
-----

More info on the API doc: FunkLoadTestCase_.


.. _FunkLoadTestCase: http://funkload.nuxeo.com/sphinx/api/core_api.html#module-funkload.FunkLoadTestCase 
