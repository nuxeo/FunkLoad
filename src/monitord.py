#!/usr/bin/python

# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
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
"""Simple XMLRPC server that monitor a linux localhost.

Used by load tests to produce charts on the server side.
See monitorctl.py for client example.

Porvide startRecord, stopRecord, getResult, getStatus ... methods.

Usage: ./monitord.py <configuration_file>.

$Id: monitord.py 24681 2005-08-30 09:48:20Z bdelbosc $
"""
import sys, os, re
from time import time, localtime, gmtime, strftime, sleep
import socket
from threading import Thread
from ConfigParser import ConfigParser
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy

CONF_PATH = "monitor.conf"

# ------------------------------------------------------------
# globals
#
g_conf_path = ''                        # the monitor configuration path
g_conf = None                           # the config parser
g_quit = 0                              # flag to quit the rpc server
g_keys = {}                             # list of recorders
g_records = []                          # list of MonitorStat
g_monitor = None                        # the thread that monitor

# ------------------------------------------------------------
# utils
#
def get_time_stamp(time_in=None):
    """Return a time stamp string

    If t is not none assume that it is a number of second since the epoch."""
    if time_in is None:
        date = gmtime()
    else:
        date = localtime(float(time_in))
    return strftime('%Y-%m-%dT%H-%M-%S', date)

def log(msg):
    """Print to stdout and flush."""
    print get_time_stamp() + " srv " + msg
    sys.stdout.flush()


def read_load_info():
    """Read the current system load from /proc/loadavg."""
    loadavg = open("/proc/loadavg").readline()
    loadavg = loadavg[:-1]
    # Contents are space separated:
    # 5, 10, 15 min avg. load, running proc/total threads, last pid
    stats = loadavg.split()
    running = stats[3].split("/")
    load_stats = {}
    load_stats['loadAvg1min'] = stats[0]
    load_stats['loadAvg5min'] = stats[1]
    load_stats['loadAvg15min'] = stats[2]
    load_stats['running'] = running[0]
    load_stats['tasks'] = running[1]
    return load_stats


def read_cpu_usage():
    """Read the current system cpu usage from /proc/stat."""
    lines = open("/proc/stat").readlines()
    for line in lines:
        #print "l = %s" % line
        l = line.split()
        if len(l) < 8:
            continue
        if l[0].startswith('cpu'):
            # cpu = sum of usr, nice, sys
            cpu = long(l[1]) + long(l[2]) + long(l[3])
            idl = long(l[4])
            return {'CPUTotalJiffies': cpu,
                    'IDLTotalJiffies': idl,
                    }
    return {}



def read_mem_info(kernel_rev):
    """Read the current status of memory from /proc/meminfo."""
    meminfo_fields = ["MemTotal", "MemFree", "SwapTotal", "SwapFree"]
    meminfo = open("/proc/meminfo")
    if kernel_rev <= 2.4:
        # Kernel 2.4 has extra lines of info, duplicate of later info
        meminfo.readline()
        meminfo.readline()
        meminfo.readline()
    lines = meminfo.readlines()
    meminfo.close()
    meminfo_stats = {}
    for line in lines:
        line = line[:-1]
        stats = line.split()
        field = stats[0][:-1]
        if field in meminfo_fields:
            meminfo_stats[field[0].lower()+field[1:]] = stats[1]

    return meminfo_stats


def read_net_info(interface='eth0'):
    """Read the stats from an interface."""
    ifaces = open( "/proc/net/dev" )
    # Skip the information banner
    ifaces.readline()
    ifaces.readline()
    # Read the rest of the lines
    lines = ifaces.readlines()
    ifaces.close()
    # Process the interface lines
    net_stats = {}
    for line in lines:
        # Parse the interface line
        # Interface is followed by a ':' and then bytes, possibly with
        # no spaces between : and bytes
        line = line[:-1]
        (device, data) = line.split(':')

        # Get rid of leading spaces
        device = device.lstrip()
        # get the stats
        stats = data.split()
        if device == interface:
            net_stats['receiveBytes'] = stats[0]
            net_stats['receivePackets'] = stats[1]
            net_stats['transmitBytes'] = stats[8]
            net_stats['transmitPackets'] = stats[9]

    return net_stats


# ------------------------------------------------------------
# classes
#
class MonitorStat:
    """A simple class to store statistic."""
    def __init__(self, host, kernel_rev, interface):
        self.time = time()
        self.host = host
        self.interface = interface
        for infos in (read_cpu_usage(),
                      read_load_info(),
                      read_mem_info(kernel_rev),
                      read_net_info(interface)):
            for key, value in infos.items():
                setattr(self, key, value)

    def __repr__(self, extra_key=None):
        text = "<monitor "
        if extra_key is not None:
            text += 'key="%s" ' % extra_key
        for key, value in self.__dict__.items():
            text += '%s="%s" ' % (key, value)
        text += ' />'
        return text


