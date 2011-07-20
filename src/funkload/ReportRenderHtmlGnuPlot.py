# (C) Copyright 2009 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: Kelvin Ward
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
"""Render chart using gnuplot >= 4.2

$Id$
"""

import os
import sys
import re
from commands import getstatusoutput
from ReportRenderRst import rst_title
from ReportRenderHtmlBase import RenderHtmlBase
from datetime import datetime
from MonitorPlugins import MonitorPlugins
from MonitorPluginsDefault import MonitorCPU, MonitorMemFree, MonitorNetwork, MonitorCUs

def gnuplot(script_path):
    """Execute a gnuplot script."""
    path = os.path.dirname(os.path.abspath(script_path))
    if sys.platform.lower().startswith('win'):
        # commands module doesn't work on win and gnuplot is named
        # wgnuplot
        ret = os.system('cd "' + path + '" && wgnuplot "' +
                        os.path.abspath(script_path) + '"')
        if ret != 0:
            raise RuntimeError("Failed to run wgnuplot cmd on " +
                               os.path.abspath(script_path))

    else:
        cmd = 'cd ' + path + '; gnuplot ' + os.path.abspath(script_path)
        ret, output = getstatusoutput(cmd)
        if ret != 0:
            raise RuntimeError("Failed to run gnuplot cmd: " + cmd +
                               "\n" + str(output))

def gnuplot_scriptpath(base, filename):
    """Return a file path string from the join of base and file name for use
    inside a gnuplot script.

    Backslashes (the win os separator) are replaced with forward
    slashes. This is done because gnuplot scripts interpret backslashes
    specially even in path elements.
    """
    return os.path.join(base, filename).replace("\\", "/")

class FakeMonitorConfig:
    def __init__(self, name):
        self.name = name

