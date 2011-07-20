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
"""Classes that render statistics.

$Id$
"""
import os
from shutil import copyfile
from utils import get_version
from MonitorPluginsDefault import MonitorCPU, MonitorMemFree, MonitorNetwork, MonitorCUs

LI = '*'
# ------------------------------------------------------------
# ReST rendering
#
def rst_title(title, level=1, newpage=True):
    """Return a rst title."""
    rst_level = ['=', '=', '-', '~']
    if level == 0:
        rst = [rst_level[level] * len(title)]
    else:
        rst = ['']
    rst.append(title)
    rst.append(rst_level[level] * len(title))
    rst.append('')
    return '\n'.join(rst)

def get_apdex_label(score):
    if score < 0.5:
        return "UNACCEPTABLE"
    if score < 0.7:
        return "POOR"
    if score < 0.85:
        return "FAIR"
    if score < 0.94:
        return "Good"
    return "Excellent"


class BaseRst:
    """Base class for ReST renderer."""
    fmt_int = "%18d"
    fmt_float = "%18.3f"
    fmt_str = "%18s"
    fmt_percent = "%16.2f%%"
    fmt_deco = "=================="
    sep = " "
    headers = []
    indent = 0
    image_names = []
    with_percentiles = False
    with_apdex = False

    def __init__(self, stats):
        self.stats = stats

    def __repr__(self):
        """Render stats."""
        ret = ['']
        ret.append(self.render_header())
        ret.append(self.render_stat())
        ret.append(self.render_footer())
        return '\n'.join(ret)

    def render_images(self):
        """Render images link."""
        indent = ' ' * self.indent
        rst = []
        for image_name in self.image_names:
            rst.append(indent + " .. image:: %s.png" % image_name)
        rst.append('')
        return '\n'.join(rst)

    def render_header(self, with_chart=False):
        """Render rst header."""
        headers = self.headers[:]
        if self.with_percentiles:
            self._attach_percentiles_header(headers)
        deco = ' ' + " ".join([self.fmt_deco] * len(headers))
        header = " " + " ".join([ "%18s" % h for h in headers ])
        indent = ' ' * self.indent
        ret = []
        if with_chart:
            ret.append(self.render_images())
        ret.append(indent + deco)
        ret.append(indent + header)
        ret.append(indent + deco)
        return '\n'.join(ret)

    def _attach_percentiles_header(self, headers):
        """ Attach percentile headers. """
        headers.extend(
            ["P10", "MED", "P90", "P95"])

    def _attach_percentiles(self, ret):
        """ Attach percentiles, if this is wanted. """
        percentiles = self.stats.percentiles
        fmt = self.fmt_float
        ret.extend([
            fmt % percentiles.perc10,
            fmt % percentiles.perc50,
            fmt % percentiles.perc90,
            fmt % percentiles.perc95
        ])

    def render_footer(self):
        """Render rst footer."""
        headers = self.headers[:]
        if self.with_percentiles:
            self._attach_percentiles_header(headers)
        deco = " ".join([self.fmt_deco] * len(headers))
        footer =  ' ' * (self.indent + 1) + deco
        footer +=  '\n\n'
        if self.with_apdex:
            footer +=  ' ' * (self.indent + 1) + "\* Apdex |APDEXT|"
        return footer

    def render_stat(self):
        """Render rst stat."""
        raise NotImplemented


class AllResponseRst(BaseRst):
    """AllResponseStat rendering."""
    headers = [ "CUs", "Apdex*", "Rating*", "RPS", "maxRPS", "TOTAL", "SUCCESS","ERROR",
        "MIN", "AVG", "MAX"]
    image_names = ['requests_rps', 'requests']
    with_apdex = True

    def render_stat(self):
        """Render rst stat."""
        ret = [' ' * self.indent]
        stats = self.stats
        stats.finalize()
        ret.append(self.fmt_int % stats.cvus)
        if self.with_apdex:
            ret.append(self.fmt_float % stats.apdex_score)
            ret.append(self.fmt_str % get_apdex_label(stats.apdex_score))
        ret.append(self.fmt_float % stats.rps)
        ret.append(self.fmt_float % stats.rps_max)
        ret.append(self.fmt_int % stats.count)
        ret.append(self.fmt_int % stats.success)
        ret.append(self.fmt_percent % stats.error_percent)
        ret.append(self.fmt_float % stats.min)
        ret.append(self.fmt_float % stats.avg)
        ret.append(self.fmt_float % stats.max)
        if self.with_percentiles:
            self._attach_percentiles(ret)
        ret = self.sep.join(ret)
        return ret


