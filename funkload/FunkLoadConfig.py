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
from utils import mmn_decode, mmn_is_bench

import os
import FunkLoadLogger
from ConfigParser import ConfigParser, NoSectionError, NoOptionError

_marker = []


class FunkLoadConfig:
    """A dumping ground for config parameters, so they're only literals once"""
    def __init__(self, section, methodName, suite_name, options, class_name):
        """Access to the config file.

        Args:
          section: default section to use for get*() methods
          methodName: test method name accessing the config
          suite_name: name of test suite
          options: object with attributes to access various settings
          class_name: test class name

        Notes:
          The options parameter can be specified as None, in which case all
          options are set to their defaults, or as follows:

          class Dummy:
            pass
          opts = Dummy()
          opts.config_path = "/some/path/to/file.conf"
          config = FunkLoadConfig(..., options=opts, ...)

          options recognized:
            verbosity: FunkLoadLogger level (WARN, INFO (default), VERBOSE, ...)
            config_dir: base directory to look for config file (<class>.conf)
            config_path: full path to config file (/some/path/myconf.conf)
            log_path: full path to use for logging (/some/path/foo.log)
            result_path: full path to use for results (/some/path/bar.xml)
            log_dir: base directory in which to place logs and results
        """
        # meta_method_name is only used for auxillary logging. Eliminate.
        self.section = section
        self.meta_method_name = methodName
        self.options = options

        self.verbosity = getattr(options, 'verbosity', FunkLoadLogger.INFO)
        self.config_dir = getattr(options, 'config_dir', None)
        self.config_path = getattr(options, 'config_path', None)
        self.log_path = getattr(options, 'log_path', None)
        self.result_path = getattr(options, 'result_path', None)
        self.log_dir = getattr(options, 'log_dir', None)

        # NOTE(mattv): Changed the following lines from the original funkload
        # library to allow the specification of a configuration file without
        # using an environment variable.  Now, you use it through the "options"
        # parameter in the __init__ function of this class
        if self.config_dir == None:
            config_directory = os.getenv('FL_CONF_PATH', '.')
        else:
            config_directory = self.config_dir

        # NOTE(msparks): allow full path to config file to be passed via options
        # parameter in __init__.
        if self.config_path:
            config_path = self.config_path
        else:
            config_path = os.path.join(config_directory, class_name + '.conf')
            config_path = os.path.abspath(config_path)

        if not os.path.exists(config_path):
            config_path = "Missing: " + config_path

        config = ConfigParser()
        config.read(config_path)
        self._config = config
        self._config_path = config_path

    #------------------------------------------------------------
    # options and configuration file utils
    #
    def opt_get(self, key, default=_marker):
        value = getattr(self.options, key, default)
        if value is _marker:
            raise
        return value

    def get(self, key, default=_marker, section=None, quiet=False):
        """Return an entry from the options or configuration file."""
        if section is None:
            section = self.section
        # check for a command line options
        opt_key = '%s_%s' % (section, key)
        opt_val = getattr(self.options, opt_key, None)
        if opt_val:
            #print('[%s] %s = %s from options.' % (section, key, opt_val))
            return opt_val
        # check for the configuration file if opt val is None
        # or nul
        try:
            val = self._config.get(section, key)
        except (NoSectionError, NoOptionError):
            if not quiet:
                self.logd('[%s] %s not found' % (section, key))
            if default is _marker:
                raise
            val = default
        #print('[%s] %s = %s from config.' % (section, key, val))
        return val

    def getInt(self, key, default=_marker, section=None, quiet=False):
        """Return an integer from the configuration file."""
        return int(self.get(key, default=default, section=section,
                            quiet=quiet))

    def getFloat(self, key, default=_marker, section=None, quiet=False):
        """Return a float from the configuration file."""
        return float(self.get(key, default=default, section=section,
                              quiet=quiet))

    def getList(self, key, default=_marker, section=None, quiet=False,
                     separator=None):
        """Return a list from the configuration file."""
        value = self.get(key, section=section, default=default,
                              quiet=quiet)
        if value is default:
            return value
        if separator is None:
            separator = ':'
        if separator in value:
            return value.split(separator)
        return [value]

    # TODO(weasel): Eliminate requirement for this (config and logger)
    def logi(self, message):
        """Interface with the logger if it exists, else print to stdout. Log at
        the INFO level.

        Args:
          message: message to log
        """
        if not hasattr(self, 'logger'):
            print '%s: %s' % (self.meta_method_name, message)
        else:
            self.logger.logi(message)

    def logd(self, message):
        """Interface with the logger if it exists, else print to stdout. Log at
        the DEBUG level.

        Args:
          message: message to log
        """
        if not hasattr(self, 'logger'):
            print '%s: %s' % (self.meta_method_name, message)
        else:
            self.logger.logd(message)

    def set_logger(self, logger):
        """Set the logger to use.

        Args:
          logger: FunkLoadLogger instance
        """
        self.logger = logger

