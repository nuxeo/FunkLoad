# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
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
"""A ConfigParser overriden by OptionParser.

$Id$
"""
import os
import logging
from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from utils import get_logger

_marker = object()

class OptionConfigParser:
    """A ConfigParser that can be override by options.

    options is a OptionParser object.
    logger is a Logger

    Options should be of the format: section_key.
    """
    def __init__(self, config_path, options=None):
        if not os.path.exists(config_path):
            config_path = "Missing: "+ config_path
        self.config_path = config_path
        config = ConfigParser()
        config.read(config_path)
        self._config = config
        self._options = options
        logger = get_logger(name="config", level=logging.INFO)
        self.logd = logger.debug
        self.logi = logger.info

    def get(self, section, key, default=_marker, quiet=False):
        """Return an entry from the options or configuration file."""
        # check for a command line options
        options = self._options
        if options is not None:
            opt_key = '%s_%s' % (section, key)
            opt_val = getattr(self._options, opt_key, None)
            if opt_val:
                self.logd('[%s] %s = %s from options.' %
                           (section, key, opt_val))
            return opt_val
        # check for the configuration file if opt val is None
        # or nul
        try:
            val = self._config.get(section, key)
        except (NoSectionError, NoOptionError):
            if not quiet:
                self.logi('[%s] %s not found' % (section, key))
            if default is _marker:
                raise
            val = default
        self.logd('[%s] %s = %s from config.' % (section, key, val))
        return val

    def getInt(self, section, key, default=_marker, quiet=False):
        """Return an integer from options or configuration file."""
        return int(self.get(section, key, default, quiet))

    def getFloat(self, section, key, default=_marker, quiet=False):
        """Return a float from options or configuration file."""
        return float(self.get(section, key, default, quiet))

    def getList(self, section, key, default=_marker, quiet=False,
                separator=None):
        """Return a list from options or configuration file."""
        value = self.get(section, key, default, quiet)
        if value is default:
            return value
        if separator is None:
            separator = ':'
        if value.count(separator):
            return value.split(separator)
        return [value]
