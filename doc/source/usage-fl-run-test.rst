Test runner ``fl-run-test`` usage
====================================

fl-run-test [options] file [class.method|class|suite] [...]

fl-run-test launch a FunkLoad unit test.

A FunkLoad unittest use a configuration file named [class].conf, this
configuration is overriden by the command line options.

See http://funkload.nuxeo.org/ for more information.


Examples
----------
  fl-run-test myFile.py
                        Run all tests.
  fl-run-test myFile.py test_suite
                        Run suite named test_suite.
  fl-run-test myFile.py MyTestCase.testSomething
                        Run a single test MyTestCase.testSomething.
  fl-run-test myFile.py MyTestCase
                        Run all 'test*' test methods in MyTestCase.
  fl-run-test myFile.py MyTestCase -u http://localhost
                        Same against localhost.
  fl-run-test --doctest myDocTest.txt
                        Run doctest from plain text file (requires python2.4).
  fl-run-test --doctest -d myDocTest.txt
                        Run doctest with debug output (requires python2.4).
  fl-run-test myfile.py -V
                        Run default set of tests and view in real time each
                        page fetch with firefox.
  fl-run-test myfile.py MyTestCase.testSomething -l 3 -n 100
                        Run MyTestCase.testSomething, reload one hundred
                        time the page 3 without concurrency and as fast as
                        possible. Output response time stats. You can loop
                        on many pages using slice -l 2:4.
  fl-run-test myFile.py -e [Ss]ome
                        Run all tests that match the regex [Ss]ome.
  fl-run-test myFile.py -e '!xmlrpc$'
                        Run all tests that does not ends with xmlrpc.
  fl-run-test myFile.py --list
                        List all the test names.
  fl-run-test -h
                        More options.


Options
---------
--version               show program's version number and exit
--help, -h              show this help message and exit
--quiet, -q             Minimal output.
--verbose, -v           Verbose output.
--debug, -d             FunkLoad and doctest debug output.
--debug-level=DEBUG_LEVEL
                        Debug level 3 is more verbose.
--url=MAIN_URL, -u MAIN_URL
                        Base URL to bench without ending '/'.
--sleep-time-min=FTEST_SLEEP_TIME_MIN, -m FTEST_SLEEP_TIME_MIN
                        Minumum sleep time between request.
--sleep-time-max=FTEST_SLEEP_TIME_MAX, -M FTEST_SLEEP_TIME_MAX
                        Maximum sleep time between request.
--dump-directory=DUMP_DIR
                        Directory to dump html pages.
--firefox-view, -V      Real time view using firefox, you must have a running
                        instance of firefox in the same host.
--no-color              Monochrome output.
--loop-on-pages=LOOP_STEPS, -l LOOP_STEPS
                        Loop as fast as possible without concurrency on pages,
                        expect a page number or a slice like 3:5. Output some
                        statistics.
--loop-number=LOOP_NUMBER, -n LOOP_NUMBER
                        Number of loop.
--accept-invalid-links  Do not fail if css/image links are not reachable.
--simple-fetch          Don't load additional links like css or images when
                        fetching an html page.
--stop-on-fail          Stop tests on first failure or error.
--regex=REGEX, -e REGEX
                        The test names must match the regex.
--list                  Just list the test names.
--doctest               Check for a doc test.
--pause                 Pause between request, press ENTER to continue.
