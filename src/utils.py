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
"""FunkLoad common utils

$Id: utils.py 24649 2005-08-29 14:20:19Z bdelbosc $
"""
import os
import sys
import time
import logging
from time import sleep
from socket import error as SocketError
from xmlrpclib import ServerProxy


MIN_SLEEPTIME = 0.005                   # minimum sleep time to let
                                        # python threads working properly
def thread_sleep(seconds=0):
    """Sleep seconds.

    Insure that seconds is at least MIN_SLEEPTIME to let
    threads working properly."""
    #if seconds:
    #    trace('sleep %s' % seconds)
    sleep(max(abs(seconds), MIN_SLEEPTIME))

# ------------------------------------------------------------
# semaphores
#
g_recording = False
g_running = False

def recording():
    """A semaphore to tell the running threads when to begin recording."""
    global g_recording
    return g_recording

def set_recording_flag(value):
    """Enable recording."""
    global g_recording
    g_recording = value

def running():
    """A semaphore to tell the running threads that it should continue running
    ftest."""
    global g_running
    return g_running

def set_running_flag(value):
    """Set running mode on."""
    global g_running
    g_running = value


# ------------------------------------------------------------
# meta method name encodage
#
MMN_SEP = ':'                           # meta method name separator

def mmn_is_bench(meta_method_name):
    """Is it a meta method name ?."""
    return meta_method_name.count(MMN_SEP) and True or False

def mmn_encode(method_name, cycle, cvus, thread_id):
    """Encode a extra information into a method_name."""
    return MMN_SEP.join((method_name, str(cycle), str(cvus), str(thread_id)))

def mmn_decode(meta_method_name):
    """Decode a meta method name."""
    if mmn_is_bench(meta_method_name):
        method_name, cycle, cvus, thread_id = meta_method_name.split(MMN_SEP)
        return (method_name, int(cycle), int(cvus), int(thread_id))
    else:
        return (meta_method_name, 1, 0, 1)

# ------------------------------------------------------------
# logging
#
def get_default_logger(log_to, log_path=None, level=logging.DEBUG,
                       name='FunkLoad'):
    """Get a logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        # already setup
        return logger
    if log_to.count("console"):
        hdlr = logging.StreamHandler()
        logger.addHandler(hdlr)
    if log_to.count("file") and log_path:
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s')
        hdlr = logging.FileHandler(log_path)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
    if log_to.count("xml") and log_path:
        if os.access(log_path, os.F_OK):
            os.rename(log_path, log_path + '.bak-' + str(int(time.time())))
        hdlr = logging.FileHandler(log_path)
        logger.addHandler(hdlr)
    logger.setLevel(level)
    return logger


def trace(message):
    """Simple print to stdout

    Not thread safe."""
    sys.stdout.write(message)
    sys.stdout.flush()


# ------------------------------------------------------------
# xmlrpc
#
def xmlrpc_get_credential(host, port, group=None):
    """Get credential thru xmlrpc credential_server."""
    url = "http://%s:%s" % (host, port)
    server = ServerProxy(url)
    try:
        return server.getCredential('file', group)
    except SocketError:
        raise SocketError(
            'No Credential server reachable at %s, use fl-credential-ctl '
            'to start the credential server.' % url)

def xmlrpc_list_groups(host, port):
    """Get list of groups thru xmlrpc credential_server."""
    url = "http://%s:%s" % (host, port)
    server = ServerProxy(url)
    try:
        return server.listGroups()
    except SocketError:
        raise SocketError(
            'No Credential server reachable at %s, use fl-credential-ctl '
            'to start the credential server.' % url)

def xmlrpc_list_credentials(host, port, group=None):
    """Get list of users thru xmlrpc credential_server."""
    url = "http://%s:%s" % (host, port)
    server = ServerProxy(url)
    try:
        return server.listCredentials(group)
    except SocketError:
        raise SocketError(
            'No Credential server reachable at %s, use fl-credential-ctl '
            'to start the credential server.' % url)



# ------------------------------------------------------------
# misc
#
_COLOR = {'green': "\x1b[32;01m",
          'red': "\x1b[31;01m",
          'reset': "\x1b[0m"
          }

def red_str(text):
    """Return red text."""
    global _COLOR
    return _COLOR['red'] + text + _COLOR['reset']

def green_str(text):
    """Return green text."""
    global _COLOR
    return _COLOR['green'] + text + _COLOR['reset']


def get_funkload_data_path():
    """Return the path of the funkload data."""
    fl_home = os.getenv('FL_HOME')
    if fl_home is None:
        return '/usr/local/funkload'
    else:
        return os.path.join(fl_home, 'data')


def is_html(text):
    """Simple check that return True if the text is an html page."""
    if '<html' in text[:300].lower():
        return True
    return False