class PageRst(AllResponseRst):
    """Page rendering."""
    headers = ["CUs", "Apdex*", "Rating", "SPPS", "maxSPPS", "TOTAL", "SUCCESS",
              "ERROR", "MIN", "AVG", "MAX"]
    image_names = ['pages_spps', 'pages']
    with_apdex = True

class ResponseRst(BaseRst):
    """Response rendering."""
    headers = ["CUs", "Apdex*", "Rating", "TOTAL", "SUCCESS", "ERROR", "MIN", "AVG", "MAX"]
    indent = 4
    image_names = ['request_']
    with_apdex = True

    def __init__(self, stats):
        BaseRst.__init__(self, stats)
        # XXX quick fix for #1017
        self.image_names = [name + str(stats.step) + '.' + str(stats.number)
                            for name in self.image_names]

    def render_stat(self):
        """Render rst stat."""
        stats = self.stats
        stats.finalize()
        ret = [' ' * self.indent]
        ret.append(self.fmt_int % stats.cvus)
        ret.append(self.fmt_float % stats.apdex_score)
        ret.append(self.fmt_str % get_apdex_label(stats.apdex_score))
        ret.append(self.fmt_int % stats.count)
        ret.append(self.fmt_int % stats.success)
        ret.append(self.fmt_percent % stats.error_percent)
        ret.append(self.fmt_float % stats.min)
        ret.append(self.fmt_float % stats.avg)
        ret.append(self.fmt_float % stats.max)
        if self.with_percentiles:
            self._attach_percentiles(ret)
        ret = self.sep.join(ret)
        return ret


class TestRst(BaseRst):
    """Test Rendering."""
    headers = ["CUs", "STPS", "TOTAL", "SUCCESS", "ERROR"]
    image_names = ['tests']
    with_percentiles = False

    def render_stat(self):
        """Render rst stat."""
        stats = self.stats
        stats.finalize()
        ret = [' ' * self.indent]
        ret.append(self.fmt_int % stats.cvus)
        ret.append(self.fmt_float % stats.tps)
        ret.append(self.fmt_int % stats.count)
        ret.append(self.fmt_int % stats.success)
        ret.append(self.fmt_percent % stats.error_percent)
        ret = self.sep.join(ret)
        return ret


