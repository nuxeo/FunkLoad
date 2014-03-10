#!/usr/bin/python
# (C) Copyright 2005-2010 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Tom Lazar
#               Goutham Bhat
#               Andrew McFague
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
"""FunkLoad Bench runner.

$Id: BenchRunner.py 24746 2005-08-31 09:59:27Z bdelbosc $
"""
import os
import platform
import sys
import threading
import time
import traceback
import unittest
from datetime import datetime
from optparse import OptionParser, TitledHelpFormatter
from socket import error as SocketError
from thread import error as ThreadError
from xmlrpclib import ServerProxy, Fault
import signal

from FunkLoadTestCase import FunkLoadTestCase
from FunkLoadHTTPServer import FunkLoadHTTPServer
from utils import mmn_encode, set_recording_flag, recording, thread_sleep, \
                  trace, red_str, green_str, get_version
try:
    from funkload.rtfeedback import (FeedbackSender, DEFAULT_ENDPOINT,
                                     DEFAULT_PUBSUB)
    LIVE_FEEDBACK = True
except ImportError:
    LIVE_FEEDBACK = False
    DEFAULT_PUBSUB = DEFAULT_ENDPOINT = None


USAGE = """%prog [options] file class.method

%prog launch a FunkLoad unit test as load test.

A FunkLoad unittest uses a configuration file named [class].conf. This
configuration may be overriden by the command line options.

See http://funkload.nuxeo.org/ for more information.

Examples
========
  %prog myFile.py MyTestCase.testSomething
  %prog my_module MyTestCase.testSomething
                        Bench MyTestCase.testSomething using MyTestCase.conf.
  %prog -u http://localhost:8080 -c 10:20 -D 30 myFile.py \\
      MyTestCase.testSomething
                        Bench MyTestCase.testSomething on localhost:8080
                        with 2 cycles of 10 and 20 users for a duration of 30s.
  %prog -h
                        More options.

Alternative Usage:
  %prog discover [options]
                        Discover test modules in the current directory and
                        bench all of them.
"""

try:
    import psyco
    psyco.full()
except ImportError:
    pass


# ------------------------------------------------------------
# utils
#
g_failures = 0                      # result of the bench
g_errors = 0                        # result of the bench
g_success = 0


def add_cycle_result(status):
    """Count number of result."""
    # XXX use a thread.lock, but we don't mind if it is not accurate
    # as the report use the xml log
    global g_success, g_failures, g_errors
    if status == 'success':
        g_success += 1
    elif status == 'error':
        g_errors += 1
    else:
        g_failures += 1

    return g_success, g_errors, g_failures


def get_cycle_results():
    """Return counters."""
    global g_success, g_failures, g_errors
    return g_success, g_failures, g_errors


def get_status(success, failures, errors, color=False):
    """Return a status and an exit code."""
    if errors:
        status = 'ERROR'
        if color:
            status = red_str(status)
        code = -1
    elif failures:
        status = 'FAILURE'
        if color:
            status = red_str(status)
        code = 1
    else:
        status = 'SUCCESSFUL'
        if color:
            status = green_str(status)
        code = 0
    return status, code


def reset_cycle_results():
    """Clear the previous results."""
    global g_success, g_failures, g_errors
    g_success = g_failures = g_errors = 0


def load_module(test_module):
    module = __import__(test_module)
    parts = test_module.split('.')[1:]
    while parts:
        part = parts.pop()
        module = getattr(module, part)
    return module


def load_unittest(test_module, test_class, test_name, options):
    """instantiate a unittest."""
    module = load_module(test_module)
    klass = getattr(module, test_class)
    return klass(test_name, options)


class ThreadSignaller:
    """
    A simple class to signal whether a thread should continue running or stop.
    """
    def __init__(self):
        self.keep_running = True

    def running(self):
        return self.keep_running

    def set_running(self, val):
        self.keep_running = val


class ThreadData:
    """Container for thread related data."""
    def __init__(self, thread, thread_id, thread_signaller):
        self.thread = thread
        self.thread_id = thread_id
        self.thread_signaller = thread_signaller


