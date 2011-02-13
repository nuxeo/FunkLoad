Writing test script
======================

**DRAFT - DRAFT - DRAFT - DRAFT**

Submiting requests
-------------------

The FunkLaodTestCase_ API:

* get
* post

  - upload file
  - submit data

* put/delete
* xmlrc

* Always use description in post/get/put/delete/xmlrpc, this improves
  the readability of the report.


Adding assertion
-------------------

* 'foo' in self.getBody()
* ret code
* token extraction
* interpreting html
  listHref ...
  beautiful soup ...

Configuration file
---------------------

* using the configuration file (conf_getInt)

Sharing credentials
---------------------

The credentials server, start/stop API.

Generating data
------------------

Lipsum module.


Adding information to the report
----------------------------------

* At runtime from the API using addMetadata
* At runtime from the command line --label



.. _FunkLoadTestCase: http://public.dev.nuxeo.com/~ben/funkload/sphinx/api/core_api.html#module-funkload.FunkLoadTestCase 