class RenderRst:
    """Render stats in ReST format."""
    # number of slowest requests to display
    slowest_items = 5

    def __init__(self, config, stats, error, monitor, monitorconfig, options):
        self.config = config
        self.stats = stats
        self.error = error
        self.monitor = monitor
        self.monitorconfig = monitorconfig
        self.options = options
        self.rst = []

        cycles = stats.keys()
        cycles.sort()
        self.cycles = cycles
        if options.with_percentiles:
            BaseRst.with_percentiles = True
        if options.html:
            self.with_chart = True
        else:
            self.with_chart = False
        self.date = config['time'][:19].replace('T', ' ')


    def getRepresentativeCycleStat(self):
        """Return the cycle stat with the maximum number of steps."""
        stats = self.stats
        max_steps = 0
        cycle_r = None
        for cycle in self.cycles:
            steps = stats[cycle]['response_step'].keys()
            if cycle_r is None:
                cycle_r = stats[cycle]
            if len(steps) > max_steps:
                max_steps = steps
                cycle_r = stats[cycle]
        return cycle_r

    def getBestStpsCycle(self):
        """Return the cycle with the maximum STPS."""
        stats = self.stats
        max_stps = -1
        cycle_r = None
        for cycle in self.cycles:
            if not stats[cycle].has_key('test'):
                continue
            stps = stats[cycle]['test'].tps
            if stps > max_stps:
                max_stps = stps
                cycle_r = cycle
        if cycle_r is None and len(self.cycles):
            # no test ends during a cycle return the first one
            cycle_r = self.cycles[0]
        return cycle_r

    def getBestCycle(self):
        """Return the cycle with the maximum Apdex and SPPS."""
        stats = self.stats
        max_spps = -1
        cycle_r = None
        for cycle in self.cycles:
            if not stats[cycle].has_key('page'):
                continue
            if stats[cycle]['page'].apdex_score < 0.85:
                continue
            spps = stats[cycle]['page'].rps * stats[cycle]['page'].apdex_score
            if spps > max_spps:
                max_spps = spps
                cycle_r = cycle
        if cycle_r is None and len(self.cycles):
            # no test ends during a cycle return the first one
            cycle_r = self.cycles[0]
        return cycle_r

    def append(self, text):
        """Append text to rst output."""
        self.rst.append(text)

    def renderHeader(self):
        config = self.config
        self.append(rst_title("FunkLoad_ bench report", 0))
        self.append('')
        self.append(':date: ' + self.date)
        description = [config['class_description']]
        description += ["Bench result of ``%s.%s``: " % (config['class'],
                                                       config['method'])]
        description += [config['description']]
        indent = "\n           "
        self.append(':abstract: ' + indent.join(description))
        self.append('')
        self.append(".. _FunkLoad: http://funkload.nuxeo.org/")
        self.append(".. sectnum::    :depth: 2")
        self.append(".. contents:: Table of contents")
        self.append(".. |APDEXT| replace:: \ :sub:`%.1f`" % self.options.apdex_t)

    def renderConfig(self):
        """Render bench configuration and metadata."""
        self.renderHeader()
        config = self.config
        self.append(rst_title("Bench configuration", 2))
        self.append(LI + " Launched: %s" % self.date)
        if config.get('node'):
            self.append(LI + " From: %s" % config['node'])
        self.append(LI + " Test: ``%s.py %s.%s``" % (config['module'],
                                                 config['class'],
                                                 config['method']))
        if config.get('label'):
            self.append(LI + " Label: %s" % config['label'])
        self.append(LI + " Target server: %s" % config['server_url'])
        self.append(LI + " Cycles of concurrent users: %s" % config['cycles'])
        self.append(LI + " Cycle duration: %ss" % config['duration'])
        self.append(LI + " Sleeptime between request: from %ss to %ss" % (
            config['sleep_time_min'], config['sleep_time_max']))
        self.append(LI + " Sleeptime between test case: %ss" %
                    config['sleep_time'])
        self.append(LI + " Startup delay between thread: %ss" %
                    config['startup_delay'])
        self.append(LI + " Apdex: |APDEXT|")
        self.append(LI + " FunkLoad_ version: %s" % config['version'])
        self.append("")
        # check for metadata
        has_meta = False
        for key in config.keys():
            if key.startswith("meta:"):
                if not has_meta:
                    self.append("Bench metadata:")
                    self.append('')
                    has_meta = True
                self.append(LI + " %s: %s" % (key[5:], config[key]))
        if has_meta:
            self.append("")

    def renderTestContent(self, test):
        """Render global information about test content."""
        self.append(rst_title("Bench content", 2)) 
        config = self.config
        self.append('The test ``%s.%s`` contains: ' % (config['class'],
                                                       config['method']))
        self.append('')
        self.append(LI + " %s page(s)" % test.pages)
        self.append(LI + " %s redirect(s)" % test.redirects)
        self.append(LI + " %s link(s)" % test.links)
        self.append(LI + " %s image(s)" % test.images)
        self.append(LI + " %s XML RPC call(s)" % test.xmlrpc)
        self.append('')

        self.append('The bench contains:')
        total_tests = 0
        total_tests_error = 0
        total_pages = 0
        total_pages_error = 0
        total_responses = 0
        total_responses_error = 0
        stats = self.stats
        for cycle in self.cycles:
            if stats[cycle].has_key('test'):
                total_tests += stats[cycle]['test'].count
                total_tests_error += stats[cycle]['test'].error
            if stats[cycle].has_key('page'):
                stat = stats[cycle]['page']
                stat.finalize()
                total_pages += stat.count
                total_pages_error += stat.error
            if stats[cycle].has_key('response'):
                total_responses += stats[cycle]['response'].count
                total_responses_error += stats[cycle]['response'].error
        self.append('')
        self.append(LI + " %s tests" % total_tests + (
            total_tests_error and ", %s error(s)" % total_tests_error or ''))
        self.append(LI + " %s pages" % total_pages + (
            total_pages_error and ", %s error(s)" % total_pages_error or ''))
        self.append(LI + " %s requests" % total_responses + (
            total_responses_error and ", %s error(s)" %
            total_responses_error or ''))
        self.append('')


    def renderCyclesStat(self, key, title, description=''):
        """Render a type of stats for all cycles."""
        stats = self.stats
        first = True
        if key == 'test':
            klass = TestRst
        elif key == 'page':
            klass = PageRst
        elif key == 'response':
            klass = AllResponseRst
        self.append(rst_title(title, 2))
        if description:
            self.append(description)
            self.append('')
        renderer = None
        for cycle in self.cycles:
            if not stats[cycle].has_key(key):
                continue
            renderer = klass(stats[cycle][key])
            if first:
                self.append(renderer.render_header(self.with_chart))
                first = False
            self.append(renderer.render_stat())
        if renderer is not None:
            self.append(renderer.render_footer())
        else:
            self.append('Sorry no %s have finished during a cycle, '
                        'the cycle duration is too short.\n' % key)


    def renderCyclesStepStat(self, step):
        """Render a step stats for all cycle."""
        stats = self.stats
        first = True
        renderer = None
        for cycle in self.cycles:
            stat = stats[cycle]['response_step'].get(step)
            if stat is None:
                continue
            renderer = ResponseRst(stat)
            if first:
                self.append(renderer.render_header(self.with_chart))
                first = False
            self.append(renderer.render_stat())
        if renderer is not None:
            self.append(renderer.render_footer())

    def renderPageDetail(self, cycle_r):
        """Render a page detail."""
        self.append(rst_title("Page detail stats", 2))
        cycle_r_steps = cycle_r['response_step']
        steps = cycle_r['response_step'].keys()
        steps.sort()
        self.steps = steps
        current_step = -1
        newpage = False
        for step_name in steps:
            a_step = cycle_r_steps[step_name]
            if a_step.step != current_step:
                current_step = a_step.step
                self.append(rst_title("PAGE %s: %s" % (
                    a_step.step, a_step.description or a_step.url), 3, newpage))
                newpage = True
            self.append(LI + ' Req: %s, %s, url ``%s``' % (a_step.number,
                                                           a_step.type,
                                                           a_step.url))
            self.append('')
            self.renderCyclesStepStat(step_name)


    def createMonitorCharts(self):
        pass

    def renderMonitors(self):
        """Render all monitored hosts."""
        if not self.monitor or not self.with_chart:
            return
        charts = self.createMonitorCharts()
        if charts == None:
            return
        for host in charts.keys():
            self.renderMonitor(host, charts[host])


    def renderMonitor(self, host, charts):
        """Render a monitored host."""
        description = self.config.get(host, '')
        if len(charts)>0:
            self.append(rst_title("%s: %s" % (host, description), 3))
        for chart in charts:
            self.append("**%s**\n\n.. image:: %s\n" % (
                    chart[0], os.path.basename(chart[1])))

    def renderSlowestRequests(self, number):
        """Render the n slowest requests of the best cycle."""
        stats = self.stats
        self.append(rst_title("Slowest requests", 2))
        cycle = self.getBestCycle()
        cycle_name = None
        if not (cycle and stats[cycle].has_key('response_step')):
            return
        steps = stats[cycle]['response_step'].keys()
        items = []
        for step_name in steps:
            stat = stats[cycle]['response_step'][step_name]
            stat.finalize()
            items.append((stat.avg, stat.step,
                          stat.type, stat.url, stat.description, 
                          stat.apdex_score))
            if not cycle_name:
                cycle_name = stat.cvus

        items.sort()
        items.reverse()
        self.append('The %d slowest average response time during the '
                    'best cycle with **%s** CUs:\n' % (number, cycle_name))
        for item in items[:number]:
            self.append(LI + ' In page %s, Apdex rating: %s, avg response time: %3.2fs, %s: ``%s``\n'
                        '  `%s`' % (
                item[1], get_apdex_label(item[5]), item[0], item[2], item[3], item[4]))

    def renderErrors(self):
        """Render error list."""
        if not len(self.error):
            return
        self.append(rst_title("Failures and Errors", 2))
        for status in ('Failure', 'Error'):
            if not self.error.has_key(status):
                continue
            stats = self.error[status]
            errors = {}
            for stat in stats:
                header = stat.header
                key = (stat.code,
                       header.get('bobo-exception-file'),
                       header.get('bobo-exception-line'),
                       )
                err_list = errors.setdefault(key, [])
                err_list.append(stat)
            err_types = errors.keys()
            err_types.sort()
            self.append(rst_title(status + 's', 3))
            for err_type in err_types:
                stat = errors[err_type][0]
                if err_type[1]:
                    self.append(LI + ' %s time(s), code: %s, %s\n'
                                '  in %s, line %s: %s' %(
                        len(errors[err_type]),
                        err_type[0],
                        header.get('bobo-exception-type'),
                        err_type[1], err_type[2],
                        header.get('bobo-exception-value')))
                else:
                    traceback = stat.traceback and stat.traceback.replace(
                        'File ', '\n    File ') or 'No traceback.'
                    self.append(LI + ' %s time(s), code: %s::\n\n'
                                '    %s\n' %(
                        len(errors[err_type]),
                        err_type[0], traceback))

    def renderDefinitions(self):
        """Render field definition."""
        self.append(rst_title("Definitions", 2))
        self.append(LI + ' CUs: Concurrent users or number of concurrent threads'
                    ' executing tests.')
        self.append(LI + ' Request: a single GET/POST/redirect/xmlrpc request.')
        self.append(LI + ' Page: a request with redirects and resource'
                    ' links (image, css, js) for an html page.')
        self.append(LI + ' STPS: Successful tests per second.')
        self.append(LI + ' SPPS: Successful pages per second.')
        self.append(LI + ' RPS: Requests per second, successful or not.')
        self.append(LI + ' maxSPPS: Maximum SPPS during the cycle.')
        self.append(LI + ' maxRPS: Maximum RPS during the cycle.')
        self.append(LI + ' MIN: Minimum response time for a page or request.')
        self.append(LI + ' AVG: Average response time for a page or request.')
        self.append(LI + ' MAX: Maximmum response time for a page or request.')
        self.append(LI + ' P10: 10th percentile, response time where 10 percent'
                    ' of pages or requests are delivered.')
        self.append(LI + ' MED: Median or 50th percentile, response time where half'
                    ' of pages or requests are delivered.')
        self.append(LI + ' P90: 90th percentile, response time where 90 percent'
                    ' of pages or requests are delivered.')
        self.append(LI + ' P95: 95th percentile, response time where 95 percent'
                    ' of pages or requests are delivered.')
        self.append(LI + ''' Apdex T: Application Performance Index, 
  this is a numerical measure of user satisfaction, it is based
  on three zones of application responsiveness:

  - Satisfied: The user is fully productive. This represents the
    time value (T seconds) below which users are not impeded by
    application response time.

  - Tolerating: The user notices performance lagging within
    responses greater than T, but continues the process.

  - Frustrated: Performance with a response time greater than 4*T
    seconds is unacceptable, and users may abandon the process.

    By default T is set to 1.5s this means that response time between 0
    and 1.5s the user is fully productive, between 1.5 and 6s the
    responsivness is tolerating and above 6s the user is frustrated.

    The Apdex score converts many measurements into one number on a
    uniform scale of 0-to-1 (0 = no users satisfied, 1 = all users
    satisfied).

    Visit http://www.apdex.org/ for more information.''')
        self.append(LI + ''' Rating: To ease interpretation the Apdex
  score is also represented as a rating:

  - U for UNACCEPTABLE represented in gray for a score between 0 and 0.5 

  - P for POOR represented in red for a score between 0.5 and 0.7

  - F for FAIR represented in yellow for a score between 0.7 and 0.85

  - G for Good represented in green for a score between 0.85 and 0.94

  - E for Excellent represented in blue for a score between 0.94 and 1.''')
        self.append('')
        self.append('Report generated with FunkLoad_ ' + get_version() +
                    ', more information available on the '
                    '`FunkLoad site <http://funkload.nuxeo.org/#benching>`_.')

    def renderHook(self):
        """Hook for post processing"""
        pass

    def __repr__(self):
        self.renderConfig()
        if not self.cycles:
            self.append('No cycle found')
            return '\n'.join(self.rst)
        cycle_r = self.getRepresentativeCycleStat()

        if cycle_r.has_key('test'):
            self.renderTestContent(cycle_r['test'])

        self.renderCyclesStat('test', 'Test stats',
                              'The number of Successful **Tests** Per Second '
                              '(STPS) over Concurrent Users (CUs).')
        self.renderCyclesStat('page', 'Page stats',
                              'The number of Successful **Pages** Per Second '
                              '(SPPS) over Concurrent Users (CUs).\n'
                              'Note that an XML RPC call count like a page.')
        self.renderCyclesStat('response', 'Request stats',
                              'The number of **Requests** Per Second (RPS) '
                              'successful or not over Concurrent Users (CUs).')
        self.renderSlowestRequests(self.slowest_items)
        self.renderMonitors()
        self.renderPageDetail(cycle_r)
        self.renderErrors()
        self.renderDefinitions()
        self.renderHook()
        return '\n'.join(self.rst)

    def getMonitorConfig(self, host):
        """Return the host config or a default for backward compat"""
        if host in self.monitorconfig:
            return self.monitorconfig[host]
        return {'MonitorCPU': MonitorCPU().getConfig(),
                'MonitorMemFree': MonitorMemFree().getConfig(),
                'MonitorNetwork': MonitorNetwork(None).getConfig(),
                'MonitorCUs': MonitorCUs().getConfig()}