# ------------------------------------------------------------
# Classes
#
class LoopTestRunner(threading.Thread):
    """Run a unit test in loop."""

    def __init__(self, test_module, test_class, test_name, options,
                 cycle, cvus, thread_id, thread_signaller, sleep_time,
                 debug=False, feedback=None):
        meta_method_name = mmn_encode(test_name, cycle, cvus, thread_id)
        threading.Thread.__init__(self, target=self.run, name=meta_method_name,
                                  args=())
        self.test = load_unittest(test_module, test_class, meta_method_name,
                                  options)
        if sys.platform.lower().startswith('win'):
            self.color = False
        else:
            self.color = not options.no_color
        self.sleep_time = sleep_time
        self.debug = debug
        self.thread_signaller = thread_signaller
        # this makes threads endings if main stop with a KeyboardInterupt
        self.setDaemon(1)
        self.feedback = feedback

    def run(self):
        """Run a test in loop."""
        while (self.thread_signaller.running()):
            test_result = unittest.TestResult()
            self.test.clearContext()
            self.test(test_result)
            feedback = {}

            if test_result.wasSuccessful():
                if recording():
                    feedback['count'] = add_cycle_result('success')

                if self.color:
                    trace(green_str('.'))
                else:
                    trace('.')

                feedback['result'] = 'success'
            else:
                if len(test_result.errors):
                    if recording():
                        feedback['count'] = add_cycle_result('error')

                    if self.color:
                        trace(red_str('E'))
                    else:
                        trace('E')

                    feedback['result'] = 'error'

                else:
                    if recording():
                        feedback['count'] = add_cycle_result('failure')

                    if self.color:
                        trace(red_str('F'))
                    else:
                        trace('F')

                    feedback['result'] = 'failure'

                if self.debug:
                    feedback['errors'] = test_result.errors
                    feedback['failures'] = test_result.failures

                    for (test, error) in test_result.errors:
                        trace("ERROR %s: %s" % (str(test), str(error)))
                    for (test, error) in test_result.failures:
                        trace("FAILURE %s: %s" % (str(test), str(error)))

            if self.feedback is not None:
                self.feedback.test_done(feedback)

            thread_sleep(self.sleep_time)


