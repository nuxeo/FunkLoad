#!/usr/bin/python
# Author: Ali-Akber Saifee
# Contributors: Andrew McFague
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
import os
import platform
import re
import socket
import threading
import time
from datetime import datetime
from socket import error as SocketError
from stat import S_ISREG, S_ISDIR
from glob import glob
from xml.etree.ElementTree import ElementTree
from xmlrpclib import ServerProxy

import paramiko

from utils import mmn_encode, trace, package_tests, get_virtualenv_script, \
                  get_version


def load_unittest(test_module, test_class, test_name, options):
    """instantiate a unittest."""
    module = __import__(test_module)
    klass = getattr(module, test_class)
    return klass(test_name, options)


class DistributorBase(object):
    """
    base class for any XXXDistributor objects that can be used
    to distribute benches accross multiple machines.
    """
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.connected = False


def requiresconnection(fn):
    """
    decorator for :class:`~SSHDistributor`
    object that raises a runtime exception upon calling methods
    if the object hasn't been connected properly.
    """
    def _requiresconnect(self, *args, **kwargs):
        if not self.connected:
            raise RuntimeError(
                "%s requires an ssh connection to be created" % fn.func_name)
        return fn(self, *args, **kwargs)
    _requiresconnect.__name__ = fn.__name__
    _requiresconnect.__doc__ = fn.__doc__
    return _requiresconnect


class SSHDistributor(DistributorBase):
    """
    Provides commands to perform distirbuted actions
    using an ssh connection (depends on paramiko). Essentially
    used by :class:`~DistributionMgr`.

    """
    def __init__(self, host, username=None, password=None):
        """
        performs authentication and tries to connect to the
        `host`.
        """
        DistributorBase.__init__(self, host, username, password)

        self.connection = paramiko.client.SSHClient()
        self.connection.load_system_host_keys()
        self.connection.set_missing_host_key_policy(paramiko.WarningPolicy())
        self.error = ""
        credentials = {}
        if username and password:
            credentials = {"username": username, "password": password}
        elif username:
            credentials = {"username": username}
        try:
            self.connection.connect(host, timeout=5, **credentials)
            self.connected = True
        except socket.gaierror, error:
            self.error = error
        except socket.timeout, error:
            self.error = error

    @requiresconnection
    def get(self, remote_path, local_path):
        """
        performs a copy from ``remote_path`` to ``local_path``.
        For performing the inverse operation, use the :meth:`put`
        """
        try:
            sftp = self.connection.open_sftp()
            sftp.get(remote_path, local_path)
        except Exception, error:
            trace("failed to get %s->%s with error %s\n" % \
                   (local_path, remote_path, error))

    @requiresconnection
    def put(self, local_path, remote_path):
        """
        performs a copy from `local_path` to `remote_path`
        For performing the inverse operation, use the :meth:`get`
        """
        try:
            sftp = self.connection.open_sftp()
            sftp.put(local_path, remote_path)
        except Exception, error:
            trace("failed to put %s->%s with error %s\n" % \
                   (local_path, remote_path, error))

    @requiresconnection
    def execute(self, cmd_string, shell_interpreter="bash -c", cwdir=None):
        """
        evaluated the command specified by ``cmd_string`` in the context
        of ``cwdir`` if it is specified. The optional ``shell_interpreter``
        parameter allows overloading the default bash.
        """
        obj = self.threaded_execute(cmd_string, shell_interpreter, cwdir)
        obj.join()
        return obj.output.read(), obj.err.read()

    @requiresconnection
    def threaded_execute(self, cmd_string, shell_interpreter="bash -c",
                                                                cwdir=None):
        """
        basically the same as :meth:`execute` execept that it returns
        a started :mod:`threading.Thread` object instead of the output.
        """
        class ThreadedExec(threading.Thread):
            "simple Thread wrapper on :meth:`execute`"
            # FIXME Remove the dependency on self.connection
            def __init__(self_, cmd_string, shell_interpreter, cwdir):
                threading.Thread.__init__(self_)
                self_.cmd_string = cmd_string
                self_.shell_interpreter = shell_interpreter
                self_.cwdir = cwdir

            def run(self_):
                exec_str = ""
                if self_.cwdir:
                    exec_str += "pushd .; cd %s;" % cwdir
                exec_str += "%s \"%s\"" % (
                    self_.shell_interpreter, self_.cmd_string)
                if self_.cwdir:
                    exec_str += "; popd;"
                self_.input, self_.output, self_.err = \
                    self.connection.exec_command(exec_str)

        th_obj = ThreadedExec(cmd_string, shell_interpreter, cwdir)
        th_obj.start()
        return th_obj

    @requiresconnection
    def isdir(self, remote_path):
        """
        test to see if the path pointing to ``remote_dir``
        exists as a directory.
        """
        try:
            sftp = self.connection.open_sftp()
            st = sftp.stat(remote_path)
            return S_ISDIR(st.st_mode)
        except Exception:
            return False

    @requiresconnection
    def isfile(self, remote_path):
        """
        test to see if the path pointing to ``remote_path``
        exists as a file.
        """
        try:
            sftp = self.connection.open_sftp()
            st = sftp.stat(remote_path)
            return S_ISREG(st.st_mode)
        except Exception:
            return False

    def die(self):
        """
        kills the ssh connection
        """
        self.connection.close()


