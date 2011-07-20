# (C) Copyright 2011 Nuxeo SAS <http://nuxeo.com>
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
"""Classes that render statistics in emacs org-mode format.
"""
import os
import re
from ReportRenderRst import RenderRst
from ReportRenderRst import BaseRst
import ReportRenderRst
from MonitorPlugins import MonitorPlugins

FL_SITE = "http://funkload.nuxeo.org"


def org_title(title, level=1, newpage=True):
    """Return an org section."""
    org = []
    if newpage:
        org.append("")
        org.append("")
        org.append("#+BEGIN_LaTeX")
        org.append("\\newpage")
        org.append('#+END_LaTeX')
    org.append('*' * (level - 1) + ' ' + title + '\n')
    return '\n'.join(org)


def org_image(self):
    org = ["#+BEGIN_LaTeX"]
    org.append('\\begin{center}')
    for image_name in self.image_names:
        org.append("\includegraphics[scale=0.5]{{./%s}.png}" % image_name)
    org.append('\\end{center}')
    org.append('#+END_LaTeX')
    return '\n'.join(org) + '\n'


def org_header(self, with_chart=False):
    headers = self.headers[:]
    if self.with_percentiles:
        self._attach_percentiles_header(headers)
    org = [self.render_image()]
    org.append("#+BEGIN_LaTeX")
    org.append("\\tiny")
    org.append('#+END_LaTeX')
    org.append(' |' + '|'.join(headers) + '|\n |-')
    return '\n'.join(org)


def org_footer(self):
    org = [' |-']
    org.append("#+BEGIN_LaTeX")
    org.append("\\normalsize")
    org.append('#+END_LaTeX')
    return '\n'.join(org)

ReportRenderRst.rst_title = org_title
ReportRenderRst.LI = '-'
BaseRst.render_header = org_header
BaseRst.render_footer = org_footer
BaseRst.render_image = org_image
BaseRst.sep = '|'


class RenderOrg(RenderRst):
    """Render stats in ReST format."""
    # number of slowest requests to display
    slowest_items = 5
    with_chart = True

    def __init__(self, config, stats, error, monitor, monitorconfig, options):
        options.html = True
        RenderRst.__init__(self, config, stats, error, monitor, monitorconfig, options)

    def renderHeader(self):
        config = self.config
        self.append('#    -*- mode: org -*-')
        self.append('#+TITLE: FunkLoad bench report')
        self.append('#+DATE: ' + self.date)
        self.append('''#+STYLE: <link rel="stylesheet" type="text/css" href="eon.css" />
#+LaTeX_CLASS: koma-article
#+LaTeX_CLASS_OPTIONS: [a4paper,landscape]
#+LATEX_HEADER: \usepackage[utf8]{inputenc}
#+LATEX_HEADER: \usepackage[en]{babel}
#+LATEX_HEADER: \usepackage{fullpage}
#+LATEX_HEADER: \usepackage[hyperref,x11names]{xcolor}
#+LATEX_HEADER: \usepackage[colorlinks=true,urlcolor=SteelBlue4,linkcolor=Firebrick4]{hyperref}
#+LATEX_HEADER: \usepackage{graphicx}
#+LATEX_HEADER: \usepackage[T1]{fontenc}''')

        description = [config['class_description']]
        description += ["Bench result of ``%s.%s``: " % (config['class'],
                                                       config['method'])]
        description += [config['description']]

        self.append('#+TEXT: Bench result of =%s.%s=: %s' % (
                config['class'], config['method'], ' '.join(description)))
        self.append('#+OPTIONS: toc:1')
        self.append('')

    def renderMonitor(self, host, charts):
        """Render a monitored host."""
        description = self.config.get(host, '')
        self.append(org_title("%s: %s" % (host, description), 3))
        for chart in charts:
            self.append('#+BEGIN_LaTeX')
            self.append('\\begin{center}')
            self.append("\includegraphics[scale=0.5]{{./%s}.png}" % chart[1])
            self.append('\\end{center}')
            self.append('#+END_LaTeX')

    def renderHook(self):
        self.rst = [line.replace('``', '=') for line in self.rst]
        lapdex = "Apdex_{%s}" % str(self.options.apdex_t)
        kv = re.compile("^(\ *\- [^\:]*)\:(.*)")
        bold = re.compile("\*\*([^\*]+)\*\*")
        link = re.compile("\`([^\<]+)\<([^\>]+)\>\`\_")
        ret = []
        for line in self.rst:
            line = re.sub(kv, lambda m: "%s :: %s\n\n" % (
                    m.group(1), m.group(2)), line)
            line = re.sub(bold, lambda m: "*%s*" % (m.group(1)),
                          line)
            line = re.sub(link, lambda m: "[[%s][%s]]" % (m.group(2),
                                                          m.group(1).strip()),
                          line)
            line = line.replace('|APDEXT|', lapdex)
            line = line.replace('Apdex*', lapdex)
            line = line.replace('Apdex T', 'Apdex_{T}')
            line = line.replace('FunkLoad_',
                                '[[%s][FunkLoad]]' % FL_SITE)
            ret.append(line)
        self.rst = ret

    def createMonitorCharts(self):
        """Create all montirored server charts."""
        if not self.monitor or not self.with_chart:
            return
        self.append(org_title("Monitored hosts", 2))
        charts = {}
        for host in self.monitor.keys():
            charts[host] = self.createMonitorChart(host)
        return charts

    def createMonitorChart(self, host):
        """Create monitrored server charts."""
        charts = []
        Plugins = MonitorPlugins()
        Plugins.registerPlugins()
        Plugins.configure(self.getMonitorConfig(host))

        for plugin in Plugins.MONITORS.values():
            image_path = ('%s_%s' % (host, plugin.name)).replace("\\", "/")
            charts.append((plugin.name, image_path))
        return charts