class Monitor(Thread):
    """The monitor thread."""
    def __init__(self, host=None, interval=None, interface=None):
        Thread.__init__(self)
        self._recorder_count = 0        # number of recorder
        self._running = 0               # boolean running mode
        self._interface = None          # net interface
        self._interval = None           # interval between monitoring
        self._host = None               # name of the monitored host
        self.setInterval(interval)
        self.setInterface(interface)
        self.setHost(host)
        self.checkKernelRev()
        # this makes threads endings if main stop with a KeyboardInterupt
        self.setDaemon(1)

    def setInterval(self, interval):
        """Set the interval between monitoring."""
        self._interval = interval

    def setInterface(self, interface):
        """Set the network interface to monitor."""
        self._interface = interface

    def setHost(self, host):
        """Set the monitored host."""
        self._host = host

    def checkKernelRev(self):
        """Check the linux kernel revision."""
        version = open("/proc/version").readline()
        kernel_rev = float(re.search(r'version (\d+\.\d+)\.\d+',
                                     version).group(1))
        if (kernel_rev > 2.6) or (kernel_rev < 2.4):
            sys.stderr.write(
                "Sorry, kernel v%0.1f is not supported\n" % kernel_rev)
            sys.exit(-1)
        self._kernel_rev = kernel_rev

    def run(self):
        """Thread jobs."""
        self._running = 1
        while self._running:
            sleep(self._interval)
            if self._recorder_count > 0:
                self.monitor()

    def stop(self):
        """Stop the thread."""
        self._running = 0

    def monitor(self):
        """The monitor task."""
        global g_records
        g_records.append(MonitorStat(self._host,
                                     self._kernel_rev,
                                     self._interface))

    def startRecord(self):
        """Enable recording."""
        self._recorder_count += 1
        log('startRecord %s' % self._recorder_count)

    def stopRecord(self):
        """Stop recording."""
        self._recorder_count -= 1
        log('stopRecord %s' % self._recorder_count)

    def countRecorders(self):
        """Return the number of recorder."""
        return self._recorder_count

# ------------------------------------------------------------
# rpc to manage the server
#
class MySimpleXMLRPCServer(SimpleXMLRPCServer):
    # this property set SO_REUSEADDR which tells the operating system to allow
    # code to connect to a socket even if it's waiting for other potential
    # packets
    allow_reuse_address = True


def stopServer():
    """Stop the server."""
    global g_quit, g_monitor
    log("""stopServer stopping monitor server.""")
    g_monitor.stop()
    g_quit = 1
    return 1

def getStatus():
    """Return the server status."""
    global g_conf, g_keys, g_monitor
    recorders = g_monitor.countRecorders()
    status = 'Waiting'
    if recorders:
        status = 'Recording for %s client' % recorders
    return "Server status: %s (index = %s, recorder list %s)." % (
        status, len(g_records), str(g_keys))

def reloadConf():
    """Reload the configuration file."""
    global g_conf, g_conf_path
    g_conf.read(g_conf_path)
    interface = g_conf.get('server', 'interface')
    g_monitor.setInterface(interface)
    interval = g_conf.getfloat('server', 'interval')
    g_monitor.setInterval(interval)
    host = g_conf.get('server', 'host')
    g_monitor.setHost(host)
    return 1

# ------------------------------------------------------------
# rpc services
#
def startRecord(key):
    """Start to monitor if it is the first key."""
    global g_keys, g_monitor
    log('startRecord %s' % key)
    if not g_keys.has_key(key) or g_keys[key][1] is not None:
        g_monitor.startRecord()
    g_keys[key] = [len(g_records), None]
    return 1

def stopRecord(key):
    """Stop to monitor if it is the last key."""
    global g_keys, g_monitor, g_records
    log('stopRecord %s' % key)
    if not g_keys.has_key(key) or g_keys[key][1] is not None:
        return 0
    g_keys[key] = [g_keys[key][0], len(g_records)]
    g_monitor.stopRecord()
    return 1

def getResult(key):
    """Return stats for key."""
    global g_records, g_keys
    log('getResult %s' % key)
    if key not in g_keys.keys():
        return []
    ret = g_records[g_keys[key][0]:g_keys[key][1]]
    return ret

def getXmlResult(key):
    """Return result as xml."""
    log('getXmlResult %s' % key)
    ret = getResult(key)
    ret = [stat.__repr__(key) for stat in ret]
    return '\n'.join(ret)

# ------------------------------------------------------------
# testing
#
def test_monitor():
    """Test getMonitor."""
    key = 'internal_test_monitor'
    startRecord(key)
    sleep(2)
    stopRecord(key)
    print getXmlResult(key)


def is_server_running(host, port):
    """Check if the server is already running."""
    server = ServerProxy("http://%s:%s" % (host, port))
    try:
        server.getStatus()
    except socket.error:
        return 0
    return 1


# ------------------------------------------------------------
# main
#
def main(conf_path):
    """Init and run XMLRPC Server."""
    global g_conf, g_quit, g_conf_path, g_monitor

    # launch monitoring thread
    g_monitor = Monitor()

    # config file
    g_conf_path = conf_path
    g_conf = ConfigParser(defaults={'FLOAD_HOME':
                                    os.getenv('FLOAD_HOME','.')})
    log("Use configuration file: %s." % conf_path)
    reloadConf()

    # setup and launch xml rpc server
    host = g_conf.get('server', 'host')
    port = int(g_conf.get('server', 'port'))


    if is_server_running(host, port):
        log("Server already running on %s:%s." % (host, port))
        return

    g_monitor.start()

    log("Init XMLRPC server %s:%s." % (host, port))
    server = MySimpleXMLRPCServer((host, port))
    server.register_function(getStatus)
    server.register_function(reloadConf)
    server.register_function(stopServer)
    server.register_function(startRecord)
    server.register_function(stopRecord)
    server.register_function(getResult)
    server.register_function(getXmlResult)
    log("monitor server started.")
    while not g_quit:
        server.handle_request()
    sleep(1)
    server.server_close()


if __name__ == '__main__':
    conf_path = CONF_PATH
    if len(sys.argv) >= 2:
        conf_path = sys.argv[1]
    main(conf_path)
