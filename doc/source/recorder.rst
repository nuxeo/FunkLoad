Recording a test
===============================

You can use ``fl-record`` to record your browser activity, this
requires the TCPWatch_ python proxy. See installation_ for
information on how to install TCPWatch_.

1. Start the recorder::

    fl-record basic_navigation


  This will output something like this::

    Hit Ctrl-C to stop recording.
    HTTP proxy listening on :8090
    Recording to directory /tmp/tmpaYDky9_funkload.


2. Setup your browser proxy and play your scenario

  * set `localhost:8090` as your browser's HTTP proxy
    http://www.wikihow.com/Change-Proxy-Settings

  * Play your scenario using your browser

  * Hit Ctrl-C to stop recording::

      ^C
      # Saving uploaded file: foo.png
      # Saving uploaded file: bar.pdf
      Creating script: ./test_BasicNavigation.py.
      Creating configuration file: ./BasicNavigation.conf.

    You now have a new python class in ``test_BaiscNavigation.py`` and
    a configuration file. Refer to the tutorial_ to
    learn how to turn it into a workable test.

To add more requests to your test, just run ``fl-record`` again, without
parameters, perform your requests with the browser, then hit
Ctrl-C. ``fl-record`` will output code ready to be pasted into your
test case.
::

    $ fl-record
    HTTP proxy listening on :8090
    Recording to directory /tmp/tmptOl7jh_funkload.
    ^C
    TCPWatch finished. 
          self.post(server_url + "/booking/register.seam", params=[
            ['registration', 'registration'],
            ['registration:usernameDecorate:username', 'scott'],
            ['registration:nameDecorate:name', 'scott'],
            ['registration:passwordDecorate:password', 'tiger'],
            ['registration:verifyDecorate:verify', 'tiger'],
            ['registration:register', 'Register'],
            ['javax.faces.ViewState', '_id6407']],
            description="Post /booking/register.seam")
    $   
  

Note that ``fl-record`` :

* works fine with multi-part encoded form and file upload.

* automaticly handles a JSF Myfaces token, which enables it to easily record
  and play any JBoss Seam application.

* doesn't support HTTPS. The work around is to first record a scenario
  on HTTP, and then change the `url` back to `https` in the
  configuration file.


.. _FunkLoad: http://funkload.nuxeo.org/
.. _TCPWatch: http://hathawaymix.org/Software/TCPWatch/
.. _tutorial: tutorial.html
.. _installation: installation.html