class BenchRunner:
    """Run a unit test in bench mode."""

    def __init__(self, module_name, class_name, method_name, options):
        self.module_name = module_name
        self.class_name = class_name
        self.method_name = method_name
        self.options = options
        self.color = not options.no_color
        # create a unittest to get the configuration file
        test = load_unittest(self.module_name, class_name,
                             mmn_encode(method_name, 0, 0, 0), options)
        self.config_path = test._config_path
        self.result_path = test.result_path
        self.class_title = test.conf_get('main', 'title')
        self.class_description = test.conf_get('main', 'description')
        self.test_id = self.method_name
        self.test_description = test.conf_get(self.method_name, 'description',
                                              'No test description')
        self.test_url = test.conf_get('main', 'url')
        self.cycles = map(int, test.conf_getList('bench', 'cycles'))
        self.duration = test.conf_getInt('bench', 'duration')
        self.startup_delay = test.conf_getFloat('bench', 'startup_delay')
        self.cycle_time = test.conf_getFloat('bench', 'cycle_time')
        self.sleep_time = test.conf_getFloat('bench', 'sleep_time')
        self.sleep_time_min = test.conf_getFloat('bench', 'sleep_time_min')
        self.sleep_time_max = test.conf_getFloat('bench', 'sleep_time_max')
        self.threads = []  # Contains list of ThreadData objects
        self.last_thread_id = -1
        self.thread_creation_lock = threading.Lock()

        # setup monitoring
        monitor_hosts = []                  # list of (host, port, descr)
        if not options.is_distributed:
            hosts = test.conf_get('monitor', 'hosts', '', quiet=True).split()
            for host in hosts:
                name = host
                host = test.conf_get(host,'host',host.strip())
                monitor_hosts.append((name, host, test.conf_getInt(name, 'port'),
                                      test.conf_get(name, 'description', '')))
        self.monitor_hosts = monitor_hosts
        # keep the test to use the result logger for monitoring
        # and call setUp/tearDown Cycle
        self.test = test

        # set up the feedback sender
        if LIVE_FEEDBACK and options.is_distributed and options.feedback:
            trace("* Creating Feedback sender")
            self.feedback = FeedbackSender(endpoint=options.feedback_endpoint or
                                           DEFAULT_ENDPOINT)
        else:
            self.feedback = None

    def run(self):
        """Run all the cycles.

        return 0 on success, 1 if there were some failures and -1 on errors."""

        trace(str(self))
        trace("Benching\n")
        trace("========\n\n")
        cycle = total_success = total_failures = total_errors = 0

        self.logr_open()
        trace("* setUpBench hook: ...")
        self.test.setUpBench()
        trace(' done.\n')
        self.getMonitorsConfig()
        trace('\n')
        for cvus in self.cycles:
            t_start = time.time()
            reset_cycle_results()
            text = "Cycle #%i with %s virtual users\n" % (cycle, cvus)
            trace(text)
            trace('-' * (len(text) - 1) + "\n\n")
            monitor_key = '%s:%s:%s' % (self.method_name, cycle, cvus)
            trace("* setUpCycle hook: ...")
            self.test.setUpCycle()
            trace(' done.\n')
            self.startMonitors(monitor_key)
            self.startThreads(cycle, cvus)
            self.logging(cycle, cvus)
            #self.dumpThreads()
            self.stopThreads()
            self.stopMonitors(monitor_key)
            cycle += 1
            trace("* tearDownCycle hook: ...")
            self.test.tearDownCycle()
            trace(' done.\n')
            t_stop = time.time()
            trace("* End of cycle, %.2fs elapsed.\n" % (t_stop - t_start))
            success, failures, errors = get_cycle_results()
            status, code = get_status(success, failures, errors, self.color)
            trace("* Cycle result: **%s**, "
                  "%i success, %i failure, %i errors.\n\n" % (
                status, success, failures, errors))
            total_success += success
            total_failures += failures
            total_errors += errors
        trace("* tearDownBench hook: ...")
        self.test.tearDownBench()
        trace(' done.\n\n')
        self.logr_close()

        # display bench result
        trace("Result\n")
        trace("======\n\n")
        trace("* Success: %s\n" % total_success)
        trace("* Failures: %s\n" % total_failures)
        trace("* Errors: %s\n\n" % total_errors)
        status, code = get_status(total_success, total_failures, total_errors)
        trace("Bench status: **%s**\n" % status)
        return code

    def createThreadId(self):
        self.last_thread_id += 1
        return self.last_thread_id

    def startThreads(self, cycle, number_of_threads):
        """Starts threads."""
        self.thread_creation_lock.acquire()
        try:
            trace("* Current time: %s\n" % datetime.now().isoformat())
            trace("* Starting threads: ")
            set_recording_flag(False)
            threads = self.createThreads(cycle, number_of_threads)
            self.threads.extend(threads)
        finally:
            set_recording_flag(True)
            self.thread_creation_lock.release()

    def addThreads(self, number_of_threads):
        """Adds new threads to existing list. Used to dynamically add new
           threads during a debug bench run."""
        self.thread_creation_lock.acquire()
        try:
            trace("Adding new threads: ")
            set_recording_flag(False)
            # In debug bench, 'cycle' value is irrelevant.
            threads = self.createThreads(0, number_of_threads)
            self.threads.extend(threads)
        finally:
            set_recording_flag(True)
            self.thread_creation_lock.release()

    def createThreads(self, cycle, number_of_threads):
        """Creates number_of_threads threads and returns as a list.

        NOTE: This method is not thread safe. Thread safety must be
        handled by the caller."""
        threads = []
        i = 0
        for i in range(number_of_threads):
            thread_id = self.createThreadId()
            thread_signaller = ThreadSignaller()
            thread = LoopTestRunner(self.module_name, self.class_name,
                                    self.method_name, self.options,
                                    cycle, number_of_threads,
                                    thread_id, thread_signaller,
                                    self.sleep_time,
                                    feedback=self.feedback)
            trace(".")
            try:
                thread.start()
            except ThreadError:
                trace("\nERROR: Can not create more than %i threads, try a "
                      "smaller stack size using: 'ulimit -s 2048' "
                      "for example\n" % (i + 1))
                raise
            thread_data = ThreadData(thread, thread_id, thread_signaller)
            threads.append(thread_data)
            thread_sleep(self.startup_delay)
        trace(' done.\n')
        return threads

    def logging(self, cycle, cvus):
        """Log activity during duration."""
        duration = self.duration
        end_time = time.time() + duration
        mid_time = time.time() + duration / 2
        trace("* Logging for %ds (until %s): " % (
            duration, datetime.fromtimestamp(end_time).isoformat()))
        set_recording_flag(True)
        while time.time() < mid_time:
            time.sleep(1)
        self.test.midCycle(cycle, cvus)
        while time.time() < end_time:
            # wait
            time.sleep(1)
        set_recording_flag(False)
        trace(" done.\n")

    def stopThreads(self):
        """Stops all running threads."""
        self.thread_creation_lock.acquire()
        try:
            trace("* Waiting end of threads: ")
            self.deleteThreads(len(self.threads))
            self.threads = []
            trace(" done.\n")
            trace("* Waiting cycle sleeptime %ds: ..." % self.cycle_time)
            time.sleep(self.cycle_time)
            trace(" done.\n")
            self.last_thread_id = -1
        finally:
            self.thread_creation_lock.release()

    def removeThreads(self, number_of_threads):
        """Removes threads. Used to dynamically remove threads during a
           debug bench run."""
        self.thread_creation_lock.acquire()
        try:
            trace('* Removing threads: ')
            self.deleteThreads(number_of_threads)
            trace(' done.\n')
        finally:
            self.thread_creation_lock.release()

    def deleteThreads(self, number_of_threads):
        """Stops given number of threads and deletes from thread list.

        NOTE: This method is not thread safe. Thread safety must be
        handled by the caller."""
        removed_threads = []
        if number_of_threads > len(self.threads):
            number_of_threads = len(self.threads)
        for i in range(number_of_threads):
            thread_data = self.threads.pop()
            thread_data.thread_signaller.set_running(False)
            removed_threads.append(thread_data)
        for thread_data in removed_threads:
            thread_data.thread.join()
            del thread_data
            trace('.')

    def getNumberOfThreads(self):
        return len(self.threads)

    def dumpThreads(self):
        """Display all different traceback of Threads for debugging.

        Require threadframe module."""
        import threadframe
        stacks = {}
        frames = threadframe.dict()
        for thread_id, frame in frames.iteritems():
            stack = ''.join(traceback.format_stack(frame))
            stacks[stack] = stacks.setdefault(stack, []) + [thread_id]

        def sort_stack(x, y):
            """sort stack by number of thread."""
            return cmp(len(x[1]), len(y[1]))

        stacks = stacks.items()
        stacks.sort(sort_stack)
        for stack, thread_ids in stacks:
            trace('=' * 72 + '\n')
            trace('%i threads : %s\n' % (len(thread_ids), str(thread_ids)))
            trace('-' * 72 + '\n')
            trace(stack + '\n')

    def getMonitorsConfig(self):
        """ Get monitors configuration from hosts """
        if not self.monitor_hosts:
            return
        monitor_hosts = []
        for (name, host, port, desc) in self.monitor_hosts:
            trace("* Getting monitoring config from %s: ..." % name)
            server = ServerProxy("http://%s:%s" % (host, port))
            try:
                config = server.getMonitorsConfig()
                data = []
                for key in config.keys():
                    xml = '<monitorconfig host="%s" key="%s" value="%s" />' % (
                                                        name, key, config[key])
                    data.append(xml)
                self.logr("\n".join(data))
            except Fault:
                trace(' not supported.\n')
                monitor_hosts.append((name, host, port, desc))
            except SocketError:
                trace(' failed, server is down.\n')
            else:
                trace(' done.\n')
                monitor_hosts.append((name, host, port, desc))
        self.monitor_hosts = monitor_hosts

    def startMonitors(self, monitor_key):
        """Start monitoring on hosts list."""
        if not self.monitor_hosts:
            return
        monitor_hosts = []
        for (name, host, port, desc) in self.monitor_hosts:
            trace("* Start monitoring %s: ..." % name)
            server = ServerProxy("http://%s:%s" % (host, port))
            try:
                server.startRecord(monitor_key)
            except SocketError:
                trace(' failed, server is down.\n')
            else:
                trace(' done.\n')
                monitor_hosts.append((name, host, port, desc))
        self.monitor_hosts = monitor_hosts

    def stopMonitors(self, monitor_key):
        """Stop monitoring and save xml result."""
        if not self.monitor_hosts:
            return
        for (name, host, port, desc) in self.monitor_hosts:
            trace('* Stop monitoring %s: ' % name)
            server = ServerProxy("http://%s:%s" % (host, port))
            try:
                server.stopRecord(monitor_key)
                xml = server.getXmlResult(monitor_key)
            except SocketError:
                trace(' failed, server is down.\n')
            else:
                trace(' done.\n')
                self.logr(xml)

    def logr(self, message):
        """Log to the test result file."""
        self.test._logr(message, force=True)

    def logr_open(self):
        """Start logging tag."""
        config = {'id': self.test_id,
                  'description': self.test_description,
                  'class_title': self.class_title,
                  'class_description': self.class_description,
                  'module': self.module_name,
                  'class': self.class_name,
                  'method': self.method_name,
                  'cycles': self.cycles,
                  'duration': self.duration,
                  'sleep_time': self.sleep_time,
                  'startup_delay': self.startup_delay,
                  'sleep_time_min': self.sleep_time_min,
                  'sleep_time_max': self.sleep_time_max,
                  'cycle_time': self.cycle_time,
                  'configuration_file': self.config_path,
                  'server_url': self.test_url,
                  'log_xml': self.result_path,
                  'node': platform.node(),
                  'python_version': platform.python_version()}
        if self.options.label:
            config['label'] = self.options.label

        for (name, host, port, desc) in self.monitor_hosts:
            config[name] = desc
        self.test._open_result_log(**config)

    def logr_close(self):
        """Stop logging tag."""
        self.test._close_result_log()
        self.test.logger_result.handlers = []

    def __repr__(self):
        """Display bench information."""
        text = []
        text.append('=' * 72)
        text.append('Benching %s.%s' % (self.class_name,
                                        self.method_name))
        text.append('=' * 72)
        text.append(self.test_description)
        text.append('-' * 72 + '\n')
        text.append("Configuration")
        text.append("=============\n")
        text.append("* Current time: %s" % datetime.now().isoformat())
        text.append("* Configuration file: %s" % self.config_path)
        text.append("* Log xml: %s" % self.result_path)
        text.append("* Server: %s" % self.test_url)
        text.append("* Cycles: %s" % self.cycles)
        text.append("* Cycle duration: %ss" % self.duration)
        text.append("* Sleeptime between request: from %ss to %ss" % (
            self.sleep_time_min, self.sleep_time_max))
        text.append("* Sleeptime between test case: %ss" % self.sleep_time)
        text.append("* Startup delay between thread: %ss\n\n" %
                    self.startup_delay)
        return '\n'.join(text)


