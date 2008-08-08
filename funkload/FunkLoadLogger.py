# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Tim Baverstock, Matthew Vail, Matt Sparks
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
from xml.sax.saxutils import quoteattr
from utils import get_version, recording

from datetime import datetime
import logging
import os
import sys
import time

# module-level log level constants
WARN = 0
INFO = 1
VERBOSE = 2
DEBUG = 3
VDEBUG = 4


class FunkLoadLogger:
    """Interface to logging and recording results using a logger."""

    def __init__(self, meta_method_name, fconf):
        """Create a logger.

        Args:
          meta_method_name: method name using the logger
          fconf: FunkLoadConfig object to access configuration
        """
        self.fconf = fconf
        self.meta_method_name = meta_method_name
        self.log_to = fconf.get('log_to', 'console file')

        # NOTE(msparks): establish a base directory for output
        log_base_dir = fconf.log_dir or ''

        # NOTE(msparks): get path specifications from config file
        log_path = fconf.get('log_path', 'funkload.log', quiet=True)
        log_path = os.path.abspath(os.path.join(log_base_dir, log_path))
        result_path = fconf.get('result_path', 'funkload.xml', quiet=True)
        result_path = os.path.abspath(os.path.join(log_base_dir, result_path))

        # NOTE(msparks): get new path specifications from options, saving old
        # paths in case higher layers need to reference the path from the config
        # file.
        if fconf.log_path:
            fconf.old_log_path = log_path
            log_path = fconf.log_path
        else:
            fconf.old_log_path = None

        if fconf.result_path:
            fconf.old_result_path = result_path
            result_path = fconf.result_path
        else:
            fconf.old_result_path = None

        # set the default log level
        if fconf.verbosity in (WARN, INFO, VERBOSE, DEBUG, VDEBUG):
            self.log_level = fconf.verbosity
        elif fconf.verbosity == 'WARN':
            self.log_level = WARN
        elif fconf.verbosity == 'INFO':
            self.log_level = INFO
        elif fconf.verbosity == 'VERBOSE':
            self.log_level = VERBOSE
        elif fconf.verbosity == 'DEBUG':
            self.log_level = DEBUG
        elif fconf.verbosity == 'VDEBUG':
            self.log_level = VDEBUG
        else:
            # given verbosity not recognized, default to INFO
            self.log_level = INFO

        # set up logger
        self.logger = fconf.opt_get('log_stream', None)
        if self.logger is None:
            self.logger = DefaultLogStream(log_to=self.log_to,
                                           log_path=log_path)

        # set up result logger
        self.results = fconf.opt_get('result_stream', None)
        if self.results is None:
            self.results = XMLResultStream(log_path=result_path)


    #------------------------------------------------------------
    # logging
    #
    def logw(self, message):
        """Warn log."""
        self.log(WARN, message)

    def logi(self, message):
        """Info log."""
        self.log(INFO, message)

    def logv(self, message):
        """Verbose info log."""
        self.log(VERBOSE, message)

    def logd(self, message):
        """Debug log."""
        self.log(DEBUG, message)

    def logdd(self, message):
        """Verbose debug log."""
        self.log(VDEBUG, message)

    def log(self, level, message):
        """Log at a given level.

        Args:
          level: (integer) WARN, INFO, VERBOSE, DEBUG, VDEBUG
          message: message to log
        """
        if not hasattr(self, 'logger'):
            print '%s: %s' % (self.meta_method_name, message)
            return

        if level == WARN and self.log_level >= WARN:
            self.logger.warn('%s: %s' % (self.meta_method_name, message))
        elif level == INFO and self.log_level >= INFO:
            self.logger.info('%s: %s' % (self.meta_method_name, message))
        elif level == VERBOSE and self.log_level >= VERBOSE:
            self.logger.info('%s: %s' % (self.meta_method_name, message))
        elif level == DEBUG and self.log_level >= DEBUG:
            self.logger.debug('%s: %s' % (self.meta_method_name, message))
        elif level >= VDEBUG and self.log_level >= VDEBUG:
            self.logger.debug('%s: %s' % (self.meta_method_name, message))


class LogStream:
    """Interface for logging. Subclasses can implement this interface to
    customize how and where logs are written.
    """
    def warn(self, message):
        """Log at WARNING level

        Args:
          message: message to log
        """
        pass

    def info(self, message):
        """Log at INFO level

        Args:
          message: message to log
        """
        pass

    def debug(self, message):
        """Log at DEBUG level

        Args:
          message: message to log
        """
        pass

    def close(self):
        """Close the logger.
        """
        pass