class RenderHtmlGnuPlot(RenderHtmlBase):
    """Render stats in html using gnuplot

    Simply render stuff in ReST than ask docutils to build an html doc.
    """
    chart_size = (640, 540)
    #big_chart_size = (640, 480)
    ticpattern = re.compile('(\:\d+)\ ')

    def getChartSizeTmp(self, cvus):
        """Override for gnuplot format"""
        return str(self.chart_size[0]) + ',' + str(self.chart_size[1])

    def getXRange(self):
        """Return the max CVUs range."""
        maxCycle = self.config['cycles'].split(',')[-1]
        maxCycle = str(maxCycle[:-1].strip())
        if maxCycle.startswith("["):
            maxCycle = maxCycle[1:]
        return "[0:" + str(int(maxCycle) + 1) + "]"

    def useXTicLabels(self):
        """Guess if we need to use labels for x axis or number."""
        cycles = self.config['cycles'][1:-1].split(',')
        if len(cycles) <= 1:
            # single cycle
            return True
        if len(cycles) != len(set(cycles)):
            # duplicates cycles
            return True
        cycles = [int(i) for i in cycles]
        for i, v in enumerate(cycles[1:]):
            # unordered cycles
            if cycles[i] > v:
                return True
        return False

    def fixXLabels(self, lines):
        """Fix gnuplot script if CUs are not ordered."""
        if not self.useXTicLabels():
            return lines
        # remove xrange line
        out = lines.replace('set xrange', '#set xrange')
        # rewrite plot using xticlabels
        out = out.replace(' 1:', ' :')
        out = self.ticpattern.sub(r'\1:xticlabels(1) ', out)
        return out

    def createTestChart(self):
        """Create the test chart."""
        image_path = gnuplot_scriptpath(self.report_dir, 'tests.png')
        gplot_path = str(os.path.join(self.report_dir, 'tests.gplot'))
        data_path  = gnuplot_scriptpath(self.report_dir, 'tests.data')
        stats = self.stats
        # data
        lines = ["CUs STPS ERROR"]
        cvus = []
        has_error = False
        for cycle in self.cycles:
            if not stats[cycle].has_key('test'):
                continue
            values = []
            test = stats[cycle]['test']
            values.append(str(test.cvus))
            cvus.append(str(test.cvus))
            values.append(str(test.tps))
            error = test.error_percent
            if error:
                has_error = True
            values.append(str(error))
            lines.append(' '.join(values))
        if len(lines) == 1:
            # No tests finished during the cycle
            return
        f = open(data_path, 'w')
        f.write('\n'.join(lines) + '\n')
        f.close()
        # script
        lines = ['set output "' + image_path +'"']
        lines.append('set title "Successful Tests Per Second"')
        lines.append('set terminal png size ' + self.getChartSizeTmp(cvus))
        lines.append('set xlabel "Concurrent Users"')
        lines.append('set ylabel "Test/s"')
        lines.append('set grid back')
        lines.append('set xrange ' + self.getXRange())

        if not has_error:
            lines.append('plot "%s" u 1:2 w linespoints lw 2 lt 2 t "STPS"' % data_path)
        else:
            lines.append('set format x ""')
            lines.append('set multiplot')
            lines.append('unset title')
            lines.append('unset xlabel')
            lines.append('set size 1, 0.7')
            lines.append('set origin 0, 0.3')
            lines.append('set lmargin 5')
            lines.append('set bmargin 0')
            lines.append('plot "%s" u 1:2 w linespoints lw 2 lt 2 t "STPS"' % data_path)
            lines.append('set format x "% g"')
            lines.append('set bmargin 3')
            lines.append('set autoscale y')
            lines.append('set style fill solid .25')
            lines.append('set size 1.0, 0.3')
            lines.append('set ytics 20')
            lines.append('set xlabel "Concurrent Users"')
            lines.append('set ylabel "% errors"')
            lines.append('set origin 0.0, 0.0')
            lines.append('set yrange [0:100]')
            lines.append('plot "%s" u 1:3 w linespoints lt 1 lw 2 t "%% Errors"' % data_path)
            lines.append('unset multiplot')
        f = open(gplot_path, 'w')
        lines = self.fixXLabels('\n'.join(lines) + '\n')
        f.write(lines)
        f.close()
        gnuplot(gplot_path)
        return

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


    def createPageChart(self):
        """Create the page chart."""
        image_path = gnuplot_scriptpath(self.report_dir, 'pages_spps.png')
        image2_path = gnuplot_scriptpath(self.report_dir, 'pages.png')
        gplot_path = str(os.path.join(self.report_dir, 'pages.gplot'))
        data_path = gnuplot_scriptpath(self.report_dir, 'pages.data')
        stats = self.stats
        # data
        lines = ["CUs SPPS ERROR MIN AVG MAX P10 P50 P90 P95 APDEX E G F P U"]
        cvus = []
        has_error = False
        apdex_t = 0
        for cycle in self.cycles:
            if not stats[cycle].has_key('page'):
                continue
            values = []
            page = stats[cycle]['page']
            values.append(str(page.cvus))
            cvus.append(str(page.cvus))
            values.append(str(page.rps))
            error = page.error_percent
            if error:
                has_error = True
            values.append(str(error))
            values.append(str(page.min))
            values.append(str(page.avg))
            values.append(str(page.max))
            values.append(str(page.percentiles.perc10))
            values.append(str(page.percentiles.perc50))
            values.append(str(page.percentiles.perc90))
            values.append(str(page.percentiles.perc95))
            score = page.apdex_score
            apdex_t = page.apdex.apdex_t
            values.append(str(score))
            apdex = ['0', '0', '0', '0', '0']
            if score < 0.5:
                apdex[4] = str(score)
            elif score < 0.7:
                apdex[3] = str(score)
            elif score < 0.85:
                apdex[2] = str(score)
            elif score < 0.94:
                apdex[1] = str(score)
            else:
                apdex[0] = str(score)
            values = values + apdex
            lines.append(' '.join(values))
        if len(lines) == 1:
            # No pages finished during a cycle
            return
        f = open(data_path, 'w')
        f.write('\n'.join(lines) + '\n')
        f.close()
        # script
        lines = ['set output "' + image_path +'"']
        lines.append('set title "Successful Pages Per Second"')
        lines.append('set ylabel "Pages Per Second"')
        lines.append('set grid back')
        lines.append('set xrange ' + self.getXRange())
        lines.append('set terminal png size ' + self.getChartSizeTmp(cvus))
        lines.append('set format x ""')
        lines.append('set multiplot')
        lines.append('unset title')
        lines.append('unset xlabel')
        lines.append('set bmargin 0')
        lines.append('set lmargin 8')
        lines.append('set rmargin 9.5')
        lines.append('set key inside top')
        if has_error:
            lines.append('set size 1, 0.4')
            lines.append('set origin 0, 0.6')
        else:
            lines.append('set size 1, 0.6')
            lines.append('set origin 0, 0.4')
        lines.append('plot "%s" u 1:2 w linespoints lw 2 lt 2 t "SPPS"' % data_path)
        # apdex
        lines.append('set boxwidth 0.8')
        lines.append('set style fill solid .7')
        lines.append('set ylabel "Apdex %.1f" ' % apdex_t)
        lines.append('set yrange [0:1]')
        lines.append('set key outside top')
        if has_error:
            lines.append('set origin 0.0, 0.3')
            lines.append('set size 1.0, 0.3')
        else:
            lines.append('set size 1.0, 0.4')
            lines.append('set bmargin 3')
            lines.append('set format x "% g"')
            lines.append('set xlabel "Concurrent Users"')
            lines.append('set origin 0.0, 0.0')

        lines.append('plot "%s" u 1:12 w boxes lw 2 lt rgb "#99CDFF" t "E", "" u 1:13 w boxes lw 2 lt rgb "#00FF01" t "G", "" u 1:14 w boxes lw 2 lt rgb "#FFFF00" t "F", "" u 1:15 w boxes lw 2 lt rgb "#FF7C81" t "P", "" u 1:16 w boxes lw 2 lt rgb "#C0C0C0" t "U"' % data_path)
        lines.append('unset boxwidth')
        lines.append('set key inside top')
        if has_error:
            lines.append('set bmargin 3')
            lines.append('set format x "% g"')
            lines.append('set xlabel "Concurrent Users"')
            lines.append('set origin 0.0, 0.0')
            lines.append('set size 1.0, 0.3')
            lines.append('set ylabel "% errors"')
            lines.append('set yrange [0:100]')
            lines.append('plot "%s" u 1:3 w boxes lt 1 lw 2 t "%% Errors"' % data_path)

        lines.append('unset yrange')
        lines.append('set autoscale y')
        lines.append('unset multiplot')
        lines.append('set size 1.0, 1.0')
        lines.append('unset rmargin')
        lines.append('set output "%s"' % image2_path)
        lines.append('set title "Pages Response time"')
        lines.append('set ylabel "Duration (s)"')
        lines.append('set bars 5.0')
        lines.append('set style fill solid .25')
        lines.append('plot "%s" u 1:8:8:10:9 t "med/p90/p95" w candlesticks lt 1 lw 1 whiskerbars 0.5, "" u 1:7:4:8:8 w candlesticks lt 2 lw 1 t "min/p10/med" whiskerbars 0.5, "" u 1:5 t "avg" w lines lt 3 lw 2' % data_path)
        f = open(gplot_path, 'w')
        lines = self.fixXLabels('\n'.join(lines) + '\n')
        f.write(lines)
        f.close()
        gnuplot(gplot_path)

    def createAllResponseChart(self):
        """Create global responses chart."""
        image_path = gnuplot_scriptpath(self.report_dir, 'requests_rps.png')
        image2_path = gnuplot_scriptpath(self.report_dir, 'requests.png')
        gplot_path = str(os.path.join(self.report_dir, 'requests.gplot'))
        data_path = gnuplot_scriptpath(self.report_dir, 'requests.data')
        stats = self.stats
        # data
        lines = ["CUs RPS ERROR MIN AVG MAX P10 P50 P90 P95 APDEX"]
        cvus = []
        has_error = False
        for cycle in self.cycles:
            if not stats[cycle].has_key('response'):
                continue
            values = []
            resp = stats[cycle]['response']
            values.append(str(resp.cvus))
            cvus.append(str(resp.cvus))
            values.append(str(resp.rps))
            error = resp.error_percent
            if error:
                has_error = True
            values.append(str(error))
            values.append(str(resp.min))
            values.append(str(resp.avg))
            values.append(str(resp.max))
            values.append(str(resp.percentiles.perc10))
            values.append(str(resp.percentiles.perc50))
            values.append(str(resp.percentiles.perc90))
            values.append(str(resp.percentiles.perc95))
            values.append(str(resp.apdex_score))
            lines.append(' '.join(values))
        if len(lines) == 1:
            # No result during a cycle
            return
        f = open(data_path, 'w')
        f.write('\n'.join(lines) + '\n')
        f.close()
        # script
        lines = ['set output "' + image_path +'"']
        lines.append('set title "Requests Per Second"')
        lines.append('set xlabel "Concurrent Users"')
        lines.append('set ylabel "Requests Per Second"')
        lines.append('set grid')
        lines.append('set xrange ' + self.getXRange())
        lines.append('set terminal png size ' + self.getChartSizeTmp(cvus))
        if not has_error:
            lines.append('plot "%s" u 1:2 w linespoints lw 2 lt 2 t "RPS"' % data_path)
        else:
            lines.append('set format x ""')
            lines.append('set multiplot')
            lines.append('unset title')
            lines.append('unset xlabel')
            lines.append('set size 1, 0.7')
            lines.append('set origin 0, 0.3')
            lines.append('set lmargin 5')
            lines.append('set bmargin 0')
            lines.append('plot "%s" u 1:2 w linespoints lw 2 lt 2 t "RPS"' % data_path)
            lines.append('set format x "% g"')
            lines.append('set bmargin 3')
            lines.append('set autoscale y')
            lines.append('set style fill solid .25')
            lines.append('set size 1.0, 0.3')
            lines.append('set xlabel "Concurrent Users"')
            lines.append('set ylabel "% errors"')
            lines.append('set origin 0.0, 0.0')
            #lines.append('set yrange [0:100]')
            #lines.append('set ytics 20')
            lines.append('plot "%s" u 1:3 w linespoints lt 1 lw 2 t "%% Errors"' % data_path)
            lines.append('unset multiplot')
            lines.append('set size 1.0, 1.0')
        lines.append('set output "%s"' % image2_path)
        lines.append('set title "Requests Response time"')
        lines.append('set ylabel "Duration (s)"')
        lines.append('set bars 5.0')
        lines.append('set grid back')
        lines.append('set style fill solid .25')
        lines.append('plot "%s" u 1:8:8:10:9 t "med/p90/p95" w candlesticks lt 1 lw 1 whiskerbars 0.5, "" u 1:7:4:8:8 w candlesticks lt 2 lw 1 t "min/p10/med" whiskerbars 0.5, "" u 1:5 t "avg" w lines lt 3 lw 2' % data_path)
        f = open(gplot_path, 'w')
        lines = self.fixXLabels('\n'.join(lines) + '\n')
        f.write(lines)
        f.close()
        gnuplot(gplot_path)

        return


    def createResponseChart(self, step):
        """Create responses chart."""
        image_path = gnuplot_scriptpath(self.report_dir,
                                        'request_%s.png' % step)
        gplot_path = str(os.path.join(self.report_dir,
                                      'request_%s.gplot' % step))
        data_path = gnuplot_scriptpath(self.report_dir,
                                       'request_%s.data' % step)
        stats = self.stats
        # data
        lines = ["CUs STEP ERROR MIN AVG MAX P10 P50 P90 P95 APDEX"]
        cvus = []
        has_error = False
        for cycle in self.cycles:
            if not stats[cycle]['response_step'].has_key(step):
                continue
            values = []
            resp = stats[cycle]['response_step'].get(step)
            values.append(str(resp.cvus))
            cvus.append(str(resp.cvus))
            values.append(str(step))
            error = resp.error_percent
            if error:
                has_error = True
            values.append(str(error))
            values.append(str(resp.min))
            values.append(str(resp.avg))
            values.append(str(resp.max))
            values.append(str(resp.percentiles.perc10))
            values.append(str(resp.percentiles.perc50))
            values.append(str(resp.percentiles.perc90))
            values.append(str(resp.percentiles.perc95))
            values.append(str(resp.apdex_score))
            lines.append(' '.join(values))
        if len(lines) == 1:
            # No result during a cycle
            return
        f = open(data_path, 'w')
        f.write('\n'.join(lines) + '\n')
        f.close()
        # script
        lines = []
        lines.append('set output "%s"' % image_path)
        lines.append('set terminal png size ' + self.getChartSizeTmp(cvus))
        lines.append('set grid')
        lines.append('set bars 5.0')
        lines.append('set title "Request %s Response time"' % step)
        lines.append('set xlabel "Concurrent Users"')
        lines.append('set ylabel "Duration (s)"')
        lines.append('set grid back')
        lines.append('set style fill solid .25')
        lines.append('set xrange ' + self.getXRange())
        if not has_error:
            lines.append('plot "%s" u 1:8:8:10:9 t "med/p90/p95" w candlesticks lt 1 lw 1 whiskerbars 0.5, "" u 1:7:4:8:8 w candlesticks lt 2 lw 1 t "min/p10/med" whiskerbars 0.5, "" u 1:5 t "avg" w lines lt 3 lw 2' % data_path)
        else:
            lines.append('set format x ""')
            lines.append('set multiplot')
            lines.append('unset title')
            lines.append('unset xlabel')
            lines.append('set size 1, 0.7')
            lines.append('set origin 0, 0.3')
            lines.append('set lmargin 5')
            lines.append('set bmargin 0')
            lines.append('plot "%s" u 1:8:8:10:9 t "med/p90/p95" w candlesticks lt 1 lw 1 whiskerbars 0.5, "" u 1:7:4:8:8 w candlesticks lt 2 lw 1 t "min/p10/med" whiskerbars 0.5, "" u 1:5 t "avg" w lines lt 3 lw 2' % data_path)
            lines.append('set format x "% g"')
            lines.append('set bmargin 3')
            lines.append('set autoscale y')
            lines.append('set style fill solid .25')
            lines.append('set size 1.0, 0.3')
            lines.append('set xlabel "Concurrent Users"')
            lines.append('set ylabel "% errors"')
            lines.append('set origin 0.0, 0.0')
            #lines.append('set yrange [0:100]')
            #lines.append('set ytics 20')
            lines.append('plot "%s" u 1:3 w linespoints lt 1 lw 2 t "%% Errors"' % data_path)
            lines.append('unset multiplot')
            lines.append('set size 1.0, 1.0')
        f = open(gplot_path, 'w')
        lines = self.fixXLabels('\n'.join(lines) + '\n')
        f.write(lines)
        f.close()
        gnuplot(gplot_path)
        return

    def createMonitorChart(self, host):
        """Create monitrored server charts."""
        stats = self.monitor[host]
        times = []
        cvus_list = []
        for stat in stats:
            test, cycle, cvus = stat.key.split(':')
            stat.cvus=cvus
            date = datetime.fromtimestamp(float(stat.time))
            times.append(date.strftime("%H:%M:%S"))
            #times.append(int(float(stat.time))) # - time_start))
            cvus_list.append(cvus)

        Plugins = MonitorPlugins()
        Plugins.registerPlugins()
        Plugins.configure(self.getMonitorConfig(host))

        charts=[]
        for plugin in Plugins.MONITORS.values():
            image_prefix = gnuplot_scriptpath(self.report_dir, '%s_%s' % (host, plugin.name))
            data_prefix = gnuplot_scriptpath(self.report_dir, '%s_%s' % (host, plugin.name))
            gplot_path = str(os.path.join(self.report_dir, '%s_%s.gplot' % (host, plugin.name)))
            r=plugin.gnuplot(times, host, image_prefix, data_prefix, gplot_path, self.chart_size, stats)
            if r!=None:
                gnuplot(gplot_path)
                charts.extend(r)
        return charts