class BenchLoader(unittest.TestLoader):
    suiteClass = list
    def loadTestsFromTestCase(self, testCaseClass):
        if not issubclass(testCaseClass, FunkLoadTestCase):
            trace(red_str("Skipping "+ testCaseClass))
            return []
        testCaseNames = self.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']

        return [dict(module_name = testCaseClass.__module__,
                     class_name = testCaseClass.__name__,
                     method_name = x)
                for x in testCaseNames]

def discover(sys_args):
    parser = get_shared_OptionParser()
    options, args = parser.parse_args(sys_args)
    options.label = None

    loader = BenchLoader()
    suite = loader.discover('.')

    def flatten_test_suite(suite):
        if type(suite) != BenchLoader.suiteClass:
            # Wasn't a TestSuite - must have been a Test
            return [suite]
        flat = []
        for x in suite:
            flat += flatten_test_suite(x)
        return flat

    flattened = flatten_test_suite(suite)
    retval = 0
    for test in flattened:
        module_name = test['module_name']
        class_name = test['class_name']
        method_name = test['method_name']
        if options.distribute:
            dist_args = sys_args[:]
            dist_args.append(module_name)
            dist_args.append('%s.%s' % (class_name, method_name))
            ret = run_distributed(options, module_name, class_name,
                                   method_name, dist_args)
        else:
            ret = run_local(options, module_name, class_name, method_name)
        # Handle failures
        if ret != 0:
            retval = ret
            if options.failfast:
                break
    return retval