class DistributionMgr(threading.Thread):
    """
    Interface for use by :mod:`funkload.TestRunner` to distribute
    the bench over multiple machines.
    """
    def __init__(self, module_file, class_name, method_name, options,
                                                                cmd_args):
        """
        mirrors the initialization of :class:`funkload.BenchRunner.BenchRunner`
        """
        # store the args. these can be passed to BenchRunner later.
        self.module_file = module_file
        self.class_name = class_name
        self.method_name = method_name
        self.options = options
        self.cmd_args = cmd_args

        self.cmd_args += " --is-distributed"
        self.module_name = os.path.basename(os.path.splitext(module_file)[0])
        self.tarred_tests, self.tarred_testsdir = package_tests(module_file)
        self.remote_res_dir = "/tmp/funkload-bench-sandbox/"

        test = load_unittest(self.module_name, class_name,
                             mmn_encode(method_name, 0, 0, 0), options)

        self.config_path = test._config_path
        self.result_path = test.result_path
        self.class_title = test.conf_get('main', 'title')
        self.class_description = test.conf_get('main', 'description')
        self.test_id = self.method_name
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

        if options.python_bin:
            self.python_bin = options.python_bin
        else:
            self.python_bin = test.conf_get(
                'distribute', 'python_bin', 'python')

        if options.distributed_packages:
            self.distributed_packages = options.distributed_packages
        else:
            self.distributed_packages = test.conf_get(
                                                'distribute', 'packages', '')

        try:
            desc = getattr(test, self.method_name).__doc__.strip()
        except:
            desc = ""
        self.test_description = test.conf_get(self.method_name, 'description',
                                              desc)
        # make a collection output location
        if test.conf_get('distribute', 'log_path', '', quiet=True):
            self.distribution_output = test.conf_get('distribute', 'log_path')
        else:
            raise UserWarning("log_path isn't defined in section [distribute]")

        # check if user has overridden the default funkload distro download
        # location this will be used to download funkload on the worker nodes.
        self.funkload_location = test.conf_get(
            'distribute', 'funkload_location', 'funkload')

        if not os.path.isdir(self.distribution_output):
            os.makedirs(self.distribution_output)

        # check if hosts are in options
        workers = []                  # list of (host, port, descr)
        if options.workerlist:
            for h in  options.workerlist.split(","):
                cred_host = h.split("@")
                if len(cred_host) == 1:
                    uname, pwd, host = None, None, cred_host[0]
                else:
                    cred = cred_host[0]
                    host = cred_host[1]
                    uname_pwd = cred.split(":")
                    if len(uname_pwd) == 1:
                        uname, pwd = uname_pwd[0], None
                    else:
                        uname, pwd = uname_pwd

                workers.append({
                    "host": host,
                    "password": pwd,
                    "username": uname})
        else:
            hosts = test.conf_get('workers', 'hosts', '', quiet=True).split()
            for host in hosts:
                host = host.strip()
                workers.append({
                    "host": host,
                    "password": test.conf_get(host, 'password', ''),
                    "username": test.conf_get(host, 'username', '')})

        self._workers = []
        [self._workers.append(SSHDistributor(**w)) for w in workers]
        self._worker_results = {}
        trace(str(self))

        # setup monitoring
        monitor_hosts = []                  # list of (host, port, descr)
        if not options.is_distributed:
            hosts = test.conf_get('monitor', 'hosts', '', quiet=True).split()
            for host in sorted(hosts):
                host = host.strip()
                monitor_hosts.append((host, test.conf_getInt(host, 'port'),
                                      test.conf_get(host, 'description', '')))
        self.monitor_hosts = monitor_hosts
        # keep the test to use the result logger for monitoring
        # and call setUp/tearDown Cycle
        self.test = test

    def __repr__(self):
        """Display distributed bench information."""
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
        text.append("* Distributed output: %s" % self.distribution_output)
        text.append("* Server: %s" % self.test_url)
        text.append("* Cycles: %s" % self.cycles)
        text.append("* Cycle duration: %ss" % self.duration)
        text.append("* Sleeptime between request: from %ss to %ss" % (
            self.sleep_time_min, self.sleep_time_max))
        text.append("* Sleeptime between test case: %ss" % self.sleep_time)
        text.append("* Startup delay between thread: %ss" %
                    self.startup_delay)
        text.append("* Workers :%s\n\n" % ",".join(
                                                w.host for w in self._workers))
        return '\n'.join(text)

    def prepare_workers(self, allow_errors=False):
        """
        initialized the sandboxes in each worker node to prepare for a
        bench run. the additional parameter `allow_errors` essentially
        will make the distinction between ignoring unresponsive/inappropriate
        nodes - or raising an error and failing the entire bench.
        """
        # right, lets figure out if funkload can be setup on each host

        def local_prep_worker(worker):
            virtual_env = os.path.join(
                self.remote_res_dir, self.tarred_testsdir)

            if worker.isdir(virtual_env):
                worker.execute("rm -rf %s" % virtual_env)

            worker.execute("mkdir -p %s" % virtual_env)
            worker.put(
                get_virtualenv_script(),
                os.path.join(self.remote_res_dir, "virtualenv.py"))

            trace(".")
            worker.execute(
                "%s virtualenv.py %s" % (
                    self.python_bin, self.tarred_testsdir),
                cwdir=self.remote_res_dir)

            tarball = os.path.split(self.tarred_tests)[1]
            remote_tarball = os.path.join(self.remote_res_dir, tarball)

            # setup funkload
            cmd = "./bin/easy_install setuptools ez_setup {funkload}".format(
                funkload=self.funkload_location)

            if self.distributed_packages:
                cmd += " %s" % self.distributed_packages

            worker.execute(cmd, cwdir=virtual_env)

            #unpackage tests.
            worker.put(
                self.tarred_tests, os.path.join(self.remote_res_dir, tarball))
            worker.execute(
                "tar -xvf %s" % tarball,
                cwdir=self.remote_res_dir)
            worker.execute("rm %s" % remote_tarball)

        threads = []
        trace("* Preparing sandboxes for %d workers." % len(self._workers))
        for worker in list(self._workers):
            if not worker.connected:
                if allow_errors:
                    trace("%s is not connected, removing from pool.\n" % \
                                                                 worker.host)
                    self._workers.remove(worker)
                    continue
                else:
                    raise RuntimeError(
                        "%s is not contactable with error %s" % (
                            worker.host, worker.error))

            # Verify that the Python binary is available
            which_python = "test -x `which %s 2>&1 > /dev/null` && echo true" \
                    % (self.python_bin)
            out, err = worker.execute(which_python)

            if out.strip() == "true":
                threads.append(threading.Thread(
                    target=local_prep_worker,
                    args=(worker,)))
            elif allow_errors:
                trace("Cannot find Python binary at path `%s` on %s, " + \
                      "removing from pool" % (self.python_bin, worker.host))
                self._workers.remove(worker)
            else:
                raise RuntimeError("%s is not contactable with error %s" % (
                    worker.host, worker.error))

        [k.start() for k in threads]
        [k.join() for k in threads]
        trace("\n")
        if not self._workers:
            raise RuntimeError("no workers available for distribution")

    def abort(self):
        for worker in self._workers:
            worker.die()

    def run(self):
        """
        """
        threads = []
        trace("* Starting %d workers" % len(self._workers))

        self.startMonitors()
        for worker in self._workers:
            venv = os.path.join(self.remote_res_dir, self.tarred_testsdir)
            obj = worker.threaded_execute(
                'bin/fl-run-bench %s' % self.cmd_args,
                cwdir=venv)
            trace(".")
            threads.append(obj)
        trace("\n")
        [t.join() for t in threads]
        trace("\n")

        for thread, worker in zip(threads, self._workers):
            self._worker_results[worker] = thread.output.read()
            trace("* [%s] returned\n" % worker.host)
            err_string = thread.err.read()
            if err_string:
                trace("\n".join("  [%s]: %s" % (worker.host, k) for k \
                        in err_string.split("\n") if k.strip()))
            trace("\n")

        self.stopMonitors()
        self.correlate_statistics()

    def final_collect(self):
        expr = re.compile("Log\s+xml:\s+(.*?)\n")
        for worker, results in self._worker_results.items():
            res = expr.findall(results)
            if res:
                remote_file = res[0]
                filename = os.path.split(remote_file)[1]
                local_file = os.path.join(
                    self.distribution_output, "%s-%s" % (
                        worker.host, filename))
                worker.get(remote_file, local_file)
                trace("* Received bench log from [%s] into %s\n" % (
                    worker.host, local_file))

    def startMonitors(self):
        """Start monitoring on hosts list."""
        if not self.monitor_hosts:
            return
        monitor_hosts = []
        monitor_key = "%s:0:0" % self.method_name
        for (host, port, desc) in self.monitor_hosts:
            trace("* Start monitoring %s: ..." % host)
            server = ServerProxy("http://%s:%s" % (host, port))
            try:
                server.startRecord(monitor_key)
            except SocketError:
                trace(' failed, server is down.\n')
            else:
                trace(' done.\n')
                monitor_hosts.append((host, port, desc))
        self.monitor_hosts = monitor_hosts

    def stopMonitors(self):
        """Stop monitoring and save xml result."""
        if not self.monitor_hosts:
            return
        monitor_key = "%s:0:0" % self.method_name
        successful_results = []
        for (host, port, desc) in self.monitor_hosts:
            trace('* Stop monitoring %s: ' % host)
            server = ServerProxy("http://%s:%s" % (host, port))
            try:
                server.stopRecord(monitor_key)
                successful_results.append(server.getXmlResult(monitor_key))
            except SocketError:
                trace(' failed, server is down.\n')
            else:
                trace(' done.\n')

        self.write_statistics(successful_results)

    def write_statistics(self, successful_results):
        """ Write the distributed stats to a file in the output dir """
        path = os.path.join(self.distribution_output, "stats.xml")
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
                  'python_version': platform.python_version()}

        for (host, port, desc) in self.monitor_hosts:
            config[host] = desc

        with open(path, "w+") as fd:
            fd.write('<funkload version="{version}" time="{time}">\n'.format(
                            version=get_version(), time=time.time()))
            for key, value in config.items():
                # Write out the config values
                fd.write('<config key="{key}" value="{value}"/>\n'.format(
                                                        key=key, value=value))
            for xml in successful_results:
                fd.write(xml)
                fd.write("\n")

            fd.write("</funkload>\n")

    def _calculate_time_skew(self, results, stats):
        def min_time(vals):
            keyfunc = lambda elem: float(elem.attrib['time'])
            return keyfunc(min(vals, key=keyfunc))

        results_min = min_time(results)
        monitor_min = min_time(stats)

        return results_min / monitor_min

    def _calculate_results_ranges(self, results):
        seen = []
        times = {}
        for element in results:
            cycle = int(element.attrib['cycle'])
            if cycle not in seen:
                seen.append(cycle)

                cvus = int(element.attrib['cvus'])
                start_time = float(element.attrib['time'])
                times[start_time] = (cycle, cvus)

        return times

    def correlate_statistics(self):
        result_path = None
        if not self.monitor_hosts:
            return
        for worker, results in self._worker_results.items():
            files = glob("%s/%s-*.xml" % (self.distribution_output,
                                          worker.host))
            if files:
                result_path = files[0]
                break

        if not result_path:
            trace("* No output files found; unable to correlate stats.\n")
            return

        # Calculate the ratio between results and monitoring
        results_tree = ElementTree(file=result_path)
        stats_path = os.path.join(self.distribution_output, "stats.xml")
        stats_tree = ElementTree(file=stats_path)

        results = results_tree.findall("testResult")
        stats = stats_tree.findall("monitor")
        ratio = self._calculate_time_skew(results, stats)

        # Now that we have the ratio, we can calculate the sessions!
        times = self._calculate_results_ranges(results)
        times_desc = sorted(times.keys(), reverse=True)

        # Now, parse the stats tree and update values
        def find_range(start_time):
            for time_ in times_desc:
                if start_time > time_:
                    return times[time_]
            else:
                return times[time_]

        for stat in stats:
            adj_time = float(stat.attrib['time']) * ratio
            cycle, cvus = find_range(adj_time)
            key, cycle_, cvus_ = stat.attrib['key'].partition(':')
            stat.attrib['key'] = "%s:%d:%d" % (key, cycle, cvus)

        stats_tree.write(stats_path)
