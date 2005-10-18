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
"""A Linux monitor server/controller.

$Id$
"""
import sys
import re
from time import time, sleep
from threading import Thread
from XmlRpcBase import XmlRpcBaseServer, XmlRpcBaseController


# ------------------------------------------------------------
# monitor readers
#
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
        if len(l) < 5:
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
class MonitorInfo:
    """A simple class to collect info."""
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


class MonitorThread(Thread):
    """The monitor thread that collect information."""
    def __init__(self, records, host=None, interval=None, interface=None):
        Thread.__init__(self)
        self.records = records
        self._recorder_count = 0        # number of recorder
        self._running = False           # boolean running mode
        self._interface = None          # net interface
        self._interval = None           # interval between monitoring
        self._host = None               # name of the monitored host
        self.setInterval(interval)
        self.setInterface(interface)
        self.setHost(host)
        self._kernel_rev = None
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
        self._running = True
        while self._running:
            sleep(self._interval)
            if self._recorder_count > 0:
                self.monitor()

    def stop(self):
        """Stop the thread."""
        self._running = False

    def monitor(self):
        """The monitor task."""
        self.records.append(MonitorInfo(self._host,
                                        self._kernel_rev,
                                        self._interface))

    def startRecord(self):
        """Enable recording."""
        self._recorder_count += 1

    def stopRecord(self):
        """Stop recording."""
        self._recorder_count -= 1

    def countRecorders(self):
        """Return the number of recorder."""
        return self._recorder_count



# ------------------------------------------------------------
# Server
#
class MonitorServer(XmlRpcBaseServer):
    """The XML RPC monitor server."""
    server_name = "monitor"
    method_names = XmlRpcBaseServer.method_names + [
        'startRecord', 'stopRecord', 'getResult', 'getXmlResult']

    def __init__(self, argv=None):
        self.interval = None
        self.interface = None
        self.records = []
        self._keys = {}
        XmlRpcBaseServer.__init__(self, argv)
        self._monitor = MonitorThread(self.records,
                                      self.host,
                                      self.interval,
                                      self.interface)
        self._monitor.start()

    def _init_cb(self, conf, options):
        """init callback."""
        self.interval = conf.getfloat('server', 'interval')
        self.interface = conf.get('server', 'interface')

    def startRecord(self, key):
        """Start to monitor if it is the first key."""
        self.logd('startRecord %s' % key)
        if not self._keys.has_key(key) or self._keys[key][1] is not None:
            self._monitor.startRecord()
        self._keys[key] = [len(self.records), None]
        return 1

    def stopRecord(self, key):
        """Stop to monitor if it is the last key."""
        self.logd('stopRecord %s' % key)
        if not self._keys.has_key(key) or self._keys[key][1] is not None:
            return 0
        self._keys[key] = [self._keys[key][0], len(self.records)]
        self._monitor.stopRecord()
        return 1

    def getResult(self, key):
        """Return stats for key."""
        self.logd('getResult %s' % key)
        if key not in self._keys.keys():
            return []
        ret = self.records[self._keys[key][0]:self._keys[key][1]]
        return ret

    def getXmlResult(self, key):
        """Return result as xml."""
        self.logd('getXmlResult %s' % key)
        ret = self.getResult(key)
        ret = [stat.__repr__(key) for stat in ret]
        return '\n'.join(ret)


    def test(self):
        """auto test."""
        key = 'internal_test_monitor'
        self.startRecord(key)
        sleep(3)
        self.stopRecord(key)
        self.log(self.records)
        self.log(self.getXmlResult(key))
        return 1



# ------------------------------------------------------------
# Controller
#
class MonitorController(XmlRpcBaseController):
    """Monitor controller."""
    server_class = MonitorServer

    def test(self):
        """Testing monitor server."""
        server = self.server
        key = 'internal_test_monitor'
        server.startRecord(key)
        sleep(2)
        server.stopRecord(key)
        self.log(server.getXmlResult(key))
        return 0

# ------------------------------------------------------------
# main
#
def main():
    """Control monitord server."""
    ctl = MonitorController()
    sys.exit(ctl())

def test():
    """Test wihtout rpc server."""
    mon = MonitorServer()
    mon.test()

if __name__ == '__main__':
    main()
