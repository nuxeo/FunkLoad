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

$Id: ReportRenderer.py 24736 2005-08-31 08:59:54Z bdelbosc $
"""
import os
try:
    import gdchart
    g_has_gdchart = 1
except ImportError:
    g_has_gdchart = 0
from shutil import copyfile

# ------------------------------------------------------------
# ReST rendering
#
def rst_title(title, level=1):
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


class BaseRst:
    """Base class for ReST renderer."""
    fmt_int = "%7d"
    fmt_float = "%7.3f"
    fmt_percent = "%6.2f%%"
    fmt_deco = "======="
    headers = []
    indent = 0
    image_names = []
    with_percentiles = False

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
        header = " " + " ".join([ "%7s" % h for h in headers ])
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
        return ' ' * (self.indent + 1) + deco

    def render_stat(self):
        """Render rst stat."""
        raise NotImplemented


class AllResponseRst(BaseRst):
    """AllResponseStat rendering."""
    headers = [ "CUs", "RPS", "maxRPS", "TOTAL", "SUCCESS","ERROR",
        "MIN", "AVG", "MAX" ]
    image_names = ['requests_rps', 'requests']

    def render_stat(self):
        """Render rst stat."""
        ret = [' ' * self.indent]
        stats = self.stats
        stats.finalize()
        ret.append(self.fmt_int % stats.cvus)
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
        ret = ' '.join(ret)
        return ret


class PageRst(AllResponseRst):
    """Page rendering."""
    headers = ["CUs", "SPPS", "maxSPPS", "TOTAL", "SUCCESS",
              "ERROR", "MIN", "AVG", "MAX"]
    image_names = ['pages_spps', 'pages']

class ResponseRst(BaseRst):
    """Response rendering."""
    headers = ["CUs", "TOTAL", "SUCCESS", "ERROR", "MIN", "AVG", "MAX"]
    indent = 4
    image_names = ['request_']

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
        ret.append(self.fmt_int % stats.count)
        ret.append(self.fmt_int % stats.success)
        ret.append(self.fmt_percent % stats.error_percent)
        ret.append(self.fmt_float % stats.min)
        ret.append(self.fmt_float % stats.avg)
        ret.append(self.fmt_float % stats.max)
        if self.with_percentiles:
            self._attach_percentiles(ret)
        ret = ' '.join(ret)
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
        ret = ' '.join(ret)
        return ret


class RenderRst:
    """Render stats in ReST format."""
    # number of slowest requests to display
    slowest_items = 5

    def __init__(self, config, stats, error, monitor, options):
        self.config = config
        self.stats = stats
        self.error = error
        self.monitor = monitor
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

    def append(self, text):
        """Append text to rst output."""
        self.rst.append(text)

    def renderConfig(self):
        """Render bench configuration."""
        config = self.config
        self.append(rst_title("FunkLoad_ bench report", 0))
        self.append('')
        date = config['time'][:19].replace('T', ' ')
        self.append(':date: ' + date)
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

        self.append(rst_title("Bench configuration", 2))
        self.append("* Launched: %s" % date)
        self.append("* Test: ``%s.py %s.%s``" % (config['module'],
                                                 config['class'],
                                                 config['method']))
        self.append("* Server: %s" % config['server_url'])
        self.append("* Cycles of concurrent users: %s" % config['cycles'])
        self.append("* Cycle duration: %ss" % config['duration'])
        self.append("* Sleeptime between request: from %ss to %ss" % (
            config['sleep_time_min'], config['sleep_time_max']))
        self.append("* Sleeptime between test case: %ss" %
                    config['sleep_time'])
        self.append("* Startup delay between thread: %ss" %
                    config['startup_delay'])
        self.append("* FunkLoad_ version: %s" % config['version'])
        self.append("")

    def renderTestContent(self, test):
        """Render global information about test content."""
        self.append(rst_title("Bench content", 2))
        config = self.config
        self.append('The test ``%s.%s`` contains: ' % (config['class'],
                                                       config['method']))
        self.append('')
        self.append("* %s page(s)" % test.pages)
        self.append("* %s redirect(s)" % test.redirects)
        self.append("* %s link(s)" % test.links)
        self.append("* %s image(s)" % test.images)
        self.append("* %s XML RPC call(s)" % test.xmlrpc)
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
        self.append("* %s tests" % total_tests + (
            total_tests_error and ", %s error(s)" % total_tests_error or ''))
        self.append("* %s pages" % total_pages + (
            total_pages_error and ", %s error(s)" % total_pages_error or ''))
        self.append("* %s requests" % total_responses + (
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
        for step_name in steps:
            a_step = cycle_r_steps[step_name]
            if a_step.step != current_step:
                current_step = a_step.step
                self.append(rst_title("PAGE %s: %s" % (
                    a_step.step, a_step.description or a_step.url), 3))
            self.append('* Req: %s, %s, url %s' % (a_step.number,
                                                   a_step.type, a_step.url))
            self.append('')
            self.renderCyclesStepStat(step_name)

    def renderMonitors(self):
        """Render all monitored hosts."""
        if not self.monitor or not self.with_chart:
            return
        self.append(rst_title("Monitored hosts", 2))
        for host in self.monitor.keys():
            self.renderMonitor(host)

    def renderMonitor(self, host):
        """Render a monitored host."""
        description = self.config.get(host, '')
        self.append(rst_title("%s: %s" % (host, description), 3))
        self.append("**Load average**\n\n.. image:: %s_load.png\n" % host)
        self.append("**Memory usage**\n\n.. image:: %s_mem.png\n" % host)
        self.append("**Network traffic**\n\n.. image:: %s_net.png\n" % host)

    def renderSlowestRequests(self, number):
        """Render the n slowest requests of the best cycle."""
        stats = self.stats
        self.append(rst_title("%i Slowest requests"% number, 2))
        cycle = self.getBestStpsCycle()
        cycle_name = None
        if not (cycle and stats[cycle].has_key('response_step')):
            return
        steps = stats[cycle]['response_step'].keys()
        items = []
        for step_name in steps:
            stat = stats[cycle]['response_step'][step_name]
            stat.finalize()
            items.append((stat.avg, stat.step,
                          stat.type, stat.url, stat.description))
            if not cycle_name:
                cycle_name = stat.cvus

        items.sort()
        items.reverse()
        self.append('Slowest average response time during the best cycle '
                    'with **%s** CUs:\n' % cycle_name)
        for item in items[:number]:
            self.append('* In page %s %s: %s took **%.3fs**\n'
                        '  `%s`' % (
                item[1], item[2], item[3], item[0], item[4]))

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
                    self.append('* %s time(s), code: %s, %s\n'
                                '  in %s, line %s: %s' %(
                        len(errors[err_type]),
                        err_type[0],
                        header.get('bobo-exception-type'),
                        err_type[1], err_type[2],
                        header.get('bobo-exception-value')))
                else:
                    traceback = stat.traceback and stat.traceback.replace(
                        'File ', '\n    File ') or 'No traceback.'
                    self.append('* %s time(s), code: %s::\n\n'
                                '    %s\n' %(
                        len(errors[err_type]),
                        err_type[0], traceback))

    def __repr__(self):
        self.renderConfig()
        if not self.cycles:
            self.append('No cycle found')
            return '\n'.join(self.rst)
        cycle_r = self.getRepresentativeCycleStat()

        if cycle_r.has_key('test'):
            self.renderTestContent(cycle_r['test'])

        self.renderCyclesStat('test', 'Test stats',
                              'The number of Successful **Test** Per Second '
                              '(STPS) over Concurrent Users (CUs).')
        self.renderCyclesStat('page', 'Page stats',
                              'The number of Successful **Page** Per Second '
                              '(SPPS) over Concurrent Users (CUs).\n'
                              'Note that an XML RPC call count like a page.')
        self.renderCyclesStat('response', 'Request stats',
                              'The number of **Request** Per Second (RPS) '
                              'successful or not over Concurrent Users (CUs).')
        self.renderSlowestRequests(self.slowest_items)
        self.renderMonitors()
        self.renderPageDetail(cycle_r)
        self.renderErrors()
        return '\n'.join(self.rst)




# ------------------------------------------------------------
# HTML rendering
#
class RenderHtml(RenderRst):
    """Render stats in html.

    Simply render stuff in ReST than ask docutils to build an html doc.
    """
    chart_size = (350, 250)
    big_chart_size = (640, 320)
    color_success = 0x00ff00
    color_error = 0xff0000
    color_time = 0x0000ff
    color_time_min_max = 0xccccee
    color_grid = 0xcccccc
    color_line = 0x333333
    color_plot = 0x003a6b
    color_bg = 0xffffff
    color_line = 0x000000

    def __init__(self, config, stats, error, monitor, options, css_file=None):
        RenderRst.__init__(self, config, stats, error, monitor, options)
        self.css_file = css_file
        self.report_dir = self.css_path = self.rst_path = self.html_path = None

    def prepareReportDirectory(self):
        """Create a folder to save the report."""
        # init output dir
        output_dir = os.path.abspath(self.options.output_dir)
        if not os.access(output_dir, os.W_OK):
            os.mkdir(output_dir, 0775)
        # init report dir
        config = self.config
        stamp = config['time'][:19].replace(':', '-')
        report_dir = os.path.join(output_dir, '%s-%s' % (config['id'],
                                                         stamp))
        if not os.access(report_dir, os.W_OK):
            os.mkdir(report_dir, 0775)
        self.report_dir = report_dir

    def createRstFile(self):
        """Create the ReST file."""
        rst_path = os.path.join(self.report_dir, 'index.rst')
        f = open(rst_path, 'w')
        f.write(str(self))
        f.close()
        self.rst_path = rst_path

    def copyCss(self):
        """Copy the css to the report dir."""
        css_file = self.css_file
        if css_file is not None:
            copyfile(css_file, css_dest_path)
            css_dest_path = os.path.join(self.report_dir, css_file)
        else:
            # use the one in our package_data
            from pkg_resources import resource_string
            css_content = resource_string('funkload', 'data/funkload.css')
            css_dest_path = os.path.join(self.report_dir, 'funkload.css')
            f = open(css_dest_path, 'w')
            f.write(css_content)
            f.close()
        self.css_path = css_dest_path

    def copyXmlResult(self):
        """Make a copy of the xml result."""
        xml_src_path = self.options.xml_file
        xml_dest_path = os.path.join(self.report_dir, 'funkload.xml')
        copyfile(xml_src_path, xml_dest_path)

    def generateHtml(self):
        """Ask docutils to convert our rst file into html."""
        from docutils.core import publish_cmdline
        html_path = os.path.join(self.report_dir, 'index.html')
        cmdline = "-t --stylesheet-path=%s %s %s" % (self.css_path,
                                                     self.rst_path,
                                                     html_path)
        cmd_argv = cmdline.split(' ')
        publish_cmdline(writer_name='html', argv=cmd_argv)
        self.html_path = html_path


    def render(self):
        """Create the html report."""
        self.prepareReportDirectory()
        self.createRstFile()
        self.copyCss()
        try:
            self.generateHtml()
            pass
        except ImportError:
            print "WARNING docultils not found, no html output."
            return ''
        self.createCharts()
        self.copyXmlResult()
        return self.html_path

    __call__ = render


    # Charts ------------------------------------------------------------
    # XXX need some factoring below
    def getChartSize(self, cvus):
        """Compute the right size lenght depending on the number of cvus."""
        size = list(self.chart_size)
        len_cvus = len(cvus)
        if len_cvus > 7:
            size = list(self.big_chart_size)
            size[0] = min(800, 50 * len(cvus))
        return tuple(size)

    def createCharts(self):
        """Create all charts."""
        global g_has_gdchart
        if not g_has_gdchart:
            return
        self.createMonitorCharts()
        self.createTestChart()
        self.createPageChart()
        self.createAllResponseChart()
        for step_name in self.steps:
            self.createResponseChart(step_name)

    def createTestChart(self):
        """Create the test chart."""
        image_path = str(os.path.join(self.report_dir, 'tests.png'))
        stats = self.stats
        errors = []
        stps = []
        cvus = []
        has_error = False
        for cycle in self.cycles:
            if not stats[cycle].has_key('test'):
                continue
            test = stats[cycle]['test']
            stps.append(test.tps)
            error = test.error_percent
            if error:
                has_error = True
            errors.append(error)
            cvus.append(str(test.cvus))
        color_error = has_error and self.color_error or self.color_bg
        gdchart.option(format=gdchart.GDC_PNG,
                       set_color=(self.color_success, self.color_success),
                       vol_color=self.color_error,
                       bg_color=self.color_bg, plot_color=self.color_plot,
                       line_color=self.color_line,
                       title='Successful Tests Per Second', xtitle='CUs',
                       ylabel_fmt='%.2f', ylabel2_fmt='%.2f %%',
                       ytitle='STPS', ytitle2="Errors",
                       ylabel_density=50,
                       ytitle2_color=color_error, ylabel2_color=color_error,
                       requested_ymin=0.0)
        gdchart.chart(gdchart.GDC_3DCOMBO_LINE_BAR,
                      self.getChartSize(cvus),
                      image_path,
                      cvus, stps, errors)

    def appendDelays(self, delay, delay_low, delay_high, stats):
        """ Show percentiles or min, avg and max in chart. """
        if self.options.with_percentiles:
            delay.append(stats.percentiles.perc50)
            delay_low.append(stats.percentiles.perc10)
            delay_high.append(stats.percentiles.perc90)
        else:
            delay.append(stats.avg)
            delay_low.append(stats.min)
            delay_high.append(stats.max)
   
    def getYTitle(self):
        if self.options.with_percentiles:
            return "Duration (10%, 50% 90%)"
        else:
            return "Duration (min, avg, max)"

    def createPageChart(self):
        """Create the page chart."""
        image_path = str(os.path.join(self.report_dir, 'pages.png'))
        image2_path = str(os.path.join(self.report_dir, 'pages_spps.png'))
        stats = self.stats
        errors = []
        delay = []
        delay_high = []
        delay_low = []
        spps = []
        cvus = []
        has_error = False
        for cycle in self.cycles:
            page = stats[cycle]['page']
            self.appendDelays(delay, delay_low, delay_high, page)
            spps.append(page.rps)
            error = page.error_percent
            if error:
                has_error = True
            errors.append(error)
            cvus.append(str(page.cvus))

        color_error = has_error and self.color_error or self.color_bg
        gdchart.option(format=gdchart.GDC_PNG,
                       set_color=(self.color_time_min_max,
                                  self.color_time_min_max, self.color_time),
                       vol_color=self.color_error,
                       bg_color=self.color_bg, plot_color=self.color_plot,
                       grid_color=self.color_grid,
                       line_color=self.color_line,
                       title='Page response time', xtitle='CUs',
                       ylabel_fmt='%.2fs', ylabel2_fmt='%.2f %%',
                       ytitle=self.getYTitle(), ytitle2="Errors",
                       ylabel_density=50,
                       hlc_style=gdchart.GDC_HLC_I_CAP+gdchart.
                       GDC_HLC_CONNECTING,
                       ytitle2_color=color_error, ylabel2_color=color_error,
                       requested_ymin=0.0)
        gdchart.chart(gdchart.GDC_3DCOMBO_HLC_BAR,
                      self.getChartSize(cvus),
                      image_path,
                      cvus, (delay_high, delay_low, delay), errors)
        gdchart.option(format=gdchart.GDC_PNG,
                       set_color=(self.color_success, self.color_success),
                       vol_color=self.color_error,
                       bg_color=self.color_bg, plot_color=self.color_plot,
                       line_color=self.color_line,
                       title='Successful Pages Per Second', xtitle='CUs',
                       ylabel_fmt='%.2f', ylabel2_fmt='%.2f %%',
                       ytitle='SPPS', ytitle2="Errors",
                       ylabel_density=50,
                       requested_ymin=0.0)
        gdchart.chart(gdchart.GDC_3DCOMBO_LINE_BAR,
                      self.getChartSize(cvus),
                      image2_path,
                      cvus, spps, errors)


    def createAllResponseChart(self):
        """Create global responses chart."""
        image_path = str(os.path.join(self.report_dir, 'requests.png'))
        image2_path = str(os.path.join(self.report_dir, 'requests_rps.png'))
        stats = self.stats
        errors = []
        delay = []
        delay_high = []
        delay_low = []
        rps = []
        cvus = []
        has_error = False
        for cycle in self.cycles:
            resp = stats[cycle]['response']
            self.appendDelays(delay, delay_low, delay_high, resp)
            rps.append(resp.rps)
            error = resp.error_percent
            if error:
                has_error = True
            errors.append(error)
            cvus.append(str(resp.cvus))

        color_error = has_error and self.color_error or self.color_bg
        gdchart.option(format=gdchart.GDC_PNG,
                       set_color=(self.color_time_min_max,
                                  self.color_time_min_max, self.color_time),
                       vol_color=self.color_error,
                       bg_color=self.color_bg, plot_color=self.color_plot,
                       grid_color=self.color_grid,
                       line_color=self.color_line,
                       title='Request response time', xtitle='CUs',
                       ylabel_fmt='%.2fs', ylabel2_fmt='%.2f %%',
                       ytitle=self.getYTitle(), ytitle2="Errors",
                       ylabel_density=50,
                       hlc_style=gdchart.GDC_HLC_I_CAP+gdchart.
                       GDC_HLC_CONNECTING,
                       ytitle2_color=color_error, ylabel2_color=color_error,
                       requested_ymin=0.0)
        gdchart.chart(gdchart.GDC_3DCOMBO_HLC_BAR,
                      self.getChartSize(cvus),
                      image_path,
                      cvus, (delay_high, delay_low, delay), errors)

        gdchart.option(format=gdchart.GDC_PNG,
                       set_color=(self.color_success, self.color_success),
                       vol_color=self.color_error,
                       bg_color=self.color_bg, plot_color=self.color_plot,
                       line_color=self.color_line,
                       title='Requests Per Second', xtitle='CUs',
                       ylabel_fmt='%.2f', ylabel2_fmt='%.2f %%',
                       ytitle='RPS', ytitle2="Errors",
                       ylabel_density=50,
                       ytitle2_color=color_error, ylabel2_color=color_error,
                       requested_ymin=0.0)
        gdchart.chart(gdchart.GDC_3DCOMBO_LINE_BAR,
                      self.getChartSize(cvus),
                      image2_path,
                      cvus, rps, errors)


    def createResponseChart(self, step):
        """Create responses chart."""
        stats = self.stats
        errors = []
        delay = []
        delay_high = []
        delay_low = []
        cvus = []
        number = 0
        has_error = False
        for cycle in self.cycles:
            resp = stats[cycle]['response_step'].get(step)
            if resp is None:
                delay.append(None)
                delay_low.append(None)
                delay_high.append(None)
                errors.append(None)
                cvus.append('?')
            else:
                self.appendDelays(delay, delay_low, delay_high, resp)
                error = resp.error_percent
                if error:
                    has_error = True
                errors.append(error)
                cvus.append(str(resp.cvus))
                number = resp.number
        image_path = str(os.path.join(self.report_dir,
                                      'request_%s.png' % step))
        title = str('Request %s response time' % step)
        color_error = has_error and self.color_error or self.color_bg
        gdchart.option(format=gdchart.GDC_PNG,
                       set_color=(self.color_time_min_max,
                                  self.color_time_min_max, self.color_time),
                       vol_color=self.color_error,
                       bg_color=self.color_bg, plot_color=self.color_plot,
                       grid_color=self.color_grid,
                       line_color=self.color_line,
                       title=title, xtitle='CUs',
                       ylabel_fmt='%.2fs', ylabel2_fmt='%.2f %%',
                       ytitle=self.getYTitle(), ytitle2="Errors",
                       ylabel_density=50,
                       hlc_style=gdchart.GDC_HLC_I_CAP+gdchart.
                       GDC_HLC_CONNECTING,
                       ytitle2_color=color_error, ylabel2_color=color_error,
                       requested_ymin=0.0)
        gdchart.chart(gdchart.GDC_3DCOMBO_HLC_BAR,
                      self.getChartSize(cvus),
                      image_path,
                      cvus, (delay_high, delay_low, delay), errors)

    # monitoring charts
    def createMonitorCharts(self):
        """Create all montirored server charts."""
        if not self.monitor or not self.with_chart:
            return
        self.append(rst_title("Monitored hosts", 2))
        for host in self.monitor.keys():
            self.createMonitorChart(host)


    def createMonitorChart(self, host):
        """Create monitrored server charts."""
        stats = self.monitor[host]
        time_start = float(stats[0].time)
        times = []
        for stat in stats:
            test, cycle, cvus = stat.key.split(':')
            times.append(str('%ss / %s CUs' % (
                int(float(stat.time) - time_start), cvus)))

        mem_total = int(stats[0].memTotal)
        mem_used = [mem_total - int(x.memFree) for x in stats]
        mem_used_start = mem_used[0]
        mem_used = [x - mem_used_start for x in mem_used]

        swap_total = int(stats[0].swapTotal)
        swap_used = [swap_total - int(x.swapFree) for x in stats]
        swap_used_start = swap_used[0]
        swap_used = [x - swap_used_start for x in swap_used]

        load_avg_1 = [float(x.loadAvg1min) for x in stats]
        load_avg_5 = [float(x.loadAvg5min) for x in stats]
        load_avg_15 = [float(x.loadAvg15min) for x in stats]

        net_in = [None]
        net_out = [None]
        cpu_usage = [0]
        for i in range(1, len(stats)):
            if not (hasattr(stats[i], 'CPUTotalJiffies') and
                    hasattr(stats[i-1], 'CPUTotalJiffies')):
                cpu_usage.append(None)
            else:
                dt = ((long(stats[i].IDLTotalJiffies) +
                       long(stats[i].CPUTotalJiffies)) -
                      (long(stats[i-1].IDLTotalJiffies) +
                       long(stats[i-1].CPUTotalJiffies)))
                if dt:
                    ttl = (float(long(stats[i].CPUTotalJiffies) -
                                 long(stats[i-1].CPUTotalJiffies)) /
                           dt)
                else:
                    ttl = None
                cpu_usage.append(ttl)
            if not (hasattr(stats[i], 'receiveBytes') and
                    hasattr(stats[i-1], 'receiveBytes')):
                net_in.append(None)
            else:
                net_in.append((int(stats[i].receiveBytes) -
                               int(stats[i-1].receiveBytes)) /
                              (1024 * (float(stats[i].time) -
                                       float(stats[i-1].time))))

            if not (hasattr(stats[i], 'transmitBytes') and
                    hasattr(stats[i-1], 'transmitBytes')):
                net_out.append(None)
            else:
                net_out.append((int(stats[i].transmitBytes) -
                                int(stats[i-1].transmitBytes))/
                              (1024 * (float(stats[i].time) -
                                       float(stats[i-1].time))))


        image_path = str(os.path.join(self.report_dir, '%s_load.png' % host))

        title = str('%s: cpu usage (green 1=100%%) and loadavg 1(red), '
                    '5 and 15 min' % host)
        gdchart.option(format=gdchart.GDC_PNG,
                       set_color=(0x00ff00, 0xff0000, 0x0000ff),
                       vol_color=0xff0000,
                       bg_color=self.color_bg, plot_color=self.color_plot,
                       line_color=self.color_line,
                       title=title,
                       xtitle='time and CUs',
                       ylabel_fmt='%.2f',
                       ytitle='loadavg',
                       ylabel_density=50,
                       requested_ymin=0.0)
        gdchart.chart(gdchart.GDC_LINE, self.big_chart_size,
                      image_path,
                      times, cpu_usage, load_avg_1, load_avg_5, load_avg_15)

        title = str('%s memory (green) and swap (red) usage' % host)
        image_path = str(os.path.join(self.report_dir, '%s_mem.png' % host))
        gdchart.option(format=gdchart.GDC_PNG,
                       title=title,
                       ylabel_fmt='%.0f kB',
                       ytitle='memory used kB')
        gdchart.chart(gdchart.GDC_LINE, self.big_chart_size,
                      image_path,
                      times, mem_used, swap_used)

        title = str('%s network in (green)/out (red)' % host)
        image_path = str(os.path.join(self.report_dir, '%s_net.png' % host))
        gdchart.option(format=gdchart.GDC_PNG,
                       title=title,
                       ylabel_fmt='%.0f kB/s',
                       ytitle='network')
        gdchart.chart(gdchart.GDC_LINE, self.big_chart_size,
                      image_path,
                      times, net_in, net_out)
