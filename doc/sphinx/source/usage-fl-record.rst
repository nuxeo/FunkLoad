Recorder ``fl-record`` usage
==============================

fl-record [options] [test_name]

fl-record launch a TCPWatch proxy and record activities, then output
a FunkLoad script or generates a FunkLoad unit test if test_name is specified.

The default proxy port is 8090.

Note that tcpwatch.py executable must be accessible from your env.

See http://funkload.nuxeo.org/ for more information.

Examples
-----------
  fl-record foo_bar
                        Run a proxy and create a FunkLoad test case,
                        generates test_FooBar.py and FooBar.conf file.
                        To test it:  fl-run-test -dV test_FooBar.py
  fl-record -p 9090
                        Run a proxy on port 9090, output script to stdout.
  fl-record -i /tmp/tcpwatch
                        Convert a tcpwatch capture into a script.


Options
---------
--version               show program's version number and exit
--help, -h              show this help message and exit
--verbose, -v           Verbose output
--port=PORT, -p PORT    The proxy port.
--tcp-watch-input=TCPWATCH_PATH, -i TCPWATCH_PATH
                        Path to an existing tcpwatch capture.
--loop=LOOP, -l LOOP    Loop mode.