_manager = None

def shutdown(*args):
    trace('Aborting run...')
    if _manager is not None:
        _manager.abort()
    trace('Aborted')
    sys.exit(0)

def get_runner_class(class_path):
    try:
        module_path, class_name = class_path.rsplit('.', 1)
    except ValueError:
        raise Exception('Invalid class path {0}'.format(class_path))

    _module = __import__(module_path, globals(), locals(), class_name, -1)
    return getattr(_module, class_name)

def parse_sys_args(sys_args):
    parser = get_shared_OptionParser()
    parser.add_option("", "--config",
                      type="string",
                      dest="config",
                      metavar='CONFIG',
                      help="Path to alternative config file")
    parser.add_option("-l", "--label",
                      type="string",
                      help="Add a label to this bench run for easier "
                           "identification (it will be appended to the "
                           "directory name for reports generated from it).")

    options, args = parser.parse_args(sys_args)

    if len(args) != 2:
        parser.error("incorrect number of arguments")

    if not args[1].count('.'):
        parser.error("invalid argument; should be [class].[method]")

    if options.as_fast_as_possible:
        options.bench_sleep_time_min = '0'
        options.bench_sleep_time_max = '0'
        options.bench_sleep_time = '0'

    if os.path.exists(args[0]):
        # We were passed a file for the first argument
        module_name = os.path.basename(os.path.splitext(args[0])[0])
    else:
        # We were passed a module name
        module_name = args[0]

    return options, args, module_name

