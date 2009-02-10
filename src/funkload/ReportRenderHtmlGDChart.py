# (C) Copyright 2008 Nuxeo SAS <http://nuxeo.com>
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
"""Render chart using gdchart2.

$Id$
"""

import os
import gdchart
try:
    # Check python-gdchart2
    from gdchart import GDChartError
except ImportError:
    raise ImportError("FunkLoad > 1.8.0R requires python-gdchart2.")
from ReportRenderRst import rst_title
from ReportRenderHtmlBase import RenderHtmlBase


class RenderHtmlGDChart(RenderHtmlBase):
    """Render stats in html using gdchart.

    Simply render stuff in ReST than ask docutils to build an html doc.
    """
    color_success = 0x00ff00
    color_error = 0xff0000
    color_time = 0x0000ff
    color_time_min_max = 0xccccee
    color_grid = 0xcccccc
    color_line = 0x333333
    color_plot = 0x003a6b
    color_bg = 0xffffff
    color_line = 0x000000

    # XXX need some factoring below
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
        x = gdchart.LineBarCombo3D()
        x.title = 'Successful Tests Per Second'
        x.xtitle = 'CUs'
        x.ylabel_fmt = '%.2f'
        x.ylabel2_fmt = '%.2f %%'
        x.ytitle = 'STPS'
        x.ytitle2 = "Errors"
        x.ylabel_density = 50
        x.ytitle2_color = color_error
        x.ylabel2_color = color_error
        x.requested_ymin = 0.0

        x.set_color = (self.color_success, self.color_success)
        x.vol_color = self.color_error
        x.bg_color = self.color_bg
        x.plot_color=self.color_plot
        x.line_color = self.color_line
        x.width, x.height = self.getChartSize(cvus)
        x.setLabels(cvus)
        x.setData(stps)
        x.setComboData(errors)
        x.draw(image_path)


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
        x = gdchart.HLCBarCombo3D()
        x.set_color = (self.color_time_min_max, self.color_time_min_max,
                       self.color_time)
        x.vol_color = self.color_error
        x.bg_color = self.color_bg
        x.plot_color = self.color_plot
        x.grid_color = self.color_grid
        x.line_color = self.color_line
        x.title = 'Page response time'
        x.xtitle = 'CUs'
        x.ylabel_fmt = '%.2fs'
        x.ylabel2_fmt = '%.2f %%'
        x.ytitle = self.getYTitle()
        x.ytitle2 = "Errors"
        x.ylabel_density = 50
        x.hlc_style = ("I_CAP", "CONNECTING")
        x.ytitle2_color = color_error
        x.ylabel2_color = color_error
        x.requested_ymin = 0.0
        x.width, x.height = self.getChartSize(cvus)
        x.setLabels(cvus)
        x.setData((delay_high, delay_low, delay))
        x.setComboData(errors)
        x.draw(image_path)

        x = gdchart.LineBarCombo3D()
        x.set_color = (self.color_success, self.color_success)
        x.vol_color = self.color_error
        x.bg_color = self.color_bg
        x.plot_color = self.color_plot
        x.line_color = self.color_line
        x.title = 'Successful Pages Per Second'
        x.xtitle = 'CUs'
        x.ylabel_fmt = '%.2f'
        x.ylabel2_fmt = '%.2f %%'
        x.ytitle = 'SPPS'
        x.ytitle2 = "Errors"
        x.ytitle2_color = color_error
        x.ylabel2_color = color_error
        x.ylabel_density = 50
        x.requested_ymin = 0.0
        x.width, x.height = self.getChartSize(cvus)
        x.setLabels(cvus)
        x.setData(spps)
        x.setComboData(errors)
        x.draw(image2_path)


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

        x = gdchart.HLCBarCombo3D()
        x.set_color = (self.color_time_min_max,
                       self.color_time_min_max, self.color_time)
        x.vol_color = self.color_error
        x.bg_color = self.color_bg
        x.plot_color = self.color_plot
        x.grid_color = self.color_grid
        x.line_color = self.color_line
        x.title = 'Request response time'
        x.xtitle = 'CUs'
        x.ylabel_fmt = '%.2fs'
        x.ylabel2_fmt = '%.2f %%'
        x.ytitle = self.getYTitle()
        x.ytitle2 = "Errors"
        x.ylabel_density = 50
        x.hlc_style = ("I_CAP", "CONNECTING")
        x.ytitle2_color = color_error
        x.ylabel2_color = color_error
        x.requested_ymin = 0.0
        x.width, x.height = self.getChartSize(cvus)
        x.setLabels(cvus)
        x.setData((delay_high, delay_low, delay))
        x.setComboData(errors)
        x.draw(image_path)

        x = gdchart.LineBarCombo3D()
        x.set_color = (self.color_success, self.color_success)
        x.vol_color = self.color_error
        x.bg_color = self.color_bg
        x.plot_color = self.color_plot
        x.line_color = self.color_line
        x.title = 'Requests Per Second'
        x.xtitle = 'CUs'
        x.ylabel_fmt = '%.2f'
        x.ylabel2_fmt = '%.2f %%'
        x.ytitle = 'RPS'
        x.ytitle2 = "Errors"
        x.ylabel_density = 50
        x.ytitle2_color = color_error
        x.ylabel2_color = color_error
        x.requested_ymin = 0.0
        x.width, x.height = self.getChartSize(cvus)
        x.setLabels(cvus)
        x.setData(rps)
        x.setComboData(errors)
        x.draw(image2_path)


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

        x = gdchart.HLCBarCombo3D()
        x.set_color = (self.color_time_min_max,
                     self.color_time_min_max, self.color_time)
        x.vol_color = self.color_error
        x.bg_color = self.color_bg
        x.plot_color = self.color_plot
        x.grid_color = self.color_grid
        x.line_color = self.color_line
        x.title = title
        x.xtitle = 'CUs'
        x.ylabel_fmt = '%.2fs'
        x.ylabel2_fmt = '%.2f %%'
        x.ytitle = self.getYTitle()
        x.ytitle2 = "Errors"
        x.ylabel_density = 50
        x.hlc_style = ("I_CAP", "CONNECTING")
        x.ytitle2_color = color_error
        x.ylabel2_color = color_error
        x.requested_ymin = 0.0
        x.width, x.height = self.getChartSize(cvus)
        x.setLabels(cvus)
        x.setData((delay_high, delay_low, delay))
        x.setComboData(errors)
        x.draw(image_path)


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
            # Limit size to 11 as 12 core dump glibc python: free() on feisty
            times.append(str('%ss-%sCUs' % (
                int(float(stat.time) - time_start), cvus))[:11])

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

        title = str('%s: cpu usage (green 1 = 100%%) and loadavg 1(red), '
                    '5 and 15 min' % host)
        x = gdchart.Line()
        x.set_color = (0x00ff00, 0xff0000, 0x0000ff)
        x.vol_color = 0xff0000
        x.bg_color = self.color_bg
        x.plot_color = self.color_plot
        x.line_color = self.color_line
        x.title = title
        x.xtitle = 'time and CUs'
        x.ylabel_fmt = '%.2f'
        x.ytitle = 'loadavg'
        x.ylabel_density = 50
        x.requested_ymin = 0.0
        x.width, x.height = self.big_chart_size
        x.setLabels(times)
        x.setData(cpu_usage, load_avg_1, load_avg_5, load_avg_15)
        x.draw(image_path)

        title = str('%s memory (green) and swap (red) usage' % host)
        image_path = str(os.path.join(self.report_dir, '%s_mem.png' % host))
        x = gdchart.Line()
        x.title = title
        x.ylabel_fmt = '%.0f kB'
        x.ytitle = 'memory used kB'
        x.set_color = (0x00ff00, 0xff0000, 0x0000ff)
        x.vol_color = 0xff0000
        x.bg_color = self.color_bg
        x.plot_color = self.color_plot
        x.line_color = self.color_line
        x.title = title
        x.xtitle = 'time and CUs'
        x.width, x.height = self.big_chart_size
        x.setLabels(times)
        x.setData(mem_used, swap_used)
        x.draw(image_path)

        title = str('%s network in (green)/out (red)' % host)
        image_path = str(os.path.join(self.report_dir, '%s_net.png' % host))
        x = gdchart.Line()
        x.title = title
        x.ylabel_fmt = '%.0f kB/s'
        x.ytitle = 'network'
        x.set_color = (0x00ff00, 0xff0000, 0x0000ff)
        x.vol_color = 0xff0000
        x.bg_color = self.color_bg
        x.plot_color = self.color_plot
        x.line_color = self.color_line
        x.title = title
        x.xtitle = 'time and CUs'
        x.width, x.height = self.big_chart_size
        x.setLabels(times)
        x.setData(net_in, net_out)
        x.draw(image_path)

