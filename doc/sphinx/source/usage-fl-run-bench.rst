Bench runner ``fl-run-bench`` usage
=====================================

fl-run-bench [options] file class.method

fl-run-bench launch a FunkLoad unit test as load test.

A FunkLoad unittest use a configuration file named [class].conf, this
configuration is overriden by the command line options.

See http://funkload.nuxeo.org/ for more information.

Examples
--------
  fl-run-bench myFile.py MyTestCase.testSomething
                        Bench MyTestCase.testSomething using MyTestCase.conf.
  fl-run-bench -u http://localhost:8080 -c 10:20 -D 30 myFile.py \
      MyTestCase.testSomething
                        Bench MyTestCase.testSomething on localhost:8080
                        with 2 cycles of 10 and 20 users during 30s.
  fl-run-bench -h
                        More options.


Options
--------

--version               show program's version number and exit
--help, -h              show this help message and exit
--url=MAIN_URL, -u MAIN_URL
                        Base URL to bench.
--cycles=BENCH_CYCLES, -c BENCH_CYCLES
                        Cycles to bench, this is a list of number of virtual
                        concurrent users, to run a bench with 3 cycles with 5,
                        10 and 20 users use: -c 2:10:20
--duration=BENCH_DURATION, -D BENCH_DURATION
                        Duration of a cycle in seconds.
--sleep-time-min=BENCH_SLEEP_TIME_MIN, -m BENCH_SLEEP_TIME_MIN
                        Minimum sleep time between requests.
--sleep-time-max=BENCH_SLEEP_TIME_MAX, -M BENCH_SLEEP_TIME_MAX
                        Maximum sleep time between requests.
--test-sleep-time=BENCH_SLEEP_TIME, -t BENCH_SLEEP_TIME
                        Sleep time between tests.
--startup-delay=BENCH_STARTUP_DELAY, -s BENCH_STARTUP_DELAY
                        Startup delay between thread.
--as-fast-as-possible, -f
                        Remove sleep times between requests and between tests,
                        shortcut for -m0 -M0 -t0
--no-color              Monochrome output.
--accept-invalid-links  Do not fail if css/image links are not reachable.
--simple-fetch          Don't load additional links like css or images when
                        fetching an html page.
--label=LABEL, -l LABEL
                        Add a label to this bench run for easier
                        identification (it will be appended to the directory
                        name for reports generated from it).
--enable-debug-server   Instantiates a debug HTTP server which exposes an
                        interface using which parameters can be modified at
                        run-time. Currently supported parameters:
                        /cvu?inc=<integer> to increase the number of CVUs,
                        /cvu?dec=<integer> to decrease the number of CVUs,
                        /getcvu returns number of CVUs
--debug-server-port=DEBUGPORT
                        Port at which debug server should run during the test
--distribute            distributes the CVUs over a group of worker machines
                        that are defined in the section [workers]
--distribute-workers=WORKERLIST
                        this parameter will  over-ride the list of workers
                        defined in the config file. expected notation is
                        uname@host,uname:pwd@host or just host...
--is-distributed        this parameter is for internal use only. it signals to
                        a worker node that it is in distributed mode and
                        shouldn't perform certain actions.