def get_shared_OptionParser():
    '''Make an OptionParser that can be used in both normal mode and in
    discover mode.
    '''
    parser = OptionParser(USAGE, formatter=TitledHelpFormatter(),
                          version="FunkLoad %s" % get_version())
    parser.add_option("-r", "--runner-class",
                      type="string",
                      dest="bench_runner_class",
                      default="funkload.BenchRunner.BenchRunner",
                      help="Python dotted import path to BenchRunner class to use.")
    parser.add_option("", "--no-color",
                      action="store_true",
                      help="Monochrome output.")
    parser.add_option("", "--accept-invalid-links",
                      action="store_true",
                      help="Do not fail if css/image links are not reachable.")
    parser.add_option("", "--simple-fetch",
                      action="store_true",
                      dest="bench_simple_fetch",
                      help="Don't load additional links like css or images "
                           "when fetching an html page.")
    parser.add_option("--enable-debug-server",
                      action="store_true",
                      dest="debugserver",
                      help="Instantiates a debug HTTP server which exposes an "
                           "interface using which parameters can be modified "
                           "at run-time. Currently supported parameters: "
                           "/cvu?inc=<integer> to increase the number of "
                           "CVUs, /cvu?dec=<integer> to decrease the number "
                           "of CVUs, /getcvu returns number of CVUs ")
    parser.add_option("--debug-server-port",
                      type="string",
                      dest="debugport",
                      help="Port at which debug server should run during the "
                           "test")
    parser.add_option("--distribute",
                      action="store_true",
                      dest="distribute",
                      help="Distributes the CVUs over a group of worker "
                           "machines that are defined in the workers section")
    parser.add_option("--distribute-workers",
                      type="string",
                      dest="workerlist",
                      help="This parameter will  override the list of "
                           "workers defined in the config file. expected "
                           "notation is uname@host,uname:pwd@host or just "
                           "host...")
    parser.add_option("--distribute-python",
                      type="string",
                      dest="python_bin",
                      help="When running in distributed mode, this Python "
                           "binary will be used across all hosts.")
    parser.add_option("--is-distributed",
                      action="store_true",
                      dest="is_distributed",
                      help="This parameter is for internal use only. It "
                           "signals to a worker node that it is in "
                           "distributed mode and shouldn't perform certain "
                           "actions.")
    parser.add_option("--distributed-packages",
                      type="string",
                      dest="distributed_packages",
                      help="Additional packages to be passed to easy_install "
                           "on remote machines when being run in distributed "
                           "mode.")
    parser.add_option("--distributed-log-path",
                      type="string",
                      dest="distributed_log_path",
                      help="Path where all the logs will be stored when "
                           "running a distributed test")
    parser.add_option("--distributed-key-filename",
                      type="string",
                      dest="distributed_key_filename",
                      help=("Path of the SSH key to use when running a "
                            "distributed test"))
    parser.add_option("--feedback-endpoint",
                      type="string",
                      dest="feedback_endpoint",
                      help=("ZMQ push/pull socket used between the master and "
                            "the node to send feedback."))
    parser.add_option("--feedback-pubsub-endpoint",
                      type="string",
                      dest="feedback_pubsub_endpoint",
                      help="ZMQ pub/sub socket use to publish feedback.")
    parser.add_option("--feedback",
                      action="store_true",
                      dest="feedback",
                      help="Activates the realtime feedback")
    parser.add_option("--failfast",
                      action="store_true",
                      dest="failfast",
                      help="Stop on first fail or error. (For discover mode)")
    parser.add_option("-u", "--url",
                      type="string",
                      dest="main_url",
                      help="Base URL to bench.")
    parser.add_option("-c", "--cycles",
                      type="string",
                      dest="bench_cycles",
                      help="Cycles to bench, colon-separated list of "
                           "virtual concurrent users. To run a bench with 3 "
                           "cycles of 5, 10 and 20 users, use: -c 5:10:20")
    parser.add_option("-D", "--duration",
                      type="string",
                      dest="bench_duration",
                      help="Duration of a cycle in seconds.")
    parser.add_option("-m", "--sleep-time-min",
                      type="string",
                      dest="bench_sleep_time_min",
                      help="Minimum sleep time between requests.")
    parser.add_option("-M", "--sleep-time-max",
                      type="string",
                      dest="bench_sleep_time_max",
                      help="Maximum sleep time between requests.")
    parser.add_option("-t", "--test-sleep-time",
                      type="string",
                      dest="bench_sleep_time",
                      help="Sleep time between tests.")
    parser.add_option("-s", "--startup-delay",
                      type="string",
                      dest="bench_startup_delay",
                      help="Startup delay between thread.")
    parser.add_option("-f", "--as-fast-as-possible",
                      action="store_true",
                      help="Remove sleep times between requests and between "
                           "tests, shortcut for -m0 -M0 -t0")
    return parser

