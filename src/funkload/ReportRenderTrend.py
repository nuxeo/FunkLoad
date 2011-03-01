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
"""Trend report rendering

The trend report uses metadata from a funkload.metadata file if present.

The format of the metadata file is the following:
label:short label to be displayed in the graph
anykey:anyvalue
a multi line description in ReST will be displayed in the listing parts
"""
import os
from ReportRenderRst import rst_title
from ReportRenderHtmlBase import RenderHtmlBase
from ReportRenderHtmlGnuPlot import gnuplot
from ReportRenderDiff import getRPath

def extract(report_dir, startswith):
    """Extract line form the ReST index file."""
    f = open(os.path.join(report_dir, "index.rst"))
    line = f.readline()
    while line:
        if line.startswith(startswith):
            f.close()
            return line[len(startswith):].strip()
        line = f.readline()
    f.close()
    return None


def extract_date(report_dir):
    """Extract the bench date form the ReST index file."""
    tag = "* Launched: "
    value = extract(report_dir, tag)
    if value is None:
        print "ERROR no date found in rst report %s" % report_dir
        return "NA"
    return value


def extract_max_cus(report_dir):
    """Extract the maximum concurrent users form the ReST index file."""
    tag = "* Cycles of concurrent users: "
    value = extract(report_dir, tag)
    if value is None:
        print "ERROR no max CUs found in rst report %s" % report_dir
        return "NA"
    return value.split(', ')[-1][:-1]


def extract_metadata(report_dir):
    """Extract the metadata from a funkload.metadata file."""
    ret = {}
    try:
        f = open(os.path.join(report_dir, "funkload.metadata"))
    except IOError:
        return ret
    lines = f.readlines()
    f.close()
    for line in lines:
        sep = None
        if line.count(':'):
            sep = ':'
        elif line.count('='):
            sep = '='
        else:
            key = 'misc'
            value = line.strip()
        if sep is not None:
            key, value = line.split(sep, 1)
            ret[key.strip()] = value.strip()
        elif value:
            v = ret.setdefault('misc', '')
            ret['misc'] = v + ' ' + value
    return ret

def extract_stat(tag, report_dir):
    """Extract stat from the ReST index file."""
    lines = open(os.path.join(report_dir, "index.rst")).readlines()
    try:
        idx = lines.index("%s stats\n" % tag)
    except ValueError:
        print "ERROR tag %s not found in rst report %s" % (tag, report_dir)
        return []
    delim = 0
    ret =  []
    header = ""
    for line in lines[idx:]:
        if line.startswith(" ====="):
            delim += 1
            continue
        if delim == 1:
            header = line.strip().split()
        if delim < 2:
            continue
        if delim == 3:
            break
        ret.append([x.replace("%","") for x in line.strip().split()])
    return header, ret

def get_metadata(metadata):
    """Format metadata."""
    ret = []
    keys = metadata.keys()
    keys.sort()
    for key in keys:
        if key not in ('label', 'misc'):
            ret.append('%s: %s' % (key, metadata[key]))
    if metadata.get('misc'):
        ret.append(metadata['misc'])
    return ', '.join(ret)