class DefaultLogStream(LogStream):
    """Implementation of LogStream API using the standard Python logging
    interface.
    """
    def __init__(self, log_to, log_path=None, name="FunkLoad"):
        """Constructor. Creates a logger using Python's logging module.

        Args:
          log_to: (string) targets for logging; contains 'file' and/or 'console'
          log_path: (string) output logfile path
          name: logger name to use
        """
        self.log_to = log_to
        self.log_path = log_path
        self.name = name
        self.logger = logging.getLogger(name)
        self.handlers = False

        if self.logger.handlers:
            # already setup
            return

        if "console" in log_to:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)
            self.handlers = True

        if "file" in log_to and log_path:
            formatter = logging.Formatter('%(asctime)s %(levelname)s '
                                          '%(message)s')
            handler = logging.FileHandler(log_path)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.handlers = True

        if not self.handlers:
            # silence logging from complaining about no handlers
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.CRITICAL)
        else:
            self.logger.setLevel(logging.DEBUG)

    def warn(self, message):
        """Log at WARNING level

        Args:
          message: message to log
        """
        self.logger.warning(message)

    def info(self, message):
        """Log at INFO level

        Args:
          message: message to log
        """
        self.logger.info(message)

    def debug(self, message):
        """Log at DEBUG level

        Args:
          message: message to log
        """
        self.logger.debug(message)

    def close(self):
        """Close the logger.
        """
        for hdlr in self.logger.handlers:
            logger.removeHandler(hdlr)


class ResultStream:
    """Interface for writing results. Subclasses can implement this interface to
    customize how and where results are written.
    """
    def write_header(self, **kw):
        """Write a header to the stream.

        Args:
          **kw: arbitary named arguments
        """
        pass

    def write(self, mtype, info, extra_info=None):
        """Write a result to the stream.

        Args:
          mtype: (string) message type (testResult, response, etc.)
          info: (dict) key/value pairs of information
          extra_info: (string) additional information to record
        """
        pass

    def raw_write(self, message):
        """Write text directly to the stream. Mainly for backward compatibility.
        """
        pass

    def close(self):
        """Close stream."""
        pass


class XMLResultStream(ResultStream):
    """Implements ResultStream API for writing results in XML format.
    """
    def __init__(self, log_path, name='FunkLoadResult'):
        """Constructor. Sets up a Python logger.

        Args:
          log_path: (string) path to output XML file
          name: (string) logger name to use (default: 'FunkLoadResult')
        """
        self.logger = logging.getLogger(name)

        if self.logger.handlers:
            # already setup
            return

        # make a backup of a log if it exists
        if os.access(log_path, os.F_OK):
            os.rename(log_path, log_path + '.bak-' + str(int(time.time())))
        handler = logging.FileHandler(log_path)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def _dict_to_xml_pairs(self, attributes):
        """Form a string of XML attributes from a Python dictionary.

        Args:
          attributes: dictionary of attributes

        Returns:
          string of '<name>=<value> pairs'

        Example:
          Input: { 'cycle': 1, 'cvus': 10 }
          Output: 'cycle="1" cvus="10"'
        """
        pairs = []
        for k, v in attributes.items():
            if not v.startswith('"'):
                v = quoteattr(v)
            pairs.append('%s=%s' % (k, v))
        return ' '.join(pairs)

    def write_header(self, **kw):
        """Open the result log.
        """
        xml = ['<funkload version="%s" time="%s">' % (
            get_version(), datetime.now().isoformat())]
        for key, value in kw.items():
            xml.append('<config key="%s" value=%s />' % (
                key, quoteattr(str(value))))
        self.logger.info("\n".join(xml))

    def write(self, mtype, info, extra_info=None):
        """Log a result.

        Args:
          mtype: (string) 'testResult' or 'response'
          info: dictionary of test info
          extra_info: optional string of extra information to write
        """
        text = '<%s %s' % (mtype, self._dict_to_xml_pairs(info))
        if extra_info is None:
            text = text + ' />'
        else:
            text = '%s>%s</%s>' % (text, extra_info, mtype)
        self.logger.info(text)

    def raw_write(self, message):
        """Write raw XML to the logger.

        Args:
          message: XML string to write
        """
        self.logger.info(message)

    def close(self):
        """Close the result log.
        """
        self.logger.info("</funkload>")