def run_distributed(options, module_name, class_name, method_name, sys_args):
    ret = None
    from funkload.Distributed import DistributionMgr
    global _manager
    
    try:
        distmgr = DistributionMgr(
            module_name, class_name, method_name, options, sys_args)
        _manager = distmgr
    except UserWarning, error:
        trace(red_str("Distribution failed with:%s \n" % (error)))
        return 1
    
    try:
        try:
            distmgr.prepare_workers(allow_errors=True)
            ret = distmgr.run()
            distmgr.final_collect()
        except KeyboardInterrupt:
            trace("* ^C received *")
    finally:
        # in any case we want to stop the workers at the end
        distmgr.abort()
    
    _manager = None
    return ret

def run_local(options, module_name, class_name, method_name):
    ret = None
    RunnerClass = get_runner_class(options.bench_runner_class)
    bench = RunnerClass(module_name, class_name, method_name, options)
    
    # Start a HTTP server optionally
    if options.debugserver:
        http_server_thread = FunkLoadHTTPServer(bench, options.debugport)
        http_server_thread.start()
    
    try:
        ret = bench.run()
    except KeyboardInterrupt:
        trace("* ^C received *")
    return ret

def main(sys_args=sys.argv[1:]):
    """Default main."""
    # enable loading of modules in the current path
    cur_path = os.path.abspath(os.path.curdir)
    sys.path.insert(0, cur_path)

    # registering signals
    if not sys.platform.lower().startswith('win'):
        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGQUIT, shutdown)

    # special case: 'discover' argument
    if sys_args and sys_args[0].lower() == 'discover':
        return discover(sys_args)

    options, args, module_name = parse_sys_args(sys_args)

    klass, method = args[1].split('.')
    if options.distribute:
        return run_distributed(options, module_name, klass, method, sys_args)
    else:
        return run_local(options, module_name, klass, method)

if __name__ == '__main__':
    ret = main()
    sys.exit(ret)