class RenderTrend(RenderHtmlBase):
    """Trend report."""
    report_dir1 = None
    report_dir2 = None
    header = None
    sep = ', '
    data_file = None
    output_dir = None
    script_file = None

    def __init__(self, args, options, css_file=None):
        # Swap windows path separator backslashes for forward slashes
        # Windows accepts '/' but some file formats like rest treat the
        # backslash specially.
        self.args = [os.path.abspath(arg).replace('\\', '/') for arg in args]
        self.options = options
        self.css_file = css_file

    def generateReportDirectory(self, output_dir):
        """Generate a directory name for a report."""
        output_dir = os.path.abspath(output_dir)
        report_dir = os.path.join(output_dir, 'trend-report')
        if not os.access(report_dir, os.W_OK):
            os.mkdir(report_dir, 0775)
        report_dir.replace('\\', '/')
        return report_dir

    def createCharts(self):
        """Render stats."""
        self.createGnuplotData()
        self.createGnuplotScript()
        gnuplot(self.script_file)

    def createRstFile(self):
        """Create the ReST file."""
        rst_path = os.path.join(self.report_dir, 'index.rst')
        lines = []
        reports = self.args
        reports_name = [os.path.basename(report) for report in reports]
        reports_date = [extract_date(report) for report in reports]
        self.reports_name = reports_name
        reports_metadata = [extract_metadata(report) for report in reports]
        self.reports_metadata = reports_metadata
        reports_rpath = [getRPath(self.report_dir, 
                                  os.path.join(report, 'index.html').replace(
                    '\\', '/')) for report in reports]
        self.max_cus = extract_max_cus(reports[0])
        # TODO: handles case where reports_name are the same
        lines.append(rst_title("FunkLoad_ trend report", level=0))
        lines.append("")
        lines.append(".. sectnum::    :depth: 2")
        lines.append("")
        lines.append(rst_title("Trends", level=2))
        lines.append(" .. image:: trend_apdex.png")
        lines.append(" .. image:: trend_spps.png")
        lines.append(" .. image:: trend_avg.png")
        lines.append("")
        lines.append(rst_title("List of reports", level=1))
        count = 0
        for report in reports_name:
            count += 1
                         
            lines.append(" * Bench **%d** %s: `%s <%s>`_ %s" % (
                    count, reports_date[count - 1], report, 
                    reports_rpath[count - 1], 
                    get_metadata(reports_metadata[count - 1])))
            lines.append("")
        lines.append(" .. _FunkLoad: http://funkload.nuxeo.org/")
        lines.append("")
        f = open(rst_path, 'w')
        f.write('\n'.join(lines))
        f.close()
        self.rst_path = rst_path

    def copyXmlResult(self):
        pass

    def __repr__(self):
        return self.render()

    def createGnuplotData(self):
        """Render rst stat."""

        def output_stat(tag, count):
            header, stat = extract_stat(tag, rep)
            text = []
            for line in stat:
                line.insert(0, str(count))
                line.append(extract_date(rep))
                text.append(' '.join(line))
            return '\n'.join(text)

        data_file = os.path.join(self.report_dir, 'trend.dat')
        self.data_file = data_file
        f = open(data_file, 'w')
        count = 0
        for rep in self.args:
            count += 1
            f.write(output_stat('Page', count) + '\n\n')
        f.close()

    def createGnuplotScript(self):
        """Build gnuplot script"""
        labels = []
        count = 0
        for metadata in self.reports_metadata:
            count += 1
            if metadata.get('label'):
                labels.append('set label "%s" at %d,%d,1 rotate by 45 front' % (
                        metadata.get('label'), count, int(self.max_cus) + 2))
        labels = '\n'.join(labels)
        script_file = os.path.join(self.report_dir, 'script.gplot')
        self.script_file = script_file
        f = open(script_file, 'w')
        f.write('# ' + ' '.join(self.reports_name))
        f.write('''# COMMON SETTINGS
set grid  back
set boxwidth 0.9 relative

# Apdex
set output "trend_apdex.png"
set terminal png size 640,380
set border 895 front linetype -1 linewidth 1.000
set grid nopolar
set grid xtics nomxtics ytics nomytics noztics nomztics \
 nox2tics nomx2tics noy2tics nomy2tics nocbtics nomcbtics
set grid layerdefault  linetype 0 linewidth 1.000,  linetype 0 linewidth 1.000
set style line 100  linetype 5 linewidth 0.10 pointtype 100 pointsize default
#set view map
unset surface
set style data pm3d
set style function pm3d
set ticslevel 0
set nomcbtics
set xrange [ * : * ] noreverse nowriteback
set yrange [ * : * ] noreverse nowriteback
set zrange [ * : * ] noreverse nowriteback
set cbrange [ * : * ] noreverse nowriteback
set lmargin 0
set pm3d at s scansforward
# set pm3d scansforward interpolate 0,1
set view map
set title "Apdex Trend"
set xlabel "Bench"
set ylabel "CUs"
%s
splot "trend.dat" using 1:2:3 with linespoints
unset label
set view

set output "trend_spps.png"
set title "Pages per second Trend"
splot "trend.dat" using 1:2:5 with linespoints

set output "trend_avg.png"
set palette negative
set title "Average response time (s)"
splot "trend.dat" using 1:2:11 with linespoints

''' % labels)
        f.close()

